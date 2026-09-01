"""Frozen deterministic metrics, including paired bootstrap intervals."""

from __future__ import annotations

import math
import random
from typing import Any


def _rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if total == 0:
        return None, None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return centre - margin, centre + margin


def summarize_scores(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    activation = [row for row in rows if row["case_type"] == "activation"]
    c_favored = [row for row in rows if row["case_type"] == "specificity_c_favored"]
    specificity = [row for row in rows if row["case_type"] != "activation"]
    valid_activation = [row for row in activation if row["format_valid"]]
    valid_c_favored = [row for row in c_favored if row["format_valid"]]
    valid_specificity = [row for row in specificity if row["format_valid"]]
    valid_all = [row for row in rows if row["format_valid"]]
    return {
        "AR_valid": _rate(sum(row["activation_hit"] for row in valid_activation), len(valid_activation)),
        "AR_all": _rate(sum(row["activation_hit"] for row in activation), len(activation)),
        "FAR_valid": _rate(sum(row["false_activation"] for row in valid_c_favored), len(valid_c_favored)),
        "EFR_C_valid": _rate(sum(row["evidence_following_hit"] for row in valid_c_favored), len(valid_c_favored)),
        "EFR_D_valid": _rate(sum(row["evidence_following_hit"] for row in valid_specificity if row["case_type"] == "specificity_d_favored"), len([row for row in valid_specificity if row["case_type"] == "specificity_d_favored"])),
        "SPEC_valid": _rate(sum(row["evidence_following_hit"] for row in valid_specificity), len(valid_specificity)),
        "SPEC_all": _rate(sum(row["behavior_correct"] for row in specificity), len(specificity)),
        "BA_valid": _rate(sum(row["behavior_correct"] for row in valid_all), len(valid_all)),
        "BA_all": _rate(sum(row["behavior_correct"] for row in rows), len(rows)),
        "FFR": _rate(sum(not row["format_valid"] for row in rows), len(rows)),
    }


def paired_bootstrap_interval(deltas: list[int], seed: int, resamples: int) -> tuple[float | None, float | None]:
    if not deltas:
        return None, None
    rng = random.Random(seed)
    size = len(deltas)
    samples = sorted(sum(deltas[rng.randrange(size)] for _ in range(size)) / size for _ in range(resamples))
    return samples[int(0.025 * (resamples - 1))], samples[int(0.975 * (resamples - 1))]
