"""Immutable local run-ledger serialization for real or fake backends."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return b"".join(_json_bytes(row) for row in rows)


def write_immutable_run_ledger(output_root: Path, run_id: str, manifest: dict[str, Any], raw_rows: list[dict[str, Any]], scored_rows: list[dict[str, Any]]) -> Path:
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    raw_payload = _jsonl_bytes(raw_rows)
    scored_payload = _jsonl_bytes(scored_rows)
    completed_manifest = {
        **manifest,
        "run_id": run_id,
        "output_checksums": {"raw.jsonl": hashlib.sha256(raw_payload).hexdigest(), "scored.jsonl": hashlib.sha256(scored_payload).hexdigest()},
    }
    (run_dir / "raw.jsonl").write_bytes(raw_payload)
    (run_dir / "scored.jsonl").write_bytes(scored_payload)
    (run_dir / "run_manifest.json").write_bytes(_json_bytes(completed_manifest))
    return run_dir


def write_reviewer_trace(
    output_dir: Path,
    scenario: dict[str, Any],
    rendered: dict[str, Any],
    raw_output: str,
    scored: dict[str, Any],
    aggregate: dict[str, Any],
    manifest: dict[str, Any],
) -> Path:
    """Write one immutable, checksum-closed scenario-to-aggregate trace."""
    output_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        "scenario.json": _json_bytes(scenario),
        "rendered.json": _json_bytes(rendered),
        "raw_output.txt": (raw_output.rstrip("\n") + "\n").encode("utf-8"),
        "scored.json": _json_bytes(scored),
        "aggregate.json": _json_bytes(aggregate),
    }
    for name, payload in payloads.items():
        (output_dir / name).write_bytes(payload)
    completed = {
        **manifest,
        "output_checksums": {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
    }
    manifest_payload = _json_bytes(completed)
    (output_dir / "manifest.json").write_bytes(manifest_payload)
    checksums = {
        **completed["output_checksums"],
        "manifest.json": hashlib.sha256(manifest_payload).hexdigest(),
    }
    (output_dir / "SHA256SUMS").write_bytes(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checksums.items())).encode("utf-8")
    )
    return output_dir
