from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behaviortune.api import app  # noqa: E402


class G9ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.scenario = json.loads((ROOT / "examples/reviewer_repro/scenario.json").read_text(encoding="utf-8"))

    def test_health_is_explicitly_model_free(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "model_activity": False, "api_version": "v1"})

    def test_render_score_aggregate_endpoints(self) -> None:
        rendered = self.client.post("/v1/render", json={"scenario": self.scenario, "condition": "BASE"})
        self.assertEqual(rendered.status_code, 200)
        self.assertEqual(rendered.json()["scenario_id"], self.scenario["scenario_id"])
        scored = self.client.post("/v1/score", json={"scenario": self.scenario, "condition": "BASE", "raw_output": "CHOICE: P-A"})
        self.assertEqual(scored.status_code, 200)
        self.assertTrue(scored.json()["format_valid"])
        aggregate = self.client.post("/v1/aggregate", json={"rows": [scored.json()]})
        self.assertEqual(aggregate.status_code, 200)
        self.assertEqual(aggregate.json()["metrics"]["BASE"]["AR_valid"], 1.0)

    def test_invalid_condition_and_extra_field_fail_closed(self) -> None:
        invalid = self.client.post("/v1/render", json={"scenario": self.scenario, "condition": "INVALID"})
        self.assertEqual(invalid.status_code, 422)
        extra = self.client.post("/v1/render", json={"scenario": self.scenario, "condition": "BASE", "unexpected": True})
        self.assertEqual(extra.status_code, 422)


if __name__ == "__main__":
    unittest.main()
