"""The BYO connector grader accepts any folder and still checks the artifact."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS = REPO_ROOT / "tests/tasks/uipath-platform/llmgateway/custom-connector"
CHECKER = TASKS / "chat-bridge-e2e/check_byo_connector.py"
SPEC = importlib.util.spec_from_file_location("byo_connector_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def put_connector(root, key=checker.CONNECTOR_KEY):
    element_dir = root / "app/element"
    element_dir.mkdir(parents=True)
    (element_dir / "element.json").write_text(json.dumps({
        "key": key,
        "resources": [{"path": checker.FLAVOR_PATH, "method": "POST"}],
        "parameters": [{"vendorName": "x-api-key", "vendorType": "header"}],
    }))
    (element_dir / "element-metadata.json").write_text(json.dumps({
        "tags": checker.FLAVOR_TAG,
    }))
    return root


@pytest.mark.parametrize("folder", ["<root>", "acme-chat-bridge", "nested/Acme Chat Bridge"])
@pytest.mark.parametrize("workspace_arg", ["<absolute>", "."])
def test_finds_connector_in_chosen_directory(tmp_path, folder, workspace_arg):
    # "<root>": the connector sits at the workspace root itself. ".": the form
    # both task criteria pass, run from the workspace as the grader does.
    relative = Path(".") if folder == "<root>" else Path(folder)
    root = put_connector(tmp_path / relative)
    assert checker.resolve_connector_root(tmp_path) == root
    absolute = workspace_arg == "<absolute>"
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path) if absolute else ".", "--print-root"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{root if absolute else relative}\n"


@pytest.mark.parametrize("flags", [
    ["--print-roots"], ["--hook"], ["--hooks", "--verbose"], ["--hooks", "--print-root"],
])
def test_refuses_unknown_or_conflicting_flags(tmp_path, flags):
    put_connector(tmp_path / "chosen")
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path), *flags], capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert result.stdout == f"{checker.__doc__}\n"
    assert not result.stderr


def test_ignores_other_connectors_and_dependency_copies(tmp_path):
    expected = put_connector(tmp_path / "chosen")
    put_connector(tmp_path / "other", "design-acme-other")
    put_connector(tmp_path / "node_modules/copy")
    put_connector(tmp_path / ".agents/skills/copy")
    assert checker.resolve_connector_root(tmp_path) == expected


def test_rejects_a_different_connector_even_in_the_old_folder(tmp_path):
    put_connector(tmp_path / "periodic-design-acme-acmechatbridge", "design-acme-other")
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path)], capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "found 0" in result.stderr


@pytest.mark.parametrize("count", [0, 2])
def test_refuses_missing_or_ambiguous_connector(tmp_path, count):
    for index in range(count):
        put_connector(tmp_path / str(index))
    with pytest.raises(ValueError, match=f"found {count}"):
        checker.resolve_connector_root(tmp_path)
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tmp_path), "--print-root"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert not result.stdout


def test_discovery_keeps_static_and_hook_checks(tmp_path):
    root = put_connector(tmp_path / "chosen")
    command = [sys.executable, str(CHECKER), str(tmp_path)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    hooks = subprocess.run(command + ["--hooks"], capture_output=True, text=True)
    assert hooks.returncode == 1
    assert "FAIL  preRequest hook registered" in hooks.stdout
    element_path = root / "app/element/element.json"
    element = json.loads(element_path.read_text())
    element["parameters"] = []
    element_path.write_text(json.dumps(element))
    static = subprocess.run(command, capture_output=True, text=True)
    assert static.returncode == 1
    assert "FAIL  API key is sent in the x-api-key header" in static.stdout


@pytest.mark.parametrize("task", [
    "scaffold-smoke/scaffold-smoke.yaml", "chat-bridge-e2e/chat-bridge-e2e.yaml",
])
def test_both_tasks_use_discovery_for_both_graders(task):
    criteria = yaml.safe_load((TASKS / task).read_text())["success_criteria"]
    commands = [entry["command"] for entry in criteria if entry["type"] == "run_command"]
    assert len(commands) == 2
    assert commands[0] == (
        'CONNECTOR_ROOT=$(python3 "$REFERENCE_DIR/check_byo_connector.py" . --print-root)'
        ' && uip is connectors builder validate --connector-dir "$CONNECTOR_ROOT"'
    )
    assert all("\n" not in command for command in commands)
    assert '"$REFERENCE_DIR/check_byo_connector.py" .' in commands[1]
    assert ("--hooks" in commands[1]) == task.startswith("chat-bridge-e2e/")
