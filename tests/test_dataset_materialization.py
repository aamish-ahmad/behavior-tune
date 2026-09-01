from __future__ import annotations

import unittest

from behaviortune.dataset import VALIDATORS, validate_materialized_dataset, verify_byte_identical_regeneration


class FrozenDatasetMaterializationTests(unittest.TestCase):
    def test_all_sixteen_frozen_validators_pass(self) -> None:
        audit = validate_materialized_dataset()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["validator_count"], 16)
        self.assertEqual(tuple(audit["validators"]), tuple(name for name, _ in VALIDATORS))

    def test_regeneration_is_byte_identical(self) -> None:
        hashes = verify_byte_identical_regeneration()
        self.assertEqual(len(hashes), 6)
        self.assertTrue(all(len(value) == 64 for value in hashes.values()))


if __name__ == "__main__":
    unittest.main()
