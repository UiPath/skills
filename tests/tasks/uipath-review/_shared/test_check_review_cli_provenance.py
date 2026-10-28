"""Unit tests for check_review_cli_provenance.py.

The checker's whole point is that its verdict tracks the REPORT's content and
never the shape of the agent's shell calls, so these tests drive it with a
stubbed `uip` (via the `UIP` env var the checker honours) and vary only the
report. A batched-vs-unbatched command trajectory cannot change any outcome
here — that is the property the criterion swap was made to buy.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_review_cli_provenance.py"

CLI_RULE_ID = "LOWCODE_EVAL_SET_EMPTY"

GOOD_REPORT = textwrap.dedent(
    f"""\
    # Review Report — ReviewSol / SampleAgent

    **Agent grade: B — Good.** The deterministic review grade was A; the judgment
    score was 71/100, so the final grade is B.

    ## Automated Review Result

    `uip agent review` returned grade **A**, score **99**, and one informational
    deterministic finding:

    | ID | Rule | Finding |
    |---|---|---|
    | I-D-001 | `{CLI_RULE_ID}` | Eval set has no datapoints. Add datapoints. |

    ## Warning Findings

    | ID | Rule | Finding |
    |---|---|---|
    | W-D-001 | `LC_GUARDRAIL_MISAPPLIED` | PII block at Llm is misapplied. Remove it. |

    ## Rules Skipped

    None. The agent review CLI completed successfully.
    """
)


def _fake_uip(tmp_path: Path, payload: object, *, exit_code: int = 0) -> Path:
    """A stand-in `uip` that prints `payload` and exits `exit_code`."""
    script = tmp_path / "fake_uip.py"
    body = payload if isinstance(payload, str) else json.dumps(payload)
    script.write_text(
        "import sys\n"
        f"sys.stdout.write({body!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    launcher = tmp_path / "fake_uip"
    launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


def _payload(issues: list[str], *, grade: str = "A", score: int = 99) -> dict:
    return {
        "Result": "Success",
        "Code": "AgentReview",
        "Data": {
            "Verdict": "PASS",
            "Score": score,
            "Grade": grade,
            "Issues": [
                {"RuleId": r, "Severity": "info", "Description": "d", "File": "f", "SuggestedFix": "s"}
                for r in issues
            ],
            "Stats": {"Errors": 0, "Warnings": 0, "Infos": len(issues)},
        },
    }


def run(tmp_path: Path, report: str | None, uip: Path) -> subprocess.CompletedProcess:
    if report is not None:
        (tmp_path / "_review_report.md").write_text(report, encoding="utf-8")
    env = {**os.environ, "UIP": str(uip)}
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )


# --- the CLI ran and the report proves it ----------------------------------

def test_passes_when_report_carries_every_cli_rule_id(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode == 0, r.stderr
    assert "carries every CLI-emitted rule_id" in r.stdout


def test_passes_regardless_of_how_the_agent_shelled_out(tmp_path):
    """No command telemetry is consulted, so batching cannot change the verdict."""
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode == 0
    assert "command" not in r.stderr.lower()


# --- the CLI did not run ----------------------------------------------------

def test_fails_when_report_omits_a_cli_rule_id(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    stripped = GOOD_REPORT.replace(f"`{CLI_RULE_ID}`", "`LC_EVAL_COVERAGE_THIN`")
    r = run(tmp_path, stripped, uip)
    assert r.returncode != 0
    assert CLI_RULE_ID in r.stderr


def test_fails_when_only_some_cli_rule_ids_are_carried(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID, "LOWCODE_ENTRY_POINTS_MISSING"]))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode != 0
    assert "LOWCODE_ENTRY_POINTS_MISSING" in r.stderr
    assert CLI_RULE_ID not in r.stderr  # the carried one is not reported missing


# --- clean fixture: nothing to carry, fall back to grade/score --------------

def test_passes_on_clean_fixture_when_grade_is_evidenced(tmp_path):
    uip = _fake_uip(tmp_path, _payload([], grade="A", score=100))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode == 0, r.stderr
    assert "no findings" in r.stdout


def test_fails_on_clean_fixture_when_report_evidences_nothing(tmp_path):
    uip = _fake_uip(tmp_path, _payload([], grade="D", score=42))
    bare = "# Review Report\n\n## Warning Findings\n\nNothing was checked here.\n"
    r = run(tmp_path, bare, uip)
    assert r.returncode != 0
    assert "no trace that Step 2.5a ran" in r.stderr


# --- ground truth unobtainable ---------------------------------------------

def test_fails_when_cli_is_down_and_report_is_silent(tmp_path):
    uip = _fake_uip(tmp_path, "boom", exit_code=3)
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode != 0
    assert "does not declare it unavailable" in r.stderr


def test_passes_when_cli_is_down_and_report_declares_it_skipped(tmp_path):
    uip = _fake_uip(tmp_path, "boom", exit_code=3)
    declared = GOOD_REPORT.replace(
        "None. The agent review CLI completed successfully.",
        "| Step 2.5a | `uip agent review` | reason: the review CLI was unavailable. |",
    )
    r = run(tmp_path, declared, uip)
    assert r.returncode == 0, r.stderr
    assert "declares the review CLI unavailable" in r.stdout


def test_skip_note_outside_rules_skipped_does_not_count(tmp_path):
    """The declaration must live under 'Rules Skipped', not anywhere in prose."""
    uip = _fake_uip(tmp_path, "boom", exit_code=3)
    misplaced = (
        "# Review Report\n\nThe review CLI was unavailable, so I guessed.\n\n"
        "## Rules Skipped\n\nNone.\n"
    )
    r = run(tmp_path, misplaced, uip)
    assert r.returncode != 0


def test_cli_capability_divergence_fails_with_an_environment_diagnostic(tmp_path):
    """Report says the CLI lacks `review`, but the checker's `uip` provides it.

    Observed for real: on a host with three `uip` installs, the Codex agent's
    login shell (per-task HOME, so no dotfiles) resolved a stale 1.0.0 without
    `agent review`, while the checker resolved 1.202.0. This must fail -- passing
    on the declaration alone would let any agent skip Step 2.5a by writing one
    line -- but the message must point at the environment, not at the skill.
    """
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    declared = GOOD_REPORT.replace(f"`{CLI_RULE_ID}`", "`LC_EVAL_COVERAGE_THIN`").replace(
        "None. The agent review CLI completed successfully.",
        "| `uip agent review` | The installed CLI does not provide the `review` command. |",
    )
    r = run(tmp_path, declared, uip)
    assert r.returncode != 0
    assert "resolved a different `uip`" in r.stderr
    assert "which -a uip" in r.stderr


def test_checker_reports_which_cli_it_resolved(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert "Checker resolved" in r.stdout
    assert str(uip) in r.stdout


def test_non_success_result_is_treated_as_unavailable(tmp_path):
    uip = _fake_uip(tmp_path, {"Result": "ValidationError", "Message": "bad project"})
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode != 0
    assert "ValidationError" in r.stdout or "ValidationError" in r.stderr


def test_non_json_output_is_treated_as_unavailable(tmp_path):
    uip = _fake_uip(tmp_path, "not json at all")
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode != 0
    assert "non-JSON output" in r.stdout


# --- report plumbing --------------------------------------------------------

def test_fails_when_report_missing(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = run(tmp_path, None, uip)
    assert r.returncode != 0
    assert "not found" in r.stderr


def test_unattributed_grade_warns_but_does_not_fail(tmp_path):
    """Step 4.5 only *requires* printing the CLI grade when it differs."""
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID], grade="F"))
    r = run(tmp_path, GOOD_REPORT, uip)
    assert r.returncode == 0, r.stderr
    assert "does not attribute grade F" in r.stdout


# --- how strong is the evidence for THIS rule_id? ---------------------------

def _run_with_repo(tmp_path: Path, report: str, uip: Path, repo: str | None):
    (tmp_path / "_review_report.md").write_text(report, encoding="utf-8")
    env = {**os.environ, "UIP": str(uip)}
    env.pop("SKILLS_REPO_PATH", None)
    if repo:
        env["SKILLS_REPO_PATH"] = repo
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, env=env,
                          capture_output=True, text=True)


REAL_REPO = str(Path(__file__).resolve().parents[4])  # .../Projects/skills


def test_rule_id_absent_from_skill_tree_is_reported_as_proof(tmp_path):
    """`LOWCODE_EVAL_SET_EMPTY` is in no skill file, so citing it proves invocation."""
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = _run_with_repo(tmp_path, GOOD_REPORT, uip, REAL_REPO)
    assert r.returncode == 0, r.stderr
    assert "appear nowhere in the skill tree" in r.stdout


def test_rule_id_documented_in_the_skill_downgrades_the_claim(tmp_path):
    """`CODED_GUARDRAIL_WRONG_IMPORT` is named in SKILL.md and agents-coded-rules.md.

    An agent could cite it from the source without running the CLI, so the
    criterion must say so rather than claim proof of invocation.
    """
    rid = "CODED_GUARDRAIL_WRONG_IMPORT"
    uip = _fake_uip(tmp_path, _payload([rid]))
    report = GOOD_REPORT.replace(CLI_RULE_ID, rid)
    r = _run_with_repo(tmp_path, report, uip, REAL_REPO)
    assert r.returncode == 0, r.stderr
    assert "does not by itself prove the CLI ran" in r.stdout


def test_probe_is_silent_without_skills_repo_path(tmp_path):
    uip = _fake_uip(tmp_path, _payload([CLI_RULE_ID]))
    r = _run_with_repo(tmp_path, GOOD_REPORT, uip, None)
    assert r.returncode == 0, r.stderr
    assert "skill tree" not in r.stdout
