"""Unit tests for the agent-module resolver and the checkers that use it.

The regressions these lock in, both from a gpt-6.1-sol run whose
projects were correct:

  * datafabric-sdk-tool: the `@tool` wrapping `sdk.entities` lived in
    `order_tools.py`, imported by `main.py`. The checker read only
    `main.py` and reported no tool.
  * langgraph-classifier: the schemas named the fields `ticket` /
    `category`. The checker searched the JSON for the substring `text`,
    which the prompt never asks for.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.project_sources import agent_modules, find_entry_module  # noqa: E402

SHARED = Path(__file__).resolve().parent
BINDINGS = json.dumps({"version": "2.0", "resources": []})


def write(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def names(root: Path, modules: list[Path]) -> list[str]:
    return [m.relative_to(root.resolve()).as_posix() for m in modules]


def run_checker(name: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SHARED / name)], cwd=cwd, capture_output=True, text=True
    )


# ── project_sources ────────────────────────────────────────────────


def test_entry_module_comes_from_langgraph_json(tmp_path: Path) -> None:
    write(tmp_path, {
        "langgraph.json": json.dumps({"graphs": {"agent": "./src/agent/graph.py:graph"}}),
        "main.py": "",
        "src/agent/graph.py": "",
    })
    assert find_entry_module(tmp_path) == (tmp_path / "src/agent/graph.py").resolve()


def test_entry_module_falls_back_to_main_py(tmp_path: Path) -> None:
    write(tmp_path, {"main.py": ""})
    assert find_entry_module(tmp_path) == (tmp_path / "main.py").resolve()


def test_closure_follows_absolute_relative_and_package_imports(tmp_path: Path) -> None:
    write(tmp_path, {
        "main.py": "from order_tools import find\nimport tools.db\n",
        "order_tools.py": "from tools import util\n",
        "tools/__init__.py": "",
        "tools/db.py": "from .shared import X\n",
        "tools/shared.py": "",
        "tools/util.py": "",
    })
    got = names(tmp_path, agent_modules(tmp_path, tmp_path / "main.py"))
    assert got[0] == "main.py"
    assert set(got) == {
        "main.py", "order_tools.py", "tools/__init__.py", "tools/db.py",
        "tools/shared.py", "tools/util.py",
    }


def test_closure_skips_scripts_setup_venv_and_tests(tmp_path: Path) -> None:
    write(tmp_path, {
        "main.py": "import helpers\n",
        "helpers.py": "",
        "verify_local.py": "from uipath.platform import UiPath\nsdk = UiPath()\n",
        "_setup/seed.py": "",
        ".venv/lib/helpers_extra.py": "",
        "tests/test_main.py": "import main\n",
    })
    got = names(tmp_path, agent_modules(tmp_path, tmp_path / "main.py"))
    assert got == ["main.py", "helpers.py"]


# ── check_datafabric_sdk_tool ──────────────────────────────────────

DF_MAIN = """\
from langgraph.graph import StateGraph
from order_tools import get_open_orders

graph = StateGraph(dict).compile()
"""

DF_TOOLS = """\
from langchain_core.tools import tool
from uipath.platform import UiPath

ENTITY_KEY = "CodedOrder"


@tool
async def get_open_orders(customer_name: str) -> list:
    sdk = UiPath()
    return await sdk.entities.retrieve_records_async(
        entity_key=ENTITY_KEY, filter_group={"customer": customer_name}
    )
