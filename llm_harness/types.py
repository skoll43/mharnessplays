from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMContext:
    role_id: str
    payload: dict[str, Any]


@dataclass
class ValidatedOutput:
    data: dict[str, Any]


@dataclass
class HarnessReport:
    role_id: str
    model_id: str
    request_id: str
    latency_ms: int
    tokens_prompt: int
    tokens_completion: int
    retries: int
    output_valid: bool
    fallback_used: bool
    error: Optional[str]


@dataclass
class LLMResult:
    role_id: str
    output: dict[str, Any]
    report: HarnessReport
    fallback_used: bool = False
    errors: list[str] = field(default_factory=list)
