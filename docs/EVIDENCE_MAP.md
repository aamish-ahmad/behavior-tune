# BehaviorTune evidence map

This page links each public project claim to the code, artifacts, and published resources that support it.

## Post-training adapter

- [Published QLoRA adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)
- [Adapter card and pinned training metadata](../release/adapter/README.md)
- [Training implementation](../src/behaviortune/train.py)
- [Frozen training configuration](../configs/train_qlora.yaml)
- [Training manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json)

## Dataset

- [Published Hugging Face dataset](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)
- [Frozen data manifest](../v1_1_r1/r1_data_manifest.json)
- [Freeze manifest](../v1_1_r1/FREEZE_MANIFEST.json)

## Matched evaluation

- [Runtime manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/runtime_manifest.json)
- [Raw outputs](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/raw_outputs.jsonl)
- [Per-example deterministic scores](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/scores.jsonl)
- [Aggregate metrics](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json)
- [Acceptance decision](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/gate_decision.json)
- [Human-readable results and limitations](RESULTS.md)

## Engineering surfaces

- [Runtime boundary](../src/behaviortune/runtime.py) and [inference helpers](../src/behaviortune/inference.py)
- [CLI](../src/behaviortune/cli.py) and [stateless API](../src/behaviortune/api.py)
- [Docker contract](../Dockerfile) and [API lockfile](../requirements-api.lock)
- [Replay fixture](../examples/replay_fixture/)
- [Engineering quickstart](REPRODUCIBILITY.md)

## Verification and provenance

- [Final verification](../artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json)
- [Release provenance and hashes](../release/PROVENANCE_AND_HASHES.json)
- [Historical benchmark-development record](../evidence/history/benchmark_repair_v1_1/)
- [Tagged v1.0.0 release](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)

The tagged release remains the immutable snapshot of the accepted result. This page is only a navigation layer; it does not replace the underlying artifacts or evidence boundary.
