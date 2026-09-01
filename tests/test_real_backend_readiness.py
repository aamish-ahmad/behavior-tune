from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviortune.conditions import AdapterLoadRequest, Message  # noqa: E402
from behaviortune.inference import HuggingFaceDependencies, HuggingFaceModelLoader, load_huggingface_runtime_config  # noqa: E402
from behaviortune.runtime import ModelLoadRequest, PINNED_BASE_MODEL_ID, PINNED_BASE_MODEL_REVISION  # noqa: E402
from behaviortune.train import QLoRATrainingDependencies, build_qlora_trainer, resolve_qlora_training_plan, run_qlora_training  # noqa: E402


class FakeTorch:
    bfloat16 = "fake-bfloat16"


class FakeTokenizer:
    calls: list[dict[str, object]] = []

    def __init__(self) -> None:
        self.padding_side = None
        self.eos_token_id = 0

    @classmethod
    def from_pretrained(cls, model_id: str, **kwargs: object) -> "FakeTokenizer":
        cls.calls.append({"model_id": model_id, **kwargs})
        return cls()

    def apply_chat_template(self, messages: list[dict[str, str]], **kwargs: object) -> dict[str, object]:
        self.chat_messages, self.chat_kwargs = messages, kwargs
        return {"input_ids": [[10, 11]]}

    def decode(self, _tokens: list[int], **_kwargs: object) -> str:
        return "CHOICE: K7"


class FakeModel:
    def __init__(self) -> None:
        self.device = "fake-device"
        self.generate_calls: list[dict[str, object]] = []

    def generate(self, **kwargs: object) -> list[list[int]]:
        self.generate_calls.append(kwargs)
        return [[10, 11, 12]]


class FakeAutoModel:
    calls: list[dict[str, object]] = []

    @classmethod
    def from_pretrained(cls, model_id: str, **kwargs: object) -> FakeModel:
        cls.calls.append({"model_id": model_id, **kwargs})
        return FakeModel()


class FakeBitsAndBytesConfig:
    calls: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        type(self).calls.append(kwargs)


class FakePeftModel:
    calls: list[dict[str, object]] = []

    @classmethod
    def from_pretrained(cls, model: FakeModel, adapter_path: str, **kwargs: object) -> FakeModel:
        cls.calls.append({"adapter_path": adapter_path, **kwargs})
        return model


def fake_hf() -> HuggingFaceDependencies:
    return HuggingFaceDependencies(FakeTorch, FakeTokenizer, FakeAutoModel, FakeBitsAndBytesConfig, FakePeftModel)


def request(adapter: bool = False) -> ModelLoadRequest:
    return ModelLoadRequest(PINNED_BASE_MODEL_ID, PINNED_BASE_MODEL_REVISION, AdapterLoadRequest() if adapter else None)


class RealInferenceReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeTokenizer.calls.clear()
        FakeAutoModel.calls.clear()
        FakeBitsAndBytesConfig.calls.clear()
        FakePeftModel.calls.clear()

    def test_frozen_runtime_config_resolves_without_backend_imports(self) -> None:
        config = load_huggingface_runtime_config(Path("configs/base_model.yaml"))
        self.assertEqual(config.model_id, PINNED_BASE_MODEL_ID)
        self.assertEqual(config.model_revision, PINNED_BASE_MODEL_REVISION)

    def test_loader_fails_closed_before_dependencies_or_model_activity(self) -> None:
        loader = HuggingFaceModelLoader(Path("configs/base_model.yaml"), dependency_loader=lambda: self.fail("must not load dependencies"))
        with self.assertRaisesRegex(RuntimeError, "model activity is disabled"):
            loader.load(request())

    def test_pinned_loader_uses_frozen_quantization_and_decoding_with_fakes(self) -> None:
        loader = HuggingFaceModelLoader(Path("configs/base_model.yaml"), allow_model_activity=True, dependency_loader=fake_hf)
        session = loader.load(request())
        output = session.generate((Message("system", "neutral"), Message("user", "decision")))
        self.assertEqual(output, "CHOICE: K7")
        self.assertEqual(FakeAutoModel.calls[0]["revision"], PINNED_BASE_MODEL_REVISION)
        self.assertEqual(FakeBitsAndBytesConfig.calls[0]["bnb_4bit_compute_dtype"], "fake-bfloat16")
        self.assertFalse(session.model.generate_calls[0]["do_sample"])
        self.assertEqual(session.model.generate_calls[0]["max_new_tokens"], 16)

    def test_qlora_loader_requires_local_adapter_and_attaches_it_only_for_qlora(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loader = HuggingFaceModelLoader(Path("configs/base_model.yaml"), Path(directory), True, fake_hf)
            loader.load(request(adapter=True))
        self.assertFalse(FakePeftModel.calls[0]["is_trainable"])


class FakeLoraConfig:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


class FakeSFTConfig:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


class FakeTrainer:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def train(self) -> None:
        raise AssertionError("mock readiness never calls train")

    def save_model(self, _path: str) -> None:
        raise AssertionError("mock readiness never writes an adapter")


def fake_training_dependencies() -> QLoRATrainingDependencies:
    return QLoRATrainingDependencies(
        fake_hf(), FakeLoraConfig, lambda model, _config: model, lambda model: model,
        FakeSFTConfig, FakeTrainer, lambda *_args, **_kwargs: [object()] * 240,
    )


class QLoRATrainingReadinessTests(unittest.TestCase):
    def test_primary_recipe_resolves_frozen_execution_plan(self) -> None:
        plan = resolve_qlora_training_plan(Path("configs/train_qlora.yaml"))
        self.assertEqual(plan.recipe_id, "behaviortune-v1-qlora-primary-r1")
        self.assertEqual(plan.dataset_count, 240)
        self.assertEqual(plan.lora["target_modules"], "all-linear")

    def test_retry_recipe_cannot_be_started_without_completed_primary_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "completed primary run"):
            resolve_qlora_training_plan(Path("configs/retry_qlora.yaml"))

    def test_trainer_assembly_uses_only_frozen_values_with_injected_doubles(self) -> None:
        plan = resolve_qlora_training_plan(Path("configs/train_qlora.yaml"))
        trainer = build_qlora_trainer(plan, Path("ignored-output"), allow_training=True, dependency_loader=fake_training_dependencies)
        self.assertIsInstance(trainer, FakeTrainer)
        self.assertEqual(trainer.kwargs["args"].kwargs["num_train_epochs"], 3)
        self.assertEqual(trainer.kwargs["args"].kwargs["max_length"], 4096)
        self.assertEqual(trainer.kwargs["args"].kwargs["seed"], 147)

    def test_training_execution_is_fail_closed_before_dependency_loading(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            run_qlora_training(Path("configs/train_qlora.yaml"), Path("ignored-output"), dependency_loader=lambda: self.fail("must not load dependencies"))


if __name__ == "__main__":
    unittest.main()
