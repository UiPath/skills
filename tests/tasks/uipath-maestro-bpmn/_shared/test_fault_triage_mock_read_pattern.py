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
raw command and against the shell-normalized form, and a hit on either counts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_TASK = (
    Path(__file__).resolve().parents[1]
    / "operate-diagnose"
    / "minimal_fault_triage.yaml"
)


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
    from coder_eval.criteria.command_executed import _match_haystacks  # type: ignore

    pattern = _pattern()
    return any(pattern.search(h) for h in _match_haystacks(command, is_shell=True))


# Commands that READ a mocked input. The guard must fire.
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
]


@pytest.mark.parametrize("command", READS)
def test_guard_fires_on_a_mock_read(command: str) -> None:
    assert _hits(command), f"guard should have counted: {command!r}"


@pytest.mark.parametrize("command", COMPLIANT)
def test_guard_is_silent_on_compliant_commands(command: str) -> None:
    assert not _hits(command), f"guard wrongly counted: {command!r}"
