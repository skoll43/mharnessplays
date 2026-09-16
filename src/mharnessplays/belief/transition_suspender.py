from __future__ import annotations

from mharnessplays.contracts import PerceptionObservation


class TransitionSuspender:
    def __init__(self, stable_frames_required: int = 2) -> None:
        self._suspended = False
        self._stable_count = 0
        self._stable_frames_required = stable_frames_required

    def should_suspend(self, obs: PerceptionObservation) -> bool:
        return self._suspended or obs.transition_detected

    def update(self, obs: PerceptionObservation) -> None:
        if obs.transition_detected:
            self._suspended = True
            self._stable_count = 0
            return
        if self._suspended:
            self._stable_count += 1
            if self._stable_count >= self._stable_frames_required:
                self._suspended = False

    @property
    def suspended(self) -> bool:
        return self._suspended
