from __future__ import annotations

import re
from typing import Any

from .base import LLMHarness
from .types import HarnessReport, LLMContext, LLMResult, ValidatedOutput

_ALLOWED_PRIORITIES = {1, 2, 3, 4, 5}


class StrategistHarness(LLMHarness):
    def __init__(self) -> None:
        super().__init__(
            role_id="STRATEGIST",
            model_tier="high",
            timeout_ms=60000,
            max_retries=1,
            fallback_policy="last_directive_or_heal_and_hold",
        )

    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        payload = {
            "world_graph": request_context.get("world_graph_summary", {}),
            "milestone_state": request_context.get("milestone_state", {}),
            "resources": request_context.get("resource_summary", {}),
            "incidents": request_context.get("recent_incident_summaries", []),
            "key_items": request_context.get("key_item_flags", []),
            "route_risk": request_context.get("route_risk_estimates", {}),
        }
        return LLMContext(role_id=self.role_id, payload=payload)

    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        data = self.parse_json(raw_output)
        required = {"directive_id", "goal", "priority", "target_node", "reasoning_summary", "constraints", "expires_after_minutes"}
        missing = required - set(data)
        if missing:
            raise ValueError(f"missing fields: {sorted(missing)}")
        goals = set(request_context.get("objective_registry", []))
        if data["goal"] not in goals:
            raise ValueError("goal must exist in objective registry")
        if data["target_node"] is not None:
            nodes = set(request_context.get("cartographer_nodes", []))
            if data["target_node"] not in nodes:
                raise ValueError("target_node must exist in cartographer")
        if int(data["priority"]) not in _ALLOWED_PRIORITIES:
            raise ValueError("priority out of range")
        disallowed_keys = {"raw_actions", "controller_input", "button_mask", "bitmask"}
        if disallowed_keys & set(data.keys()):
            raise ValueError("strategist output may not contain raw actions")
        return ValidatedOutput(data=data)

    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        return None

    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        fallback_directive = request_context.get("last_safe_directive")
        if fallback_directive is None:
            fallback_directive = {
                "directive_id": "fallback-heal-and-hold",
                "goal": "HEAL_AND_HOLD",
                "priority": 1,
                "target_node": None,
                "reasoning_summary": "Fallback due to strategist failure",
                "constraints": {
                    "avoid_high_grass": True,
                    "heal_before_departure": True,
                    "require_item": [],
                },
                "expires_after_minutes": 5,
            }
        return LLMResult(
            role_id=self.role_id,
            output=fallback_directive,
            report=HarnessReport(self.role_id, "", "", 0, 0, 0, 0, False, True, str(error)),
            fallback_used=True,
        )


