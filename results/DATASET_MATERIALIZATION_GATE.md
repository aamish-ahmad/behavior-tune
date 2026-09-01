# BehaviorTune dataset-materialization gate

- Status: PASS
- Supersedes the pre-G2-SOURCE blocker recorded here.
- Immutable source baseline: `661620cede67aece65219b734f504e3c87f9be4d`.
- Materialization proof: exactly 544 scenarios / 272 counterfactual pairs across the six frozen JSONL splits, with SHA-256 entries in `manifests/data_manifest.json`.
- Verification proof: `manifests/dataset_validation_audit.json` records PASS for all 16 frozen validators, and deterministic regeneration was byte-identical for every split file.
- Checkpoint: `results/DATASET_MATERIALIZATION_CHECKPOINT.md`.
- Stop state: no model run/download, QLoRA training, adapter, scientific-result interpretation, remote Git operation, or G4 transition occurred.
