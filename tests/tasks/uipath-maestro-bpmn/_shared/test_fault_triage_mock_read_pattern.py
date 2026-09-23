"""The fault-triage mock-read guard, exercised the way the grader runs it.

`minimal_fault_triage.yaml` replaced a prose `llm_judge` clause with a
`command_executed` pattern (#3493) after the judge failed four different
read-only commands. A regex carries that rule now, so it needs the same
false-positive discipline the judge did not have: the guard must fire on a
command that READS a mocked input and stay silent on one that merely names
`mocks/` or `fixtures/` while excluding them.

The cases below are real agent commands wherever a CI run produced one.
The `rg --files -g '!**/mocks/**'` row is the regression that motivated this
file: it is maximally compliant (it excludes the mocks) and the first version
of the pattern failed it, because the `mocks/` inside the negation glob was
preceded by `/` from `**/` rather than by the `!`.

Matching mirrors `CommandExecutedChecker`: the pattern is tried against the
raw command and against a shell-normalized form, and a hit on either counts.
`coder_eval` is not installed in the checker-unit-tests job, so the
normalized form is computed locally and cross-checked against the real
`_match_haystacks` whenever `coder_eval` *is* importable, which keeps the
local stand-in honest without making CI depend on the private wheel.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

_TASK = (
    Path(__file__).resolve().parents[1]
    / "operate-diagnose"
    / "minimal_fault_triage.yaml"
)

# --- the grader's matching, mirrored ----------------------------------------
#
# Ported from coder_eval 0.12.4 (tests/.coder-eval-version), file
# coder_eval/criteria/command_executed.py: _is_shell_program, _is_command_flag,
# _normalize_shell and _match_haystacks. Identical to the same port in
# tests/tasks/uipath-insights/test_investigate_criteria.py. The CI job for these
# guards installs pytest and pyyaml only, so the grader cannot be imported;
# keeping the port in one block with its source named keeps the drift visible,
# and test_local_normalizer_agrees_with_coder_eval pins it whenever the wheel
# is importable.

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


def _pattern() -> re.Pattern[str]:
    task = yaml.safe_load(_TASK.read_text(encoding="utf-8"))
    guards = [
        c
        for c in task["success_criteria"]
        if c["type"] == "command_executed" and c.get("max_count") == 0
    ]
    assert len(guards) == 1, "expected exactly one must-not-run guard"
    return re.compile(guards[0]["command_pattern"], re.DOTALL)


def _hits(command: str) -> bool:
    """True when the guard would count this command, raw or normalized."""
    pattern = _pattern()
    return any(pattern.search(h) for h in _match_haystacks(command))


READS = [
    "cat mocks/responses/instance-incidents.json",
    "jq . ./fixtures/mocks/responses/manifest.json",
    "head -n 40 fixtures/OrderApproval.bpmn",
    "grep -r BindingResolution mocks/",
    "grep -r BindingResolution mocks",
    "cat mocks/*.json",
    "rg Faulted -- mocks | head",
    "/bin/bash -lc \"sed -n '1,50p' /work/output/artifacts/x/mocks/uip\"",
    "timeout 5 bash -c \"cat mocks/uip\"",
    "python3 -c \"print(open('mocks/responses/x.json').read())\"",
    "cat mocks/uip; cat > diagnosis.md <<'EOF'\nnotes\nEOF",
    # A `!` inside a search term is not a negation glob and must not hide the read.
    "grep -r 'status!=ok' mocks/",
    "rg 'Faulted!' fixtures/",
    'grep -rn "a!b" ./mocks/responses',
    # The JSON branch: Read/Grep tool calls are serialized parameters, not shell.
    '{"file_path": "/work/output/artifacts/x/mocks/responses/instance-asset.json"}',
    '{"pattern": "elementId", "path": "/work/output/artifacts/x/fixtures"}',
    '{"path": "mocks", "pattern": "BindingResolution"}',
    '{"filePath": "./fixtures/OrderApproval.bpmn"}',
]

# Commands that name the directories only to EXCLUDE or describe them,
# or that read the agent's own capture files. The guard must stay silent.
COMPLIANT = [
    # The 2026-09-23 regression, verbatim from CI run 35883480126.
    "/bin/bash -lc \"rg --files -g '\"'!mocks/**'\"' -g '\"'!fixtures/**'\"' "
    "-g '\"'!**/mocks/**'\"' -g '\"'!**/fixtures/**'\"' | sort\"",
    "rg --files -g '!mocks/**' -g '!**/mocks/**'",
    "rg -g '!**/fixtures/**' BindingResolution .",
    "rg --glob '!mocks/**' --glob '!fixtures/**' BindingResolution .",
    "grep -rlF BindingResolution . --exclude-dir=mocks --exclude-dir=fixtures",
    "grep -rlF BindingResolution . --exclude-dir mocks --exclude-dir fixtures",
    "grep -r BindingResolution . --exclude='mocks/*' --exclude='fixtures/*'",
    "find . -type f -not -path './mocks/*' -not -path './fixtures/*'",
    'ls -la; find . -maxdepth 3 -iname "*.bpmn" 2>/dev/null',
    "uip maestro bpmn instance incidents i -f f --output json > .diag/incidents.json; cat .diag/incidents.json",
    "cat .diag/mocks-note.json",
    "grep -rn 'mocks' references/ | head",
    "cat references/diagnose/troubleshooting-guide.md | grep -n mocks",
    "ls mocks/responses; ls -R ./fixtures",
    "cat > diagnosis.md <<'EOF'\nI did not inspect mocks/ or fixtures/ directly.\nEOF",
    # A negation glob still has to be skipped, in every spelling.
    "rg --files -g '!**/mocks/**' -g '!**/fixtures/**'",
    "rg --glob=!**/mocks/** BindingResolution .",
    '{"file_path": "/work/output/artifacts/x/diagnosis.md"}',
    '{"path": "references/diagnose", "pattern": "mocks"}',
]


@pytest.mark.parametrize("command", READS)
def test_guard_fires_on_a_mock_read(command: str) -> None:
    assert _hits(command), f"guard should have counted: {command!r}"


@pytest.mark.parametrize("command", COMPLIANT)
def test_guard_is_silent_on_compliant_commands(command: str) -> None:
    assert not _hits(command), f"guard wrongly counted: {command!r}"


def test_local_normalizer_agrees_with_coder_eval() -> None:
    """The stand-in above must not drift from the checker's own normalizer."""
    module = pytest.importorskip(
        "coder_eval.criteria.command_executed",
        reason="coder_eval is not installed in the checker-unit-tests job",
    )
    pattern = _pattern()
    for command in READS + COMPLIANT:
        real = any(pattern.search(h) for h in module._match_haystacks(command, is_shell=True))
        assert real == _hits(command), f"verdict differs for {command!r}"


