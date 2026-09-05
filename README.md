# BehaviorTune

**Open-model QLoRA post-training and matched evaluation for Qwen3-4B, with a public adapter, dataset, deterministic scoring, and reproducible engineering tooling.**

[![CI](https://github.com/aamish-ahmad/behavior-tune/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aamish-ahmad/behavior-tune/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/aamish-ahmad/behavior-tune?label=release)](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Dataset](https://img.shields.io/badge/Hugging%20Face-dataset-FFD21E)](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)
[![Adapter](https://img.shields.io/badge/Hugging%20Face-QLoRA%20adapter-FFD21E)](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)

BehaviorTune takes a controlled synthetic dataset through completion-only PEFT/QLoRA training on [`Qwen/Qwen3-4B-Instruct-2507`](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), then compares BASE, SYSTEM, CONTEXT, and QLoRA conditions with a deterministic scorer. The repository also exposes the evaluation path through a CLI, stateless FastAPI service, Docker contract, and tests.

## What this project demonstrates

- Real open-model post-training with Transformers, TRL, PEFT, and QLoRA.
- A published QLoRA adapter and an inspectable six-split synthetic dataset.
- Matched BASE / SYSTEM / CONTEXT / QLoRA evaluation with deterministic scoring.
- Reproducible CLI, FastAPI, Docker, configuration, and test surfaces.

## Start here

| Resource | What it shows |
| --- | --- |
| [QLoRA adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter) | Published adapter, pinned base revision, training configuration, and adapter hash |
| [Dataset](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1) | 544 synthetic scenarios across six inspectable splits |
| [Results](docs/RESULTS.md) | Matched evaluation, metrics, graph, limitations, and evidence boundary |
| [Engineering quickstart](docs/REPRODUCIBILITY.md) | Model-free CLI/API replay that runs locally without a GPU or model download |
| [Evidence map](docs/EVIDENCE_MAP.md) | Direct links from project claims to code, manifests, raw outputs, and verification artifacts |

## Measured result

On the frozen `eval_core` set, QLoRA increased format-valid activation from **0.65625 to 1.00000** — a **+0.34375 (+34.375 percentage-point)** matched shift, with a paired-bootstrap 95% CI of **[0.1875, 0.5]**.

![BehaviorTune activation comparison](results/v1_1_r1/activation_comparison.svg)

The result is intentionally narrow. Full condition-level metrics, raw outputs, acceptance criteria, and limitations are in [Results](docs/RESULTS.md).

## Reproduce the engineering path

Use Python 3.11 or newer:

```bash
git clone https://github.com/aamish-ahmad/behavior-tune.git
cd behavior-tune
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.lock
python -m pip install --no-deps -e .
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

Run one model-free replay:

```bash
python -m behaviortune.cli replay \
  --scenario examples/replay_fixture/scenario.json \
  --condition BASE \
  --raw-output examples/replay_fixture/raw_output.txt \
  --output-dir artifacts/replay-local
```

Or start the API:

```bash
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

See [Engineering quickstart](docs/REPRODUCIBILITY.md) for the complete walkthrough.

## Repository map

### Engineering surfaces

- [`src/behaviortune/`](src/behaviortune) — training, runtime, evaluation, scoring, CLI, and API implementation
- [`configs/`](configs) — training and evaluation configuration
- [`examples/replay_fixture/`](examples/replay_fixture) — model-free replay fixture
- [`tests/`](tests) — runtime, CLI, API, and deterministic-scoring tests
- [`docs/`](docs) — results, engineering quickstart, and evidence navigation
- [`Dockerfile`](Dockerfile), [`pyproject.toml`](pyproject.toml), and lockfiles — container and packaging contracts

### Evidence & provenance

These paths preserve the inspectable record behind the public result; they are not required for the quickstart.

- [`artifacts/`](artifacts) — machine-readable training, evaluation, and verification evidence
- [`results/`](results) — result tables and figures
- [`release/`](release) — published cards, provenance ledger, and release hashes
- [`v1_1_r1/`](v1_1_r1) — current frozen benchmark package, manifests, and checksums
- [`manifests/`](manifests) — dataset and run manifests
- [`evidence/history/`](evidence/history) — historical benchmark-development provenance retained for inspection

For direct claim-to-evidence links, use the [Evidence map](docs/EVIDENCE_MAP.md).

## Scope

The published result covers `eval_core` under BASE, SYSTEM, CONTEXT, and QLoRA. It does not claim observed holdout, LONG-NEUTRAL, persistence, remediation, or second-run results. See [Results](docs/RESULTS.md) for the full evidence boundary.
