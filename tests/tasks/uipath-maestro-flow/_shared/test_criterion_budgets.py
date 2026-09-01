"""Every debug criterion must grant more time than its check can spend.

`run_debug` bounds itself with a deadline, so it can no longer overrun. What it
cannot do is notice that the task YAML granted less than the deadline it needs:
the criterion `timeout:` would fire first and the grader would SIGKILL the check
mid-attempt, discarding the payload, the instanceId, and the CLI's own envelope.
That is how skill-flow-api-workflow scored 0 on a gating criterion in 2026-09.

This is NOT a new class of failure. It was root-caused for skill-flow-subflow on
2026-05-29 (run 2026-05-29_04-04-25) and guarded there, for that one task, by
`single_node/subflow/test_check_subflow_flow.py`. The RCA's own words, worth
keeping because the doc it lived in is no longer in the tree:

    The criterion budget (120s) was *below* `flow_check.run_debug`'s own
    `subprocess.run` timeout (240s default). That inversion means the checker
    can NEVER surface the underlying CLI error: the sandbox kills the whole
    process first, yielding exit `-1` with empty output ("Command ... timed out
    after N seconds") instead of the informative exit `1` + traceback that the
    inner `subprocess.TimeoutExpired` would produce.

Four months later api_workflow hit the same wall, because the guard covered one
task out of forty-four. That per-task test is deleted here and this module owns
the rule for the whole suite: one source of truth, checked for every criterion
rather than the one that already burned someone.

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
  priced at one pass. The criterion must declare the count on its ``timeout:``
  line as ``# budget-guard: manual xN``, and the guard then checks THAT
  arithmetic — a bare ``manual`` is refused, a stale one is refused, and where
  the task ships a ``seed.py`` that states its cases literally, ``N`` is
  cross-checked against it — and a count with nothing to corroborate it is
  refused outright. An annotation nobody verifies is just a comment.
- Pricing and "did we have to guess?" come out of ONE traversal (:class:`_Price`).
  When they walked separately they disagreed about scope, and a loop inside a
  helper was priced at one pass while going unreported.

"Cannot compute" must never read as "fine". Every round of review on this guard
found a live under-budgeted criterion hiding behind exactly that reflex:
wiki_pageviews behind an unresolvable subcommand, decision behind ``max()``,
billing_invoice_lookup behind an uncounted loop, customer_escalation_triage
behind an unverified annotation.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from typing import NamedTuple

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flow_check  # noqa: E402

_SUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUN_COMMAND_SPLIT = re.compile(r"\n\s*-\s+type:\s*run_command")
_COMMAND = re.compile(r'command:\s*"?([^"\n]+)')
_TIMEOUT = re.compile(r"timeout:\s*(\d+)")
_TASK_DIR_SCRIPT = re.compile(r"\$TASK_DIR/(\S+\.py)")
# Anchored so it cannot match `turn_timeout:` / `task_timeout:`.
_ANY_COMMAND_TIMEOUT = re.compile(r"^\s*timeout:\s*(\d+)", re.M)
_TASK_TIMEOUT = re.compile(r"^\s*task_timeout:\s*(\d+)", re.M)
# Everything from `success_criteria:` up to the next top-level key. Only these
# timeouts run inside the watchdog.
_SUCCESS_CRITERIA = re.compile(
    r"^success_criteria:\n(.*?)(?=^\S|\Z)", re.M | re.S
)
# A criterion whose check loops over runtime seeds cannot be priced statically.
# The author supplies the pass count and the guard checks THAT arithmetic — a
# bare `manual` with no count is refused, because an unverified annotation is
# just a comment.
_MANUAL_MARKER = re.compile(r"#\s*budget-guard:\s*manual(?:\s*x\s*(\d+))?")


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
    This is what makes ``for raw, label in CASES`` a countable loop.

    A name any function rebinds is dropped: the module value would be shadowed
    at the point the loop reads it, and a wrong multiplier is worse than none."""
    lengths = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lengths[target.id] = len(node.value.elts)
    for func in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(func):
            targets = node.targets if isinstance(node, ast.Assign) else []
            for target in targets:
                if isinstance(target, ast.Name):
                    lengths.pop(target.id, None)
    return lengths


