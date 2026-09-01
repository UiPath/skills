"""A debug criterion must grant more time than its check can spend.

`run_debug` bounds itself with a deadline but cannot see the task YAML. If the
criterion `timeout:` is smaller, the grader SIGKILLs the check mid-attempt and
the payload, instanceId and CLI envelope are all lost (skill-flow-api-workflow,
2026-09; skill-flow-subflow before it, RCA 2026-05-29, which guarded one task
out of forty-four via a per-task test now absorbed here).

    criterion timeout >= debug_budget(...) + CRITERION_MARGIN_SECONDS

Budgets are read statically off each `run_debug(...)` call. Straight-line calls
sum, exclusive branches take the worst arm, helper calls cost inline at the call
site, and a loop over a module-level literal multiplies. What cannot be counted
is refused, never assumed: a runtime-seeded loop must declare
`# budget-guard: manual xN` on its timeout line, cross-checked against the
task's seed.py. Every round of review on this guard found a live under-budgeted
criterion behind a "cannot compute, assume fine" default.
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
# Split on ANY criterion so a block ends at its neighbour, and stop at the next
# top-level KEY (not any column-0 char — comments live there too). Both anchored:
# an unanchored `timeout:` matches inside `turn_timeout:` and `task_timeout:`.
_CRITERION_SPLIT = re.compile(r"\n\s*-\s+type:\s*")
_TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][\w-]*:", re.M)
# Everything from `command:` to the end of the criterion, so a quoting style
# cannot hide the script: `command: 'python3 "$TASK_DIR/..."'` stopped a
# quote-aware capture at the first inner `"` and silently skipped the criterion.
_COMMAND = re.compile(r"command:\s*(.*)", re.S)
_TIMEOUT = re.compile(r"^\s*timeout:\s*(\d+)", re.M)
_TASK_DIR_SCRIPT = re.compile(r"\$TASK_DIR/(\S+\.py)")
_TASK_TIMEOUT = re.compile(r"^\s*task_timeout:\s*(\d+)", re.M)
# Only these timeouts run inside the watchdog.
_SUCCESS_CRITERIA = re.compile(
    r"^success_criteria:\n(.*?)(?=^[A-Za-z_][\w-]*:|\Z)", re.M | re.S
)
# coder_eval/models/criteria.py:185 — a criterion that declares none still costs
# this, so counting it as 0 under-charges the grading sum.
_DEFAULT_CRITERION_TIMEOUT = 30
# Bounded work a check does OUTSIDE run_debug — the jira checks resolve a
# connection and re-read issues, each a 120s CLI call. The count comes from
# runtime data, so it is declared and checked, never guessed.
_OVERHEAD_MARKER = re.compile(r"#\s*budget-guard:[^#\n]*?\boverhead\s+(\d+)")
# `xN` is required: an unverified annotation is just a comment.
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
    if any(kw.arg is None for kw in call.keywords):
        return None  # **splat: the real arguments are not visible here
    kwargs = {kw.arg: _literal(kw.value) for kw in call.keywords}
    if "budget" in kwargs:
        return kwargs["budget"] if isinstance(kwargs["budget"], int) else None
    passed = {k: kwargs[k] for k in ("timeout", "retries", "backoff_seconds") if k in kwargs}
    if any(v is None for v in passed.values()):
        return None
    return flow_check.debug_budget(**passed)


def _is_run_debug(node: ast.AST) -> bool:
    """Bare or `mod.run_debug`. Matching only a Name made an attribute call read
    as no debug at all, skipping the criterion."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
    return name == "run_debug"


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if _is_run_debug(n)]


def _sibling_modules(script: str) -> list[str]:
    """Modules the check imports from its own task directory (e.g. `jira_is`)."""
    tree = ast.parse(open(script).read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    directory = os.path.dirname(script)
    found = [os.path.join(directory, f"{n}.py") for n in sorted(names)]
    return [f for f in found if os.path.exists(f)]


def _is_subprocess_run(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    )


def _nondebug_calls(script: str) -> list[tuple[str, int, int]]:
    """(module, line, seconds) per bounded subprocess call outside run_debug,
    in the check or a sibling it imports. `run_debug` has its own budget."""
    out = []
    for path in [script] + _sibling_modules(script):
        for node in ast.walk(ast.parse(open(path).read())):
            if not _is_subprocess_run(node):
                continue
            arg = next((kw.value for kw in node.keywords if kw.arg == "timeout"), None)
            seconds = _literal(arg) if arg is not None else None
            if isinstance(seconds, (int, float)):
                out.append((os.path.basename(path), node.lineno, int(seconds)))
    return out


def _probe_caps(script: str) -> list[int]:
    """Module-level `MAX_*` int constants: the bound a checker puts on its own
    non-debug probes. Raising one must raise the declared overhead with it."""
    return [
        node.value.value
        for node in ast.parse(open(script).read()).body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id.startswith("MAX_")
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int)
    ]


