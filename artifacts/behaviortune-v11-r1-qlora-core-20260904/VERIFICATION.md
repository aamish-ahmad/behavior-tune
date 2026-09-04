# BehaviorTune V1.1-R1 primary QLoRA matched-core verification

**Result: PASS**

- Independent checks: 23/23
- Training: one primary run, 240 R1 rows, 3 epochs, 90 optimizer steps
- Evaluation: 64 eval_core records x BASE/SYSTEM/CONTEXT/QLORA = 256 outputs
- Frozen gates: PASS (6/6)
- QLoRA minus BASE activation delta: 0.34375
- Paired bootstrap 95% interval: [0.1875, 0.5]
- Lifecycle: one launch, one termination, fresh authenticated inventory 0
- Authority: returned; stale epoch continuation rejected
- Retry/additional scientific run: not executed
