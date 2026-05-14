"""Demonstration harness exercising every custom data structure concurrently."""

from __future__ import annotations

from typing import Any

from simulator import OSSimulator


def blueprint(*segments: Any) -> tuple[Any, ...]:
    """DSL helper keeping `main()` aligned with coursework readability goals."""
    return segments


def main() -> None:
    kernel = OSSimulator(pcb_capacity=32, default_quantum=4, verbosity=True)

    kernel.create_process(
        "init_daemon",
        86,
        blueprint(
            ("cpu", 5),
            ("io", "disk", 2),
            ("cpu", 4),
            ("io", "network", 2),
            ("cpu", 3),
        ),
    )
    kernel.create_process(
        "logger_agent",
        72,
        blueprint(
            ("cpu", 2),
            ("io", "printer", 3),
            ("cpu", 6),
            ("io", "disk", 1),
            ("cpu", 2),
        ),
    )
    kernel.create_process(
        "analytics_job",
        64,
        blueprint(
            ("cpu", 7),
            ("io", "disk", 2),
            ("cpu", 3),
            ("io", "network", 1),
            ("cpu", 4),
        ),
    )
    kernel.create_process(
        "cron_worker_a",
        58,
        blueprint(
            ("cpu", 3),
            ("io", "disk", 1),
            ("cpu", 2),
            ("io", "printer", 2),
            ("cpu", 5),
            ("io", "network", 1),
            ("cpu", 3),
        ),
    )
    kernel.create_process(
        "cron_worker_b",
        54,
        blueprint(
            ("cpu", 4),
            ("io", "printer", 1),
            ("cpu", 3),
            ("io", "disk", 3),
            ("cpu", 2),
        ),
    )
    kernel.create_process(
        "streaming_client",
        70,
        blueprint(
            ("cpu", 2),
            ("io", "network", 3),
            ("cpu", 5),
            ("io", "network", 1),
            ("cpu", 4),
            ("io", "printer", 1),
            ("cpu", 3),
        ),
    )
    kernel.create_process(
        "compile_server",
        62,
        blueprint(
            ("cpu", 6),
            ("io", "disk", 2),
            ("cpu", 5),
            ("io", "disk", 2),
            ("cpu", 4),
            ("io", "printer", 2),
            ("cpu", 6),
            ("cpu", 2),
        ),
    )
    kernel.create_process(
        "sandbox_probe",
        48,
        blueprint(
            ("cpu", 2),
            ("io", "disk", 1),
            ("cpu", 2),
            ("io", "network", 2),
            ("cpu", 2),
        ),
    )
    kernel.create_process(
        "backup_daemon",
        60,
        blueprint(
            ("cpu", 3),
            ("io", "disk", 4),
            ("cpu", 3),
            ("io", "printer", 1),
            ("cpu", 4),
        ),
    )
    kernel.create_process(
        "latency_probe_x",
        52,
        blueprint(
            ("cpu", 4),
            ("io", "network", 2),
            ("cpu", 5),
            ("io", "disk", 1),
            ("cpu", 6),
            ("io", "printer", 2),
            ("cpu", 8),
            ("cpu", 7),
            ("cpu", 6),
            ("cpu", 5),
            ("cpu", 4),
            ("cpu", 3),
            ("cpu", 2),
            ("cpu", 1),
            ("cpu", 22),
            ("cpu", 18),
            ("cpu", 15),
            ("cpu", 12),
            ("cpu", 9),
            ("cpu", 7),
            ("cpu", 5),
            ("cpu", 34),
            ("cpu", 56),
            ("cpu", 73),
            ("cpu", 89),
        ),
    )

    kernel.run(180)

    print("\n=== Simulation report ===")
    for key, value in kernel.generate_report().items():
        print(f"{key}: {value}")

    sink = kernel.trace_sink()
    print("\n=== Tail of timeline ===")
    for line in sink.tail(28):
        print(line)


if __name__ == "__main__":
    main()
