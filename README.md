# BehaviorTune

BehaviorTune V1 compares a frozen principal-conditioned decision behavior across
BASE, SYSTEM, CONTEXT, LONG-NEUTRAL, and QLoRA installation conditions.

## G3-A status

This repository currently contains only the frozen condition-rendering
substrate. It preserves one canonical scenario representation and renders the
same final decision block for every condition. No scientific scenario data,
model download, inference, training, adapter, or result artifact is included.

Run the local unit tests with:

```powershell
python -m unittest discover -s tests -v
```

The project uses local Git only; no remote operation is part of this milestone.
