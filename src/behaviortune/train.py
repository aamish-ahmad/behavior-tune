"""Fail-closed dry-run training entrypoint; it never starts QLoRA without later authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .harness import build_dry_run_readiness


def training_dry_run(config_path: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    readiness = build_dry_run_readiness()
    return {"status": "READY", "mode": "dry_run_only", "recipe_id": config["recipe_id"], "dataset": config["dataset"], "freeze": readiness["freeze"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("training is disabled in harness-readiness mode; use --dry-run only")
    print(json.dumps(training_dry_run(Path(args.config)), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
