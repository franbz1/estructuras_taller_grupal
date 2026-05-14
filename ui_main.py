"""Punto de entrada de la interfaz gráfica del simulador."""

from __future__ import annotations

import tkinter as tk

from ui.app import SimulatorApp


def main() -> None:
    root = tk.Tk()
    SimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
