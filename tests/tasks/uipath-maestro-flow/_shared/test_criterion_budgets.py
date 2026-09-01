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
- A loop whose iteration count is STATIC (``for raw, label in CASES``, with
  ``CASES`` a module-level literal) is multiplied out. Helper calls are costed
  inline at the call site, so a ``verify_case(case)`` inside that loop is
  multiplied with it rather than counted once.
- A loop whose count only exists at runtime (``seed.json``) is NOT quietly
  priced at one pass. The criterion must be sized by hand and marked
  ``# budget-guard: manual`` on its ``timeout:`` line, which records that a
  human did the arithmetic. The one-pass floor still applies on top.
  "Cannot compute" must never read as "fine": that is how
  billing_invoice_lookup sat 555s short while this guard was green.
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
# A criterion whose check loops over runtime seeds cannot be priced statically.
# The author sizes it and signs off with this marker; the floor still applies.
_MANUAL_MARKER = re.compile(r"#\s*budget-guard:\s*manual")


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


def _module_lengths(tree: ast.Module) -> dict[str, int]:
    """Module-level names bound to a literal list or tuple, and their lengths.
    This is what makes ``for raw, label in CASES`` a countable loop."""
    lengths = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lengths[target.id] = len(node.value.elts)
    return lengths


_TRANSPARENT_ITERATORS = ("enumerate", "list", "reversed", "sorted", "tuple")


def _iterations(loop: ast.For, lengths: dict[str, int]) -> int | None:
    """How many times ``loop`` runs, or None when that is not static.

    A loop reading its cases from ``seed.json`` is unknowable here, and is
    reported rather than assumed to run once — see
    :func:`_unsized_loops`."""
    target = loop.iter
    if (
        isinstance(target, ast.Call)
        and isinstance(target.func, ast.Name)
        and target.func.id in _TRANSPARENT_ITERATORS
        and target.args
    ):
        target = target.args[0]
    if isinstance(target, (ast.List, ast.Tuple)):
        return len(target.elts)
    if isinstance(target, ast.Name):
        return lengths.get(target.id)
    return None


def _cost(
    node: ast.AST,
    lengths: dict[str, int],
    defs: dict[str, ast.FunctionDef],
    seen: frozenset = frozenset(),
) -> int:
    """What one execution of ``node`` can spend in ``run_debug``.

    Straight-line calls ADD UP: ``check_decision_flow.py`` runs two in one
    ``main()`` and the criterion has to fund both. Mutually exclusive branches
    (``if`` / ``match`` / ``try``) take the most expensive arm instead, so an
    ``if/elif`` dispatch over cases (``check_wiki_pageviews_flow.py``) is
    charged for the one branch that runs, not all of them. A countable loop
    multiplies its body; an uncountable one counts once and is reported by
    :func:`_unsized_loops`.

    A call to a module-level function is costed INLINE, at the call site, so a
    helper invoked once per seed (``verify_case`` in the escalation checks) is
    multiplied with the loop around it rather than counted once. ``seen`` breaks
    recursion."""
    if _is_run_debug(node):
        return _budget_of_call(node) or 0
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in defs
        and node.func.id not in seen
    ):
        inner = _cost(defs[node.func.id], lengths, defs, seen | {node.func.id})
        args = node.args + [kw.value for kw in node.keywords]
        return inner + sum(_cost(a, lengths, defs, seen) for a in args)
    if isinstance(node, ast.If):
        return _cost(node.test, lengths, defs, seen) + max(
            _body(node.body, lengths, defs, seen),
            _body(node.orelse, lengths, defs, seen),
        )
    if isinstance(node, ast.IfExp):
        return _cost(node.test, lengths, defs, seen) + max(
            _cost(node.body, lengths, defs, seen),
            _cost(node.orelse, lengths, defs, seen),
        )
    if isinstance(node, ast.Match):
        return _cost(node.subject, lengths, defs, seen) + max(
            [0] + [_body(c.body, lengths, defs, seen) for c in node.cases]
        )
    if isinstance(node, ast.Try):
        return (
            _body(node.body, lengths, defs, seen)
            + _body(node.orelse, lengths, defs, seen)
            + max([0] + [_body(h.body, lengths, defs, seen) for h in node.handlers])
            + _body(node.finalbody, lengths, defs, seen)
        )
    if isinstance(node, (ast.For, ast.While)):
        runs = _iterations(node, lengths) if isinstance(node, ast.For) else None
        return (
            _cost(node.iter, lengths, defs, seen)
            if isinstance(node, ast.For)
            else _cost(node.test, lengths, defs, seen)
        ) + _body(node.body, lengths, defs, seen) * (1 if runs is None else runs) + _body(
            node.orelse, lengths, defs, seen
        )
    return sum(_cost(c, lengths, defs, seen) for c in ast.iter_child_nodes(node))


def _body(stmts: list, lengths, defs, seen=frozenset()) -> int:
    return sum(_cost(s, lengths, defs, seen) for s in stmts)


def _entry(tree: ast.Module, subcommand: str | None, path: str) -> ast.FunctionDef:
    """The function a criterion executes.

    A subcommand that names a function scopes to it. One that does not is NOT
    silently skipped — dispatch is often an ``if/elif`` on ``sys.argv`` inside
    ``main()`` — so it falls back to ``main`` and lets :func:`_cost` pick the
    branch. A module with neither fails loudly rather than being charged whole,
    which would double-count every helper."""
    defs = _defs(tree)
    entry = (defs.get(subcommand) if subcommand else None) or defs.get("main")
    if entry is None:
        pytest.fail(
            f"{path}: calls run_debug but defines neither main() nor "
            f"{subcommand!r}, so its criterion cannot be priced"
        )
    return entry


