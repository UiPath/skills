#!/usr/bin/env python3
"""OpenAI Agents agent project-shape check.

The factory-function pattern (a function that returns an `Agent`, e.g.
`def main() -> Agent`) is the load-bearing invariant for this framework
— without it, `UiPathChatOpenAI(...)` and
`_openai_shared.set_default_openai_client(...)` execute at module
import time and `uip codedagent init` blows up before it can introspect
the agent. The skill guide
(`references/coded/frameworks/openai-agents-integration.md`) documents
the mapping as `<file>:<symbol>` where the symbol may be any variable
or "function that returns an Agent" — so the factory's NAME is free;
what matters is that the symbol is a function, not a module-level
variable.

Checks performed:

  1. `triage-agent/pyproject.toml` declares `uipath-openai-agents`, has
     `[project]` with `authors`, no `[build-system]`.
  2. `openai_agents.json` exists with an `agents` mapping whose target
     `<file>:<symbol>` resolves (AST) to a top-level FUNCTION in that
     file (factory pattern, any name) — pointing at a top-level
     variable would mean module-level `Agent[...]` construction,
     which fails because the agent context type resolution itself can
     pull in the LLM client.
  3. `main.py` declares a `CustomerInput` Pydantic model with
     `customer_id`, has the
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
import subprocess
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-agents")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.bindings_assertions import load_bindings  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("triage-agent")


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


def check_openai_agents_json() -> tuple[Path, str]:
    """Validate the agents mapping and return (factory_file, factory_symbol).

    The skill guide allows `<file>:<symbol>` where the symbol is a variable
    OR a function that returns an Agent. Only the function form preserves
    the lazy-LLM-init invariant, so require the symbol to resolve to a
    top-level function def — under any name (`main`, `agent`, ...).
    """
    doc = _load_json(ROOT / "openai_agents.json")
    agents = doc.get("agents") or {}
    if not agents:
        sys.exit("FAIL: openai_agents.json has no `agents` mapping")
    target = next(iter(agents.values()))
    if not isinstance(target, str) or ":" not in target:
        sys.exit(
            f"FAIL: openai_agents.json agent target must be `<file>:<symbol>`, "
            f"got {target!r}"
        )
    file_part, symbol = target.split(":", 1)
    factory_path = ROOT / file_part
    tree = ast.parse(_read_text(factory_path), filename=str(factory_path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            print(
                f"OK: openai_agents.json registers an agent -> {target!r} "
                f"(factory function `{symbol}`)"
            )
            return factory_path, symbol
    assigned = {
        t.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(t, ast.Name)
    }
    if symbol in assigned:
        sys.exit(
            f"FAIL: openai_agents.json points at {target!r}, a top-level "
            f"variable — module-level `Agent[...]` construction breaks the "
            f"lazy-LLM-init invariant. Point at a factory function that "
            f"returns the Agent instead."
        )
    sys.exit(
        f"FAIL: openai_agents.json points at {target!r} but {file_part} "
        f"defines no top-level function or variable named `{symbol}`."
    )


def check_main_py(factory_symbol: str) -> None:
    main_path = ROOT / "main.py"
    text = _read_text(main_path)
    for needle in ("CustomerInput", "customer_id", "handoffs"):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")
    if "set_default_openai_client" not in text:
        sys.exit(
            "FAIL: main.py never calls `_openai_shared.set_default_openai_client(...)` — "
            "without it the agents fall through to the default OpenAI client "
            "instead of UiPath's gateway."
        )
    # Three named agents: triage, billing, technical. Normalize "BillingAgent" /
    # "billing_agent" / "billing-agent" / "Billing Agent" / "billing" all to
    # "billing" so role-equivalent names pass.
    name_pattern = re.compile(r'''name\s*=\s*['"]([^'"]+)['"]''')
    declared_names = {
        re.sub(r"[\s_-]*agents?$", "", n.lower())
        for n in name_pattern.findall(text)
    }
    expected = {"triage", "billing", "technical"}
    if not expected.issubset(declared_names):
        missing = expected - declared_names
        sys.exit(
            f"FAIL: main.py is missing agent declarations for {sorted(missing)}. "
            f"Found agent names (normalized): {sorted(declared_names)}"
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
                    "is at module level — it must run inside a function body "
                    "(the factory or a hook) to defer authentication until "
                    f"the runtime resolves `{factory_symbol}()`."
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
    _, factory_symbol = check_openai_agents_json()
    check_main_py(factory_symbol)
    check_entry_points()
    check_bindings()
    check_run()


def check_run() -> None:
    """Re-run the agent and verify it completes cleanly.

    Replaces the old run_marker.txt proof — that marker only existed
    because the prompt dictated writing it. Re-running is
    prompt-independent and verifies the same thing the marker did (the
    triage agent runs to completion through the UiPath gateway).
    """
    payload = json.dumps(
        {"messages": "I was charged twice last month, can you check?", "customer_id": "C-101"}
    )
    try:
        proc = subprocess.run(
            ["uip", "codedagent", "run", "agent", payload],
            cwd=ROOT, capture_output=True, text=True, timeout=180,
        )
    except FileNotFoundError:
        sys.exit("FAIL: `uip` CLI not found on PATH — cannot verify the agent runs")
    except subprocess.TimeoutExpired:
        sys.exit("FAIL: `uip codedagent run agent` did not finish within 180s")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[-800:]
        sys.exit(f"FAIL: `uip codedagent run agent` exited {proc.returncode}:\n{detail}")
    print("OK: `uip codedagent run agent` completed cleanly (triage/handoff runs)")


if __name__ == "__main__":
    main()
