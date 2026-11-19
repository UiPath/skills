#!/usr/bin/env python3
"""Locate the submitted CustomerEscalationTriage process for every grader of this task.

The prompt states the CLI layout,
``CustomerEscalationTriageSolution/CustomerEscalationTriage/CustomerEscalationTriage.bpmn``,
and that exact path is graded first.
Studio Web cannot honour it: its export names the solution after the project and
gives every BPMN project the main file ``Process.bpmn``
(``CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn``).
Only that Studio Web shape is accepted in its place, found through the shared
``bpmn_check.resolve_bpmn_file`` (one ``Process.bpmn`` with ``project.uiproj``
beside it, in a project directory named ``CustomerEscalationTriage``), so a
CLI agent that ignores the stated layout still fails.

Run as a script, it prints the path (for the validate criterion) or exits
non-zero with a ``FAIL:`` line.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared import bpmn_check  # noqa: E402

PROJECT_NAME = "CustomerEscalationTriage"
BPMN_NAME = f"{PROJECT_NAME}.bpmn"
# The layout the prompt states (Node CLI).
CLI_BPMN_FILE = Path(f"{PROJECT_NAME}Solution") / PROJECT_NAME / BPMN_NAME


def bpmn_file(exclude_under: Iterable[Path] = ()) -> Path:
    """The submitted process file, relative to the sandbox root; exits ``FAIL:`` when absent."""
    if CLI_BPMN_FILE.is_file():
        return CLI_BPMN_FILE
    found = bpmn_check.resolve_bpmn_file(BPMN_NAME, exclude_under)
    if found.name != bpmn_check.STUDIO_WEB_MAIN_FILE:
        bpmn_check.fail(
            f"missing {CLI_BPMN_FILE} (the layout the prompt states); "
            f"found {found.relative_to(Path.cwd())} instead"
        )
    return found.relative_to(Path.cwd())


if __name__ == "__main__":
    print(bpmn_file())
