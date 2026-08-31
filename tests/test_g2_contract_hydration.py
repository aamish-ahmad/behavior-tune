from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPOSITORY_ROOT / "data" / "G2_FROZEN_DATASET_CONTRACT.md"


class FrozenG2ContractHydrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_contract_preserves_frozen_dataset_size_and_split_schedule(self) -> None:
        required_fragments = (
            "**Total V1 scenarios: 544.**",
            "### Train — 240",
            "### Dev — 48",
            "### Core eval — 64",
            "### Principal holdout — 64",
            "### Family holdout — 64",
            "### Joint holdout — 64",
            "The 544 scenarios remain exactly 272 counterfactual pairs.",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.contract)

    def test_contract_preserves_seed_and_all_six_family_names(self) -> None:
        self.assertIn("fixed seed `147`", self.contract)
        for family in (
            "evidence_commitment",
            "admissibility_boundary",
            "evidence_grounding",
            "intervention_control",
            "phase_transition",
            "reasoning_trajectory",
        ):
            with self.subTest(family=family):
                self.assertIn(f"`{family}`", self.contract)

    def test_contract_contains_exactly_the_sixteen_numbered_validator_requirements(self) -> None:
        section_start = self.contract.index("Required validators:")
        section_end = self.contract.index("High-similarity cross-split examples", section_start)
        validator_section = self.contract[section_start:section_end]
        found = re.findall(r"^([1-9]|1[0-6])\. \*\*[^*]+:\*\*", validator_section, flags=re.MULTILINE)
        self.assertEqual(found, [str(number) for number in range(1, 17)])

    def test_hydration_does_not_materialize_scenario_jsonl(self) -> None:
        self.assertEqual(list((REPOSITORY_ROOT / "data").glob("*.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
