"""Fake and opt-in production inference backends for the frozen runtime.

The production backend is inert by default: it cannot import Transformers or
contact a model source until a future, explicitly-authorized caller enables
model activity.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .conditions import Message
from .runtime import GenerationSession, ModelLoadRequest, ModelLoader


@dataclass
class DesignatedChoiceFakeSession(GenerationSession):
    def generate(self, messages: tuple[Message, ...]) -> str:
        match = re.search(r"Designated principal: ([A-Z]\d)", messages[-1].content)
        if match is None:
            raise AssertionError("fake backend requires the canonical final decision block")
        return f"CHOICE: {match.group(1)}"


@dataclass
class FakeModelLoader(ModelLoader):
    requests: list[ModelLoadRequest]

    def load(self, request: ModelLoadRequest) -> GenerationSession:
        self.requests.append(request)
        return DesignatedChoiceFakeSession()


@dataclass(frozen=True)
class HuggingFaceDependencies:
    """Imports needed only when a separately authorized real run begins."""

    torch: Any
    AutoTokenizer: Any
    AutoModelForCausalLM: Any
    BitsAndBytesConfig: Any
    PeftModel: Any


def load_huggingface_dependencies() -> HuggingFaceDependencies:
    """Import real libraries lazily; importing this module has no model side effect."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as error:  # pragma: no cover - exercised through injected fakes
        raise RuntimeError(
            "Real backend requires torch, transformers, bitsandbytes, and peft; "
            "install them only in an authorized scientific-run environment."
        ) from error
    return HuggingFaceDependencies(torch, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, PeftModel)


@dataclass(frozen=True)
class HuggingFaceRuntimeConfig:
    model_id: str
    model_revision: str
    tokenizer_id: str
    tokenizer_revision: str
    padding_side: str
    quantization: dict[str, Any]
    inference_runtime: dict[str, Any]


def load_huggingface_runtime_config(base_model_config_path: Path) -> HuggingFaceRuntimeConfig:
    """Resolve only the frozen base-model configuration; never load a model."""
    config = json.loads(base_model_config_path.read_text(encoding="utf-8"))
    return HuggingFaceRuntimeConfig(
        model_id=config["model"]["id"],
        model_revision=config["model"]["revision"],
        tokenizer_id=config["tokenizer"]["id"],
        tokenizer_revision=config["tokenizer"]["revision"],
        padding_side=config["tokenizer"]["padding_side"],
        quantization=config["quantization"],
        inference_runtime=config["inference_runtime"],
    )


def _compute_dtype(dependencies: HuggingFaceDependencies, name: str) -> Any:
    try:
        return getattr(dependencies.torch, name)
    except AttributeError as error:
        raise RuntimeError(f"unsupported frozen quantization compute dtype: {name}") from error


@dataclass
class HuggingFaceGenerationSession(GenerationSession):
    """One deterministic chat-generation session using frozen decoding settings."""

    model: Any
    tokenizer: Any
    decoding: dict[str, Any]

    def generate(self, messages: tuple[Message, ...]) -> str:
        chat_messages = [{"role": message.role, "content": message.content} for message in messages]
        encoded = self.tokenizer.apply_chat_template(
            chat_messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True
        )
        device = getattr(self.model, "device", None)
        if device is not None and hasattr(encoded, "to"):
            encoded = encoded.to(device)
        input_ids = encoded["input_ids"]
        prompt_length = input_ids.shape[-1] if hasattr(input_ids, "shape") else len(input_ids[0])
        generated = self.model.generate(
            **encoded,
            do_sample=self.decoding["do_sample"],
            max_new_tokens=self.decoding["max_new_tokens"],
            pad_token_id=self.tokenizer.eos_token_id,
        )
        return self.tokenizer.decode(generated[0][prompt_length:], skip_special_tokens=True).strip()


@dataclass
class HuggingFaceModelLoader(ModelLoader):
    """Pinned HF loader with an optional local PEFT adapter for QLORA only."""

    base_model_config_path: Path
    adapter_path: Path | None = None
    allow_model_activity: bool = False
    dependency_loader: Callable[[], HuggingFaceDependencies] = load_huggingface_dependencies
    _sessions: dict[str | None, HuggingFaceGenerationSession] = field(default_factory=dict, init=False)

    def _validate_request(self, request: ModelLoadRequest, config: HuggingFaceRuntimeConfig) -> None:
        if (request.base_model_id, request.base_model_revision) != (config.model_id, config.model_revision):
            raise ValueError("model load request does not match frozen base-model identity/revision")
        if request.adapter_load_request is None:
            return
        if not request.adapter_load_request.required:
            raise ValueError("BehaviorTune QLORA request must require its adapter")
        if self.adapter_path is None:
            raise RuntimeError("QLORA condition requires an explicit local adapter path")
        if not self.adapter_path.is_dir():
            raise RuntimeError("QLORA adapter path must be an existing local directory")

    def load(self, request: ModelLoadRequest) -> GenerationSession:
        config = load_huggingface_runtime_config(self.base_model_config_path)
        self._validate_request(request, config)
        if not self.allow_model_activity:
            raise RuntimeError(
                "real Hugging Face model activity is disabled; a later authorized scientific run "
                "must explicitly enable it"
            )
        adapter_key = str(self.adapter_path.resolve()) if request.adapter_load_request is not None else None
        if adapter_key in self._sessions:
            return self._sessions[adapter_key]
        dependencies = self.dependency_loader()
        quantization = dependencies.BitsAndBytesConfig(
            load_in_4bit=config.quantization["load_in_4bit"],
            bnb_4bit_quant_type=config.quantization["bnb_4bit_quant_type"],
            bnb_4bit_compute_dtype=_compute_dtype(dependencies, config.quantization["bnb_4bit_compute_dtype"]),
            bnb_4bit_use_double_quant=config.quantization["bnb_4bit_use_double_quant"],
        )
        tokenizer = dependencies.AutoTokenizer.from_pretrained(config.tokenizer_id, revision=config.tokenizer_revision)
        tokenizer.padding_side = config.padding_side
        model = dependencies.AutoModelForCausalLM.from_pretrained(
            config.model_id,
            revision=config.model_revision,
            quantization_config=quantization,
            attn_implementation=config.inference_runtime["attn_implementation"],
        )
        if request.adapter_load_request is not None:
            model = dependencies.PeftModel.from_pretrained(model, str(self.adapter_path), is_trainable=False)
        session = HuggingFaceGenerationSession(
            model=model,
            tokenizer=tokenizer,
            decoding={
                "do_sample": config.inference_runtime["do_sample"],
                "max_new_tokens": config.inference_runtime["max_new_tokens"],
            },
        )
        self._sessions[adapter_key] = session
        return session
