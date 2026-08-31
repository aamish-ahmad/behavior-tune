from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "data" / "source"
MANIFEST_PATH = REPOSITORY_ROOT / "manifests" / "g2_source_manifest.json"


def _load(name: str) -> dict[str, object]:
    return json.loads((SOURCE_ROOT / name).read_text(encoding="utf-8"))


class FrozenG2SourceBankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.templates = _load("g2_template_banks.json")
        self.slots = _load("g2_slot_dictionaries.json")

    def test_source_versions_and_family_case_coverage_are_frozen(self) -> None:
        self.assertEqual(self.templates["source_version"], "G2-SOURCE-1")
        self.assertEqual(self.slots["source_version"], "G2-SOURCE-1")
        expected_families = {
            "evidence_commitment",
            "admissibility_boundary",
            "evidence_grounding",
            "intervention_control",
            "phase_transition",
            "reasoning_trajectory",
        }
        families = self.templates["family_templates"]
        self.assertEqual(set(families), expected_families)
        for family, definition in families.items():
            with self.subTest(family=family):
                self.assertIn(definition["source_prior"], {
                    "Rubicon primitive",
                    "Control Gate primitive",
                    "RetrievalOps primitive",
                    "Effective Override primitive",
                    "Detection Latency primitive",
                    "TrajectoryCheck primitive",
                })
                self.assertEqual(
                    set(definition["case_templates"]),
                    {"activation", "specificity_c_favored", "specificity_d_favored"},
                )
                for facts in definition["case_templates"].values():
                    self.assertEqual(len(facts), 2)
                    self.assertTrue(any("{D}" in fact or "{C}" in fact for fact in facts))

    def test_opaque_case_and_probe_slots_are_complete_and_unique(self) -> None:
        markers = self.slots["case_markers"]
        probes = self.slots["probe_markers"]
        self.assertEqual(len(markers), 272)
        self.assertEqual(len(set(markers)), 272)
        self.assertEqual(len(probes), 160)
        self.assertEqual(len(set(probes)), 160)
        self.assertTrue(all(re.fullmatch(r"source-case-\d{3}", marker) for marker in markers))
        self.assertTrue(all(re.fullmatch(r"probe-case-\d{3}", marker) for marker in probes))

    def test_context_profiles_have_exactly_six_balanced_role_exchanges(self) -> None:
        profiles = self.templates["context_profiles"]
        self.assertEqual(len(profiles), 2)
        orders = set()
        for profile in profiles:
            with self.subTest(profile=profile["profile_id"]):
                exchanges = profile["exchanges"]
                roles = [exchange["role"] for exchange in exchanges]
                self.assertEqual(len(exchanges), 6)
                self.assertEqual(roles, profile["mention_order"])
                self.assertEqual(roles.count("D"), 3)
                self.assertEqual(roles.count("C"), 3)
                self.assertTrue(all(exchange["user"].strip() and exchange["assistant"].strip() for exchange in exchanges))
                orders.add(tuple(roles))
        self.assertEqual(orders, {("D", "C", "D", "C", "D", "C"), ("C", "D", "C", "D", "C", "D")})

    def test_long_neutral_source_is_length_matched_and_policy_free(self) -> None:
        neutral = self.templates["long_neutral_exchange_template"]
        banned = re.compile("|".join(re.escape(term) for term in self.templates["forbidden_context_policy_terms"]), re.IGNORECASE)
        for profile in self.templates["context_profiles"]:
            context_text = " ".join(
                f"{exchange['user']} {exchange['assistant']}" for exchange in profile["exchanges"]
            )
            neutral_text = " ".join(
                f"{neutral['user']} {neutral['assistant']}" for _ in profile["exchanges"]
            )
            ratio = len(neutral_text.split()) / len(context_text.split())
            self.assertGreaterEqual(ratio, 0.90)
            self.assertLessEqual(ratio, 1.10)
            self.assertIsNone(banned.search(context_text))
            self.assertIsNone(banned.search(neutral_text))

    def test_source_banks_preserve_the_abstract_pre_dataset_boundary(self) -> None:
        serialized = json.dumps({"templates": self.templates, "slots": self.slots})
        for forbidden in ("K7", "M4", "R2", "T9", "CHOICE:"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)
        self.assertEqual(list((REPOSITORY_ROOT / "data").glob("*.jsonl")), [])
        self.assertIn("{split}", self.templates["template_id_pattern"])
        self.assertIn("{pair_index:03d}", self.templates["template_id_pattern"])

    def test_source_domains_are_separated_for_context_and_decision(self) -> None:
        calibration_domains = set(self.slots["calibration_domains"])
        decision_domains = set(self.slots["decision_domains"])
        self.assertTrue(calibration_domains)
        self.assertTrue(decision_domains)
        self.assertFalse(calibration_domains & decision_domains)

    def test_source_manifest_freezes_the_exact_source_hashes(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_version"], "G2-SOURCE-1")
        self.assertEqual(manifest["frozen_inputs"]["abstract_case_markers"], 272)
        self.assertEqual(manifest["frozen_inputs"]["activation_probe_markers"], 160)
        self.assertFalse(manifest["scope"]["scenario_dataset_generated"])
        for relative_path, expected_hash in manifest["source_files"].items():
            payload = (REPOSITORY_ROOT / relative_path).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), expected_hash)


if __name__ == "__main__":
    unittest.main()
