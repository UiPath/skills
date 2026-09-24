import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TWINS = [
    ["bash", str(ROOT / "hooks/guard-case-plan.sh")],
    ["pwsh", "-NoProfile", "-File", str(ROOT / "hooks/guard-case-plan.ps1")],
]


def run_hook(hook, cwd: Path, target: Path) -> str:
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(cwd),
        "tool_name": "Write",
        "tool_input": {"file_path": str(target)},
    }
    result = subprocess.run(
        hook, input=json.dumps(payload), text=True, capture_output=True, check=True
    )
    return result.stdout


@pytest.mark.parametrize("hook", TWINS, ids=["bash", "pwsh"])
def test_requires_structured_plan_before_caseplan_write(hook, tmp_path):
    if shutil.which(hook[0]) is None:
        pytest.skip(f"{hook[0]} not available")
    (tmp_path / "sdd.md").write_text("# SDD\n", encoding="utf-8")
    target = tmp_path / "Solution/Project/caseplan.json"

    output = json.loads(run_hook(hook, tmp_path, target))
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "tasks/tasks.md" in decision["permissionDecisionReason"]

    plan = tmp_path / "tasks/tasks.md"
    plan.parent.mkdir()
    plan.write_text("# Implementation plan\nEverything is covered.\n", encoding="utf-8")
    assert json.loads(run_hook(hook, tmp_path, target))[
        "hookSpecificOutput"
    ]["permissionDecision"] == "deny"

    plan.write_text(
        "## Inventory\n\n## T01: Case\n## T02: Trigger\n## T03: Stage\n",
        encoding="utf-8",
    )
    assert run_hook(hook, tmp_path, target) == ""
