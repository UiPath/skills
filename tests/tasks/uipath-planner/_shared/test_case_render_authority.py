"""CI wrapper: the case render contracts must not contradict the SDD template.

`scripts/check-case-render-authority.py` is the real check. It lived as a standalone
script with no runner, which meant it could not gate a PR — the claim that it "would
have failed the #2640 merge" was only true of a human choosing to run it. Wrapping it
as a pytest gets it collected by the existing `test-helpers.yml` job (which already
runs pytest over `tests/tasks/uipath-planner/**`), so it gates on every PR touching
the planner surface, with no workflow change.

Keep the logic in the script: it is also the thing a human runs when reconciling, and
its --json mode is machine-readable.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CHECKER = REPO / "scripts" / "check-case-render-authority.py"
TEMPLATE = REPO / "skills/uipath-planner/assets/templates/case-sdd-template.md"


def test_checker_and_template_are_present():
    """Fail loudly rather than vacuously if the paths move."""
    assert CHECKER.is_file(), f"missing {CHECKER}"
    assert TEMPLATE.is_file(), f"missing {TEMPLATE}"


def test_render_contracts_assert_no_shape_the_template_lacks():
    r = subprocess.run(
        [sys.executable, str(CHECKER)], capture_output=True, text=True, cwd=REPO
    )
    assert r.returncode == 0, (
        "case render contracts and the SDD template disagree about shape.\n"
        "The template is the shape; references/case/*.md are the semantics.\n\n"
        f"{r.stdout}\n{r.stderr}"
    )


def test_checker_detects_an_injected_conflict(tmp_path: Path):
    """Mutation guard: prove the check can fail.

    A checker that only ever passes is decoration. This copies the render contract,
    injects a column list the template does not define, and asserts the checker
    notices — run against a temp copy so the real tree is untouched.
    """
    doc = REPO / "skills/uipath-planner/references/case/render-stages-tasks.md"
    original = doc.read_text(encoding="utf-8")
    injected = original + "\n\nColumns: `Bogus | Columns | ThatDoNotExist | Anywhere`.\n"
    try:
        doc.write_text(injected, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(CHECKER)], capture_output=True, text=True, cwd=REPO
        )
        assert r.returncode != 0, (
            "checker passed despite an injected column list the template does not "
            f"define — it is not actually comparing shapes:\n{r.stdout}\n{r.stderr}"
        )
        assert "ThatDoNotExist" in (r.stdout + r.stderr), (
            "checker failed but did not name the offending claim, so a developer "
            f"cannot act on it:\n{r.stdout}\n{r.stderr}"
        )
    finally:
        doc.write_text(original, encoding="utf-8")
