"""BehaviorTune G9 model-free command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engineering import aggregate_scores, render_record, replay_to_directory, score_record


def _json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _jsonl(path: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="behaviortune", description="Deterministic BehaviorTune reviewer tools")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render")
    render.add_argument("--scenario", required=True)
    render.add_argument("--condition", required=True)
    score = sub.add_parser("score")
    score.add_argument("--scenario", required=True)
    score.add_argument("--condition", required=True)
    score.add_argument("--raw-output", required=True)
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--scores", required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--scenario", required=True)
    replay.add_argument("--condition", required=True)
    replay.add_argument("--raw-output", required=True)
    replay.add_argument("--output-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "render":
        result = render_record(_json(args.scenario), args.condition)
    elif args.command == "score":
        result = score_record(_json(args.scenario), args.condition, Path(args.raw_output).read_text(encoding="utf-8").strip())
    elif args.command == "aggregate":
        result = aggregate_scores(_jsonl(args.scores))
    else:
        destination = replay_to_directory(
            _json(args.scenario), args.condition,
            Path(args.raw_output).read_text(encoding="utf-8").strip(), Path(args.output_dir),
        )
        result = {"status": "PASS", "output_dir": str(destination), "model_activity": False}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
