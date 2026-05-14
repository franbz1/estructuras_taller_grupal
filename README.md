# OS Process Scheduler Simulator

Educational simulator of process scheduling inside a multitasking-like kernel toy model.

It exercises four custom-built data structures:

- **Fixed array (`PCBTable`)** — \(O(1)\) PCB lookup by PID
- **Doubly-linked circular list** — ready queue used for Round-Robin traversal
- **Stack (`CallStack`)** — modeled per-process activation records / syscall nesting
- **Linked queue (`IOQueue`)** — FIFO wait lists for device drivers

Language: Python 3.10+. All source code identifiers and comments are in English.

Run the demo:

```bash
python main.py
```

Graphical UI (Tkinter, standard library):

```bash
python ui_main.py
```

## Package layout

- `data_structures/` — custom ADT implementations used by higher layers.
- `models/` — domain objects (`Process`, `IODevice`, enums).
- `simulator/` — scheduling, I/O subsystems and top-level simulator.
- `utils/` — structured logging helpers.
- `ui/` — Tkinter front-end for live PCB, RR ring, I/O queues and event log.

## Collaboration workflow

Course commits rotate authorship with `git -c user.name=... -c user.email=...` so each teammate appears in history while leaving code and identifiers in English.