_TRANSPARENT_ITERATORS = ("enumerate", "list", "reversed", "sorted", "tuple")


def _iterations(loop: ast.AST, lengths: dict[str, int]) -> int | None:
    """How many times ``loop`` runs, or None when that is not static.

    A ``while``, or a ``for`` over cases read from ``seed.json``, is unknowable
    here. It is reported rather than assumed to run once."""
    if not isinstance(loop, ast.For):
        return None
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


class _Price(NamedTuple):
    """Seconds one execution can spend, and the loops we had to guess at.

    Both come out of ONE traversal on purpose. When the cost model and the
    "did we guess?" detector walked separately they disagreed about scope, and
    a loop inside a helper was priced at one pass while going unreported."""

    seconds: int
    unsized: tuple[int, ...]


_FREE = _Price(0, ())


def _merge(*prices: _Price) -> _Price:
    """Sequential composition: seconds add, guesses accumulate."""
    return _Price(
        sum(p.seconds for p in prices),
        tuple(sorted({line for p in prices for line in p.unsized})),
    )


def _worst(prices: list[_Price]) -> _Price:
    """Exclusive composition: the priciest arm wins, but every arm's guesses
    are reported — any of them may be the one that runs."""
    if not prices:
        return _FREE
    return _Price(
        max(p.seconds for p in prices),
        tuple(sorted({line for p in prices for line in p.unsized})),
    )


def _cost(
    node: ast.AST,
    lengths: dict[str, int],
    defs: dict[str, ast.FunctionDef],
    seen: frozenset = frozenset(),
    manual: int | None = None,
) -> _Price:
    """What one execution of ``node`` can spend in ``run_debug``.

    Straight-line calls ADD UP: ``check_decision_flow.py`` runs two in one
    ``main()`` and the criterion has to fund both. Mutually exclusive branches
    (``if`` / ``match`` / ``try``) take the most expensive arm instead, so an
    ``if/elif`` dispatch over cases (``check_wiki_pageviews_flow.py``) is
    charged for the one branch that runs, not all of them.

    A call to a module-level function is costed INLINE, at the call site, so a
    helper invoked once per seed (``verify_case`` in the escalation checks) is
    multiplied with the loop around it rather than counted once. ``seen``
    breaks recursion.

    A countable loop multiplies its body. An uncountable one is charged
    ``manual`` passes when the criterion supplies that count, and one pass
    otherwise — in which case its line is reported so the caller can refuse to
    accept the number."""
    if _is_run_debug(node):
        budget = _budget_of_call(node)
        if budget is None:
            # Reachable code only: a dead helper's variable timeout is not this
            # guard's problem.
            pytest.fail(
                f"line {node.lineno}: run_debug called with a non-literal "
                "timeout/budget, so its criterion cannot be priced"
            )
        return _Price(budget, ())
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in defs
        and node.func.id not in seen
    ):
        inner = _cost(defs[node.func.id], lengths, defs, seen | {node.func.id}, manual)
        args = node.args + [kw.value for kw in node.keywords]
        return _merge(inner, *[_cost(a, lengths, defs, seen, manual) for a in args])
    if isinstance(node, ast.If):
        return _merge(
            _cost(node.test, lengths, defs, seen, manual),
            _worst(
                [
                    _body(node.body, lengths, defs, seen, manual),
                    _body(node.orelse, lengths, defs, seen, manual),
                ]
            ),
        )
    if isinstance(node, ast.IfExp):
        return _merge(
            _cost(node.test, lengths, defs, seen, manual),
            _worst(
                [
                    _cost(node.body, lengths, defs, seen, manual),
                    _cost(node.orelse, lengths, defs, seen, manual),
                ]
            ),
        )
    if isinstance(node, ast.Match):
        return _merge(
            _cost(node.subject, lengths, defs, seen, manual),
            _worst([_body(c.body, lengths, defs, seen, manual) for c in node.cases]),
        )
    if isinstance(node, ast.Try):
        return _merge(
            _body(node.body, lengths, defs, seen, manual),
            _body(node.orelse, lengths, defs, seen, manual),
            _worst([_body(h.body, lengths, defs, seen, manual) for h in node.handlers]),
            _body(node.finalbody, lengths, defs, seen, manual),
        )
    if isinstance(node, (ast.For, ast.While)):
        head = node.iter if isinstance(node, ast.For) else node.test
        body = _body(node.body, lengths, defs, seen, manual)
        runs = _iterations(node, lengths)
        guessed = ()
        if runs is None:
            # Only a loop that actually costs something needs sizing.
            guessed = (node.lineno,) if body.seconds else ()
            runs = manual if manual is not None else 1
        return _merge(
            _cost(head, lengths, defs, seen, manual),
            _Price(body.seconds * runs, body.unsized + guessed),
            _body(node.orelse, lengths, defs, seen, manual),
        )
    return _merge(
        *[_cost(c, lengths, defs, seen, manual) for c in ast.iter_child_nodes(node)]
    )


