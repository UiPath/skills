"""Control matrix for the `command_executed` segment-scoping guard.

The guard restricts a lookahead to "the rest of THIS command" so a Bash call
that batches two commands grades per command. It must do that WITHOUT dying at
a backslash line continuation — coder_eval's shlex normalization re-emits
`\\` + newline as a bare `'\\n'` token, so a guard that stops at any newline
zeroes every multi-line command in both haystacks.

Each control is graded in a single-line AND a multi-line shape through a copy
of coder_eval's haystack matching, then compared against the outcome the task
author intended.

Run from repo root:
    pytest tests/scripts/test_command_pattern_segment_guard.py
"""

import re
import shlex
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACES_TASKS = REPO_ROOT / "tests" / "tasks" / "uipath-platform" / "traces"
FILTERS_TASK = TRACES_TASKS / "traces_feedback_list_filters_smoke.yaml"
DETAILED_TASK = TRACES_TASKS / "traces_feedback_list_detailed_smoke.yaml"


# --- Faithful copy of coder_eval's matching surface -------------------------
# Mirrors coder_eval 0.11.5 `criteria/command_executed.py` (`_normalize_shell`,
# `_match_haystacks`, and the `re.DOTALL` compile). Copied rather than imported
# because coder_eval is not a dependency of this pytest job.

_MAX_PATTERN_SEARCH_LEN = 2000


def _is_shell_program(arg0: str) -> bool:
    return arg0.rsplit("/", 1)[-1].endswith("sh")


def _is_command_flag(tok: str) -> bool:
    return len(tok) >= 2 and tok[0] == "-" and tok[1] != "-" and tok[1:].isalpha() and "c" in tok[1:]


def _normalize_shell(cmd_text: str) -> str | None:
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


def _match_haystacks(cmd_text: str) -> list[str]:
    window = cmd_text[:_MAX_PATTERN_SEARCH_LEN]
    haystacks = [window]
    normalized = _normalize_shell(window)
    if normalized is not None and normalized != window:
        haystacks.append(normalized)
    return haystacks


# --- Guards under test ------------------------------------------------------

GUARD_SHIPPED = r"(?:(?!&&|\|\||;|\||\s(?:uip|\$UIP)\s)[\s\S])*"
GUARD_NEWLINE_STOP = r"(?:(?!\n|&&|\|\||;|\||\s(?:uip|\$UIP)\s).)*"
GUARD_ESCAPED_NEWLINE_STOP = r"(?:(?!(?<!\\)\n|&&|\|\||;|\||\s(?:uip|\$UIP)\s).)*"

# The three `command_pattern` regexes of skill-platform-traces-feedback-list-filters,
# with the segment guard left as `{S}` so the same criteria can be replayed
# against any candidate guard.
CRITERIA = {
    "c1": r"(uip|\$UIP)\s+traces\s+feedback\s+list(?!\s+detailed)(?={S}--span-id)(?!{S}--agent-id)",
    "c2": (
        r"(uip|\$UIP)\s+traces\s+feedback\s+list(?:\s+detailed)?"
        r"(?={S}--negative)(?={S}--agent-id)(?={S}--agent-version)"
    ),
    "c3": (
        r"(uip|\$UIP)\s+traces\s+feedback\s+list(?:\s+detailed)?"
        r"(?={S}--negative)(?={S}--limit[\s=]5(?:\s|$))(?={S}--offset[\s=]5(?:\s|$))"
    ),
}


# --- Control matrix ---------------------------------------------------------
# `{B}` marks a place the agent may break the line. The single-line shape
# renders it as a space, the multi-line shape as a backslash continuation.

FOLDER = "2f6c8a41-93bd-4d17-8e55-6a0b7c19d3e2"
TRACE = "7d3a91e0f5c24b8ea0c6d219bb47f0a3"
SPAN = "b7e41c93a05d2f68"
AGENT = "c41d7b62-05ae-4f39-9a18-73e2b6d4c08f"

SPAN_READ = f"uip traces feedback list --folder-key {FOLDER}{{B}}--trace-id {TRACE}{{B}}--span-id {SPAN}"
SPAN_READ_DETAILED = (
    f"uip traces feedback list detailed --folder-key {FOLDER}{{B}}--trace-id {TRACE}{{B}}--span-id {SPAN}"
)


def _paged_read(offset: int) -> str:
    return (
        f"uip traces feedback list --folder-key {FOLDER}{{B}}--agent-id {AGENT}"
        f"{{B}}--agent-version 2.4.0{{B}}--negative{{B}}--limit 5{{B}}--offset {offset}"
    )


