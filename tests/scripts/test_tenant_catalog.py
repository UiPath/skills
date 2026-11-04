"""Contract tests for tests/scripts/tenant_catalog.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import tenant_catalog as tc


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def task_yaml(task_id: str, body: str = "") -> str:
    return f"task_id: {task_id}\ninitial_prompt: Build it.\n" + textwrap.dedent(body)


@pytest.fixture
def tasks_root(tmp_path: Path) -> Path:
    root = tmp_path / "tasks"
    write(
        root / "demo" / "_setup" / "preflight.py",
        """
        import subprocess
        subprocess.run(["uip", "is", "connections", "list", "uipath-salesforce-slack", "--output", "json"])
        """,
    )
    return root


def report(tasks_root: Path) -> dict:
    return tc.to_json(tc.build_catalog("demo", tasks_root))


def task(result: dict, task_id: str) -> dict:
    return next(t for t in result["tasks"] if t["task_id"] == task_id)


def test_pre_run_helper_makes_the_task_hard_and_records_helper_and_connector(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "connector" / "connector.yaml",
        task_yaml(
            "demo-connector",
            """
            sandbox:
              template_sources:
                - type: template_dir
                  path: ../_setup
                  mount_point: _setup
            pre_run:
              - command: 'python3 "_setup/preflight.py"'
            """,
        ),
    )
    result = report(tasks_root)
    entry = task(result, "demo-connector")
    assert entry["tier"] == "hard"
    assert entry["helpers"] == ["preflight.py"]
    assert "connector:::uipath-salesforce-slack" in entry["dependencies"]
    assert entry["blocking"] == [{"dependency": "connector:::uipath-salesforce-slack", "disposition": "substitutable"}]
    assert entry["runs_on_automation_suite"] is False


def test_offline_grader_keeps_the_task_local(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "offline" / "offline.yaml",
        task_yaml(
            "demo-offline",
            """
            success_criteria:
              - type: run_command
                command: "uip maestro case validate Case/caseplan.case --output json"
            """,
        ),
    )
    assert task(report(tasks_root), "demo-offline")["tier"] == "local"


def test_imported_function_verbs_count_only_when_the_checker_calls_them(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "_shared" / "helpers.py",
        '''
        """Mentions `uip maestro case debug` in prose only."""

        def run_debug(path):
            return ["uip", "maestro", "case", "debug", path]

        def validate(path):
            return ["uip", "maestro", "case", "validate", path]
        ''',
    )
    write(tasks_root / "demo" / "_shared" / "check_live.py", "from helpers import run_debug\nrun_debug('x')\n")
    write(tasks_root / "demo" / "_shared" / "check_static.py", "from helpers import validate\nvalidate('x')\n")
    for name in ("live", "static"):
        write(
            tasks_root / "demo" / name / f"{name}.yaml",
            task_yaml(
                f"demo-{name}",
                f"""
                reference:
                  directory: ..
                success_criteria:
                  - type: run_command
                    command: "python3 $REFERENCE_DIR/_shared/check_{name}.py"
                """,
            ),
        )
    result = report(tasks_root)
    assert task(result, "demo-live")["tier"] == "hard"
    assert task(result, "demo-static")["tier"] == "local"


def test_wrapper_calls_with_literal_arguments_are_tenant_verbs(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "diag" / "check.py",
        """
        def uip(*args):
            pass
        uip("maestro", "case", "processes", "list")
        """,
    )
    write(
        tasks_root / "demo" / "diag" / "diag.yaml",
        task_yaml(
            "demo-diag",
            """
            success_criteria:
              - type: run_command
                command: "python3 $REFERENCE_DIR/check.py"
            """,
        ),
    )
    entry = task(report(tasks_root), "demo-diag")
    assert entry["tier"] == "hard"
    assert "maestro case processes" in entry["tier_evidence"][0]


def test_post_run_cleanup_does_not_raise_the_tier(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "_setup" / "cleanup.py",
        'import subprocess\nsubprocess.run(["uip", "solution", "delete", "x"])\n',
    )
    write(
        tasks_root / "demo" / "clean" / "clean.yaml",
        task_yaml(
            "demo-clean",
            """
            sandbox:
              template_sources:
                - type: template_dir
                  path: ../_setup
                  mount_point: _setup
            post_run:
              - command: "python3 _setup/cleanup.py"
            """,
        ),
    )
    assert task(report(tasks_root), "demo-clean")["tier"] == "local"


def test_sdd_task_detail_and_caseplan_binding_become_resources_and_folders(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "sdd" / "sdd.yaml",
        task_yaml(
            "demo-sdd",
            """
            description: The uip CLI is already authenticated.
            """,
        ),
    )
    write(
        tasks_root / "demo" / "sdd" / "fixtures" / "sdd.md",
        """
        **Type:** api-workflow

        **Resolved Resource:** WeatherAPI
        **Folder Path:** Shared/uipath-agents/WeatherAPI
        **Resource Identity:** be88b8d6-ec4d-484c-9474-805dd82d8d68
        **Binding Sub-Type:** Api
        """,
    )
    write(
        tasks_root / "demo" / "sdd" / "fixtures" / "caseplan.case",
        """
        {"bindings": [
          {"resource": "process", "resourceSubType": "Agent", "resourceKey": "Shared/Agents.Drafter",
           "propertyAttribute": "name", "default": "Drafter"},
          {"resource": "process", "resourceSubType": "Agent", "resourceKey": "Shared/Agents.Drafter",
           "propertyAttribute": "folderPath", "default": "Shared/Agents"}
        ]}
        """,
    )
    result = report(tasks_root)
    entry = task(result, "demo-sdd")
    assert entry["tier"] == "soft"
    assert "process:api:Shared/uipath-agents/WeatherAPI:WeatherAPI" in entry["dependencies"]
    assert "process:agent:Shared/Agents:Drafter" in entry["dependencies"]
    assert "folder:::Shared/uipath-agents/WeatherAPI" in entry["dependencies"]
    weather = next(d for d in result["dependencies"] if d["name"] == "WeatherAPI")
    assert weather["pinned_ids"] == ["be88b8d6-ec4d-484c-9474-805dd82d8d68"]
    assert weather["disposition"] == "creatable"


def test_connection_id_on_the_line_after_its_connector_key_is_pinned(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "conn" / "conn.yaml",
        task_yaml(
            "demo-conn",
            """
            initial_prompt: |
              Use the target tenant.
              **Connector Key:** `uipath-salesforce-slack`
              **Connection:** sandbox · **Connection ID:** `e03f734e-0f80-4e8a-a7c1-0ece309b0ca4`
            """,
        ),
    )
    slack = next(d for d in report(tasks_root)["dependencies"] if d["name"] == "uipath-salesforce-slack")
    assert slack["pinned_ids"] == ["e03f734e-0f80-4e8a-a7c1-0ece309b0ca4"]


def test_an_unknown_connector_is_unclassified_and_fails_strict(
    tasks_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write(
        tasks_root / "demo" / "new" / "new.yaml",
        task_yaml(
            "demo-new",
            """
            pre_run:
              - command: "uip is connections list uipath-acme-shipping --output json"
            """,
        ),
    )
    entry = task(report(tasks_root), "demo-new")
    assert entry["blocking"] == [{"dependency": "connector:::uipath-acme-shipping", "disposition": "unclassified"}]
    monkeypatch.setattr(tc, "TASKS_ROOT", tasks_root)
    assert tc.main(["--skill", "demo", "--strict", "--out", str(tasks_root / "out.json")]) == 1
    assert "connector:::uipath-acme-shipping" in capsys.readouterr().err


def test_ixp_project_calls_are_unavailable_on_automation_suite(tasks_root: Path) -> None:
    write(
        tasks_root / "demo" / "ixp" / "ixp.yaml",
        task_yaml(
            "demo-ixp",
            """
            success_criteria:
              - type: run_command
                command: "uip ixp projects list --output json"
            """,
        ),
    )
    entry = task(report(tasks_root), "demo-ixp")
    assert entry["blocking"] == [{"dependency": "service:::IXP projects", "disposition": "unavailable"}]


def test_every_tenant_dependency_in_the_case_suite_has_a_disposition() -> None:
    """A dependency added to a case task fails here until a rule in tenant_catalog.py classifies it."""
    result = tc.to_json(tc.build_catalog("uipath-maestro-case"))
    unclassified = sorted(
        {b["dependency"] for t in result["tasks"] for b in t["blocking"] if b["disposition"] == "unclassified"}
    )
    assert unclassified == []
    assert any(t["tier"] == "hard" for t in result["tasks"])
