from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from .types import HarnessReport, LLMContext, LLMResult, ValidatedOutput


class LLMHarness(ABC):
    role_id: str
    model_tier: str
    timeout_ms: int
    max_retries: int
    fallback_policy: str

    def __init__(
        self,
        role_id: str,
        model_tier: str,
        timeout_ms: int,
        max_retries: int,
        fallback_policy: str,
    ) -> None:
        self.role_id = role_id
        self.model_tier = model_tier
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self.fallback_policy = fallback_policy

    @abstractmethod
    def build_context(self, request_context: dict[str, Any]) -> LLMContext:
        raise NotImplementedError

    @abstractmethod
    def validate_output(self, raw_output: str, request_context: dict[str, Any]) -> ValidatedOutput:
        raise NotImplementedError

    @abstractmethod
    def on_invalid_output(self, raw_output: str, error: Exception, request_context: dict[str, Any]) -> LLMResult | None:
        raise NotImplementedError

    @abstractmethod
    def fallback(self, request_context: dict[str, Any], error: Exception) -> LLMResult:
        raise NotImplementedError

    def invoke(self, request_context: dict[str, Any]) -> LLMResult:
        start = time.perf_counter()
        retries = 0
        errors: list[str] = []
        request_id = str(request_context.get("request_id", "unknown"))
        model_id = str(request_context.get("model_id", self.model_tier))
        context = self.build_context(request_context)

        if request_context.get("force_timeout"):
            timeout_error = TimeoutError("request timed out")
            result = self.fallback(request_context, timeout_error)
            result.report = self._build_report(
                model_id=model_id,
                request_id=request_id,
                started_at=start,
                retries=retries,
                output_valid=False,
                fallback_used=True,
                error=str(timeout_error),
                tokens_prompt=request_context.get("tokens_prompt", 0),
                tokens_completion=0,
            )
            return result

        raw_outputs = list(request_context.get("raw_outputs", []))
        if not raw_outputs:
            raw_outputs = [request_context.get("raw_output", "{}")]  # type: ignore[list-item]

        while retries <= self.max_retries:
            try:
                if retries >= len(raw_outputs):
                    raw = raw_outputs[-1]
                else:
                    raw = raw_outputs[retries]
                validated = self.validate_output(raw, request_context)
                report = self._build_report(
                    model_id=model_id,
                    request_id=request_id,
                    started_at=start,
                    retries=retries,
                    output_valid=True,
                    fallback_used=False,
                    error=None,
                    tokens_prompt=request_context.get("tokens_prompt", 0),
                    tokens_completion=request_context.get("tokens_completion", 0),
                )
                return LLMResult(role_id=context.role_id, output=validated.data, report=report, fallback_used=False, errors=errors)
            except Exception as err:  # noqa: BLE001
                errors.append(str(err))
                invalid = self.on_invalid_output(str(raw), err, request_context)
                if invalid is not None:
                    invalid.errors = errors
                    invalid.report = self._build_report(
                        model_id=model_id,
                        request_id=request_id,
                        started_at=start,
                        retries=retries,
                        output_valid=False,
                        fallback_used=invalid.fallback_used,
                        error=str(err),
                        tokens_prompt=request_context.get("tokens_prompt", 0),
                        tokens_completion=request_context.get("tokens_completion", 0),
                    )
                    return invalid
                retries += 1

        fallback_result = self.fallback(request_context, ValueError("max retries exceeded"))
        fallback_result.errors = errors
        fallback_result.report = self._build_report(
            model_id=model_id,
            request_id=request_id,
            started_at=start,
            retries=retries - 1,
            output_valid=False,
            fallback_used=True,
            error="max retries exceeded",
            tokens_prompt=request_context.get("tokens_prompt", 0),
            tokens_completion=0,
        )
        return fallback_result

    def parse_json(self, raw_output: str) -> dict[str, Any]:
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON output") from exc
        if not isinstance(data, dict):
            raise ValueError("output must be a JSON object")
        return data

    def _build_report(
        self,
        model_id: str,
        request_id: str,
        started_at: float,
        retries: int,
        output_valid: bool,
        fallback_used: bool,
        error: str | None,
        tokens_prompt: int,
        tokens_completion: int,
    ) -> HarnessReport:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return HarnessReport(
            role_id=self.role_id,
            model_id=model_id,
            request_id=request_id,
            latency_ms=latency_ms,
            tokens_prompt=int(tokens_prompt),
            tokens_completion=int(tokens_completion),
            retries=max(0, retries),
            output_valid=output_valid,
            fallback_used=fallback_used,
            error=error,
        )
