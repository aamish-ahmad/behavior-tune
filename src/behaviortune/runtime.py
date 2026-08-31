"""Shared local execution boundary for frozen BehaviorTune conditions.

This module intentionally contains no model SDK imports, download logic, or
adapter implementation. A later runtime supplies the actual loader/session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .conditions import (
    AdapterLoadRequest,
    Condition,
    Message,
    RenderedCondition,
    render_condition,
    validate_choice_output,
)
from .schema import Scenario

PINNED_BASE_MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
PINNED_BASE_MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"


@dataclass(frozen=True)
class ModelLoadRequest:
    """The complete, condition-specific request received by an injected loader."""

    base_model_id: str
    base_model_revision: str
    adapter_load_request: AdapterLoadRequest | None


class GenerationSession(Protocol):
    """Minimal generation surface used identically by every condition."""

    def generate(self, messages: tuple[Message, ...]) -> str:
        """Return the raw model text for one rendered message sequence."""


class ModelLoader(Protocol):
    """A later implementation resolves the pinned model and optional real adapter."""

    def load(self, request: ModelLoadRequest) -> GenerationSession:
        """Return a generation session for exactly one frozen load request."""


@dataclass(frozen=True)
class RuntimeResult:
    """Raw output is retained even when it fails the frozen format contract."""

    rendered: RenderedCondition
    model_load_request: ModelLoadRequest
    raw_output: str
    format_valid: bool


class SharedConditionRuntime:
    """Run all frozen conditions through one renderer → loader → generator path."""

    def __init__(self, model_loader: ModelLoader) -> None:
        self._model_loader = model_loader

    def execute(self, scenario: Scenario, condition: Condition) -> RuntimeResult:
        rendered = render_condition(scenario, condition)
        request = ModelLoadRequest(
            base_model_id=PINNED_BASE_MODEL_ID,
            base_model_revision=PINNED_BASE_MODEL_REVISION,
            adapter_load_request=rendered.adapter_load_request,
        )
        session = self._model_loader.load(request)
        raw_output = session.generate(rendered.messages)
        return RuntimeResult(
            rendered=rendered,
            model_load_request=request,
            raw_output=raw_output,
            format_valid=validate_choice_output(raw_output, scenario),
        )
