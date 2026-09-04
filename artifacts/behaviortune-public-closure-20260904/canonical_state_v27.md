## CONTROL PLANE — CURRENT AUTHORITATIVE STATE
**STATE_VERSION:** 27  
**STATUS:** STARTED  
**CURRENT_TRANSITION_ID:** `V1.1-R1-PUBLIC-PROOF-CLOSURE`  
**CURRENT_TRANSITION:** G8/G10 public-proof closure and terminal verification  
**NEXT_AUTHORITY:** project controller only
**Accepted predecessor state:**
- Canonical v26 G9 PASS was freshly read back with the exact prepared block SHA-256 `4c03113bb64060fdb134cf130758917d21e691fcfe73e45013910b2ace4039d0`, one checked G9 gate, no unchecked G9 gate, and no v25 block.
- G9 remains committed at `6ef019e996982417df50127a5c351f179b75ea6b`; its independent verification remains PASS, 15/15.
- R1 sensitivity verification remains PASS, 28/28; accepted primary QLoRA verification remains PASS, 23/23, with six gates passed and no retry.
**Committed scope:**
- Publish current R1 code/evidence to `https://github.com/aamish-ahmad/behavior-tune`, preserving its archival history without force replacement.
- Publish the exact frozen V1.1-R1 dataset and accepted adapter to the authenticated `aamish-ahmad` Hugging Face namespace with R1-current cards, provenance, and hashes.
- Map the frozen canonical CV claim clauses verbatim to public proof, verify every URL/hash, mark G8 and G10 PASS, write CLOSED, and return authority.
**Current evidence and boundary:**
- Local R1 release packaging, results, cards, provenance, claim mapping, curated raw/scored evidence, and no-license-grant metadata are committed; eight model-free G9 tests and the release checksum ledger pass.
- The private GitHub archival history is integrated by a non-destructive unrelated-history merge. Public visibility, push, tag, and Hugging Face uploads are not yet claimed.
- The public Hugging Face profile `aamish-ahmad` exists, but the current host `HF_TOKEN` has been rejected by the API after safe normalization; credential recovery remains in-scope only through already available non-secret tooling.
- No model run, training, inference, benchmark/data mutation, holdout observation, scientific expansion, cloud GPU lifecycle, or secret persistence is authorized or performed.
**Exact stop state:** `V1.1-R1-PUBLIC-PROOF-CLOSURE` is STARTED. Continue only through the committed public-proof transition; stop at verified CLOSED or one irreducible external blocker.
