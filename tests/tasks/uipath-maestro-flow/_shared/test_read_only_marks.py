"""`read_only: true` reruns a criterion, unscored, in a half-built sandbox after a
crash or a turn timeout, and coder_eval does not verify the claim. A grader that
calls `flow validate` or `run_debug` there hits the tenant or rewrites the
`.uipx`. So the mark is allowed only on a reviewed pure reader: a new checker is
added here on purpose, never inherited by copying a marked block.
"""

from __future__ import annotations

import os
import re
import shlex

import pytest

_SUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PURE_READERS = {
    "_shared/flow_contains.py",
    "_shared/project_profile.py",
    "_shared/check_simulated_hitl.py",
    "_shared/check_inline_agent.py",
    "_shared/check_escalation_behavior.py",
    "smoke/check_merge_parallel_sync_flow.py",
    "smoke/check_scheduled_trigger_flow.py",
    "ixp/check_project_selection.py",
    "interactive/check_solution_select.py",
}
# Modes of an allowed reader that leave the sandbox: `validate` calls the tenant.
WRITING_MODES = {"interactive/check_solution_select.py": {"validate"}}
SUBSTITUTIONS = ("$(", "`")
SCRIPT_PREFIX = "$REFERENCE_DIR/"


def _has_shell_operator(command: str) -> bool:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return any(token and set(token) <= set(lexer.punctuation_chars) for token in lexer)


def _is_recursive_flag(arg: str) -> bool:
    if arg in ("--recursive", "--dereference-recursive"):
        return True
    return arg.startswith("-") and not arg.startswith("--") and bool(set(arg[1:]) & {"r", "R"})


def _refusal(command: str) -> str | None:
    """Why this command may not carry `read_only`, or None when it may."""
    if any(s in command for s in SUBSTITUTIONS) or _has_shell_operator(command):
        return "chains, redirects or substitutes shell commands"

    argv = shlex.split(command)
    if not argv:
        return "is empty"

    if argv[0] == "grep":
        recursive = any(_is_recursive_flag(a) for a in argv[1:])
        return None if recursive else "is a grep without -r"

    if argv[0] != "python3" or len(argv) < 2 or not argv[1].startswith(SCRIPT_PREFIX):
        return "is neither a reviewed checker nor a plain grep -r"
    script = argv[1][len(SCRIPT_PREFIX):]
    if script not in PURE_READERS:
        return f"runs {script}, which is not a reviewed pure reader"
    modes = WRITING_MODES.get(script, set()).intersection(argv[2:])
    if modes:
        return f"runs {script} in its {min(modes)} mode, which leaves the sandbox"
    return None


# Regex, not PyYAML: CI installs only pytest (see test_criterion_budgets.py).
_CRITERION_SPLIT = re.compile(r"\n\s*-\s+type:\s*")
_TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][\w-]*:", re.M)
_READ_ONLY = re.compile(r"^\s*read_only:\s*(?i:true)\s*(#.*)?$", re.M)
_COMMAND = re.compile(r"^([ \t]*)command:[ \t]*(.*)$", re.M)
_BLOCK_SCALAR = re.compile(r"[>|][+-]?")


def _quoted(text: str) -> str:
    quote, out, i = text[0], [], 1
    while i < len(text):
        char = text[i]
        if quote == '"' and char == "\\":
            out.append(text[i + 1])
            i += 2
            continue
        if char == quote:
            if quote == "'" and text[i + 1 : i + 2] == "'":
                out.append("'")
                i += 2
                continue
            return "".join(out)
        out.append(char)
        i += 1
    raise ValueError(f"unterminated {quote}-quoted command: {text}")


def _command(block: str) -> str:
    found = _COMMAND.search(block)
    if not found:
        return ""
    indent, rest = len(found.group(1)), found.group(2).strip()
    if rest[:1] in ("'", '"'):
        return _quoted(rest)
    if not _BLOCK_SCALAR.fullmatch(rest):
        return rest
    lines = []
    for line in block[found.end() :].splitlines()[1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        lines.append(line.strip())
    return " ".join(lines)


def _marked_criteria():
    for directory, _, names in sorted(os.walk(_SUITE_ROOT)):
        for name in sorted(names):
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(directory, name)
            text = open(path).read()
            blocks = _CRITERION_SPLIT.split("\n" + text)[1:]
            for index, block in enumerate(blocks):
                stop = _TOP_LEVEL_KEY.search(block)
                block = block[: stop.start()] if stop else block
                if _READ_ONLY.search(block):
                    rel = os.path.relpath(path, _SUITE_ROOT)
                    kind = block.split(None, 1)[0].strip("\"'")
                    yield f"{rel}#{index}", kind, " ".join(_command(block).split())


MARKED = list(_marked_criteria())


def test_the_corpus_has_marks():
    assert MARKED, "no read_only criteria found; the split or the key changed"


@pytest.mark.parametrize(("where", "kind", "command"), MARKED, ids=[w for w, _, _ in MARKED])
def test_read_only_runs_only_a_reviewed_reader(where, kind, command):
    assert kind == "run_command", f"{where}: read_only on a {kind}"
    reason = _refusal(command)
    assert reason is None, f"{where}: read_only command {reason}: {command}"


@pytest.mark.parametrize(
    "command",
    [
        "python3 $REFERENCE_DIR/_shared/validate_flow.py",
        "python3 $REFERENCE_DIR/hitl/check_weather_flow_simulated.py",
        "python3 $REFERENCE_DIR/interactive/check_solution_select.py validate",
        "python3 $REFERENCE_DIR/interactive/check_solution_select.py --verbose validate",
        'grep --regexp="x" f.flow',
        "python3 $REFERENCE_DIR/_shared/flow_contains.py x && uip maestro flow validate f.flow",
        "uip maestro flow validate f.flow --output json",
        'grep -q "x" f.flow',
    ],
)
def test_refuses_a_command_that_leaves_the_sandbox(command):
    assert _refusal(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "python3 $REFERENCE_DIR/_shared/flow_contains.py --flow-name X",
        'python3 "$REFERENCE_DIR/_shared/check_inline_agent.py" --mode a',
        "python3 $REFERENCE_DIR/interactive/check_solution_select.py flow",
        'grep -rqE "core\\.action\\.http|x" --include="*.flow" .',
        'grep -qiR "x" --include="*.flow" .',
    ],
)
def test_accepts_a_reviewed_reader(command):
    assert _refusal(command) is None