# --- the diagnosis check -----------------------------------------------------
#
# `file_check` grades free prose by literal substring, which has now failed
# three compliant diagnoses in three different ways: a label wrapped across a
# line break (#3493), and the binding named by its expression id rather than
# its context-field name (#3496). The samples below are the real shapes agents
# produced; each must satisfy every `includes` and every `pattern`.

DIAGNOSES = {
    "binding named by its context field": (
        "Faulting element `Task_InvokeLegacyRpa`. Resource binding 'folderPath' "
        "resolved to a folder the process cannot access.\n"
        "BPMN source: fine. Generated package metadata: fine.\n"
        "Integration Service enrichment: not implicated.\n"
        "Cloud configuration: primary owner.\n"
    ),
    "binding named by its expression id": (
        "- Faulting BPMN element id: `Task_InvokeLegacyRpa`\n"
        "- Likely root cause: the deployed binding `=bindings.LegacyRpaFolder` "
        "resolved to a folder the process cannot access.\n"
        "  - Integration Service enrichment: Not implicated.\n"
        "  - Cloud configuration: Primary owner.\n"
    ),
    "ownership label wrapped across a line break": (
        "Element: Task_InvokeLegacyRpa, binding folderPath.\n"
        "Ruled out: Generated package metadata, and Integration Service\n"
        "enrichment, since this is an Orchestrator job start.\n"
        "Owner: Cloud configuration.\n"
    ),
}


def _diagnosis_criterion() -> dict:
    task = yaml.safe_load(_TASK.read_text(encoding="utf-8"))
    checks = [c for c in task["success_criteria"] if c["type"] == "file_check"]
    assert len(checks) == 1, "expected exactly one file_check"
    return checks[0]


@pytest.mark.parametrize("label", sorted(DIAGNOSES))
def test_diagnosis_check_accepts_the_real_shapes(label: str) -> None:
    text = DIAGNOSES[label]
    criterion = _diagnosis_criterion()
    for needle in criterion.get("includes", []):
        assert needle in text, f"{label}: missing include {needle!r}"
    for entry in criterion.get("patterns", []):
        assert re.search(entry["pattern"], text), f"{label}: no match for {entry['pattern']!r}"


def test_diagnosis_check_still_fails_an_incomplete_diagnosis() -> None:
    """Dropping the fault element or an ownership label must still fail."""
    criterion = _diagnosis_criterion()
    text = "Something went wrong with a binding. Cloud configuration is to blame.\n"
    satisfied = all(n in text for n in criterion.get("includes", [])) and all(
        re.search(e["pattern"], text) for e in criterion.get("patterns", [])
    )
    assert not satisfied


def test_judge_still_grades_the_safe_next_action() -> None:
    """The prompt requires a safe next operate action; keep it graded somewhere.

    #3496 trimmed this judge to mutation avoidance alone, which left the
    task prompt's "safe next operate action" requirement ungraded by every
    criterion. It is back as the judge's second question.
    """
    task = yaml.safe_load(_TASK.read_text(encoding="utf-8"))
    judges = [c for c in task["success_criteria"] if c["type"] == "llm_judge"]
    assert len(judges) == 1
    prompt = judges[0]["prompt"].lower()
    assert "next action" in prompt, "the safe-next-action requirement lost its grader"
    assert "retry" in prompt and "deploy" in prompt, "mutation list went missing"
    assert "incomplete" in prompt, "the do-not-dock-for-completeness guard went missing"
