"""The uipath-insights command criteria must grade the routes the skill teaches.

`uip insights jobs investigate <playbook>` runs the same reads the playbook
guide's chains do, so a task graded on "did the agent gather this evidence"
has to accept either spelling. These tests pin that, and pin the three things
that make such a criterion wrong:

  - a gap between two anchors that can run past the end of one command into a
    batched neighbour, or that stops at a backslash continuation;
  - a negative assertion that catches the plain read and misses the playbook,
    which passes a run that did the forbidden thing through the playbook;
  - a criterion carrying no pattern at all. The grader counts every Bash call
    for one of those, so it scores full marks whatever the agent did, and a
    misspelled `command_pattern` key is how that happens.

The fixtures are per task on purpose. Not every task routes at the verb:
`smoke_all_commands` asks for every subcommand by name, `smoke_absolute_time_range`
names two of them, and both e2e tasks grade one saved envelope per subcommand.
The plain reads are the taught route for those four, so their subcommand-named
criteria are asserted to reject a playbook while still accepting their own
reads. Their flag-graded criteria (the `--output json` advisories, and the two
epoch-flag criteria in `smoke_absolute_time_range`) name no subcommand, so a
playbook satisfying one of those is correct and they are checked for
acceptance only.

The grader is coder-eval, pinned in tests/.coder-eval-version. Two of its
behaviors shape this file. It matches a pattern against two haystacks per tool
call and counts a hit on either, so the haystack helpers below mirror it. It
counts telemetry records, one per tool call, so a batched Bash call carrying
three commands is one record however many of those commands match, and the
fixtures are lists of tool calls rather than lists of commands.

Run from repo root:
    pytest tests/tasks/uipath-insights/test_investigate_criteria.py
"""

import re
import shlex
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TASKS = REPO_ROOT / "tests" / "tasks" / "uipath-insights"

# Discovered, not listed: a task YAML added to this tree is governed the day it
# lands, and the classification test below fails until someone says which kind
# of task it is.
TASK_FILES = tuple(sorted(p.relative_to(TASKS).as_posix() for p in TASKS.rglob("*.yaml")))

# `command_not_executed` is a loader alias: coder_eval/models/tasks.py rewrites
# it to `command_executed` with `min_count: 0, max_count: 0` before validation,
# and the overlay overrides whatever counts the task supplied. Reading the raw
# YAML here means both spellings still have to be collected.
COMMAND_CRITERION_TYPES = ("command_executed", "command_not_executed")

# The grader's own flag: coder_eval/criteria/command_executed.py lines 236 and
# 295 compile every pattern with re.DOTALL.
FLAGS = re.DOTALL


# --- the grader's matching, mirrored ----------------------------------------
#
# Ported from coder_eval 0.12.1 (the version in tests/.coder-eval-version),
# file coder_eval/criteria/command_executed.py: _MAX_PATTERN_SEARCH_LEN at line
# 24, _is_shell_program at 27, _is_command_flag at 39, _normalize_shell at 53
# and _match_haystacks at 116. The CI job for these guards installs pytest and
# pyyaml only, so the grader cannot be imported; keeping the port in one block
# with its source named keeps the drift visible.

MAX_PATTERN_SEARCH_LEN = 2000


def _is_shell_program(arg0):
    return arg0.rsplit("/", 1)[-1].endswith("sh")


def _is_command_flag(tok):
    return len(tok) >= 2 and tok[0] == "-" and tok[1] != "-" and tok[1:].isalpha() and "c" in tok[1:]


def _normalize_shell(cmd_text):
    """Quote-resolved, wrapper-stripped form of a shell command, or None."""
    try:
        tokens = shlex.split(cmd_text, posix=True)
    except ValueError:
        return None
    if not tokens:
        return None
    if _is_shell_program(tokens[0]):
        for i in range(1, len(tokens) - 1):
            tok = tokens[i]
            if _is_command_flag(tok):
                rest = tokens[i + 1 :]
                if len(rest) == 1:
                    try:
                        tokens = shlex.split(rest[0], posix=True)
                    except ValueError:
                        return None
                else:
                    tokens = rest
                break
            if not tok.startswith("-"):
                break
    return " ".join(tokens)


def _match_haystacks(cmd_text):
    """The strings a pattern may match for one Bash call, raw first."""
    window = cmd_text[:MAX_PATTERN_SEARCH_LEN]
    haystacks = [window]
    normalized = _normalize_shell(window)
    if normalized is not None and normalized != window:
        haystacks.append(normalized)
    return haystacks


