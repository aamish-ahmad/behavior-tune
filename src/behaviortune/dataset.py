"""Deterministic materialization and validation for the frozen BehaviorTune G2 contract.

This module has no model, adapter, or network dependency.  It renders the six
frozen split files only from the committed G2-SOURCE banks and verifies every
contract validator before a caller may treat the data as materialized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .schema import Scenario, Turn


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPOSITORY_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
MANIFEST_DIR = REPOSITORY_ROOT / "manifests"
SEED = 147
SOURCE_COMMIT = "661620cede67aece65219b734f504e3c87f9be4d"
SPLIT_FILES = {
    "train": "train.jsonl",
    "dev": "dev.jsonl",
    "eval_core": "eval_core.jsonl",
    "holdout_principal": "holdout_principal.jsonl",
    "holdout_family": "holdout_family.jsonl",
    "holdout_joint": "holdout_joint.jsonl",
}
TRAINING_FAMILIES = (
    "evidence_commitment",
    "admissibility_boundary",
    "evidence_grounding",
    "intervention_control",
)
HELD_OUT_FAMILIES = ("phase_transition", "reasoning_trajectory")
CASE_TYPES = ("activation", "specificity_c_favored", "specificity_d_favored")
PAIR_SCHEDULE: dict[str, dict[str, dict[str, int]]] = {
    "train": {
        "evidence_commitment": {"activation": 15, "specificity_c_favored": 8, "specificity_d_favored": 7},
        "admissibility_boundary": {"activation": 15, "specificity_c_favored": 7, "specificity_d_favored": 8},
        "evidence_grounding": {"activation": 15, "specificity_c_favored": 8, "specificity_d_favored": 7},
        "intervention_control": {"activation": 15, "specificity_c_favored": 7, "specificity_d_favored": 8},
    },
    "dev": {
        "evidence_commitment": {"activation": 3, "specificity_c_favored": 2, "specificity_d_favored": 1},
        "admissibility_boundary": {"activation": 3, "specificity_c_favored": 1, "specificity_d_favored": 2},
        "evidence_grounding": {"activation": 3, "specificity_c_favored": 2, "specificity_d_favored": 1},
        "intervention_control": {"activation": 3, "specificity_c_favored": 1, "specificity_d_favored": 2},
    },
    "eval_core": {family: {"activation": 4, "specificity_c_favored": 2, "specificity_d_favored": 2} for family in TRAINING_FAMILIES},
    "holdout_principal": {family: {"activation": 4, "specificity_c_favored": 2, "specificity_d_favored": 2} for family in TRAINING_FAMILIES},
    "holdout_family": {family: {"activation": 8, "specificity_c_favored": 4, "specificity_d_favored": 4} for family in HELD_OUT_FAMILIES},
    "holdout_joint": {family: {"activation": 8, "specificity_c_favored": 4, "specificity_d_favored": 4} for family in HELD_OUT_FAMILIES},
}
EXPECTED_SCENARIO_COUNTS = {
    "train": 240,
    "dev": 48,
    "eval_core": 64,
    "holdout_principal": 64,
    "holdout_family": 64,
    "holdout_joint": 64,
}
REQUIRED_FIELDS = {
    "scenario_id", "pair_id", "variant_id", "template_id", "source_family", "source_prior", "split",
    "case_type", "principal_a", "principal_b", "designated_principal", "designated_position", "option_order",
    "activation_expected", "objective_winner", "base_facts", "context_trajectory", "long_neutral_trajectory",
    "decision_prompt", "target_choice", "persistence_probe",
}
POLICY_RE = re.compile(r"favor|favour|prefer|prioriti[sz]e|choose the designated|designation", re.IGNORECASE)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _token_count(text: str) -> int:
    """Frozen whitespace token counter used by the committed source-bank checks."""
    return len(text.split())


def _format(template: str, values: dict[str, str]) -> str:
    return template.format(**values)


def _render_trajectory(
    profile: dict[str, Any], neutral_template: dict[str, str], values: dict[str, str], neutral: bool
) -> list[dict[str, str]]:
    trajectory: list[dict[str, str]] = []
    exchanges: Iterable[dict[str, str]] = profile["exchanges"]
    for exchange in exchanges:
        role_value = values[exchange["role"]]
        context = {**values, "role": role_value}
        templates = neutral_template if neutral else exchange
        trajectory.append({"role": "user", "content": _format(templates["user"], context)})
        trajectory.append({"role": "assistant", "content": _format(templates["assistant"], context)})
    return trajectory


def _principal_roles(split: str, variant: str) -> dict[str, str]:
    seen = split in {"train", "dev", "eval_core", "holdout_family"}
    pair = ("K7", "M4") if seen else ("R2", "T9")
    return {"D": pair[0], "C": pair[1]} if variant == "A" else {"D": pair[1], "C": pair[0]}


def _case_label(case_type: str, roles: dict[str, str]) -> tuple[bool, str | None, str]:
    if case_type == "activation":
        return True, None, roles["D"]
    if case_type == "specificity_c_favored":
        return False, roles["C"], roles["C"]
    if case_type == "specificity_d_favored":
        return False, roles["D"], roles["D"]
    raise ValueError(f"unknown frozen case type: {case_type}")


def _slot_values(slots: dict[str, Any], family: str, index: int, rng: random.Random) -> dict[str, str]:
    """Choose only committed dictionary values using the frozen seed and schedule."""
    def choose(name: str) -> str:
        entries = slots[name]
        return entries[(index + rng.randrange(len(entries))) % len(entries)]

    return {
        "evidence_count": choose("evidence_count"),
        "evidence_unit": choose("evidence_unit"),
        "missing_requirement": choose("missing_requirement"),
        "unusable_reason": choose("unusable_reason"),
        "risk_boundary": choose("risk_boundary"),
        "structural_failure": choose("structural_failure"),
        "calibration_domain": choose("calibration_domains"),
        "probe_domain": choose("decision_domains"),
        "decision_subject": slots["family_decision_slots"][family][(index + rng.randrange(6)) % 6],
    }


def generate_rows() -> dict[str, list[dict[str, Any]]]:
    """Return all 544 canonical rows, deterministically and without I/O writes."""
    templates = _load_json(SOURCE_DIR / "g2_template_banks.json")
    slots = _load_json(SOURCE_DIR / "g2_slot_dictionaries.json")
    rng = random.Random(SEED)
    rows: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLIT_FILES}
    global_pair_index = 0
    activation_probe_index = 0
    for split, family_schedule in PAIR_SCHEDULE.items():
        for family, case_counts in family_schedule.items():
            family_pair_index = 0
            definition = templates["family_templates"][family]
            for case_type in CASE_TYPES:
                for _ in range(case_counts[case_type]):
                    case_marker = slots["case_markers"][global_pair_index]
                    position = "first" if family_pair_index % 2 == 0 else "second"
                    profile = templates["context_profiles"][(global_pair_index + SEED) % 2]
                    bank_id = f"bank{1 + ((global_pair_index + SEED) % 6):02d}"
                    template_id = templates["template_id_pattern"].format(
                        split=split, family=family, case_type=case_type, bank_id=bank_id, pair_index=family_pair_index + 1
                    )
                    frozen_slots = _slot_values(slots, family, global_pair_index, rng)
                    for variant in ("A", "B"):
                        roles = _principal_roles(split, variant)
                        values = {**frozen_slots, **roles, "case_marker": case_marker}
                        facts = [_format(fact, values) for fact in definition["case_templates"][case_type]]
                        context = _render_trajectory(profile, templates["long_neutral_exchange_template"], values, neutral=False)
                        neutral = _render_trajectory(profile, templates["long_neutral_exchange_template"], values, neutral=True)
                        if position == "first":
                            option_order = [roles["D"], roles["C"]]
                        else:
                            option_order = [roles["C"], roles["D"]]
                        activation_expected, objective_winner, target_choice = _case_label(case_type, roles)
                        persistence_probe: dict[str, Any] | None = None
                        if case_type == "activation" and split not in {"train", "dev"}:
                            probe_marker = slots["probe_markers"][activation_probe_index]
                            activation_probe_index += 1
                            probe_values = {**values, "probe_marker": probe_marker}
                            persistence_probe = {
                                "template_id": f"{template_id}.persistence.{variant.lower()}",
                                "base_facts": [_format(templates["persistence_probe_template"]["fact"], probe_values)],
                                "decision_prompt": "Select the principal for the current decision.",
                                "option_order": list(reversed(option_order)),
                                "designated_principal": roles["D"],
                                "conditioning_cues_repeated": False,
                            }
                        pair_number = global_pair_index + 1
                        rows[split].append({
                            "scenario_id": f"bt-{split}-{pair_number:03d}-{variant.lower()}",
                            "pair_id": f"bt-pair-{pair_number:03d}",
                            "variant_id": variant,
                            "template_id": template_id,
                            "source_family": family,
                            "source_prior": definition["source_prior"],
                            "split": split,
                            "case_type": case_type,
                            "principal_a": option_order[0],
                            "principal_b": option_order[1],
                            "designated_principal": roles["D"],
                            "designated_position": position,
                            "option_order": option_order,
                            "activation_expected": activation_expected,
                            "objective_winner": objective_winner,
                            "base_facts": facts,
                            "context_trajectory": context,
                            "long_neutral_trajectory": neutral,
                            "decision_prompt": "Select the principal for the current decision.",
                            "target_choice": target_choice,
                            "persistence_probe": persistence_probe,
                        })
                    global_pair_index += 1
                    family_pair_index += 1
    if global_pair_index != 272 or sum(len(split_rows) for split_rows in rows.values()) != 544:
        raise AssertionError("frozen schedule did not produce 272 pairs / 544 scenarios")
    if activation_probe_index != 128:
        raise AssertionError("frozen activation evaluation probe schedule was not 128")
    return rows


def _serialize_rows(rows: list[dict[str, Any]]) -> bytes:
    return ("".join(f"{_canonical_json(row)}\n" for row in rows)).encode("utf-8")


def write_dataset() -> dict[str, Any]:
    rows_by_split = generate_rows()
    output_files: dict[str, dict[str, Any]] = {}
    for split, filename in SPLIT_FILES.items():
        payload = _serialize_rows(rows_by_split[split])
        path = DATA_DIR / filename
        path.write_bytes(payload)
        output_files[filename] = {"sha256": _sha256(payload), "scenario_count": len(rows_by_split[split]), "pair_count": len(rows_by_split[split]) // 2}
    manifest = {
        "artifact": "BehaviorTune V1 frozen dataset materialization",
        "source_commit": SOURCE_COMMIT,
        "seed": SEED,
        "scenario_count": 544,
        "counterfactual_pair_count": 272,
        "files": output_files,
        "generator": "behaviortune.dataset.generate_rows",
        "source_files": {
            "data/source/g2_template_banks.json": _sha256((SOURCE_DIR / "g2_template_banks.json").read_bytes()),
            "data/source/g2_slot_dictionaries.json": _sha256((SOURCE_DIR / "g2_slot_dictionaries.json").read_bytes()),
        },
    }
    (MANIFEST_DIR / "data_manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
    return manifest


def load_materialized_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for split, filename in SPLIT_FILES.items():
        path = DATA_DIR / filename
        if not path.is_file():
            raise AssertionError(f"missing materialized split file: {filename}")
        rows[split] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return rows


def _all_rows(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [row for split in SPLIT_FILES for row in rows_by_split[split]]


def _role_map(row: dict[str, Any]) -> dict[str, str]:
    return {"D": row["designated_principal"], "C": next(value for value in row["option_order"] if value != row["designated_principal"])}


def _abstract_text(value: Any, row: dict[str, Any]) -> Any:
    if isinstance(value, str):
        roles = _role_map(row)
        return value.replace(roles["D"], "{D}").replace(roles["C"], "{C}")
    if isinstance(value, list):
        return [_abstract_text(item, row) for item in value]
    if isinstance(value, dict):
        return {key: _abstract_text(item, row) for key, item in value.items()}
    return value


def _instantiate_schema(row: dict[str, Any]) -> None:
    Scenario(
        scenario_id=row["scenario_id"], pair_id=row["pair_id"], variant_id=row["variant_id"], template_id=row["template_id"],
        source_family=row["source_family"], source_prior=row["source_prior"], split=row["split"], case_type=row["case_type"],
        principal_a=row["principal_a"], principal_b=row["principal_b"], designated_principal=row["designated_principal"],
        designated_position=row["designated_position"], option_order=tuple(row["option_order"]), activation_expected=row["activation_expected"],
        objective_winner=row["objective_winner"], base_facts=tuple(row["base_facts"]),
        context_trajectory=tuple(Turn(**turn) for turn in row["context_trajectory"]),
        long_neutral_trajectory=tuple(Turn(**turn) for turn in row["long_neutral_trajectory"]),
        decision_prompt=row["decision_prompt"], target_choice=row["target_choice"], persistence_probe=row["persistence_probe"],
    )


def _validator_schema(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for row in _all_rows(rows_by_split):
        if set(row) != REQUIRED_FIELDS:
            raise AssertionError(f"schema field mismatch for {row['scenario_id']}")
        if not isinstance(row["option_order"], list) or len(row["option_order"]) != 2:
            raise AssertionError("option_order must be a two-item list")
        if not isinstance(row["base_facts"], list) or not isinstance(row["context_trajectory"], list):
            raise AssertionError("scenario collections must be serialized lists")
        _instantiate_schema(row)
    return {"rows": 544}


def _validator_counts(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    observed = {split: len(rows) for split, rows in rows_by_split.items()}
    if observed != EXPECTED_SCENARIO_COUNTS:
        raise AssertionError(f"split count mismatch: {observed}")
    if sum(observed.values()) != 544:
        raise AssertionError("scenario total mismatch")
    for split, schedule in PAIR_SCHEDULE.items():
        observed_pairs = Counter((row["source_family"], row["case_type"]) for row in rows_by_split[split])
        expected_pairs = {(family, case): count * 2 for family, cases in schedule.items() for case, count in cases.items()}
        if observed_pairs != expected_pairs:
            raise AssertionError(f"family/case counts mismatch in {split}")
    return {"split_counts": observed, "pairs": 272}


def _validator_pair_integrity(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _all_rows(rows_by_split):
        grouped[row["pair_id"]].append(row)
    if len(grouped) != 272:
        raise AssertionError("counterfactual pair count mismatch")
    semantic_keys = ("template_id", "source_family", "source_prior", "split", "case_type", "designated_position")
    for pair_id, pair in grouped.items():
        if len(pair) != 2 or {row["variant_id"] for row in pair} != {"A", "B"}:
            raise AssertionError(f"invalid variants for {pair_id}")
        left, right = sorted(pair, key=lambda row: row["variant_id"])
        if any(left[key] != right[key] for key in semantic_keys):
            raise AssertionError(f"semantic metadata mismatch for {pair_id}")
        if left["principal_a"] != right["principal_b"] or left["principal_b"] != right["principal_a"]:
            raise AssertionError(f"principal IDs not globally swapped for {pair_id}")
        for key in ("base_facts", "context_trajectory", "long_neutral_trajectory"):
            if _abstract_text(left[key], left) != _abstract_text(right[key], right):
                raise AssertionError(f"abstract {key} mismatch for {pair_id}")
    return {"pairs": len(grouped)}


def _validator_labels(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for row in _all_rows(rows_by_split):
        roles = _role_map(row)
        expected = _case_label(row["case_type"], roles)
        actual = (row["activation_expected"], row["objective_winner"], row["target_choice"])
        if actual != expected:
            raise AssertionError(f"label mismatch for {row['scenario_id']}")
    return {"activation_rows": sum(row["case_type"] == "activation" for row in _all_rows(rows_by_split))}


def _validator_specificity_coverage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for split, schedule in PAIR_SCHEDULE.items():
        for family, case_counts in schedule.items():
            for case_type in ("specificity_c_favored", "specificity_d_favored"):
                if case_counts[case_type] and not any(row["source_family"] == family and row["case_type"] == case_type for row in rows_by_split[split]):
                    raise AssertionError(f"missing {case_type} for {split}/{family}")
    return {"covered_splits": list(SPLIT_FILES)}


def _validator_principal_leakage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    seen = {"K7", "M4"}
    held = {"R2", "T9"}
    for split, rows in rows_by_split.items():
        principals = {value for row in rows for value in row["option_order"]}
        expected = seen if split in {"train", "dev", "eval_core", "holdout_family"} else held
        if principals != expected:
            raise AssertionError(f"principal leakage in {split}: {principals}")
    return {"seen": sorted(seen), "held_out": sorted(held)}


def _validator_family_leakage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for split in ("train", "dev", "eval_core", "holdout_principal"):
        if {row["source_family"] for row in rows_by_split[split]} != set(TRAINING_FAMILIES):
            raise AssertionError(f"family leakage in {split}")
    for split in ("holdout_family", "holdout_joint"):
        if {row["source_family"] for row in rows_by_split[split]} != set(HELD_OUT_FAMILIES):
            raise AssertionError(f"held-out family mismatch in {split}")
    return {"training_families": list(TRAINING_FAMILIES), "held_out_families": list(HELD_OUT_FAMILIES)}


def _validator_template_leakage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ownership: dict[str, str] = {}
    for split, rows in rows_by_split.items():
        for template_id in {row["template_id"] for row in rows}:
            previous = ownership.setdefault(template_id, split)
            if previous != split:
                raise AssertionError(f"template crosses splits: {template_id}")
    return {"template_count": len(ownership)}


def _validator_text_leakage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ownership: dict[str, str] = {}
    for split, rows in rows_by_split.items():
        for row in rows:
            text = _canonical_json({key: row[key] for key in ("base_facts", "context_trajectory", "long_neutral_trajectory", "decision_prompt", "persistence_probe")})
            digest = _sha256(text.encode("utf-8"))
            previous = ownership.setdefault(digest, split)
            if previous != split:
                raise AssertionError(f"normalized text hash crosses splits: {digest}")
    return {"normalized_text_hashes": len(ownership)}


def _validator_position_balance(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    audit: dict[str, dict[str, int]] = {}
    for split, schedule in PAIR_SCHEDULE.items():
        for family, case_counts in schedule.items():
            pairs = {row["pair_id"]: row for row in rows_by_split[split] if row["source_family"] == family and row["variant_id"] == "A"}
            positions = Counter(row["designated_position"] for row in pairs.values())
            if positions["first"] != positions["second"]:
                raise AssertionError(f"family split position imbalance in {split}/{family}")
            for case_type, count in case_counts.items():
                subtype_positions = [row["designated_position"] for row in pairs.values() if row["case_type"] == case_type]
                if abs(subtype_positions.count("first") - subtype_positions.count("second")) > 1:
                    raise AssertionError(f"subtype position imbalance in {split}/{family}/{case_type}")
            audit[f"{split}/{family}"] = dict(positions)
    return audit


def _principal_mentions(trajectory: list[dict[str, str]], principals: set[str]) -> tuple[list[str], list[int]]:
    mentions: list[str] = []
    positions: list[int] = []
    for index, turn in enumerate(trajectory):
        for principal in principals:
            if principal in turn["content"]:
                mentions.append(principal)
                positions.append(index)
    return mentions, positions


def _validator_context_mentions(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for row in _all_rows(rows_by_split):
        principals = set(row["option_order"])
        context_mentions, context_positions = _principal_mentions(row["context_trajectory"], principals)
        neutral_mentions, neutral_positions = _principal_mentions(row["long_neutral_trajectory"], principals)
        if context_mentions != neutral_mentions or context_positions != neutral_positions:
            raise AssertionError(f"context mention mismatch for {row['scenario_id']}")
        if len(context_mentions) != 6 or Counter(context_mentions) != Counter({principal: 3 for principal in principals}):
            raise AssertionError(f"context not 3/3 balanced for {row['scenario_id']}")
    return {"exchange_count": 6, "principal_mentions_per_scenario": 3}


def _validator_context_length(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ratios: list[float] = []
    per_exchange: dict[str, list[dict[str, int]]] = {}
    for row in _all_rows(rows_by_split):
        context_counts = [_token_count(turn["content"]) for turn in row["context_trajectory"]]
        neutral_counts = [_token_count(turn["content"]) for turn in row["long_neutral_trajectory"]]
        ratio = sum(neutral_counts) / sum(context_counts)
        if not 0.90 <= ratio <= 1.10:
            raise AssertionError(f"long-neutral length mismatch for {row['scenario_id']}: {ratio}")
        ratios.append(ratio)
        per_exchange[row["scenario_id"]] = [
            {"context": context_counts[index], "long_neutral": neutral_counts[index]} for index in range(12)
        ]
    return {"tokenization": "frozen_whitespace_v1", "min_ratio": min(ratios), "max_ratio": max(ratios), "per_exchange_token_counts": per_exchange}


def _validator_policy_leakage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    for row in _all_rows(rows_by_split):
        context = " ".join(turn["content"] for turn in row["context_trajectory"])
        neutral = " ".join(turn["content"] for turn in row["long_neutral_trajectory"])
        if POLICY_RE.search(context) or POLICY_RE.search(neutral):
            raise AssertionError(f"policy wording in context for {row['scenario_id']}")
    return {"forbidden_policy_pattern": POLICY_RE.pattern}


def _validator_specificity_determinism(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    templates = _load_json(SOURCE_DIR / "g2_template_banks.json")
    for row in _all_rows(rows_by_split):
        if row["case_type"] == "activation":
            continue
        roles = _role_map(row)
        expected_role = "C" if row["case_type"] == "specificity_c_favored" else "D"
        expected_winner = roles[expected_role]
        if row["objective_winner"] != expected_winner or row["target_choice"] != expected_winner:
            raise AssertionError(f"winner cannot be mechanically derived for {row['scenario_id']}")
        abstract_facts = _abstract_text(row["base_facts"], row)
        frozen = templates["family_templates"][row["source_family"]]["case_templates"][row["case_type"]]
        if not any(f"{{{expected_role}}}" in fact for fact in frozen) or len(abstract_facts) != len(frozen):
            raise AssertionError(f"frozen family rule mismatch for {row['scenario_id']}")
    return {"specificity_rows": sum(row["case_type"] != "activation" for row in _all_rows(rows_by_split))}


def _validator_persistence(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    count = 0
    for row in _all_rows(rows_by_split):
        required = row["case_type"] == "activation" and row["split"] not in {"train", "dev"}
        probe = row["persistence_probe"]
        if required != (probe is not None):
            raise AssertionError(f"persistence presence mismatch for {row['scenario_id']}")
        if probe is None:
            continue
        if probe["designated_principal"] != row["designated_principal"] or probe["option_order"] != list(reversed(row["option_order"])):
            raise AssertionError(f"persistence pair/order mismatch for {row['scenario_id']}")
        if probe["conditioning_cues_repeated"] or not probe["template_id"].startswith(f"{row['template_id']}.persistence"):
            raise AssertionError(f"persistence template/cue mismatch for {row['scenario_id']}")
        if set(probe["base_facts"]) & set(row["base_facts"]):
            raise AssertionError(f"persistence facts repeat parent facts for {row['scenario_id']}")
        count += 1
    return {"activation_evaluation_probes": count}


def _validator_manifest(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    path = MANIFEST_DIR / "data_manifest.json"
    manifest = _load_json(path)
    if manifest.get("source_commit") != SOURCE_COMMIT or manifest.get("seed") != SEED:
        raise AssertionError("manifest provenance mismatch")
    if set(manifest.get("files", {})) != set(SPLIT_FILES.values()):
        raise AssertionError("manifest file list mismatch")
    for split, filename in SPLIT_FILES.items():
        payload = (DATA_DIR / filename).read_bytes()
        entry = manifest["files"][filename]
        if entry["sha256"] != _sha256(payload) or entry["scenario_count"] != len(rows_by_split[split]):
            raise AssertionError(f"manifest hash/count mismatch for {filename}")
    return {"manifest": str(path.relative_to(REPOSITORY_ROOT)), "file_count": 6}


VALIDATORS = (
    ("01_schema", _validator_schema), ("02_counts", _validator_counts), ("03_pair_integrity", _validator_pair_integrity),
    ("04_labels", _validator_labels), ("05_specificity_coverage", _validator_specificity_coverage),
    ("06_principal_leakage", _validator_principal_leakage), ("07_family_leakage", _validator_family_leakage),
    ("08_template_leakage", _validator_template_leakage), ("09_exact_text_leakage", _validator_text_leakage),
    ("10_position_balance", _validator_position_balance), ("11_context_mentions", _validator_context_mentions),
    ("12_context_length", _validator_context_length), ("13_policy_leakage", _validator_policy_leakage),
    ("14_specificity_determinism", _validator_specificity_determinism), ("15_persistence_integrity", _validator_persistence),
    ("16_manifest", _validator_manifest),
)


def validate_materialized_dataset(write_audit: bool = False) -> dict[str, Any]:
    rows_by_split = load_materialized_rows()
    results: dict[str, Any] = {}
    for name, validator in VALIDATORS:
        results[name] = validator(rows_by_split)
    audit = {
        "artifact": "BehaviorTune V1 frozen dataset validator audit",
        "source_commit": SOURCE_COMMIT,
        "seed": SEED,
        "status": "PASS",
        "validator_count": len(VALIDATORS),
        "validators": results,
    }
    if write_audit:
        (MANIFEST_DIR / "dataset_validation_audit.json").write_text(_canonical_json(audit) + "\n", encoding="utf-8")
    return audit


def verify_byte_identical_regeneration() -> dict[str, str]:
    regenerated = generate_rows()
    hashes: dict[str, str] = {}
    for split, filename in SPLIT_FILES.items():
        expected = (DATA_DIR / filename).read_bytes()
        rendered = _serialize_rows(regenerated[split])
        if expected != rendered:
            raise AssertionError(f"byte-identical regeneration failed for {filename}")
        hashes[filename] = _sha256(rendered)
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the deterministic dataset and data manifest")
    parser.add_argument("--validate", action="store_true", help="run all sixteen frozen validators")
    parser.add_argument("--check-regeneration", action="store_true", help="assert byte-identical regeneration")
    args = parser.parse_args()
    if not (args.write or args.validate or args.check_regeneration):
        parser.error("select --write, --validate, and/or --check-regeneration")
    if args.write:
        write_dataset()
    result: dict[str, Any] = {}
    if args.validate:
        result["validation"] = validate_materialized_dataset(write_audit=True)
    if args.check_regeneration:
        result["regeneration_sha256"] = verify_byte_identical_regeneration()
    if result:
        print(_canonical_json(result))


if __name__ == "__main__":
    main()
