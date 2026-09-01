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
