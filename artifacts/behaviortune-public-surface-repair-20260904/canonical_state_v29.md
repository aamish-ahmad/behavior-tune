## CONTROL PLANE — CURRENT AUTHORITATIVE STATE
**STATE_VERSION:** 29  
**STATUS:** STARTED  
**CURRENT_TRANSITION_ID:** `V1.1-R1-ANONYMOUS-PUBLIC-SURFACE-REPAIR`  
**CURRENT_TRANSITION:** Repair and independently verify the actual anonymous GitHub and Hugging Face dataset-viewer surfaces  
**NEXT_AUTHORITY:** project controller only

**Reconciled predecessor and defects:**
- The accepted scientific and engineering state remains unchanged through commit `f5921758f334bab356ec64492850d029f9903cb6`; G1–G10 evidence is retained but terminal public closure is suspended pending this repair.
- Anonymous `https://github.com/aamish-ahmad/behavior-tune` and its raw `main/README.md` currently return HTTP 404, proving the repository is private despite v28 metadata.
- Hugging Face lists all six dataset splits, but `is-valid` reports `viewer: false`; `eval_core` and all three holdouts return HTTP 500 because `persistence_probe` was inferred as `null` from train and cannot cast later struct values.
- The public adapter is reachable and is out of mutation scope unless a broken link requires repair.

**Committed repair boundary:** make GitHub genuinely public; repair only dataset presentation/configuration, preserving every canonical JSONL byte/hash, label, and split membership; anonymously verify GitHub, all six dataset viewer splits, adapter, and public proof links; then re-close. No training, inference, cloud/GPU work, new science, V2, benchmark change, force push, or secret exposure is authorized.

**Exact stop state:** `V1.1-R1-ANONYMOUS-PUBLIC-SURFACE-REPAIR` is STARTED. Continue only through the committed public-surface repair to verified CLOSED or one irreducible external blocker.
