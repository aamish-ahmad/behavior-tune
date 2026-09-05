# BehaviorTune V1.1 opaque-marker benchmark repair

This directory is a separately versioned design artifact. It does not modify,
read, or derive rows from frozen V1 data files.

`build.py` materializes and validates a 544-row abstract blueprint with the V1
split and counterfactual structure. It checks the opaque-marker contract,
counterfactual principal/position balance, split isolation, deterministic
labels, and case coverage. The blueprint is not a model-evaluation dataset and
does not authorize a BASE/SYSTEM run or training.

Run:

```powershell
python v1_1_benchmark_repair/build.py
python v1_1_benchmark_repair/validate_sensitivity_screen_protocol.py
```
