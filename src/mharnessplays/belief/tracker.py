from __future__ import annotations

from collections import deque

from mharnessplays.belief.transition_suspender import TransitionSuspender
from mharnessplays.contracts import BeliefState, PerceptionObservation

LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "OVERWORLD": {"OVERWORLD", "MENU", "DIALOGUE", "TRANSITION", "BATTLE"},
    "MENU": {"MENU", "OVERWORLD", "TRANSITION"},
    "DIALOGUE": {"DIALOGUE", "OVERWORLD", "TRANSITION"},
    "BATTLE": {"BATTLE", "MENU", "TRANSITION", "OVERWORLD"},
    "TRANSITION": {"TRANSITION", "OVERWORLD", "MENU", "BATTLE", "DIALOGUE"},
}


class BeliefTracker:
    def __init__(self, confidence_threshold: float = 0.7, smoothing_window: int = 3) -> None:
        self._confidence_threshold = confidence_threshold
        self._history: deque[str] = deque(maxlen=smoothing_window)
        self._last_state = "OVERWORLD"
        self._suspender = TransitionSuspender()

    def update(self, obs: PerceptionObservation) -> BeliefState:
        self._suspender.update(obs)
        proposed = obs.scene_class
        self._history.append(proposed)
        smoothed = max(set(self._history), key=self._history.count)

        uncertain = obs.scene_confidence < self._confidence_threshold
        if smoothed not in LEGAL_TRANSITIONS.get(self._last_state, {smoothed}):
            uncertain = True
            smoothed = self._last_state
        else:
            self._last_state = smoothed

        return BeliefState(
            frame_id=obs.frame_id,
            tick=obs.tick,
            game_state=smoothed,
            game_state_confidence=obs.scene_confidence,
            position_estimate=None,
            position_confidence=0.0,
            menu_context=obs.ui_state if obs.ui_state.get("menu_detected") else None,
            battle_context={} if smoothed == "BATTLE" else None,
            text_context={"text": obs.text} if obs.text else None,
            uncertain=uncertain,
            suspended=self._suspender.should_suspend(obs),
        )
