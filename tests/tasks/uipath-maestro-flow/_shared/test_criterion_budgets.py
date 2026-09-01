"""Every debug criterion must grant more time than its check can spend.

`run_debug` bounds itself with a deadline, so it can no longer overrun. What it
cannot do is notice that the task YAML granted less than the deadline it needs:
the criterion `timeout:` would fire first and the grader would SIGKILL the check
mid-attempt, discarding the payload, the instanceId, and the CLI's own envelope.
That is how skill-flow-api-workflow scored 0 on a gating criterion in 2026-09.

So the relation is enforced here instead of eyeballed per task:

    criterion timeout >= debug_budget(...) + _CRITERION_MARGIN_SECONDS

Scope and limits:

- The budget is read STATICALLY off each ``run_debug(...)`` call, so only
  literal keyword arguments are understood. A call whose ``timeout`` is a
  variable is reported, not silently skipped.
- A check that dispatches on ``sys.argv`` gets its subcommand resolved through
  the AST, so a static-only criterion (no ``run_debug`` on that path) is not
  charged for a debug it never runs.
- A check that LOOPS over seeds pays the budget once per iteration. The loop
  count is not modelled, so this asserts a floor, not the true cost. Seeded
  checks still need their criterion sized by hand — they just cannot fall below
  one call's worth.
"""

from __future__ import annotations

import ast
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flow_check  # noqa: E402

_SUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUN_COMMAND_SPLIT = re.compile(r"\n\s*-\s+type:\s*run_command")
_COMMAND = re.compile(r'command:\s*"?([^"\n]+)')
_TIMEOUT = re.compile(r"timeout:\s*(\d+)")
_TASK_DIR_SCRIPT = re.compile(r"\$TASK_DIR/(\S+\.py)")


def _literal(node: ast.AST):
    """The Python value of a literal AST node, or None when it is not one."""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def _budget_of_call(call: ast.Call) -> int | None:
    """`debug_budget` for one `run_debug(...)` call, or None if an argument that
    drives it is not a literal (a variable timeout cannot be checked here)."""
    kwargs = {kw.arg: _literal(kw.value) for kw in call.keywords if kw.arg}
    if "budget" in kwargs:
        return kwargs["budget"] if isinstance(kwargs["budget"], int) else None
    passed = {k: kwargs[k] for k in ("timeout", "retries", "backoff_seconds") if k in kwargs}
    if any(v is None for v in passed.values()):
        return None
    return flow_check.debug_budget(**passed)


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "run_debug"
    ]


def _budget_of_script(path: str, subcommand: str | None) -> int | None:
    """Worst-case budget for one execution of ``path``.

    With a ``subcommand``, only that function's body counts (plus anything it
    calls in the same module); without one, the whole module counts. Returns
    None when the path runs no debug at all."""
    tree = ast.parse(open(path).read())
    scope: ast.AST = tree
    if subcommand:
        named = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == subcommand
        ]
        if not named:
            return None
        scope = named[0]
        # A subcommand that only delegates still pays for what it delegates to.
        helpers = {
            n.func.id
            for n in ast.walk(scope)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        bodies = [scope] + [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name in helpers
        ]
        calls = [c for b in bodies for c in _calls_in(b)]
    else:
        calls = _calls_in(scope)
    if not calls:
        return None
    budgets = [_budget_of_call(c) for c in calls]
    if any(b is None for b in budgets):
        pytest.fail(f"{path}: run_debug called with a non-literal timeout/budget")
    return max(budgets)


def _criteria():
    """(yaml, script, subcommand, criterion timeout) for every run_command
    criterion in the suite that points at a $TASK_DIR check script."""
    for root, _dirs, files in os.walk(_SUITE_ROOT):
        for name in files:
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(root, name)
            text = open(path).read()
            for block in _RUN_COMMAND_SPLIT.split(text)[1:]:
                command = _COMMAND.search(block)
                timeout = _TIMEOUT.search(block)
                if not command:
                    continue
                script = _TASK_DIR_SCRIPT.search(command.group(1))
                if not script:
                    continue
                resolved = os.path.join(root, script.group(1))
                if not os.path.exists(resolved):
                    continue
                parts = command.group(1).split()
                sub = parts[-1] if parts[-1].isidentifier() else None
                yield (
                    os.path.relpath(path, _SUITE_ROOT),
                    resolved,
                    sub,
                    int(timeout.group(1)) if timeout else None,
                )


_CASES = sorted(_criteria(), key=lambda c: (c[0], c[2] or ""))


def test_the_suite_was_actually_discovered():
    """A broken walk would make every assertion below vacuously pass."""
    assert len(_CASES) > 40


@pytest.mark.parametrize(
    "yaml_path,script,subcommand,criterion",
    _CASES,
    ids=[f"{y}:{s or '-'}" for y, _p, s, _t in _CASES],
)
def test_criterion_clears_the_debug_budget(yaml_path, script, subcommand, criterion):
    budget = _budget_of_script(script, subcommand)
    if budget is None:
        return  # static-only criterion, nothing to fund
    required = budget + flow_check._CRITERION_MARGIN_SECONDS
    assert criterion is not None, f"{yaml_path}: run_command has no timeout:"
    assert criterion >= required, (
        f"{yaml_path} grants {criterion}s to {os.path.basename(script)}"
        f"{f' {subcommand}' if subcommand else ''}, which can spend {budget}s in "
        f"run_debug. Raise the criterion to >= {required}s, or lower the check's "
        "timeout / pass retries=1."
    )
