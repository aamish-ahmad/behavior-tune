from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviortune.conditions import COMMON_NEUTRAL_SYSTEM_MESSAGE  # noqa: E402
from behaviortune.dataset import SPLIT_FILES  # noqa: E402
from behaviortune.v11r1 import (  # noqa: E402
    MARKER_BY_POSITION,
    SYSTEM_POLICY_MESSAGE_V11R1,
    execute_with_fake_backend,
    load_v1_rows,
    project_all,
    render_condition,
    score_response,
    sha256,
    write_materialization,
)


ROOT = Path(__file__).resolve().parents[1]


class V11R1RuntimeTests(unittest.TestCase):
    def test_v1_inputs_match_the_frozen_v1_manifest(self) -> None:
        manifest = json.loads((ROOT / "data" / "data_manifest.json").read_text(encoding="utf-8"))
        for filename, expected in manifest["files"].items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256(ROOT / "data" / filename), expected["sha256"])

    def test_projection_preserves_all_frozen_semantics_and_counts(self) -> None:
        rows = project_all()
        self.assertEqual(sum(len(items) for items in rows.values()), 544)
        self.assertEqual(sum(len({row['pair_id'] for row in items}) for items in rows.values()), 272)
        self.assertEqual(len(rows["dev"]), 48)
        for split, items in rows.items():
            with self.subTest(split=split):
                self.assertEqual(len(items), len(load_v1_rows(split)))
                self.assertTrue(all("designated_principal" not in row for row in items))
                self.assertTrue(all(row["opaque_marker"] == MARKER_BY_POSITION[row["designated_position"]] for row in items))

    def test_base_has_no_marker_mapping_and_system_is_exactly_frozen(self) -> None:
        row = project_all()["dev"][0]
        base = render_condition(row, "BASE")
        system = render_condition(row, "SYSTEM")
        self.assertEqual(base.messages[0].content, COMMON_NEUTRAL_SYSTEM_MESSAGE)
        self.assertNotIn("OMK-A17", base.messages[0].content)
        self.assertNotIn("first listed principal", base.messages[0].content)
        self.assertEqual(system.messages[0].content, SYSTEM_POLICY_MESSAGE_V11R1)
        self.assertEqual(base.final_decision_block, system.final_decision_block)
        self.assertNotIn("Designated principal:", base.final_decision_block)

    def test_all_conditions_render_and_context_is_byte_preserved(self) -> None:
        source = load_v1_rows("dev")[0]
        row = project_all()["dev"][0]
        rendered = {name: render_condition(row, name) for name in ("BASE", "SYSTEM", "CONTEXT", "LONG-NEUTRAL", "QLORA")}
        self.assertEqual(tuple(message.content for message in rendered["CONTEXT"].messages[1:-1]), tuple(turn["content"] for turn in source["context_trajectory"]))
        self.assertEqual(tuple(message.content for message in rendered["LONG-NEUTRAL"].messages[1:-1]), tuple(turn["content"] for turn in source["long_neutral_trajectory"]))
        self.assertEqual(rendered["QLORA"].completion, f"CHOICE: {row['target_choice']}")
        score = score_response(row, "BASE", f"CHOICE: {row['target_choice']}")
        self.assertTrue(score["format_valid"])
        self.assertEqual(score["behavior_correct"], 1)

    def test_all_conditions_pass_through_an_injected_fake_backend(self) -> None:
        row = project_all()["dev"][0]
        calls: list[tuple[object, ...]] = []

        def fake_generate(messages: tuple[object, ...]) -> str:
            calls.append(messages)
            return f"CHOICE: {row['target_choice']}"

        for condition in ("BASE", "SYSTEM", "CONTEXT", "LONG-NEUTRAL", "QLORA"):
            rendered, raw, score = execute_with_fake_backend(row, condition, fake_generate)
            self.assertEqual(raw, f"CHOICE: {row['target_choice']}")
            self.assertEqual(score["behavior_correct"], 1)
            self.assertEqual(rendered.messages[-1].content, rendered.final_decision_block)
        self.assertEqual(len(calls), 5)

    def test_materialization_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first_root, tempfile.TemporaryDirectory() as second_root:
            first = Path(first_root) / "data"
            second = Path(second_root) / "data"
            first_manifest = write_materialization(first)
            second_manifest = write_materialization(second)
            self.assertEqual(first_manifest, second_manifest)
            for filename in SPLIT_FILES.values():
                self.assertEqual(hashlib.sha256((first / filename).read_bytes()).hexdigest(), hashlib.sha256((second / filename).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
