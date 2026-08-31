# BehaviorTune G2 local contract hydration checkpoint

- Status: PASS
- Source: `07 — BehaviorTune V1` (Notion page `3c0d086d-0fe9-8157-851e-ddec745382af`), fetched 2026-09-01.
- Local frozen source: `data/G2_FROZEN_DATASET_CONTRACT.md`
- Contract SHA-256: `f32ee1aca121fab4ccd148fd0d5c3998f41fc5ff1e5e255197fe0e90c8735256`
- Hydrated scope: canonical 544-scenario / 272-pair generation contract, six family allocations, fixed seed 147, split schedules, context/long-neutral/persistence rules, reproducibility rule, and all 16 validator requirements.
- Verification: `python -m unittest discover -s tests -v` passed 12 tests, including local contract schedule, family, seed, validator-numbering, and no-JSONL-materialization checks.
- Stop state: the dataset-generation contract is now project-local versioned truth. No scenario dataset, template bank, slot dictionary, model run, model download, training, adapter, or scientific result was created.
