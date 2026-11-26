#!/usr/bin/env python3
"""Deployment criterion: the seeded folder holds both the process and the agent.

Lists the processes in `<parentFolderPath>/<folderName>` and requires one
`ProcessOrchestration` (the BPMN process) and one `Agent` (the low-code agent)
deployed there.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
_suite_dir = HERE
while _suite_dir != os.path.dirname(_suite_dir) and not os.path.isdir(
    os.path.join(_suite_dir, "_shared")
):
    _suite_dir = os.path.dirname(_suite_dir)
sys.path.insert(0, _suite_dir)

from _shared.bpmn_live import CheckFailure, get_ci, payload_data, run_cli  # noqa: E402

REQUIRED_TYPES = ("ProcessOrchestration", "Agent")


def missing_types(rows: list[Any]) -> list[str]:
    present = {str(get_ci(row, "ProcessType", "") or "").casefold() for row in rows}
    return [t for t in REQUIRED_TYPES if t.casefold() not in present]


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    folder_path = f"{seed['parentFolderPath']}/{seed['folderName']}"

    try:
        completed = run_cli(
            ["uip", "or", "processes", "list", "--folder-path", folder_path, "--all-fields", "--limit", "200"],
            timeout=120,
        )
        _payload, data = payload_data(completed, f"processes list in {folder_path}")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error

    rows = data if isinstance(data, list) else []
    missing = missing_types(rows)
    found = [(get_ci(r, "Name"), get_ci(r, "ProcessType")) for r in rows]
    if missing:
        raise SystemExit(f"FAIL: {folder_path} has no {missing} process; found {found}")
    print(f"PASS: {folder_path} holds {found}")


if __name__ == "__main__":
    main()
