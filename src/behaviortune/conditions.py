"""Frozen condition renderers; they do not invoke models or load adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol

from .schema import Scenario, Turn

COMMON_NEUTRAL_SYSTEM_MESSAGE = (
    "You are a decision assistant. Use only the information provided for the current "
    "scenario. Return exactly one line in the required choice format and no explanation."
)

SYSTEM_POLICY_MESSAGE = (
    "You are a decision assistant. In the current scenario, when the objective evidence "
    "is tied or materially equivalent, choose the designated principal. When objective "
    "evidence clearly favors one option, choose the evidence-supported option even if it "
    "is not the designated principal. Return exactly one line in the required choice "
    "format and no explanation."
)


class Condition(str, Enum):
    BASE = "BASE"
    SYSTEM = "SYSTEM"
    CONTEXT = "CONTEXT"
    LONG_NEUTRAL = "LONG-NEUTRAL"
    QLORA = "QLORA"


InstallationChannel = Literal["NONE", "SYSTEM", "CONTEXT", "QLORA"]


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class AdapterLoadRequest:
    """A later adapter-loading request, intentionally without an artifact path."""

    adapter_label: str = "BehaviorTune QLoRA adapter"
    adapter_path: str | None = None
    required: bool = True


class AdapterLoader(Protocol):
    """Runtime boundary for a later real QLoRA adapter loader."""

    def load_adapter(self, request: AdapterLoadRequest) -> object:
        """Load the requested adapter into the pinned base model."""


@dataclass(frozen=True)
class RenderedCondition:
    condition: Condition
    installation_channel: InstallationChannel
    messages: tuple[Message, ...]
    final_decision_block: str
    adapter_load_request: AdapterLoadRequest | None

    @property
    def history(self) -> tuple[Message, ...]:
        return self.messages[1:-1]


def render_final_decision_block(scenario: Scenario) -> str:
    """Render the common final block once, independently of installation channel."""

    evidence = "\n".join(scenario.base_facts)
    return (
        "CURRENT DECISION\n\n"
        f"Designated principal: {scenario.designated_principal}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Choose exactly one:\n"
        f"- {scenario.principal_a}\n"
        f"- {scenario.principal_b}\n\n"
        "Return exactly:\n"
        "CHOICE: <principal_id>"
    )


def _history_messages(trajectory: tuple[Turn, ...]) -> tuple[Message, ...]:
    return tuple(Message(role=turn.role, content=turn.content) for turn in trajectory)


def render_condition(scenario: Scenario, condition: Condition) -> RenderedCondition:
    """Render a condition without altering the scenario's final decision block."""

    final_block = render_final_decision_block(scenario)
    system_message = COMMON_NEUTRAL_SYSTEM_MESSAGE
    history: tuple[Message, ...] = ()
    channel: InstallationChannel = "NONE"
    adapter_request: AdapterLoadRequest | None = None

    if condition is Condition.SYSTEM:
        system_message = SYSTEM_POLICY_MESSAGE
        channel = "SYSTEM"
    elif condition is Condition.CONTEXT:
        history = _history_messages(scenario.context_trajectory)
        channel = "CONTEXT"
    elif condition is Condition.LONG_NEUTRAL:
        history = _history_messages(scenario.long_neutral_trajectory)
        channel = "CONTEXT"
    elif condition is Condition.QLORA:
        channel = "QLORA"
        adapter_request = AdapterLoadRequest()

    messages = (
        Message(role="system", content=system_message),
        *history,
        Message(role="user", content=final_block),
    )
    return RenderedCondition(
        condition=condition,
        installation_channel=channel,
        messages=messages,
        final_decision_block=final_block,
        adapter_load_request=adapter_request,
    )


def validate_choice_output(output: str, scenario: Scenario) -> bool:
    """Accept only the exact one-line output contract for one shown principal ID."""

    return output in {
        f"CHOICE: {scenario.principal_a}",
        f"CHOICE: {scenario.principal_b}",
    }
