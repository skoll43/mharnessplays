from __future__ import annotations

from mharnessplays.belief.tracker import BeliefTracker
from mharnessplays.control.deliberator_stub import DeliberatorStub
from mharnessplays.emulator.gateway import EmulatorGateway
from mharnessplays.execution.effector import VisualServoingEffector
from mharnessplays.perception.perceptor import Perceptor
from mharnessplays.safety.action_validator import ActionValidator


class RuntimeHypervisor:
    def __init__(self) -> None:
        self.gateway = EmulatorGateway()
        self.perceptor = Perceptor()
        self.belief = BeliefTracker()
        self.deliberator = DeliberatorStub()
        self.validator = ActionValidator()
        self.effector = VisualServoingEffector(self.gateway)

    def run_tick(self) -> None:
        frame = self.gateway.step()
        obs = self.perceptor.observe(frame)
        belief = self.belief.update(obs)
        proposal = self.deliberator.propose(belief)
        validation = self.validator.validate(proposal, belief)
        if validation.allowed:
            primitive = validation.downgraded_to or proposal.primitive
            if primitive != proposal.primitive:
                proposal = proposal.__class__(
                    action_id=proposal.action_id,
                    actor=proposal.actor,
                    primitive=primitive,
                    params=proposal.params,
                    preconditions=proposal.preconditions,
                    cancel_on=proposal.cancel_on,
                    ttl_ticks=proposal.ttl_ticks,
                )
            self.effector.execute(proposal, expected_min_delta=0.0)

    def run_ticks(self, count: int) -> None:
        for _ in range(count):
            self.run_tick()
