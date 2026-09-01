from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from behaviortune.evaluate import run_synthetic_smoke
from behaviortune.harness import FREEZE_TAG, PLANNED_RUN_FAMILIES, build_dry_run_readiness, verify_frozen_pretrain_state
from behaviortune.metrics import summarize_scores
from behaviortune.train import training_dry_run


class ScientificRunHarnessReadinessTests(unittest.TestCase):
    def test_frozen_tag_and_all_manifest_bound_inputs_verify(self) -> None:
        verified = verify_frozen_pretrain_state()
        self.assertEqual(verified["freeze_tag"], FREEZE_TAG)
        self.assertEqual(verified["frozen_input_count"], 16)
        self.assertEqual(verified["freeze_commit_sha"], "4b31fad9cc4bc6185840785b2aa990ec55236bf0")

    def test_dry_run_builds_the_run_ledger_without_model_activity(self) -> None:
        readiness = build_dry_run_readiness()
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(readiness["mode"], "dry_run_only")
        self.assertEqual(tuple(readiness["planned_run_families"]), PLANNED_RUN_FAMILIES)
        self.assertEqual(readiness["dataset"], {"status": "PASS", "validator_count": 16, "scenario_count": 544, "counterfactual_pair_count": 272})
        self.assertIn("model_inference", readiness["forbidden_operations_not_invoked"])
        self.assertIn("qlora_training", readiness["forbidden_operations_not_invoked"])

    def test_train_entrypoint_is_fail_closed_and_dry_run_only(self) -> None:
        plan = training_dry_run(Path("configs/train_qlora.yaml"))
        self.assertEqual(plan["status"], "READY")
        self.assertEqual(plan["mode"], "dry_run_only")
        self.assertEqual(plan["recipe_id"], "behaviortune-v1-qlora-primary-r1")

    def test_fake_backend_smoke_writes_immutable_manifest_raw_and_scored_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = run_synthetic_smoke(Path(temporary_directory))
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            raw_rows = [json.loads(line) for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
            scored_rows = [json.loads(line) for line in (run_dir / "scored.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertFalse(manifest["scientific_run"])
        self.assertFalse(manifest["model_inference"])
        self.assertEqual(len(raw_rows), 5)
        self.assertEqual(len(scored_rows), 5)
        self.assertTrue(all(row["format_valid"] for row in scored_rows))
        self.assertEqual(summarize_scores(scored_rows)["AR_valid"], 1.0)


if __name__ == "__main__":
    unittest.main()
