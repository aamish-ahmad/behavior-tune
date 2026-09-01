# BehaviorTune dataset-materialization checkpoint

- Status: PASS
- Immutable source baseline: G2-SOURCE commit `661620cede67aece65219b734f504e3c87f9be4d`.
- Materialized scope: exactly 544 scenarios arranged as 272 counterfactual pairs, with the frozen seed `147`.
- Split files: `data/train.jsonl` (240), `data/dev.jsonl` (48), `data/eval_core.jsonl` (64), `data/holdout_principal.jsonl` (64), `data/holdout_family.jsonl` (64), and `data/holdout_joint.jsonl` (64).
- SHA-256 manifest: `manifests/data_manifest.json`; validator audit: `manifests/dataset_validation_audit.json`.
- Validation: all 16 frozen validators PASS, including exact split/family/case counts, pair swap integrity, leakage boundaries, position balance, six-exchange context/long-neutral matching, frozen whitespace-token length ratio (1.0400 to 1.0417), specificity determinism, 128 activation-evaluation persistence probes, and all six manifest hashes.
- Reproducibility: a fresh deterministic regeneration was byte-identical for all six JSONL files.
- Local verification: `python -m unittest discover -s tests -v` passed 21 tests.
- Stop state: no model was run or downloaded; no QLoRA training, adapter creation, scientific-result interpretation, G4 transition, or remote Git operation occurred.
