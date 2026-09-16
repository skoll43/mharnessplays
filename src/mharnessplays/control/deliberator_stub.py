from __future__ import annotations

from mharnessplays.contracts import ActionProposal, BeliefState


class DeliberatorStub:
    def propose(self, belief: BeliefState) -> ActionProposal:
        primitive = "ADVANCE_TEXT" if belief.text_context else "WAIT"
        if belief.uncertain:
            primitive = "SAFE_PAUSE"
        return ActionProposal(
            action_id=f"a-{belief.tick}",
            actor="agent",
            primitive=primitive,
            params={},
            preconditions={"state": belief.game_state},
            cancel_on=["transition"],
            ttl_ticks=10,
        )
