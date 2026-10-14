"""Tests for check_scenario_findings.py."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_scenario_findings.py"

PADDING = "\n" + ("Context line for the review report body. " * 40) + "\n"


def _report(rows: str, grade: str = "C", extra: str = "") -> str:
    return textwrap.dedent(
        """\
        # Review Report

        ## Warning Findings

        | ID | Rule | Recommendation |
        |---|---|---|
        """
    ) + textwrap.dedent(rows) + PADDING + extra + f"\n**Final grade: {grade}**"


def _spec(tmp_path: Path, **overrides) -> Path:
    spec = {
        "project": "ReviewSol/SampleAgent",
        "inject": "inject_x.py",
        "expected": [
            {"ids": ["LC_TOOL_OVERLAP"], "category": "tools"},
            {"ids": ["LC_OUTPUT_ENUM_VS_PROMPT_DRIFT", "LC_OUTPUT_CLASSIFIER_NO_ENUM"], "category": "schema"},
        ],
        "min_recall": 1.0,
        "decoys": [{"id": "LC_CONTEXT_SOURCE_OVERLAP", "reason": "single source"}],
        "min_categories": 1,
        "min_severity_bands": 1,
        "max_findings": None,
        "forbidden_bands": [],
        "allowed_grades": ["A", "B", "C", "D", "F"],
        "grade_not_above_cli": True,
        "cli_expected": [],
        "cli_only_expected": False,
    }
    spec.update(overrides)
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def _fake_uip(tmp_path: Path, payload: object, *, exit_code: int = 0) -> Path:
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


def _cli(tmp_path: Path, grade: str = "C") -> Path:
    return _fake_uip(tmp_path, {"Result": "Success", "Data": {"Grade": grade, "Issues": []}})


def run(tmp_path: Path, report: str | None, spec: Path, uip: Path) -> subprocess.CompletedProcess:
    if report is not None:
        (tmp_path / "_review_report.md").write_text(report, encoding="utf-8")
    env = {**os.environ, "UIP": str(uip)}
    return subprocess.run(
        [sys.executable, str(CHECKER), "--spec", str(spec)],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )


BOTH_HITS = """\
    | W-D-001 | `LC_TOOL_OVERLAP` | lookup_customer / find_customer overlap. |
    | W-D-002 | `LC_OUTPUT_CLASSIFIER_NO_ENUM` | category has no enum. |
    """


def test_passes_when_all_planted_rules_are_cited(tmp_path):
    r = run(tmp_path, _report(BOTH_HITS), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HIT  LC_TOOL_OVERLAP" in r.stdout


def test_alternative_ids_count_as_one_hit(tmp_path):
    rows = BOTH_HITS.replace("LC_OUTPUT_CLASSIFIER_NO_ENUM", "LC_OUTPUT_ENUM_VS_PROMPT_DRIFT")
    r = run(tmp_path, _report(rows), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr


def test_fails_below_min_recall_and_names_the_miss(tmp_path):
    rows = "| W-D-001 | `LC_TOOL_OVERLAP` | overlap. |\n"
    r = run(tmp_path, _report(rows), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0
    assert "MISS LC_OUTPUT_ENUM_VS_PROMPT_DRIFT|LC_OUTPUT_CLASSIFIER_NO_ENUM" in r.stdout
    assert "recall 0.50 < 1.00" in r.stderr


def test_rule_cited_only_in_prose_is_a_miss(tmp_path):
    rows = "| W-D-001 | `LC_TOOL_OVERLAP` | overlap. |\n"
    extra = "\nLC_OUTPUT_CLASSIFIER_NO_ENUM was considered.\n"
    r = run(tmp_path, _report(rows, extra=extra), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0


def test_pattern_must_match_the_same_row(tmp_path):
    spec = _spec(tmp_path, expected=[
        {"ids": ["LC_GUARDRAIL_RECOMMENDED"], "category": "guardrails", "pattern": r"audit|\blog\b"},
    ])
    wrong = "| I-D-001 | `LC_GUARDRAIL_RECOMMENDED` | Add a PII block guardrail. |\n"
    right = "| I-D-001 | `LC_GUARDRAIL_RECOMMENDED` | Add a Tool-scope log guardrail for audit. |\n"
    assert run(tmp_path, _report(wrong), spec, _cli(tmp_path)).returncode != 0
    assert run(tmp_path, _report(right), spec, _cli(tmp_path)).returncode == 0


def test_decoy_in_finding_row_fails(tmp_path):
    rows = BOTH_HITS + "| W-D-003 | `LC_CONTEXT_SOURCE_OVERLAP` | overlap. |\n"
    r = run(tmp_path, _report(rows), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0
    assert "DECOY LC_CONTEXT_SOURCE_OVERLAP" in r.stdout


def test_decoy_outside_finding_rows_is_ignored(tmp_path):
    extra = "\n## Rules Skipped\n\n- `LC_CONTEXT_SOURCE_OVERLAP`: not applicable, single source.\n"
    r = run(tmp_path, _report(BOTH_HITS, extra=extra), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr


def test_decoy_with_element_fails_only_when_element_is_in_the_row(tmp_path):
    spec = _spec(tmp_path, decoys=[
        {"id": "LC_GUARDRAIL_MISAPPLIED", "element": "Made-up validator", "reason": "CLI owns it"},
    ])
    other = BOTH_HITS + "| W-D-003 | `LC_GUARDRAIL_MISAPPLIED` | PII block at Llm is misapplied. |\n"
    same = BOTH_HITS + "| W-D-003 | `LC_GUARDRAIL_MISAPPLIED` | Made-up validator is misapplied. |\n"
    assert run(tmp_path, _report(other), spec, _cli(tmp_path)).returncode == 0
    assert run(tmp_path, _report(same), spec, _cli(tmp_path)).returncode != 0


def test_all_finding_row_prefixes_are_parsed(tmp_path):
    rows = """\
    | C-001 | `LC_TOOL_OVERLAP` | overlap. |
    """
    extra = "\n- [V-E-001] SampleAgent/agent.json: **LC_OUTPUT_CLASSIFIER_NO_ENUM** — no enum\n"
    r = run(tmp_path, _report(rows, extra=extra), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr


def test_rule_id_decorations_are_parsed(tmp_path):
    rows = """\
    | W-001 | **LC_TOOL_OVERLAP** | overlap. |
    | I-D-002 | [LC_OUTPUT_CLASSIFIER_NO_ENUM](#enum) | no enum. |
    """
    r = run(tmp_path, _report(rows), _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr


def test_fails_below_min_categories(tmp_path):
    spec = _spec(tmp_path, min_categories=3)
    r = run(tmp_path, _report(BOTH_HITS), spec, _cli(tmp_path))
    assert r.returncode != 0
    assert "categories 2 < 3" in r.stderr


def test_fails_below_min_severity_bands(tmp_path):
    spec = _spec(tmp_path, min_severity_bands=2)
    r = run(tmp_path, _report(BOTH_HITS), spec, _cli(tmp_path))
    assert r.returncode != 0
    rows = BOTH_HITS + "| C-D-003 | `LC_FAILURE_IRREVERSIBLE_ACTION` | delete tool. |\n"
    assert run(tmp_path, _report(rows), spec, _cli(tmp_path)).returncode == 0


def test_max_findings_and_forbidden_bands(tmp_path):
    spec = _spec(tmp_path, expected=[], min_categories=0, max_findings=1, forbidden_bands=["C"])
    one_info = "| I-D-001 | `LC_PROMPT_STRUCTURE` | minor. |\n"
    critical = "| C-D-001 | `LC_PROMPT_STRUCTURE` | minor. |\n"
    assert run(tmp_path, _report(one_info, grade="A"), spec, _cli(tmp_path, "A")).returncode == 0
    assert run(tmp_path, _report(BOTH_HITS, grade="A"), spec, _cli(tmp_path, "A")).returncode != 0
    assert run(tmp_path, _report(critical, grade="A"), spec, _cli(tmp_path, "A")).returncode != 0


def test_fails_when_grade_not_allowed(tmp_path):
    spec = _spec(tmp_path, allowed_grades=["D", "F"])
    r = run(tmp_path, _report(BOTH_HITS, grade="C"), spec, _cli(tmp_path))
    assert r.returncode != 0
    assert "final grade C not in ['D', 'F']" in r.stderr


def test_fails_when_grade_is_better_than_cli_grade(tmp_path):
    r = run(tmp_path, _report(BOTH_HITS, grade="B"), _spec(tmp_path), _cli(tmp_path, "C+"))
    assert r.returncode != 0
    assert "better than CLI Data.Grade C" in r.stderr


def test_cli_unavailable_skips_grade_ceiling(tmp_path):
    uip = _fake_uip(tmp_path, "boom", exit_code=1)
    r = run(tmp_path, _report(BOTH_HITS, grade="A"), _spec(tmp_path), uip)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WARN" in r.stdout


def test_fails_when_final_grade_footer_missing(tmp_path):
    report = _report(BOTH_HITS).rsplit("**Final grade", 1)[0]
    r = run(tmp_path, report, _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0
    assert "Final grade" in r.stderr


def test_final_grade_footer_allows_trailing_newline(tmp_path):
    r = run(tmp_path, _report(BOTH_HITS) + "\n", _spec(tmp_path), _cli(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr


def test_fails_when_report_missing(tmp_path):
    r = run(tmp_path, None, _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0
    assert "not found" in r.stderr


def test_fails_when_report_is_short(tmp_path):
    r = run(tmp_path, "# tiny\n**Final grade: C**", _spec(tmp_path), _cli(tmp_path))
    assert r.returncode != 0
    assert "short" in r.stderr
