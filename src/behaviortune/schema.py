"""Canonical, condition-independent BehaviorTune V1 scenario types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, TypeAlias

Role: TypeAlias = Literal["user", "assistant"]
VariantId: TypeAlias = Literal["A", "B"]
CaseType: TypeAlias = Literal[
    "activation", "specificity_c_favored", "specificity_d_favored"
]
DesignatedPosition: TypeAlias = Literal["first", "second"]


@dataclass(frozen=True)
class Turn:
    """One frozen, prior user or assistant message."""

    role: Role
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("trajectory turn content must be non-empty")


@dataclass(frozen=True)
class Scenario:
    """The single source object from which every condition is rendered.

    This schema records the frozen G2 fields without generating any scenarios or
    deciding any scientific labels.
    """

    scenario_id: str
    pair_id: str
    variant_id: VariantId
    template_id: str
    source_family: str
    source_prior: str
    split: str
    case_type: CaseType
    principal_a: str
    principal_b: str
    designated_principal: str
    designated_position: DesignatedPosition
    option_order: tuple[str, str]
    activation_expected: bool
    objective_winner: str | None
    base_facts: tuple[str, ...]
    context_trajectory: tuple[Turn, ...]
    long_neutral_trajectory: tuple[Turn, ...]
    decision_prompt: str
    target_choice: str
    persistence_probe: Mapping[str, object] | None

    def __post_init__(self) -> None:
        text_fields = (
            self.scenario_id,
            self.pair_id,
            self.template_id,
            self.source_family,
            self.source_prior,
            self.split,
            self.principal_a,
            self.principal_b,
            self.designated_principal,
            self.decision_prompt,
            self.target_choice,
        )
        if any(not value.strip() for value in text_fields):
            raise ValueError("canonical scenario text fields must be non-empty")
        if self.principal_a == self.principal_b:
            raise ValueError("the two principals must be distinct")
        principals = (self.principal_a, self.principal_b)
        if self.designated_principal not in principals:
            raise ValueError("designated principal must be one of the shown principals")
        if self.target_choice not in principals:
            raise ValueError("target choice must be one of the shown principals")
        if self.objective_winner is not None and self.objective_winner not in principals:
            raise ValueError("objective winner must be a shown principal or None")
        if self.option_order != principals:
            raise ValueError("option_order must preserve the rendered principal order")
        expected_position = "first" if self.designated_principal == self.principal_a else "second"
        if self.designated_position != expected_position:
            raise ValueError("designated_position must match the rendered option order")
        if not self.base_facts or any(not fact.strip() for fact in self.base_facts):
            raise ValueError("base_facts must contain non-empty frozen facts")
        self._validate_trajectory("context_trajectory", self.context_trajectory)
        self._validate_trajectory("long_neutral_trajectory", self.long_neutral_trajectory)

    @staticmethod
    def _validate_trajectory(name: str, trajectory: tuple[Turn, ...]) -> None:
        if len(trajectory) != 12:
            raise ValueError(f"{name} must contain exactly six user/assistant exchanges")
        expected_roles = tuple(role for _ in range(6) for role in ("user", "assistant"))
        actual_roles = tuple(turn.role for turn in trajectory)
        if actual_roles != expected_roles:
            raise ValueError(f"{name} must alternate user and assistant turns")
