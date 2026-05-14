"""Call stack abstraction used to model syscall / procedure nesting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(slots=True)
class StackFrame:
    """Minimal activation record used for demonstration purposes."""

    function_name: str
    return_address: int = 0
    local_scope: Dict[str, Any] = field(default_factory=dict)


class EmptyStackError(IndexError):
    """Raised on illegal pop/peek operations."""


class CallStack:
    """
    Lightweight stack modeled with a contiguous buffer (behaves like a hardware stack).

    The educational goal is separating per-process stacks from global scheduler state.
    """

    __slots__ = ("_capacity", "_frames")

    def __init__(self, capacity: Optional[int] = None) -> None:
        self._capacity = capacity
        self._frames: list[StackFrame] = []

    def push(self, frame: StackFrame) -> None:
        if self._capacity is not None and len(self._frames) >= self._capacity:
            raise RuntimeError("call stack overflow (capacity exceeded)")
        self._frames.append(frame)

    def pop(self) -> StackFrame:
        if not self._frames:
            raise EmptyStackError("pop from empty call stack")
        return self._frames.pop()

    def peek(self) -> StackFrame:
        if not self._frames:
            raise EmptyStackError("peek on empty call stack")
        return self._frames[-1]

    def is_empty(self) -> bool:
        return len(self._frames) == 0

    def size(self) -> int:
        return len(self._frames)

    def snapshot(self) -> tuple[str, ...]:
        """Return shallow tuple of callee names for diagnostics."""
        return tuple(frame.function_name for frame in self._frames)
