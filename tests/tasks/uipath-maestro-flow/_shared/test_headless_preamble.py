"""Every zero-shot flow task states the run is headless, in one exact wording.

Kept in the task prompt rather than an experiment config because flow tasks run
under nightly.yaml, smoke.yaml, default.yaml and dispatch-selected configs, and
coder_eval has no pattern-scoped defaults — a config would either miss a runner
or reach another skill's simulated tasks.

Regex, not PyYAML: CI installs only pytest (see test_criterion_budgets).
"""

from __future__ import annotations

import functools
import glob
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_SUITE = os.path.normpath(os.path.join(_HERE, ".."))

CANONICAL = """This run is headless. No user is present and nobody will answer a question or
grant an approval, so do not ask, do not pause, and do not wait for input.
Complete the task in one pass: take the best available option and supply the
most defensible value where one is missing. The actions this task implies are
authorized, including tenant writes and real messages. Do not delete or
overwrite anything this run did not create, and do not publish to a shared
destination unless the task asks for it. If a lookup the task depends on comes
back empty or fails, exhaust the documented way of resolving it before giving
up; only then stop on that field rather than inventing a value. Record every
decision, assumption, and blocked step in your final response."""

# The variants this replaced. A task reintroducing one is drifting back.
_SUPERSEDED = re.compile(r"Do NOT ask for approval|Do NOT pause between planning")


@functools.lru_cache(maxsize=1)
def _tasks():
    """(path, text, is_simulated) for every task file in the suite."""
    out = []
    for path in sorted(glob.glob(os.path.join(_SUITE, "**", "*.yaml"), recursive=True)):
        text = open(path, encoding="utf-8").read()
        if re.search(r"^success_criteria:", text, re.M):
            out.append((path, text, bool(re.search(r"^simulation:", text, re.M))))
    return tuple(out)


def _rel(path: str) -> str:
    return os.path.relpath(path, _SUITE)


def test_every_zero_shot_task_states_the_run_is_headless():
    """Absent, an agent stops at a consent gate nobody is there to answer."""
    marker = CANONICAL.split("\n")[0]
    missing = [_rel(p) for p, text, sim in _tasks() if not sim and marker not in text]
    assert not missing, "tasks missing the headless preamble:\n  " + "\n  ".join(missing)


def test_the_wording_is_identical_everywhere():
    """8 variants is what made the old line unmaintainable. One wording, or none."""
    flat = " ".join(CANONICAL.split())
    drifted = [
        _rel(p)
        for p, text, sim in _tasks()
        if not sim and "This run is headless." in text and flat not in " ".join(text.split())
    ]
    assert not drifted, (
        "tasks whose headless preamble differs from the canonical wording in "
        f"{_rel(__file__)}:\n  " + "\n  ".join(drifted)
    )


def test_simulated_tasks_are_not_told_nobody_is_present():
    """They have a live simulated user; the preamble contradicts their premise."""
    wrong = [_rel(p) for p, text, sim in _tasks() if sim and "This run is headless." in text]
    assert not wrong, "simulated tasks carrying the headless preamble:\n  " + "\n  ".join(wrong)


def test_no_task_reintroduces_a_superseded_variant():
    stale = [_rel(p) for p, text, _ in _tasks() if _SUPERSEDED.search(text)]
    assert not stale, (
        "tasks using a superseded autonomy line; replace it with the canonical "
        "preamble:\n  " + "\n  ".join(stale)
    )