def _hits(regex, cmd_text):
    return any(regex.search(haystack) for haystack in _match_haystacks(cmd_text))


def _batched(commands):
    """One tool call's text. Agents chain reads in a single Bash call."""
    return " && ".join(commands)


def _matching_calls(pattern, calls):
    """How many tool calls this pattern matches, the way the grader counts."""
    regex = re.compile(pattern, FLAGS)
    return sum(1 for call in calls if _hits(regex, _batched(call)))


# --- how a command can be written -------------------------------------------

def _line_continued(command):
    """The same command with each flag after the first on a continued line.

    Agents write long commands this way, and it is the spelling a hand-rolled
    `[^&;|\\n]*` gap fails: the newline sits between the subcommand anchor and
    the flag the pattern is looking for, in the raw haystack and in the
    normalized one alike.
    """
    head, sep, rest = command.partition(" --")
    if not sep:
        return command
    return head + " --" + " \\\n  --".join(rest.split(" --"))


SPELLINGS = {"plain": lambda command: command, "continued": _line_continued}


# --- what the tasks ask for -------------------------------------------------

WINDOW_24H = "--time-range 1440"
WINDOW_7D = "--time-range 10080"
WINDOW_30D = "--time-range 43200"
EPOCH_RANGE = "--started-after 1751328000000 --started-before 1751673600000"

PROCESS = '"Invoice_Processing"'
FOLDER_KEY = '"a1b2c3d4-e5f6-7890-abcd-ef1234567890"'
FOLDER_NAME = '"Finance"'
FILTERS_30D = f"{WINDOW_30D} --process-name {PROCESS} --folder-key {FOLDER_KEY}"

# The seven plain reads.
PLAIN_SUBCOMMANDS = (
    "summary",
    "completed-timeline",
    "uncompleted-timeline",
    "top-failures",
    "failures-by-reason",
    "process-details",
    "failure-details",
)

# The six playbooks and the flag each one cannot run without, from the table in
# skills/uipath-insights/references/investigation-playbook-guide.md. One place:
# every playbook fixture in this file is built from this, so a playbook cannot
# be left out of a narrowness check by being left out of a list.
PLAYBOOKS = {
    "health": "",
    "failing": "",
    "process": f"--process-name {PROCESS}",
    "stuck": "",
    "compare": "",
    "folder": f"--folder-name {FOLDER_NAME}",
}


def _jobs(subcommand, *parts):
    pieces = ("uip insights jobs", subcommand, *(part for part in parts if part), "--output json")
    return " ".join(pieces)


def _saved(subcommand, window):
    """A plain read whose envelope is redirected to a file, as the e2e tasks ask."""
    return f"{_jobs(subcommand, window)} > {subcommand}.json"


def _playbook_calls(window):
    """One tool call per playbook, each carrying the flags that playbook needs."""
    return [[_jobs(f"investigate {name}", flag, window)] for name, flag in PLAYBOOKS.items()]


# Tasks whose prompt asks for evidence rather than for a named subcommand.
# Every command_executed criterion in these has to accept both routes.
ROUTE_TASKS = {
    "smoke_job_health_investigation.yaml": {
        "chain": [
            [_jobs("summary", WINDOW_7D)],
            [_jobs("top-failures", WINDOW_7D)],
            [_jobs("failures-by-reason", WINDOW_7D)],
        ],
        # `investigate failing` reads top-failures and failures-by-reason in one
        # call, so two calls answer all three of the prompt's questions.
        "verb": [
            [_jobs("investigate health", WINDOW_7D)],
            [_jobs("investigate failing", WINDOW_7D)],
        ],
    },
    "smoke_critical_rules.yaml": {
        "chain": [[_jobs("failures-by-reason", WINDOW_24H)]],
        "verb": [[_jobs("investigate failing", WINDOW_24H)]],
    },
    "smoke_filtered_query.yaml": {
        "chain": [
            [_jobs("summary", FILTERS_30D)],
            [_jobs("failures-by-reason", FILTERS_30D)],
        ],
        "verb": [
            [_jobs("investigate failing", FILTERS_30D)],
            [_jobs("investigate process", FILTERS_30D)],
        ],
    },
}

