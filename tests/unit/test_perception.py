from __future__ import annotations

from mharnessplays.contracts import Frame
from mharnessplays.perception.frame_differencer import FrameDifferencer
from mharnessplays.perception.perceptor import Perceptor
from mharnessplays.perception.tile_hasher import TileHasher


def _frame(frame_id: int, tick: int, value: int) -> Frame:
    return Frame(
        frame_id=frame_id,
        tick=tick,
        timestamp_ms=tick * 16,
        width=8,
        height=8,
        pixels=bytes([value] * 64),
    )


def test_tile_hash_stability() -> None:
    hasher = TileHasher()
    frame = _frame(1, 1, 12)
    assert hasher.hash_frame(frame) == hasher.hash_frame(frame)


def test_frame_differencing() -> None:
    differencer = FrameDifferencer()
    a = _frame(1, 1, 0)
    b = _frame(2, 2, 255)
    assert differencer.delta_ratio(a, b) == 1.0


def test_perceptor_confidence_and_transition() -> None:
    perceptor = Perceptor(transition_threshold=0.2)
    first = _frame(1, 1, 10)
    second = _frame(2, 2, 250)
    _ = perceptor.observe(first)
    obs = perceptor.observe(second)
    assert obs.scene_confidence > 0
    assert obs.transition_detected is True
