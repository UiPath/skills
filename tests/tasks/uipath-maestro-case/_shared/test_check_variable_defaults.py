"""Unit tests for check_variable_defaults.py — the variable-default encoding grader.

Synthetic stubs only; no tenant, no captured artifact. The grader was additionally run against the
real shipped caseplan that surfaced this (13 non-string defaults) and exits 1.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_variable_defaults.py")


def caseplan(*variables):
    return {
        "id": "case-Stub000001",
        "version": "27.0.0",
        "name": "Stub",
        "metadata": {},
        "variables": {"inputs": [], "outputs": [], "inputOutputs": list(variables)},
        "nodes": [],
        "edges": [],
    }


def var(vid, vtype, **kw):
    e = {"id": vid, "name": vid, "type": vtype, "elementId": "root"}
    e.update(kw)
    return e


def run(tmp_path, case=None, *, nested="Sol/Proj"):
    if case is not None:
        d = tmp_path / nested
        d.mkdir(parents=True, exist_ok=True)
        (d / "caseplan.json").write_text(json.dumps(case))
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          capture_output=True, text=True)


# --- the regression ------------------------------------------------------------------

def test_object_default_fails(tmp_path):
    """A dict default is deleted at serialization."""
    res = run(tmp_path, caseplan(var("payload", "jsonSchema", default={"amount": 125.5})))
    assert res.returncode == 1, res.stdout
    assert "DELETED at serialization" in res.stdout


def test_empty_object_default_fails(tmp_path):
    """`{}` is just as deleted as a populated object."""
    res = run(tmp_path, caseplan(var("errorInfo", "jsonSchema", default={})))
    assert res.returncode == 1, res.stdout
    assert '"{}"' in res.stdout          # suggests the two-character string


def test_string_encoded_default_passes(tmp_path):
    res = run(tmp_path, caseplan(var("payload", "jsonSchema", default='{"amount":125.5}')))
    assert res.returncode == 0, res.stdout
    assert "every variable default is a string" in res.stdout


def test_suggested_encoding_round_trips(tmp_path):
    """The 'should:' line must be valid JSON that decodes to the original object."""
    original = {"amount": 125.5, "currency": "USD"}
    res = run(tmp_path, caseplan(var("r", "jsonSchema", default=original)))
    line = [l for l in res.stdout.splitlines() if "should:" in l][0]
    suggested = line.split("should:", 1)[1].strip()
    assert json.loads(json.loads(suggested)) == original


# --- non-fatal but still contract-violating -------------------------------------------

@pytest.mark.parametrize("value,vtype", [(5, "integer"), (12.5, "float"), (True, "boolean")])
def test_numeric_and_boolean_defaults_fail(tmp_path, value, vtype):
    """These survive serialization but violate the declared string type."""
    res = run(tmp_path, caseplan(var("v", vtype, default=value)))
    assert res.returncode == 1, res.stdout
    assert "violates declared string type" in res.stdout


def test_boolean_encoding_is_lowercase_json(tmp_path):
    """Python True must be suggested as "true", not "True"."""
    res = run(tmp_path, caseplan(var("flag", "boolean", default=True)))
    assert '"true"' in res.stdout, res.stdout
    assert '"True"' not in res.stdout


# --- clean cases -----------------------------------------------------------------------

def test_no_defaults_at_all_passes(tmp_path):
    res = run(tmp_path, caseplan(var("a", "string"), var("b", "jsonSchema")))
    assert res.returncode == 0, res.stdout


def test_empty_string_default_passes(tmp_path):
    """The `file` type requires exactly this."""
    res = run(tmp_path, caseplan(var("doc", "file", default="")))
    assert res.returncode == 0, res.stdout


def test_no_caseplan_passes(tmp_path):
    res = run(tmp_path)
    assert res.returncode == 0
    assert "nothing to check" in res.stdout


# --- coverage across all three variable arrays -----------------------------------------

@pytest.mark.parametrize("arr", ["inputs", "outputs", "inputOutputs"])
def test_all_variable_arrays_scanned(tmp_path, arr):
    case = caseplan()
    case["variables"][arr] = [var("v", "jsonSchema", default={"a": 1})]
    res = run(tmp_path, case)
    assert res.returncode == 1, f"{arr} not scanned:\n{res.stdout}"
    assert f"variables.{arr}" in res.stdout


# --- guards ------------------------------------------------------------------------------

def test_venv_copies_ignored(tmp_path):
    v = tmp_path / ".venv" / "s"
    v.mkdir(parents=True)
    (v / "caseplan.json").write_text(json.dumps(caseplan(var("x", "jsonSchema", default={}))))
    res = run(tmp_path, caseplan(var("ok", "string", default="fine")))
    assert res.returncode == 0, res.stdout


def test_unparseable_caseplan_fails(tmp_path):
    d = tmp_path / "Sol" / "Proj"
    d.mkdir(parents=True)
    (d / "caseplan.json").write_text("{ not json")
    res = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                         capture_output=True, text=True)
    assert res.returncode == 1
    assert "unparseable" in res.stdout
