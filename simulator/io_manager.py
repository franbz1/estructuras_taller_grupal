"""Multiplex orchestration wrapping every mocked IODevice."""

from __future__ import annotations

from typing import Iterable, List, Mapping, MutableMapping, Optional

from models.io_device import IODevice, IODeviceType, coerce_device_token


class IOManager:
    """Bundles several devices and multiplexes completions back to OSSimulator."""

    __slots__ = ("_devices",)

    def __init__(self, devices: Optional[Iterable[IODeviceType]] = None) -> None:
        iterable = tuple(devices) if devices else tuple(IODeviceType)
        self._devices: MutableMapping[IODeviceType, IODevice] = {dtype: IODevice(dtype) for dtype in iterable}

    def devices_snapshot(self) -> Mapping[IODeviceType, IODevice]:
        return self._devices

    def enqueue_blocked_operation(self, process, device_keyword: str) -> None:
        resolved = coerce_device_token(device_keyword)
        self._devices[resolved].enqueue_blocked(process)

    def request_io(self, process, device_type: object) -> None:
        """Enqueue a syscall according to textual or enum-backed device selectors."""
        label = getattr(device_type, "name", str(device_type))
        self.enqueue_blocked_operation(process, label)

    def tick(self) -> List[object]:
        """OSSimulator-visible hook aligning with pedagogical sequencing diagrams."""
        return self.clock_blocking_layer()

    def clock_blocking_layer(self) -> List[object]:
        """Advance every device concurrently and flatten completions."""
        completed: List[object] = []
        for bridge in self._devices.values():
            finished = bridge.tick()
            if finished is not None:
                completed.append(finished)
        return completed
