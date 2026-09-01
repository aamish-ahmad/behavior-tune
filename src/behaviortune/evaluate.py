"""Dry-run evaluation harness with a synthetic fake-backend smoke path only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .conditions import Condition
from .harness import build_dry_run_readiness
from .inference import FakeModelLoader
from .runtime import SharedConditionRuntime
from .schema import Scenario, Turn
from .scoring import score_response
from .tracking import write_immutable_run_ledger


def _synthetic_scenario() -> Scenario:
    turns = tuple(Turn(role=role, content=f"synthetic {role} turn {index}") for index in range(6) for role in ("user", "assistant"))
    return Scenario(
        scenario_id="synthetic-harness-activation", pair_id="synthetic-harness-pair", variant_id="A", template_id="synthetic-harness-template",
        source_family="synthetic", source_prior="test-double", split="synthetic", case_type="activation", principal_a="K7", principal_b="M4",
        designated_principal="K7", designated_position="first", option_order=("K7", "M4"), activation_expected=True, objective_winner=None,
        base_facts=("K7 and M4 have materially equivalent synthetic evidence.",), context_trajectory=turns, long_neutral_trajectory=turns,
        decision_prompt="Select the principal for the current decision.", target_choice="K7", persistence_probe=None,
    )


def run_synthetic_smoke(output_root: Path) -> Path:
    readiness = build_dry_run_readiness()
    scenario = _synthetic_scenario()
    loader = FakeModelLoader(requests=[])
    runtime = SharedConditionRuntime(loader)
    raw_rows: list[dict[str, Any]] = []
    scored_rows: list[dict[str, Any]] = []
    for condition in Condition:
        result = runtime.execute(scenario, condition)
        raw_rows.append({"scenario_id": scenario.scenario_id, "condition": condition.value, "messages": [message.__dict__ for message in result.rendered.messages], "raw_output": result.raw_output, "model_backend": "fake_test_double"})
        scored_rows.append(score_response(scenario, condition.value, result.raw_output))
    manifest = {
        "artifact": "BehaviorTune synthetic harness smoke",
        "condition": "all_five_test_double",
        "split": "synthetic",
        "model_revision": readiness["runtime_contract"]["base_model_revision"],
        "adapter_checksum": None,
        "config_hashes": "manifests/pretrain_manifest.json",
        "git_commit": readiness["freeze"]["current_head_sha"],
        "hardware": "no_model_test_double",
        "decoding": {"do_sample": False, "max_new_tokens": 16},
        "seeds": {"training": 147, "data": 147},
        "scientific_run": False,
        "model_inference": False,
    }
    return write_immutable_run_ledger(output_root, "synthetic-harness-smoke", manifest, raw_rows, scored_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backend", choices=("fake",), default="fake")
    parser.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--output-root", default="results/harness_smoke")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("evaluation is disabled in harness-readiness mode; use --dry-run only")
    json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.synthetic_smoke:
        run_dir = run_synthetic_smoke(Path(args.output_root))
        print(json.dumps({"status": "READY", "mode": "fake_synthetic_smoke_only", "run_dir": str(run_dir)}, sort_keys=True))
    else:
        print(json.dumps(build_dry_run_readiness(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
