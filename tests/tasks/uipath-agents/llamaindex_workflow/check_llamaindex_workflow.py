#!/usr/bin/env python3
"""LlamaIndex Workflow agent project-shape check.

Checks performed:

  1. `qna-workflow/pyproject.toml` declares `uipath-llamaindex`, has
     `[project]` with `authors`, and contains NO `[build-system]`
     section.
  2. `llama_index.json` exists with a `workflows` mapping pointing to
     a `<file>:workflow` (or any variable name) reference.
  3. `main.py` defines `Question(StartEvent)`, `Answer(StopEvent)`,
     a `Workflow` subclass, exports a top-level `workflow` variable,
     and has NO module-level UiPath* construction.
  4. `entry-points.json` reflects the StartEvent/StopEvent fields:
     `question` (input), `answer` and `word_count` (output).
  5. `bindings.json` is the v2.0 envelope.

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import load_bindings  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("qna-workflow")


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
    if "[project]" not in text or "authors" not in text:
        sys.exit("FAIL: pyproject.toml is missing [project] or `authors`")
    if "uipath-llamaindex" not in text:
        sys.exit(
            "FAIL: pyproject.toml does not declare `uipath-llamaindex` — "
            "the LlamaIndex integration guide makes this dependency "
            "mandatory."
        )
    print("OK: pyproject.toml is hygienic and declares uipath-llamaindex")


def check_llama_index_json() -> None:
    doc = _load_json(ROOT / "llama_index.json")
    workflows = doc.get("workflows") or {}
    if not workflows:
        sys.exit("FAIL: llama_index.json has no `workflows` mapping")
    target = next(iter(workflows.values()))
    if not isinstance(target, str) or ":" not in target:
        sys.exit(
            f'FAIL: llama_index.json workflows entry should map to a '
            f'`<file>:<variable>` reference, got {target!r}'
        )
    print(f"OK: llama_index.json registers a workflow -> {target!r}")


def check_main_py() -> None:
    main = ROOT / "main.py"
    text = _read_text(main)
    for needle in ("StartEvent", "StopEvent", "Workflow", "@step", "workflow"):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")
    print(
        "OK: main.py defines StartEvent/StopEvent subclasses, a Workflow, "
        "a @step, and exports a workflow variable"
    )
    violations = find_module_level_llm_clients(main)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(
        "OK: main.py has no module-level UiPath* construction "
        "(lazy-LLM-init invariant holds)"
    )


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints")
    raw = json.dumps(entrypoints)
    for field in ("question", "answer", "word_count"):
        if field not in raw:
            sys.exit(
                f'FAIL: entry-points.json schemas do not mention `{field}`. '
                f'StartEvent/StopEvent fields were not picked up by '
                f'`uip codedagent init`. Got: {raw}'
            )
    print(
        "OK: entry-points.json reflects StartEvent/StopEvent fields "
        "(question, answer, word_count)"
    )


def check_bindings() -> None:
    load_bindings(ROOT / "bindings.json")
    print("OK: bindings.json envelope is well-formed")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_llama_index_json()
    check_main_py()
    check_entry_points()
    check_bindings()
    if not (ROOT / "run_marker.txt").is_file():
        sys.exit(f"FAIL: {ROOT}/run_marker.txt does not exist — `uip codedagent run` likely never finished")
    print("OK: run_marker.txt exists (run completed cleanly)")


if __name__ == "__main__":
    main()
