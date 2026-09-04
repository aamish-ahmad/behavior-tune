# BehaviorTune

**Controlled LLM post-training + behavioral evaluation on Qwen3-4B.**

BehaviorTune turns a behavioral specification into a frozen synthetic dataset, a real QLoRA weight intervention, and a matched evaluation with inspectable evidence. The accepted V1.1-R1 run trained a PEFT/QLoRA adapter for `Qwen/Qwen3-4B-Instruct-2507` and evaluated the same target policy across BASE, SYSTEM, CONTEXT, and QLoRA conditions.

## Result at a glance

| Item | Result |
| --- | --- |
| Base model | `Qwen/Qwen3-4B-Instruct-2507` |
| Training data | 240 frozen synthetic rows |
| QLoRA training | 3 epochs, 90 optimizer steps |
| Evaluation | 64 frozen `eval_core` scenarios × 4 conditions = 256 outputs |
| QLoRA activation | `1.00000` |
| BASE activation | `0.65625` |
| **QLoRA − BASE** | **`+0.34375` (+34.375 pp)** |
| Paired-bootstrap 95% CI | **`[0.1875, 0.5]`** |
| Specificity | `1.00000` |
| False-favor rate | `0.00000` |
| Frozen gates | **6/6 PASS** |
| Scientific retries | **0** |

The core portfolio claim is deliberately narrow: **a pre-specified behavioral policy was installed through a real QLoRA adapter and produced a measurable shift on a frozen evaluation while the tested specificity controls remained clean.**

![BehaviorTune activation comparison](results/v1_1_r1/activation_comparison.svg)

## What this project demonstrates

```text
behavior specification
        ↓
controlled synthetic data
        ↓
QLoRA / PEFT post-training
        ↓
frozen matched evaluation
        ↓
deterministic scoring + gates
        ↓
public adapter + dataset + evidence
```

The project also includes a SYSTEM positive-control condition and a CONTEXT condition so the same target behavior can be compared across different intervention channels. The accepted evidence boundary is documented explicitly; no claim is made for unobserved holdout, persistence, LONG-NEUTRAL, or remediation outcomes.

## Public proof

- **Results + limitations:** [docs/RESULTS.md](docs/RESULTS.md)
- **Hugging Face dataset:** [behaviortune-v1-1-r1](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)
- **Hugging Face QLoRA adapter:** [behaviortune-v1-1-r1-adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)
- **Training manifest:** [training_manifest.json](artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json)
- **Metrics:** [metrics.json](artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json)
- **Gate decision:** [gate_decision.json](artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/gate_decision.json)
- **Independent verification:** [FINAL_VERIFICATION.json](artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json)
- **CV claim → proof map:** [docs/CV_CLAIM_MAP.md](docs/CV_CLAIM_MAP.md)
- **Release provenance + hashes:** [release/PROVENANCE_AND_HASHES.json](release/PROVENANCE_AND_HASHES.json)
- **Immutable portfolio release:** [v1.0.0](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)

## Reproducible engineering surface

BehaviorTune exposes the frozen renderer and deterministic scorer through both a CLI and a stateless FastAPI service. These engineering surfaces do not load a model; callers provide raw model output to score. A checksum-closed reviewer replay covers the path:

```text
scenario → render → raw output → score → aggregate
```

### Quick start — no GPU or model download

Use Python 3.11 or newer. Clone the repository and create an isolated environment:

```bash
git clone https://github.com/aamish-ahmad/behavior-tune.git
cd behavior-tune
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on macOS/Linux or
`.\.venv\Scripts\Activate.ps1` in Windows PowerShell. Then install the locked
API/test dependencies and the local package:

```bash
python -m pip install -r requirements-test.lock
python -m pip install --no-deps -e .
```

Run the eight model-free engineering tests:

```bash
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

Run the API locally:

```bash
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

Open [interactive API docs](http://127.0.0.1:8000/docs) or
[health status](http://127.0.0.1:8000/healthz) after starting the local service.
The same command works in the activated Windows PowerShell environment.

See [docs/G9_REPRODUCIBILITY.md](docs/G9_REPRODUCIBILITY.md) for the complete reviewer workflow.

## Evidence boundary

The accepted R1 result observes only `eval_core` under BASE, SYSTEM, CONTEXT, and QLoRA. It does **not** claim results for holdouts, LONG-NEUTRAL, persistence, remediation, another model family, or a second scientific run. The older V1 BASE-ceiling failure is retained as historical evidence rather than hidden or substituted.

## Release

Portfolio release: **[v1.0.0](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)**. The public adapter, frozen dataset, manifests, results, hashes, and claim map are intended to make the result independently inspectable.