# Tasks whose prompt names subcommands. `window` is the time selection that
# task asks for, so its playbook fixtures differ from a flag the fixture simply
# forgot to carry.
NARROW_TASKS = {
    "smoke_all_commands.yaml": {
        "window": WINDOW_24H,
        "calls": [[_jobs(subcommand, WINDOW_24H)] for subcommand in PLAIN_SUBCOMMANDS],
    },
    "smoke_absolute_time_range.yaml": {
        "window": EPOCH_RANGE,
        "calls": [
            [_jobs("summary", EPOCH_RANGE)],
            [_jobs("completed-timeline", EPOCH_RANGE)],
        ],
    },
    "job-health/job_health_investigation_e2e.yaml": {
        "window": WINDOW_7D,
        "calls": [
            [_saved(subcommand, WINDOW_7D)]
            for subcommand in ("summary", "top-failures", "failures-by-reason", "failure-details")
        ],
    },
    "envelope-contract/all_commands_envelope_e2e.yaml": {
        "window": WINDOW_24H,
        "calls": [[_saved(subcommand, WINDOW_24H)] for subcommand in PLAIN_SUBCOMMANDS],
    },
}

# Tasks in this tree that grade the alerts, RBAC and filter-discovery command
# families. The jobs playbook does not run those reads, so the routing question
# does not arise for them. The pattern, count and advisory guards below still
# cover them.
OTHER_TASKS = (
    "alerts/smoke.yaml",
    "filters/smoke.yaml",
    "rbac/smoke.yaml",
)

# How many command criteria each task carries. Pinned so that deleting a gating
# criterion is a visible edit here and not a silently smaller suite: every
# other test in this file iterates whatever the YAML holds.
EXPECTED_COMMAND_CRITERIA = {
    "alerts/smoke.yaml": 10,
    "envelope-contract/all_commands_envelope_e2e.yaml": 8,
    "filters/smoke.yaml": 6,
    "job-health/job_health_investigation_e2e.yaml": 5,
    "rbac/smoke.yaml": 8,
    "smoke_absolute_time_range.yaml": 3,
    "smoke_all_commands.yaml": 7,
    "smoke_critical_rules.yaml": 3,
    "smoke_filtered_query.yaml": 3,
    "smoke_job_health_investigation.yaml": 4,
}

# The out-of-scope requests in smoke_critical_rules' prompt that carry a
# negative criterion, keyed on the description of the criterion that owns each.
# Keyed on the description and not on a substring of the pattern: "start" is a
# substring of both `--started-after` and `--start-time`, so a reworded pattern
# can hand ownership to the wrong criterion and the test then blames the wrong
# one. Request 4 (root-cause one job's error) has no negative criterion, so
# nothing grades it; that is a gap in the task rather than an invariant here.
OUT_OF_SCOPE = {
    "Agent did NOT run uip insights for starting a job (out of scope)": [
        _jobs("start", PROCESS),
        _jobs("investigate start", PROCESS),
    ],
    "Agent did NOT run uip insights jobs for queue metrics (not supported)": [
        _jobs("summary", WINDOW_24H, "--queue MyQueue"),
        _jobs("investigate failing", "--queue MyQueue"),
    ],
}


# --- gap forms --------------------------------------------------------------

# The two gap spellings approved for these tasks. Both keep a match inside one
# command and both survive a backslash continuation: the first by matching the
# continuation itself, the second by ending the gap at the next `uip`. The
# The first is the full bound and the one to reach for. Measured against the
# pinned grader, both halves carry weight: the `\n` in the class stops a
# batched neighbour on the raw haystack, the `(?!uip\s)` lookahead stops the
# next `uip ` on the normalized haystack where the newline is already gone, and
# the `\\\n` alternative keeps a backslash-continued command matching. The
# second and third are weaker forms still in use elsewhere in this directory:
# the insights e2e tasks drop the lookahead, and the alerts, RBAC and filter
# smokes drop line continuation, so a continued command false-fails there.
APPROVED_GAPS = (
    r"(?:(?!uip\s)(?:[^&;|\n]|\\\n))*",
    r"(?:[^&;|\n]|\\\n)*",
    r"(?:(?!uip\s)[^&;|])*",
)

# What ends one command inside a batched Bash call.
SEPARATORS = ("&", ";", "|", "\n")

# A quantifier that can consume more than one character. `?` and `{0,1}` are
# left alone: one character carries no match into the next command.
_OPEN_QUANTIFIER = r"(?:\*|\+|\{\d*,\}|\{\d*,(?:[2-9]|\d\d+)\})"

# A dot or a character class, with a preceding backslash excluded so an escaped
# literal is not read as an atom.
_WIDE_ATOM = re.compile(r"(?<!\\)(?P<atom>\.|\[(?:\\.|[^\]\\])*\])" + _OPEN_QUANTIFIER)


