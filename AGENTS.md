# BehaviorTune local execution boundary

This repository contains only BehaviorTune project state. Resolve shared Codex
runtime from the installed global skills; do not copy skill implementations into
this repository.

For G3-A/G3-B, the frozen V1 Notion contract is authoritative. G1 and G2 must
not be reinterpreted or modified. G3-B may add only the shared
condition-runtime/model-loading boundary and deterministic test doubles. It
must not generate scenarios, train or download a model, create an adapter, or
write scientific results.

Use local Git only. Do not configure or operate any Git remote from this
repository unless a later controller instruction explicitly permits it.
