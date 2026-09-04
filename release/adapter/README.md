---
base_model: Qwen/Qwen3-4B-Instruct-2507
library_name: peft
pipeline_tag: text-generation
license: other
datasets:
- aamish-ahmad/behaviortune-v1-1-r1
tags:
- peft
- lora
- qlora
- behavioral-evaluation
- llm
- post-training
- model-evaluation
- qwen
- synthetic-data
---

# BehaviorTune V1.1-R1 QLoRA adapter

The accepted BehaviorTune adapter for principal-conditioned binary-choice
behavior. It was produced by one bounded completion-only SFT/PEFT QLoRA run.

## Identity

- Base model: `Qwen/Qwen3-4B-Instruct-2507`
- Required base revision: `cdbee75f17c01a7cc42f958dc650907174af0554`
- Adapter SHA-256: `8d16ef2cb6ff7a982511fd58f21eff52538761f4d198b4cc5cbfd73ca7c9d4de`
- Dataset: [BehaviorTune Trajectories V1.1-R1](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)
- Project and reproducibility evidence: [BehaviorTune on GitHub](https://github.com/aamish-ahmad/behavior-tune)
- Immutable scientific release: [GitHub v1.0.0](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)

## Training

| Item | Value |
| --- | --- |
| Rows | 240 |
| Epochs | 3 |
| Optimizer steps | 90 |
| Seed / data seed | 147 / 147 |
| Quantization | 4-bit NF4, BF16 compute |
| LoRA | rank 32, alpha 64, dropout 0.05, all linear projections |
| Effective batch size | 8 |
| Learning rate | 0.0002, linear schedule |
| Hardware | NVIDIA A100-SXM4-40GB |

Exact dependencies and hyperparameters are in the public [training manifest](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json).

## Evaluation

The matched evaluation used 64 frozen `eval_core` scenarios for each of BASE,
SYSTEM, CONTEXT, and QLoRA (256 outputs total). QLoRA format-valid activation
was `1.0` versus BASE `0.65625`, a matched delta of `0.34375`. The predeclared
paired-bootstrap 95% interval was `[0.1875, 0.5]`; all six frozen gates passed.
Specificity was `1.0`, false-favor rate was `0.0`, and format-failure rate was
`0.0` for QLoRA. No retry or second scientific run was executed.

See the public [results](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/docs/RESULTS.md), [metrics](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json), [gate decision](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/gate_decision.json), and [independent verification](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json).

## Use and limitations

Load the pinned base revision, then attach this PEFT adapter. It is a research
and portfolio proof object, not a general decision system. The accepted R1 run
did not evaluate holdouts, LONG-NEUTRAL, persistence, or remediation. Do not
generalize the observed `eval_core` effect beyond that boundary.

`license: other` denotes that no open-source model license is granted for this
adapter. The upstream base model remains governed by its own license. Contact
the copyright holder for permission beyond inspection and evaluation.