"""


def datafabric_project(root: Path, tools: str = DF_TOOLS) -> None:
    write(root, {
        "pyproject.toml": "[project]\nname = 'order-lookup'\n",
        "langgraph.json": json.dumps({"graphs": {"agent": "./main.py:graph"}}),
        "bindings.json": BINDINGS,
        "main.py": DF_MAIN,
        "order_tools.py": tools,
    })


def test_datafabric_tool_in_helper_module_passes(tmp_path: Path) -> None:
    datafabric_project(tmp_path)
    proc = run_checker("check_datafabric_sdk_tool.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "main.py, order_tools.py" in proc.stdout


def test_datafabric_module_level_client_in_helper_fails(tmp_path: Path) -> None:
    datafabric_project(tmp_path, DF_TOOLS.replace('ENTITY_KEY = "CodedOrder"', 'sdk = UiPath()\nENTITY_KEY = "CodedOrder"'))
    proc = run_checker("check_datafabric_sdk_tool.py", tmp_path)
    assert proc.returncode != 0
    assert "order_tools.py" in proc.stderr and "module-level call to UiPath()" in proc.stderr


def test_datafabric_unimported_script_does_not_count(tmp_path: Path) -> None:
    datafabric_project(tmp_path)
    (tmp_path / "main.py").write_text("from langgraph.graph import StateGraph\ngraph = StateGraph(dict).compile()\n")
    proc = run_checker("check_datafabric_sdk_tool.py", tmp_path)
    assert proc.returncode != 0
    assert "must import UiPath" in proc.stderr


# ── check_langgraph_classifier ─────────────────────────────────────

CLASSIFIER_MAIN = """\
from typing import Literal
from langgraph.graph import StateGraph
from pydantic import BaseModel


class GraphInput(BaseModel):
    ticket: str


class GraphOutput(BaseModel):
    category: Literal["billing", "technical", "general"]
    ticket: str


builder = StateGraph(GraphInput, input=GraphInput, output=GraphOutput)
graph = builder.compile()
"""


def classifier_project(root: Path, input_schema: dict, output_schema: dict) -> None:
    write(root, {
        "pyproject.toml": (
            "[project]\nname = 'support-classifier'\n"
            "authors = [{ name = 'A' }]\ndependencies = ['uipath-langchain']\n"
        ),
        "langgraph.json": json.dumps({"graphs": {"agent": "./main.py:graph"}}),
        "bindings.json": BINDINGS,
        "main.py": CLASSIFIER_MAIN,
        "entry-points.json": json.dumps({
            "entryPoints": [{"input": input_schema, "output": output_schema}]
        }),
    })


def obj(props: dict, **extra) -> dict:
    return {"type": "object", "properties": props, **extra}


TICKET_IN = obj({"ticket": {"type": "string"}})
ENUM = {"type": "string", "enum": ["billing", "technical", "general"]}


def test_classifier_accepts_ticket_and_category_names(tmp_path: Path) -> None:
    classifier_project(tmp_path, TICKET_IN, obj({"category": ENUM, "ticket": {"type": "string"}}))
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_classifier_accepts_enum_behind_ref(tmp_path: Path) -> None:
    out = obj(
        {"bucket": {"$ref": "#/$defs/Bucket"}, "original_text": {"type": "string"}},
        **{"$defs": {"Bucket": ENUM}},
    )
    classifier_project(tmp_path, obj({"text": {"type": "string"}}), out)
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_classifier_accepts_plain_string_category(tmp_path: Path) -> None:
    out = obj({"category": {"type": "string"}, "ticket": {"type": "string"}})
    classifier_project(tmp_path, TICKET_IN, out)
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_classifier_rejects_enum_missing_a_bucket(tmp_path: Path) -> None:
    bad = {"type": "string", "enum": ["billing", "technical", "other"]}
    classifier_project(tmp_path, TICKET_IN, obj({"category": bad, "ticket": {"type": "string"}}))
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode != 0
    assert "missing bucket(s) ['general']" in proc.stderr


def test_classifier_rejects_output_without_ticket_text(tmp_path: Path) -> None:
    classifier_project(tmp_path, TICKET_IN, obj({"category": ENUM}))
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode != 0
    assert "original ticket text" in proc.stderr


def test_classifier_rejects_stale_schema(tmp_path: Path) -> None:
    classifier_project(tmp_path, obj({}), obj({}))
    proc = run_checker("check_langgraph_classifier.py", tmp_path)
    assert proc.returncode != 0
    assert "no string property" in proc.stderr
