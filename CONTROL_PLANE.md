# BehaviorTune Control Plane

## Human interface

Aamish issues only one of three operational commands:

- `START`
- `DONE`
- `BLOCKED`

He is not the transport layer for prompts, hashes, paths, or state summaries.

## State architecture

- **Notion** is the canonical decision/state record.
- **GitHub** mirrors the machine-readable execution state in `state/behaviortune_state.json`.
- Executors must read both before acting.
- Executors must write completion/blocker state back to both.
- Any disagreement between the two is `BLOCKED_STATE_DIVERGENCE`; never guess or self-reconcile.

## Transition ownership

Controller owns WHAT / WHY / admissibility / next transition.

Executor owns HOW inside the currently authorized transition.

Only the controller may authorize the next transition.

## Required writeback

Each transition records:

- transition id/name
- `STARTED`, `PASS`, or `BLOCKED`
- authorized scope
- evidence paths/URLs
- hashes / commit SHAs
- exact stop state
- confirmation that forbidden work did not occur
- next authority = controller

## Current state

See `state/behaviortune_state.json`.
