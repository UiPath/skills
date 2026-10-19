"""Every BPMN reference file stays under MAX_CHARS, so it is read whole.

A file over the cap gets split into an index plus parts, the way #3698 split
registry-workflow.md, structural-bpmn.md and local-metadata-regeneration-guide.md.
"""

from __future__ import annotations

import glob
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
REFERENCES = os.path.join(_REPO, "skills", "uipath-maestro-bpmn", "references")

MAX_CHARS = 15_000


def oversized(paths: list[str]) -> list[str]:
    problems = []
    for path in sorted(paths):
        with open(path, encoding="utf-8") as f:
            size = len(f.read())
        if size >= MAX_CHARS:
            problems.append(f"{os.path.relpath(path, _REPO)} is {size} chars")
    return problems


def test_references_fit_budget():
    paths = glob.glob(os.path.join(REFERENCES, "**", "*.md"), recursive=True)
    assert paths, f"no reference files under {REFERENCES}"

    problems = oversized(paths)
    assert not problems, (
        f"maximum is {MAX_CHARS} chars; split the file into an index and parts:\n  "
        + "\n  ".join(problems)
    )


def test_flags_a_file_at_the_cap(tmp_path):
    small = tmp_path / "small.md"
    small.write_text("x" * (MAX_CHARS - 1), encoding="utf-8")
    large = tmp_path / "large.md"
    large.write_text("x" * MAX_CHARS, encoding="utf-8")

    problems = oversized([str(small), str(large)])

    assert len(problems) == 1 and "large.md" in problems[0]