def _defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _unsized_loops(path: str, subcommand: str | None) -> list[int]:
    """Line numbers of loops that run a debug an unknown number of times.

    A loop counts if its body costs anything, whether it calls ``run_debug``
    directly or through a helper. These are the criteria a human has to size,
    because the case list only exists at runtime (``seed.json``). The guard
    refuses to guess."""
    tree = ast.parse(open(path).read())
    lengths, defs = _module_lengths(tree), _defs(tree)
    lines = []
    for node in ast.walk(_entry(tree, subcommand, path)):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        if not _body(node.body, lengths, defs):
            continue
        if isinstance(node, ast.While) or _iterations(node, lengths) is None:
            lines.append(node.lineno)
    return sorted(set(lines))


def _budget_of_script(path: str, subcommand: str | None) -> int | None:
    """Worst-case budget for one execution of ``path``, or None when the module
    runs no debug at all."""
    tree = ast.parse(open(path).read())
    if not _calls_in(tree):
        return None
    if any(_budget_of_call(c) is None for c in _calls_in(tree)):
        pytest.fail(f"{path}: run_debug called with a non-literal timeout/budget")
    lengths, defs = _module_lengths(tree), _defs(tree)
    entry = _entry(tree, subcommand, path)
    # Seed `seen` with the entry so a self-call is not charged a second level.
    return _cost(entry, lengths, defs, frozenset({entry.name})) or None


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
                    bool(_MANUAL_MARKER.search(block)),
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
    "yaml_path,script,subcommand,criterion,manual",
    _CASES,
    ids=[f"{y}:{s or '-'}" for y, _p, s, _t, _m in _CASES],
)
def test_criterion_clears_the_debug_budget(
    yaml_path, script, subcommand, criterion, manual
):
    budget = _budget_of_script(script, subcommand)
    if budget is None:
        return  # static-only criterion, nothing to fund
    where = f"{os.path.basename(script)}{f' {subcommand}' if subcommand else ''}"
    assert criterion is not None, f"{yaml_path}: run_command has no timeout:"

    # An uncountable loop is NOT quietly priced at one iteration. Either the
    # author sizes the criterion and says so, or this fails.
    unsized = _unsized_loops(script, subcommand)
    if unsized and not manual:
        pytest.fail(
            f"{yaml_path}: {where} runs a debug inside a loop whose iteration "
            f"count is not static (line{'s' if len(unsized) > 1 else ''} "
            f"{', '.join(map(str, unsized))}), so this guard can only price one "
            f"pass ({budget}s). Size the criterion for the real case count, then "
            "mark it `# budget-guard: manual` on the timeout line to record that "
            "a human did the arithmetic."
        )

    required = budget + flow_check.CRITERION_MARGIN_SECONDS
    assert criterion >= required, (
        f"{yaml_path} grants {criterion}s to {where}, which can spend {budget}s "
        f"in run_debug. Raise the criterion to >= {required}s, or lower the "
        "check's timeout / pass retries=1."
    )


# ── cost model ──────────────────────────────────────────────────────────────
#
# The guard's own regressions. Each of these shapes shipped a wrong number at
# some point in this PR's review, so they are locked with a synthetic module
# rather than by pointing at a task that could be edited out from under them.


def _price(source: str, subcommand: str | None = None, tmp=None) -> int | None:
    path = os.path.join(tmp, "check_x.py")
    open(path, "w").write(source)
    return _budget_of_script(path, subcommand)


_ONE = "run_debug(timeout=240)"  # debug_budget(240) == 485


def test_straight_line_calls_are_summed(tmp_path):
    src = f"def main():\n    {_ONE}\n    {_ONE}\n"
    assert _price(src, tmp=str(tmp_path)) == 970


def test_exclusive_branches_take_the_worse_arm(tmp_path):
    src = f"def main():\n    if x:\n        {_ONE}\n    else:\n        {_ONE}\n"
    assert _price(src, tmp=str(tmp_path)) == 485


def test_static_loop_multiplies(tmp_path):
    src = f"CASES = [1, 2, 3]\n\n\ndef main():\n    for c in CASES:\n        {_ONE}\n"
    assert _price(src, tmp=str(tmp_path)) == 1455


def test_static_loop_sees_through_enumerate(tmp_path):
    src = f"CASES = [1, 2]\n\n\ndef main():\n    for i, c in enumerate(CASES):\n        {_ONE}\n"
    assert _price(src, tmp=str(tmp_path)) == 970


def test_helper_in_a_loop_is_multiplied_not_counted_once(tmp_path):
    """The escalation shape: the loop calls a helper, the helper runs the debug.
    Costing helpers separately priced this at one pass."""
    src = (
        f"CASES = [1, 2, 3]\n\n\ndef verify(c):\n    {_ONE}\n\n\n"
        "def main():\n    for c in CASES:\n        verify(c)\n"
    )
    assert _price(src, tmp=str(tmp_path)) == 1455


def test_runtime_loop_is_reported_not_guessed(tmp_path):
    """A seed-driven loop must surface for manual sizing, including when the
    debug is one helper call away."""
    src = (
        f"def verify(c):\n    {_ONE}\n\n\n"
        "def main():\n    for c in load():\n        verify(c)\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [6]
    assert _budget_of_script(path, None) == 485  # the floor, not the truth


def test_recursion_does_not_hang(tmp_path):
    src = f"def main():\n    {_ONE}\n    main()\n"
    assert _price(src, tmp=str(tmp_path)) == 485


def test_module_without_an_entry_point_fails_loudly(tmp_path):
    """Charging the module whole would double-count every helper."""
    src = f"def helper():\n    {_ONE}\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    with pytest.raises(BaseException, match="neither main"):
        _budget_of_script(path, None)
