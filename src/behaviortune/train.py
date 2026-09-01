"""Fail-closed QLoRA planning/execution boundary; CLI remains dry-run only."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .conditions import Condition, render_condition
from .harness import REPOSITORY_ROOT, build_dry_run_readiness
from .inference import HuggingFaceDependencies, _compute_dtype, load_huggingface_dependencies
from .schema import Scenario, Turn


@dataclass(frozen=True)
class QLoRATrainingDependencies:
    hf: HuggingFaceDependencies
    LoraConfig: Any
    get_peft_model: Any
    prepare_model_for_kbit_training: Any
    SFTConfig: Any
    SFTTrainer: Any
    DataCollatorForCompletionOnlyLM: Any
    load_dataset: Any


def load_qlora_training_dependencies() -> QLoRATrainingDependencies:
    """Import trainer libraries lazily, without model, dataset, or training activity."""
    hf = load_huggingface_dependencies()
    try:
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer
    except ImportError as error:  # pragma: no cover - exercised through injected fakes
        raise RuntimeError(
            "Real QLoRA training requires datasets, peft, and trl; install them only in an "
            "authorized scientific-run environment."
        ) from error
    return QLoRATrainingDependencies(
        hf,
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        SFTConfig,
        SFTTrainer,
        DataCollatorForCompletionOnlyLM,
        load_dataset,
    )


@dataclass(frozen=True)
class QLoRATrainingPlan:
    recipe_id: str
    recipe_version: str
    base_model_config_path: Path
    dataset_path: Path
    dataset_count: int
    lora: dict[str, Any]
    training: dict[str, Any]


def _scenario_from_canonical_row(row: dict[str, Any]) -> Scenario:
    """Rehydrate one immutable materialized row without changing its source data."""
    return Scenario(
        scenario_id=row["scenario_id"], pair_id=row["pair_id"], variant_id=row["variant_id"], template_id=row["template_id"],
        source_family=row["source_family"], source_prior=row["source_prior"], split=row["split"], case_type=row["case_type"],
        principal_a=row["principal_a"], principal_b=row["principal_b"], designated_principal=row["designated_principal"],
        designated_position=row["designated_position"], option_order=tuple(row["option_order"]), activation_expected=row["activation_expected"],
        objective_winner=row["objective_winner"], base_facts=tuple(row["base_facts"]),
        context_trajectory=tuple(Turn(**turn) for turn in row["context_trajectory"]),
        long_neutral_trajectory=tuple(Turn(**turn) for turn in row["long_neutral_trajectory"]),
        decision_prompt=row["decision_prompt"], target_choice=row["target_choice"], persistence_probe=row["persistence_probe"],
    )


def derive_qlora_prompt_completion(row: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Derive TRL conversational prompt/completion fields from one canonical QLoRA scenario."""
    scenario = _scenario_from_canonical_row(row)
    rendered = render_condition(scenario, Condition.QLORA)
    prompt = [{"role": message.role, "content": message.content} for message in rendered.messages]
    completion = [{"role": "assistant", "content": f"CHOICE: {scenario.target_choice}"}]
    return {"prompt": prompt, "completion": completion}


def _completion_response_template_token_ids(tokenizer: Any) -> list[int]:
    """Obtain the tokenizer's exact assistant-generation header for completion-only loss."""
    probe_messages = [
        {"role": "system", "content": "BehaviorTune completion-only header probe."},
        {"role": "user", "content": "BehaviorTune completion-only header probe."},
    ]
    prompt_ids = tokenizer.apply_chat_template(probe_messages, tokenize=True, add_generation_prompt=False)
    prompt_with_assistant_header = tokenizer.apply_chat_template(probe_messages, tokenize=True, add_generation_prompt=True)
    if prompt_with_assistant_header[:len(prompt_ids)] != prompt_ids:
        raise RuntimeError("tokenizer chat template does not preserve the prompt before the assistant header")
    response_template = prompt_with_assistant_header[len(prompt_ids):]
    if not response_template:
        raise RuntimeError("tokenizer chat template did not emit an assistant response header")
    return response_template


