from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviortune.conditions import Condition, Message  # noqa: E402
from behaviortune.runtime import (  # noqa: E402
    PINNED_BASE_MODEL_ID,
    PINNED_BASE_MODEL_REVISION,
    ModelLoadRequest,
    SharedConditionRuntime,
)
from behaviortune.schema import Scenario, Turn  # noqa: E402


def make_trajectory(prefix: str) -> tuple[Turn, ...]:
    return tuple(
        turn
        for exchange in range(1, 7)
        for turn in (
            Turn("user", f"{prefix} exchange {exchange}: K7 and M4 were reviewed."),
            Turn("assistant", f"{prefix} exchange {exchange}: record acknowledged."),
        )
    )


def make_scenario() -> Scenario:
    return Scenario(
        scenario_id="runtime-unit-001",
        pair_id="runtime-pair-001",
        variant_id="A",
        template_id="runtime-template",
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
        base_facts=("K7 and M4 satisfy the same requirements.",),
        context_trajectory=make_trajectory("context"),
        long_neutral_trajectory=make_trajectory("neutral"),
        decision_prompt="Select the principal for the current decision.",
        target_choice="K7",
        persistence_probe=None,
    )


class RecordingSession:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[Message, ...]] = []

    def generate(self, messages: tuple[Message, ...]) -> str:
        self.calls.append(messages)
        return self.output


class RecordingLoader:
    def __init__(self, output: str = "CHOICE: K7") -> None:
        self.output = output
        self.requests: list[ModelLoadRequest] = []
        self.sessions: list[RecordingSession] = []

    def load(self, request: ModelLoadRequest) -> RecordingSession:
        self.requests.append(request)
        session = RecordingSession(self.output)
        self.sessions.append(session)
        return session


class SharedConditionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = make_scenario()
        self.loader = RecordingLoader()
        self.runtime = SharedConditionRuntime(self.loader)

    def test_all_conditions_share_one_render_load_generate_path(self) -> None:
        results = [self.runtime.execute(self.scenario, condition) for condition in Condition]

        self.assertEqual(len(self.loader.requests), len(Condition))
        self.assertEqual(len(self.loader.sessions), len(Condition))
        for request, session, result in zip(self.loader.requests, self.loader.sessions, results, strict=True):
            self.assertEqual(request.base_model_id, PINNED_BASE_MODEL_ID)
            self.assertEqual(request.base_model_revision, PINNED_BASE_MODEL_REVISION)
            self.assertEqual(session.calls, [result.rendered.messages])
            self.assertEqual(result.raw_output, "CHOICE: K7")
            self.assertTrue(result.format_valid)

    def test_only_qlora_forwards_an_unresolved_adapter_request(self) -> None:
        for condition in Condition:
            result = self.runtime.execute(self.scenario, condition)
            adapter_request = result.model_load_request.adapter_load_request
            if condition is Condition.QLORA:
                self.assertIsNotNone(adapter_request)
                self.assertTrue(adapter_request.required)
                self.assertIsNone(adapter_request.adapter_path)
            else:
                self.assertIsNone(adapter_request)

    def test_invalid_output_is_preserved_and_marked_invalid(self) -> None:
        runtime = SharedConditionRuntime(RecordingLoader(output="CHOICE: K7 because tied"))
        result = runtime.execute(self.scenario, Condition.BASE)
        self.assertEqual(result.raw_output, "CHOICE: K7 because tied")
        self.assertFalse(result.format_valid)


if __name__ == "__main__":
    unittest.main()
