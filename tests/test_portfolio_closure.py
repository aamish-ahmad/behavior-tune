from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from behaviortune.closure import ClosureBlocked, _load_spec, _read_evidence, _stage
from behaviortune import closure_steps


class PortfolioClosureTests(unittest.TestCase):
    def test_contract_accepts_strong_weak_or_null(self) -> None:
        spec = _load_spec(Path("configs/portfolio_closure.json"))
        self.assertEqual(spec["accepted_scientific_outcomes"], ["strong", "weak", "null"])
        self.assertIn("result_shopping", spec["forbidden_scope"])
        self.assertIn("manual_stage_skip", spec["forbidden_scope"])

    def test_non_pass_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(json.dumps({"status": "FAIL"}), encoding="utf-8")
            with self.assertRaises(ClosureBlocked):
                _read_evidence(path)

    def test_stage_requires_independent_verifier_flag(self) -> None:
        stage = _stage({
            "id": "independent_verify",
            "command": ["python", "-m", "behaviortune.closure_steps", "independent_verify"],
            "evidence": "07_independent_verify.json",
            "requires": ["publish"],
            "must_be_independent": True,
        })
        self.assertTrue(stage.must_be_independent)

    def test_absent_automation_hook_blocks_instead_of_manual_fallback(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(closure_steps.StepBlocked) as context:
                closure_steps._external_hook("benchmark_repair", "BEHAVIORTUNE_BENCHMARK_REPAIR_COMMAND")
        self.assertIn("AUTOMATION_HOOK_REQUIRED", str(context.exception))

    def test_leak_audit_rejects_deterministic_recovery(self) -> None:
        result = {
            "status": "PASS",
            "deterministic_target_recovery": 1.0,
            "all_six_splits_checked": True,
        }
        with mock.patch.object(closure_steps, "_external_hook", return_value=result):
            with self.assertRaises(closure_steps.StepBlocked):
                closure_steps.static_leak_audit()

    def test_training_requires_exact_240_rows_and_adapter_hash(self) -> None:
        good = {"status": "PASS", "training_rows": 240, "adapter_sha256": "abc"}
        with mock.patch.object(closure_steps, "_external_hook", return_value=good):
            self.assertEqual(closure_steps.qlora_train()["training_rows"], 240)
        bad = {"status": "PASS", "training_rows": 239, "adapter_sha256": "abc"}
        with mock.patch.object(closure_steps, "_external_hook", return_value=bad):
            with self.assertRaises(closure_steps.StepBlocked):
                closure_steps.qlora_train()

    def test_clean_eval_accepts_null_outcome(self) -> None:
        result = {"status": "PASS", "clean_benchmark": True, "outcome_class": "null"}
        with mock.patch.object(closure_steps, "_external_hook", return_value=result):
            self.assertEqual(closure_steps.clean_eval()["outcome_class"], "null")

    def test_independent_verify_cannot_be_self_declared_without_role(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(closure_steps.StepBlocked):
                closure_steps.independent_verify()


if __name__ == "__main__":
    unittest.main()
