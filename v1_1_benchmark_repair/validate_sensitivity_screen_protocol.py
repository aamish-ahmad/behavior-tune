"""Static validation for the frozen, dev-only V1.1 sensitivity-screen protocol."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "sensitivity_screen_protocol.json"


def main() -> None:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    errors: list[str] = []
    scope = p.get("input_scope", {})
    constraints = p.get("execution_constraints", {})
    gates = p.get("acceptance_gates", {})
    if p.get("status") != "PREDECLARED_NOT_EXECUTED": errors.append("status")
    if scope.get("allowed_split") != "dev" or scope.get("record_count") != 48 or scope.get("pair_count") != 24: errors.append("dev_scope")
    if set(scope.get("forbidden_splits", [])) != {"train", "eval_core", "holdout_principal", "holdout_family", "holdout_joint"}: errors.append("forbidden_splits")
    if set(p.get("conditions", {})) != {"BASE", "SYSTEM"}: errors.append("conditions")
    required_constraints = {"no_training", "no_adapter", "no_model_download_in_this_transition", "no_model_inference_in_this_transition", "no_benchmark_redesign_after_observation", "no_eval_core_or_holdout_read"}
    if any(constraints.get(key) is not True for key in required_constraints): errors.append("execution_constraints")
    expected_gates = {"base_valid_format_rate_min": 0.95, "system_valid_format_rate_min": 0.95, "base_activation_rate_max": 0.7, "system_activation_lift_min": 0.2, "system_activation_rate_min": 0.8, "system_false_favor_rate_max": 0.2}
    if gates != expected_gates: errors.append("acceptance_gates")
    if "controller decision" not in p.get("decision_rule", "").lower(): errors.append("decision_rule")
    if errors:
        raise SystemExit("protocol validation failed: " + ", ".join(errors))
    print("PASS: V1.1 sensitivity-screen protocol is frozen, dev-only, BASE+SYSTEM-only, and unexecuted.")


if __name__ == "__main__":
    main()
