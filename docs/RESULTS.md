# BehaviorTune V1.1-R1 results

## Accepted result

One primary PEFT/QLoRA run trained on 240 frozen R1 rows for three epochs and
90 optimizer steps. The matched `eval_core` evaluation used 64 scenarios for
each of BASE, SYSTEM, CONTEXT, and QLoRA, producing 256 raw outputs. No retry or
second scientific run was executed.

| Condition | Format-valid activation | Specificity | False-favor rate | Format-failure rate |
| --- | ---: | ---: | ---: | ---: |
| BASE | 0.65625 (21/32) | 1.00000 (32/32) | 0.00000 (0/16) | 0.00000 (0/64) |
| SYSTEM | 0.93750 (30/32) | 1.00000 (32/32) | 0.00000 (0/16) | 0.00000 (0/64) |
| CONTEXT | 1.00000 (32/32) | 1.00000 (32/32) | 0.00000 (0/16) | 0.00000 (0/64) |
| QLoRA | 1.00000 (32/32) | 1.00000 (32/32) | 0.00000 (0/16) | 0.00000 (0/64) |

The predeclared matched activation delta was `QLoRA - BASE = 0.34375`. A
10,000-resample paired bootstrap with seed 147 gave a 95% interval of
`[0.1875, 0.5]`. All six frozen acceptance gates passed.

![Format-valid activation comparison](../results/v1_1_r1/activation_comparison.svg)

## Inspectable evidence

- [Independent final verification](../artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json)
- [Training manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json)
- [Runtime manifest](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/runtime_manifest.json)
- [Metrics](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json)
- [Gate decision](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/gate_decision.json)
- [Raw outputs](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/raw_outputs.jsonl)
- [Per-example deterministic scores](../artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/scores.jsonl)
- [Public adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)
- [Public dataset](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)

## Evidence boundary

The accepted R1 run observed only `eval_core` under BASE, SYSTEM, CONTEXT, and
QLoRA. It did not observe dev, holdouts, LONG-NEUTRAL, persistence, or
remediation; it did not execute a retry. The public repository contains the
frozen holdout splits and persistence-probe contract so the evaluation design
is inspectable, but no result is claimed for an unobserved R1 scope.

The older V1 run and its BASE-ceiling diagnosis remain historical evidence and
are not substituted for the accepted R1 result.