MERGED = (
    f"uip traces feedback list --folder-key {FOLDER}{{B}}--trace-id {TRACE}{{B}}--span-id {SPAN}"
    f"{{B}}--agent-id {AGENT}{{B}}--agent-version 2.4.0{{B}}--negative{{B}}--limit 5{{B}}--offset 5"
)
# Same merged command, but the only break sits between the two flags c1 plays
# off against each other — the shape a `(?<!\\)\n` guard mis-splits.
MERGED_BREAK_BETWEEN_FLAGS = (
    f"uip traces feedback list --folder-key {FOLDER} --trace-id {TRACE} --span-id {SPAN}"
    f"{{B}}--agent-id {AGENT} --agent-version 2.4.0 --negative --limit 5 --offset 5"
)

CONTROLS = {
    "A-correct-two-calls": ([SPAN_READ, _paged_read(5)], {"c1": True, "c2": True, "c3": True}),
    "B-merged-one-command": ([MERGED], {"c1": False, "c2": True, "c3": True}),
    "B2-merged-break-between-flags": ([MERGED_BREAK_BETWEEN_FLAGS], {"c1": False, "c2": True, "c3": True}),
    "C-offset-as-page-number": ([SPAN_READ, _paged_read(10)], {"c1": True, "c2": True, "c3": False}),
    "D-span-read-via-list-detailed": ([SPAN_READ_DETAILED, _paged_read(5)], {"c1": False, "c2": True, "c3": True}),
    "E-two-reads-chained-with-and": ([f"{SPAN_READ} && {_paged_read(5)}"], {"c1": True, "c2": True, "c3": True}),
    "F-two-reads-stacked-on-lines": ([f"{SPAN_READ}\n{_paged_read(5)}"], {"c1": True, "c2": True, "c3": True}),
}

SHAPES = {"single-line": " ", "multi-line": " \\\n  "}


def _render(calls: list[str], shape: str) -> list[str]:
    return [call.replace("{B}", SHAPES[shape]) for call in calls]


def _grade(calls: list[str], guard: str) -> dict[str, bool]:
    graded = {}
    for name, template in CRITERIA.items():
        pattern = re.compile(template.format(S=guard), re.DOTALL)
        graded[name] = any(pattern.search(hay) for call in calls for hay in _match_haystacks(call))
    return graded


def _mismatching_cells(guard: str) -> list[str]:
    bad = []
    for shape in SHAPES:
        for control, (calls, expected) in CONTROLS.items():
            if _grade(_render(calls, shape), guard) != expected:
                bad.append(f"{control}/{shape}")
    return bad


# --- The shipped patterns are the ones under test ---------------------------


def _command_patterns(task_path: Path) -> list[str]:
    task = yaml.safe_load(task_path.read_text())
    return [c["command_pattern"] for c in task["success_criteria"] if c["type"] == "command_executed"]


@pytest.mark.parametrize("task_path", [FILTERS_TASK, DETAILED_TASK], ids=lambda p: p.name)
def test_shipped_guard_never_stops_at_a_newline(task_path):
    """Every segment guard in the traces tasks uses the continuation-safe form."""
    for pattern in _command_patterns(task_path):
        assert GUARD_NEWLINE_STOP not in pattern, (
            f"{task_path.name} re-introduced the newline-terminated segment guard. "
            "It zeroes every backslash-continued command — see tests/README.md."
        )
        assert GUARD_ESCAPED_NEWLINE_STOP not in pattern, (
            f"{task_path.name} uses the `(?<!\\\\)\\n` guard variant. It repairs the raw "
            "haystack but mis-splits the shlex-normalized one (control B2)."
        )


def test_filters_criteria_match_the_replayed_templates():
    """The replay templates are the shipped regexes, not a drifted copy."""
    expected = [template.format(S=GUARD_SHIPPED) for template in CRITERIA.values()]
    assert _command_patterns(FILTERS_TASK) == expected


@pytest.mark.parametrize("shape", list(SHAPES))
@pytest.mark.parametrize("control", list(CONTROLS))
def test_shipped_guard_grades_control_as_intended(control, shape):
    calls, expected = CONTROLS[control]
    assert _grade(_render(calls, shape), GUARD_SHIPPED) == expected


def test_newline_stop_guard_zeroes_every_multi_line_shape():
    """Regression record: the guard PR #2836 shipped fails all 7 multi-line controls."""
    assert _mismatching_cells(GUARD_NEWLINE_STOP) == [f"{control}/multi-line" for control in CONTROLS]


def test_escaped_newline_guard_still_mis_splits_a_merged_command():
    r"""Regression record: `(?<!\\)\n` is not enough — the normalized haystack has a bare newline."""
    assert _mismatching_cells(GUARD_ESCAPED_NEWLINE_STOP) == ["B2-merged-break-between-flags/multi-line"]
