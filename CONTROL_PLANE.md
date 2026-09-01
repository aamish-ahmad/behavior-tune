# BehaviorTune Control Plane

## Human interface

Aamish issues only one of three operational tokens:

- `START`
- `DONE`
- `BLOCKED`

He is not the transport layer for prompts, hashes, paths, state summaries, or transition logic.

## Mandatory reconciliation — FIRST

**Every token begins with a fresh remote reconciliation. No exception.**

Before interpreting `START`, `DONE`, or `BLOCKED`:

1. Read canonical Notion state.
2. Read `state/behaviortune_state.json` from this GitHub repository.
3. Compare current transition id, status, authorized scope, exact stop state, and next authority.
4. Treat local files, prior chat context, cached blockers, and previous terminal output as NON-AUTHORITATIVE.

If Notion and GitHub disagree: return `BLOCKED_STATE_DIVERGENCE` and stop.

A stale local transition is not a blocker. Discard it after successful remote reconciliation.

## Token semantics

### START
After reconciliation, execute only the current remotely authorized transition. Write `STARTED` to both durable stores before substantive execution. Finish by writing `PASS` or `BLOCKED` to both, then stop.

### DONE
After reconciliation, report the current durable state only. Do not execute a transition.

### BLOCKED
This is a **force-reconcile-and-stop** token. After reconciliation, report the current remote blocker if one exists. If remote state is READY, report READY and the authorized transition. Never preserve or acknowledge a stale cached blocker.

## State architecture

- **Notion** is the canonical decision/state record.
- **GitHub** mirrors the machine-readable execution state.
- Executors read both before every action.
- Executors write terminal transition state back to both.
- Local runtime state is only a cache and may never override reconciled remote state.

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
