"""Unit tests for ``flow_contains.py`` — substring and ``--regex`` assertions.

Covers the path-agnostic replacements for the ``file_contains`` /
``file_matches_regex`` criterion types: substrings and regexes must match at
least one discovered ``.flow`` file, exit 1 when absent (the negative-check
contract relied on by quality_08_variable_binding_fieldid), and exit 2 on a
dangling ``--regex`` flag.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_contains import main  # noqa: E402

FLOW_BODY = json.dumps(
    {
        "nodes": [{"id": "h1", "type": "uipath.human-in-the-loop.quick-form"}],
        "expr": "$vars.h1.output.approved",
    }
)


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    proj = tmp_path / "DemoSolution" / "Demo"
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (proj / "Demo.flow").write_text(FLOW_BODY)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_no_args_asserts_flow_exists(sandbox):
    assert main([]) == 0


def test_substring_present(sandbox):
    assert main(['"uipath.human-in-the-loop.quick-form"']) == 0


def test_substring_absent_exits_1(sandbox):
    assert main(["no-such-substring"]) == 1


def test_regex_present(sandbox):
    assert main(["--regex", r"\$vars\.[A-Za-z0-9_-]+\.output"]) == 0


def test_regex_absent_exits_1(sandbox):
    assert main(["--regex", r"\.output\.(legalApproval|legalNotes)"]) == 1


def test_mixed_substring_and_regex(sandbox):
    assert main(["quick-form", "--regex", r"\$vars\."]) == 0


def test_dangling_regex_flag_exits_2(sandbox):
    assert main(["--regex"]) == 2
