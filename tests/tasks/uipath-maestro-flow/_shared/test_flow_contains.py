"""Unit tests for ``flow_contains.py`` — substring, ``--regex``, ``--flow-name``
and ``--absent-regex`` assertions.

Covers the path-agnostic replacements for the ``file_contains`` /
``file_matches_regex`` criterion types and the three PR-review contracts:
positive assertion sets must be satisfied by ONE file (no split-matching
across subflows), ``--flow-name`` restores the basename enforcement the
literal paths had, and ``--absent-regex`` succeeds (exit 0) only after
discovery + reads complete without the forbidden pattern — so a missing flow
can never score a negative criterion.
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


def _make_project(tmp_path, solution="DemoSolution", project="Demo", flows=None):
    proj = tmp_path / solution / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    for name, body in (flows or {"Demo": FLOW_BODY}).items():
        (proj / f"{name}.flow").write_text(body)
    return proj


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    _make_project(tmp_path)
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


def test_dangling_flag_exits_2(sandbox):
    with pytest.raises(SystemExit) as exc:
        main(["--regex"])
    assert exc.value.code == 2


def test_assertion_set_must_match_single_file(tmp_path, monkeypatch):
    # Split across two flows: "alpha" in one, "beta" in the other — must FAIL.
    _make_project(
        tmp_path,
        flows={"Main": '{"nodes": ["alpha"]}', "Sub": '{"nodes": ["beta"]}'},
    )
    monkeypatch.chdir(tmp_path)
    assert main(["alpha", "beta"]) == 1
    assert main(["alpha"]) == 0
    assert main(["beta"]) == 0


def test_flow_name_match(sandbox):
    assert main(["--flow-name", "Demo"]) == 0
    assert main(["--flow-name", "Demo", "quick-form"]) == 0


def test_flow_name_mismatch_exits_1(sandbox):
    assert main(["--flow-name", "VendorApproval"]) == 1


def test_flow_name_scopes_assertions(tmp_path, monkeypatch):
    # "beta" only exists in Sub.flow; scoping to Main must fail on it.
    _make_project(
        tmp_path,
        flows={"Main": '{"nodes": ["alpha"]}', "Sub": '{"nodes": ["beta"]}'},
    )
    monkeypatch.chdir(tmp_path)
    assert main(["--flow-name", "Main", "alpha"]) == 0
    assert main(["--flow-name", "Main", "beta"]) == 1


def test_absent_regex_passes_when_absent(sandbox):
    assert main(["--absent-regex", r"\.output\.(legalApproval|legalNotes)"]) == 0


def test_absent_regex_fails_when_present(sandbox):
    assert main(["--absent-regex", r"\.output\.approved"]) == 1


def test_absent_regex_fails_without_flow(tmp_path, monkeypatch):
    # No flow at all: the negative assertion must NOT succeed (exit != 0) —
    # discovery aborts before the absence check can pass.
    proj = tmp_path / "Empty" / "Empty"
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    monkeypatch.chdir(tmp_path)
    assert main(["--absent-regex", "anything"]) != 0


def test_absent_and_positive_combined(sandbox):
    assert main(["quick-form", "--absent-regex", "forbidden-token"]) == 0
    assert main(["quick-form", "--absent-regex", r"\.output\.approved"]) == 1
