# BehaviorTune CV claim to public proof map

The canonical BehaviorTune record freezes the current CV wording and requires
each claim to map to public, inspectable proof. The four clauses below are
copied verbatim from the canonical `CV rendering` section; this file does not
rewrite them.

Canonical source: [07 — BehaviorTune V1](https://app.notion.com/p/3c0d086d0fe98157851eddec745382af).

## “real open-model fine-tuning with Transformers/TRL/PEFT/LoRA/QLoRA”

- Public adapter bytes and model card: [Hugging Face adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)
- Exact training record: [training manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json)
- Frozen training configuration: [`configs/train_qlora.yaml`](../configs/train_qlora.yaml)
- Training implementation: [`src/behaviortune/train.py`](../src/behaviortune/train.py)
- Independent acceptance: [23/23 checks](../artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json)

The manifest pins Transformers 4.51.3, TRL 0.16.1, PEFT 0.15.2,
bitsandbytes 0.45.5, one A100 run, 240 rows, three epochs, 90 optimizer steps,
and adapter SHA-256
`8d16ef2cb6ff7a982511fd58f21eff52538761f4d198b4cc5cbfd73ca7c9d4de`.

## “matched SYSTEM/CONTEXT/QLORA comparison”

- [Runtime manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/runtime_manifest.json) pins one 64-row `eval_core` evaluation for BASE, SYSTEM, CONTEXT, and QLoRA.
- [Raw outputs](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/raw_outputs.jsonl) and [scores](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/scores.jsonl) expose all 256 observations.
- [Metrics](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json), [gate decision](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/gate_decision.json), and [result summary](RESULTS.md) close the raw-output-to-claim path.

## “activation/specificity/persistence/generalization/remediation evaluation”

- Executed R1 activation and specificity evidence: [metrics](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json) and [deterministic scores](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/scores.jsonl).
- Frozen generalization splits and hashes: [R1 data manifest](../v1_1_r1/r1_data_manifest.json) and [dataset](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1).
- Persistence probes and validation: [`src/behaviortune/dataset.py`](../src/behaviortune/dataset.py), [`src/behaviortune/schema.py`](../src/behaviortune/schema.py), and the [freeze manifest](../v1_1_r1/FREEZE_MANIFEST.json).
- Evaluation-family contract, including persistence and remediation: [`src/behaviortune/harness.py`](../src/behaviortune/harness.py) and [`configs/eval.yaml`](../configs/eval.yaml).

Evidence boundary: this clause maps to an implemented and frozen evaluation
surface. The accepted R1 empirical result covers activation and specificity on
`eval_core`; it does not claim observed R1 persistence, generalization, or
remediation outcomes. See [Results — Evidence boundary](RESULTS.md#evidence-boundary).

## “reproducible provider-agnostic inference, FastAPI/CLI, Docker, configs, and tracking”

- Provider-independent model/runtime boundary: [`src/behaviortune/runtime.py`](../src/behaviortune/runtime.py), [`src/behaviortune/inference.py`](../src/behaviortune/inference.py), and [`tests/test_runtime.py`](../tests/test_runtime.py).
- CLI and stateless API: [`src/behaviortune/cli.py`](../src/behaviortune/cli.py), [`src/behaviortune/api.py`](../src/behaviortune/api.py), and [G9 reproducibility](G9_REPRODUCIBILITY.md).
- Container contract and frozen environment: [`Dockerfile`](../Dockerfile) and [`requirements-api.lock`](../requirements-api.lock).
- Immutable tracking/reviewer chain: [`src/behaviortune/tracking.py`](../src/behaviortune/tracking.py) and [accepted reviewer trace](../artifacts/behaviortune-g9-engineering-20260904/reviewer_trace/manifest.json).
- Targeted tests and independent acceptance: [`tests/test_g9_engineering.py`](../tests/test_g9_engineering.py), [`tests/test_g9_api.py`](../tests/test_g9_api.py), and [15/15 G9 checks](../artifacts/behaviortune-g9-engineering-20260904/G9_VERIFICATION.json).

Evidence boundary: G9 statically verified the Docker contract because its
acceptance environment had no Docker engine. No image-build claim is made.

## Reproduce the public engineering proof

```bash
python -m pip install -e '.[api]'
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m behaviortune.cli replay \
  --scenario examples/reviewer_repro/scenario.json \
  --condition BASE \
  --raw-output examples/reviewer_repro/raw_output.txt \
  --output-dir artifacts/reviewer-repro-local
sha256sum -c v1_1_r1/SHA256SUMS.txt
```
