"""Lightweight chronological logging for OSSimulator timelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(slots=True)
class SimulatorLogger:
    """Collects textual timelines that students can replay or diff."""

    emit_to_stdout: bool = True
    records: List[str] = field(default_factory=list)
    buckets: Dict[str, int] = field(default_factory=dict)

    def record(self, label: str, message: str) -> None:
        token = f"[{label.upper():<10}] {message}"
        self.records.append(token)
        self.buckets[label] = self.buckets.get(label, 0) + 1
        if self.emit_to_stdout:
            print(token)

    def tail(self, max_lines: int = 48) -> List[str]:
        if max_lines <= 0:
            return []
        start = max(0, len(self.records) - max_lines)
        return self.records[start:]

    def buckets_snapshot(self) -> Dict[str, int]:
        return dict(self.buckets.items())
