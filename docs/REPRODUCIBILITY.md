# Engineering quickstart

This walkthrough reproduces BehaviorTune's **model-free engineering surfaces**: the renderer, deterministic scorer, CLI replay, and stateless FastAPI routes. It does not download a model, run training, or rerun the frozen scientific evaluation.

## Setup

Use Python 3.11 or newer. From a fresh clone:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.lock
python -m pip install --no-deps -e .
```

## Run the engineering tests

```bash
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

These tests cover the renderer/scorer/aggregate chain, trace checksum checks, CLI replay, API routes, request validation, health metadata, and the static container contract.

## Create an inspectable replay

macOS/Linux:

```bash
python -m behaviortune.cli replay \
  --scenario examples/reviewer_repro/scenario.json \
  --condition BASE \
  --raw-output examples/reviewer_repro/raw_output.txt \
  --output-dir artifacts/reviewer-repro-local
```

Windows PowerShell:

```powershell
python -m behaviortune.cli replay `
  --scenario examples/reviewer_repro/scenario.json `
  --condition BASE `
  --raw-output examples/reviewer_repro/raw_output.txt `
  --output-dir artifacts/reviewer-repro-local
```

A replay writes `scenario.json`, `rendered.json`, `raw_output.txt`, `scored.json`, `aggregate.json`, `manifest.json`, and `SHA256SUMS` without overwriting an existing trace. Use a new output directory for each run.

## Inspect the API

```bash
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

Available routes:

- `GET /healthz`
- `POST /v1/render`
- `POST /v1/score`
- `POST /v1/aggregate`

Open <http://127.0.0.1:8000/docs> for the interactive request schemas. All routes are stateless and model-free.

## Optional container build

```bash
docker build -t behaviortune .
docker run --rm -p 8000:8000 behaviortune
```

The image runs as a non-root user, installs the versions in `requirements-api.lock`, and exposes the same health endpoint. The published release statically verified this container contract; no image-build claim is made for the scientific evaluation.

## What this reproduces

This path verifies the public engineering interface without modifying the frozen training or evaluation evidence. For the measured result and its limitations, see [Results](RESULTS.md). For direct claim-to-artifact links, see the [Evidence map](EVIDENCE_MAP.md).
