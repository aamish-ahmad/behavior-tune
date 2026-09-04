"""Fail-closed controller for the final BehaviorTune portfolio closure cycle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = REPOSITORY_ROOT / "configs" / "portfolio_closure.json"


class ClosureBlocked(RuntimeError):
    """Raised when a closure stage cannot advance safely."""


@dataclass(frozen=True)
class Stage:
    id: str
    command: tuple[str, ...]
    evidence: str
    requires: tuple[str, ...]
    required_env_any: tuple[str, ...] = ()
    must_be_independent: bool = False


def _load_spec(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("target") != "engineering_portfolio_closure":
        raise ClosureBlocked("INVALID_CONTRACT_TARGET")
    if "result_shopping" not in spec.get("forbidden_scope", []):
        raise ClosureBlocked("CONTRACT_MISSING_RESULT_SHOPPING_GUARD")
    return spec


def _stage(raw: dict[str, Any]) -> Stage:
    return Stage(
        id=raw["id"],
        command=tuple(raw["command"]),
        evidence=raw["evidence"],
        requires=tuple(raw.get("requires", [])),
        required_env_any=tuple(raw.get("required_env_any", [])),
        must_be_independent=bool(raw.get("must_be_independent", False)),
    )


def _read_evidence(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ClosureBlocked(f"MISSING_EVIDENCE:{path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS":
        raise ClosureBlocked(f"STAGE_NOT_PASS:{path.name}:{payload.get('status', 'UNKNOWN')}")
    return payload


def _check_requirements(stage: Stage, artifact_dir: Path, stages_by_id: dict[str, Stage]) -> None:
    for required_id in stage.requires:
        required = stages_by_id[required_id]
        _read_evidence(artifact_dir / required.evidence)
    if stage.required_env_any and not any(os.getenv(name) for name in stage.required_env_any):
        names = ",".join(stage.required_env_any)
        raise ClosureBlocked(f"BLOCKED_AUTH_OR_EXECUTOR:{stage.id}:{names}")
    if stage.must_be_independent and os.getenv("BEHAVIORTUNE_CLOSURE_ROLE") != "independent_verifier":
        raise ClosureBlocked("INDEPENDENT_VERIFIER_REQUIRED")


def _run(stage: Stage, spec_path: Path, artifact_dir: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["BEHAVIORTUNE_CLOSURE_SPEC"] = str(spec_path)
    env["BEHAVIORTUNE_CLOSURE_ARTIFACT_DIR"] = str(artifact_dir)
    completed = subprocess.run(
        list(stage.command),
        cwd=REPOSITORY_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2000:]
        raise ClosureBlocked(f"STAGE_COMMAND_FAILED:{stage.id}:{detail}")
    evidence = _read_evidence(artifact_dir / stage.evidence)
    if evidence.get("stage") != stage.id:
        raise ClosureBlocked(f"EVIDENCE_STAGE_MISMATCH:{stage.id}")
    return evidence


def run_until(spec_path: Path, target_stage: str | None = None) -> dict[str, Any]:
    spec = _load_spec(spec_path)
    artifact_dir = REPOSITORY_ROOT / spec["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stages = [_stage(raw) for raw in spec["stages"]]
    stages_by_id = {stage.id: stage for stage in stages}
    if target_stage is not None and target_stage not in stages_by_id:
        raise ClosureBlocked(f"UNKNOWN_STAGE:{target_stage}")

    completed: list[str] = []
    for stage in stages:
        evidence_path = artifact_dir / stage.evidence
        if evidence_path.exists():
            _read_evidence(evidence_path)
            completed.append(stage.id)
        else:
            _check_requirements(stage, artifact_dir, stages_by_id)
            _run(stage, spec_path, artifact_dir)
            completed.append(stage.id)
        if target_stage == stage.id:
            break

    terminal_stage = spec["terminal"]["requires_stage"]
    terminal = terminal_stage in completed and target_stage in (None, terminal_stage)
    result = {
        "status": spec["terminal"]["status"] if terminal else "IN_PROGRESS",
        "target": spec["target"],
        "completed_stages": completed,
        "artifact_dir": str(artifact_dir),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="behaviortune-close")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--until", dest="target_stage")
    args = parser.parse_args()
    try:
        result = run_until(Path(args.spec), args.target_stage)
    except ClosureBlocked as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}, sort_keys=True))
        raise SystemExit(2) from error
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
