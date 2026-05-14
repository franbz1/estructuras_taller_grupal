"""Top-level orchestrator binding PCBTable, RR and IO together."""

from __future__ import annotations

from typing import List, Mapping, MutableMapping, Sequence, Tuple

from data_structures.array import PCBFullError, PCBTable
from models.process import IOSyscallPending, LiteralBurst, Process, ProcessState
from simulator.io_manager import IOManager
from simulator.scheduler import RoundRobinScheduler
from utils.logger import SimulatorLogger


class OSSimulator:
    """
    Extremely small kernel-like harness so students inspect four cooperating ADTs.

    Deterministic scripted workloads intentionally avoid randomness — every tuple maps
    to either a CPU quantum segment or an IO subsystem release.
    """

    __slots__ = (
        "_aging_interval",
        "_clock",
        "_io",
        "_logger",
        "_pcb_board",
        "_registry",
        "_scheduler",
    )

    def __init__(
        self,
        *,
        pcb_capacity: int = 96,
        default_quantum: int = 4,
        verbosity: bool = True,
        aging_interval: int = 5,
    ) -> None:
        if pcb_capacity <= 0:
            raise ValueError("PCB backing store must expose positive capacity")
        if aging_interval <= 0:
            raise ValueError("Priority aging interval must stay positive")

        self._pcb_board = PCBTable(pcb_capacity)
        self._scheduler = RoundRobinScheduler(default_quantum)
        self._io = IOManager()
        self._logger = SimulatorLogger(emit_to_stdout=verbosity)
        self._registry: List[Process] = []
        self._clock = 0
        self._aging_interval = aging_interval
        self._boot_idle_process()

    @property
    def clock(self) -> int:
        return self._clock

    @property
    def pcb(self) -> PCBTable:
        return self._pcb_board

    @property
    def scheduler_gate(self) -> RoundRobinScheduler:
        return self._scheduler

    @property
    def io_plane(self) -> IOManager:
        return self._io

    def trace_sink(self) -> SimulatorLogger:
        return self._logger

    # ---------------------------------------------------------------- ingestion
    def create_process(self, name: str, priority: int, plan: Sequence[Tuple[str, ...]]) -> Process:
        slot_hint = self._pcb_board.first_available_slot()
        if slot_hint is None:
            raise PCBFullError("No free PCB slots available")

        sculpted_plan = tuple(tuple(step) for step in plan)
        rookie = Process(pid=slot_hint, name=name, priority=priority, plan=sculpted_plan)
        rookie.arrival_tick = self._clock

        try:
            self._pcb_board.add_process(rookie)
        except PCBFullError as exc:
            raise PCBFullError(f"Conflict while reserving PID `{slot_hint}`") from exc

        self._scheduler.enqueue_ready(rookie)
        self._registry.append(rookie)

        textual_stack = ".".join(rookie.call_stack.snapshot()) if rookie.call_stack.size() else "(empty)"

        self._logger.record(
            "lifecycle",
            (
                f"Spawned pid={rookie.pid} `{rookie.name}` pri={rookie.priority} "
                f"stack.depth={rookie.call_stack.size()} [{textual_stack}]"
            ),
        )

        return rookie

    def _apply_priority_aging(self) -> None:
        """Boost priorities for READY workloads that sit too long in the RR ring."""

        for proc in self._scheduler.walk_ready_ring():
            if proc.is_idle:
                continue
            if proc.state != ProcessState.READY:
                continue
            proc.ready_ticks += 1
            if proc.ready_ticks % self._aging_interval == 0:
                proc.priority += 1

    def _boot_idle_process(self) -> None:
        """Reserve PID 0 as a permanent idle workload whenever no real job is runnable."""

        idle_plan = (("cpu", 9_999_999),)
        idle_proc = Process(pid=0, name="idle", priority=0, plan=idle_plan, is_idle=True)
        idle_proc.arrival_tick = self._clock
        self._pcb_board.add_process(idle_proc)
        self._scheduler.enqueue_ready(idle_proc)

    # ---------------------------------------------------------------- simulation kernel
    def tick(self) -> None:
        self._clock += 1
        self._apply_priority_aging()

        for released in self._io.tick():
            self._finalize_device_feedback(released)

        current = self._scheduler.current_process()
        if current is None:
            raise RuntimeError("Ready ring is empty; idle PID 0 should always be present")

        if current.state == ProcessState.TERMINATED:
            self._purge_stale_execution_context(current)
            return

        current.mark_running()
        if current.start_tick == -1:
            current.start_tick = self._clock

        try:
            current.consume_cpu_micro_step(self._clock)
        except RuntimeError:
            err = (
                f"Pid {current.pid} issued CPU stepping without runnable burst — investigate "
                f"blueprint index `{current.step_index}`"
            )
            self._logger.record("fault", err)
            raise

        diverted = False
        if current.cpu_burst_remaining <= 0:
            diverted = self._handle_cpu_burst_rollout(current)

        if diverted:
            return

        current.quantum_remaining -= 1

        if current.quantum_remaining <= 0:
            previous = current
            self._scheduler.rotate_scheduler_pointer()
            successor = self._scheduler.current_process()

            successor_pid = successor.pid if successor else "∅"
            self._logger.record(
                "rr",
                f"Quantum shelf drained — rollover pid={previous.pid} → pid={successor_pid}",
            )

            if successor:
                successor.reset_quantum_slice(self._scheduler.quantum)
                successor.mark_running()

    def run(self, total_ticks: int) -> None:
        if total_ticks < 0:
            raise ValueError("Cannot regress simulated ticks")

        for _ in range(total_ticks):
            self.tick()

    # ---------------------------------------------------------------- diagnostics snapshot
    def generate_report(self) -> Mapping[str, object]:
        state_bins: MutableMapping[str, int] = {bucket.name.lower(): 0 for bucket in ProcessState}
        for phantom in self._registry:
            state_bins[phantom.state.name.lower()] += 1

        pcb_pressure = sum(1 for _ in self._pcb_board.all_registered())

        per_process_stats: List[Mapping[str, object]] = []
        for phantom in self._registry:
            if phantom.finish_tick < 0:
                continue
            turnaround = phantom.finish_tick - phantom.arrival_tick
            service_span = phantom.finish_tick - phantom.start_tick
            waiting = turnaround - service_span
            per_process_stats.append(
                {
                    "pid": phantom.pid,
                    "name": phantom.name,
                    "arrival_tick": phantom.arrival_tick,
                    "start_tick": phantom.start_tick,
                    "finish_tick": phantom.finish_tick,
                    "turnaround_ticks": turnaround,
                    "waiting_ticks": waiting,
                }
            )

        backlog: MutableMapping[str, int] = {}
        for bridge_type, facade in self._io.devices_snapshot().items():
            backlog[bridge_type.name.lower()] = facade.backlog_len()

        rr_richness = len(self._scheduler)
        ring_outline = tuple(node.pid for node in self._scheduler.walk_ready_ring())
        return {
            "sim_clock": self._clock,
            "pcb_slots_in_use": pcb_pressure,
            "pcb_capacity": self._pcb_board.capacity,
            "process_states": dict(state_bins),
            "registered_process_total": len(self._registry),
            "round_robin_depth": rr_richness,
            "ready_ring_order": ring_outline,
            "per_process_stats": per_process_stats,
            "io_device_backlogs": dict(backlog),
            "telemetry_buckets": self._logger.buckets_snapshot(),
        }

    # ---------------------------------------------------------------- internal helpers
    def _purge_stale_execution_context(self, corpse: Process) -> None:
        self._finalize_process_accounts(corpse)

    def _finalize_device_feedback(self, released: Process) -> None:
        synopsis = released.resume_after_io_service()

        if isinstance(synopsis, LiteralBurst) and synopsis.kind == "DONE":
            self._finalize_process_accounts(released)
            return

        if isinstance(synopsis, IOSyscallPending):
            bridge_name = synopsis.keyword.upper()
            self._logger.record("syscall", f"Chained syscall pid={released.pid} device={bridge_name}")
            self._io.request_io(released, bridge_name)
            return

        self._scheduler.enqueue_ready(released)
        self._logger.record(
            "wakeup",
            f"IODevice completion pid={released.pid} backlog.stack={released.call_stack.snapshot()}",
        )

    def _handle_cpu_burst_rollout(self, proc: Process) -> bool:
        if proc.is_idle:
            proc.cpu_burst_remaining = 9_999_999
            return False

        descriptor = proc.advance_plan_pointer()

        if isinstance(descriptor, LiteralBurst) and descriptor.kind == "DONE":
            self._finalize_process_accounts(proc)
            self._logger.record("done", f"Workload finished pid={proc.pid}")
            return True

        if isinstance(descriptor, IOSyscallPending):
            self._scheduler.dequeue_matching(lambda runnable: runnable.pid == proc.pid)
            self._io.request_io(proc, descriptor.keyword)
            self._logger.record(
                "syscall",
                f"syscall pid={proc.pid} device={descriptor.keyword} ticks={descriptor.service_ticks}",
            )
            return True

        proc.reset_quantum_slice(self._scheduler.quantum)
        self._logger.record(
            "burst",
            f"Activated next CPU slug pid={proc.pid} leftover={proc.cpu_burst_remaining}",
        )
        return False

    def _finalize_process_accounts(self, proc: Process) -> None:
        if proc.is_idle:
            return

        proc.finish_tick = self._clock
        self._scheduler.dequeue_matching(lambda runnable: runnable.pid == proc.pid)
        self._pcb_board.remove_process(proc.pid)
        if proc.state != ProcessState.TERMINATED:
            proc.finalize_termination_cleanup()