def _body(stmts: list, lengths, defs, seen=frozenset(), manual=None) -> _Price:
    return _merge(*[_cost(s, lengths, defs, seen, manual) for s in stmts])


def _defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


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


def _price_script(
    path: str, subcommand: str | None, manual: int | None = None
) -> _Price | None:
    """Price one execution of ``path``, or None when it runs no debug at all.

    ``manual`` is the pass count the criterion declares for a loop this guard
    cannot count. One count cannot describe two differently-sized loops, so the
    caller refuses that case rather than picking a number: applying N to both
    under-charges whenever the other loop runs more often."""
    tree = ast.parse(open(path).read())
    if not _calls_in(tree):
        return None
    lengths, defs = _module_lengths(tree), _defs(tree)
    entry = _entry(tree, subcommand, path)
    # Seed `seen` with the entry so a self-call is not charged a second level.
    price = _cost(entry, lengths, defs, frozenset({entry.name}), manual)
    return price if price.seconds else None


def _budget_of_script(path: str, subcommand: str | None) -> int | None:
    price = _price_script(path, subcommand)
    return price.seconds if price else None


def _unsized_loops(path: str, subcommand: str | None) -> list[int]:
    price = _price_script(path, subcommand)
    return list(price.unsized) if price else []


_SEED_CASE_NAMES = ("cases", "seed_cases")


def _seed_case_count(script: str) -> int | None:
    """Cases the task's own ``seed.py`` writes, when it states them literally.

    This is what turns the declared ``manual xN`` from an assertion into a
    checked one. Returns None when the generator does not exist, does not name
    its cases, or names them more than once with different lengths — better no
    cross-check than a wrong one."""
    seed = os.path.join(os.path.dirname(script), "seed.py")
    if not os.path.exists(seed):
        return None
    counts = set()
    for node in ast.walk(ast.parse(open(seed).read())):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.lower() in _SEED_CASE_NAMES:
                    counts.add(len(node.value.elts))
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if getattr(key, "value", None) in _SEED_CASE_NAMES and isinstance(
                    value, (ast.List, ast.Tuple)
                ):
                    counts.add(len(value.elts))
    return counts.pop() if len(counts) == 1 else None


_EXPERIMENT_DEFAULTS = os.path.join(
    os.path.dirname(_SUITE_ROOT), "..", "experiments", "default.yaml"
)


def _inherited_task_timeout() -> int:
    """`defaults.run_limits.task_timeout` from the default experiment.

    A task that declares no `task_timeout` does not run uncapped, it runs at
    this value — which is why skipping those tasks silently exempted 58 of
    them. Parsed with a regex, not PyYAML: CI installs only pytest, and a
    module-level `import yaml` would error at collection and take the whole
    maestro-flow suite with it."""
    text = open(os.path.normpath(_EXPERIMENT_DEFAULTS)).read()
    found = _TASK_TIMEOUT.search(text)
    assert found, f"no task_timeout in {_EXPERIMENT_DEFAULTS}"
    return int(found.group(1))


