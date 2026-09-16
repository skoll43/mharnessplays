from __future__ import annotations

from collections import deque
from datetime import UTC, datetime

from mharnessplays.contracts import ActionProposal, BeliefState, EffectorReport, IncidentPacket


class Overseer:
    def __init__(self, max_repeated_failures: int = 3) -> None:
        self._reports: deque[EffectorReport] = deque(maxlen=max_repeated_failures)
        self._actions: deque[ActionProposal] = deque(maxlen=10)
        self._max_repeated_failures = max_repeated_failures

    def record_action(self, action: ActionProposal) -> None:
        self._actions.append(action)

    def record_report(self, report: EffectorReport) -> None:
        self._reports.append(report)

    def should_recover(self) -> bool:
        if len(self._reports) < self._max_repeated_failures:
            return False
        return all(report.status == "FAILED" for report in self._reports)

    def create_incident(self, belief: BeliefState, trigger: str, replay_ref: str) -> IncidentPacket:
        incident_id = f"incident-{belief.tick}-{len(self._reports)}"
        return IncidentPacket(
            incident_id=incident_id,
            created_at=datetime.now(UTC).isoformat(),
            trigger=trigger,
            belief_state=belief,
            last_actions=list(self._actions),
            last_effector_reports=list(self._reports),
            frame_window_ref="latest_window",
            replay_ref=replay_ref,
            severity="medium",
        )
