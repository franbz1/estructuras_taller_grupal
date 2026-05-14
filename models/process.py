"""Process descriptors and deterministic workload scripting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple, Optional, Tuple, Union

from data_structures.stack import CallStack, EmptyStackError, StackFrame

PlanStep = Tuple[str, ...]


class ProcessState(Enum):
    READY = auto()
    RUNNING = auto()
    BLOCKED = auto()
    TERMINATED = auto()


class BurstDescriptorError(ValueError):
    """Raised whenever the authoring DSL violates the toy constraints."""


class LiteralBurst(NamedTuple):
    kind: str  # "CPU", "DONE", etc.


class IOSyscallPending(NamedTuple):
    keyword: str
    service_ticks: int


BurstView = Union[LiteralBurst, IOSyscallPending]


@dataclass(slots=True)
class Process:
    """Represents PCB fields needed by the pedagogical OSSimulator."""

    pid: int
    name: str
    priority: int
    plan: Tuple[PlanStep, ...]
    quantum_remaining: int = 0
    state: ProcessState = ProcessState.READY
    step_index: int = 0
    cpu_burst_remaining: int = 0
    pending_io_ticks: int = 0
    pending_io_keyword: Optional[str] = None
    cpu_registers: list[int] = field(default_factory=lambda: [0] * 8)
    call_stack: CallStack = field(default_factory=CallStack)
    arrival_tick: int = -1
    start_tick: int = -1
    finish_tick: int = -1
    is_idle: bool = False

    def __post_init__(self) -> None:
        if not self.plan:
            raise BurstDescriptorError("Plan needs at least one descriptor")
        self._reload_burst_from_plan()

        if isinstance(self.inspect_burst_kind(), IOSyscallPending):
            raise BurstDescriptorError(
                "Plans must start with a CPU burst — prepend a warmup CPU segment"
            )

    # ------------------------------------------------------------------ state mutations
    def mark_ready(self) -> None:
        self.state = ProcessState.READY

    def mark_running(self) -> None:
        self.state = ProcessState.RUNNING

    def mark_blocked_syscall(self, frame_name: str) -> None:
        self.state = ProcessState.BLOCKED
        self.call_stack.push(StackFrame(function_name=frame_name))

    def finalize_termination_cleanup(self) -> None:
        self.state = ProcessState.TERMINATED
        while not self.call_stack.is_empty():
            try:
                self.call_stack.pop()
            except EmptyStackError:
                break

    def finish_io_burst(self) -> None:
        if not self.call_stack.is_empty():
            try:
                self.call_stack.pop()
            except EmptyStackError:
                pass
        self.pending_io_ticks = 0
        self.pending_io_keyword = None

    # ------------------------------------------------------------------ simulation helpers
    def plan_finished(self) -> bool:
        return self.step_index >= len(self.plan)

    def inspect_burst_kind(self) -> BurstView:
        if self.plan_finished():
            return LiteralBurst(kind="DONE")

        head = tuple(str(token).lower() for token in self.plan[self.step_index])
        opcode = head[0]
        if opcode == "cpu":
            ticks = max(int(head[1]), 0)
            if ticks == 0:
                raise BurstDescriptorError("CPU bursts must be strictly positive")
            return LiteralBurst(kind="CPU")

        if opcode == "io":
            keyword = head[1].upper()
            service = int(head[2])
            if service <= 0:
                raise BurstDescriptorError("IO durations must stay positive integers")
            return IOSyscallPending(keyword=keyword, service_ticks=service)

        raise BurstDescriptorError(f"Unknown opcode `{opcode}`")

    def reset_quantum_slice(self, value: int) -> None:
        self.quantum_remaining = value

    def touch_registers(self, clock_tick: int) -> None:
        scrambling = ((self.pid * 92837111) ^ (clock_tick << 16)) & 0xFFFFFFFF
        rotating = scrambling % len(self.cpu_registers)

        chunk = self.cpu_registers[: rotating + 1]
        del self.cpu_registers[: rotating + 1]
        self.cpu_registers.extend(chunk)

        pivot = scrambling % len(self.cpu_registers)
        self.cpu_registers[pivot] ^= scrambling

    def consume_cpu_micro_step(self, clock_tick: int) -> None:
        if self.cpu_burst_remaining <= 0:
            raise RuntimeError("consume_cpu_micro_step called without runnable CPU burst")
        self.touch_registers(clock_tick)
        self.cpu_burst_remaining -= 1

    def advance_plan_pointer(self) -> BurstView:
        self.step_index += 1

        if self.plan_finished():
            self.finalize_termination_cleanup()
            return LiteralBurst(kind="DONE")

        self._reload_burst_from_plan()

        awaiting_io = isinstance(self.inspect_burst_kind(), IOSyscallPending)
        if awaiting_io:
            descriptor = IOSyscallPending(
                keyword=self.pending_io_keyword or "",
                service_ticks=self.pending_io_ticks,
            )
            syscall_name = f"syscall_{descriptor.keyword.lower()}"
            self.mark_blocked_syscall(syscall_name)

        return self.inspect_burst_kind()

    def resume_after_io_service(self) -> BurstView:
        """Called when a mocked device acknowledges completion of pending work."""
        self.finish_io_burst()
        self.step_index += 1

        if self.plan_finished():
            self.finalize_termination_cleanup()
            return LiteralBurst(kind="DONE")

        self._reload_burst_from_plan()

        if isinstance(self.inspect_burst_kind(), IOSyscallPending):
            descriptor = IOSyscallPending(
                keyword=self.pending_io_keyword or "",
                service_ticks=self.pending_io_ticks,
            )
            syscall_name = f"syscall_{descriptor.keyword.lower()}"
            self.mark_blocked_syscall(syscall_name)
            return IOSyscallPending(
                keyword=descriptor.keyword.upper(), service_ticks=descriptor.service_ticks
            )

        self.mark_ready()
        return LiteralBurst(kind="CPU")

    # ------------------------------------------------------------------ internals
    def _reload_burst_from_plan(self) -> None:
        peek = tuple(str(token).lower() for token in self.plan[self.step_index])
        opcode = peek[0]
        if opcode == "cpu":
            ticks = max(int(peek[1]), 0)
            if ticks == 0:
                raise BurstDescriptorError("CPU bursts must remain positive integers")
            self.cpu_burst_remaining = ticks
            self.pending_io_keyword = None
            self.pending_io_ticks = 0
        elif opcode == "io":
            keyword = peek[1].upper()
            service = int(peek[2])
            self.cpu_burst_remaining = 0
            self.pending_io_keyword = keyword
            self.pending_io_ticks = service
        else:
            raise BurstDescriptorError(f"Malformed opcode `{opcode}`")
