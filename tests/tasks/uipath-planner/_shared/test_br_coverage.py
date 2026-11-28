"""br-coverage.mjs: every rule the source numbers is carried by the SDD under its own ID, with its rule beside it.

Run: pytest tests/tasks/uipath-planner/_shared/test_br_coverage.py -v
"""

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRIPT = REPO / "skills" / "uipath-planner" / "scripts" / "br-coverage.mjs"

PDD = """# Order to Cash — PDD

## 5. Business Rules

| Rule ID | Description | Source | Evidence status |
|---|---|---|---|
| [BR-001](../wiki/as-is/business-rules.md#br-001) | An invoice open more than 30 days goes to collections. | SOP.pdf, p. 4 | source-backed |
| [BR-F01](../wiki/to-be/business-rules.md#br-f01) | When SAP is down, show the last good list with a banner. | Workshop 2 | user-stated |

==TBD: verify BR-001 against the named source and owner==
"""

CASE_SDD = """# SDD — Order to Cash

## Action Required — SME Review Items

D1. Confirm BR-F01 with the collections lead.

## Section 1: Case Definition

### Business Rules

#### Rules Applied in the Case

| ID | Rule | When | What happens | Applied by |
|---|---|---|---|---|
| BR-001 | An invoice open more than 30 days goes to collections. | invoice age > 30 days | the Collections stage starts | Collections entry condition |
| BR-F01 | When SAP is down, show the last good list with a banner. | SAP call fails | the last good list shows, bannered | Review.Show worklist |
"""


@pytest.fixture
def check(tmp_path):
    def run(sdds, source=PDD):
        src = tmp_path / "pdd.md"
        src.write_text(source, encoding="utf-8")
        paths = []
        for index, text in enumerate(sdds):
            path = tmp_path / f"sdd-{index}.md"
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        done = subprocess.run(
            ["node", str(SCRIPT), "--source", str(src), *paths],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        return done.returncode, done.stdout
    return run


def test_an_sdd_carrying_every_source_rule_prints_ok(check):
    rc, out = check([CASE_SDD])
    assert rc == 0, out
    assert out.startswith("OK: 2 of 2 source rules carried")


def test_a_source_rule_the_sdd_drops_fails(check):
    sdd = "\n".join(line for line in CASE_SDD.split("\n") if not line.startswith("| BR-F01"))
    rc, out = check([sdd])
    assert rc == 1
    assert "BR-F01 is in the source and in no SDD" in out


def test_a_rule_named_only_in_action_required_is_not_carried(check):
    sdd = CASE_SDD.replace("| BR-F01 | When SAP is down", "| BR-F99 | When SAP is down")
    rc, out = check([sdd])
    assert rc == 1
    assert "BR-F01 is in the source and in no SDD" in out


def test_a_rule_cited_by_its_id_alone_fails(check):
    sdd = CASE_SDD + "\n| # | invoiceAge | → route | Rule |\n|---|---|---|---|\n| 1 | > 30 | collections | BR-001 |\n"
    sdd = sdd.replace("| BR-001 | An invoice open more than 30 days goes to collections. | invoice age > 30 days | the Collections stage starts | Collections entry condition |\n", "")
    rc, out = check([sdd])
    assert rc == 1
    assert "BR-001 is cited by its ID alone" in out


def test_a_renumbered_rule_fails_both_ways(check):
    rc, out = check([CASE_SDD.replace("| BR-001 |", "| BR-01 |")])
    assert rc == 1
    assert "BR-001 is in the source and in no SDD" in out
    assert "BR-01 is in the SDD and not in the source" in out


def test_a_rule_the_design_adds_passes_with_its_marker(check):
    added = "| BR-002 | An invoice number is 10 digits. [DEFAULT] | invoice received | rejected when not | Intake.Validate |\n"
    rc, out = check([CASE_SDD + added])
    assert rc == 0, out
    assert "1 added by the design" in out


def test_an_sdd_with_no_business_rules_section_fails(check):
    rc, out = check([CASE_SDD.replace("### Business Rules", "### Rules")])
    assert rc == 1
    assert "no SDD has a Business Rules section" in out


def test_a_solution_carries_a_rule_in_any_of_its_sdds(check):
    lines = CASE_SDD.split("\n")
    root = "\n".join(line for line in lines if not line.startswith("| BR-F01"))
    child = "# SDD — Worklist App\n\n## 9. Business Rules\n\n" + next(line for line in lines if line.startswith("| BR-F01")) + "\n"
    rc, out = check([root, child])
    assert rc == 0, out


@pytest.mark.parametrize("heading", ["## 4. Business Rules", "## 3. Business Rules and Decisions", "## 2. Agent Framework, Steps and Business Rules", "### Business Rules"])
def test_every_template_heading_counts_as_the_section(check, heading):
    rc, out = check([CASE_SDD.replace("### Business Rules", heading)])
    assert rc == 0, out


def test_a_source_that_numbers_no_rules_checks_the_section_only(check):
    rc, out = check([CASE_SDD.replace("BR-001", "BR-01").replace("BR-F01", "BR-02")], source="# PDD\n\nInvoices over 30 days go to collections.\n")
    assert rc == 0, out
    assert "the source numbers no rules" in out
