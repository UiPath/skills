"""The debug tasks accept both spellings of the debug-instance command group.

uipcli#5251 (uip 1.205.0) renamed `maestro bpmn debug-instance` to
`debug-instances` and kept the singular as a Commander alias. Studio Web run
`2026-11-16_09-25-49` scored agents zero for running the plural: the graders
matched only the singular, and the mocks answered it with `{}`. Each grader must
count both spellings, must not count `--help`, and the mocks must return fixture
data for both.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

_SHARED = Path(__file__).resolve().parent
_SUITE = _SHARED.parent
_DISPATCHER = _SHARED / "mock_template" / "mocks" / "uip"

_INSPECT = "debug/debug_instance_inspect_mocked"
_WORKFLOW = "debug/debug_workflow_mocked"
_LIVE = "debug/live_debug_e2e"


def _load(name: str, path: Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


_match_haystacks = _load("fault_triage_port", _SHARED / "test_fault_triage_mock_read_pattern.py")._match_haystacks
_matches = _load("mock_uip", _DISPATCHER)._matches


def _pattern(task_dir: str, description_part: str) -> re.Pattern[str]:
    yaml_path = _SUITE / task_dir / f"{Path(task_dir).name}.yaml"
    criteria = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["success_criteria"]
    found = [c["command_pattern"] for c in criteria if description_part in c["description"]]
    assert len(found) == 1, f"{task_dir}: expected one criterion matching {description_part!r}"
    return re.compile(found[0], re.DOTALL)


def _hits(pattern: re.Pattern[str], command: str) -> bool:
    return any(pattern.search(h) for h in _match_haystacks(command))


VERBS = ["debug-instances", "debug-instance"]

INSPECTIONS = [
    (_INSPECT, "read the debug session's incidents", "incidents debug-fault-777"),
    (_INSPECT, "inspected the debug session's runtime variables", "variables debug-fault-777"),
    (_INSPECT, "inspected the debug session's runtime variables", "variables-all debug-fault-777"),
    (_WORKFLOW, "inspected the debug instance's runtime variables", "variables debug-run-042"),
    (_WORKFLOW, "inspected the debug instance's runtime variables", "variables-all debug-run-042"),
    (_LIVE, "inspected the debug instance's runtime variables", 'variables-all "$INSTANCE_ID"'),
    (_LIVE, "inspected the debug instance's runtime variables", "variables 7c1e-instance"),
]


@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize(("task", "criterion", "tail"), INSPECTIONS)
def test_inspection_counts_either_spelling(task: str, criterion: str, tail: str, verb: str) -> None:
    assert _hits(_pattern(task, criterion), f"uip maestro bpmn {verb} {tail} --output json")


@pytest.mark.parametrize(
    "command",
    [
        "uip maestro bpmn debug-instances variables --help",
        "uip maestro bpmn debug-instance variables-all -h",
        "uip maestro bpmn debug-instancesX variables-all 7c1e-instance",
        "uip maestro bpmn instances variables 7c1e-instance --folder-key f",
        "uip maestro bpmn debug ProductCalc --output json",
    ],
)
def test_live_inspection_ignores_help_and_other_verbs(command: str) -> None:
    assert not _hits(_pattern(_LIVE, "inspected the debug instance's runtime variables"), command)


@pytest.mark.parametrize("group", ["instance", "instances", "debug-instance", "debug-instances"])
@pytest.mark.parametrize("op", ["retry", "cancel", "continue"])
def test_no_operate_guard_catches_both_spellings(group: str, op: str) -> None:
    guard = _pattern(_INSPECT, "did not operate the debug instance")
    assert _hits(guard, f"uip maestro bpmn {group} {op} debug-fault-777 --output json")


def test_no_operate_guard_allows_reads() -> None:
    guard = _pattern(_INSPECT, "did not operate the debug instance")
    assert not _hits(guard, "uip maestro bpmn debug-instances variables debug-fault-777 --output json")


MOCK_READS = [
    (_INSPECT, "incidents debug-fault-777", "debug-incidents.json"),
    (_INSPECT, "variables debug-fault-777", "debug-variables.json"),
    (_INSPECT, "variables-all debug-fault-777", "debug-variables-all.json"),
    (_WORKFLOW, "variables debug-run-042", "debug-variables.json"),
    (_WORKFLOW, "variables-all debug-run-042", "debug-variables-all.json"),
    (_WORKFLOW, "incidents debug-run-042", "debug-incidents-empty.json"),
]


@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize(("task", "tail", "expected_file"), MOCK_READS)
def test_mock_answers_either_spelling(task: str, tail: str, expected_file: str, verb: str) -> None:
    manifest = json.loads((_SUITE / task / "fixtures/mocks/responses/manifest.json").read_text(encoding="utf-8"))
    argv = f"maestro bpmn {verb} {tail} --output json"
    rule = next((r for r in manifest["rules"] if _matches(r["match"], argv)), None)
    assert rule is not None, f"{argv} falls through to unmocked_default"
    assert rule["file"] == expected_file
