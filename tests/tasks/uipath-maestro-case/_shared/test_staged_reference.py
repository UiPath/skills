"""A checker that imports `_shared/` must find it in the copy coder_eval stages.

coder_eval runs `$REFERENCE_DIR/...` from a copy of `reference.directory` only, and
`$TASK_DIR/...` from a copy of the task directory only (under docker). A checker
whose staged copy has no `_shared/` above it fails with ModuleNotFoundError on
every run, so the task scores zero.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

CASE_ROOT = Path(__file__).resolve().parents[1]
COMMAND = re.compile(r"\$(REFERENCE_DIR|TASK_DIR)/(\S+\.py)")


def _checker_runs():
    for task in sorted(CASE_ROOT.rglob("*.yaml")):
        if "_shared" in task.parts:
            continue
        spec = yaml.safe_load(task.read_text()) or {}
        if not isinstance(spec, dict):
            continue
        reference = (spec.get("reference") or {}).get("directory")
        for criterion in spec.get("success_criteria") or []:
            for var, rel in COMMAND.findall(str(criterion.get("command") or "")):
                staged = task.parent / (reference if var == "REFERENCE_DIR" and reference else ".")
                yield pytest.param(staged.resolve(), rel, id=f"{task.relative_to(CASE_ROOT)}:{rel}")


@pytest.mark.parametrize("staged_root,checker", list(_checker_runs()))
def test_shared_import_survives_staging(staged_root, checker):
    path = staged_root / checker
    assert path.is_file(), f"{checker} is not inside the staged copy {staged_root}"
    if "_shared" not in path.read_text():
        return
    ancestors = [p for p in path.parents if p == staged_root or staged_root in p.parents]
    assert any((p / "_shared").is_dir() for p in ancestors) or path.parent.name == "_shared", (
        f"{checker} imports _shared/, which its staged copy {staged_root} does not contain"
    )
