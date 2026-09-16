from __future__ import annotations

from mharnessplays.contracts import ActionProposal, BeliefState, EffectorReport
from mharnessplays.emulator.gateway import EmulatorGateway
from mharnessplays.execution.effector import VisualServoingEffector
from mharnessplays.oversight.overseer import Overseer


def _action(primitive: str = "WAIT") -> ActionProposal:
    return ActionProposal("a1", "agent", primitive, {}, {}, [], 10)


def _belief() -> BeliefState:
    return BeliefState(
        frame_id=1,
        tick=1,
        game_state="OVERWORLD",
        game_state_confidence=0.9,
        position_estimate=None,
        position_confidence=0.0,
        menu_context=None,
        battle_context=None,
        text_context=None,
        uncertain=False,
        suspended=False,
    )


def test_effector_reports_failure_and_interrupt() -> None:
    effector = VisualServoingEffector(EmulatorGateway())
    report_failed = effector.execute(_action("WAIT"), expected_min_delta=1.1)
    assert report_failed.status == "FAILED"

    report_interrupt = effector.execute(_action("WAIT"), cancel=True)
    assert report_interrupt.status == "INTERRUPTED"


def test_overseer_incident_on_repeated_failures() -> None:
    overseer = Overseer(max_repeated_failures=2)
    report1 = EffectorReport("a1", "FAILED", 1, 2, {}, {}, "x")
    report2 = EffectorReport("a2", "FAILED", 3, 4, {}, {}, "x")
    overseer.record_action(_action())
    overseer.record_report(report1)
    overseer.record_report(report2)

    assert overseer.should_recover() is True
    incident = overseer.create_incident(_belief(), "loop", "replay_001")
    assert incident.trigger == "loop"
