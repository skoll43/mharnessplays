from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategicDirective:
    directive_id: str
    goal: str
    priority: int
    target_node: str | None
    constraints: dict
    issued_at_tick: int


class StrategistStub:
    def choose(self, tick: int) -> StrategicDirective:
        return StrategicDirective(
            directive_id=f"d-{tick}",
            goal="HEAL_AND_HOLD",
            priority=1,
            target_node=None,
            constraints={"heal_before_departure": True},
            issued_at_tick=tick,
        )
