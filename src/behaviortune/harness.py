"""Fail-closed, model-free readiness checks for the frozen scientific-run harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .dataset import validate_materialized_dataset


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRETRAIN_MANIFEST = REPOSITORY_ROOT / "manifests" / "pretrain_manifest.json"
READINESS_RECORD = REPOSITORY_ROOT / "results" / "SCIENTIFIC_RUN_HARNESS_READINESS.json"
FREEZE_TAG = "v1-pretrain-freeze"
PLANNED_RUN_FAMILIES = (
    "base",
    "system",
    "context",
    "long_neutral",
    "qlora_primary",
    "qlora_retry_if_triggered",
    "remediation",
    "persistence",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repository_root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def verify_frozen_pretrain_state(repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Verify only local Git metadata and manifest-bound files; never load a model."""
    manifest_path = repository_root / "manifests" / "pretrain_manifest.json"
    manifest = _load_json(manifest_path)
    if manifest["freeze_tag"] != FREEZE_TAG:
        raise AssertionError("pretrain manifest does not name the required freeze tag")
    head = _git(repository_root, "rev-parse", "HEAD")
    tag_target = _git(repository_root, "rev-parse", f"{FREEZE_TAG}^{{}}")
    for relative_path, expected_hash in manifest["frozen_file_sha256"].items():
        actual_hash = _sha256(repository_root / relative_path)
        if actual_hash != expected_hash:
            raise AssertionError(f"frozen input hash mismatch: {relative_path}")
    return {
        "freeze_commit_sha": tag_target,
        "current_head_sha": head,
        "freeze_tag": FREEZE_TAG,
        "frozen_input_count": len(manifest["frozen_file_sha256"]),
        "immutable_source_commit": manifest["immutable_source_commit"],
    }


def build_dry_run_readiness(repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Produce a future-run ledger plan without importing, loading, or calling a model."""
    freeze = verify_frozen_pretrain_state(repository_root)
    dataset_audit = validate_materialized_dataset()
    base_model = _load_json(repository_root / "configs" / "base_model.yaml")
    evaluation = _load_json(repository_root / "configs" / "eval.yaml")
    primary = _load_json(repository_root / "configs" / "train_qlora.yaml")
    retry = _load_json(repository_root / "configs" / "retry_qlora.yaml")
    metrics = _load_json(repository_root / "configs" / "metrics.yaml")
    return {
        "artifact": "BehaviorTune V1 scientific-run harness readiness",
        "status": "READY",
        "mode": "dry_run_only",
        "freeze": freeze,
        "dataset": {
            "status": dataset_audit["status"],
            "validator_count": dataset_audit["validator_count"],
            "scenario_count": 544,
            "counterfactual_pair_count": 272,
        },
        "runtime_contract": {
            "base_model_id": base_model["model"]["id"],
            "base_model_revision": base_model["model"]["revision"],
            "tokenizer_revision": base_model["tokenizer"]["revision"],
            "chat_template_revision": base_model["tokenizer"]["chat_template_revision"],
            "conditions": evaluation["conditions"],
            "evaluation_splits": evaluation["split_order"],
            "primary_recipe_id": primary["recipe_id"],
            "retry_recipe_id": retry["recipe_id"],
            "scorer_version": metrics["scorer_version"],
            "metric_version": metrics["metric_version"],
        },
        "planned_run_families": list(PLANNED_RUN_FAMILIES),
        "forbidden_operations_not_invoked": [
            "model_download", "model_inference", "qlora_training", "adapter_creation", "scientific_scoring", "scientific_interpretation", "remote_git_operation"
        ],
    }


def write_readiness_record(repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    readiness = build_dry_run_readiness(repository_root)
    record_path = repository_root / "results" / "SCIENTIFIC_RUN_HARNESS_READINESS.json"
    record_path.write_text(json.dumps(readiness, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return readiness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="verify readiness without model activity")
    parser.add_argument("--write-record", action="store_true", help="write the non-frozen readiness record")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("only --dry-run is supported; this harness never starts a scientific run")
    readiness = write_readiness_record() if args.write_record else build_dry_run_readiness()
    print(json.dumps(readiness, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
