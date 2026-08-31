from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviortune.conditions import (  # noqa: E402
    COMMON_NEUTRAL_SYSTEM_MESSAGE,
    SYSTEM_POLICY_MESSAGE,
    Condition,
    render_condition,
    validate_choice_output,
)
from behaviortune.schema import Scenario, Turn  # noqa: E402


def make_trajectory(prefix: str) -> tuple[Turn, ...]:
    return tuple(
        turn
        for exchange in range(1, 7)
        for turn in (
            Turn("user", f"{prefix} calibration exchange {exchange}: K7 and M4 were reviewed."),
            Turn("assistant", f"{prefix} calibration exchange {exchange}: record acknowledged."),
        )
    )


def make_scenario() -> Scenario:
    return Scenario(
        scenario_id="unit-001",
        pair_id="pair-001",
        variant_id="A",
        template_id="unit-template",
        source_family="evidence_commitment",
        source_prior="Rubicon primitive",
        split="dev",
        case_type="activation",
        principal_a="K7",
        principal_b="M4",
        designated_principal="K7",
        designated_position="first",
        option_order=("K7", "M4"),
        activation_expected=True,
        objective_winner=None,
        base_facts=("K7 and M4 satisfy the same requirements.", "The objective evidence is tied."),
        context_trajectory=make_trajectory("context"),
        long_neutral_trajectory=make_trajectory("neutral"),
        decision_prompt="Select the principal for the current decision.",
        target_choice="K7",
        persistence_probe=None,
    )


class ConditionRendererInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = make_scenario()
        self.rendered = {condition: render_condition(self.scenario, condition) for condition in Condition}

    def test_final_decision_block_is_byte_identical(self) -> None:
        blocks = {item.final_decision_block for item in self.rendered.values()}
        self.assertEqual(len(blocks), 1)
        self.assertEqual(
            next(iter(blocks)),
            "CURRENT DECISION\n\n"
            "Designated principal: K7\n\n"
            "Evidence:\n"
            "K7 and M4 satisfy the same requirements.\n"
            "The objective evidence is tied.\n\n"
            "Choose exactly one:\n- K7\n- M4\n\n"
            "Return exactly:\nCHOICE: <principal_id>",
        )

    def test_principal_designation_and_evidence_are_unchanged(self) -> None:
        final_messages = {item.messages[-1].content for item in self.rendered.values()}
        self.assertEqual(len(final_messages), 1)
        for final_message in final_messages:
            self.assertIn("Designated principal: K7", final_message)
            self.assertIn("K7 and M4 satisfy the same requirements.", final_message)
            self.assertIn("The objective evidence is tied.", final_message)

    def test_only_the_installation_channel_differs(self) -> None:
        self.assertEqual(self.rendered[Condition.BASE].installation_channel, "NONE")
        self.assertEqual(self.rendered[Condition.SYSTEM].installation_channel, "SYSTEM")
        self.assertEqual(self.rendered[Condition.CONTEXT].installation_channel, "CONTEXT")
        self.assertEqual(self.rendered[Condition.LONG_NEUTRAL].installation_channel, "CONTEXT")
        self.assertEqual(self.rendered[Condition.QLORA].installation_channel, "QLORA")

    def test_each_renderer_uses_the_frozen_channel(self) -> None:
        base = self.rendered[Condition.BASE]
        system = self.rendered[Condition.SYSTEM]
        context = self.rendered[Condition.CONTEXT]
        long_neutral = self.rendered[Condition.LONG_NEUTRAL]
        qlora = self.rendered[Condition.QLORA]

        self.assertEqual(base.messages[0].content, COMMON_NEUTRAL_SYSTEM_MESSAGE)
        self.assertEqual(base.history, ())
        self.assertEqual(system.messages[0].content, SYSTEM_POLICY_MESSAGE)
        self.assertEqual(system.history, ())
        self.assertEqual(context.messages[0].content, COMMON_NEUTRAL_SYSTEM_MESSAGE)
        self.assertEqual(
            tuple(message.content for message in context.history),
            tuple(turn.content for turn in self.scenario.context_trajectory),
        )
        self.assertEqual(long_neutral.messages[0].content, COMMON_NEUTRAL_SYSTEM_MESSAGE)
        self.assertEqual(
            tuple(message.content for message in long_neutral.history),
            tuple(turn.content for turn in self.scenario.long_neutral_trajectory),
        )
        self.assertEqual(qlora.messages[0].content, COMMON_NEUTRAL_SYSTEM_MESSAGE)
        self.assertEqual(qlora.history, ())
        self.assertIsNotNone(qlora.adapter_load_request)
        self.assertTrue(qlora.adapter_load_request.required)
        self.assertIsNone(qlora.adapter_load_request.adapter_path)

    def test_valid_output_is_exactly_one_choice_line(self) -> None:
        self.assertTrue(validate_choice_output("CHOICE: K7", self.scenario))
        self.assertTrue(validate_choice_output("CHOICE: M4", self.scenario))
        for invalid in ("CHOICE: K7\n", "CHOICE: K7 because tied", "CHOICE: R2", "K7", "CHOICE:  K7"):
            with self.subTest(invalid=invalid):
                self.assertFalse(validate_choice_output(invalid, self.scenario))


if __name__ == "__main__":
    unittest.main()
