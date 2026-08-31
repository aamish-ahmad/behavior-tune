# BehaviorTune dataset-materialization gate

- Status: BLOCKED
- Target: materialize the frozen 544-scenario G2 dataset and deterministic validator suite.
- Observed local state: hydrated `data/G2_FROZEN_DATASET_CONTRACT.md` fixes the 544/272 schedule, seed 147, split/pair allocation, six family mechanisms, context/long-neutral/persistence rules, and 16 validator predicates.
- Missing authoritative inputs: the frozen, versioned template-bank entries and slot-dictionary entries required by the contract to determine each scenario's facts, calibration history, neutral control history, and persistence-probe wording.
- Mechanical checks: the local project contains no template bank or slot dictionary; canonical Notion searches for `BehaviorTune template bank` and `BehaviorTune slot dictionary` returned only the specification's references to those missing inputs, not their contents.
- Decision: do not generate or infer scenario text, template IDs, facts, histories, probes, or slot values. The generator and 16 validators cannot be implemented against concrete scenario records without these frozen inputs.
- Scope preserved: no scenario dataset, generator, validator implementation, model execution, model download, training, adapter creation, scientific scoring, or G4 work was performed.
