from __future__ import annotations

from pathlib import Path

import pytest

from mharnessplays.belief.transition_suspender import TransitionSuspender
from mharnessplays.contracts import ActionProposal, BeliefState, PerceptionObservation
from mharnessplays.meta.pipeline import ProposalPipeline
from mharnessplays.safety.action_validator import ActionValidator


def _belief(
    uncertain: bool = False,
    suspended: bool = False,
    state: str = "OVERWORLD",
) -> BeliefState:
    return BeliefState(
        frame_id=1,
        tick=1,
        game_state=state,
        game_state_confidence=0.9,
        position_estimate=None,
        position_confidence=0.0,
        menu_context=None,
        battle_context=None,
        text_context=None,
        uncertain=uncertain,
        suspended=suspended,
    )


def _action(primitive: str) -> ActionProposal:
    return ActionProposal("a1", "agent", primitive, {}, {}, [], 10)


def test_validator_blocks_invalid_primitive() -> None:
    validator = ActionValidator()
    result = validator.validate(_action("RAW_INPUT"), _belief())
    assert result.allowed is False


def test_validator_downgrades_low_confidence() -> None:
    validator = ActionValidator()
    result = validator.validate(_action("NAVIGATE"), _belief(uncertain=True))
    assert result.allowed is True
    assert result.downgraded_to == "SAFE_PAUSE"


def test_transition_suspender_blocks_input() -> None:
    suspender = TransitionSuspender(stable_frames_required=2)
    obs = PerceptionObservation(1, 1, "TRANSITION", 0.9, {}, None, 0.0, 0.5, True, {})
    suspender.update(obs)
    assert suspender.should_suspend(obs) is True


def test_meta_loop_cannot_hot_patch_bootstrap(tmp_path: Path) -> None:
    pipeline = ProposalPipeline(tmp_path, live_patch_mode=False)
    with pytest.raises(PermissionError):
        pipeline.apply_live_patch(None)  # type: ignore[arg-type]