def _module_lengths(tree: ast.Module) -> dict[str, int]:
    """Module-level list/tuple names and their lengths, so `for x in CASES` is
    countable. A name any function rebinds is dropped — the module value is
    shadowed where the loop reads it, and a wrong multiplier beats no multiplier
    only in the wrong direction."""
    lengths = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lengths[target.id] = len(node.value.elts)
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef)
    for func in (n for n in ast.walk(tree) if isinstance(n, kinds)):
        for node in ast.walk(func):
            targets = node.targets if isinstance(node, ast.Assign) else []
            for target in targets:
                if isinstance(target, ast.Name):
                    lengths.pop(target.id, None)
    return lengths


_TRANSPARENT_ITERATORS = ("enumerate", "list", "reversed", "sorted", "tuple")


def _iterations_of(target: ast.AST, lengths: dict[str, int]) -> int | None:
    """Length of an iterable expression, or None when that is not static."""
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


def _iterations(loop: ast.AST, lengths: dict[str, int]) -> int | None:
    """Iterations of ``loop``, or None when not static (a ``while``, or a ``for``
    over runtime seeds). None is reported, never assumed to be 1."""
    return _iterations_of(loop.iter, lengths) if isinstance(loop, ast.For) else None


class _Price(NamedTuple):
    """Seconds one execution can spend, and the loops we had to guess at. One
    traversal produces both: when they walked separately they disagreed about
    scope and a loop inside a helper went unreported."""

    seconds: int
    unsized: tuple[int, ...]


_FREE = _Price(0, ())


def _merge(*prices: _Price) -> _Price:
    """Sequential: seconds add, guesses accumulate."""
    return _Price(
        sum(p.seconds for p in prices),
        tuple(sorted({line for p in prices for line in p.unsized})),
    )


def _worst(prices: list[_Price]) -> _Price:
    """Exclusive: priciest arm wins, but every arm's guesses are reported since
    any of them may be the one that runs."""
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
    seen: tuple = (),
    manual: int | None = None,
) -> _Price:
    """What one execution of ``node`` can spend in ``run_debug``.

    Straight-line calls sum; exclusive branches (if/match/try) take the worst
    arm; a countable loop multiplies its body, an uncountable one is charged
    ``manual`` passes or 1, reporting its line either way. Calls to module-level
    functions cost INLINE at the call site, so a helper invoked once per seed is
    multiplied with the loop around it. ``seen`` breaks recursion."""
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
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in defs:
        name = node.func.id
        args = [_cost(a, lengths, defs, seen, manual) for a in node.args]
        args += [_cost(kw.value, lengths, defs, seen, manual) for kw in node.keywords]
        if name in seen:
            # Inspect the whole CYCLE, not the name that closes it: in a -> b -> a
            # the debug may live in b while a is the repeated name.
            cycle = seen[seen.index(name):] + (name,)
            if any(_calls_in(defs[c]) for c in cycle if c in defs):
                pytest.fail(
                    f"line {node.lineno}: the cycle {' -> '.join(cycle)} recurses and "
                    "runs a debug, so "
                    "its cost cannot be counted. Flatten the recursion or bound "
                    "it in a loop this guard can size."
                )
            return _merge(*args)
        inner = _cost(defs[name], lengths, defs, seen + (name,), manual)
        return _merge(inner, *args)
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
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        # Every generator multiplies, and a filter runs once per iteration of the
        # generators to its left. Pricing only the first generator under-charged
        # a nested comprehension, and dropping the filters priced a debug inside
        # an `if` clause at zero, which skipped the criterion outright.
        element = _merge(*[_cost(c, lengths, defs, seen, manual)
                           for c in ast.iter_child_nodes(node)
                           if not isinstance(c, ast.comprehension)])
        runs, guessed, total = 1, (), _FREE
        for gen in node.generators:
            total = _merge(total, _cost(gen.iter, lengths, defs, seen, manual))
            count = _iterations_of(gen.iter, lengths)
            if count is None:
                count = manual if manual is not None else 1
                guessed = (node.lineno,)
            runs *= count
            for cond in gen.ifs:
                priced = _cost(cond, lengths, defs, seen, manual)
                total = _merge(total, _Price(priced.seconds * runs, priced.unsized))
        if not element.seconds and not any(
            _cost(c, lengths, defs, seen, manual).seconds
            for g in node.generators for c in g.ifs
        ):
            guessed = ()
        return _merge(total, _Price(element.seconds * runs, element.unsized + guessed))
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


