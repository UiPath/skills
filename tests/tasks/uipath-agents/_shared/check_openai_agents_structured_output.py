#!/usr/bin/env python3
"""OpenAI Agents structured-output project-shape check.

The factory-function pattern (`def main() -> Agent`) is the load-bearing
invariant — without it, `UiPathChatOpenAI(...)` and
`_openai_shared.set_default_openai_client(...)` execute at module import
time and `uip codedagent init` fails before it can introspect the agent.

This task also exercises `output_type` schema detection: `uip codedagent
init` must extract both the `Agent[ReviewInput]` context type and the
`output_type=ReviewOutput` into `entry-points.json`.

Checks performed:

  1. `review-analyzer/pyproject.toml` declares `uipath-openai-agents`,
     has `[project]` with `authors`, no `[build-system]`.
  2. `openai_agents.json` exists with an `agents` mapping pointing at
     `main.py:main` (factory pattern — a top-level `agent` variable
     would trigger module-level LLM setup and break init).
  3. `main.py` defines `ReviewInput` (with `review_text`), `ReviewOutput`
     (with `sentiment`, `confidence`, `summary`), a `def main()` factory,
     `output_type=ReviewOutput` on the Agent, deferred
     `set_default_openai_client(...)`, and no module-level UiPath*
     construction.
  4. `entry-points.json` reflects `review_text` (from `Agent[ReviewInput]`)
     and `sentiment` (from `output_type=ReviewOutput`) — proves
     `uip codedagent init` ran after both Pydantic models were written.
  5. `bindings.json` is the v2.0 envelope.

Exits 0 on all checks passing, with a `FAIL: ...` message on the first violation.
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

ROOT = find_project_root("review-analyzer")


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
            "the OpenAI Agents integration guide makes this dependency mandatory."
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
            f"FAIL: openai_agents.json should point at the factory function "
            f"(`<file>:main`), got {target!r}. "
            f"Pointing at a top-level variable breaks the lazy-LLM-init invariant."
        )
    print(f"OK: openai_agents.json registers an agent -> {target!r} (factory pattern)")


def check_main_py() -> None:
    main_path = ROOT / "main.py"
    text = _read_text(main_path)
    for needle in (
        "ReviewInput",
        "review_text",
        "ReviewOutput",
        "sentiment",
        "confidence",
        "summary",
        "def main",
        "output_type",
    ):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")
    if "set_default_openai_client" not in text:
        sys.exit(
            "FAIL: main.py never calls `_openai_shared.set_default_openai_client(...)` — "
            "without it the agent falls through to the default OpenAI client "
            "instead of UiPath's gateway."
        )
    print(
        "OK: main.py declares ReviewInput, ReviewOutput with output_type, "
        "factory function, and UiPath gateway routing"
    )
    violations = find_module_level_llm_clients(main_path)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(
        "OK: main.py has no module-level UiPath* construction "
        "(factory-function pattern preserved)"
    )


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit(
            "FAIL: entry-points.json has no entryPoints — "
            "`uip codedagent init` did not run successfully"
        )
    raw = json.dumps(entrypoints)
    for field in ("review_text", "sentiment"):
        if field not in raw:
            sys.exit(
                f"FAIL: entry-points.json schemas do not mention `{field}`. "
                f"Either `uip codedagent init` ran before the Pydantic models "
                f"were written, or the models did not declare the expected fields. "
                f"Got: {raw}"
            )
    print(
        "OK: entry-points.json reflects Agent[ReviewInput] (review_text) "
        "and output_type=ReviewOutput (sentiment)"
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


if __name__ == "__main__":
    main()
