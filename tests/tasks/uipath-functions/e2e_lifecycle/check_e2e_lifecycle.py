#!/usr/bin/env python3
"""Python Coded Function (uip functions CLI) — project-shape check.

Verifies that the agent used the updated `uip functions` CLI, chose the Python
Coded Function pattern for a naturally-phrased validation request, and produced
a project that satisfies all structural invariants.

Checks performed:

  1. `invoice-validator/pyproject.toml` has `[project]` with `authors`, no
     `[build-system]`, and no LLM framework dependencies. (Project type is
     determined from `uipath.json`, not pyproject — see check 3.)
  2. `invoice-validator/main.py` uses typed I/O for Input and Output (stdlib
     `@dataclass`, pydantic `BaseModel`, or `pydantic.dataclasses.dataclass`),
     declares all required fields (`invoice_number`, `vendor_name`,
     `total_amount`, `currency`, `is_valid`, `validation_errors`,
     `normalized_currency`), includes the `@traced` decorator (SDK integration),
     and contains no LLM imports.
  3. `invoice-validator/uipath.json` has a `functions` key with a valid
     `<file>:<function_name>` entrypoint — this is what identifies the project
     as a Coded Function (`determine_project_type()` reads the entrypoint type
     from uipath.json, not pyproject).
  4. `invoice-validator/entry-points.json` has at least one entrypoint whose
     schema mentions `invoice_number` and `is_valid` — proves `uip functions init`
     ran after the schema models were written.
  5. `invoice-validator/run_marker.txt` exists — proves `uip functions run`
     completed successfully.

Exits 0 on PASS, `sys.exit("FAIL: ...")` on the first violation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def find_project_root(default_subdir: str) -> Path:
    """Resolve the on-disk project root for a Coded Function test.

    Functions are scaffolded with `uip functions new <NAME>`, which produces
    a `<NAME>/` subdir. Some agents `cd` in and work flat; others stay at the
    sandbox root. This helper handles both by looking for `pyproject.toml`.
    """
    cwd = Path(os.getcwd())
    if (cwd / "pyproject.toml").is_file():
        return cwd
    nested = cwd / default_subdir
    if (nested / "pyproject.toml").is_file():
        return nested
    return nested


ROOT = find_project_root("invoice-validator")

_LLM_IMPORT_TOKENS = (
    "llm_gateway",
    "UiPathChat",
    "UiPathChatOpenAI",
    "UiPathAzureChatOpenAI",
    "from openai import",
    "import openai",
    "from langchain",
    "from llama_index",
    "from agents import",
)

_LLM_PACKAGES = (
    "uipath-langchain",
    "uipath-openai-agents",
    "uipath-llama-index",
)


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
            "Python Coded Functions must not use a build system (Critical Rule C1)."
        )
    if "[project]" not in text:
        sys.exit("FAIL: pyproject.toml has no [project] section")
    if "authors" not in text:
        sys.exit("FAIL: pyproject.toml has no `authors` entry")
    for pkg in _LLM_PACKAGES:
        if pkg in text:
            sys.exit(
                f"FAIL: pyproject.toml declares `{pkg}` — Python Coded Functions "
                f"are deterministic and must not depend on LLM frameworks."
            )
    print("OK: pyproject.toml — [project], authors, no [build-system], "
          "no LLM packages")


def check_main_py() -> None:
    main_path = ROOT / "main.py"
    text = _read_text(main_path)

    # Typed I/O is required, but the SDK accepts several forms: stdlib
    # @dataclass, pydantic BaseModel, or pydantic.dataclasses.dataclass (the
    # shipped samples use pydantic). Accept any recognized typed form.
    if not any(m in text for m in ("@dataclass", "BaseModel", "pydantic")):
        sys.exit(
            "FAIL: main.py Input/Output are not typed — use a stdlib @dataclass, "
            "pydantic BaseModel, or pydantic.dataclasses.dataclass."
        )

    for needle in ("class Input", "class Output"):
        if needle not in text:
            sys.exit(f"FAIL: main.py is missing `{needle}`")

    input_fields = ("invoice_number", "vendor_name", "total_amount", "currency")
    output_fields = ("is_valid", "validation_errors", "normalized_currency")
    for field in (*input_fields, *output_fields):
        if field not in text:
            sys.exit(f"FAIL: main.py is missing field `{field}` in schema or logic")

    if "traced" not in text:
        sys.exit(
            "FAIL: main.py does not use the `@traced` decorator — "
            "SDK tracing integration is required for Python Coded Functions."
        )

    print("OK: main.py — typed Input/Output, all required fields, @traced present")

    for token in _LLM_IMPORT_TOKENS:
        if token in text:
            sys.exit(
                f"FAIL: main.py imports or references `{token}` — Python Coded "
                f"Functions must be deterministic with no LLM calls."
            )
    print("OK: main.py — no LLM imports")


def check_uipath_json() -> None:
    doc = _load_json(ROOT / "uipath.json")
    functions = doc.get("functions") or {}
    if not functions:
        sys.exit(
            "FAIL: uipath.json has no `functions` key — the entrypoint is not "
            "registered. `uip functions init` may not have run."
        )
    # Any key is valid (not required to be "main"); value must be file:function
    entrypoint = next(iter(functions.values()), "")
    if ":" not in str(entrypoint):
        sys.exit(
            f"FAIL: uipath.json functions entrypoint should be `<file>:<function_name>`, "
            f"got {entrypoint!r}"
        )
    print(f"OK: uipath.json registers functions entrypoint -> {entrypoint!r}")


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit(
            "FAIL: entry-points.json has no entryPoints — "
            "`uip functions init` (Python-only) did not run successfully."
        )
    raw = json.dumps(entrypoints)
    for field in ("invoice_number", "is_valid"):
        if field not in raw:
            sys.exit(
                f"FAIL: entry-points.json schemas do not mention `{field}`. "
                f"Either `uip functions init` ran before the schema models "
                f"were written, or the models did not declare the expected fields. "
                f"Got: {raw}"
            )
    print("OK: entry-points.json reflects Input schema (invoice_number) and "
          "Output schema (is_valid)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_main_py()
    check_uipath_json()
    check_entry_points()
    # Agent may write the marker in the project dir or the sandbox root
    marker = ROOT / "run_marker.txt"
    sandbox_marker = ROOT.parent / "run_marker.txt"
    if not marker.is_file() and not sandbox_marker.is_file():
        sys.exit(
            f"FAIL: run_marker.txt not found in {ROOT} or {ROOT.parent} — "
            "`uip functions run` likely never completed."
        )
    print("OK: run_marker.txt exists (run completed cleanly)")


if __name__ == "__main__":
    main()
