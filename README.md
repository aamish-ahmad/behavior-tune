# BehaviorTune

**Open-model QLoRA post-training and matched evaluation for Qwen3-4B — public adapter, dataset, deterministic scoring, and reproducible engineering surfaces.**

[![CI](https://github.com/aamish-ahmad/behavior-tune/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aamish-ahmad/behavior-tune/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/aamish-ahmad/behavior-tune?label=release)](https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)

What you should know in 10 seconds

- Real QLoRA post-training on Qwen3-4B with a published PEFT/QLoRA adapter.
- Public dataset and frozen evaluation evidence that produced a measurable, inspectable result.
- Engineering surfaces: CLI, stateless FastAPI, Docker contract, and tests — all reproducible without a GPU.

What this project demonstrates

- PEFT/QLoRA post-training (adapter published on Hugging Face)
- A matched BASE/SYSTEM/CONTEXT/QLoRA evaluation with deterministic scoring
- Reproducible engineering: CLI, FastAPI, Docker, and unit tests

Quick recruiter tour

| Start here | What you'll see |
| --- | --- |
| Adapter (Hugging Face) | Published QLoRA adapter and adapter hash |
| Dataset (Hugging Face) | Inspectable six-split synthetic dataset |
| Short result & graph | One measured matched result with a link to full evidence |
| Reproduce (Engineering) | CLI replay and API quickstart (no GPU required) |

One measured result (short)

QLoRA increased format-valid activation from **0.65625 → 1.00000** on the frozen eval_core set — a **+0.34375 (+34.375 pp)** matched shift (paired-bootstrap 95% CI: [0.1875, 0.5]).

See docs/RESULTS.md for the full condition tables, raw outputs, gates, and frozen evidence.

Quick start — no GPU or model download

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

Run a replay (engineering verification):

```bash
python -m behaviortune.cli replay \
  --scenario examples/reviewer_repro/scenario.json \
  --condition BASE \
  --raw-output examples/reviewer_repro/raw_output.txt \
  --output-dir artifacts/reviewer-repro-local
```

Repository map (recruiter-first)

- src/behaviortune/ — runtime, CLI, API, scoring, dataset helpers
- configs/ — frozen training & evaluation configuration
- docs/ — results, reproducibility, evidence map (deep links)
- examples/ — reviewer replay fixtures
- tests/ — unit and engineering tests
- release/, artifacts/, results/, v1_1_r1/, v1_1_benchmark_repair/, manifests/ — deep evidence and provenance (inspectable)

For full scientific detail (condition-level tables, raw outputs, manifests, and the acceptance decision) see docs/RESULTS.md and the artifacts/ directory referenced there.
