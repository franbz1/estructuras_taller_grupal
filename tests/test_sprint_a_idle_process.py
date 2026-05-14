"""Sprint A: permanent idle workload occupying PID 0."""

from __future__ import annotations

from models.process import ProcessState
from simulator.os_simulator import OSSimulator


def test_idle_process_registered_at_pid_zero() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    idle = kernel.pcb.get_process(0)
    assert idle.pid == 0
    assert idle.name == "idle"
    assert idle.is_idle is True


def test_user_processes_start_at_pid_one() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    job = kernel.create_process("work", 70, (("cpu", 3),))
    assert job.pid == 1


def test_scheduler_ring_always_has_current_after_boot() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    assert kernel.scheduler_gate.current_process() is not None


def test_tick_with_only_idle_does_not_finalize_idle() -> None:
    kernel = OSSimulator(pcb_capacity=8, default_quantum=2, verbosity=False)
    kernel.run(25)
    idle = kernel.pcb.get_process(0)
    assert idle.is_idle is True
    assert idle.state != ProcessState.TERMINATED