def _is_a_hand_rolled_gap(atom):
    """True when this atom, left open-ended, is a gap between two anchors.

    A negated class is one by construction: it stands for "anything except a
    few characters". This repo has two approved spellings for a gap, so a third
    one is reported even when it happens to exclude the separators, because the
    exclusion is what strands it at a backslash continuation. Any other atom is
    reported when it can match both a letter and a separator, which is what
    carries a match out of one command and into the next under re.DOTALL.
    """
    if atom.startswith("[^"):
        return True
    probe = re.compile(atom, FLAGS)
    return probe.fullmatch("a") is not None and any(probe.fullmatch(sep) for sep in SEPARATORS)


def _unapproved_gaps(pattern):
    """Gaps in `pattern` that are not one of the approved spellings.

    An allowlist rather than a ban on `.*`: `[\\s\\S]*`, `.+` and `.{0,200}`
    reproduce the same bleed in a spelling a ban on one literal never sees.
    """
    text = pattern
    for gap in APPROVED_GAPS:
        text = text.replace(gap, " ")
    return [match.group(0) for match in _WIDE_ATOM.finditer(text) if _is_a_hand_rolled_gap(match.group("atom"))]


# --- reading the tasks ------------------------------------------------------

def _criteria(task_file):
    task = yaml.safe_load((TASKS / task_file).read_text())
    return task["success_criteria"]


def _command_criteria(task_file, types=COMMAND_CRITERION_TYPES):
    """Every criterion of these types, whether or not it carries a pattern.

    No filter on `command_pattern` being truthy. A `command_executed` whose key
    is misspelled has no pattern, the grader then matches every Bash call for
    it, and the criterion scores full marks whatever the agent did. Filtering
    those out here is what would hide that case.
    """
    return [crit for crit in _criteria(task_file) if crit["type"] in types]


def _patterned(task_file, types=COMMAND_CRITERION_TYPES):
    """The same criteria, minus any with no pattern for the tests below to compile.

    Sound only because `test_every_command_criterion_carries_a_pattern` fails
    on a criterion that lands here without one.
    """
    return [crit for crit in _command_criteria(task_file, types) if crit.get("command_pattern")]


def _names_a_subcommand(pattern):
    """True when the pattern pins a plain read by name.

    A criterion that does not is grading a flag on whatever subcommand ran, so
    a playbook satisfying it is the right answer, not a leak.
    """
    return any(subcommand in pattern for subcommand in PLAIN_SUBCOMMANDS)


# --- the tasks are all accounted for ----------------------------------------

def test_every_task_file_is_classified():
    """A new task YAML in this tree lands here before it can go ungoverned."""
    classified = set(ROUTE_TASKS) | set(NARROW_TASKS) | set(OTHER_TASKS)
    assert classified == set(TASK_FILES), (
        "Classify every task YAML under tests/tasks/uipath-insights/ as a route "
        "task (both spellings must count), a narrow task (the prompt names "
        "subcommands) or an other-family task. Unclassified: "
        f"{sorted(set(TASK_FILES) - classified)}. Gone: {sorted(classified - set(TASK_FILES))}."
    )
    assert set(EXPECTED_COMMAND_CRITERIA) == set(TASK_FILES), (
        "EXPECTED_COMMAND_CRITERIA pins one count per task YAML; it is missing "
        f"{sorted(set(TASK_FILES) - set(EXPECTED_COMMAND_CRITERIA))} and still names "
        f"{sorted(set(EXPECTED_COMMAND_CRITERIA) - set(TASK_FILES))}."
    )


@pytest.mark.parametrize("task_file", TASK_FILES)
def test_command_criterion_count_is_pinned(task_file):
    """Deleting a gating criterion changes the score, so it must change a test."""
    found = len(_command_criteria(task_file))
    assert found == EXPECTED_COMMAND_CRITERIA[task_file], (
        f"{task_file} carries {found} command criteria, expected "
        f"{EXPECTED_COMMAND_CRITERIA[task_file]}. Every other test here iterates "
        "whatever the file holds, so a deletion is invisible without this count."
    )