def _task_budgets():
    """(yaml, effective task_timeout, worst-case grading seconds) per task.

    Grading is the success-criteria budget ONLY. `pre_run` and `post_run` are
    outside the watchdog — coder_eval/orchestrator.py calls them at 468 and 579,
    while the `ThreadedWatchdog` wraps only `_evaluation_loop` at 484-499 — so
    charging them here would demand ceilings nothing needs."""
    inherited = _inherited_task_timeout()
    for root, _dirs, files in os.walk(_SUITE_ROOT):
        for name in files:
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(root, name)
            text = open(path).read()
            criteria = _SUCCESS_CRITERIA.search(text)
            if not criteria:
                continue
            declared = _TASK_TIMEOUT.search(text)
            yield (
                os.path.relpath(path, _SUITE_ROOT),
                int(declared.group(1)) if declared else inherited,
                sum(int(m) for m in _ANY_COMMAND_TIMEOUT.findall(criteria.group(1))),
            )


def _criteria():
    """(yaml, script, subcommand, criterion timeout, declared pass count) for
    every run_command criterion in the suite that points at a $TASK_DIR check.

    The timeout and its ``budget-guard`` annotation are read off the SAME line,
    so an annotation cannot drift away from the number it explains."""
    for root, _dirs, files in os.walk(_SUITE_ROOT):
        for name in files:
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(root, name)
            text = open(path).read()
            for block in _RUN_COMMAND_SPLIT.split(text)[1:]:
                command = _COMMAND.search(block)
                if not command:
                    continue
                script = _TASK_DIR_SCRIPT.search(command.group(1))
                if not script:
                    continue
                resolved = os.path.join(root, script.group(1))
                if not os.path.exists(resolved):
                    continue
                timeout_line = next(
                    (ln for ln in block.split("\n") if _TIMEOUT.search(ln)), ""
                )
                found = _TIMEOUT.search(timeout_line)
                marker = _MANUAL_MARKER.search(timeout_line)
                parts = command.group(1).split()
                yield (
                    os.path.relpath(path, _SUITE_ROOT),
                    resolved,
                    parts[-1] if parts[-1].isidentifier() else None,
                    int(found.group(1)) if found else None,
                    # "" marks a marker with no count, distinct from no marker.
                    (marker.group(1) or "") if marker else None,
                )


def _annotation_error(
    price: _Price, declared: str | None, seeded: int | None, where: str
) -> str | None:
    """Why this criterion's `budget-guard` annotation is unacceptable, or None.

    Pure, so every refusal path is unit-testable. The multi-loop and
    uncorroborated-count branches have no live task to exercise them, and an
    untested branch is where each previous round of this guard went wrong."""
    if declared is not None and not price.unsized:
        return (
            f"{where} has no loop this guard needs help counting, so the "
            "`budget-guard: manual` annotation is stale. Remove it."
        )
    if not price.unsized:
        return None
    # One declared count cannot describe two loops of different sizes, and
    # picking one under-charges whenever the other runs more often.
    if len(price.unsized) > 1:
        return (
            f"{where} runs a debug inside {len(price.unsized)} loops this guard "
            f"cannot count (lines {', '.join(map(str, price.unsized))}). A "
            "single `budget-guard: manual xN` cannot describe them. Give the "
            "check one such loop, make the counts static, or extend this guard."
        )
    if declared is None:
        return (
            f"{where} runs a debug inside a loop whose iteration count is not "
            f"static (line {price.unsized[0]}), so this guard can only price "
            f"one pass ({price.seconds}s). Annotate the timeout with "
            "`# budget-guard: manual xN` for the real pass count and the guard "
            "will check the arithmetic."
        )
    if not declared:
        return (
            f"{where} is marked `budget-guard: manual` with no count. Write "
            "`manual xN` so the number can be checked rather than trusted."
        )
    # Every declared count must be checkable against something. Accepting one
    # on trust is the reflex that produced every bug this guard exists to catch.
    if seeded is None:
        return (
            f"{where} declares `manual x{declared}` but nothing corroborates it "
            "— the task has no seed.py stating its cases literally. Add one, "
            "make the loop countable, or extend _seed_case_count to read this "
            "task's generator. An unchecked count is a comment."
        )
    if int(declared) != seeded:
        return (
            f"{where} declares `manual x{declared}` but the task's seed.py "
            f"writes {seeded} cases. Fix whichever is wrong; a declared count "
            "that nobody checks is how this guard drifts."
        )
    return None


