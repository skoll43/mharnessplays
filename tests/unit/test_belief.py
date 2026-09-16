from __future__ import annotations

from mharnessplays.belief.tracker import BeliefTracker
from mharnessplays.contracts import PerceptionObservation


def _obs(
    frame_id: int,
    tick: int,
    scene: str,
    confidence: float,
    transition: bool = False,
) -> PerceptionObservation:
    return PerceptionObservation(
        frame_id=frame_id,
        tick=tick,
        scene_class=scene,
        scene_confidence=confidence,
        ui_state={},
        text=None,
        text_confidence=0.0,
        visual_delta=0.0,
        transition_detected=transition,
        diagnostics={},
    )


def test_noisy_labels_smoothed() -> None:
    tracker = BeliefTracker(confidence_threshold=0.7, smoothing_window=3)
    tracker.update(_obs(1, 1, "OVERWORLD", 0.9))
    tracker.update(_obs(2, 2, "MENU", 0.9))
    belief = tracker.update(_obs(3, 3, "OVERWORLD", 0.9))
    assert belief.game_state == "OVERWORLD"


def test_invalid_transition_marked_uncertain() -> None:
    tracker = BeliefTracker(confidence_threshold=0.7, smoothing_window=1)
    tracker.update(_obs(1, 1, "OVERWORLD", 0.9))
    belief = tracker.update(_obs(2, 2, "UNKNOWN", 0.9))
    assert belief.uncertain is True


def test_transition_sets_suspended() -> None:
    tracker = BeliefTracker(confidence_threshold=0.7, smoothing_window=1)
    belief = tracker.update(_obs(1, 1, "TRANSITION", 0.9, transition=True))
    assert belief.suspended is True
