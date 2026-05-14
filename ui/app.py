"""Ventana principal del simulador con barra de controles y layout."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from simulator import OSSimulator

from ui.scenario import populate_demo_processes
from ui.widgets import EventLogFrame, ReadyRingFrame


class SimulatorApp:
    """Aplicación Tkinter: reloj simulado, paso a paso y reinicio."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        root.title("Simulador OS — Planificador RR + I/O")
        root.geometry("1200x720")
        root.minsize(960, 600)

        self._pcb_capacity = 32
        self._auto_job: Optional[str] = None
        self._speed_ms = 250

        toolbar = ttk.Frame(root, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self._clock_var = tk.StringVar(value="Reloj: 0")
        ttk.Label(toolbar, textvariable=self._clock_var, width=14).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(toolbar, text="Step", command=self._on_step).pack(side=tk.LEFT, padx=2)
        self._run_btn = ttk.Button(toolbar, text="Run", command=self._toggle_auto)
        self._run_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self._on_reset).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Label(toolbar, text="Quantum:").pack(side=tk.LEFT)
        self._quantum_var = tk.IntVar(value=4)
        self._quantum_spin = ttk.Spinbox(
            toolbar,
            from_=1,
            to=32,
            width=4,
            textvariable=self._quantum_var,
        )
        self._quantum_spin.pack(side=tk.LEFT, padx=4)

        upper = ttk.Frame(root, padding=(6, 0))
        upper.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._pcb_placeholder = ttk.LabelFrame(upper, text="Tabla PCB", padding=8)
        self._pcb_placeholder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        ttk.Label(self._pcb_placeholder, text="(panel PCB — pendiente)").pack(anchor=tk.W)

        self._rr_placeholder = ttk.LabelFrame(upper, text="Anillo Round Robin", padding=4)
        self._rr_placeholder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self._rr_panel = ReadyRingFrame(self._rr_placeholder)
        self._rr_panel.pack(fill=tk.BOTH, expand=True)

        self._io_placeholder = ttk.LabelFrame(upper, text="Dispositivos I/O", padding=8)
        self._io_placeholder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        ttk.Label(self._io_placeholder, text="(panel I/O — pendiente)").pack(anchor=tk.W)

        log_frame = ttk.LabelFrame(root, text="Log de eventos", padding=6)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)
        self._log_panel = EventLogFrame(log_frame)
        self._log_panel.pack(fill=tk.BOTH, expand=True)

        self._kernel = self._build_kernel()
        self._update_clock_title()
        self._rr_panel._canvas.bind("<Configure>", self._on_rr_resize)
        self._refresh_panels()

    def _on_rr_resize(self, _evt: tk.Event) -> None:
        self._rr_panel.refresh(
            self._kernel.scheduler_gate.walk_ready_ring(),
            self._kernel.scheduler_gate.current_process(),
        )

    def _build_kernel(self) -> OSSimulator:
        q = int(self._quantum_var.get())
        kernel = OSSimulator(pcb_capacity=self._pcb_capacity, default_quantum=q, verbosity=False)
        populate_demo_processes(kernel)
        return kernel

    def _on_reset(self) -> None:
        self._stop_auto()
        self._kernel = self._build_kernel()
        self._log_panel.reset()
        self._update_clock_title()
        self._refresh_panels()

    def _on_step(self) -> None:
        self._kernel.tick()
        self._update_clock_title()
        self._refresh_panels()

    def _toggle_auto(self) -> None:
        if self._auto_job is not None:
            self._stop_auto()
        else:
            self._run_btn.configure(text="Pause")
            self._schedule_auto_tick()

    def _schedule_auto_tick(self) -> None:
        self._on_step()
        self._auto_job = self._root.after(self._speed_ms, self._auto_tick)

    def _auto_tick(self) -> None:
        if self._auto_job is None:
            return
        self._auto_job = None
        self._schedule_auto_tick()

    def _stop_auto(self) -> None:
        if self._auto_job is not None:
            self._root.after_cancel(self._auto_job)
            self._auto_job = None
        self._run_btn.configure(text="Run")

    def _update_clock_title(self) -> None:
        self._clock_var.set(f"Reloj: {self._kernel.clock}")

    def _refresh_panels(self) -> None:
        self._rr_panel.refresh(
            self._kernel.scheduler_gate.walk_ready_ring(),
            self._kernel.scheduler_gate.current_process(),
        )
        self._log_panel.refresh_from_records(self._kernel.trace_sink().records)

    @property
    def root(self) -> tk.Tk:
        return self._root

    @property
    def kernel(self) -> OSSimulator:
        return self._kernel
