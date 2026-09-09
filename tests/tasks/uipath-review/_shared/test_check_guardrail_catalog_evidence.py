"""Unit tests for check_guardrail_catalog_evidence.py.

Drives the checker with a stubbed `uip` (via the `UIP` env var it honours) and
varies the report, covering all four cells of the reachable x declared matrix.
The point of the criterion is that a batched `set +e ... exit 0` wrapper can no
longer make a broken catalog look verified, so the "unreachable" cases matter
as much as the happy path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_guardrail_catalog_evidence.py"

CATALOG_OK = {
    "Result": "Success",
    "Code": "GuardrailCatalog",
    "Data": {"SchemaVersion": "1.0.0", "Guardrails": [
        {"ValidatorId": "pii_detection"}, {"ValidatorId": "prompt_injection"}]},
}

SILENT_REPORT = textwrap.dedent("""\
    # Review Report

    ## Warning Findings

    | W-D-001 | `LC_GUARDRAIL_MISAPPLIED` | PII block at Llm is misapplied. |

    ## Rules Skipped

    None. The live guardrail catalog was available.
    """)

DECLARED_REPORT = textwrap.dedent("""\
    # Review Report

    ## Warning Findings

    None.

    ## Rules Skipped

    | `LC_GUARDRAIL_MISAPPLIED` | the guardrails catalog was unavailable, so the rule was skipped. |
    """)


def _fake_uip(tmp_path: Path, payload, *, exit_code: int = 0) -> Path:
    script = tmp_path / "fake_uip.py"
    body = payload if isinstance(payload, str) else json.dumps(payload)
    script.write_text(
        "import sys\n"
        f"a=sys.argv[1:]\n"
        f"sys.stdout.write('1.202.0' if a==['--version'] else {body!r})\n"
        f"sys.exit(0 if a==['--version'] else {exit_code})\n",
        encoding="utf-8",
    )
    launcher = tmp_path / "fake_uip"
    launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


def run(tmp_path: Path, report: str | None, uip: Path) -> subprocess.CompletedProcess:
    if report is not None:
        (tmp_path / "_review_report.md").write_text(report, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          env={**os.environ, "UIP": str(uip)}, capture_output=True, text=True)


# --- reachable ---------------------------------------------------------------

def test_reachable_and_report_silent_passes(tmp_path):
    r = run(tmp_path, SILENT_REPORT, _fake_uip(tmp_path, CATALOG_OK))
    assert r.returncode == 0, r.stderr
    assert "catalog is reachable" in r.stdout
    assert "pii_detection" in r.stdout


def test_reachable_but_report_claims_unavailable_fails(tmp_path):
    r = run(tmp_path, DECLARED_REPORT, _fake_uip(tmp_path, CATALOG_OK))
    assert r.returncode != 0
    assert "declares the guardrail catalog unavailable" in r.stderr
    assert "which -a uip" in r.stderr


# --- unreachable: the hole `require_success: true` could not close -----------

def test_unreachable_and_report_silent_fails(tmp_path):
    """The demonstrated false positive: batched `exit 0` hid `unknown command`."""
    uip = _fake_uip(tmp_path, {"Result": "ValidationError", "Message": "unknown command 'catalog'"})
    r = run(tmp_path, SILENT_REPORT, uip)
    assert r.returncode != 0
    assert "could not be fetched" in r.stderr


def test_unreachable_and_report_declares_it_passes(tmp_path):
    uip = _fake_uip(tmp_path, {"Result": "ValidationError", "Message": "unknown command 'catalog'"})
    r = run(tmp_path, DECLARED_REPORT, uip)
    assert r.returncode == 0, r.stderr
    assert "report declares the guardrail catalog unavailable" in r.stdout


def test_catalog_unavailable_code_is_treated_as_unreachable(tmp_path):
    """guardrails-review.md Step 0 names this exact payload shape."""
    uip = _fake_uip(tmp_path, {"Result": "Success", "Code": "GuardrailCatalogUnavailable"})
    r = run(tmp_path, SILENT_REPORT, uip)
    assert r.returncode != 0
    assert "GuardrailCatalogUnavailable" in r.stdout


def test_empty_validator_list_is_unreachable(tmp_path):
    uip = _fake_uip(tmp_path, {"Result": "Success", "Data": {"Guardrails": []}})
    r = run(tmp_path, SILENT_REPORT, uip)
    assert r.returncode != 0
    assert "zero validators" in r.stdout


def test_non_json_output_is_unreachable(tmp_path):
    r = run(tmp_path, SILENT_REPORT, _fake_uip(tmp_path, "not json"))
    assert r.returncode != 0
    assert "non-JSON output" in r.stdout


def test_missing_binary_is_unreachable(tmp_path):
    (tmp_path / "_review_report.md").write_text(SILENT_REPORT, encoding="utf-8")
    r = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                       env={**os.environ, "UIP": "/nonexistent/uip"}, capture_output=True, text=True)
    assert r.returncode != 0
    assert "not on PATH" in r.stdout


# --- report plumbing ---------------------------------------------------------

def test_missing_report_fails(tmp_path):
    r = run(tmp_path, None, _fake_uip(tmp_path, CATALOG_OK))
    assert r.returncode != 0
    assert "not found" in r.stderr


def test_unavailability_prose_outside_rules_skipped_does_not_count(tmp_path):
    uip = _fake_uip(tmp_path, {"Result": "ValidationError", "Message": "boom"})
    misplaced = "# R\n\nThe guardrails catalog was unavailable, so I guessed.\n\n## Rules Skipped\n\nNone.\n"
    r = run(tmp_path, misplaced, uip)
    assert r.returncode != 0
