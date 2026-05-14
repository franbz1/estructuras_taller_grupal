"""Paneles de visualización del simulador OS (incremental)."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Iterable, Optional

from models.process import Process


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
        c.configure(background="#1e1e1e")

        nodes = list(scheduler_nodes)
        n = len(nodes)
        if n == 0:
            c.create_text(
                w // 2,
                h // 2,
                text="Anillo vacío (idle)",
                fill="#888888",
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
            c.create_line(x0, y0, x1, y1, fill="#444444", width=2)

        for proc, (x, y) in zip(nodes, positions):
            is_current = current is not None and proc.pid == current.pid
            outline = "#ff5555" if is_current else "#4da3ff"
            width_o = 4 if is_current else 2
            c.create_oval(
                x - node_r,
                y - node_r,
                x + node_r,
                y + node_r,
                fill="#2d2d2d",
                outline=outline,
                width=width_o,
            )
            c.create_text(
                x,
                y - 8,
                text=str(proc.pid),
                fill="#ffffff",
                font=("Segoe UI Semibold", 10),
            )
            short = proc.name if len(proc.name) <= 10 else proc.name[:9] + "…"
            c.create_text(x, y + 10, text=short, fill="#aaaaaa", font=("Segoe UI", 8))
