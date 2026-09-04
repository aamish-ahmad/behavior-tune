# BehaviorTune

BehaviorTune V1 compares a frozen principal-conditioned decision behavior across
BASE, SYSTEM, CONTEXT, LONG-NEUTRAL, and QLoRA installation conditions.

## Reproducible engineering surface

The repository exposes its frozen condition renderer and deterministic scorer
through both a CLI and a stateless FastAPI service. These engineering surfaces
never load a model; callers provide the raw output to score. A checksum-closed
reviewer replay records the complete path from scenario through render, raw
output, score, and aggregate.

See [docs/G9_REPRODUCIBILITY.md](docs/G9_REPRODUCIBILITY.md) for the CLI, API,
container, and synthetic reviewer workflow.

Run the model-free G9 tests with:

```powershell
python -m unittest tests.test_g9_engineering tests.test_g9_api -v
```

Run the API locally with:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m uvicorn behaviortune.api:app --host 127.0.0.1 --port 8000
```

The project uses local Git only; no remote operation or publication is part of
this milestone.
