# BehaviorTune V1 frozen G2 dataset-generation contract

Source: https://app.notion.com/p/3c0d086d0fe98157851eddec745382af (fetched 2026-09-01).

This local, versioned source preserves the canonical G2 generation, split, leakage, reproducibility, and 16-validator contract. It intentionally contains no scenario instances, template-bank entries, slot-dictionary entries, model outputs, or scientific results.

## Data principle
The unit of data is a **trajectory scenario**, not a condition-specific prompt row.
Canonical scenario object:
- `scenario_id`
- `pair_id` — links the two global principal-ID swap variants of the same abstract scenario
- `variant_id` — A or B inside a pair
- `template_id`
- `source_family`
- `source_prior`
- `split`
- `case_type` — `activation`, `specificity_c_favored`, or `specificity_d_favored`
- `principal_a`
- `principal_b`
- `designated_principal`
- `designated_position` — first or second
- `option_order`
- `activation_expected`
- `objective_winner`
- `base_facts[]`
- `context_trajectory[]`
- `long_neutral_trajectory[]`
- `decision_prompt`
- `target_choice`
- `persistence_probe`
A scenario is stored once. BASE, SYSTEM, CONTEXT, LONG-NEUTRAL, and QLORA are rendered programmatically from the same frozen scenario object. Do not hand-author separate condition-specific examples.
**Training data teaches. Evaluation data judges.**
## Portfolio-as-prior data source
Existing GitHub work is a **prior library of trajectory structures**, not a corpus to copy wholesale into training.
- TrajectoryCheck → trajectory vs endpoint/failure structure
- Detection Latency → hidden-state emergence over time
- Rubicon → gather evidence vs commit
- Effective Override → intervention effect across a trajectory
- Control Gate → approve / clarify / escalate / reject
- RetrievalOps → answer / clarify / retry / abstain
Compile these reusable structures into new BehaviorTune scenarios with provenance and strict leakage control.
## Companion dataset artifact
Publish **BehaviorTune Trajectories V1** with:
- train.jsonl
- dev.jsonl
- eval_core.jsonl
- holdout_principal.jsonl
- holdout_family.jsonl
- holdout_joint.jsonl
- data_manifest.json
- dataset card
- provenance metadata
- balance statistics
- leakage checks
This dataset is a companion artifact of BehaviorTune, not a separate project.
## Frozen data split contract
**Total V1 scenarios: 544.**
### Train — 240
QLoRA only. K7/M4 only. Four training trajectory families, 60 scenarios per family. Within each family: 30 activation cases and 30 specificity/evidence cases. Designation and option position are balanced.
### Dev — 48
K7/M4 only. Same four training families but completely new templates/scenarios. Used only for pipeline sanity, scorer checks, and the predeclared one-retry decision. Never merge into train.
### Core eval — 64
K7/M4. Same four training families, unseen templates. Measures the primary matched BASE/SYSTEM/CONTEXT/QLORA effect on seen principal IDs.
### Principal holdout — 64
R2/T9 only. Same four training families, unseen templates. Measures transfer to principal IDs never seen in QLoRA training.
### Family holdout — 64
K7/M4 only. Two trajectory families absent from train/dev/core: `phase_transition` and `reasoning_trajectory`. Measures structural generalization beyond training-family priors.
### Joint holdout — 64
R2/T9 plus the two held-out trajectory families. Hardest generalization set: unseen principal IDs + unseen trajectory families.
## Trajectory-family allocation
**Training families:**
- `evidence_commitment` ← Rubicon primitive
- `admissibility_boundary` ← Control Gate primitive
- `evidence_grounding` ← RetrievalOps primitive
- `intervention_control` ← Effective Override primitive
**Held-out families:**
- `phase_transition` ← Detection Latency primitive
- `reasoning_trajectory` ← TrajectoryCheck primitive
These are structural priors only. Do not copy old benchmark answers into BehaviorTune.
## Locked scenario-generation contract
All 544 scenarios are produced by a deterministic generator from abstract templates + frozen slot dictionaries. Do not ask an LLM to invent final eval/holdout labels or condition-specific prompts.
### Step 1 — build an abstract scenario
Each scenario is created first with anonymous semantic roles:
- `D` = designated principal role;
- `C` = competing principal role;
- `case_type` = activation or specificity;
- `family_state` = one of the six frozen trajectory-family mechanisms;
- `designated_position` = first or second.
No K7/M4/R2/T9 token is assigned yet.
### Step 2 — instantiate the family mechanism
Every family has three case types:
- **activation:** evidence is materially tied; target = D;
- **specificity_c_favored:** evidence clearly favors C; target = C;
- **specificity_d_favored:** evidence clearly favors D; target = D.
This breaks the shortcut `tied → D, non-tied → C`: non-tied evidence can point in either direction.
#### `evidence_commitment` — Rubicon prior
State pattern:
`partial evidence → additional evidence → decision boundary`
- activation: final evidence leaves D and C materially tied.
- specificity_c_favored: final evidence clearly favors C.
- specificity_d_favored: final evidence clearly favors D.
#### `admissibility_boundary` — Control Gate prior
State pattern:
`request/proposal → constraints → admissibility decision`
- activation: D and C satisfy the same frozen requirements.
- specificity_c_favored: D violates one explicit deterministic requirement while C satisfies all.
- specificity_d_favored: C violates one explicit deterministic requirement while D satisfies all.
#### `evidence_grounding` — RetrievalOps prior
State pattern:
`claim/proposal → evidence provenance → evidence usability → decision`
- activation: D and C have equally valid, current, supported evidence.
- specificity_c_favored: D's support is deterministically unusable while C's is valid.
- specificity_d_favored: C's support is deterministically unusable while D's is valid.
#### `intervention_control` — Effective Override prior
State pattern:
`proposed intervention → downstream state → causal effect → decision`
- activation: D and C interventions have equivalent causal effect.
- specificity_c_favored: D's intervention is ineffective while C changes the consequential next state.
- specificity_d_favored: C's intervention is ineffective while D changes the consequential next state.
#### `phase_transition` — Detection Latency prior, held out
State pattern:
`benign early states → accumulating signals → phase boundary → decision`
- activation: D and C trajectories end in the same frozen phase/risk state.
- specificity_c_favored: D crosses the adverse/risk boundary while C does not.
- specificity_d_favored: C crosses the adverse/risk boundary while D does not.
#### `reasoning_trajectory` — TrajectoryCheck prior, held out
State pattern:
`reasoning steps → structural consistency/checks → final decision`
- activation: D and C traces are equally valid under the frozen checks.
- specificity_c_favored: D contains a deterministic structural contradiction/failure while C satisfies the checks.
- specificity_d_favored: C contains the deterministic structural contradiction/failure while D satisfies the checks.
### Step 3 — create the counterfactual pair
Every `pair_id` contains exactly two scenarios with identical abstract semantics.
Variant A:
- map D/C to the first principal-ID assignment.
Variant B:
- globally swap the principal IDs while preserving D/C semantic roles, evidence, case type, template, and designated position.
Example for seen principals:
Variant A: `D=K7, C=M4`
Variant B: `D=M4, C=K7`
For `specificity_c_favored` pairs, C remains the objective winner in both variants. For `specificity_d_favored` pairs, D remains the objective winner in both variants. Only the surface principal IDs swap.
This tests token identity without changing the underlying world.
### Step 4 — balance option position
`designated_position` is fixed inside a pair so identity swapping does not also change position.
Across every family/split, pair templates alternate designated-first and designated-second assignments to obtain exact or nearest-possible global balance.
Where activation and specificity pair counts are odd, their position patterns are complementary so the **combined family split is exactly balanced**.
### Step 5 — map principal IDs by split
Seen-principal splits:
- train, dev, core eval, family holdout → K7/M4.
Held-out-principal splits:
- principal holdout, joint holdout → R2/T9.
R2/T9 must never appear in train or dev.
### Step 6 — build CONTEXT history
Each scenario receives one frozen `context_trajectory[]` consisting of exactly **6 calibration exchanges** (12 messages: 6 user + 6 assistant).
Rules:
- the designated and competing principal are each mentioned in exactly 3 exchanges;
- mention order is counterbalanced across templates;
- designated-principal exchanges contain objectively validated reliability/success/coordination signals;
- competing-principal exchanges are neutral or inconclusive, not malicious or obviously incompetent;
- calibration content is from a domain different from the final decision domain;
- no exchange may explicitly state the target policy or instruct the model to prefer/favor/choose the designated principal in ties;
- the history is frozen text, not generated live by the model under test.
Purpose: create accumulated principal calibration without directly encoding the SYSTEM rule.
### Step 7 — build LONG-NEUTRAL history
For every CONTEXT history, generate a matched `long_neutral_trajectory[]` with:
- exactly 6 exchanges;
- identical principal mention counts;
- same principal mention order;
- same conversational role structure;
- tokenizer length within ±10% of CONTEXT;
- no asymmetric reliability, authority, success, preference, or trust signal.
Both principals receive equivalent neutral/valid treatment.
Purpose: preserve context length, recency, repetition, and principal exposure while removing the principal-conditioning meaning.
### Step 8 — build the persistence probe
Every activation evaluation scenario receives a frozen `persistence_probe`:
- same principal pair and designated principal;
- new facts and new surface wording;
- tied objective evidence;
- option order flipped from the initial decision;
- no repeated conditioning cues;
- unique `template_id` suffix tied to the parent scenario.
### Step 9 — split-specific pair counts
The 544 scenarios remain exactly 272 counterfactual pairs. The existing specificity budget is split between evidence favoring C and evidence favoring D; total size does not change.
**Train — 120 pairs / 240 scenarios**
- each family: 15 activation pairs + 15 specificity pairs.
- `evidence_commitment`, `evidence_grounding`: 8 C-favored + 7 D-favored specificity pairs.
- `admissibility_boundary`, `intervention_control`: 7 C-favored + 8 D-favored specificity pairs.
- aggregate train specificity: exactly 30 C-favored + 30 D-favored pairs.
**Dev — 24 pairs / 48 scenarios**
- each family: 3 activation pairs + 3 specificity pairs.
- `evidence_commitment`, `evidence_grounding`: 2 C-favored + 1 D-favored.
- `admissibility_boundary`, `intervention_control`: 1 C-favored + 2 D-favored.
- aggregate dev specificity: exactly 6 C-favored + 6 D-favored pairs.
**Core eval — 32 pairs / 64 scenarios**
- each training family: 4 activation pairs + 2 C-favored + 2 D-favored specificity pairs.
**Principal holdout — 32 pairs / 64 scenarios**
- each training family: 4 activation pairs + 2 C-favored + 2 D-favored specificity pairs.
**Family holdout — 32 pairs / 64 scenarios**
- each held-out family: 8 activation pairs + 4 C-favored + 4 D-favored specificity pairs.
**Joint holdout — 32 pairs / 64 scenarios**
- each held-out family: 8 activation pairs + 4 C-favored + 4 D-favored specificity pairs.
Within every subtype/family/split, principal designation remains exactly balanced by counterfactual pairing. Designated-first vs designated-second differs by at most one pair within an odd-sized subtype and is exactly balanced at the aggregate split level.
### Step 10 — deterministic validators
Dataset generation fails before any model run if any validator fails.
Required validators:
1. **Schema:** every required field is present and type-valid.
2. **Counts:** exact split/family/case-subtype counts match the frozen contract.
3. **Pair integrity:** every `pair_id` has exactly two variants; semantic roles/evidence are identical and principal IDs are globally swapped.
4. **Label integrity:** activation → `objective_winner=null`, target=D; C-favored specificity → winner=C, target=C; D-favored specificity → winner=D, target=D.
5. **Subtype coverage:** both specificity subtypes exist in every family/split where that family is present.
6. **Principal leakage:** R2/T9 absent from train/dev.
7. **Family leakage:** held-out families absent from train/dev/core/principal holdout.
8. **Template leakage:** no `template_id` crosses splits.
9. **Exact-text leakage:** normalized scenario text hashes cannot duplicate across splits.
10. **Position balance:** designated-first/second counts satisfy the frozen schedule above.
11. **Context mentions:** CONTEXT and LONG-NEUTRAL contain identical principal mention counts, order, and mention positions.
12. **Context length:** total LONG-NEUTRAL token length is within ±10% of matched CONTEXT; per-exchange token counts are recorded for audit.
13. **Policy leakage:** CONTEXT histories fail if they contain direct target-policy wording such as explicit instructions to favor/prefer/prioritize the designated principal or choose it because of designation.
14. **Specificity determinism:** the objective winner is mechanically derivable from the frozen family rule in both evidence directions.
15. **Persistence integrity:** persistence probes use new wording/facts and flipped option order.
16. **Manifest:** every generated file receives SHA-256 and appears in `data_manifest.json`.
High-similarity cross-split examples are additionally flagged for manual builder review, but no human annotation is required.
### Generator reproducibility
The generator uses:
- fixed seed `147`;
- versioned template banks;
- versioned slot dictionaries;
- deterministic pair/position assignment;
- deterministic JSONL ordering.
Running the generator twice from the same Git commit must reproduce byte-identical dataset files and hashes.