def _body(stmts: list, lengths, defs, seen=(), manual=None) -> _Price:
    return _merge(*[_cost(s, lengths, defs, seen, manual) for s in stmts])


def _defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef)
    return {n.name: n for n in ast.walk(tree) if isinstance(n, kinds)}


def _entry(tree: ast.Module, subcommand: str | None, path: str) -> ast.FunctionDef:
    """The function a criterion executes. A subcommand naming no function falls
    back to ``main`` rather than being skipped, since dispatch is often an
    ``if/elif`` on ``sys.argv``. Neither present fails loudly: charging the
    module whole would double-count every helper."""
    defs = _defs(tree)
    entry = (defs.get(subcommand) if subcommand else None) or defs.get("main")
    if entry is None:
        pytest.fail(
            f"{path}: calls run_debug but defines neither main() nor "
            f"{subcommand!r}, so its criterion cannot be priced"
        )
    return entry


def _reject_aliased_debug(tree: ast.Module, path: str) -> None:
    """`run_debug` under another name reads as no debug, silently skipping the
    criterion. Refuse rather than guess."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if alias.name == "run_debug" and alias.asname:
                pytest.fail(
                    f"{path}: imports run_debug as `{alias.asname}`, which this "
                    "guard cannot follow. Import it under its own name."
                )


def _price_script(
    path: str, subcommand: str | None, manual: int | None = None
) -> _Price | None:
    """Price one execution of ``path``, or None if it runs no debug.

    ``manual`` is the declared pass count for an uncountable loop. It applies to
    every such loop, which is why the caller refuses more than one: applying N
    to both under-charges whenever the other runs more often."""
    tree = ast.parse(open(path).read())
    _reject_aliased_debug(tree, path)
    if not _calls_in(tree):
        return None
    lengths, defs = _module_lengths(tree), _defs(tree)
    entry = _entry(tree, subcommand, path)
    # Seed `seen` with the entry so a self-call is not charged a second level.
    price = _cost(entry, lengths, defs, (entry.name,), manual)
    return price if price.seconds else None


def _budget_of_script(path: str, subcommand: str | None) -> int | None:
    price = _price_script(path, subcommand)
    return price.seconds if price else None


def _unsized_loops(path: str, subcommand: str | None) -> list[int]:
    price = _price_script(path, subcommand)
    return list(price.unsized) if price else []


_SEED_CASE_NAMES = ("cases", "seed_cases")


def _seed_case_count(script: str) -> int | None:
    """Cases the task's ``seed.py`` writes, when stated literally — what makes
    ``manual xN`` checkable. None when absent, unnamed, or ambiguous: better no
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
    """`defaults.run_limits.task_timeout` from the default experiment. A task
    declaring none runs at this value, not uncapped — skipping those silently
    exempted 58. Regex, not PyYAML: CI installs only pytest, and a module-level
    `import yaml` would error at collection and take the suite with it."""
    text = open(os.path.normpath(_EXPERIMENT_DEFAULTS)).read()
    found = _TASK_TIMEOUT.search(text)
    assert found, f"no task_timeout in {_EXPERIMENT_DEFAULTS}"
    return int(found.group(1))


def _criterion_blocks(text: str, kind: str | None = None):
    """Each criterion's own text, cut at its neighbour or the next top-level key.
    The leading newline lets a body that starts at its first item split like a
    whole file does."""
    for block in _CRITERION_SPLIT.split("\n" + text)[1:]:
        stop = _TOP_LEVEL_KEY.search(block)
        block = block[: stop.start()] if stop else block
        if kind is None or block.startswith(kind):
            yield block


def _criterion_seconds(block: str) -> int:
    found = _TIMEOUT.search(block)
    return int(found.group(1)) if found else _DEFAULT_CRITERION_TIMEOUT


