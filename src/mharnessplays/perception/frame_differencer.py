from __future__ import annotations

from mharnessplays.contracts import Frame


class FrameDifferencer:
    def delta_ratio(self, previous: Frame, current: Frame) -> float:
        if previous.width != current.width or previous.height != current.height:
            raise ValueError("frame dimensions must match")
        if len(previous.pixels) != len(current.pixels):
            raise ValueError("pixel lengths must match")
        if not previous.pixels:
            return 0.0
        changed = sum(a != b for a, b in zip(previous.pixels, current.pixels, strict=True))
        return changed / len(previous.pixels)
