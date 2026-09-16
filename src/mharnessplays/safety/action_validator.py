from __future__ import annotations

from mharnessplays.contracts import ActionProposal, BeliefState, ValidationResult

ALLOWED_PRIMITIVES = {
    "NAVIGATE",
    "INTERACT",
    "OPEN_MENU",
    "CLOSE_MENU",
    "SELECT_MENU_ITEM",
    "USE_ITEM",
    "USE_MOVE",
    "SWITCH_CHARACTER",
    "RUN_AWAY",
    "ADVANCE_TEXT",
    "WAIT",
    "SAFE_PAUSE",
}


class ActionValidator:
    def validate(self, action: ActionProposal, belief: BeliefState) -> ValidationResult:
        if action.primitive not in ALLOWED_PRIMITIVES:
            return ValidationResult(action.action_id, False, None, "invalid primitive")
        if belief.suspended:
            return ValidationResult(action.action_id, False, None, "transition suspension active")
        if belief.uncertain and action.primitive not in {"SAFE_PAUSE", "WAIT"}:
            return ValidationResult(action.action_id, True, "SAFE_PAUSE", "belief uncertainty")
        if belief.game_state == "BATTLE" and action.primitive == "NAVIGATE":
            return ValidationResult(action.action_id, False, None, "NAVIGATE illegal in battle")
        return ValidationResult(action.action_id, True, None, None)