def _task_budgets():
    """(yaml, effective task_timeout, worst-case grading) per task.

    Grading is success_criteria only: orchestrator.py runs pre_run at 468 and
    post_run at 579, outside the watchdog wrapping `_evaluation_loop` (484-499)."""
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
                sum(
                    _criterion_seconds(b)
                    for b in _criterion_blocks(criteria.group(1))
                ),
            )


def _criteria():
    """(yaml, script, subcommand, timeout, declared pass count) per $TASK_DIR
    criterion. Timeout and annotation are read off the SAME line so the
    annotation cannot drift from the number it explains."""
    for root, _dirs, files in os.walk(_SUITE_ROOT):
        for name in files:
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(root, name)
            text = open(path).read()
            for block in _criterion_blocks(text, "run_command"):
                command = _COMMAND.search(block)
                if not command:
                    continue
                script = _TASK_DIR_SCRIPT.search(command.group(1))
                if not script:
                    continue
                first_line = command.group(1).split("\n")[0].strip().strip("'\"")
                resolved = os.path.join(root, script.group(1))
                if not os.path.exists(resolved):
                    continue
                timeout_line = next(
                    (ln for ln in block.split("\n") if _TIMEOUT.search(ln)), ""
                )
                marker = _MANUAL_MARKER.search(timeout_line)
                parts = first_line.split()
                yield (
                    os.path.relpath(path, _SUITE_ROOT),
                    resolved,
                    parts[-1] if parts[-1].isidentifier() else None,
                    _criterion_seconds(block),
                    # "" marks a marker with no count, distinct from no marker.
                    (marker.group(1) or "") if marker else None,
                    int(over.group(1)) if (over := _OVERHEAD_MARKER.search(timeout_line)) else None,
                )


def _annotation_error(
    price: _Price, declared: str | None, seeded: int | None, where: str
) -> str | None:
    """Why this criterion's `budget-guard` annotation is unacceptable, or None.
    Pure so every refusal path is testable: two have no live task to reach
    them, and untested branches are where this guard kept going wrong."""
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


def _eligible():
    """Independently of `_criteria()`: every $TASK_DIR run_command whose script
    exists, and every YAML with success_criteria. Counted a second way so a
    parser regression cannot quietly shrink what the guard enforces."""
    criteria = tasks = 0
    for root, _dirs, files in os.walk(_SUITE_ROOT):
        for name in files:
            if not name.endswith((".yaml", ".yml")):
                continue
            text = open(os.path.join(root, name)).read()
            if _SUCCESS_CRITERIA.search(text):
                tasks += 1
            for block in _criterion_blocks(text, "run_command"):
                command = _COMMAND.search(block)
                script = _TASK_DIR_SCRIPT.search(command.group(1)) if command else None
                if script and os.path.exists(os.path.join(root, script.group(1))):
                    criteria += 1
    return criteria, tasks


def test_every_eligible_criterion_and_task_is_enforced():
    """Thresholds like `> 40` stayed green while `_criteria()`'s `continue`
    paths silently dropped most of the suite. Assert the exact counts instead."""
    criteria, tasks = _eligible()
    assert len(_CASES) == criteria, f"{criteria - len(_CASES)} criteria went undiscovered"
    assert len(_TASK_BUDGETS) == tasks, f"{tasks - len(_TASK_BUDGETS)} tasks went undiscovered"
    priced = [c for c in _CASES if _budget_of_script(c[1], c[2]) is not None]
    assert len(priced) > 40, f"only {len(priced)} criteria resolved a budget"


