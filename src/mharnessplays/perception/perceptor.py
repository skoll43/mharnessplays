from __future__ import annotations

from mharnessplays.contracts import Frame, PerceptionObservation
from mharnessplays.perception.frame_differencer import FrameDifferencer
from mharnessplays.perception.scene_classifier_stub import SceneClassifierStub
from mharnessplays.perception.tile_hasher import TileHasher


class Perceptor:
    def __init__(self, transition_threshold: float = 0.35) -> None:
        self._hasher = TileHasher()
        self._differencer = FrameDifferencer()
        self._classifier = SceneClassifierStub()
        self._transition_threshold = transition_threshold
        self._last_frame: Frame | None = None

    def observe(self, frame: Frame) -> PerceptionObservation:
        scene_class, scene_confidence = self._classifier.classify(frame)
        if self._last_frame is None:
            delta = 0.0
        else:
            delta = self._differencer.delta_ratio(self._last_frame, frame)
        transition_detected = delta >= self._transition_threshold or scene_class == "TRANSITION"
        text = "..." if scene_class == "DIALOGUE" else None
        text_conf = 0.8 if text else 0.0
        ui_state = {
            "menu_detected": scene_class == "MENU",
            "text_box_detected": scene_class == "DIALOGUE",
            "tile_hash": self._hasher.hash_frame(frame),
        }
        obs = PerceptionObservation(
            frame_id=frame.frame_id,
            tick=frame.tick,
            scene_class=scene_class,
            scene_confidence=scene_confidence,
            ui_state=ui_state,
            text=text,
            text_confidence=text_conf,
            visual_delta=delta,
            transition_detected=transition_detected,
            diagnostics={"pixel_only": True},
        )
        self._last_frame = frame
        return obs
