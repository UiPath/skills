from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
FLOW_TASKS = SHARED.parent


def run_script(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_simulated_hitl_checks_accept_root_sdk_emit(tmp_path: Path) -> None:
    flow = {
        "nodes": [
            {
                "id": "review",
                "type": "uipath.human-in-the-loop",
                "inputs": {
                    "type": "quick",
                    "priority": "High",
                    "schema": {
                        "fields": [
                            {
                                "id": "amount",
                                "label": "Amount",
                                "type": "number",
                                "direction": "input",
                            },
                            {
                                "id": "reason",
                                "label": "Reason",
                                "type": "text",
                                "direction": "output",
                            },
                        ],
                        "outcomes": [{"name": "Approve"}, {"name": "Reject"}],
                    },
                },
            },
            {
                "id": "log",
                "type": "core.action.script",
                "inputs": {"script": "return $vars.review.output.reason;"},
            },
        ],
        "edges": [
            {
                "sourceNodeId": "review",
                "sourcePort": "completed",
                "targetNodeId": "log",
                "targetPort": "input",
            }
        ],
    }
    (tmp_path / "Review.flow").write_text(json.dumps(flow))
    script = SHARED / "check_simulated_hitl.py"

    for check in ("expense", "priority", "quick-form", "schema"):
        result = run_script(script, check, cwd=tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr


def test_quick_form_check_accepts_specialized_node_type(tmp_path: Path) -> None:
    flow = {
        "nodes": [
            {
                "id": "review",
                "type": "uipath.human-in-the-loop.quick-form",
                "inputs": {},
            }
        ]
    }
    (tmp_path / "Review.flow").write_text(json.dumps(flow))

    result = run_script(SHARED / "check_simulated_hitl.py", "quick-form", cwd=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_quick_form_check_rejects_action_app_variant(tmp_path: Path) -> None:
    flow = {
        "nodes": [
            {
                "id": "review",
                "type": "uipath.human-in-the-loop",
                "inputs": {"type": "custom"},
            }
        ]
    }
    (tmp_path / "Review.flow").write_text(json.dumps(flow))

    result = run_script(SHARED / "check_simulated_hitl.py", "quick-form", cwd=tmp_path)

    assert result.returncode != 0
    assert "inline HITL quick form" in result.stderr


def test_solution_select_checks_use_selected_solution(tmp_path: Path) -> None:
    for name in ("SolarReports", "TideTracker"):
        directory = tmp_path / name
        directory.mkdir()
        (directory / f"{name}.uipx").write_text(json.dumps({"Projects": []}))

    selected = tmp_path / "WeatherSelection-7K4M"
    project = selected / "WeatherAlert"
    project.mkdir(parents=True)
    (selected / "WeatherSelection-7K4M.uipx").write_text(
        json.dumps({"Projects": [{"Name": "WeatherAlert", "Type": "Flow"}]})
    )
    (project / "project.uiproj").write_text(
        json.dumps({"Name": "WeatherAlert", "ProjectType": "Flow"})
    )
    (project / "WeatherAlert.flow").write_text(json.dumps({"nodes": []}))
    script = FLOW_TASKS / "interactive" / "check_solution_select.py"

    for check in (
        "existing-untouched",
        "flow",
        "no-extra-solution",
        "project",
        "solution",
    ):
        result = run_script(script, check, cwd=tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr


def test_solution_select_advisory_reports_extra_default_solution(
    tmp_path: Path,
) -> None:
    extra = tmp_path / "WeatherAlertSol"
    extra.mkdir()
    (extra / "WeatherAlertSol.uipx").write_text(json.dumps({"Projects": []}))
    script = FLOW_TASKS / "interactive" / "check_solution_select.py"

    result = run_script(script, "no-extra-solution", cwd=tmp_path)

    assert result.returncode != 0
    assert "unexpected default solution" in result.stderr
