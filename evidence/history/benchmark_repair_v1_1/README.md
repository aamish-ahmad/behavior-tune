# BehaviorTune V1.1 opaque-marker benchmark repair

This directory preserves the historical benchmark-repair design record used before the current frozen V1.1-R1 benchmark. It does not modify, read, or derive rows from the frozen V1 data files.

`build.py` materializes and validates a 544-row abstract blueprint with the V1 split and counterfactual structure. It checks the opaque-marker contract, counterfactual principal/position balance, split isolation, deterministic labels, and case coverage. The blueprint is not a model-evaluation dataset and does not authorize a BASE/SYSTEM run or training.

Run from the repository root:

```powershell
python evidence/history/benchmark_repair_v1_1/build.py
python evidence/history/benchmark_repair_v1_1/validate_sensitivity_screen_protocol.py
```
