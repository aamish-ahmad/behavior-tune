"""Materialize the versioned V1.1-R1 runnable benchmark without model activity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviortune.v11r1 import write_materialization  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(write_materialization(), sort_keys=True))
