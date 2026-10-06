"""E4 degraded_sdd_conformance: the SDD gate does what each defect's `expect` says.

`uip maestro case sdd validate` runs on every fixture in manifest.json:

- reject-naming-line: exits non-zero and names the recorded line, as an
  issue's `Line` or, while a check still reports through the parse failure
  message, as "line <N>" in `Message`.
- reject-naming-document: exits non-zero; there is no line to name.
- read-as-seed: validate gives the seed's verdict (same exit code, same issues)
  plus, when one is recorded, exactly the defect's `warning` code at its line,
  and parse gives exactly the seed's Model, while the seed blob is unchanged.
  Seed-relative, not "exits zero": the seeds are hand-written, pre-template
  SDDs that the strict validate rejects on their own (no Planner Handoff, no
  task envelopes), and a defect read as its seed inherits that verdict.

Needs `uip` on PATH. Skips without it unless REQUIRE_UIP=1, and skips in
either case when the installed CLI has no `sdd validate`, so it switches
itself on once a build that has one is under test.

Run from repo root:
    REQUIRE_UIP=1 pytest tests/tasks/uipath-maestro-case/degraded_sdd_conformance/test_degraded_gate.py -rs
"""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
DEFECTS = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))["defects"]


def _uip(*args):
    r = subprocess.run(["uip", "maestro", "case", "sdd", *args, "--output", "json"],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, json.loads(r.stdout)


def _blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


@pytest.fixture(scope="module")
def gate():
    if shutil.which("uip") is None:
        if os.environ.get("REQUIRE_UIP") == "1":
            pytest.fail("REQUIRE_UIP=1 but no `uip` on PATH")
        pytest.skip("no `uip` on PATH")
    _, probe = _uip("validate", str(HERE / DEFECTS[0]["fixture"]))
    if "unknown command" in (probe.get("Message") or ""):
        pytest.skip("not checking: the installed CLI has no `sdd validate`")


@pytest.mark.parametrize("d", DEFECTS, ids=lambda d: d["defect_class"])
def test_gate_meets_expect(gate, d):
    code, out = _uip("validate", str(HERE / d["fixture"]))
    issues = (out.get("Data") or {}).get("Issues") or []
    expect = d["expect"]
    if expect == "reject-naming-document":
        assert code != 0, out
    elif expect == "reject-naming-line":
        assert code != 0, out
        lines = {i.get("Line") for i in issues if i.get("Severity") == "error"}
        assert d["line"] in lines or f"line {d['line']}" in (out.get("Message") or ""), out
    elif expect == "read-as-seed":
        seed = REPO_ROOT / d["seed"]
        if _blob(seed) != d["seed_blob"]:
            pytest.skip("seed fixture has since changed; cannot compare")
        seed_code, seed_out = _uip("validate", str(seed))
        assert code == seed_code, (code, seed_code, out)
        seed_issues = (seed_out.get("Data") or {}).get("Issues") or []

        def key(i):
            return (i.get("Code"), i.get("Severity"), i.get("Message"))

        extra = [i for i in issues if key(i) not in {key(j) for j in seed_issues}]
        missing = [j for j in seed_issues if key(j) not in {key(i) for i in issues}]
        assert not missing, f"fixture lost seed issues: {missing}"
        want_extra = []
        if "warning" in d:
            w = d["warning"]
            want_extra = [(w["code"], "warning", w["line"])]
        assert [(i.get("Code"), i.get("Severity"), i.get("Line")) for i in extra] == want_extra, extra
        _, got = _uip("parse", str(HERE / d["fixture"]))
        _, want = _uip("parse", str(seed))
        assert got["Data"]["Model"] == want["Data"]["Model"]
    else:
        pytest.fail(f"unknown expect {expect}")
