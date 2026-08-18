"""Reusable LangGraph project assertions for coded-agent check scripts."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# Keyword names LangGraph accepts for the schemas passed to `StateGraph`.
# The first positional argument is the state schema.
_INPUT_KEYWORDS = ("input", "input_schema")
_OUTPUT_KEYWORDS = ("output", "output_schema")
_IO_KEYWORDS = _INPUT_KEYWORDS + _OUTPUT_KEYWORDS
_SCHEMA_KEYWORDS = _IO_KEYWORDS + ("state_schema",)


def assert_langgraph_config(root: Path, module: Path) -> None:
    """Assert `langgraph.json` points at the exported graph module."""
    path = root / "langgraph.json"
    if not path.is_file():
        sys.exit(f"FAIL: missing LangGraph config at {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: {path} is not valid JSON: {exc}")

    graphs = data.get("graphs")
    if not isinstance(graphs, dict) or not graphs:
        sys.exit("FAIL: langgraph.json must contain a non-empty `graphs` object")

    expected_targets = {f"./{module.name}:graph", f"{module.name}:graph"}
    if not any(target in expected_targets for target in graphs.values()):
        sys.exit(
            "FAIL: langgraph.json must map a graph entry to the exported graph "
            f"({', '.join(sorted(expected_targets))}); got {graphs!r}"
        )
    print(f"OK: langgraph.json registers {module.name}:graph")


def _base_name(node: ast.expr) -> str | None:
    """Last name segment of a class base (`pydantic.BaseModel` -> `BaseModel`)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _pydantic_models(tree: ast.Module) -> set[str]:
    """Names of classes in this module that subclass `BaseModel`."""
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(_base_name(base) == "BaseModel" for base in node.bases)
    }


def _defined_classes(tree: ast.Module) -> set[str]:
    """Names of every class defined in this module."""
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _state_graph_call(tree: ast.Module) -> ast.Call | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _base_name(node.func) == "StateGraph":
            return node
    return None


def _exports_compiled_graph(tree: ast.Module) -> bool:
    """True when the module assigns a top-level `graph` from `.compile(...)`."""
    for stmt in tree.body:
        targets: list[ast.expr] = []
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
        elif isinstance(stmt, ast.AnnAssign):
            targets = [stmt.target]
        if not any(isinstance(t, ast.Name) and t.id == "graph" for t in targets):
            continue
        value = stmt.value
        if isinstance(value, ast.Call) and _base_name(value.func) == "compile":
            return True
        # `graph = builder` / `graph = some_factory()` still exports something
        # importable; only a bare `graph = None` is meaningless.
        if value is not None and not (
            isinstance(value, ast.Constant) and value.value is None
        ):
            return True
    return False


def assert_graph_module_shape(path: Path) -> None:
    """Assert the module has LangGraph agent shape, ignoring class names.

    Class names are not an invariant — `references/coded/frameworks/
    agent-patterns.md` explicitly allows `Input`/`Output` or
    `GraphInput`/`GraphOutput` or anything else. What matters:

      1. A `StateGraph(...)` is constructed.
      2. Its positional state schema is a class defined in the module
         (`TypedDict` state is idiomatic LangGraph, so `BaseModel` is
         not required there).
      3. Its `input`/`input_schema`/`output`/`output_schema` keywords
         resolve to Pydantic `BaseModel` subclasses defined in the
         module — those two are what `uip codedagent init` turns into
         the entrypoint schema.
      4. The output schema differs from the input schema, so the
         agent's input and output shapes are separately typed.
      5. The module exports a top-level `graph`.
    """
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        sys.exit(f"FAIL: {path.name} is not valid Python: {exc}")

    call = _state_graph_call(tree)
    if call is None:
        sys.exit(f"FAIL: {path.name} does not construct a StateGraph")

    models = _pydantic_models(tree)
    classes = _defined_classes(tree)
    schemas: dict[str, str] = {}
    if call.args:
        schemas["state"] = ast.unparse(call.args[0])
    for keyword in call.keywords:
        if keyword.arg in _SCHEMA_KEYWORDS:
            schemas[keyword.arg] = ast.unparse(keyword.value)

    state = schemas.get("state") or schemas.get("state_schema")
    if state is not None and state not in classes:
        sys.exit(
            f"FAIL: {path.name} passes StateGraph state schema `{state}`, which is "
            f"not a class defined in the module (found: {sorted(classes) or 'none'})"
        )

    io_schemas = {k: v for k, v in schemas.items() if k in _IO_KEYWORDS}
    non_models = sorted({v for v in io_schemas.values() if v not in models})
    if non_models:
        sys.exit(
            f"FAIL: {path.name} passes StateGraph input/output schema(s) "
            f"{non_models} that are not Pydantic BaseModel subclasses defined in "
            f"the module (found models: {sorted(models) or 'none'})"
        )

    outputs = {io_schemas[k] for k in _OUTPUT_KEYWORDS if k in io_schemas}
    if not outputs:
        sys.exit(
            f"FAIL: {path.name} declares no output schema — pass "
            f"`output_schema=<PydanticModel>` to StateGraph so the agent's "
            f"output shape is typed for `uip codedagent init`."
        )
    inputs = {io_schemas[k] for k in _INPUT_KEYWORDS if k in io_schemas} or {state}
    if outputs & inputs:
        sys.exit(
            f"FAIL: {path.name} uses the same model for input and output "
            f"({sorted(outputs & inputs)}) — declare distinct input and "
            f"output schemas."
        )

    if not _exports_compiled_graph(tree):
        sys.exit(
            f"FAIL: {path.name} does not export a top-level `graph` — the "
            f"runtime resolves the agent through `<file>:graph`."
        )

    print(
        f"OK: {path.name} declares Pydantic input/output schemas "
        f"({', '.join(f'{k}={v}' for k, v in schemas.items())}) and exports `graph`"
    )
