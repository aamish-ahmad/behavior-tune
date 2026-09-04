# G9 reviewer reproducibility path

BehaviorTune exposes the frozen R1 renderer and deterministic scorer without
starting a model. The included fixture is explicitly synthetic and does not
belong to any scientific split.

## Local CLI replay

From the repository root:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m behaviortune.cli replay `
  --scenario examples/reviewer_repro/scenario.json `
  --condition BASE `
  --raw-output examples/reviewer_repro/raw_output.txt `
  --output-dir artifacts/reviewer-repro-local
```

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
