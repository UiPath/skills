"""Pin the hand-tuned command_patterns PR #4574 rewrote to recorded agent commands.

Each pattern is loaded from its task YAML (never a copy) and searched with and
without re.DOTALL: coder-eval 1.x compiles command patterns with DOTALL, and the
grade must be the same on both versions.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
import yaml

TASKS = Path(__file__).resolve().parents[1] / "tasks"
FLAGS = (0, re.DOTALL)


def _pattern(task: str, description: str) -> str:
    data = yaml.safe_load((TASKS / task).read_text(encoding="utf-8"))
    (criterion,) = [c for c in data["success_criteria"] if c.get("description") == description]
    return criterion["command_pattern"]


def _hits(pattern: str, command: str) -> set[bool]:
    return {bool(re.search(pattern, command, flags)) for flags in FLAGS}


# --- uipath-review: one criterion per project ---------------------------------

REVIEW = "uipath-review/review_multi_project_solution.yaml"
PROJECT_A = _pattern(REVIEW, "Agent invoked uip rpa get-errors or validate on ProjectA")
PROJECT_B = _pattern(REVIEW, "Agent invoked uip rpa get-errors or validate on ProjectB")

BOTH = [
    'for p in ProjectA ProjectB; do uip rpa get-errors --project-dir "MySolution/$p" --output json; done',
    'for p in ProjectA ProjectB\ndo\n  uip rpa validate --project-dir "MySolution/$p" --output json\ndone',
    'for d in MySolution/*/; do uip rpa get-errors --project-dir "$d" --output json; done',
]
ONLY_A = [
    "uip rpa get-errors --project-dir MySolution/ProjectA --output json",
    "cd MySolution/ProjectA && uip rpa validate --file-path Main.xaml --output json",
    "uip rpa validate --file-path MySolution/ProjectA/Main.xaml --project-dir MySolution/ProjectA",
    # ProjectB is named in the same call but never validated.
    "ls MySolution/ProjectA MySolution/ProjectB && uip rpa get-errors --project-dir MySolution/ProjectA",
    "uip rpa get-errors --project-dir MySolution/ProjectA; cat MySolution/ProjectB/Main.xaml",
    "for p in ProjectA ProjectB; do ls $p; done; uip rpa validate --project-dir MySolution/ProjectA",
]
NEITHER = [
    "cat <<EOF\nProjectA ProjectB\nEOF\nuip rpa get-errors --help",
    "uip rpa get-errors --project-dir MySolution/ProjectAB",
    "ls MySolution/ProjectA MySolution/ProjectB",
]


@pytest.mark.parametrize("command", BOTH)
def test_review_loop_credits_both_projects(command):
    assert _hits(PROJECT_A, command) == {True}
    assert _hits(PROJECT_B, command) == {True}


@pytest.mark.parametrize("command", ONLY_A)
def test_review_credits_only_the_validated_project(command):
    assert _hits(PROJECT_A, command) == {True}
    assert _hits(PROJECT_B, command) == {False}


@pytest.mark.parametrize("command", NEITHER)
def test_review_credits_neither_project(command):
    assert _hits(PROJECT_A, command) == {False}
    assert _hits(PROJECT_B, command) == {False}


# --- uipath-mcp-servers: no new login after not_supported ----------------------

LOGIN = _pattern(
    "uipath-mcp-servers/swagger-not-supported/task.yaml",
    "Agent did NOT log in again (not_supported is not an auth failure)",
)


@pytest.mark.parametrize(
    "command",
    [
        "uip login",
        "uip login --tenant DefaultTenant",
        "uip auth login",
        "uip login refresh",
        "uip login tenant set DefaultTenant",
        "uip login status --output json && uip login",
    ],
)
def test_login_guard_forbids_a_new_login(command):
    assert _hits(LOGIN, command) == {True}


@pytest.mark.parametrize(
    "command",
    [
        "uip login status",
        "uip login status --output json",
        "uip auth login status",
        "uip login which",
        "uip login tenant list --output json",
        "uip login profiles list",
        "uip login --help",
        "uip login -h",
    ],
)
def test_login_guard_allows_reading_the_session(command):
    assert _hits(LOGIN, command) == {False}


# --- uipath-test: clone commands skip single-quoted words whole ----------------

CLONE_LABELS = _pattern(
    "uipath-test/testcase_clone_smoke.yaml",
    "Agent cloned with labels included (`clone ... --include ... labels`, must succeed)",
)
SUBSTITUTED_KEY = "\"$(python3 -c 'import json;print(json.load(open(\"k.json\"))[\"key\"])')\""


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testcases clone --project-key HEALTH --test-case-key HEALTH:5 --include steps labels --output json",
        f"uip tm testcases clone --test-case-key {SUBSTITUTED_KEY} --new-name X --include labels",
        "uip tm testcases clone --test-case-key 'HEALTH:5' --new-name 'Copy of 5' --include 'labels'",
        "uip tm testcases clone --test-case-key HEALTH:5 \\\n  --include labels",
    ],
)
def test_clone_labels_matches(command):
    assert _hits(CLONE_LABELS, command) == {True}


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testcases clone --project-key HEALTH --test-case-key 'HEALTH:5'; "
        "uip tm testcases get --test-case-key 'HEALTH:5' --include labels",
        "uip tm testcases clone --test-case-key 'HEALTH:5' --name X | jq '.Data' ; echo '--include labels'",
        "uip tm testcases clone --test-case-key HEALTH:5 --include steps",
    ],
)
def test_clone_labels_stops_at_the_command_boundary(command):
    assert _hits(CLONE_LABELS, command) == {False}


def test_clone_labels_does_not_backtrack_on_many_quoted_words():
    command = "uip tm testcases clone " + " ".join(f"'a{i}'" for i in range(24)) + " --include steps"
    for flags in FLAGS:
        start = time.perf_counter()
        assert not re.search(CLONE_LABELS, command, flags)
        assert time.perf_counter() - start < 0.05


SIBLINGS = [
    ("uipath-test/testcase_lifecycle_e2e.yaml", "testcases", "--new-name X"),
    ("uipath-test/testset_clone_smoke.yaml", "testsets", '--new-name "$NAME"'),
    ("uipath-test/testset_order_integration.yaml", "testsets", '--new-name "$NAME"'),
    ("uipath-test/testset_lifecycle_e2e.yaml", "testsets", '--new-name "$NAME"'),
]


def _clone_pattern(task: str) -> str:
    data = yaml.safe_load((TASKS / task).read_text(encoding="utf-8"))
    (pattern,) = [
        c["command_pattern"]
        for c in data["success_criteria"]
        if c.get("type") == "command_executed" and r"\s+clone\b" in c.get("command_pattern", "")
    ]
    return pattern


@pytest.mark.parametrize(("task", "noun", "new_name"), SIBLINGS)
def test_sibling_clone_patterns_skip_a_quoted_semicolon(task, noun, new_name):
    pattern = _clone_pattern(task)
    command = f"uip tm {noun} clone --key {SUBSTITUTED_KEY} {new_name}"
    assert _hits(pattern, command) == {True}
    assert _hits(pattern, f"uip tm {noun} clone --key 'K:1'; echo {new_name}") == {False}
