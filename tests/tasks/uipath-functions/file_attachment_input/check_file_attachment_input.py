#!/usr/bin/env python3
"""File-attachment-input Coded Function check.

Verifies the artifacts a Coded Function accepting a `job-attachment` input
MUST produce, per the uipath-functions skill ("File attachment inputs"):

  1. `attachment-agent/pyproject.toml` has `[project]` + `authors` and
     NO `[build-system]` section.
  2. `attachment-agent/main.py` imports `Attachment` from
     `uipath.platform.attachments` and declares an `Input` model with an
     `Attachment`-typed field.
  3. `attachment-agent/main.py` has no module-level UiPath* client
     construction (lazy init).
  4. `attachment-agent/entry-points.json` carries
     `x-uipath-resource-kind: JobAttachment` somewhere in the input
     schema — the load-bearing artifact proving `uip functions init`
     understood the `Attachment` type so Studio Web / Orchestrator render
     a file picker for that field.

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("attachment-agent")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit(
            "FAIL: pyproject.toml contains a [build-system] section — "
            "Critical Rule C1 forbids it."
        )
    if "[project]" not in text:
        sys.exit("FAIL: pyproject.toml has no [project] section")
    if "authors" not in text:
        sys.exit(
            "FAIL: pyproject.toml has no `authors` entry — `uip functions "
            "pack` will reject the package."
        )
    print("OK: pyproject.toml has [project], `authors`, and no [build-system]")


def check_main_py() -> None:
    main = ROOT / "main.py"
    text = _read_text(main)
    if "from uipath.platform.attachments import Attachment" not in text:
        sys.exit(
            "FAIL: main.py does not import `Attachment` from "
            "`uipath.platform.attachments`."
        )
    if "class Input" not in text:
        sys.exit("FAIL: main.py is missing `class Input`")
    input_block = text.split("class Input", 1)[1].split("class Output", 1)[0]
    if "Attachment" not in input_block:
        sys.exit(
            "FAIL: `Input` model does not reference `Attachment` — the input "
            "field must be typed as `Attachment`."
        )
    print("OK: main.py imports Attachment and declares it on the Input model")
    violations = find_module_level_llm_clients(main)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: main.py has no module-level UiPath* construction")


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    raw = json.dumps(doc)
    if "JobAttachment" not in raw:
        sys.exit(
            "FAIL: entry-points.json does not contain "
            "`x-uipath-resource-kind: JobAttachment` — `uip functions init` "
            "did not emit the job-attachment schema."
        )
    print(
        "OK: entry-points.json carries x-uipath-resource-kind=JobAttachment"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_main_py()
    check_entry_points()


if __name__ == "__main__":
    main()
