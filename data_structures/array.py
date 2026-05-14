"""Fixed-size PCB table backed by positional slots (Python list as array)."""


from typing import Iterable, Iterator, Optional, Protocol


class _HasPidAndName(Protocol):
    pid: int
    name: str


class PCBFullError(RuntimeError):
    """Raised when the PCB array cannot allocate another PID."""


class PCBTable:
    """
    Tracks every process descriptor in contiguous slots keyed by PID for O(1) access.

    The underlying storage is modeled as an array-like structure sized at construction time.
    `pid` doubles as index into `_slots`.
    """

    __slots__ = ("_size", "_slots")

    def __init__(self, max_processes: int) -> None:
        if max_processes <= 0:
            raise ValueError("max_processes must be positive")
        self._size = max_processes
        self._slots: list[Optional[_HasPidAndName]] = [None] * max_processes

    @property
    def capacity(self) -> int:
        return self._size

    def add_process(self, process: _HasPidAndName) -> int:
        """Registers `process`; returns PID index."""
        moniker = getattr(process, "name", None)
        if not isinstance(moniker, str) or not moniker.strip():
            raise ValueError("PCB requires non-empty textual process names")

        pid = process.pid
        if pid < 0 or pid >= self._size:
            raise ValueError("process.pid is outside PCB capacity")
        if self._slots[pid] is not None:
            raise PCBFullError(f"PCB slot {pid} is already occupied")
        self._slots[pid] = process
        return pid

    def remove_process(self, pid: int) -> None:
        """Clears PCB slot."""
        self._validate_pid(pid)
        self._slots[pid] = None

    def get_process(self, pid: int) -> _HasPidAndName:
        self._validate_pid(pid)
        entry = self._slots[pid]
        if entry is None:
            raise KeyError(pid)
        return entry

    def update_slot(self, process: _HasPidAndName) -> None:
        """Ensures PCB slot references the authoritative object instance."""
        pid = process.pid
        self._validate_pid(pid)
        self._slots[pid] = process

    def is_slot_free(self, pid: int) -> bool:
        self._validate_pid(pid)
        return self._slots[pid] is None

    def occupied_pids(self) -> Iterator[int]:
        for idx in range(self._size):
            if self._slots[idx] is not None:
                yield idx

    def first_available_slot(self) -> Optional[int]:
        """Returns the smallest free PID/index or None if saturated."""
        for idx in range(self._size):
            if self._slots[idx] is None:
                return idx
        return None

    def all_registered(self) -> Iterable[_HasPidAndName]:
        for idx in range(self._size):
            proc = self._slots[idx]
            if proc is not None:
                yield proc

    def _validate_pid(self, pid: int) -> None:
        if pid < 0 or pid >= self._size:
            raise ValueError("pid outside PCB boundaries")
