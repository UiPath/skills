"""case-draft-parity.mjs: a final that keeps its draft prints OK; each kind of drift prints its FAIL line.

Run: pytest tests/tasks/uipath-planner/_shared/test_case_draft_parity.py -v
"""

import re
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRIPT = REPO / "skills" / "uipath-planner" / "scripts" / "case-draft-parity.mjs"
CASE = REPO / "tests" / "tasks" / "uipath-planner" / "case"
DRAFTS = sorted(CASE.glob("case_finalize_draft*/fixtures/sdd.draft.md"))
LOAN = CASE / "case_finalize_draft_loan" / "fixtures" / "sdd.draft.md"
REJECT = CASE / "case_finalize_draft_reject" / "fixtures" / "sdd.draft.md"


def parity(tmp_path, final_text, draft=LOAN):
    final = tmp_path / "sdd.md"
    final.write_text(final_text, encoding="utf-8")
    done = subprocess.run(["node", str(SCRIPT), str(draft), str(final)], capture_output=True, text=True, encoding="utf-8", check=False)
    return done.returncode, done.stdout


GUARD = '\n**Recipient:** =js:vars.loanAmount > 5000000 ? "Role:Credit Analyst" : "Role:Underwriter"\n'


def finalized(text):
    """The draft with the final's first heading, and the loan's $5M role policy encoded as a Recipient."""
    text = re.sub(r"\A.*", lambda m: m[0] if m[0].startswith("# SDD — ") else "# SDD — Sample", text, count=1)
    return text + GUARD if "≤$5M" in text else text


@pytest.mark.parametrize("draft", DRAFTS, ids=lambda p: p.parent.parent.name)
def test_a_final_that_keeps_its_draft_prints_ok(tmp_path, draft):
    rc, out = parity(tmp_path, finalized(draft.read_text(encoding="utf-8")), draft)
    assert rc == 0, out
    assert out.startswith("OK:")


def test_task_id_suffix_without_backticks_still_matches(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).replace("(`t01`)", "(t01)")
    assert parity(tmp_path, text)[0] == 0


def test_a_dropped_stage_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8"))
    text = re.sub(r"^### Secondary Stage: Rejected[\s\S]*?(?=^### )", "", text, count=1, flags=re.M)
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "FAIL: stage 10: 'Rejected' is missing from the final" in out


def test_a_primary_stage_made_secondary_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8"))
    text = text.replace("### Stage 4: QA/QC (`stage-qa-qc`)\n", "### Stage 4: QA/QC (`stage-qa-qc`)\n\n**Stage Kind:** secondary\n", 1)
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "FAIL: stage 'QA/QC': draft primary, final secondary" in out


def test_two_stage_kind_lines_fail(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).replace("**Stage Kind:** secondary", "**Stage Kind:** primary\n**Stage Kind:** secondary", 1)
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "final both primary and secondary" in out


def test_a_dropped_variable_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).replace("| loanApplicationId |", "| renamedId |", 1)
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "FAIL: Case Variables: 'loanApplicationId' is missing from the final" in out


def test_a_rewritten_expression_fails(tmp_path):
    draft = REJECT.read_text(encoding="utf-8")
    expression = re.search(r"=js:[^|`\n]*[^|`\s]", draft)[0]
    rc, out = parity(tmp_path, finalized(draft).replace(expression, "=js:true"), REJECT)
    assert rc == 1
    assert f"FAIL: expression missing from the final: {expression}" in out


def test_a_final_without_its_first_heading_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).split("\n", 1)[1]
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "FAIL: first line is not '# SDD — <Case Name>'" in out


def test_a_role_threshold_left_in_prose_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).replace(GUARD, "")
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "FAIL: threshold '≤$5M' picks a role, and no =js: line holds 5000000 with a Role:" in out


def test_a_role_threshold_as_an_entry_if_fails(tmp_path):
    text = finalized(LOAN.read_text(encoding="utf-8")).replace(GUARD, "\n| `current-stage-entered` | =js:vars.loanAmount > 5000000 ? true : false | — |\n")
    rc, out = parity(tmp_path, text)
    assert rc == 1
    assert "picks a role" in out
