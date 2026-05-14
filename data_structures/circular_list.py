"""Doubly linked circular list modelling the ready-queue ring used by RR."""

from __future__ import annotations

from typing import Callable, Iterator, Optional, Generic, TypeVar


T = TypeVar("T")


class Node(Generic[T]):
    """Node holding payload plus prev/next neighbours on the circular ring."""

    __slots__ = ("data", "prev", "next")

    def __init__(self, data: T) -> None:
        self.data = data
        self.prev: Optional[Node[T]] = None
        self.next: Optional[Node[T]] = None


class DoubleCircularLinkedList(Generic[T]):
    """
    Implements a cyclic doubly linked list oriented around `_current`.

    Round-Robin rotates `_current`; priority inserts splice the ring preserving a
    local ordering rule expressed via `priority_key`.
    """

    __slots__ = ("_current", "_length", "_priority_key")

    def __init__(
        self,
        priority_key: Callable[[T], int],
    ) -> None:
        self._priority_key = priority_key
        self._current: Optional[Node[T]] = None
        self._length: int = 0

    # ---------------------------------------------------------------- bookkeeping
    def __len__(self) -> int:
        return self._length

    def is_empty(self) -> bool:
        return self._current is None or self._length == 0

    # ---------------------------------------------------------------- accessors
    def current(self) -> Optional[T]:
        if self.is_empty():
            return None
        assert self._current is not None
        return self._current.data

    def advance(self) -> Optional[T]:
        """Advance pointer to successor and return underlying payload."""
        if self.is_empty():
            return None
        assert self._current is not None
        self._current = self._current.next
        return self.current()

    # ---------------------------------------------------------------- mutations
    def insert_by_priority(self, value: T) -> None:
        """Insert respecting descending priority travelling forward."""
        node = Node(value)

        if self.is_empty():
            node.next = node.prev = node
            self._current = node
            self._length = 1
            return

        assert self._current is not None
        prio = self._priority_key(value)

        if self._length == 1:
            incumbent = self._current
            assert incumbent is not None
            newcomer = node
            inc_prio = self._priority_key(incumbent.data)
            if prio > inc_prio:
                self._wire_pair(newcomer, incumbent)
            else:
                self._wire_pair(incumbent, newcomer)
            self._length = 2
            return

        scout: Node[T] = self._current
        for _ in range(self._length):
            successor = scout.next
            assert successor is not None
            if self._priority_key(successor.data) < prio:
                self._insert_before(successor, node)
                self._length += 1
                return
            scout = successor

        successor = scout.next  # unwrap after lap
        assert successor is not None
        self._insert_before(successor, node)
        self._length += 1

    def remove_matching(self, predicate: Callable[[T], bool]) -> Optional[T]:
        """Remove node matching predicate updating `_current` coherently."""
        if self.is_empty():
            return None

        assert self._current is not None
        cursor: Optional[Node[T]] = self._current
        for _ in range(self._length):
            assert cursor is not None
            if predicate(cursor.data):
                return self._extract_node(cursor)
            cursor = cursor.next
        return None

    def walk_from_current(self) -> Iterator[T]:
        """Yield payloads starting at `_current` including all nodes."""
        if self.is_empty():
            return
        start = self._current
        assert start is not None
        yield start.data
        walker = start.next
        while walker is not start:
            yield walker.data
            walker = walker.next  # type: ignore[assignment]

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _wire_pair(first: Node[T], second: Node[T]) -> None:
        """Links two mutually adjacent nodes preserving circularity."""
        first.next = second
        second.prev = first
        second.next = first
        first.prev = second

    @staticmethod
    def _insert_before(successor: Node[T], newcomer: Node[T]) -> None:
        predecessor = successor.prev
        assert predecessor is not None
        predecessor.next = newcomer
        newcomer.prev = predecessor
        newcomer.next = successor
        successor.prev = newcomer

    def _extract_node(self, node: Node[T]) -> T:
        payload = node.data

        predecessor = node.prev
        successor = node.next
        assert predecessor is not None and successor is not None

        if self._length == 1:
            self._clear()
            return payload

        predecessor.next = successor
        successor.prev = predecessor

        if node is self._current:
            self._current = successor

        node.prev = node.next = None  # unlink for GC ergonomics

        self._length -= 1
        return payload

    def _clear(self) -> None:
        self._current = None
        self._length = 0