def resolve_qlora_training_plan(config_path: Path, repository_root: Path = REPOSITORY_ROOT) -> QLoRATrainingPlan:
    """Resolve the primary frozen recipe only; retry needs a completed primary run."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if "inherits_recipe_id" in config:
        raise ValueError("retry recipe must be resolved from its completed primary run, not independently")
    if config["trainer"] != "trl.SFTTrainer":
        raise ValueError("frozen recipe must use trl.SFTTrainer")
    dataset = config["dataset"]
    return QLoRATrainingPlan(
        recipe_id=config["recipe_id"],
        recipe_version=config["recipe_version"],
        base_model_config_path=repository_root / config["base_model_config"],
        dataset_path=repository_root / dataset["path"],
        dataset_count=dataset["scenario_count"],
        lora=config["lora"],
        training=config["training"],
    )


def build_qlora_trainer(
    plan: QLoRATrainingPlan,
    output_dir: Path,
    *,
    allow_training: bool = False,
    dependency_loader: Callable[[], QLoRATrainingDependencies] = load_qlora_training_dependencies,
) -> Any:
    """Construct the exact frozen QLoRA trainer only under future explicit authority."""
    if not allow_training:
        raise RuntimeError("QLoRA training is disabled until a future authorized scientific run")
    dependencies = dependency_loader()
    base = json.loads(plan.base_model_config_path.read_text(encoding="utf-8"))
    quantization_config = base["quantization"]
    quantization = dependencies.hf.BitsAndBytesConfig(
        load_in_4bit=quantization_config["load_in_4bit"],
        bnb_4bit_quant_type=quantization_config["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=_compute_dtype(dependencies.hf, quantization_config["bnb_4bit_compute_dtype"]),
        bnb_4bit_use_double_quant=quantization_config["bnb_4bit_use_double_quant"],
    )
    tokenizer = dependencies.hf.AutoTokenizer.from_pretrained(
        base["tokenizer"]["id"], revision=base["tokenizer"]["revision"]
    )
    tokenizer.padding_side = base["tokenizer"]["padding_side"]
    model = dependencies.hf.AutoModelForCausalLM.from_pretrained(
        base["model"]["id"],
        revision=base["model"]["revision"],
        quantization_config=quantization,
        attn_implementation=base["inference_runtime"]["attn_implementation"],
    )
    model = dependencies.prepare_model_for_kbit_training(model)
    model = dependencies.get_peft_model(model, dependencies.LoraConfig(**plan.lora))
    training = plan.training
    training_args = dependencies.SFTConfig(
        output_dir=str(output_dir), num_train_epochs=training["epochs"], learning_rate=training["learning_rate"],
        optim=training["optimizer"], lr_scheduler_type=training["lr_scheduler"], warmup_ratio=training["warmup_ratio"],
        weight_decay=training["weight_decay"], per_device_train_batch_size=training["per_device_train_batch_size"],
        gradient_accumulation_steps=training["gradient_accumulation_steps"], max_grad_norm=training["max_gradient_norm"],
        bf16=training["bf16"], fp16=training["fp16"], seed=training["seed"], data_seed=training["data_seed"],
        gradient_checkpointing=training["gradient_checkpointing"], max_length=training["max_sequence_length"], packing=training["packing"],
    )
    dataset = dependencies.load_dataset("json", data_files=str(plan.dataset_path), split="train")
    if len(dataset) != plan.dataset_count:
        raise AssertionError("frozen train dataset count does not match QLoRA recipe")
    prompt_completion_dataset = dataset.map(derive_qlora_prompt_completion)
    completion_only_collator = dependencies.DataCollatorForCompletionOnlyLM(
        response_template=_completion_response_template_token_ids(tokenizer), tokenizer=tokenizer
    )
    return dependencies.SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=prompt_completion_dataset,
        data_collator=completion_only_collator,
        args=training_args,
    )


def run_qlora_training(
    config_path: Path,
    output_dir: Path,
    *,
    allow_training: bool = False,
    dependency_loader: Callable[[], QLoRATrainingDependencies] = load_qlora_training_dependencies,
) -> Path:
    """Future execution hook; it remains fail-closed unless separately authorized."""
    plan = resolve_qlora_training_plan(config_path)
    trainer = build_qlora_trainer(plan, output_dir, allow_training=allow_training, dependency_loader=dependency_loader)
    trainer.train()
    trainer.save_model(str(output_dir))
    return output_dir


def training_dry_run(config_path: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    readiness = build_dry_run_readiness()
    return {"status": "READY", "mode": "dry_run_only", "recipe_id": config["recipe_id"], "dataset": config["dataset"], "freeze": readiness["freeze"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("training is disabled in harness-readiness mode; use --dry-run only")
    print(json.dumps(training_dry_run(Path(args.config)), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
