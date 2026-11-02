"""
Behaviour tests for scripts/parse-required-checks.py, the single parser of the
"Current target set" table in docs/REQUIRED-CHECKS.md.

test_required_checks_contract.py checks the live table against the workflows.
These tests pin the parser itself on fixture documents, so the way a malformed
table is rejected does not depend on what the live doc happens to contain.

Run from repo root:
    pytest tests/scripts/test_parse_required_checks.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "parse-required-checks.py"

_spec = importlib.util.spec_from_file_location("parse_required_checks_behaviour", SCRIPT)
parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parser)

GOOD = """\
# Required checks

Prose that mentions | pipes | but is not a row.

## Current target set

| Check | Workflow |
|-------|----------|
| `lint` | `lint.yml` |
| `unit / python` | `test.yml` | extra prose after the second cell |

## Notes

| `ignored` | `after-the-section.yml` |
"""


def write(tmp_path, text):
    doc = tmp_path / "REQUIRED-CHECKS.md"
    doc.write_text(text, encoding="utf-8")
    return doc


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)


def test_parse_returns_context_workflow_pairs_and_stops_at_the_next_section(tmp_path):
    assert parser.parse(write(tmp_path, GOOD)) == [("lint", "lint.yml"), ("unit / python", "test.yml")]


def test_rows_inside_a_code_fence_are_not_part_of_the_table(tmp_path):
    text = GOOD.replace("| `lint` | `lint.yml` |", "```\n| not a row at all |\n```\n| `lint` | `lint.yml` |")
    assert parser.parse(write(tmp_path, text)) == [("lint", "lint.yml"), ("unit / python", "test.yml")]


def test_half_backticked_row_is_an_error_naming_its_line(tmp_path):
    text = GOOD.replace("| `lint` | `lint.yml` |", "| `lint` | lint.yml |")
    with pytest.raises(parser.TableError) as exc:
        parser.parse(write(tmp_path, text))
    message = str(exc.value)
    assert ":9:" in message
    assert "| `lint` | lint.yml |" in message
    assert "backtick BOTH cells" in message


def test_missing_heading_is_an_error(tmp_path):
    with pytest.raises(parser.TableError, match="no '## Current target set' heading found"):
        parser.parse(write(tmp_path, "# Required checks\n\nNothing here.\n"))


def test_duplicate_heading_is_an_error(tmp_path):
    with pytest.raises(parser.TableError, match="duplicate '## Current target set' heading"):
        parser.parse(write(tmp_path, GOOD + "\n## Current target set\n"))


def test_section_without_rows_is_an_error(tmp_path):
    text = "## Current target set\n\n| Check | Workflow |\n|---|---|\n"
    with pytest.raises(parser.TableError, match="parsed zero rows"):
        parser.parse(write(tmp_path, text))


def test_duplicate_context_is_an_error_listing_it(tmp_path):
    text = GOOD.replace("`unit / python`", "`lint`")
    with pytest.raises(parser.TableError, match=r"duplicate context\(s\) in the table: \['lint'\]"):
        parser.parse(write(tmp_path, text))


def test_default_output_is_tab_separated_pairs():
    done = run_cli("--doc", str(REPO_ROOT / "docs" / "REQUIRED-CHECKS.md"))
    assert done.returncode == 0
    lines = done.stdout.splitlines()
    assert lines and all(line.count("\t") == 1 for line in lines)


def test_cli_prints_each_format(tmp_path):
    doc = str(write(tmp_path, GOOD))

    pairs = run_cli("--doc", doc)
    assert (pairs.returncode, pairs.stdout) == (0, "lint\tlint.yml\nunit / python\ttest.yml\n")

    contexts = run_cli("--doc", doc, "--contexts")
    assert (contexts.returncode, contexts.stdout) == (0, "lint\nunit / python\n")

    as_json = run_cli("--doc", doc, "--json")
    assert as_json.returncode == 0
    assert json.loads(as_json.stdout) == [
        {"context": "lint", "workflow": "lint.yml"},
        {"context": "unit / python", "workflow": "test.yml"},
    ]


def test_cli_reports_a_malformed_table_on_stderr_and_exits_1(tmp_path):
    done = run_cli("--doc", str(write(tmp_path, "# nothing\n")))
    assert done.returncode == 1
    assert done.stdout == ""
    assert "error:" in done.stderr
    assert "no '## Current target set' heading found" in done.stderr


def test_json_and_contexts_are_mutually_exclusive(tmp_path):
    done = run_cli("--doc", str(write(tmp_path, GOOD)), "--json", "--contexts")
    assert done.returncode == 2
    assert "not allowed with argument" in done.stderr
