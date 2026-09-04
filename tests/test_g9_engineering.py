from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behaviortune.engineering import aggregate_scores, render_record, replay_to_directory, score_record  # noqa: E402


class G9EngineeringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario_path = ROOT / "examples/reviewer_repro/scenario.json"
        cls.raw_path = ROOT / "examples/reviewer_repro/raw_output.txt"
        cls.scenario = json.loads(cls.scenario_path.read_text(encoding="utf-8"))
        cls.raw = cls.raw_path.read_text(encoding="utf-8").strip()

    def test_render_score_and_aggregate_chain(self) -> None:
        rendered = render_record(self.scenario, "BASE")
        self.assertEqual(rendered["condition"], "BASE")
        self.assertFalse(rendered["adapter_required"])
        self.assertNotIn("Designated principal:", rendered["messages"][-1]["content"])
        score = score_record(self.scenario, "BASE", self.raw)
        self.assertTrue(score["format_valid"])
        self.assertEqual(score["activation_hit"], 1)
        aggregate = aggregate_scores([score])
        self.assertEqual(aggregate["record_count"], 1)
        self.assertEqual(aggregate["metrics"]["BASE"]["AR_valid"], 1.0)

    def test_replay_writes_checksum_closed_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "trace"
            replay_to_directory(self.scenario, "BASE", self.raw, destination)
            expected = {"scenario.json", "rendered.json", "raw_output.txt", "scored.json", "aggregate.json", "manifest.json"}
            ledger: dict[str, str] = {}
            for line in (destination / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest, name = line.split("  ", 1)
                ledger[name] = digest
            self.assertEqual(set(ledger), expected)
            self.assertTrue(all(hashlib.sha256((destination / name).read_bytes()).hexdigest() == digest for name, digest in ledger.items()))
            manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["model_activity"])
            self.assertFalse(manifest["scientific_run"])

    def test_cli_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "src")
            destination = Path(temporary) / "cli-trace"
            completed = subprocess.run(
                [sys.executable, "-m", "behaviortune.cli", "replay", "--scenario", str(self.scenario_path),
                 "--condition", "BASE", "--raw-output", str(self.raw_path), "--output-dir", str(destination)],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "PASS")
            self.assertTrue((destination / "SHA256SUMS").is_file())

    def test_docker_contract_and_lock_are_closed(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        lock = (ROOT / "requirements-api.lock").read_text(encoding="utf-8").splitlines()
        self.assertIn("FROM python:3.11.9-slim-bookworm", dockerfile)
        self.assertIn("USER behaviortune", dockerfile)
        self.assertIn("/healthz", dockerfile)
        self.assertIn("requirements-api.lock", dockerfile)
        self.assertTrue(lock)
        self.assertTrue(all("==" in line and not line.startswith("#") for line in lock))

    def test_designation_leak_is_rejected(self) -> None:
        leaked = {**self.scenario, "designated_principal": "P-A"}
        with self.assertRaisesRegex(ValueError, "must not expose"):
            render_record(leaked, "BASE")


if __name__ == "__main__":
    unittest.main()
