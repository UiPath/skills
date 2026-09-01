"""Every debug criterion must grant more time than its check can spend.

`run_debug` bounds itself with a deadline, so it can no longer overrun. What it
cannot do is notice that the task YAML granted less than the deadline it needs:
the criterion `timeout:` would fire first and the grader would SIGKILL the check
mid-attempt, discarding the payload, the instanceId, and the CLI's own envelope.
That is how skill-flow-api-workflow scored 0 on a gating criterion in 2026-09.

So the relation is enforced here instead of eyeballed per task:

    criterion timeout >= debug_budget(...) + CRITERION_MARGIN_SECONDS

Scope and limits:

- The budget is read STATICALLY off each ``run_debug(...)`` call, so only
  literal keyword arguments are understood. A call whose ``timeout`` is a
  variable is reported, not silently skipped.
- Straight-line calls in one execution ADD UP; mutually exclusive branches take
  the more expensive arm. So ``check_decision_flow.py`` is charged for both of
  its sequential debugs, while ``check_wiki_pageviews_flow.py`` is charged for
  the one ``if/elif`` case the criterion selects, not all of them.
- A check that dispatches on ``sys.argv`` gets its subcommand resolved through
  the AST, so a static-only criterion (no ``run_debug`` on that path) is not
  charged for a debug it never runs. A subcommand that names no function falls
  back to ``main`` rather than being skipped: dispatch is often an ``if/elif``
  chain, not one function per case.
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


def _is_run_debug(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_debug"
    )


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if _is_run_debug(n)]


def _cost(node: ast.AST) -> int:
    """What one execution of ``node`` can spend in ``run_debug``.

    Straight-line calls ADD UP: ``check_decision_flow.py`` runs two in one
    ``main()`` and the criterion has to fund both. Mutually exclusive branches
    take the more expensive arm instead, so an ``if/elif`` dispatch over cases
    (``check_wiki_pageviews_flow.py``) is charged for the one branch that runs,
    not all of them. A loop body counts once, since its iteration count is not
    knowable here — the documented floor."""
    if _is_run_debug(node):
        return _budget_of_call(node) or 0
    if isinstance(node, ast.If):
        return _cost(node.test) + max(_body(node.body), _body(node.orelse))
    if isinstance(node, ast.IfExp):
        return _cost(node.test) + max(_cost(node.body), _cost(node.orelse))
    if isinstance(node, ast.Try):
        return (
            _body(node.body)
            + _body(node.orelse)
            + max([0] + [_body(h.body) for h in node.handlers])
            + _body(node.finalbody)
        )
    return sum(_cost(child) for child in ast.iter_child_nodes(node))


def _body(stmts: list) -> int:
    return sum(_cost(s) for s in stmts)


def _entry(tree: ast.Module, subcommand: str | None) -> ast.AST | None:
    """The function a criterion actually executes.

    A subcommand that names a function scopes to it. One that does not is NOT
    silently skipped — dispatch may be an ``if/elif`` on ``sys.argv`` inside
    ``main()`` — so it falls back to ``main`` and lets :func:`_cost` pick the
    branch. Modules with neither are charged whole."""
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if subcommand and subcommand in defs:
        return defs[subcommand]
    return defs.get("main")


def _budget_of_script(path: str, subcommand: str | None) -> int | None:
    """Worst-case budget for one execution of ``path``, or None when the module
    runs no debug at all."""
    tree = ast.parse(open(path).read())
    if any(_budget_of_call(c) is None for c in _calls_in(tree)):
        pytest.fail(f"{path}: run_debug called with a non-literal timeout/budget")
    entry = _entry(tree, subcommand) or tree
    cost = _cost(entry)
    # A delegating entry point still pays for the helpers it calls.
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for name in {
        n.func.id
        for n in ast.walk(entry)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }:
        if name in defs and defs[name] is not entry:
            cost += _cost(defs[name])
    return cost or None


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
    """A broken walk, or an AST change that stops resolving `run_debug`, would
    make every assertion below vacuously pass. Assert on both: criteria found,
    AND criteria that actually priced a debug."""
    assert len(_CASES) > 40
    priced = [c for c in _CASES if _budget_of_script(c[1], c[2]) is not None]
    assert len(priced) > 40, f"only {len(priced)} criteria resolved a budget"


@pytest.mark.parametrize(
    "yaml_path,script,subcommand,criterion",
    _CASES,
    ids=[f"{y}:{s or '-'}" for y, _p, s, _t in _CASES],
)
def test_criterion_clears_the_debug_budget(yaml_path, script, subcommand, criterion):
    budget = _budget_of_script(script, subcommand)
    if budget is None:
        return  # static-only criterion, nothing to fund
    required = budget + flow_check.CRITERION_MARGIN_SECONDS
    assert criterion is not None, f"{yaml_path}: run_command has no timeout:"
    assert criterion >= required, (
        f"{yaml_path} grants {criterion}s to {os.path.basename(script)}"
        f"{f' {subcommand}' if subcommand else ''}, which can spend {budget}s in "
        f"run_debug. Raise the criterion to >= {required}s, or lower the check's "
        "timeout / pass retries=1."
    )
