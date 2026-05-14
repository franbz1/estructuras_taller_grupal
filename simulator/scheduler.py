"""Round Robin façade built on top of custom circular doubly linked lists."""

from __future__ import annotations

from typing import Callable, Iterator, Optional

from data_structures.circular_list import DoubleCircularLinkedList
from models.process import Process, ProcessState


class RoundRobinScheduler:
    """Maintains READY workloads and rotates the RR cursor each quantum expiry."""

    __slots__ = ("_quantum", "_ready_ring")

    def __init__(self, quantum: int):
        if quantum <= 0:
            raise ValueError("Quantum slices must remain positive integers")
        self._quantum = quantum
        self._ready_ring = DoubleCircularLinkedList[Process](
            priority_key=lambda runnable: runnable.priority,
        )

    def __len__(self) -> int:
        """How many READY processes currently hang off the RR ring."""

        return len(self._ready_ring)

    @property
    def quantum(self) -> int:
        return self._quantum

    def is_idle(self) -> bool:
        return self._ready_ring.is_empty()

    def current_process(self) -> Optional[Process]:
        return self._ready_ring.current()

    def enqueue_ready(self, process: Process) -> None:
        if process.state == ProcessState.TERMINATED:
            raise RuntimeError("Cannot schedule terminated workloads")
        process.mark_ready()
        process.reset_quantum_slice(self.quantum)
        self._ready_ring.insert_by_priority(process)

    def rotate_scheduler_pointer(self) -> Optional[Process]:
        """Moves the RR cursor one slot forward."""
        return self._ready_ring.advance()

    def dequeue_matching(self, predicate: Callable[[Process], bool]) -> Optional[Process]:
        """Detach whichever READY node fulfills `predicate`."""
        return self._ready_ring.remove_matching(predicate)

    def walk_ready_ring(self) -> Iterator[Process]:
        """Read-only traversal starting at RR cursor."""

        yield from self._ready_ring.walk_from_current()