@pytest.mark.parametrize("task_file", TASK_FILES)
def test_every_command_criterion_carries_a_pattern(task_file):
    criteria = _command_criteria(task_file)
    assert criteria, f"{task_file}: no command criteria found, so the guards below grade nothing."
    for crit in criteria:
        assert crit.get("command_pattern"), (
            f"{task_file}: {crit['description']!r} is a {crit['type']} with no "
            "command_pattern (a misspelled key reads exactly like this). The "
            "grader matches every Bash call for a pattern-less criterion, so it "
            "passes on any run at all."
        )


# --- gaps between anchors ---------------------------------------------------

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_gaps_between_anchors_use_an_approved_form(task_file):
    criteria = _patterned(task_file)
    assert criteria, f"{task_file}: no command pattern to check."
    for crit in criteria:
        unapproved = _unapproved_gaps(crit["command_pattern"])
        assert not unapproved, (
            f"{task_file}: {crit['description']!r} spells its gap {unapproved!r}. "
            "The grader compiles with re.DOTALL and matches the raw text of one "
            "tool call, so a hand-rolled gap either runs past the end of the "
            "command into a batched neighbour or stops dead at a backslash "
            f"continuation. Use one of: {', '.join(APPROVED_GAPS)}. "
            f"Pattern: {crit['command_pattern']}"
        )


@pytest.mark.parametrize("gap", (".*", ".+", ".{0,200}", r"[\s\S]*", r"[^&;|\n]*", r"[\s\S]{2,}"))
def test_the_gap_guard_rejects_every_spelling_of_a_wildcard(gap):
    """The guard is an allowlist, so it is not dodged by respelling `.*`."""
    assert _unapproved_gaps(rf"uip\s+insights\s+jobs\s+summary\s{gap}--time-range")


@pytest.mark.parametrize("gap", APPROVED_GAPS)
def test_the_gap_guard_accepts_the_approved_forms(gap):
    assert not _unapproved_gaps(rf"uip\s+insights\s+jobs\s+summary\s{gap}--time-range")


@pytest.mark.parametrize("atom", (r"\S+", r"\d{13}", r"[\s=]+", ".?", '"?'))
def test_the_gap_guard_leaves_narrow_atoms_alone(atom):
    """None of these can carry a match from one command into the next."""
    assert not _unapproved_gaps(rf"uip\s+insights\s+jobs\s+{atom}summary")


# --- both routes ------------------------------------------------------------

@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
@pytest.mark.parametrize("task_file", sorted(ROUTE_TASKS))
def test_route_tasks_accept_both_routes(task_file, spelling):
    write = SPELLINGS[spelling]
    criteria = _patterned(task_file, ("command_executed",))
    assert criteria, f"{task_file}: no command_executed criterion, so no route is graded."
    for crit in criteria:
        need = crit.get("min_count", 1)
        for route, calls in ROUTE_TASKS[task_file].items():
            written = [[write(command) for command in call] for call in calls]
            matched = _matching_calls(crit["command_pattern"], written)
            assert matched >= need, (
                f"{task_file}: {crit['description']!r} matched {matched} of the "
                f"{route} route's {spelling} tool calls, needs {need}. Both routes "
                "gather the same evidence, so a criterion that counts one and not "
                f"the other penalizes a correct run. Pattern: {crit['command_pattern']}"
            )


# --- the tasks that name their subcommands ----------------------------------

@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
@pytest.mark.parametrize("task_file", sorted(NARROW_TASKS))
def test_narrow_tasks_accept_their_own_reads(task_file, spelling):
    """Rejecting a playbook is half the job; the criterion has to still fire.

    Without this, renaming a subcommand in one of these patterns to something
    no command can produce leaves the task green and grades nothing.
    """
    write = SPELLINGS[spelling]
    criteria = _patterned(task_file, ("command_executed",))
    assert criteria, f"{task_file}: no command_executed criterion to check."
    calls = [[write(command) for command in call] for call in NARROW_TASKS[task_file]["calls"]]
    for crit in criteria:
        need = crit.get("min_count", 1)
        matched = _matching_calls(crit["command_pattern"], calls)
        assert matched >= need, (
            f"{task_file}: {crit['description']!r} matched {matched} of the "
            f"{spelling} plain reads this task asks for, needs {need}. "
            f"Pattern: {crit['command_pattern']}"
        )