@pytest.mark.parametrize(
    "yaml_path,script,subcommand,criterion,declared,overhead",
    _CASES,
    ids=[f"{y}:{s or '-'}" for y, _p, s, _t, _d, _o in _CASES],
)
def test_criterion_clears_the_debug_budget(
    yaml_path, script, subcommand, criterion, declared, overhead
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

    # Bounded non-debug work: detected so it cannot be forgotten, declared
    # because its call count comes from runtime data.
    nondebug = _nondebug_calls(script)
    if nondebug and overhead is None:
        where_calls = ", ".join(f"{m}:{ln} ({sec}s)" for m, ln, sec in nondebug[:4])
        pytest.fail(
            f"{yaml_path}: {where} also runs bounded work outside run_debug "
            f"({where_calls}), which this guard prices at nothing and the "
            f"{flow_check.CRITERION_MARGIN_SECONDS}s margin does not cover. "
            "Annotate the timeout with `# budget-guard: overhead <seconds>` for "
            "the success path's worth and the guard will fund it."
        )
    if nondebug and overhead is not None:
        # Weak but non-zero corroboration: the declared total must be whole
        # calls at the price the code actually uses. Catches a typo or a number
        # picked out of the air; the call COUNT still comes from the bound the
        # checker enforces (MAX_ISSUE_PROBES and friends).
        unit = min(sec for _m, _ln, sec in nondebug)
        if overhead < unit or overhead % unit:
            pytest.fail(
                f"{yaml_path}: {where} declares `overhead {overhead}`, which is "
                f"not a whole number of {unit}s calls. Its bounded work costs "
                f"{unit}s a call, so the declaration should be a multiple of it."
            )
        # Tie the declaration to the cap the checker enforces, so raising one
        # without the other fails instead of silently under-funding.
        caps = _probe_caps(script)
        if caps and overhead // unit < max(caps):
            pytest.fail(
                f"{yaml_path}: {where} declares {overhead // unit} calls of "
                f"{unit}s but caps its probes at {max(caps)}, which it can spend "
                "on top of the fixed calls. Raise the overhead with the cap."
            )
    if overhead is not None and not nondebug:
        pytest.fail(
            f"{yaml_path}: {where} does no bounded work outside run_debug, so "
            "the `budget-guard: overhead` annotation is stale. Remove it."
        )

    required = price.seconds + (overhead or 0) + flow_check.CRITERION_MARGIN_SECONDS
    assert criterion >= required, (
        f"{yaml_path} grants {criterion}s to {where}, which can spend "
        f"{price.seconds}s in run_debug. Raise the criterion to >= {required}s, "
        "or lower the check's timeout / pass retries=1."
    )


# ── cost model ──────────────────────────────────────────────────────────────
#
# Each shape below shipped a wrong number during review. Locked against a
# synthetic module so a task edit cannot quietly retire the coverage.


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
    """Loop calls a helper, helper runs the debug. Costing helpers separately
    priced this at one pass."""
    src = (
        f"CASES = [1, 2, 3]\n\n\ndef verify(c):\n    {_ONE}\n\n\n"
        "def main():\n    for c in CASES:\n        verify(c)\n"
    )
    assert _price(src, tmp=str(tmp_path)) == 1455


def test_runtime_loop_is_reported_not_guessed(tmp_path):
    """Must surface for manual sizing even when the debug is a helper away."""
    src = (
        f"def verify(c):\n    {_ONE}\n\n\n"
        "def main():\n    for c in load():\n        verify(c)\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [6]
    assert _budget_of_script(path, None) == 485  # the floor, not the truth


def test_debug_bearing_recursion_is_refused(tmp_path):
    """Depth is no more knowable than a loop count. Pricing it at one pass let a
    recursive checker through on an insufficient criterion timeout."""
    src = f"def main():\n    {_ONE}\n    main()\n"
    with pytest.raises(BaseException, match="recurses and runs a debug"):
        _price(src, tmp=str(tmp_path))


def test_mutual_recursion_is_refused(tmp_path):
    src = f"def a():\n    {_ONE}\n    b()\n\n\ndef b():\n    a()\n\n\ndef main():\n    a()\n"
    with pytest.raises(BaseException, match="recurses and runs a debug"):
        _price(src, tmp=str(tmp_path))


def test_recursion_without_a_debug_is_free(tmp_path):
    """A recursive helper that runs no debug costs nothing and is not refused."""
    src = f"def walk(n):\n    walk(n)\n\n\ndef main():\n    walk(1)\n    {_ONE}\n"
    assert _price(src, tmp=str(tmp_path)) == 485


def test_module_without_an_entry_point_fails_loudly(tmp_path):
    """Charging the module whole would double-count every helper."""
    src = f"def helper():\n    {_ONE}\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    with pytest.raises(BaseException, match="neither main"):
        _budget_of_script(path, None)


def test_loop_inside_a_helper_is_reported(tmp_path):
    """Mirror of the escalation shape: LOOP in the helper, not the entry. The
    detector once walked only the entry, so this went unreported."""
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
    """One `_Price` so cost and detection cannot disagree about scope."""
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
    """Either arm might run, so both arms' unsized loops must surface."""
    src = (
        "def main():\n    if x:\n        for c in load():\n"
        f"            {_ONE}\n    else:\n        for d in other():\n"
        f"            {_ONE}\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == [3, 6]


def test_locally_rebound_list_is_not_treated_as_static(tmp_path):
    """A rebound constant is shadowed where the loop reads it."""
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
    """Two different case lists: no cross-check beats a wrong one."""
    open(os.path.join(str(tmp_path), "seed.py"), "w").write(
        'a = {"cases": [1, 2]}\nb = {"cases": [1, 2, 3]}\n'
    )
    assert _seed_case_count(os.path.join(str(tmp_path), "check_x.py")) is None


def test_two_uncountable_loops_are_refused_not_guessed(tmp_path):
    """One count cannot describe two loops of different sizes; applying N to
    both under-charges, so the shape is refused rather than guessed."""
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
# Every refusal path, including the two no live task reaches.

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
# The checks above bound each criterion; nothing bounded their SUM against the
# cap around them. `task_timeout` wraps agent turns AND grading in one watchdog
# (orchestrator.py 484-499); firing it reports the whole task TIMEOUT, losing
# even the criteria that passed.
#
#     task_timeout > worst-case grading
#
# An impossibility check, not a sufficiency one — anything stronger needs the
# agent's real wall clock. An earlier draft demanded `grading + turn_timeout`
# and broke on smoke.yaml, where the two are equal.


def _grading_of(text: str) -> int:
    """Worst-case grading seconds for a task YAML's success_criteria."""
    body = _SUCCESS_CRITERIA.search(text)
    return sum(_criterion_seconds(b) for b in _criterion_blocks(body.group(1))) if body else 0


def _task_budget_error(task_timeout: int, grading: int) -> str | None:
    """Why this task can never complete, or None. Pure, so the fixtures below
    exercise the same rule the suite is held to instead of restating it."""
    if task_timeout > grading:
        return None
    return (
        f"worst-case grading is {grading}s against a task_timeout of "
        f"{task_timeout}s, so the watchdog can fire before grading finishes no "
        "matter how fast the agent is. It SIGKILLs the run and reports TIMEOUT, "
        f"losing every criterion. Raise task_timeout well above {grading}s (the "
        "agent needs the remainder), or lower the criterion timeouts."
    )


_TASK_BUDGETS = sorted(_task_budgets())


@pytest.mark.parametrize(
    "yaml_path,task_timeout,grading",
    _TASK_BUDGETS,
    ids=[y for y, _t, _g in _TASK_BUDGETS],
)
def test_grading_alone_fits_the_task_timeout(yaml_path, task_timeout, grading):
    problem = _task_budget_error(task_timeout, grading)
    assert problem is None, f"{yaml_path}: {problem}"


def _fixture(tmp_path, body: str) -> str:
    path = tmp_path / "x.yaml"
    path.write_text(body)
    return path.read_text()


def test_impossible_task_is_rejected(tmp_path):
    """Grading alone at or above the cap: no agent run fits."""
    text = _fixture(
        tmp_path,
        "run_limits:\n  turn_timeout: 900\n  task_timeout: 600\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 600\n",
    )
    assert _grading_of(text) == 600
    assert _task_budget_error(600, _grading_of(text))


def test_smoke_shaped_task_is_not_flagged(tmp_path):
    """smoke.yaml has task_timeout == turn_timeout, which the earlier
    `grading + turn_timeout` draft made impossible. The floor must accept it."""
    text = _fixture(
        tmp_path,
        "run_limits:\n  turn_timeout: 900\n  task_timeout: 900\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 210\n",
    )
    assert _task_budget_error(900, _grading_of(text)) is None


def test_grading_excludes_pre_and_post_run(tmp_path):
    """Both run outside the watchdog (orchestrator.py 468 / 579 vs 484-499)."""
    text = _fixture(
        tmp_path,
        "pre_run:\n  - command: seed\n    timeout: 500\n\n"
        "success_criteria:\n  - type: run_command\n    timeout: 60\n\n"
        "post_run:\n  - command: cleanup\n    timeout: 400\n",
    )
    assert _grading_of(text) == 60


def test_grading_scan_ignores_the_limit_keys_themselves(tmp_path):
    """An unanchored `timeout:` matches inside `turn_timeout:`/`task_timeout:`."""
    text = _fixture(
        tmp_path,
        "success_criteria:\n  - type: run_command\n"
        "    turn_timeout: 900\n    task_timeout: 1200\n    timeout: 60\n",
    )
    assert _grading_of(text) == 60


def test_criterion_without_a_timeout_costs_the_coder_eval_default(tmp_path):
    """Counting it as 0 under-charged; coder_eval defaults it to 30s."""
    text = _fixture(
        tmp_path,
        "success_criteria:\n  - type: run_command\n    command: a\n"
        "  - type: run_command\n    command: b\n    timeout: 100\n",
    )
    assert _grading_of(text) == _DEFAULT_CRITERION_TIMEOUT + 100


def test_a_criterion_cannot_borrow_its_neighbours_timeout(tmp_path):
    """Blocks end at the next criterion, so a missing timeout is the default and
    never a number lifted from the item below it."""
    text = _fixture(
        tmp_path,
        "success_criteria:\n  - type: run_command\n    command: a\n"
        "  - type: run_command\n    command: b\n    timeout: 900\n",
    )
    first = next(_criterion_blocks(text, "run_command"))
    assert _criterion_seconds(first) == _DEFAULT_CRITERION_TIMEOUT


def test_bounded_nondebug_work_is_detected(tmp_path):
    """The 60s margin covers interpreter start and static asserts, not a check
    that shells out. Detected through sibling imports so it cannot be forgotten."""
    (tmp_path / "helper.py").write_text(
        "import subprocess\n\n\ndef go():\n    subprocess.run(['uip'], timeout=120)\n"
    )
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(f"import helper\n\n\ndef main():\n    {_ONE}\n    helper.go()\n")
    assert _nondebug_calls(path) == [("helper.py", 5, 120)]


def test_nondebug_scan_ignores_run_debug_and_untimed_calls(tmp_path):
    """`run_debug` has its own budget, and an unbounded call cannot be priced."""
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(
        f"import subprocess\n\n\ndef main():\n    {_ONE}\n"
        "    subprocess.run(['uip'])\n"
    )
    assert _nondebug_calls(path) == []


def test_overhead_annotation_parses_off_the_timeout_line():
    line = "    timeout: 1800  # budget-guard: overhead 480. connection_id (2) + 2 reads"
    assert int(_OVERHEAD_MARKER.search(line).group(1)) == 480
    assert _OVERHEAD_MARKER.search("    timeout: 1800  # nothing declared") is None


def test_overhead_must_be_whole_calls():
    """A number picked out of the air is not a bound. It has to be whole calls
    at the price the code uses; the COUNT comes from the checker's own cap."""
    unit = 120
    for declared, ok in ((480, True), (600, True), (500, False), (60, False)):
        whole = declared >= unit and not declared % unit
        assert whole is ok, declared


def test_mutual_recursion_with_the_debug_in_the_other_leg_is_refused(tmp_path):
    """`a -> b -> a` where `b` holds the debug: the repeated name is `a`, so
    inspecting only the name that closes the cycle missed it."""
    src = f"def a():\n    b()\n\n\ndef b():\n    {_ONE}\n    a()\n\n\ndef main():\n    a()\n"
    with pytest.raises(BaseException, match="recurses and"):
        _price(src, tmp=str(tmp_path))


def test_probe_cap_is_read_off_the_checker(tmp_path):
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write("MAX_ISSUE_PROBES = 3\nMAX_OTHER = 7\nNOT_A_CAP = 9\n")
    assert _probe_caps(path) == [3, 7]


# ── shapes the scan must not read as "no debug" or "one pass" ───────────────


def test_keyword_splat_is_unpriceable(tmp_path):
    """`run_debug(**opts)` hides its arguments; pricing the default would accept
    an under-budgeted criterion."""
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write('def main():\n    run_debug(**{"timeout": 600})\n')
    with pytest.raises(BaseException, match="non-literal"):
        _budget_of_script(path, None)


def test_comprehension_over_a_runtime_iterable_is_reported(tmp_path):
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(f"def main():\n    [{_ONE} for _ in load()]\n")
    assert _unsized_loops(path, None) == [2]


def test_comprehension_over_a_literal_multiplies(tmp_path):
    src = f"A = [1, 2, 3]\n\n\ndef main():\n    [{_ONE} for _ in A]\n"
    assert _price(src, tmp=str(tmp_path)) == 485 * 3


def test_async_entry_point_is_priced(tmp_path):
    assert _price(f"async def main():\n    {_ONE}\n", tmp=str(tmp_path)) == 485


def test_attribute_style_debug_call_is_priced(tmp_path):
    """`mod.run_debug(...)` read as no debug and skipped the whole criterion."""
    src = "def main():\n    mod.run_debug(timeout=240)\n"
    assert _price(src, tmp=str(tmp_path)) == 485


def test_aliased_debug_import_is_refused(tmp_path):
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(
        "from flow_check import run_debug as rd\n\n\ndef main():\n    rd(timeout=240)\n"
    )
    with pytest.raises(BaseException, match="imports run_debug as"):
        _budget_of_script(path, None)


def test_nested_comprehension_multiplies_every_generator(tmp_path):
    """Pricing only the first generator under-charged by the rest."""
    src = f"A = [1, 2]\nB = [1, 2, 3]\n\n\ndef main():\n    [{_ONE} for a in A for b in B]\n"
    assert _price(src, tmp=str(tmp_path)) == 485 * 6


def test_debug_inside_a_comprehension_filter_is_priced(tmp_path):
    """Filters were excluded from the body, so this priced at zero and skipped
    the criterion entirely."""
    src = f"A = [1, 2]\n\n\ndef main():\n    [x for x in A if {_ONE}]\n"
    assert _price(src, tmp=str(tmp_path)) == 485 * 2


def test_comprehension_without_a_debug_is_not_reported(tmp_path):
    src = f"A = [1, 2]\n\n\ndef main():\n    [x for x in load()]\n    {_ONE}\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(src)
    assert _unsized_loops(path, None) == []


# ── generated coverage ──────────────────────────────────────────────────────
#
# Hand-picked examples kept missing shapes (nested comprehensions priced by
# their first generator, a debug inside a filter priced at zero). These generate
# programs and check the model against what the program actually does.


def _reference(text: str, path: str) -> int:
    """What the program really spends: execute it with a counting run_debug."""
    calls = []
    ns = {"run_debug": lambda **kw: calls.append(flow_check.debug_budget(kw.get("timeout", 240)))}
    exec(compile(text, path, "exec"), ns)  # noqa: S102 — generated, not user input
    ns["main"]()
    return sum(calls)


_BODIES = [
    "run_debug(timeout=240)",
    "helper()",
    "[run_debug(timeout=240) for _ in A]",
    "[run_debug(timeout=240) for _ in A for _ in B]",
    "[x for x in A if run_debug(timeout=240)]",
    "[run_debug(timeout=240) for _ in enumerate(B)]",
]
_LOOPS = ["", "for _i in A:", "for _i in B:", "for _i in [1, 2, 3, 4]:", "for _i in sorted(A):"]


@pytest.mark.parametrize("body", _BODIES)
@pytest.mark.parametrize("loop", _LOOPS)
def test_branch_free_programs_price_exactly(body, loop, tmp_path):
    """No branches, so the worst case IS the actual case: the model must agree
    with execution to the second."""
    lines = ["A = [1, 2]", "B = [1, 2, 3]", "", "", "def helper():",
             "    run_debug(timeout=240)", "", "", "def main():"]
    lines += [f"    {loop}", f"        {body}"] if loop else [f"    {body}"]
    text = "\n".join(lines) + "\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(text)
    assert _budget_of_script(path, None) == _reference(text, path), text


@pytest.mark.parametrize("arm", ["if flag:", "try:"])
@pytest.mark.parametrize("body", _BODIES[:4])
def test_branching_programs_are_an_upper_bound(arm, body, tmp_path):
    """Exclusive arms take the priciest, so the model must never come in under
    what a run actually spends."""
    other = "else:" if arm.startswith("if") else "except Exception:"
    text = "\n".join([
        "A = [1, 2]", "B = [1, 2, 3]", "flag = True", "", "", "def helper():",
        "    run_debug(timeout=240)", "", "", "def main():", f"    {arm}",
        f"        {body}", f"    {other}", "        run_debug(timeout=240)",
    ]) + "\n"
    path = os.path.join(str(tmp_path), "check_x.py")
    open(path, "w").write(text)
    assert _budget_of_script(path, None) >= _reference(text, path), text


def test_single_quoted_command_is_not_skipped(tmp_path):
    """`command: 'python3 "$TASK_DIR/x.py"'` stopped a quote-aware capture at the
    first inner quote, silently dropping the criterion from enforcement."""
    block = """    description: "x"
    command: 'python3 "$TASK_DIR/check_x.py" "a/*.json"'
    timeout: 15
"""
    found = _COMMAND.search(block)
    assert found and "$TASK_DIR" in found.group(1)
    assert _TASK_DIR_SCRIPT.search(found.group(1)).group(1) == "check_x.py"
