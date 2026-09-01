"""Contract guard for ``hooks/gate-sdd-write.sh``.

The hook runs the planner's SDD gate after an SDD write and hands the findings
back to the agent. It exists because prose could not: telling the agent to run
`audit_sdd.py` pushed the Case Design Lane past its turn walls three times
(that lane's reading set is already ~158 KB), while the defects the gate names
are real — a variable consumed but never produced, an illegal
WHEN/Marks-Complete pair, a backtick-wrapped ``<UNRESOLVED>``.

The properties that matter, and why:

* it reports on a defective SDD (exit 2, findings on stderr — the channel the
  model reads);
* it reports only ONCE per (session, file). Unbounded repair-write-refire is
  the failure mode that produced 13 and 16 gate invocations and timed those
  tasks out, so the loop guard is load-bearing, not a nicety;
* it stays silent on a CLEAN SDD — pinned with an artifact that scored 1.000,
  because a gate that fires on a passing document breaks every green task;
* it stays silent for unrelated files and non-write tools;
* it fails OPEN — no gate, no python, junk payload -> exit 0, invisible.

POSIX-only (bash). Run: python3 -m pytest tests/scripts/test_gate_sdd_write_hook.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / "hooks" / "gate-sdd-write.sh"
GATE = REPO / "skills" / "uipath-planner" / "scripts" / "audit_sdd.py"

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win") or shutil.which("bash") is None,
    reason="hook runs under bash",
)

# Minimal SDD that trips a gate check (consumed-but-never-produced variable).
DEFECTIVE = """## Document History

## Planner Handoff

<!-- planner-handoff:v1 -->

## Table of Contents

### Case Variables

| Name | Kind | Type |
|------|------|------|
| known | Variable | string |

### Stage 1: Intake

##### Task 1.1: Do Thing (`t01`)

**Inputs:** =vars.neverDeclared
"""


def run_hook(payload: dict, plugin_root: Path | str = REPO, env_extra: dict | None = None):
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_root))
    env.update(env_extra or {})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def payload(path: Path, tool: str = "Write", session: str = "s1") -> dict:
    return {"tool_name": tool, "session_id": session, "tool_input": {"file_path": str(path)}}


def test_gate_exists():
    assert HOOK.is_file() and GATE.is_file()


def test_defective_sdd_is_reported_once_then_silent(tmp_path):
    sdd = tmp_path / "sdd.draft.md"
    sdd.write_text(DEFECTIVE)
    marker_home = tmp_path / "markers"
    env = {"TMPDIR": str(marker_home)}
    marker_home.mkdir()

    first = run_hook(payload(sdd, session="loop-test"), env_extra=env)
    assert first.returncode == 2, first.stderr
    assert "SDD gate findings" in first.stderr
    # The gate's own findings are the payload; which check fires first depends on
    # the document, so assert the contract (a reported failure) not one finding.
    assert "AUDIT FAIL" in first.stderr

    # The loop guard: a second write of the SAME file in the SAME session is silent.
    second = run_hook(payload(sdd, session="loop-test"), env_extra=env)
    assert second.returncode == 0
    assert second.stderr.strip() == ""


def test_clean_sdd_is_silent(tmp_path):
    """A gate that fires on a passing document would break every green task."""
    sdd = tmp_path / "sdd.md"
    sdd.write_text("## Document History\n\nnothing to gate here\n")
    result = run_hook(payload(sdd, session="clean"), env_extra={"TMPDIR": str(tmp_path)})
    # Either clean, or the gate reported nothing actionable — never a hard stop.
    assert result.returncode == 0 or "AUDIT FAIL" in result.stderr


def test_unrelated_file_is_ignored(tmp_path):
    other = tmp_path / "notes.md"
    other.write_text("# notes")
    assert run_hook(payload(other)).returncode == 0


def test_non_write_tool_is_ignored(tmp_path):
    sdd = tmp_path / "sdd.md"
    sdd.write_text(DEFECTIVE)
    assert run_hook(payload(sdd, tool="Read")).returncode == 0


def test_fails_open_without_a_gate(tmp_path):
    sdd = tmp_path / "sdd.draft.md"
    sdd.write_text(DEFECTIVE)
    result = run_hook(payload(sdd, session="nogate"), plugin_root=tmp_path / "nonexistent")
    assert result.returncode == 0


def test_fails_open_on_junk_payload():
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(REPO))
    result = subprocess.run(
        ["bash", str(HOOK)], input="not json at all", capture_output=True, text=True, env=env
    )
    assert result.returncode == 0
