"""Tests for the ProjectEuler RPA flow checker."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_rpa_flow.py")


def test_accepts_static_rpa_node_contract(tmp_path: Path) -> None:
    project = tmp_path / "ProjectEulerTitle" / "ProjectEulerTitle"
    project.mkdir(parents=True)
    flow = project / "ProjectEulerTitle.flow"
    flow.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "getTitle",
                        "type": "uipath.core.rpa-workflow.1234",
                        "inputs": {"problemId": 123},
                    },
                    {
                        "id": "end",
                        "type": "core.control.end",
                        "outputs": {
                            "title": {
                                "source": "=js:$vars.getTitle.output.title"
                            }
                        },
                    },
                ],
                "bindings": [
                    {
                        "resourceName": "ProjectEuler RPA",
                        "resourceSubType": "RPA Workflow",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
