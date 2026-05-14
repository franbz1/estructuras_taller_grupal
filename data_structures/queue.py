"""FIFO queue backing each I/O device's wait channel."""

from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar


T = TypeVar("T")


class _QNode(Generic[T]):
    __slots__ = ("data", "next")

    def __init__(self, data: T, next_: Optional["_QNode[T]"] = None) -> None:
        self.data = data
        self.next = next_


class IOQueue(Generic[T]):
    """Classic singly-linked queue with FIFO ordering."""

    __slots__ = ("_head", "_tail", "_length")

    def __init__(self) -> None:
        self._head: Optional[_QNode[T]] = None
        self._tail: Optional[_QNode[T]] = None
        self._length = 0

    def __len__(self) -> int:
        return self._length

    def is_empty(self) -> bool:
        return self._head is None

    def enqueue(self, item: T) -> None:
        node = _QNode(item)
        if self._tail is None:
            self._head = self._tail = node
        else:
            self._tail.next = node  # type: ignore[attr-defined]
            self._tail = node
        self._length += 1

    def dequeue(self) -> T:
        if self._head is None:
            raise IndexError("dequeue from empty IOQueue")
        head = self._head
        self._head = head.next
        if self._head is None:
            self._tail = None
        self._length -= 1
        head.next = None
        return head.data

    def peek(self) -> T:
        if self._head is None:
            raise IndexError("peek on empty IOQueue")
        return self._head.data

    def iterate(self) -> Iterator[T]:
        cursor = self._head
        while cursor is not None:
            yield cursor.data
            cursor = cursor.next
