from __future__ import annotations

from mharnessplays.contracts import Frame


class SceneClassifierStub:
    """Simple pixel-statistics scene classifier for bootstrap tests."""

    def classify(self, frame: Frame) -> tuple[str, float]:
        if not frame.pixels:
            return "UNKNOWN", 0.0
        mean = sum(frame.pixels) / len(frame.pixels)
        if mean < 40:
            return "BATTLE", 0.8
        if mean < 90:
            return "OVERWORLD", 0.8
        if mean < 170:
            return "MENU", 0.8
        if mean < 240:
            return "DIALOGUE", 0.75
        return "TRANSITION", 0.9
