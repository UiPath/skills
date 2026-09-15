"""The uipath-insights command criteria must match both delivery routes.

`uip insights jobs investigate <playbook>` runs the same reads the
playbook guide's chains do, so a task graded on "did the agent gather
this evidence" has to accept either spelling. These tests pin that, and
pin the two things that make such a pattern wrong: an unbounded wildcard
(the grader compiles with `re.DOTALL`, so `.*` bleeds past the end of one
command into a batched neighbour) and a negative assertion that misses
the new route.

The fixtures are per task on purpose. Not every task routes at the verb:
`smoke_all_commands` asks for every subcommand by name and
`smoke_absolute_time_range` names subcommands too, so the plain reads are
the taught route for both and their patterns stay narrow. Those two are
asserted to stay narrow rather than to accept the verb.

Run from repo root:
    pytest tests/scripts/test_insights_investigate_criteria.py
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS = REPO_ROOT / "tests" / "tasks" / "uipath-insights"

# The grader's own flag (coder_eval criteria/command_executed.py).
FLAGS = re.DOTALL

WINDOW = "--time-range 10080"
JSON = "--output json"
FOLDER_KEY = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# What each task's two routes actually type.
ROUTES = {
    "smoke_job_health_investigation.yaml": {
        "chain": [
            f"uip insights jobs summary {WINDOW} {JSON}",
            f"uip insights jobs top-failures {WINDOW} {JSON}",
            f"uip insights jobs failures-by-reason {WINDOW} {JSON}",
        ],
        # `investigate failing` reads top-failures and failures-by-reason
        # in one call, so two commands answer all three questions.
        "verb": [
            f"uip insights jobs investigate health {WINDOW} {JSON}",
            f"uip insights jobs investigate failing {WINDOW} {JSON}",
        ],
    },
    "smoke_critical_rules.yaml": {
        "chain": [f"uip insights jobs failures-by-reason --time-range 1440 {JSON}"],
        "verb": [f"uip insights jobs investigate failing --time-range 1440 {JSON}"],
    },
    "smoke_filtered_query.yaml": {
        "chain": [
            f'uip insights jobs summary --time-range 43200 --process-name "Invoice_Processing" --folder-key "{FOLDER_KEY}" {JSON}',
            f'uip insights jobs failures-by-reason --time-range 43200 --process-name "Invoice_Processing" --folder-key "{FOLDER_KEY}" {JSON}',
        ],
        "verb": [
            f'uip insights jobs investigate failing --time-range 43200 --process-name "Invoice_Processing" --folder-key "{FOLDER_KEY}" {JSON}',
            f'uip insights jobs investigate process --time-range 43200 --process-name "Invoice_Processing" --folder-key "{FOLDER_KEY}" {JSON}',
        ],
    },
}

# The out-of-scope requests smoke_critical_rules exists to catch, in both
# spellings. A negative that catches only the plain one is worse than
# none: it would pass a run that did the forbidden thing via the verb.
OUT_OF_SCOPE = {
    "start": [
        f"uip insights jobs start Invoice_Processing {JSON}",
        f"uip insights jobs investigate start Invoice_Processing {JSON}",
    ],
    "queue": [
        f"uip insights jobs summary --time-range 1440 --queue MyQueue {JSON}",
        f"uip insights jobs investigate failing --queue MyQueue {JSON}",
    ],
}

# Tasks whose prompt names the subcommands, so the plain reads are the
# taught route and the patterns must NOT accept a playbook.
NARROW_TASKS = ("smoke_all_commands.yaml", "smoke_absolute_time_range.yaml")


def _criteria(task_file):
    task = yaml.safe_load((TASKS / task_file).read_text())
    return task["success_criteria"]


def _command_patterns(task_file, criterion_type):
    return [
        crit
        for crit in _criteria(task_file)
        if crit["type"] == criterion_type and crit.get("command_pattern")
    ]


@pytest.mark.parametrize("task_file", sorted(ROUTES))
def test_each_positive_criterion_matches_both_routes(task_file):
    routes = ROUTES[task_file]
    for crit in _command_patterns(task_file, "command_executed"):
        regex = re.compile(crit["command_pattern"], FLAGS)
        need = crit.get("min_count", 1)
        for route_name, commands in routes.items():
            hits = sum(1 for command in commands if regex.search(command))
            assert hits >= need, (
                f"{task_file}: {crit['description']!r} matched {hits} of the "
                f"{route_name} route's commands, needs {need}. "
                f"Pattern: {crit['command_pattern']}"
            )


@pytest.mark.parametrize("task_file", sorted(ROUTES))
def test_no_criterion_uses_an_unbounded_wildcard(task_file):
    for criterion_type in ("command_executed", "command_not_executed"):
        for crit in _command_patterns(task_file, criterion_type):
            assert ".*" not in crit["command_pattern"], (
                f"{task_file}: {crit['description']!r} uses '.*'. The grader "
                "compiles with re.DOTALL, so it bleeds past the end of the "
                "command. Use '[^&;|\\n]*'."
            )


def test_negatives_catch_both_spellings_of_their_own_request():
    negatives = _command_patterns("smoke_critical_rules.yaml", "command_not_executed")
    assert len(negatives) == len(OUT_OF_SCOPE), (
        "One negative criterion per out-of-scope request; update OUT_OF_SCOPE "
        "when a request is added."
    )
    for key, commands in OUT_OF_SCOPE.items():
        owner = [n for n in negatives if key in n["command_pattern"]]
        assert owner, f"No negative criterion covers the {key!r} request."
        regex = re.compile(owner[0]["command_pattern"], FLAGS)
        for command in commands:
            assert regex.search(command), (
                f"The {key!r} negative misses {command!r}. A negative that "
                "misses a route would pass a run that did the forbidden "
                "thing through it."
            )


def test_negatives_do_not_fire_on_an_in_scope_command():
    routes = ROUTES["smoke_critical_rules.yaml"]
    in_scope = routes["chain"] + routes["verb"]
    for crit in _command_patterns("smoke_critical_rules.yaml", "command_not_executed"):
        regex = re.compile(crit["command_pattern"], FLAGS)
        for command in in_scope:
            assert not regex.search(command), (
                f"{crit['description']!r} fires on the in-scope command "
                f"{command!r}, so a correct run would fail the task."
            )


@pytest.mark.parametrize("task_file", NARROW_TASKS)
def test_subcommand_named_tasks_stay_narrow(task_file):
    """These prompts name subcommands, so a playbook must not satisfy them."""
    playbooks = [
        f"uip insights jobs investigate {name} {WINDOW} {JSON}"
        for name in ("health", "failing", "stuck", "compare")
    ]
    for crit in _command_patterns(task_file, "command_executed"):
        regex = re.compile(crit["command_pattern"], FLAGS)
        for command in playbooks:
            assert not regex.search(command), (
                f"{task_file}: {crit['description']!r} accepts {command!r}. "
                "This task asks for a named subcommand, so a playbook must "
                "not satisfy it."
            )
