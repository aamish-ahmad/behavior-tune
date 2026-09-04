# Reproduce the model-free engineering path

This walkthrough exercises BehaviorTune's renderer, deterministic scorer,
checksum-closed trace, CLI, and FastAPI routes. It does not download a model or
adapter, use a GPU, or read a scientific dataset split.

## Setup

Use Python 3.11 or newer. From a fresh clone:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.lock
python -m pip install --no-deps -e .
```

The test lock includes the API dependencies and HTTP client used by FastAPI's
test client.

## Run the tests

```bash
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

The eight tests cover the renderer/scorer/aggregate chain, designation-leak
rejection, trace checksums, CLI replay, API routes, request validation, health
metadata, and the static container contract.

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

Choose a new output directory for each run. A replay writes `scenario.json`,
`rendered.json`, `raw_output.txt`, `scored.json`, `aggregate.json`,
`manifest.json`, and `SHA256SUMS` without overwriting an existing trace.

```text
scenario → render → raw output → deterministic score → aggregate
```

## Inspect the API

```bash
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

Available routes:

- `GET /healthz`
- `POST /v1/render`
- `POST /v1/score`
- `POST /v1/aggregate`

Open <http://127.0.0.1:8000/docs> for the interactive request schemas. All
routes are stateless and model-free.

## Optional container build

```bash
docker build -t behaviortune .
docker run --rm -p 8000:8000 behaviortune
```

The image runs as a non-root user, installs the exact versions in
`requirements-api.lock`, and exposes the same health endpoint. The accepted
release statically verified this container contract; it does not claim that a
container image was built during scientific evaluation.
