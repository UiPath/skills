"""A later turn's edit of an existing Flow must not lose the user's work.

Two ways it did (PILOT-9162, review of UiPath/skills#4281):
- `flow init <Name> --sdk-source --force` on an existing project resets
  `<Name>.flow` to a trigger-only stub and rewrites `project.uiproj` and
  `operate.json`. No instruction may pair `init` with `--force` except to forbid it.
- The generated `<Name>.pipeline.mjs` compiles a baseline only when none exists.
  A turn-1 baseline left in `.flow-sdk/` makes the turn-2 merge read an edit that
  matches it as "no change" and keep the canvas value. The editing loop must
  remove the pipeline's artifacts before its fresh decompile.

The artifact names are the pipeline's own (`BASELINE`, `EDITED`, `MERGED` in a
generated `.pipeline.mjs`, @uipath/maestro-builder-sdk 6.61.1).
Regex, not PyYAML: CI installs only pytest.
"""
from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
_SKILL = os.path.join(_REPO, "skills", "uipath-maestro-flow")
SKILL_PATH = os.path.join(_SKILL, "SKILL.md")
BROWNFIELD_PATH = os.path.join(_SKILL, "references", "brownfield.md")

PIPELINE_ARTIFACTS = (".flow-sdk/{n}.baseline", ".flow-sdk/{n}.edited", ".flow-sdk/{n}.merged.flow")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## )", text, re.S | re.M)
    assert match, f"missing section: ## {heading}"
    return match.group(1)


def _cleans_before_decompile(block: str, name: str) -> bool:
    lines = block.splitlines()
    decompile = next((i for i, line in enumerate(lines) if "flow decompile" in line), None)
    if decompile is None:
        return False

    before = "\n".join(lines[:decompile])
    return all("rm -rf" in before and path.format(n=name) in before for path in PIPELINE_ARTIFACTS)


def test_init_never_paired_with_force():
    offenders = []
    for path in (SKILL_PATH, BROWNFIELD_PATH):
        for number, line in enumerate(_read(path).splitlines(), 1):
            if "init" in line and "--force" in line and "never" not in line.lower():
                offenders.append(f"{os.path.relpath(path, _REPO)}:{number}: {line.strip()}")

    assert not offenders, "init with --force resets an existing project:\n" + "\n".join(offenders)


def test_editing_loop_clears_pipeline_artifacts_first():
    editing = _section(_read(SKILL_PATH), "Editing an existing flow")
    assert _cleans_before_decompile(editing, "<Name>"), (
        "## Editing an existing flow must `rm -rf` "
        + ", ".join(p.format(n="<Name>") for p in PIPELINE_ARTIFACTS)
        + " before `decompile`: a stale baseline drops the edit"
    )


def test_generated_pipeline_names_the_artifacts():
    pipeline = _section(_read(BROWNFIELD_PATH), "The generated pipeline")
    missing = [p.format(n="Deployed") for p in PIPELINE_ARTIFACTS if p.format(n="Deployed") not in pipeline]
    assert not missing, f"brownfield.md generated pipeline does not name: {missing}"
