# Evidence map — claims to public proof

This document maps the repository's public claims to inspectable, versioned artifacts. It intentionally avoids internal planning or portfolio-language; each claim links directly to the evidence a reviewer or engineer needs to verify the claim.

1) Post-training adapter (identity and bytes)
- Adapter (Hugging Face): https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter
- Adapter SHA-256 and pinned base revision: release/adapter/README.md

2) Training implementation and manifest
- Training code: src/behaviortune/train.py
- Training manifest (frozen): artifacts/behaviortune-v11-r1-qlora-core-20260904/training_evidence/training_manifest.json

3) Public dataset
- Hugging Face dataset: https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1
- R1 data manifest (frozen splits & hashes): v1_1_r1/r1_data_manifest.json

4) Matched evaluation and metrics
- Runtime manifest: artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/runtime_manifest.json
- Raw outputs: artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/raw_outputs.jsonl
- Per-example deterministic scores: artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/scores.jsonl
- Aggregate metrics & gate decision: artifacts/behaviortune-v11-r1-qlora-core-20260904/evaluation_evidence/metrics.json and gate_decision.json

5) Engineering surfaces and contracts
- Runtime boundary and inference helpers: src/behaviortune/runtime.py, src/behaviortune/inference.py
- CLI and stateless API: src/behaviortune/cli.py, src/behaviortune/api.py
- Container / API lockfile: Dockerfile, requirements-api.lock
- Reviewer replay fixture: examples/reviewer_repro/

6) Independent verification and provenance
- Final verification: artifacts/behaviortune-v11-r1-qlora-core-20260904/FINAL_VERIFICATION.json
- Release provenance and hashes: release/PROVENANCE_AND_HASHES.json

Notes
- The v1.0.0 tag and the release artifacts are immutable evidence. Do not treat the Evidence Map as authoritative for runtime behavior; it is a navigational guide to the public artifacts included in the repository and referenced by the tagged release.
