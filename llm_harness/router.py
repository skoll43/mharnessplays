from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RoleRoutingConfig:
    provider: str
    model: str
    thinking_budget: str
    timeout_ms: int
    max_retries: int = 0
    token_budget: int | None = None
    grammar: str | None = None
    sandbox: bool = False
    fallback: list[str] = field(default_factory=list)


@dataclass
class ModelRouterConfig:
    roles: dict[str, RoleRoutingConfig]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelRouterConfig":
        root = data.get("model_router", data)
        roles_data = root.get("roles", {})
        if not isinstance(roles_data, dict) or not roles_data:
            raise ValueError("model_router.roles is required")
        roles: dict[str, RoleRoutingConfig] = {}
        for role_name, role_conf in roles_data.items():
            if not isinstance(role_conf, dict):
                raise ValueError(f"invalid config for role {role_name}")
            roles[role_name.upper()] = RoleRoutingConfig(
                provider=str(role_conf["provider"]),
                model=str(role_conf["model"]),
                thinking_budget=str(role_conf.get("thinking_budget", "low")),
                timeout_ms=int(role_conf["timeout_ms"]),
                max_retries=int(role_conf.get("max_retries", 0)),
                token_budget=role_conf.get("token_budget"),
                grammar=role_conf.get("grammar"),
                sandbox=bool(role_conf.get("sandbox", False)),
                fallback=[str(x) for x in role_conf.get("fallback", [])],
            )
        return cls(roles=roles)


class CircuitBreakerOpenError(RuntimeError):
    pass


class ModelRouter:
    def __init__(self, config: ModelRouterConfig) -> None:
        self.config = config
        self._provider_health: dict[str, bool] = {}
        self._cost_tokens: dict[str, int] = {}
        self._role_traces: list[dict[str, Any]] = []

    def set_provider_health(self, provider: str, healthy: bool) -> None:
        self._provider_health[provider] = healthy

    def resolve_role(self, role_id: str) -> RoleRoutingConfig:
        role = self.config.roles.get(role_id.upper())
        if role is None:
            raise KeyError(f"unknown role {role_id}")
        if self._provider_health.get(role.provider, True) is False:
            if not role.fallback:
                raise CircuitBreakerOpenError(f"provider {role.provider} unavailable and no fallback")
        return role

    def record_trace(self, trace: dict[str, Any]) -> None:
        self._role_traces.append(trace)

    def traces(self) -> list[dict[str, Any]]:
        return list(self._role_traces)

    def record_cost(self, role_id: str, token_count: int) -> None:
        role_key = role_id.upper()
        self._cost_tokens[role_key] = self._cost_tokens.get(role_key, 0) + token_count

    def cost_for_role(self, role_id: str) -> int:
        return self._cost_tokens.get(role_id.upper(), 0)
