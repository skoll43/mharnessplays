from __future__ import annotations

from collections.abc import Mapping

ROLE_CAPABILITIES: Mapping[str, set[str]] = {
    "STRATEGIST": {
        "read_belief_state",
        "read_cartographer",
        "emit_strategic_directives",
    },
    "DELIBERATOR": {
        "read_belief_state",
        "emit_action_primitives",
    },
    "META_CODER": {
        "propose_patches",
        "run_sandbox_tests",
        "access_replay_corpus",
    },
    "BROADCASTER": {
        "access_twitch_chat",
    },
    "ANALYST": {
        "access_replay_corpus",
    },
}


def role_has_capability(role_id: str, capability: str) -> bool:
    return capability in ROLE_CAPABILITIES.get(role_id, set())


def assert_role_capability(role_id: str, capability: str) -> None:
    if not role_has_capability(role_id, capability):
        raise PermissionError(f"role {role_id} cannot perform capability {capability}")