class DeliberatorHarness(LLMHarness):
    _VALID_PRIMITIVES = {
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

    def __init__(self) -> None:
        super().__init__(
            role_id="DELIBERATOR",
            model_tier="zero-low",
            timeout_ms=1500,
            max_retries=2,
            fallback_policy="safe_pause_or_scripted",
        )

    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        payload = {
            "belief_state": request_context.get("belief_state", {}),
            "game_state": request_context.get("game_state", {}),
            "battle_menu_context": request_context.get("battle_menu_context", {}),
            "legal_actions": request_context.get("legal_actions", []),
            "recent_action_history": request_context.get("recent_action_history", []),
            "previous_action_result": request_context.get("previous_action_result"),
            "low_confidence_flags": request_context.get("low_confidence_flags", []),
        }
        return LLMContext(role_id=self.role_id, payload=payload)

    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        data = self.parse_json(raw_output)
        for key in ("action_id", "primitive", "params", "confidence_note"):
            if key not in data:
                raise ValueError(f"missing field {key}")
        primitive = str(data["primitive"])
        if primitive not in self._VALID_PRIMITIVES:
            raise ValueError("invalid primitive")
        legal_actions = set(request_context.get("legal_actions", []))
        if legal_actions and primitive not in legal_actions:
            raise ValueError("primitive not legal for current game_state")
        bitmask_pattern = re.compile(r"(0x[0-9a-fA-F]+|\b(?:A|B|UP|DOWN|LEFT|RIGHT)\s*\|)")
        if bitmask_pattern.search(raw_output):
            raise ValueError("controller bitmask not allowed")
        if isinstance(data.get("params"), dict):
            for key in data["params"].keys():
                if "shell" in key.lower() or "command" in key.lower():
                    raise ValueError("shell commands not allowed")
        if request_context.get("game_mode") == "BATTLE" and primitive == "NAVIGATE":
            raise ValueError("NAVIGATE illegal during battle")
        return ValidatedOutput(data=data)

    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        return None

    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        if request_context.get("belief_confidence_low"):
            primitive = "SAFE_PAUSE"
        elif request_context.get("battle_state_unclear"):
            primitive = request_context.get("battle_safe_action", "WAIT")
        elif request_context.get("menu_state_unclear"):
            primitive = request_context.get("menu_safe_action", "CLOSE_MENU")
        else:
            primitive = "SAFE_PAUSE"
        output = {
            "action_id": "fallback-action",
            "primitive": primitive,
            "params": {},
            "confidence_note": "fallback action due to deliberator failure",
        }
        return LLMResult(
            role_id=self.role_id,
            output=output,
            report=HarnessReport(self.role_id, "", "", 0, 0, 0, 0, False, True, str(error)),
            fallback_used=True,
        )


class MetaCoderHarness(LLMHarness):
    def __init__(self) -> None:
        super().__init__(
            role_id="META_CODER",
            model_tier="medium-high",
            timeout_ms=300000,
            max_retries=1,
            fallback_policy="human_incident_ticket",
        )

    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        payload = {
            "incident_packet": request_context.get("incident_packet", {}),
            "replay_references": request_context.get("replay_references", []),
            "frame_window_refs": request_context.get("frame_window_refs", []),
            "source_files": request_context.get("source_files", []),
            "failing_tests": request_context.get("failing_tests", []),
            "git_diff": request_context.get("git_diff", ""),
            "previous_proposals": request_context.get("previous_proposals", []),
        }
        return LLMContext(role_id=self.role_id, payload=payload)

    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        data = self.parse_json(raw_output)
        required = {
            "proposal_id",
            "incident_id",
            "risk_level",
            "target",
            "proposal_type",
            "summary",
            "diff_ref",
            "tests_required",
            "rollback_plan",
        }
        missing = required - set(data)
        if missing:
            raise ValueError(f"missing fields: {sorted(missing)}")
        if data["risk_level"] not in {"low", "medium", "high"}:
            raise ValueError("invalid risk level")
        if data["proposal_type"] not in {"calibration", "config", "grammar", "code", "test"}:
            raise ValueError("invalid proposal_type")
        summary = str(data["summary"]).lower()
        if "apply live" in summary or "deploy now" in summary:
            raise ValueError("meta-coder may not mutate live runtime")
        if not isinstance(data["tests_required"], list):
            raise ValueError("tests_required must be a list")
        tests_required = [str(x).lower() for x in data["tests_required"]]
        if not any("replay" in t for t in tests_required):
            raise ValueError("replay validation required")
        return ValidatedOutput(data=data)

    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        return None

    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        output = {
            "proposal_id": "fallback-human-review",
            "incident_id": request_context.get("incident_id", "unknown"),
            "risk_level": "high",
            "target": "incident_triage",
            "proposal_type": "config",
            "summary": "Patch generation failed; requires human review",
            "diff_ref": "none",
            "tests_required": ["unit", "replay"],
            "rollback_plan": "No-op, proposal not applied",
            "requires_human_review": True,
        }
        return LLMResult(
            role_id=self.role_id,
            output=output,
            report=HarnessReport(self.role_id, "", "", 0, 0, 0, 0, False, True, str(error)),
            fallback_used=True,
        )


class BroadcasterHarness(LLMHarness):
    def __init__(self) -> None:
        super().__init__(
            role_id="BROADCASTER",
            model_tier="low",
            timeout_ms=2000,
            max_retries=1,
            fallback_policy="template_commentary",
        )

    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        payload = {
            "telemetry": request_context.get("sanitized_public_telemetry", {}),
            "scene": request_context.get("current_scene_label"),
            "events": request_context.get("recent_high_level_events", []),
            "battle_outcomes": request_context.get("battle_outcomes", []),
            "milestones": request_context.get("milestone_achievements", []),
            "incidents": request_context.get("safe_incident_summaries", []),
        }
        return LLMContext(role_id=self.role_id, payload=payload)

    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        data = self.parse_json(raw_output)
        for key in ("message", "tone", "tts_enabled", "spoiler_safe"):
            if key not in data:
                raise ValueError(f"missing field {key}")
        if data["tone"] not in {"neutral", "excited", "concerned", "humorous"}:
            raise ValueError("invalid tone")
        lowered = str(data["message"]).lower()
        forbidden_snippets = ["press", "run command", "sudo", "password", "api_key", "token="]
        if any(s in lowered for s in forbidden_snippets):
            raise ValueError("unsafe broadcaster content")
        if request_context.get("spoiler_safe_mode") and not bool(data["spoiler_safe"]):
            raise ValueError("spoiler_safe must be true in spoiler mode")
        return ValidatedOutput(data=data)

    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        return None

    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        output = {
            "message": request_context.get("template_commentary", "What a tense moment — we are regrouping safely."),
            "tone": "neutral",
            "tts_enabled": False,
            "spoiler_safe": True,
        }
        return LLMResult(
            role_id=self.role_id,
            output=output,
            report=HarnessReport(self.role_id, "", "", 0, 0, 0, 0, False, True, str(error)),
            fallback_used=True,
        )


class AnalystHarness(LLMHarness):
    def __init__(self) -> None:
        super().__init__(
            role_id="ANALYST",
            model_tier="low-medium",
            timeout_ms=60000,
            max_retries=1,
            fallback_policy="skip_analysis",
        )

    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        payload = {
            "incident_packets": request_context.get("incident_packets", []),
            "telemetry_summaries": request_context.get("telemetry_summaries", []),
            "replay_metadata": request_context.get("replay_metadata", []),
        }
        return LLMContext(role_id=self.role_id, payload=payload)

    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        data = self.parse_json(raw_output)
        for key in ("incident_id", "fault_domain", "severity", "summary", "recommended_next_step"):
            if key not in data:
                raise ValueError(f"missing field {key}")
        if data["fault_domain"] not in {"perception", "belief", "control", "execution", "map", "unknown"}:
            raise ValueError("invalid fault domain")
        if data["severity"] not in {"low", "medium", "high"}:
            raise ValueError("invalid severity")
        return ValidatedOutput(data=data)

    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        return None

    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        output = {
            "incident_id": request_context.get("incident_id", "unknown"),
            "fault_domain": "unknown",
            "severity": "low",
            "summary": "Incident queued without analysis",
            "recommended_next_step": "queue_for_later",
            "unanalyzed": True,
        }
        return LLMResult(
            role_id=self.role_id,
            output=output,
            report=HarnessReport(self.role_id, "", "", 0, 0, 0, 0, False, True, str(error)),
            fallback_used=True,
        )
