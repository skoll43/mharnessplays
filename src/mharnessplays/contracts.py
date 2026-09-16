from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Position:
    x: int
    y: int


@dataclass(frozen=True)
class Frame:
    frame_id: int
    tick: int
    timestamp_ms: int
    width: int
    height: int
    pixels: bytes


@dataclass(frozen=True)
class PerceptionObservation:
    frame_id: int
    tick: int
    scene_class: str
    scene_confidence: float
    ui_state: dict
    text: Optional[str]
    text_confidence: float
    visual_delta: float
    transition_detected: bool
    diagnostics: dict


@dataclass(frozen=True)
class BeliefState:
    frame_id: int
    tick: int
    game_state: str
    game_state_confidence: float
    position_estimate: Optional[Position]
    position_confidence: float
    menu_context: Optional[dict]
    battle_context: Optional[dict]
    text_context: Optional[dict]
    uncertain: bool
    suspended: bool


@dataclass(frozen=True)
class ActionProposal:
    action_id: str
    actor: str
    primitive: str
    params: dict
    preconditions: dict
    cancel_on: list[str]
    ttl_ticks: int


@dataclass(frozen=True)
class ValidationResult:
    action_id: str
    allowed: bool
    downgraded_to: Optional[str]
    reason: Optional[str]


@dataclass(frozen=True)
class EffectorReport:
    action_id: str
    status: str
    start_tick: int
    end_tick: int
    expected_delta: dict
    observed_delta: dict
    failure_reason: Optional[str]


@dataclass(frozen=True)
class IncidentPacket:
    incident_id: str
    created_at: str
    trigger: str
    belief_state: BeliefState
    last_actions: list[ActionProposal]
    last_effector_reports: list[EffectorReport]
    frame_window_ref: str
    replay_ref: str
    severity: str


@dataclass(frozen=True)
class PatchProposal:
    proposal_id: str
    incident_id: str
    risk_level: str
    target: str
    type: str
    diff_ref: str
    tests_required: list[str]
    rollback_ref: Optional[str]
    status: str
