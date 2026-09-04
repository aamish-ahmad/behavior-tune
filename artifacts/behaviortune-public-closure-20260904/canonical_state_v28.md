## CONTROL PLANE — CURRENT AUTHORITATIVE STATE
**STATE_VERSION:** 28  
**STATUS:** CLOSED  
**CURRENT_TRANSITION_ID:** `V1.1-R1-PUBLIC-PROOF-CLOSURE`  
**CURRENT_TRANSITION:** PASS — G8/G10 public proof and portfolio terminal verification  
**NEXT_AUTHORITY:** Aamish Ahmad; project authority returned

**Terminal proof:**
- GitHub source, configs, tests, reproducibility docs, accepted evidence, results, failures, cards, provenance, hashes, and claim map are public at `https://github.com/aamish-ahmad/behavior-tune`; release tag `v1.0.0` is the immutable portfolio entrypoint. Archival remote history was preserved by a non-destructive merge and no force push occurred.
- The exact frozen V1.1-R1 dataset is public at `https://huggingface.co/datasets/aamish-ahmad/behaviortune-v1-1-r1`; verified content revision `1cafbc1f9cf421d43446c385545319a3b0a0a3eb`, current repository revision `2911473b2166e7e4b3173cbcf534b54a348373b9`. Its card exposes all six splits, schema, provenance, balance/design, limitations, license metadata, manifests, and hashes. All 12 published content blobs match the local frozen sources.
- The accepted QLoRA adapter is public at `https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter`; verified content revision `9b4095666621104a94ce2193e62de363e35cba75`, current repository revision `89daa76d5ba62f47118f376695199ec2ad4db401`. The 264,308,896-byte LFS object has SHA-256 `8d16ef2cb6ff7a982511fd58f21eff52538761f4d198b4cc5cbfd73ca7c9d4de`; its card records the pinned base revision, recipe, dependencies, matched results, provenance, limitations, and license metadata.
- Release checksum ledger PASS, 21/21. Public-proof verification SHA-256: `b8d268f1365bebbb125dfa5a567e093e37e49fe42e084e1089d3fb1784338251`.

**Gate closure:**
- G8 PASS — both public Hugging Face repositories and their exact payloads were independently read back and verified.
- G10 PASS — `docs/CV_CLAIM_MAP.md` SHA-256 `4a90b928a790be0df8aa4043fe9361324edb9911cdc4114d735233860ea3f073` contains all four canonical clauses verbatim and maps each to public inspectable proof.
- G1 through G10 are PASS. The accepted R1 empirical boundary remains explicit: observed results cover activation and specificity on `eval_core`; no observed holdout, persistence, generalization, or remediation outcome is claimed.

**Forbidden-work confirmation:** no new training, inference, benchmark redesign, holdout observation, model family, sweep, cloud/GPU lifecycle, or scientific expansion occurred. No secret value was emitted or persisted by the executor.

**Exact stop state:** BehaviorTune V1 is `CLOSED`; all portfolio hard gates pass, public code/dataset/adapter proof is verified, and no next execution transition is authorized.
