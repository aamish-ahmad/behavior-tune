# BehaviorTune

BehaviorTune is a reproducible post-training and behavioral-evaluation project.
The accepted V1.1-R1 run compares one frozen principal-conditioned decision
behavior across matched BASE, SYSTEM, CONTEXT, and QLoRA conditions using
`Qwen/Qwen3-4B-Instruct-2507` at revision
`cdbee75f17c01a7cc42f958dc650907174af0554`.

## Public release

- [Results and limitations](docs/RESULTS.md)
- [CV claim to public proof map](docs/CV_CLAIM_MAP.md)
- [Hugging Face dataset](https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1)
- [Hugging Face QLoRA adapter](https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter)
- [Dataset card source](release/dataset/README.md)
- [Adapter card source](release/adapter/README.md)
- [Release provenance and hashes](release/PROVENANCE_AND_HASHES.json)

The accepted R1 result is a real, bounded QLoRA intervention: 240 training
rows, three epochs, 90 optimizer steps, and one matched 64-scenario evaluation
per condition. QLoRA improved format-valid activation by `0.34375` over BASE;
the predeclared paired-bootstrap 95% interval was `[0.1875, 0.5]`, all six
frozen gates passed, and no retry was run. See [results](docs/RESULTS.md) for
the exact evidence boundary; R1 did not evaluate holdouts, persistence,
remediation, or LONG-NEUTRAL.

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

The accepted G9 evidence used static Docker-contract validation because its
environment had no Docker engine; it does not claim that an image build was
executed. Release artifacts are checksum-closed and the repository is tagged
`v1.0.0`.
