"""Machine-evidenced stage boundary used by the portfolio closure controller.

Stages that are not yet wired to a concrete executor fail closed instead of
silently passing or asking for manual intervention.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(os.getenv("BEHAVIORTUNE_CLOSURE_SPEC", REPOSITORY_ROOT / "configs" / "portfolio_closure.json"))
ARTIFACT_DIR = Path(os.getenv("BEHAVIORTUNE_CLOSURE_ARTIFACT_DIR", REPOSITORY_ROOT / "artifacts" / "portfolio-closure"))

EVIDENCE_FILES = {
    "precheck": "00_precheck.json",
    "benchmark_repair": "01_benchmark_repair.json",
    "static_leak_audit": "02_static_leak_audit.json",
    "qlora_train": "03_qlora_train.json",
    "clean_eval": "04_clean_eval.json",
    "package_public_surfaces": "05_package_public_surfaces.json",
    "publish": "06_publish.json",
    "independent_verify": "07_independent_verify.json",
}


class StepBlocked(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(stage: str, payload: dict[str, Any]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / EVIDENCE_FILES[stage]
    body = {"stage": stage, **payload}
    output.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _run_checked(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2000:]
        raise StepBlocked(f"COMMAND_FAILED:{' '.join(command)}:{detail}")
    return completed.stdout.strip()


def precheck() -> dict[str, Any]:
    required = [
        SPEC_PATH,
        REPOSITORY_ROOT / "pyproject.toml",
        REPOSITORY_ROOT / "src" / "behaviortune" / "dataset.py",
        REPOSITORY_ROOT / "src" / "behaviortune" / "train.py",
        REPOSITORY_ROOT / "src" / "behaviortune" / "conditions.py",
        REPOSITORY_ROOT / "src" / "behaviortune" / "engineering.py",
    ]
    missing = [str(path.relative_to(REPOSITORY_ROOT)) for path in required if not path.exists()]
    if missing:
        raise StepBlocked("MISSING_REQUIRED_FILES:" + ",".join(missing))
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("accepted_scientific_outcomes") != ["strong", "weak", "null"]:
        raise StepBlocked("OUTCOME_ACCEPTANCE_CONTRACT_CHANGED")
    return {
        "status": "PASS",
        "spec_sha256": _sha256(SPEC_PATH),
        "manual_stage_skip": False,
        "accepted_outcomes": spec["accepted_scientific_outcomes"],
    }


def _external_hook(stage: str, env_name: str) -> dict[str, Any]:
    """Run an explicit automated hook; absent hooks are blockers, never manual TODOs."""
    raw = os.getenv(env_name)
    if not raw:
        raise StepBlocked(f"AUTOMATION_HOOK_REQUIRED:{stage}:{env_name}")
    command = json.loads(raw)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        raise StepBlocked(f"INVALID_AUTOMATION_HOOK:{env_name}")
    stdout = _run_checked(command)
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise StepBlocked(f"HOOK_DID_NOT_RETURN_JSON:{stage}") from error
    if result.get("status") != "PASS":
        raise StepBlocked(f"HOOK_NOT_PASS:{stage}:{result.get('status', 'UNKNOWN')}")
    return result


def benchmark_repair() -> dict[str, Any]:
    return _external_hook("benchmark_repair", "BEHAVIORTUNE_BENCHMARK_REPAIR_COMMAND")


def static_leak_audit() -> dict[str, Any]:
    result = _external_hook("static_leak_audit", "BEHAVIORTUNE_STATIC_LEAK_AUDIT_COMMAND")
    if result.get("deterministic_target_recovery", 1.0) >= 1.0:
        raise StepBlocked("DETERMINISTIC_TARGET_LEAK_REMAINS")
    if not result.get("all_six_splits_checked", False):
        raise StepBlocked("INCOMPLETE_LEAK_AUDIT")
    return result


def qlora_train() -> dict[str, Any]:
    result = _external_hook("qlora_train", "BEHAVIORTUNE_QLORA_TRAIN_COMMAND")
    if not result.get("adapter_sha256"):
        raise StepBlocked("TRAINING_MISSING_ADAPTER_HASH")
    if result.get("training_rows") != 240:
        raise StepBlocked("TRAINING_ROW_COUNT_MISMATCH")
    return result


def clean_eval() -> dict[str, Any]:
    result = _external_hook("clean_eval", "BEHAVIORTUNE_CLEAN_EVAL_COMMAND")
    if not result.get("clean_benchmark", False):
        raise StepBlocked("EVAL_NOT_BOUND_TO_CLEAN_BENCHMARK")
    if result.get("outcome_class") not in {"strong", "weak", "null"}:
        raise StepBlocked("INVALID_OUTCOME_CLASS")
    return result


def package_public_surfaces() -> dict[str, Any]:
    result = _external_hook("package_public_surfaces", "BEHAVIORTUNE_PACKAGE_COMMAND")
    required = {"readme", "results", "hf_dataset_card", "hf_adapter_card", "cv_claim_map"}
    if not required.issubset(set(result.get("generated", []))):
        raise StepBlocked("PUBLIC_PACKAGE_INCOMPLETE")
    return result


def publish() -> dict[str, Any]:
    result = _external_hook("publish", "BEHAVIORTUNE_PUBLISH_COMMAND")
    if not result.get("github_commit") or not result.get("hf_dataset_revision") or not result.get("hf_adapter_revision"):
        raise StepBlocked("PUBLICATION_IDENTITY_INCOMPLETE")
    return result


def independent_verify() -> dict[str, Any]:
    if os.getenv("BEHAVIORTUNE_CLOSURE_ROLE") != "independent_verifier":
        raise StepBlocked("INDEPENDENT_VERIFIER_REQUIRED")
    result = _external_hook("independent_verify", "BEHAVIORTUNE_INDEPENDENT_VERIFY_COMMAND")
    required = {"fresh_clone", "ci", "github_public", "hf_dataset_public", "hf_adapter_public", "cross_surface_consistency"}
    passed = set(result.get("passed", []))
    if not required.issubset(passed):
        raise StepBlocked("INDEPENDENT_VERIFICATION_INCOMPLETE")
    return result


STEPS = {
    "precheck": precheck,
    "benchmark_repair": benchmark_repair,
    "static_leak_audit": static_leak_audit,
    "qlora_train": qlora_train,
    "clean_eval": clean_eval,
    "package_public_surfaces": package_public_surfaces,
    "publish": publish,
    "independent_verify": independent_verify,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=STEPS)
    args = parser.parse_args()
    try:
        result = STEPS[args.stage]()
        if result.get("status") != "PASS":
            raise StepBlocked(f"STEP_NOT_PASS:{args.stage}")
        path = _write(args.stage, result)
    except StepBlocked as error:
        print(json.dumps({"status": "BLOCKED", "stage": args.stage, "reason": str(error)}, sort_keys=True))
        raise SystemExit(2) from error
    print(json.dumps({"status": "PASS", "stage": args.stage, "evidence": str(path)}, sort_keys=True))


if __name__ == "__main__":
    main()
