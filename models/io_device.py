"""I/O subsystem primitives used by OSSimulator queues."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from data_structures.queue import IOQueue


class IODeviceType(Enum):
    DISK = "disk"
    NETWORK = "network"
    PRINTER = "printer"


_LABEL_MAP: dict[str, IODeviceType] = {}
for variant in IODeviceType:
    _LABEL_MAP[variant.name.upper()] = variant
    _LABEL_MAP[variant.value.upper()] = variant


def coerce_device_token(label: str) -> IODeviceType:
    normalized = label.strip().upper()
    try:
        return _LABEL_MAP[normalized]
    except KeyError as exc:
        raise KeyError(f"Unsupported device `{label}`") from exc


class IODevice:
    """One-at-a-time device serviced through a deterministic FIFO backlog."""

    __slots__ = ("_kind", "_active", "_ticks_left", "_wait")

    def __init__(self, kind: IODeviceType) -> None:
        self._kind = kind
        self._active: Optional[Any] = None
        self._ticks_left = 0
        self._wait: IOQueue[Any] = IOQueue()

    @property
    def kind(self) -> IODeviceType:
        return self._kind

    def backlog_len(self) -> int:
        return len(self._wait) + (1 if self._active is not None else 0)

    def enqueue_blocked(self, process: Any) -> None:
        self._wait.enqueue(process)
        self._kick()

    def _kick(self) -> None:
        if self._active is not None or self._wait.is_empty():
            return

        runner = self._wait.dequeue()
        self._active = runner
        ticks = int(getattr(runner, "pending_io_ticks"))
        if ticks <= 0:
            raise ValueError(f"Pid {runner.pid}: IO duration must be positive")
        self._ticks_left = ticks

    def tick(self) -> Optional[Any]:
        """Plan-facing alias that mirrors OSSimulator nomenclature."""
        return self.advance()

    def advance(self) -> Optional[Any]:
        """Returns whichever workload finished draining this tick."""
        completion: Optional[Any] = None
        if self._active is not None:
            if self._ticks_left > 0:
                self._ticks_left -= 1

            if self._ticks_left == 0:
                completion = self._active
                self._active = None

        self._kick()
        return completion
