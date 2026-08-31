# BehaviorTune

BehaviorTune V1 compares a frozen principal-conditioned decision behavior across
BASE, SYSTEM, CONTEXT, LONG-NEUTRAL, and QLoRA installation conditions.

## G3-A/B status

This repository currently contains the frozen condition-rendering substrate and
a shared, injected model-loading/generation boundary. It preserves one canonical
scenario representation and renders the same final decision block for every
condition. The boundary is verified with test doubles only: no scientific
scenario data, model download, inference, training, adapter, or result artifact
is included.

Run the local unit tests with:

```powershell
python -m unittest discover -s tests -v
```

The project uses local Git only; no remote operation is part of this milestone.
