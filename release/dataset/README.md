---
license: other
language:
- en
task_categories:
- text-generation
pretty_name: BehaviorTune Trajectories V1.1-R1
size_categories:
- n<1K
tags:
- synthetic
- behavioral-evaluation
- qlora
configs:
- config_name: default
  data_files:
  - split: eval_core
    path: data/eval_core.jsonl
  - split: train
    path: data/train.jsonl
  - split: dev
    path: data/dev.jsonl
  - split: holdout_principal
    path: data/holdout_principal.jsonl
  - split: holdout_family
    path: data/holdout_family.jsonl
  - split: holdout_joint
    path: data/holdout_joint.jsonl
---

# BehaviorTune Trajectories V1.1-R1

A frozen synthetic dataset for evaluating principal-conditioned binary-choice
behavior under BASE, SYSTEM, CONTEXT, LONG-NEUTRAL, and QLoRA installation
conditions. It contains 544 scenarios arranged as 272 counterfactual pairs.

## Splits

| Split | Scenarios | Pairs | SHA-256 |
| --- | ---: | ---: | --- |
| `train` | 240 | 120 | `be16a7c198cacd727992f4ff82493ec40e5c042f9a485e2091a62eab213f91eb` |
| `dev` | 48 | 24 | `5eed447ba0878e4a6e26729476ef43d5bd59966469558fc1a0545af904023e5f` |
| `eval_core` | 64 | 32 | `807eb5c7ef3bede23aa2fbf44fa4ad3607877835256cdad9383518953c681c1d` |
| `holdout_principal` | 64 | 32 | `48fef33ebfb7a8d4f3b46ad4b8c3eb6befcb4c542d6af828455c5860e8e344fc` |
| `holdout_family` | 64 | 32 | `f823607a3f42b2c549c502a9958fb805a75beff18fdf1d177d839f752a166df2` |
| `holdout_joint` | 64 | 32 | `0cc76df04c5cc394b4f9f46938c6d2605328caffbb9930b8907494f3bb44cd24` |

## Record schema

Each JSONL row is one scenario. Stable identifiers and grouping fields include
`schema_version`, `scenario_id`, `pair_id`, `split`, `template_id`,
`source_family`, `case_type`, and `variant_id`. Decision inputs include
`principal_a`, `principal_b`, `option_order`, `base_facts`, `decision_prompt`,
`opaque_marker`, `context_trajectory`, and `long_neutral_trajectory`. Frozen
labels and controls include `designated_position`, `marker_target_position`,
`target_choice`, `objective_winner`, `activation_expected`,
`persistence_probe`, and `source_designation_removed`.

The `eval_core` file is listed first in the viewer configuration so the generic
JSON builder infers the optional `persistence_probe` struct before loading the
train and dev splits, where that field is uniformly null. This ordering changes
only Hub presentation; the canonical JSONL files and their hashes are unchanged.

## Design and provenance

The opaque markers `OMK-A17` and `OMK-B29` encode first/second-position policy
only in the privileged SYSTEM contract. BASE receives no mapping. Specificity
cases require following decisive evidence regardless of the marker. Split
membership, counterfactual pairing, labels, and hashes are frozen at Git commit
[`8ab1915`](https://github.com/aamish-ahmad/behavior-tune/commit/8ab1915df01498c0c30aad7162dbfe47ca4cdd89).

The repository contains the exact [data manifest](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/v1_1_r1/r1_data_manifest.json), [freeze manifest](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/v1_1_r1/FREEZE_MANIFEST.json), [checksum ledger](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/v1_1_r1/SHA256SUMS.txt), and [materializer](https://github.com/aamish-ahmad/behavior-tune/blob/v1.0.0/v1_1_r1/materialize.py).

## Intended use and limitations

Use the dataset with the pinned BehaviorTune renderer and deterministic scorer.
Do not use dev or holdout splits for training or model selection. All records
are synthetic; they do not represent real people, organizations, or deployment
decisions.

The accepted R1 result evaluates only `eval_core`. Publishing the remaining
splits makes the frozen design inspectable and reproducible; it does not imply
that holdout, persistence, or remediation results were observed.

## License and usage

`license: other` denotes that no open-source or open-data license is granted.
The public files may be inspected and evaluated. Contact the copyright holder
for permission to copy, modify, redistribute, or use them beyond rights
provided by the hosting platform.
