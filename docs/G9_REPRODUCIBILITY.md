# G9 reviewer reproducibility path

BehaviorTune exposes the frozen R1 renderer and deterministic scorer without
starting a model. The included fixture is explicitly synthetic and does not
belong to any scientific split.

## Setup

Use Python 3.11 or newer. From a fresh clone, create and activate a virtual
environment, then install only the model-free API/test dependencies and package:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.lock
python -m pip install --no-deps -e .
```

`requirements-test.lock` includes the API lock and the HTTP client needed by
FastAPI's test client. No model, adapter, GPU runtime, or scientific dataset is
downloaded by these setup commands.

## Local CLI replay

From the repository root:

```powershell
python -m behaviortune.cli replay `
  --scenario examples/reviewer_repro/scenario.json `
  --condition BASE `
  --raw-output examples/reviewer_repro/raw_output.txt `
  --output-dir artifacts/reviewer-repro-local
```

macOS/Linux:

```bash
python -m behaviortune.cli replay \
  --scenario examples/reviewer_repro/scenario.json \
  --condition BASE \
  --raw-output examples/reviewer_repro/raw_output.txt \
  --output-dir artifacts/reviewer-repro-local
```

Choose a new output directory on each replay: existing traces are immutable
and are intentionally not overwritten.

The immutable trace contains `scenario.json`, `rendered.json`,
`raw_output.txt`, `scored.json`, `aggregate.json`, `manifest.json`, and
`SHA256SUMS`. This makes the exact path inspectable:

`scenario → render → raw output → deterministic score → aggregate`.

The individual `render`, `score`, and `aggregate` CLI subcommands emit
canonical compact JSON to standard output.

## FastAPI

```powershell
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

Routes:

- `GET /healthz`
- `POST /v1/render`
- `POST /v1/score`
- `POST /v1/aggregate`

All routes are stateless. None loads a model or adapter.
After starting the server, open <http://127.0.0.1:8000/docs> to inspect and try
the request schemas, or <http://127.0.0.1:8000/healthz> for health status.

## Container

```powershell
docker build -t behaviortune-g9 .
docker run --rm -p 8000:8000 behaviortune-g9
```

The container runs as a non-root user, uses the exact top-level and transitive
versions in `requirements-api.lock`, and exposes the same health endpoint.
The G9 acceptance environment did not have a Docker engine, so this transition
performs static Docker-contract validation and records that the image build was
not executed.

## Tests

The G9 suite is deliberately synthetic and model-free:

```powershell
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

It does not read `dev`, `eval_core`, or holdout records.
