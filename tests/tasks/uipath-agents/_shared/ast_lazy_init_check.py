"""AST scan for the lazy-LLM-init invariant.

`references/coded/quickstart.md` Critical Rule C4:

  > Always instantiate `UiPath()` inside functions/nodes, never at
  > module level.
  > NEVER instantiate `UiPathAzureChatOpenAI`, `UiPathChat`,
  > `UiPathChatOpenAI`, or any LLM client at module level — `uip
  > codedagent init` imports the file and module-level LLM clients
  > will fail because auth hasn't happened yet.

This module finds module-level *call expressions* that look like LLM
client construction (e.g. `llm = UiPathAzureChatOpenAI(...)` at column
zero). Use it from check scripts to verify positive tests obey the rule
and from anti-pattern tests to verify the agent refactored a known
violation away.

The check is conservative — it flags by class name only and does not
attempt to follow imports. False negatives are possible if the agent
aliases a class to a non-LLM-shaped name; false positives are rare in
practice because `UiPath*Chat*` is a UiPath-specific convention.

Usage:

    from _shared.ast_lazy_init_check import find_module_level_llm_clients

    violations = find_module_level_llm_clients(Path("main.py"))
    if violations:
        sys.exit("FAIL: " + ", ".join(violations))
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

DEFAULT_LLM_CLASS_NAMES = frozenset({
    "UiPath",
    "UiPathAzureChatOpenAI",
    "UiPathChat",
    "UiPathChatOpenAI",
    "UiPathOpenAIEmbeddings",
    "UiPathAzureOpenAIEmbeddings",
})


def _called_class_name(node: ast.Call) -> str | None:
    """Return the class name being called, or None if it isn't a simple
    Name/Attribute callable.

    Examples:
      `UiPath()` -> "UiPath"
      `uipath.platform.UiPath()` -> "UiPath" (last attribute segment)
      `factory()` -> "factory" (will be filtered out by class-name set)
    """
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def find_module_level_llm_clients(
    path: Path,
    *,
    class_names: frozenset[str] = DEFAULT_LLM_CLASS_NAMES,
) -> list[str]:
    """Return a list of human-readable violation descriptions.

    A violation is any module-level *statement* (i.e. directly inside
    `Module.body`, not nested inside a function/class) whose value is a
    Call whose callable resolves to one of `class_names`.

    Returns an empty list when the file obeys the lazy-init rule.
    """
    if not path.is_file():
        return [f"{path} not found"]
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as e:
        return [f"{path} is not valid Python: {e}"]

    violations: list[str] = []
    for stmt in tree.body:
        # Walk only the *direct* expressions in this statement — calls
        # nested inside a function body are fine. Targets that count as
        # "module-level instantiation":
        #   - `llm = UiPathChat()`              (Assign)
        #   - `llm: UiPathChat = UiPathChat()`  (AnnAssign)
        #   - `UiPathChat()`                    (bare Expr)
        candidate_calls: list[ast.Call] = []
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
            candidate_calls.append(stmt.value)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and isinstance(stmt.value, ast.Call)
        ):
            candidate_calls.append(stmt.value)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            candidate_calls.append(stmt.value)
        for call in candidate_calls:
            name = _called_class_name(call)
            if name in class_names:
                violations.append(
                    f"{path}:{call.lineno} module-level call to {name}() — "
                    f"violates lazy-LLM-init Critical Rule (C4). Move this "
                    f"into a function/node body."
                )
    return violations


def assert_no_module_level_llm_clients(
    path: Path,
    *,
    class_names: frozenset[str] = DEFAULT_LLM_CLASS_NAMES,
) -> None:
    """Print OK on pass, exit with FAIL on the first violation.

    Designed for use as the entry of a sidecar check script."""
    violations = find_module_level_llm_clients(path, class_names=class_names)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(f"OK: {path} has no module-level LLM client construction")
