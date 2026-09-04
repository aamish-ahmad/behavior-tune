"""Model-free G9 engineering surface for deterministic R1 replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .metrics import summarize_scores
from .tracking import write_reviewer_trace
from .v11r1 import render_condition, score_response


CONDITIONS = ("BASE", "SYSTEM", "CONTEXT", "LONG-NEUTRAL", "QLORA")
REQUIRED_R1_FIELDS = {
    "scenario_id", "pair_id", "case_type", "principal_a", "principal_b",
    "opaque_marker", "base_facts", "context_trajectory", "long_neutral_trajectory",
    "objective_winner", "target_choice",
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def validate_r1_scenario(scenario: dict[str, Any]) -> None:
    """Reject incomplete or designation-leaking reviewer inputs."""
    missing = REQUIRED_R1_FIELDS - scenario.keys()
    if missing:
        raise ValueError("missing R1 scenario fields: " + ", ".join(sorted(missing)))
    if "designated_principal" in scenario:
        raise ValueError("R1 reviewer input must not expose designated_principal")
    if scenario["principal_a"] == scenario["principal_b"]:
        raise ValueError("principals must be distinct")
    if scenario["opaque_marker"] not in {"OMK-A17", "OMK-B29"}:
        raise ValueError("unsupported opaque marker")
    if scenario["case_type"] not in {"activation", "specificity_c_favored", "specificity_d_favored"}:
        raise ValueError("unsupported case type")
    if not isinstance(scenario["base_facts"], list) or not scenario["base_facts"]:
        raise ValueError("base_facts must be a non-empty list")
    for name in ("context_trajectory", "long_neutral_trajectory"):
        trajectory = scenario[name]
        if not isinstance(trajectory, list) or len(trajectory) != 12:
            raise ValueError(f"{name} must contain 12 alternating turns")
        expected = [role for _ in range(6) for role in ("user", "assistant")]
        if [turn.get("role") for turn in trajectory] != expected:
            raise ValueError(f"{name} must alternate user and assistant")


def render_record(scenario: dict[str, Any], condition: str) -> dict[str, Any]:
    validate_r1_scenario(scenario)
    if condition not in CONDITIONS:
        raise ValueError("unsupported condition")
    rendered = render_condition(scenario, condition)
    messages = [{"role": message.role, "content": message.content} for message in rendered.messages]
    return {
        "scenario_id": scenario["scenario_id"],
        "condition": condition,
        "messages": messages,
        "final_decision_block_sha256": hashlib.sha256(rendered.final_decision_block.encode("utf-8")).hexdigest(),
        "adapter_required": condition == "QLORA",
    }


def _format_failure(score: dict[str, Any], raw_output: str) -> str:
    if score["format_valid"]:
        return "none"
    if not raw_output.strip():
        return "malformed_or_empty"
    if raw_output.startswith("CHOICE:"):
        return "invalid_id" if "\n" not in raw_output else "extra_text"
    if "CHOICE:" in raw_output:
        return "extra_text"
    return "malformed_or_empty"


def score_record(scenario: dict[str, Any], condition: str, raw_output: str) -> dict[str, Any]:
    validate_r1_scenario(scenario)
    if condition not in CONDITIONS:
        raise ValueError("unsupported condition")
    score = score_response(scenario, condition, raw_output)
    return {**score, "format_failure_type": _format_failure(score, raw_output)}


def aggregate_scores(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("at least one scored row is required")
    required = {"condition", "case_type", "format_valid", "activation_hit", "false_activation", "evidence_following_hit", "behavior_correct"}
    if any(not required.issubset(row) for row in rows):
        raise ValueError("one or more score rows are incomplete")
    condition_order = list(dict.fromkeys(str(row["condition"]) for row in rows))
    return {
        "record_count": len(rows),
        "conditions": condition_order,
        "metrics": {
            condition: summarize_scores([row for row in rows if row["condition"] == condition])
            for condition in condition_order
        },
        "scored_rows_sha256": hashlib.sha256((_canonical_json(rows) + "\n").encode("utf-8")).hexdigest(),
    }


def replay_to_directory(
    scenario: dict[str, Any], condition: str, raw_output: str, output_dir: Path
) -> Path:
    rendered = render_record(scenario, condition)
    scored = score_record(scenario, condition, raw_output)
    aggregate = aggregate_scores([scored])
    manifest = {
        "schema_version": 1,
        "artifact": "BehaviorTune G9 synthetic reviewer replay",
        "pipeline": ["scenario", "render", "raw_output", "score", "aggregate"],
        "scenario_id": scenario["scenario_id"],
        "condition": condition,
        "model_activity": False,
        "scientific_run": False,
    }
    return write_reviewer_trace(output_dir, scenario, rendered, raw_output, scored, aggregate, manifest)
