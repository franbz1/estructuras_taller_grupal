"""Paneles de visualización del simulador OS (incremental)."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Iterable, Optional, Sequence

from models.io_device import IODeviceType
from models.process import Process, ProcessState
from simulator import OSSimulator


class PCBTableFrame(ttk.Frame):
    """Tabla Treeview con estado de cada proceso registrado."""

    def __init__(self, parent: tk.Misc, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        cols = ("pid", "name", "pri", "state", "cpu_rem", "q_rem")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        headings = {
            "pid": "PID",
            "name": "Nombre",
            "pri": "Pri",
            "state": "Estado",
            "cpu_rem": "CPU rest.",
            "q_rem": "Quantum",
        }
        widths = {"pid": 44, "name": 120, "pri": 40, "state": 88, "cpu_rem": 72, "q_rem": 64}
        for cid in cols:
            self._tree.heading(cid, text=headings[cid])
            self._tree.column(cid, width=widths[cid], stretch=True)

        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for tag, fg in (
            ("ready", "#58a6ff"),
            ("running", "#3fb950"),
            ("blocked", "#d29922"),
            ("terminated", "#8b949e"),
        ):
            self._tree.tag_configure(tag, foreground=fg)

    def refresh(self, registry: Sequence[Process]) -> None:
        self._tree.delete(*self._tree.get_children())
        for proc in sorted(registry, key=lambda p: p.pid):
            state = proc.state.name
            tag = proc.state.name.lower()
            vals = (
                proc.pid,
                proc.name,
                proc.priority,
                state,
                proc.cpu_burst_remaining,
                proc.quantum_remaining,
            )
            self._tree.insert("", tk.END, values=vals, tags=(tag,))


class ReadyRingFrame(ttk.Frame):
    """Dibujo del anillo Round Robin en un lienzo."""

    def __init__(self, parent: tk.Misc, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self._canvas = tk.Canvas(self, highlightthickness=0, width=340, height=320)
        self._canvas.pack(fill=tk.BOTH, expand=True)

    def refresh(self, scheduler_nodes: Iterable[Process], current: Optional[Process]) -> None:
        c = self._canvas
        c.delete("all")
        w = int(c.winfo_width() or 340)
        h = int(c.winfo_height() or 320)
        c.configure(background="#0d1117")

        nodes = list(scheduler_nodes)
        n = len(nodes)
        if n == 0:
            c.create_text(
                w // 2,
                h // 2,
                text="Anillo vacío (idle)",
                fill="#8b949e",
                font=("Segoe UI", 11),
            )
            return

        cx, cy = w / 2, h / 2
        ring_r = min(w, h) * 0.36
        node_r = max(22, min(32, int(220 / max(n, 1))))

        positions: list[tuple[float, float]] = []
        for i in range(n):
            angle = (2 * math.pi * i) / n - math.pi / 2
            x = cx + ring_r * math.cos(angle)
            y = cy + ring_r * math.sin(angle)
            positions.append((x, y))

        for i in range(n):
            x0, y0 = positions[i]
            x1, y1 = positions[(i + 1) % n]
            c.create_line(x0, y0, x1, y1, fill="#30363d", width=2)

        for proc, (x, y) in zip(nodes, positions):
            is_current = current is not None and proc.pid == current.pid
            outline = "#f85149" if is_current else "#58a6ff"
            width_o = 4 if is_current else 2
            c.create_oval(
                x - node_r,
                y - node_r,
                x + node_r,
                y + node_r,
                fill="#161b22",
                outline=outline,
                width=width_o,
            )
            c.create_text(
                x,
                y - 8,
                text=str(proc.pid),
                fill="#f0f6fc",
                font=("Segoe UI Semibold", 10),
            )
            short = proc.name if len(proc.name) <= 10 else proc.name[:9] + "…"
            c.create_text(x, y + 10, text=short, fill="#8b949e", font=("Segoe UI", 8))


class IODevicesFrame(ttk.Frame):
    """Vista de colas por dispositivo I/O simulado."""

    def __init__(self, parent: tk.Misc, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self._text = tk.Text(
            self,
            height=14,
            width=36,
            wrap=tk.WORD,
            font=("Consolas", 10),
            relief=tk.FLAT,
            borderwidth=0,
            background="#0d1117",
            foreground="#c9d1d9",
            insertbackground="#ffffff",
        )
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=scroll.set, state=tk.DISABLED)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self, kernel: OSSimulator) -> None:
        snapshot = kernel.io_plane.devices_snapshot()
        registry: list[Process] = list(kernel._registry)
        lines: list[str] = []

        for dtype in (IODeviceType.DISK, IODeviceType.NETWORK, IODeviceType.PRINTER):
            dev = snapshot[dtype]
            backlog = dev.backlog_len()
            blocked_pids = sorted(
                p.pid
                for p in registry
                if p.state == ProcessState.BLOCKED
                and p.pending_io_keyword is not None
                and p.pending_io_keyword.upper() == dtype.name
            )
            pid_str = ", ".join(str(pid) for pid in blocked_pids) or "—"
            lines.append(f"▸ {dtype.name}  (cola: {backlog})")
            lines.append(f"   PIDs bloqueados: {pid_str}")
            lines.append("")

        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert(tk.END, "\n".join(lines).rstrip() + "\n")
        self._text.configure(state=tk.DISABLED)


class EventLogFrame(ttk.Frame):
    """Registro coloreado de eventos del SimulatorLogger."""

    _MAX_LINES = 200

    def __init__(self, parent: tk.Misc, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self._next_index = 0
        self._text = tk.Text(
            self,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 10),
            relief=tk.FLAT,
            borderwidth=0,
            background="#0d1117",
            foreground="#c9d1d9",
            insertbackground="#ffffff",
        )
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=scroll.set)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        palette = {
            "rr": "#56d4dd",
            "syscall": "#e3b341",
            "done": "#3fb950",
            "fault": "#f85149",
            "lifecycle": "#f0f6fc",
            "cpu": "#a371f7",
            "wakeup": "#79c0ff",
            "burst": "#8b949e",
        }
        self._text.tag_configure("default", foreground="#c9d1d9")
        for name, color in palette.items():
            self._text.tag_configure(name, foreground=color)

    def _tag_for_line(self, line: str) -> str:
        if line.startswith("[") and "]" in line:
            label_chunk = line[1 : line.index("]")].strip().lower()
            first = label_chunk.split()[0] if label_chunk else ""
            for key in (
                "rr",
                "syscall",
                "done",
                "fault",
                "lifecycle",
                "cpu",
                "wakeup",
                "burst",
            ):
                if first.startswith(key):
                    return key
        return "default"

    def refresh_from_records(self, records: Sequence[str]) -> None:
        if self._next_index >= len(records):
            return
        new_chunk = records[self._next_index :]
        self._next_index = len(records)

        self._text.configure(state=tk.NORMAL)
        for line in new_chunk:
            tag = self._tag_for_line(line)
            self._text.insert(tk.END, line + "\n", (tag,))

        total_lines = int(self._text.index("end-1c").split(".")[0])
        if total_lines > self._MAX_LINES:
            trim = total_lines - self._MAX_LINES
            self._text.delete("1.0", f"{trim + 1}.0")
        self._text.see(tk.END)
        self._text.configure(state=tk.DISABLED)

    def reset(self) -> None:
        self._next_index = 0
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)


class ReportWindow(tk.Toplevel):
    """Ventana modal con el resultado de `generate_report()`."""

    def __init__(self, parent: tk.Misc, report: dict[str, object]) -> None:
        super().__init__(parent)
        self.title("Reporte del simulador")
        self.configure(background="#0d1117")
        self.transient(parent)
        self.grab_set()

        txt = tk.Text(
            self,
            width=82,
            height=26,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#161b22",
            foreground="#f0f6fc",
            insertbackground="#f0f6fc",
            relief=tk.FLAT,
        )
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for key, value in report.items():
            txt.insert(tk.END, f"{key}: {value}\n")
        txt.configure(state=tk.DISABLED)

        ttk.Button(self, text="Cerrar", command=self.destroy).pack(pady=(0, 8))

