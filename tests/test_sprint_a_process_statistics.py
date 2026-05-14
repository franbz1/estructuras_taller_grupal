"""Sprint A: process turnaround statistics surfaced via generate_report."""

from __future__ import annotations

from simulator.os_simulator import OSSimulator


def test_arrival_tick_captured_at_spawn_clock() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    kernel.run(3)
    job = kernel.create_process("late", 70, (("cpu", 1),))
    assert job.arrival_tick == kernel.clock


def test_finish_populates_per_process_stats_with_turnaround_and_waiting() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    kernel.create_process("short", 80, (("cpu", 1),))
    kernel.run(5)

    report = kernel.generate_report()
    stats = report["per_process_stats"]
    assert len(stats) == 1
    row = stats[0]
    assert row["pid"] == 1
    assert row["name"] == "short"
    assert row["arrival_tick"] == 0
    assert row["finish_tick"] >= row["start_tick"] >= 0
    turnaround = row["finish_tick"] - row["arrival_tick"]
    waiting = turnaround - (row["finish_tick"] - row["start_tick"])
    assert row["turnaround_ticks"] == turnaround
    assert row["waiting_ticks"] == waiting


def test_running_process_omitted_from_per_process_stats() -> None:
    kernel = OSSimulator(pcb_capacity=16, default_quantum=4, verbosity=False)
    kernel.create_process("slow", 80, (("cpu", 500),))
    kernel.run(8)

    report = kernel.generate_report()
    assert report["per_process_stats"] == []
