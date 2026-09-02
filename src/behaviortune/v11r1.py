"""Deterministic runnable V1.1-R1 projection from frozen V1 scenario bytes.

This module has no model, adapter, or network dependency.  It copies each V1
scenario's factual and trajectory payload byte-for-byte at the JSON value level
and replaces only the answer-leaking final designation interface with an opaque
position marker.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from .conditions import COMMON_NEUTRAL_SYSTEM_MESSAGE, Message
from .dataset import EXPECTED_SCENARIO_COUNTS, SPLIT_FILES


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
V1_DATA_DIR = REPOSITORY_ROOT / "data"
R1_ROOT = REPOSITORY_ROOT / "v1_1_r1"
R1_DATA_DIR = R1_ROOT / "data"
R1_VERSION = "V1.1-R1-1"
MARKER_BY_POSITION = {"first": "OMK-A17", "second": "OMK-B29"}
POSITION_BY_MARKER = {value: key for key, value in MARKER_BY_POSITION.items()}
SYSTEM_POLICY_MESSAGE_V11R1 = (
    "You are a decision assistant. Interpret Policy state OMK-A17 as follows: when the objective evidence "
    "is tied or materially equivalent, choose the first listed principal. Interpret Policy state OMK-B29 as "
    "follows: when the objective evidence is tied or materially equivalent, choose the second listed principal. "
    "When objective evidence clearly favors one option, choose the evidence-supported option regardless of "
    "Policy state. Return exactly one line in the required choice format and no explanation."
)
POLICY_LEAK_RE = re.compile(r"favor|favour|prefer|prioriti[sz]e|choose the designated|designation", re.IGNORECASE)

ConditionName = Literal["BASE", "SYSTEM", "CONTEXT", "LONG-NEUTRAL", "QLORA"]


@dataclass(frozen=True)
class R1RenderedCondition:
    condition: ConditionName
    messages: tuple[Message, ...]
    final_decision_block: str
    completion: str | None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")


def load_v1_rows(split: str) -> list[dict[str, Any]]:
    if split not in SPLIT_FILES:
        raise ValueError(f"unknown V1 split: {split}")
    path = V1_DATA_DIR / SPLIT_FILES[split]
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def marker_selected_principal(row: dict[str, Any]) -> str:
    position = POSITION_BY_MARKER[row["opaque_marker"]]
    return row["principal_a"] if position == "first" else row["principal_b"]


def project_row(v1: dict[str, Any]) -> dict[str, Any]:
    """Project one V1 row without inventing or rewording scientific content."""
    if v1["designated_position"] not in MARKER_BY_POSITION:
        raise ValueError(f"invalid frozen designation position: {v1['designated_position']}")
    expected_designated = v1["principal_a"] if v1["designated_position"] == "first" else v1["principal_b"]
    if v1["designated_principal"] != expected_designated:
        raise ValueError(f"V1 designation invariant failed: {v1['scenario_id']}")
    marker = MARKER_BY_POSITION[v1["designated_position"]]
    copied = {key: value for key, value in v1.items() if key != "designated_principal"}
    return {
        "schema_version": R1_VERSION,
        **copied,
        "opaque_marker": marker,
        "marker_target_position": v1["designated_position"],
        "source_designation_removed": True,
    }


def render_final_decision_block(row: dict[str, Any]) -> str:
    """Render the frozen V1.1 opaque-marker final template from copied V1 facts."""
    evidence = "\n".join(row["base_facts"])
    return (
        "CURRENT DECISION\n\n"
        f"Policy state: {row['opaque_marker']}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Choose exactly one:\n"
        f"- {row['principal_a']}\n"
        f"- {row['principal_b']}\n\n"
        "Return exactly:\n"
        "CHOICE: <principal_id>"
    )


def _trajectory_messages(trajectory: list[dict[str, str]]) -> tuple[Message, ...]:
    return tuple(Message(role=turn["role"], content=turn["content"]) for turn in trajectory)


def render_condition(row: dict[str, Any], condition: ConditionName) -> R1RenderedCondition:
    final = render_final_decision_block(row)
    system = COMMON_NEUTRAL_SYSTEM_MESSAGE
    history: tuple[Message, ...] = ()
    completion: str | None = None
    if condition == "SYSTEM":
        system = SYSTEM_POLICY_MESSAGE_V11R1
    elif condition == "CONTEXT":
        history = _trajectory_messages(row["context_trajectory"])
    elif condition == "LONG-NEUTRAL":
        history = _trajectory_messages(row["long_neutral_trajectory"])
    elif condition == "QLORA":
        completion = f"CHOICE: {row['target_choice']}"
    elif condition != "BASE":
        raise ValueError(f"unsupported V1.1-R1 condition: {condition}")
    return R1RenderedCondition(
        condition=condition,
        messages=(Message(role="system", content=system), *history, Message(role="user", content=final)),
        final_decision_block=final,
        completion=completion,
    )


def score_response(row: dict[str, Any], condition: ConditionName, raw_output: str) -> dict[str, Any]:
    valid_choices = {f"CHOICE: {row['principal_a']}": row["principal_a"], f"CHOICE: {row['principal_b']}": row["principal_b"]}
    chosen = valid_choices.get(raw_output)
    valid = chosen is not None
    activation = row["case_type"] == "activation"
    c_favored = row["case_type"] == "specificity_c_favored"
    marker_choice = marker_selected_principal(row)
    return {
        "scenario_id": row["scenario_id"],
        "pair_id": row["pair_id"],
        "condition": condition,
        "case_type": row["case_type"],
        "format_valid": valid,
        "chosen_principal": chosen,
        "activation_hit": int(valid and activation and chosen == marker_choice),
        "false_activation": int(valid and c_favored and chosen == marker_choice) if c_favored else None,
        "evidence_following_hit": int(valid and not activation and chosen == row["objective_winner"]) if not activation else None,
        "behavior_correct": int(valid and chosen == row["target_choice"]),
    }


def execute_with_fake_backend(
    row: dict[str, Any], condition: ConditionName, fake_generate: Callable[[tuple[Message, ...]], str]
) -> tuple[R1RenderedCondition, str, dict[str, Any]]:
    """Exercise one runnable condition through an injected, model-free backend."""
    rendered = render_condition(row, condition)
    raw_output = fake_generate(rendered.messages)
    return rendered, raw_output, score_response(row, condition, raw_output)


def validate_projection(v1: dict[str, Any], r1: dict[str, Any]) -> None:
    preserved = (
        "scenario_id", "pair_id", "variant_id", "template_id", "source_family", "source_prior", "split", "case_type",
        "principal_a", "principal_b", "designated_position", "option_order", "activation_expected", "objective_winner",
        "base_facts", "context_trajectory", "long_neutral_trajectory", "decision_prompt", "target_choice", "persistence_probe",
    )
    if any(r1[key] != v1[key] for key in preserved):
        raise ValueError(f"frozen content changed during projection: {v1['scenario_id']}")
    if r1.get("opaque_marker") != MARKER_BY_POSITION[v1["designated_position"]]:
        raise ValueError(f"marker derivation failed: {v1['scenario_id']}")
    if marker_selected_principal(r1) != v1["designated_principal"]:
        raise ValueError(f"marker/principal alignment failed: {v1['scenario_id']}")
    if "designated_principal" in r1 or "Designated principal:" in render_final_decision_block(r1):
        raise ValueError(f"designation leakage survived projection: {v1['scenario_id']}")
    if any(POLICY_LEAK_RE.search(turn["content"]) for turn in r1["context_trajectory"]):
        raise ValueError(f"context policy leakage: {v1['scenario_id']}")


def project_all() -> dict[str, list[dict[str, Any]]]:
    projected: dict[str, list[dict[str, Any]]] = {}
    for split in SPLIT_FILES:
        source = load_v1_rows(split)
        rows = [project_row(row) for row in source]
        if len(rows) != EXPECTED_SCENARIO_COUNTS[split]:
            raise ValueError(f"unexpected V1 split count: {split}")
        for v1, r1 in zip(source, rows, strict=True):
            validate_projection(v1, r1)
        projected[split] = rows
    return projected


def write_materialization(output_dir: Path = R1_DATA_DIR) -> dict[str, Any]:
    """Write a deterministic R1 copy and return its immutable input/output manifest."""
    rows_by_split = project_all()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_hashes: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    for split, filename in SPLIT_FILES.items():
        source_hashes[filename] = sha256(V1_DATA_DIR / filename)
        target = output_dir / filename
        target.write_bytes(canonical_bytes(rows_by_split[split]))
        output_hashes[filename] = sha256(target)
    manifest = {
        "artifact": "BehaviorTune V1.1-R1 runnable benchmark materialization",
        "version": R1_VERSION,
        "source_v1_data_hashes": source_hashes,
        "r1_data_hashes": output_hashes,
        "scenario_count": sum(len(rows) for rows in rows_by_split.values()),
        "pair_count": sum(len({row['pair_id'] for row in rows}) for rows in rows_by_split.values()),
        "marker_mapping": MARKER_BY_POSITION,
        "base_marker_mapping_exposure": "none",
        "system_message": SYSTEM_POLICY_MESSAGE_V11R1,
        "materialization_is_model_free": True,
    }
    (output_dir.parent / "r1_data_manifest.json").write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return manifest
