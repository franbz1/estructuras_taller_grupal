"""Sprint A: READY-queue priority aging."""

from __future__ import annotations

import pytest

from simulator.os_simulator import OSSimulator


def test_invalid_aging_interval_rejected() -> None:
    with pytest.raises(ValueError, match="Priority aging interval"):
        OSSimulator(pcb_capacity=8, default_quantum=2, verbosity=False, aging_interval=0)


def test_priority_aging_boosts_waiting_low_priority_job() -> None:
    kernel = OSSimulator(
        pcb_capacity=16,
        default_quantum=2,
        verbosity=False,
        aging_interval=3,
    )
    # Wide quantum on the dominant job keeps competitors READY while it runs.
    kernel.create_process("hog", 95, (("cpu", 400),), quantum=25)
    tail = kernel.create_process("starved", 15, (("cpu", 400),))
    baseline = tail.priority
    kernel.run(160)
    assert tail.priority > baseline
