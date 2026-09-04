## CONTROL PLANE — CURRENT AUTHORITATIVE STATE
**STATE_VERSION:** 31
**STATUS:** CLOSED
**CURRENT_TRANSITION_ID:** `V1.1-R1-RECRUITER-PUBLIC-METADATA`
**CURRENT_TRANSITION:** Recruiter-facing GitHub/Hugging Face metadata and anonymous public-surface repair
**NEXT_AUTHORITY:** returned to human

**Terminal verdict:** VERIFIED. An unauthenticated external reviewer can open the GitHub repository and raw README, GitHub About metadata and all eight requested topics render, the public `v1.0.0` release resolves, no deployments exist, and irrelevant Packages/Deployments sections are absent from the anonymous repository page.

**Hugging Face proof:** the public dataset revision is `3c38b860a4443fe7ca0c31d09347d7ec8910bc62`; Dataset Viewer reports `viewer: true`, lists all six required splits, and renders rows for each split. The public adapter revision is `3322230280eed993711dfc09705ebef5cef39b41`; its immutable adapter LFS SHA-256 remains `8d16ef2cb6ff7a982511fd58f21eff52538761f4d198b4cc5cbfd73ca7c9d4de`.

**Public proof:** GitHub https://github.com/aamish-ahmad/behavior-tune ; release https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0 ; dataset https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1 ; adapter https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter . GitHub presentation commit: `97d8189cf76a69b58dd0e31320d82aacedf510f5`.

**Independent verification:** `artifacts/behaviortune-public-surface-repair-20260904/ANONYMOUS_PUBLIC_SURFACE_VERIFICATION.json`, SHA-256 `5da4ab2eaf441ebdc5db8bca712eafe2c22f9a0926bd5de38b0b733880350226`, verdict `VERIFIED`; every public card/results/claim-map link resolves anonymously. Both release and frozen V1.1-R1 checksum ledgers pass, including all 12 frozen canonical objects.

**Scientific integrity:** no frozen JSONL bytes, labels, split membership, adapter weights/config, accepted result, or canonical scientific hash changed. No training, inference, GPU/cloud work, new science, V2, benchmark change, holdout observation, or secret exposure occurred.

**Hard gates:** G1 PASS; G2 PASS; G3 PASS; G4 PASS; G5 PASS; G6 PASS; G7 PASS; G8 PASS; G9 PASS; G10 PASS.

**Exact terminal state:** BehaviorTune is CLOSED. Authority is returned to the human.
