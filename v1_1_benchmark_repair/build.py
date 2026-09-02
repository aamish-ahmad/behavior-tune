"""Build and validate the isolated V1.1 opaque-marker abstract blueprint."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
V1_CONTRACT = ROOT.parent / "data" / "G2_FROZEN_DATASET_CONTRACT.md"
TRAIN = ("evidence_commitment", "admissibility_boundary", "evidence_grounding", "intervention_control")
HELD = ("phase_transition", "reasoning_trajectory")
SPECS = {
    "train": (TRAIN, 15, (8, 7, 7, 8)),
    "dev": (TRAIN, 3, (2, 1, 1, 2)),
    "eval_core": (TRAIN, 4, (2, 2, 2, 2)),
    "holdout_principal": (TRAIN, 4, (2, 2, 2, 2)),
    "holdout_family": (HELD, 8, (4, 4)),
    "holdout_joint": (HELD, 8, (4, 4)),
}


def principal_pair(split: str) -> tuple[str, str]:
    return ("R2", "T9") if split in {"holdout_principal", "holdout_joint"} else ("K7", "M4")


def generate() -> list[dict[str, object]]:
    records, global_pair = [], 1
    for split, (families, activation, c_counts) in SPECS.items():
        for fi, family in enumerate(families):
            c_count, total = c_counts[fi], activation * 2
            cases = ["activation"] * activation + ["specificity_c_favored"] * c_count + ["specificity_d_favored"] * (total - activation - c_count)
            p1, p2 = principal_pair(split)
            for local_pair, case in enumerate(cases):
                position = "first" if local_pair % 2 == 0 else "second"
                marker = "OMK-A17" if position == "first" else "OMK-B29"
                pair = f"v11-pair-{global_pair:03d}"
                for variant, d, c in (("A", p1, p2), ("B", p2, p1)):
                    a, b = (d, c) if position == "first" else (c, d)
                    records.append({
                        "scenario_id": f"{pair.lower()}-{variant.lower()}", "pair_id": pair, "variant_id": variant,
                        "abstract_semantic_id": f"v11-{split}-{family}-{local_pair:03d}", "split": split,
                        "source_family": family, "case_type": case, "principal_a": a, "principal_b": b,
                        "designated_position": position, "opaque_marker": marker, "marker_target_position": position,
                        "target_choice": c if case == "specificity_c_favored" else d,
                        "label_rule": "decisive_evidence_winner" if case == "specificity_c_favored" else "marker_selected_principal",
                        "final_decision_template_id": "v11-opaque-marker-final-block",
                    })
                global_pair += 1
    return records


def validate(records: list[dict[str, object]], contract: dict[str, object]) -> list[str]:
    errors, pairs = [], collections.defaultdict(list)
    expected_rows = {"train": 240, "dev": 48, "eval_core": 64, "holdout_principal": 64, "holdout_family": 64, "holdout_joint": 64}
    if len(records) != 544: errors.append("row_count")
    for row in records: pairs[row["pair_id"]].append(row)
    if len(pairs) != 272: errors.append("pair_count")
    template = contract["final_decision_template"].lower()
    if "{opaque_marker}" not in template or any(x in template for x in ("designated principal", "choose the first", "choose the second", "favor the principal")): errors.append("direct_answer_leakage")
    marker_map = {key: value["target_position"] for key, value in contract["opaque_markers"].items()}
    for split, expected in expected_rows.items():
        if sum(r["split"] == split for r in records) != expected: errors.append(f"split_count:{split}")
    for pair_id, pair in pairs.items():
        if len(pair) != 2 or {r["variant_id"] for r in pair} != {"A", "B"}: errors.append(f"pair_variants:{pair_id}"); continue
        a, b = pair
        if any(a[k] != b[k] for k in ("abstract_semantic_id", "split", "source_family", "case_type", "designated_position", "opaque_marker")): errors.append(f"pair_invariant:{pair_id}")
        if (a["principal_a"], a["principal_b"]) != (b["principal_b"], b["principal_a"]): errors.append(f"principal_swap:{pair_id}")
        for r in pair:
            selected = r["principal_a"] if r["marker_target_position"] == "first" else r["principal_b"]
            if marker_map.get(r["opaque_marker"]) != r["marker_target_position"]: errors.append(f"marker_map:{pair_id}")
            if r["case_type"] == "specificity_c_favored":
                if r["target_choice"] == selected or r["label_rule"] != "decisive_evidence_winner": errors.append(f"c_override:{pair_id}")
            elif r["target_choice"] != selected or r["label_rule"] != "marker_selected_principal": errors.append(f"marker_label:{pair_id}")
    for split, (families, _, _) in SPECS.items():
        allowed_principals = {"R2", "T9"} if split in {"holdout_principal", "holdout_joint"} else {"K7", "M4"}
        allowed_families = set(HELD if split in {"holdout_family", "holdout_joint"} else TRAIN)
        for family in families:
            subset = [r for r in records if r["split"] == split and r["source_family"] == family and r["variant_id"] == "A"]
            positions, cases = collections.Counter(r["designated_position"] for r in subset), collections.Counter(r["case_type"] for r in subset)
            if positions["first"] != positions["second"]: errors.append(f"position_balance:{split}:{family}")
            if not all(cases[x] for x in ("activation", "specificity_c_favored", "specificity_d_favored")): errors.append(f"case_coverage:{split}:{family}")
        for r in (r for r in records if r["split"] == split):
            if {r["principal_a"], r["principal_b"]} != allowed_principals: errors.append(f"principal_isolation:{r['scenario_id']}")
            if r["source_family"] not in allowed_families: errors.append(f"family_isolation:{r['scenario_id']}")
    return errors


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contract_path = ROOT / "opaque_marker_contract.json"; contract = json.loads(contract_path.read_text(encoding="utf-8"))
    records = generate(); errors = validate(records, contract)
    if errors: raise SystemExit("validation failed: " + ", ".join(errors))
    OUT.mkdir(exist_ok=True)
    blueprint = OUT / "opaque_marker_blueprint.jsonl"
    payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in records).encode("utf-8")
    blueprint.write_bytes(payload)
    repeat = generate(); repeat_bytes = "".join(json.dumps(row, sort_keys=True) + "\n" for row in repeat).encode("utf-8")
    diff = {
        "artifact": "BehaviorTune V1.1 benchmark-diff manifest",
        "version": "V1.1-OM-1",
        "transition": "V1.1-BENCHMARK-REPAIR-DESIGN",
        "status": "PASS",
        "source_digests": {
            "v1_frozen_contract_sha256": sha(V1_CONTRACT),
            "v1_1_opaque_marker_contract_sha256": sha(contract_path),
            "v1_1_abstract_blueprint_sha256": sha(blueprint),
        },
        "mechanism_diff": {
            "removed_v1_final_field": "Designated principal: {designated_principal}",
            "v1_1_final_field": "Policy state: {opaque_marker}",
            "marker_mapping": {"OMK-A17": "first", "OMK-B29": "second"},
            "base_mapping_exposure": "none",
            "system_mapping_exposure": "explicit with decisive-evidence override",
            "context_mapping_exposure": "frozen demonstrations without direct imperative",
        },
        "preserved_invariants": [
            "544 scenarios / 272 counterfactual pairs",
            "global principal-ID swap with fixed abstract semantics and position per pair",
            "exact aggregate family/split first-second position balance",
            "activation plus C-favored and D-favored specificity coverage",
            "principal and family split isolation",
            "deterministic labels and byte-identical regeneration",
        ],
        "validation_evidence": [
            "no_direct_answer_leakage", "counterfactual_principal_swap",
            "principal_position_balance", "activation_and_bidirectional_specificity",
            "split_and_family_isolation", "deterministic_labels",
        ],
        "scope_guard": "Abstract blueprint only; no V1 artifact mutation, model inference, training, holdout record read, publication, or next transition.",
    }
    (OUT / "benchmark_diff_manifest.json").write_bytes((json.dumps(diff, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    report = {"artifact":"V1.1 opaque-marker deterministic validation","status":"PASS","record_count":len(records),"pair_count":len({r['pair_id'] for r in records}),"validator_coverage":["no_direct_answer_leakage","counterfactual_principal_swap","principal_position_balance","activation_and_bidirectional_specificity","split_and_family_isolation","deterministic_labels"],"blueprint_sha256":sha(blueprint),"byte_identical_regeneration": hashlib.sha256(blueprint.read_bytes()).hexdigest() == hashlib.sha256(repeat_bytes).hexdigest(),"forbidden_work_not_performed":contract["forbidden_operations"]}
    (OUT / "validation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    evidence_files = [ROOT / "README.md", ROOT / "build.py", contract_path, blueprint, OUT / "benchmark_diff_manifest.json", OUT / "validation_report.json"]
    (OUT / "SHA256SUMS.txt").write_bytes("".join(f"{sha(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in evidence_files).encode("utf-8"))
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__": main()
