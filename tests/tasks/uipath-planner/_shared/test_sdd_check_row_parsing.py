"""Regression guards for sdd_check.py's row parsing and SDD discovery.

Both bugs below made the checker report failures on CORRECT input, which is worse
than not running it: the first person to hit a false positive stops trusting the
grader. Found while grading a real 2,220-line SDD from the 08/18 bug bash.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
CHECK = SHARED / "sdd_check.py"

MINIMAL = """# SDD — RowParse

## Document History

<!-- planner-handoff:v1 -->
## Planner Handoff

| Field | Value |
|---|---|
| **Status** | ready |

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | RowParse |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Exit Type | Marks Case Complete | Display Name |
|------|-----|------|-----------|---------------------|--------------|
| required-stages-completed | — | Case exited | exit-only | Yes | — |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|---|---|---|---|---|---|---|
| cost | Variable | double | | | 0 | Cost |

## Section 2: Stages & Tasks

### Stage 1: Only

**Type:** Stage
**Design Rationale:** Single stage.
**Description:** Single stage.
**Required for case completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|--------------|--------------|
| case-entered | — | No | Start |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | {guard} | exit-only | Yes | Done |

#### Tasks

| # | Task Name | Type | Activation Mode | Starts When | Required | Run Only Once | Persona | SLA |
|---|-----------|------|-----------------|-------------|----------|---------------|---------|-----|
| 1 | Do it | action | parallel | stage enters | Yes | No | Owner | — |

##### Task 1.1: Do it

**Type:** action
**Activation Mode:** parallel
**Design Rationale:** Human decides.
**Description:** Human decides.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | — |

**Task envelope**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

## Section 3: Personas & App Views

### Personas

### Process App Views

## Section 4: Integrations

> None.
"""


def run(tmp_path: Path, name: str, guard: str):
    (tmp_path / name).write_text(MINIMAL.replace("{guard}", guard), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECK)], cwd=tmp_path, capture_output=True, text=True
    )


# Symptoms of the column-shift bug. The fixture is deliberately not a fully
# conformant SDD — these tests isolate ROW PARSING, so they assert the specific
# false positives are gone rather than demanding an overall clean bill.
SHIFT_SYMPTOMS = ("invalid exit-type", "not legal for stage-exit")


def test_escaped_pipe_in_guard_does_not_shift_columns(tmp_path: Path):
    """A JS `||` must be written `\\|\\|` inside a markdown table.

    Splitting the row on every `|` invented phantom cells and shifted every column
    right, so `Exit Type` landed on a lone backslash and rule legality was graded
    against the wrong Marks-Complete value — on a legal table.
    """
    r = run(tmp_path, "sdd.md", r"=js:(vars.cost < 5000 \|\| vars.cost > 9000)")
    out = r.stdout + r.stderr
    hits = [s for s in SHIFT_SYMPTOMS if s in out]
    assert not hits, f"escaped pipes still shift columns ({hits}):\n{out}"


def test_plain_guard_is_symptom_free_too(tmp_path: Path):
    """Control: without an escaped pipe the same symptoms must be absent, so the
    test above measures escape handling rather than a fixture defect."""
    r = run(tmp_path, "sdd.md", "=js:(vars.cost < 5000)")
    out = r.stdout + r.stderr
    hits = [s for s in SHIFT_SYMPTOMS if s in out]
    assert not hits, f"baseline fixture already trips the symptoms ({hits}):\n{out}"


def test_finds_direct_design_basename(tmp_path: Path):
    """Direct design writes `<case-name-kebab>-sdd.md`, not `sdd.md`. Globbing only
    `sdd.md` made the checker exit before reading anything, so wiring it into a
    design-lane eval produced a criterion that could never pass."""
    r = run(tmp_path, "row-parse-sdd.md", "=js:(vars.cost < 5000)")
    out = r.stdout + r.stderr
    # Assert it actually READ the file, not merely that one error string is absent —
    # the pre-fix message was "no sdd.md found", so asserting on "no SDD found"
    # passed vacuously against the broken finder.
    assert "row-parse-sdd.md" in out, (
        "checker never opened the `*-sdd.md` design-lane artifact — its output does "
        f"not name the file:\n{out}"
    )


def test_missing_sdd_still_fails_loudly(tmp_path: Path):
    """The finder must stay strict — an empty directory is a failure, not a pass."""
    r = subprocess.run(
        [sys.executable, str(CHECK)], cwd=tmp_path, capture_output=True, text=True
    )
    assert r.returncode != 0
    assert "no SDD found" in (r.stdout + r.stderr)