_CASES = sorted(_criteria(), key=lambda c: (c[0], c[2] or ""))


def test_the_suite_was_actually_discovered():
    """A broken walk, or an AST change that stops resolving `run_debug`, would
    make every assertion below vacuously pass. Assert on both: criteria found,
    AND criteria that actually priced a debug."""
    assert len(_CASES) > 40
    priced = [c for c in _CASES if _budget_of_script(c[1], c[2]) is not None]
    assert len(priced) > 40, f"only {len(priced)} criteria resolved a budget"


@pytest.mark.parametrize(
    "yaml_path,script,subcommand,criterion,declared",
    _CASES,
    ids=[f"{y}:{s or '-'}" for y, _p, s, _t, _d in _CASES],
)
def test_criterion_clears_the_debug_budget(
    yaml_path, script, subcommand, criterion, declared
):
    price = _price_script(script, subcommand)
    if price is None:
        return  # static-only criterion, nothing to fund
    where = f"{os.path.basename(script)}{f' {subcommand}' if subcommand else ''}"
    assert criterion is not None, f"{yaml_path}: run_command has no timeout:"

    seeded = _seed_case_count(script) if price.unsized else None
    problem = _annotation_error(price, declared, seeded, where)
    if problem:
        pytest.fail(f"{yaml_path}: {problem}")
    if price.unsized:
        price = _price_script(script, subcommand, manual=int(declared))

    required = price.seconds + flow_check.CRITERION_MARGIN_SECONDS
    assert criterion >= required, (
        f"{yaml_path} grants {criterion}s to {where}, which can spend "
        f"{price.seconds}s in run_debug. Raise the criterion to >= {required}s, "
        "or lower the check's timeout / pass retries=1."
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


def test_loop_inside_a_helper_is_reported(tmp_path):
    """The mirror of the escalation shape: the LOOP is in the helper, not the
    entry. The detector once walked only the entry while the cost model walked
    helpers too, so this was priced at one pass and never reported."""
    src = (
        "def sweep():\n    for c in load():\n        run_debug(timeout=240)\n\n\n"
        "def main():\n    sweep()\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [2]
    assert _budget_of_script(path, None) == 485


def test_declared_pass_count_multiplies_the_runtime_loop(tmp_path):
    src = f"def main():\n    for c in load():\n        {_ONE}\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _price_script(path, None).seconds == 485  # floor, one pass
    assert _price_script(path, None, manual=3).seconds == 1455


def test_price_and_report_come_from_one_traversal(tmp_path):
    """`_Price` carries both so the cost model and the detector cannot disagree
    about scope, which is how the helper-loop gap opened."""
    src = (
        f"CASES = [1, 2]\n\n\ndef main():\n    for c in CASES:\n        {_ONE}\n"
        "    for d in load():\n        run_debug(timeout=240)\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    price = _price_script(path, None)
    assert price.seconds == 970 + 485  # static loop x2, runtime loop x1
    assert price.unsized == (7,)


def test_exclusive_branches_report_every_arms_guesses(tmp_path):
    """Only one arm runs, but either might be the one that does, so both arms'
    unsized loops must surface."""
    src = (
        "def main():\n    if x:\n        for c in load():\n"
        f"            {_ONE}\n    else:\n        for d in other():\n"
        f"            {_ONE}\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [3, 6]


def test_locally_rebound_list_is_not_treated_as_static(tmp_path):
    """A module constant a function overwrites is shadowed where the loop reads
    it, so its length must not be used as a multiplier."""
    src = (
        f"CASES = [1, 2, 3]\n\n\ndef main():\n    CASES = load()\n"
        f"    for c in CASES:\n        {_ONE}\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [6]
    assert _budget_of_script(path, None) == 485


def test_dead_helper_with_a_variable_timeout_is_not_our_problem(tmp_path):
    """The non-literal check follows reachable code only."""
    src = f"def unused():\n    run_debug(timeout=n)\n\n\ndef main():\n    {_ONE}\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _budget_of_script(path, None) == 485


def test_reachable_variable_timeout_fails_loudly(tmp_path):
    src = "def main():\n    run_debug(timeout=n)\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    with pytest.raises(BaseException, match="non-literal"):
        _budget_of_script(path, None)


def test_seed_case_count_reads_a_literal_generator(tmp_path):
    open(os.path.join(str(tmp_path), "seed.py"), "w").write(
        'payload = {"cases": [{"a": 1}, {"a": 2}, {"a": 3}]}\n'
    )
    assert _seed_case_count(os.path.join(str(tmp_path), "check_x.py")) == 3


def test_seed_case_count_declines_when_ambiguous(tmp_path):
    """Two different literal case lists: no cross-check beats a wrong one."""
    open(os.path.join(str(tmp_path), "seed.py"), "w").write(
        'a = {"cases": [1, 2]}\nb = {"cases": [1, 2, 3]}\n'
    )
    assert _seed_case_count(os.path.join(str(tmp_path), "check_x.py")) is None


def test_two_uncountable_loops_are_refused_not_guessed(tmp_path):
    """One declared count cannot describe two loops of different sizes.
    Applying N to both under-charges whenever the other runs more often, so the
    criterion test refuses the shape instead of picking a number."""
    src = (
        f"def main():\n    for a in two():\n        {_ONE}\n"
        f"    for b in seven():\n        {_ONE}\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [2, 4]
    # The under-charge this refusal exists to prevent: x2 prices 970, but if the
    # second loop runs 7 times the real cost is 4365.
    assert _price_script(path, None, manual=2).seconds == 485 * 4


# ── annotation policy ───────────────────────────────────────────────────────
#
# Every refusal path, including the two no live task reaches. An untested branch
# is where each earlier round of this guard went wrong.

_ONE_LOOP = _Price(485, (7,))
_TWO_LOOPS = _Price(970, (7, 9))
_NO_LOOP = _Price(485, ())


@pytest.mark.parametrize(
    "price,declared,seeded,expected",
    [
        (_NO_LOOP, None, None, None),                       # ordinary criterion
        (_ONE_LOOP, "2", 2, None),                          # declared and corroborated
        (_NO_LOOP, "3", None, "stale"),                     # marker with nothing to size
        (_TWO_LOOPS, "2", 2, "cannot describe them"),       # one count, two loops
        (_ONE_LOOP, None, None, "not static"),              # unannotated runtime loop
        (_ONE_LOOP, "", None, "with no count"),             # bare `manual`
        (_ONE_LOOP, "2", None, "nothing corroborates it"),  # unverifiable count
        (_ONE_LOOP, "1", 2, "writes 2 cases"),              # understated count
    ],
)
def test_annotation_policy(price, declared, seeded, expected):
    problem = _annotation_error(price, declared, seeded, "check_x.py")
    if expected is None:
        assert problem is None
    else:
        assert problem and expected in problem


# ── task budget ─────────────────────────────────────────────────────────────
#
# The criterion checks above bound each check in isolation. Nothing bounded
# their SUM against the cap enclosing them, and raising 41 of them at once is
# how you find that out. `task_timeout` wraps the agent turns AND the grading in
# one watchdog (coder_eval/orchestrator.py: ThreadedWatchdog around
# `_evaluation_loop`, 484-499); when it fires the agent subprocess is SIGKILLed
# and the whole task is reported TIMEOUT. That loses every criterion, including
# the ones that already passed — strictly less diagnosable than the single
# failed criterion this suite's timeouts exist to produce.
#
# The relation is an IMPOSSIBILITY check, not a sufficiency one:
#
#     task_timeout > worst-case grading
#
# If grading alone can consume the cap, no agent run can fit, whatever it does.
# That is provable from the numbers in the file. Anything stronger needs the
# agent's real wall clock, which is not knowable here — an earlier draft
# demanded `grading + turn_timeout` and was wrong on contact with a second
# experiment: smoke.yaml sets task_timeout == turn_timeout == 900, so every
# smoke task would have been flagged impossible while being perfectly fine.


_TASK_BUDGETS = sorted(_task_budgets())


def test_every_task_with_criteria_was_discovered():
    """Covers tasks that INHERIT their cap, not just ones that declare it.
    Skipping the inheritors silently exempted 58 of them."""
    assert len(_TASK_BUDGETS) > 90
    inherited = [b for b in _TASK_BUDGETS if b[1] == _inherited_task_timeout()]
    assert len(inherited) > 20, "experiment-default inheritance is not being resolved"


@pytest.mark.parametrize(
    "yaml_path,task_timeout,grading",
    _TASK_BUDGETS,
    ids=[y for y, _t, _g in _TASK_BUDGETS],
)
def test_grading_alone_fits_the_task_timeout(yaml_path, task_timeout, grading):
    assert task_timeout > grading, (
        f"{yaml_path}: worst-case grading is {grading}s against a task_timeout "
        f"of {task_timeout}s, so the watchdog can fire before grading finishes "
        "no matter how fast the agent is. It SIGKILLs the run and reports "
        "TIMEOUT, losing every criterion. Raise task_timeout well above "
        f"{grading}s (the agent needs the remainder), or lower the criterion "
        "timeouts."
    )


def test_impossible_task_is_rejected(tmp_path):
    """Grading alone at or above the cap: no agent run fits, whatever it does."""
    yaml = tmp_path / "x.yaml"
    yaml.write_text(
        "run_limits:\n  turn_timeout: 900\n  task_timeout: 600\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 600\n"
    )
    text = yaml.read_text()
    grading = sum(
        int(m)
        for m in _ANY_COMMAND_TIMEOUT.findall(_SUCCESS_CRITERIA.search(text).group(1))
    )
    assert grading == 600
    assert int(_TASK_TIMEOUT.search(text).group(1)) <= grading  # the rejected shape


def test_smoke_shaped_task_is_not_flagged(tmp_path):
    """An earlier draft demanded `grading + turn_timeout`, which smoke.yaml
    (task_timeout == turn_timeout == 900) makes impossible for any task with any
    grading at all. The floor must accept this shape."""
    yaml = tmp_path / "x.yaml"
    yaml.write_text(
        "run_limits:\n  turn_timeout: 900\n  task_timeout: 900\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 210\n"
    )
    text = yaml.read_text()
    grading = sum(
        int(m)
        for m in _ANY_COMMAND_TIMEOUT.findall(_SUCCESS_CRITERIA.search(text).group(1))
    )
    assert int(_TASK_TIMEOUT.search(text).group(1)) > grading


def test_grading_excludes_pre_and_post_run(tmp_path):
    """Both run OUTSIDE the watchdog (orchestrator.py 468 and 579, vs the block
    at 484-499), so charging them would demand ceilings nothing needs."""
    yaml = tmp_path / "x.yaml"
    yaml.write_text(
        "pre_run:\n  - command: seed\n    timeout: 500\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 60\n\n"
        "post_run:\n  - command: cleanup\n    timeout: 400\n"
    )
    body = _SUCCESS_CRITERIA.search(yaml.read_text()).group(1)
    assert _ANY_COMMAND_TIMEOUT.findall(body) == ["60"]


def test_grading_scan_ignores_the_limit_keys_themselves(tmp_path):
    """`turn_timeout:` / `task_timeout:` must not be counted as command time."""
    yaml = tmp_path / "x.yaml"
    yaml.write_text(
        "run_limits:\n  turn_timeout: 900\n  task_timeout: 1200\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 60\n"
    )
    body = _SUCCESS_CRITERIA.search(yaml.read_text()).group(1)
    assert _ANY_COMMAND_TIMEOUT.findall(body) == ["60"]
