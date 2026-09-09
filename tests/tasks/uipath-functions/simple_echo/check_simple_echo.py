#!/usr/bin/env python3
"""Simple Function agent project-shape check.

Verifies the artifacts a Simple Function scaffold MUST produce:

  1. `echo-agent/pyproject.toml` exists, has `[project]` with `authors`,
     and contains NO `[build-system]` section (Critical Rule C1).
  2. `echo-agent/main.py` defines `Input` and `Output` Pydantic models
     and the entry function that `uipath.json` registers. The function
     NAME is arbitrary (SKILL.md), so it is read from `uipath.json`
     rather than assumed to be `main`.
  3. `echo-agent/main.py` does NOT instantiate any UiPath* class at
     module level (Critical Rule C4 — lazy LLM init).
  4. `echo-agent/uipath.json` registers a `main` KEY (required — the
     success criteria run `uip function run main`) pointing at
     `main.py:<any_function_name>`.
  5. `echo-agent/entry-points.json` has one entrypoint whose
     `filePath` is `main` (or `main.py`) and whose input/output
     JSON schemas mention the `message`/`repeat`/`echoed`/`length`
     fields the agent declared.
  6. `echo-agent/bindings.json` is the v2.0 envelope with zero
     resources (the agent makes no SDK calls).

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import load_bindings, count_resources_by_type  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("echo-agent")


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
            "Critical Rule C1 forbids it. UiPath agents do not use a build "
            "system."
        )
    if "[project]" not in text:
        sys.exit("FAIL: pyproject.toml has no [project] section")
    if "authors" not in text:
        sys.exit(
            "FAIL: pyproject.toml has no `authors` entry — `uip function "
            "pack` will reject the package with `Project authors cannot "
            "be empty`."
        )
    print("OK: pyproject.toml has [project], `authors`, and no [build-system]")


def check_uipath_json() -> str:
    """Validate the entrypoint registration; return the entry function name.

    The `main` KEY is required — the task's success criteria run
    `uip function run main`, which resolves that key. The function name
    behind it is arbitrary (SKILL.md: "Both the key and the function name
    are arbitrary"), so any identifier is accepted.
    """
    doc = _load_json(ROOT / "uipath.json")
    functions = doc.get("functions") or {}
    if not functions:
        sys.exit(
            "FAIL: uipath.json has no `functions` map — the entrypoint is not "
            "registered, so the project is not a Coded Function"
        )
    main_entry = functions.get("main")
    if main_entry is None:
        sys.exit(
            f'FAIL: uipath.json `functions` has no "main" key — '
            f'`uip function run main` cannot resolve an entrypoint. '
            f'Got keys: {sorted(functions)}'
        )
    module, _, func = str(main_entry).partition(":")
    if not func:
        sys.exit(
            f'FAIL: uipath.json functions.main should be "<file>:<function_name>", '
            f'got {main_entry!r}'
        )
    if Path(module).name not in ("main.py", "main"):
        sys.exit(
            f'FAIL: uipath.json functions.main should point at main.py, '
            f'got {main_entry!r}'
        )
    print(f'OK: uipath.json registers functions.main -> {main_entry!r}')
    return func


def check_main_py(entry_func: str) -> None:
    main = ROOT / "main.py"
    text = _read_text(main)
    for needle in ("class Input", "class Output"):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")
    # The entry function's NAME is arbitrary — take it from uipath.json and
    # assert main.py actually defines it (sync or async).
    if not re.search(rf"^\s*(async\s+)?def\s+{re.escape(entry_func)}\s*\(", text, re.M):
        sys.exit(
            f"FAIL: main.py does not define `def {entry_func}` — uipath.json "
            f"registers it as the entrypoint but the function is missing"
        )
    print(f"OK: main.py defines Input, Output, and {entry_func}()")
    violations = find_module_level_llm_clients(main)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: main.py has no module-level UiPath* construction")


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints — `uip function init` did not run successfully")
    matches = [
        ep for ep in entrypoints
        if ep.get("filePath") in ("main", "main.py")
    ]
    if not matches:
        paths = [ep.get("filePath") for ep in entrypoints]
        sys.exit(f'FAIL: no entrypoint with filePath "main" or "main.py"; got {paths}')
    ep = matches[0]
    if not ep.get("uniqueId"):
        sys.exit("FAIL: entrypoint is missing `uniqueId` — `uip function init` did not generate it")
    raw = json.dumps(ep)
    for field in ("message", "repeat", "echoed", "length"):
        if field not in raw:
            sys.exit(
                f'FAIL: entrypoint schema does not mention `{field}` — '
                f'agent.json ↔ entry-points.json schema sync failed. '
                f'Got: {raw}'
            )
    print(
        "OK: entry-points.json has one `main` entrypoint with all four "
        "schema fields (message / repeat / echoed / length)"
    )


def check_bindings() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    total = sum(
        count_resources_by_type(doc, t)
        for t in ("asset", "queue", "process", "bucket", "app", "index", "connection", "mcpServer")
    )
    if total != 0:
        sys.exit(
            f"FAIL: simple-echo agent makes no SDK calls — bindings.json "
            f"should have 0 resources, got {total}"
        )
    print("OK: bindings.json is the empty v2.0 envelope (no SDK calls expected)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    entry_func = check_uipath_json()
    check_main_py(entry_func)
    check_entry_points()
    check_bindings()
    if not (ROOT / "run_marker.txt").is_file():
        sys.exit(f"FAIL: {ROOT}/run_marker.txt does not exist — `uip function run` likely never finished")
    print("OK: run_marker.txt exists (run completed cleanly)")


if __name__ == "__main__":
    main()
