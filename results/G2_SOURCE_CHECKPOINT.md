# BehaviorTune G2-SOURCE checkpoint

- Status: PASS
- Frozen source artifacts: `data/source/g2_template_banks.json` and `data/source/g2_slot_dictionaries.json`.
- Source version: `G2-SOURCE-1`.
- Contract binding: `data/G2_FROZEN_DATASET_CONTRACT.md` SHA-256 `f32ee1aca121fab4ccd148fd0d5c3998f41fc5ff1e5e255197fe0e90c8735256`.
- Template-bank SHA-256: `8ff36499f7669b0e053201a30b77663ee54f91be7f2010bf9f38fb1ba4c18cce`.
- Slot-dictionary SHA-256: `d158abebb9bf7ce7dbc9ca7a6fa26f973d5f628491c08e696894097e43231a4b`.
- Contents: six frozen family mechanisms, all three frozen case types, counterfactual-pair rule, split-safe template-ID pattern, two counterbalanced six-exchange CONTEXT profiles, matched LONG-NEUTRAL source text, activation persistence-probe source, 272 abstract case markers, and 160 abstract probe markers.
- Verification: `python -m unittest discover -s tests -v` passed 18 tests, including source version, family/case coverage, 6-exchange balance, policy leakage, approximate long-neutral length match, no principal IDs/final choices, source-domain separation, uniqueness slots, and no dataset JSONL.
- Stop state: no final 544-scenario dataset, principal assignment, target choice, model execution/download, training, adapter, or scientific result was created.
