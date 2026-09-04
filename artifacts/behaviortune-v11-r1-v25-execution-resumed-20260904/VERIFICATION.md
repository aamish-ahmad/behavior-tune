# BehaviorTune v25 canonical runtime verification

**Result: PASS**

- Independent checks: 28/28
- Routed worker: one verified effect, returned, stale continuation rejected
- Lambda lifecycle: one launch, one termination request, fresh authenticated inventory 0
- Real host: A100-SXM4, CUDA 12.8, BF16, NF4, frozen dependency hash verified
- Screen: 48 dev records x BASE/SYSTEM = 96 outputs; all six gates PASS
- Diagnostics: BASE and SYSTEM C-favored/D-favored evidence-following all 1.0
- QLoRA: not started