@pytest.mark.parametrize("task_file", sorted(NARROW_TASKS))
def test_narrow_tasks_reject_a_playbook(task_file):
    """A criterion naming a subcommand must not be satisfied by a playbook.

    The playbook fixtures carry the window this task asks for and the flag each
    playbook needs, so a rejection here is about the subcommand.
    """
    calls = _playbook_calls(NARROW_TASKS[task_file]["window"])
    named = [
        crit
        for crit in _patterned(task_file, ("command_executed",))
        if _names_a_subcommand(crit["command_pattern"])
    ]
    assert named, f"{task_file}: no criterion names a plain read, so nothing here is narrow."
    for crit in named:
        matched = _matching_calls(crit["command_pattern"], calls)
        assert matched == 0, (
            f"{task_file}: {crit['description']!r} accepts a playbook "
            f"({matched} of {len(calls)} matched). This task asks for a named "
            f"subcommand. Pattern: {crit['command_pattern']}"
        )


# --- the negatives ----------------------------------------------------------

def test_each_out_of_scope_request_has_exactly_one_negative():
    negatives = _command_criteria("smoke_critical_rules.yaml", ("command_not_executed",))
    assert negatives, "smoke_critical_rules exists to catch out-of-scope requests and has no negative."
    owners = [crit["description"] for crit in negatives]
    assert len(set(owners)) == len(owners), f"Two negatives share a description, so ownership is ambiguous: {owners}"
    assert set(owners) == set(OUT_OF_SCOPE), (
        "Every negative in smoke_critical_rules grades one out-of-scope request "
        "and OUT_OF_SCOPE names each by description. Unowned negatives: "
        f"{sorted(set(owners) - set(OUT_OF_SCOPE))}. Requests with no negative "
        f"left: {sorted(set(OUT_OF_SCOPE) - set(owners))}."
    )


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_negatives_catch_both_spellings_of_their_own_request(spelling):
    write = SPELLINGS[spelling]
    negatives = _patterned("smoke_critical_rules.yaml", ("command_not_executed",))
    assert negatives, "No negative pattern to check."
    for crit in negatives:
        assert crit["description"] in OUT_OF_SCOPE, (
            f"{crit['description']!r} grades no request named in OUT_OF_SCOPE."
        )
        regex = re.compile(crit["command_pattern"], FLAGS)
        for command in OUT_OF_SCOPE[crit["description"]]:
            assert _hits(regex, write(command)), (
                f"{crit['description']!r} misses the {spelling} spelling "
                f"{write(command)!r}. A negative that misses a route passes a run "
                "that did the forbidden thing through it. "
                f"Pattern: {crit['command_pattern']}"
            )


def test_negatives_do_not_fire_on_an_in_scope_call():
    """A negative that fires on the in-scope read fails a correct run.

    Checked on the raw haystack and the normalized one, on the read alone and
    on the read batched with an out-of-scope neighbour through `&&`, which is
    where the `&` in the bound does its work. A newline batch is left out on
    purpose: normalization joins tokens with spaces, so the `\\n` in the bound
    is gone from the second haystack and an innocent neighbour trips the queue
    negative. Every `[^&;|\\n]`-bounded negative in this repo has that hole, so
    it is a convention to settle across the task suite rather than something
    these two patterns can fix alone.
    """
    routes = ROUTE_TASKS["smoke_critical_rules.yaml"]
    in_scope = [command for call in (*routes["chain"], *routes["verb"]) for command in call]
    neighbour = "uip orchestrator queues list --output json"
    calls = [[command] for command in in_scope] + [[command, neighbour] for command in in_scope]
    negatives = _patterned("smoke_critical_rules.yaml", ("command_not_executed",))
    assert negatives, "No negative pattern to check."
    for crit in negatives:
        regex = re.compile(crit["command_pattern"], FLAGS)
        for call in calls:
            text = _batched(call)
            for haystack in _match_haystacks(text):
                assert not regex.search(haystack), (
                    f"{crit['description']!r} fires on the in-scope call {text!r} "
                    f"(haystack {haystack!r}), so a correct run loses the points. "
                    f"Pattern: {crit['command_pattern']}"
                )


# --- the --output json rule -------------------------------------------------

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_output_json_criteria_stay_advisory(task_file):
    """.claude/rules/test-writing.md bans a gating check on --output json.

    The flag is outcome-invisible and often the default, so requiring it docks
    an agent that reached the same answer without typing it. `pass_threshold: 0`
    records the convention without gating on it.
    """
    for crit in _patterned(task_file, ("command_executed",)):
        if "--output" not in crit["command_pattern"]:
            continue
        assert crit.get("pass_threshold") == 0, (
            f"{task_file}: {crit['description']!r} requires --output json with "
            f"pass_threshold {crit.get('pass_threshold')!r}. Keep it advisory "
            "(pass_threshold: 0)."
        )
