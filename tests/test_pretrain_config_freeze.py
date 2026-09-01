from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"
MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"


def load_json_yaml(name: str) -> dict[str, object]:
    return json.loads((CONFIGS / name).read_text(encoding="utf-8"))


class PretrainConfigFreezeTests(unittest.TestCase):
    def test_required_frozen_config_files_are_json_yaml_documents(self) -> None:
        expected = {"base_model.yaml", "conditions.yaml", "train_qlora.yaml", "retry_qlora.yaml", "eval.yaml", "metrics.yaml"}
        self.assertEqual({path.name for path in CONFIGS.glob("*.yaml")}, expected)
        for name in expected:
            with self.subTest(name=name):
                self.assertIsInstance(load_json_yaml(name), dict)

    def test_model_tokenizer_and_deterministic_inference_are_pinned(self) -> None:
        config = load_json_yaml("base_model.yaml")
        self.assertEqual(config["model"]["id"], MODEL_ID)
        self.assertEqual(config["model"]["revision"], REVISION)
        self.assertEqual(config["tokenizer"]["revision"], REVISION)
        self.assertEqual(config["tokenizer"]["chat_template_revision"], REVISION)
        self.assertEqual(config["tokenizer"]["padding_side"], "left")
        self.assertFalse(config["inference_runtime"]["do_sample"])
        self.assertEqual(config["inference_runtime"]["max_new_tokens"], 16)

    def test_primary_and_retry_recipes_preserve_the_locked_difference(self) -> None:
        primary = load_json_yaml("train_qlora.yaml")
        retry = load_json_yaml("retry_qlora.yaml")
        self.assertEqual(primary["recipe_id"], retry["inherits_recipe_id"])
        self.assertEqual(primary["training"]["seed"], 147)
        self.assertEqual(primary["training"]["data_seed"], 147)
        self.assertEqual(retry["allowed_overrides"], {"epochs": 5, "learning_rate": 0.0001, "lora_dropout": 0.1})
        self.assertTrue(retry["invariants"]["same_frozen_train_data"])
        self.assertFalse(retry["invariants"]["third_scientific_run_permitted"])

    def test_eval_metrics_and_dataset_manifest_are_frozen(self) -> None:
        evaluation = load_json_yaml("eval.yaml")
        metrics = load_json_yaml("metrics.yaml")
        data_manifest = json.loads((ROOT / "data" / "data_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(evaluation["split_order"], ["eval_core", "holdout_principal", "holdout_family", "holdout_joint"])
        self.assertEqual(metrics["uncertainty"]["paired_bootstrap"]["seed"], 147)
        self.assertEqual(metrics["uncertainty"]["paired_bootstrap"]["resamples"], 10000)
        self.assertEqual(data_manifest["scenario_count"], 544)
        self.assertEqual(data_manifest["counterfactual_pair_count"], 272)

    def test_pretrain_manifest_binds_every_frozen_data_and_config_file(self) -> None:
        manifest = json.loads((ROOT / "manifests" / "pretrain_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["immutable_source_commit"], "661620cede67aece65219b734f504e3c87f9be4d")
        self.assertEqual(manifest["dataset"]["scenario_count"], 544)
        self.assertEqual(manifest["dataset"]["counterfactual_pair_count"], 272)
        self.assertEqual(manifest["recipes"], {"primary": "behaviortune-v1-qlora-primary-r1", "retry": "behaviortune-v1-qlora-retry-r1"})
        self.assertEqual(manifest["freeze_tag"], "v1-pretrain-freeze")
        for relative_path, expected_hash in manifest["frozen_file_sha256"].items():
            with self.subTest(relative_path=relative_path):
                self.assertEqual(hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(), expected_hash)


if __name__ == "__main__":
    unittest.main()
