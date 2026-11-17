"""The Studio Web Build-it check: compile over a clean skeleton, merge when the target holds more.

The check is the `node -e` command in the Studio Web flavor's Validation loop. It compares
the undo copy with step 1's baseline and prints what a compile would drop. Fixtures: a
Studio Web skeleton target, and the same target with a text annotation added on the canvas
(Studio Web's validator reports 0 errors on it); each `*.baseline.bpmn` is the compile of the
decompiled original (uip 1.207.0).

Run with:
    pytest tests/scripts/test_bpmn_build_it_check.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn" / "SKILL.md"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bpmn_build_it_check"


def _check_command() -> str:
    match = re.search(
        r"(node -e \".*?\") \.flow-sdk/original/<Name>\.bpmn <Draft>/baseline/<Name>\.bpmn",
        SKILL.read_text(),
    )
    assert match, "the Build-it check command is missing from the Studio Web SKILL.md"
    return match.group(1)


def _run(name: str) -> str:
    script = f'{_check_command()} "$1" "$2"'
    out = subprocess.run(
        ["bash", "-c", script, "check", str(FIXTURES / f"{name}.original.bpmn"), str(FIXTURES / f"{name}.baseline.bpmn")],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")


def test_clean_skeleton_compiles_over() -> None:
    assert _run("skeleton") == "none"


def test_canvas_annotation_forces_a_merge() -> None:
    assert "bpmn:textAnnotation" in _run("annotated").split()
