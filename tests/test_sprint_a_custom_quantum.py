"""Sprint A: optional per-process RR quantum overrides."""

from __future__ import annotations

import pytest

from models.process import Process
from simulator.os_simulator import OSSimulator
from simulator.scheduler import RoundRobinScheduler


def test_create_process_rejects_non_positive_quantum_override() -> None:
    kernel = OSSimulator(pcb_capacity=8, default_quantum=4, verbosity=False)
    with pytest.raises(ValueError, match="Per-process quantum"):
        kernel.create_process("bad", 55, (("cpu", 1),), quantum=0)


def test_custom_quantum_sets_initial_scheduler_slice() -> None:
    kernel = OSSimulator(pcb_capacity=8, default_quantum=9, verbosity=False)
    proc = kernel.create_process("slice", 60, (("cpu", 30),), quantum=3)
    assert proc.quantum_remaining == 3


def test_enqueue_ready_honors_custom_quantum_on_scheduler() -> None:
    scheduler = RoundRobinScheduler(8)
    rookie = Process(pid=3, name="solo", priority=40, plan=(("cpu", 12),), custom_quantum=2)
    scheduler.enqueue_ready(rookie)
    assert rookie.quantum_remaining == 2


def test_effective_quantum_used_after_rr_handoff() -> None:
    kernel = OSSimulator(pcb_capacity=12, default_quantum=6, verbosity=False)
    kernel.create_process("leader", 92, (("cpu", 200),))
    follower = kernel.create_process("tail", 75, (("cpu", 200),), quantum=2)

    seen_refresh = False
    for _ in range(400):
        kernel.tick()
        cur = kernel.scheduler_gate.current_process()
        if cur is not None and cur.pid == follower.pid and cur.quantum_remaining == 2:
            seen_refresh = True
            break

    assert seen_refresh, "Expected follower to receive a fresh quantum-2 slice after RR rotation"
