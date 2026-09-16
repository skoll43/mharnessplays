from __future__ import annotations

from dataclasses import dataclass

from mharnessplays.contracts import Frame


@dataclass(frozen=True)
class StateRef:
    name: str
    tick: int


class EmulatorGateway:
    """Deterministic emulator gateway stub for bootstrap."""

    def __init__(self, width: int = 8, height: int = 8) -> None:
        self._tick = 0
        self._frame_id = 0
        self._width = width
        self._height = height
        self._last_input_mask = 0
        self._state_store: dict[str, tuple[int, int]] = {}

    def step(self) -> Frame:
        self._tick += 1
        self._frame_id += 1
        intensity = (self._frame_id + self._last_input_mask) % 256
        pixels = bytes([intensity] * (self._width * self._height))
        return Frame(
            frame_id=self._frame_id,
            tick=self._tick,
            timestamp_ms=self._tick * 16,
            width=self._width,
            height=self._height,
            pixels=pixels,
        )

    def send_input(self, input_mask: int) -> None:
        self._last_input_mask = input_mask

    def save_state(self, name: str) -> StateRef:
        self._state_store[name] = (self._tick, self._frame_id)
        return StateRef(name=name, tick=self._tick)

    def load_state(self, ref: StateRef) -> None:
        tick, frame_id = self._state_store[ref.name]
        self._tick = tick
        self._frame_id = frame_id

    def get_tick(self) -> int:
        return self._tick
