"""Every committed case SDD parses clean through the installed `uip`.

Scope is `tests/tasks/uipath-maestro-case/` only. A glob across `tests/tasks`
would also collect planner documents (RPA SDDs, a PDD, an ASDD template) that
are correctly refused as case SDDs, and the pressure to make those pass is the
pressure to loosen this check.

Clean means `uip maestro case sdd parse` returns Success, at least one stage,
and no parse notes.

When a document is refused, never edit or regenerate it until it passes: that
shapes the corpus to fit the check, which is the failure this check exists to
catch. Give it exactly one verdict and record it in EXCLUDED:

1. generator-malformed: the skill that wrote it produced a real defect. The
   refusal stays; record the code, the line, and the skill that wrote it.
2. parser-false-positive: the document is valid and the check is wrong. The
   refusal stays and goes to the CLI as a bug; fix the check, not the input.
3. not-an-input: only when a grep, recorded in the entry, shows no task yaml
   references the file and nothing reads it. Then delete the file instead of
   listing it.
4. routing-input: the document is refused on purpose because its eval grades
   the route a refused SDD takes (case skill Rule 2 case (c): no receipt, parse
   fails, planner normalization). It goes in EXPECTED_REFUSALS, never EXCLUDED:
   the test then pins the exact refusal, so a new defect in the file, or a CLI
   that starts accepting it (and silently stops the eval exercising
   normalization), both fail here.

The degraded corpus is excluded wholesale: those documents are wrong on
purpose, and its own manifest says what each must do.

Needs `uip` on PATH. Skips without it unless REQUIRE_UIP=1 (set by the CI job
that installs it). Skips, in either case, when the installed CLI has no `sdd`
command: the check switches itself on once one is published.

Run from repo root:
    REQUIRE_UIP=1 pytest tests/tasks/uipath-maestro-case/_shared/test_sdd_corpus_parses_clean.py -rs
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

CASE_TASKS = Path(__file__).resolve().parents[1]
REPO_ROOT = CASE_TASKS.parents[2]

EXCLUDED_DIRS = {"degraded_sdd_conformance": "wrong on purpose; see its manifest.json"}
EXCLUDED = {}  # repo-relative path -> "<verdict>: <evidence>"

# repo-relative path -> the complete set of refusal messages parse must return.
EXPECTED_REFUSALS = {
    # routing-input: io_binding.yaml grades a hand-written SDD that writes the
    # non-template type `number`. Run 37494190705 (2026-10-06): parse refused these
    # three cells, the planner rewrote exactly them to `integer`, and the build
    # scored 1.00 — the normalization route the eval is kept to exercise.
    "tests/tasks/uipath-maestro-case/io_binding/fixtures/sdd.md": {
        f'Case Variables row "{name}" Type is "number". `number` is not a template type. '
        "Use integer for whole numbers, or float or double for decimals."
        for name in ("estimatedAge", "collisionCopy", "customReferenceCopy")
    },
}

CORPUS = sorted(
    p for p in CASE_TASKS.rglob("sdd.md")
    if not EXCLUDED_DIRS.keys() & set(p.relative_to(CASE_TASKS).parts)
    and str(p.relative_to(REPO_ROOT)) not in EXCLUDED
    and str(p.relative_to(REPO_ROOT)) not in EXPECTED_REFUSALS
)


def _parse(path):
    r = subprocess.run(
        ["uip", "maestro", "case", "sdd", "parse", str(path), "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def uip_with_sdd():
    if shutil.which("uip") is None:
        if os.environ.get("REQUIRE_UIP") == "1":
            pytest.fail("REQUIRE_UIP=1 but no `uip` on PATH")
        pytest.skip("no `uip` on PATH")
    probe = _parse(CORPUS[0])
    if "unknown command 'sdd'" in (probe.get("Message") or ""):
        pytest.skip("not checking: the installed CLI has no `sdd` command")


def test_corpus_is_the_expected_scope():
    assert CORPUS, "no case SDDs collected"
    for name in EXCLUDED_DIRS:
        assert (CASE_TASKS / name).is_dir(), f"excluded dir {name} no longer exists"
    for rel in [*EXCLUDED, *EXPECTED_REFUSALS]:
        assert (REPO_ROOT / rel).is_file(), f"listed file {rel} no longer exists"


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: str(p.relative_to(CASE_TASKS)))
def test_sdd_parses_clean(uip_with_sdd, path):
    d = _parse(path)
    assert d["Result"] == "Success", d.get("Message")
    model = d["Data"]["Model"]
    assert model["stages"], "parsed no stages"
    assert model["intake"]["parseNotes"] == []


@pytest.mark.parametrize("rel", sorted(EXPECTED_REFUSALS))
def test_routing_input_is_refused_exactly(uip_with_sdd, rel):
    d = _parse(REPO_ROOT / rel)
    assert d["Result"] == "Failure", (
        f"{rel} now parses whole: its eval no longer exercises planner normalization"
    )
    message = (d.get("Message") or "").split(" did not parse whole: ", 1)[-1]
    got = {m.strip() for m in message.split("; ") if m.strip()}
    assert got == EXPECTED_REFUSALS[rel], f"refusal changed: {got ^ EXPECTED_REFUSALS[rel]}"
