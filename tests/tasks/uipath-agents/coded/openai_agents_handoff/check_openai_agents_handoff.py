#!/usr/bin/env python3
"""OpenAI Agents agent project-shape check.

The factory-function pattern (`def main() -> Agent`) is the load-bearing
invariant for this framework — without it, `UiPathChatOpenAI(...)` and
`_openai_shared.set_default_openai_client(...)` execute at module
import time and `uip codedagent init` blows up before it can introspect
the agent.

Checks performed:

  1. `triage-bot/pyproject.toml` declares `uipath-openai-agents`, has
     `[project]` with `authors`, no `[build-system]`.
  2. `openai_agents.json` exists with an `agents` mapping pointing at
     `main.py:main` (factory pattern) — pointing at a top-level
     `agent` variable would mean module-level `Agent[...]`
     construction, which fails because the agent context type
     resolution itself can pull in the LLM client.
  3. `main.py` defines a `def main()` factory, declares a
     `CustomerInput` Pydantic model with `customer_id`, has the
     `_openai_shared.set_default_openai_client(...)` call INSIDE the
     factory, configures three agents (`triage`, `billing`,
     `technical`) with at least one `handoffs=` list, and has NO
     module-level UiPath* construction.
  4. `entry-points.json` reflects the `customer_id` context field
     and the standard `messages` field every OpenAI Agent accepts.
  5. `bindings.json` is the v2.0 envelope.

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import load_bindings  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("triage-bot")


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
    if "uipath-openai-agents" not in text:
        sys.exit(
            "FAIL: pyproject.toml does not declare `uipath-openai-agents` — "
            "the OpenAI Agents integration guide makes this dependency "
            "mandatory."
        )
    print("OK: pyproject.toml is hygienic and declares uipath-openai-agents")


def check_openai_agents_json() -> None:
    doc = _load_json(ROOT / "openai_agents.json")
    agents = doc.get("agents") or {}
    if not agents:
        sys.exit("FAIL: openai_agents.json has no `agents` mapping")
    target = next(iter(agents.values()))
    if not isinstance(target, str) or ":main" not in target:
        sys.exit(
            f'FAIL: openai_agents.json should point at the factory function '
            f'(`<file>:main`), got {target!r}. Pointing at a top-level '
            f'variable would break the lazy-LLM-init invariant.'
        )
    print(f"OK: openai_agents.json registers an agent -> {target!r} (factory pattern)")


def check_main_py() -> None:
    main_path = ROOT / "main.py"
    text = _read_text(main_path)
    for needle in ("CustomerInput", "customer_id", "def main", "handoffs"):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")
    if "set_default_openai_client" not in text:
        sys.exit(
            "FAIL: main.py never calls `_openai_shared.set_default_openai_client(...)` — "
            "without it the agents fall through to the default OpenAI client "
            "instead of UiPath's gateway."
        )
    # Three named agents: triage, billing, technical
    name_pattern = re.compile(r'name\s*=\s*"([^"]+)"')
    declared_names = set(name_pattern.findall(text))
    expected = {"triage", "billing", "technical"}
    if not expected.issubset(declared_names):
        missing = expected - declared_names
        sys.exit(
            f"FAIL: main.py is missing agent declarations for {sorted(missing)}. "
            f"Found agent names: {sorted(declared_names)}"
        )
    print("OK: main.py declares triage / billing / technical agents with handoffs")
    violations = find_module_level_llm_clients(main_path)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(
        "OK: main.py has no module-level UiPath* construction "
        "(factory-function pattern preserved)"
    )
    # Confirm set_default_openai_client is INSIDE a function body — not at
    # module level — by AST walk.
    tree = ast.parse(text, filename=str(main_path))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr == "set_default_openai_client":
                sys.exit(
                    f"FAIL: main.py:{node.lineno} `set_default_openai_client(...)` "
                    "is at module level — it must run inside the factory "
                    "function body to defer authentication until the runtime "
                    "calls main()."
                )
    print("OK: set_default_openai_client(...) is inside the factory body")


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints")
    raw = json.dumps(entrypoints)
    for field in ("customer_id", "messages"):
        if field not in raw:
            sys.exit(
                f'FAIL: entry-points.json schemas do not mention `{field}`. '
                f'`uip codedagent init` did not pick up the Agent[CustomerInput] '
                f'context type. Got: {raw}'
            )
    print(
        "OK: entry-points.json reflects the Agent[CustomerInput] context "
        "(customer_id) and the standard `messages` field"
    )


def check_bindings() -> None:
    load_bindings(ROOT / "bindings.json")
    print("OK: bindings.json envelope is well-formed")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_openai_agents_json()
    check_main_py()
    check_entry_points()
    check_bindings()
    if not (ROOT / "run_marker.txt").is_file():
        sys.exit(f"FAIL: {ROOT}/run_marker.txt does not exist — `uip codedagent run` likely never finished")
    print("OK: run_marker.txt exists (run completed cleanly)")


if __name__ == "__main__":
    main()
