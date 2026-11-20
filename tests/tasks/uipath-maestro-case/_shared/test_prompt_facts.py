"""Each path-to-ga Case prompt states the facts its grader asserts.

A fact is either in what the task already stages (the request, the SDD or the
request note) or in the helper block, which is where a fact the agent cannot
read elsewhere goes. Facts are read from the graders' own constants.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

CASE_ROOT = Path(__file__).resolve().parent.parent
HELPER = re.compile(r"<!-- helper:start -->(.*?)<!-- helper:end -->", re.S)
ISO_MINUTES = re.compile(r"PT(\d+)M")
STAGED_DOC_SUFFIXES = {".md"}

sys.path.insert(0, str(CASE_ROOT))
sys.path.insert(0, str(CASE_ROOT / "_setup"))


def _module(relative: str):
    path = CASE_ROOT / relative
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"facts_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minutes(iso: object) -> str:
    iso = str(iso)
    return f"{ISO_MINUTES.fullmatch(iso).group(1)} minutes"


def _asserted_duration(task: dict) -> str:
    """The ISO duration the json_check criteria pin, in either form: expected value or inside the expression."""
    for criterion in task["success_criteria"]:
        if criterion["type"] != "json_check":
            continue
        for assertion in criterion["assertions"]:
            found = ISO_MINUTES.search(f"{assertion['expression']} {assertion['expected']}")
            if found:
                return found.group(0)
    raise AssertionError("no timer duration asserted")


def _business_rule() -> tuple[list[str], list[str]]:
    grader = _module("single_node/business_rule/check_business_rule_run.py")
    return (
        [grader.RULE, str(grader.SCORE), grader.SCORE_FIELD, grader.BAND_FIELD],
        list(grader.BANDS),
    )


def _http_request() -> tuple[list[str], list[str]]:
    grader = _module("single_node/http_request/check_http_request_run.py")
    return (
        [grader.URL, grader.PROBE, grader.INVOICE, grader.QUERY_SOURCE, grader.BOUND_VAR, grader.ACCEPT_VALUE],
        [],
    )


def _io_binding() -> tuple[list[str], list[str]]:
    grader = _module("io_binding/check_io_binding_run.py")
    names = [name for name, *_ in grader.CHAIN]
    fields = {field for _, _, field, _ in grader.CHAIN}
    values = {value for *_, value in grader.CHAIN if value}
    literals = {v for v in values if not any(o != v and v.startswith(o) for o in values)}
    outputs = list(grader.NAMED_OUTPUTS) + ["metadataResult", "collisionCopy", "customReferenceCopy"]
    return names + sorted(fields) + sorted(literals) + outputs + [grader.CASE_ID_PREFIX], []


def _expense_runnable() -> tuple[list[str], list[str]]:
    grader = _module("_shared/check_expense_runnable_structure.py")
    sdd = (CASE_ROOT / "e2e_expense_runnable" / "fixtures" / "sdd.md").read_text(encoding="utf-8")
    renamed = [name for name in grader.REQUIRED_EXTERNAL_BINDINGS.values() if name not in sdd]
    return (
        list(grader.PRIMARY_STAGES)
        + list(grader.TERMINAL_LANES)
        + ["ExpenseReimbursementRunnable"]
        + list(grader.REQUIRED_EXTERNAL_BINDINGS.values()),
        renamed,
    )


def _contract_execution() -> tuple[list[str], list[str]]:
    grader = _module("golden_rebuild/contract_execution/check_contract_exec_bindings.py")
    return [grader.WITHDRAWN_STAGE, "ContractExecution", "ContractOperationsApi"], []


def _cm_golden() -> tuple[list[str], list[str]]:
    grader = _module("_shared/check_cm_golden_bindings.py")
    expected = grader.parse_fixture()
    return sorted(expected["resource_names"]) + ["CMGoldenExpense"], []


def _outcome_external() -> tuple[list[str], list[str]]:
    seed = _module("e2e_outcome_external/_setup/seed_outcome.py")
    probe = _module("e2e_outcome_external/_setup/outcome_probe.py")
    pins = json.loads((CASE_ROOT / "_setup" / "tenant_ids.json").read_text())["connections"]
    names = [pins[i]["name"] for i in seed.REQUIRED_CONNECTIONS.values() if "name" in pins[i]]
    return list(seed.REQUIRED_CONNECTIONS.values()) + names + [probe.JIRA_PROJECT], []


def _saved_plan() -> tuple[list[str], list[str]]:
    task = _load_task("edit/designer_saved_plan/designer_saved_plan.yaml")
    duration = _asserted_duration(task)
    return ["Stage 7 - user select", "Final cool-off", _minutes(duration)], []


def _stale_bindings() -> tuple[list[str], list[str]]:
    task = _load_task("edit/designer_stale_bindings/designer_stale_bindings.yaml")
    duration = _asserted_duration(task)
    return ["Wait for timer - S5", _minutes(duration)], []


def _load_task(relative: str) -> dict:
    return yaml.safe_load((CASE_ROOT / relative).read_text(encoding="utf-8"))


# task yaml -> (facts the graders assert, facts that must be in the helper block)
TASKS = {
    "single_node/business_rule/business_rule.yaml": _business_rule,
    "single_node/http_request/http_request.yaml": _http_request,
    "io_binding/io_binding.yaml": _io_binding,
    "e2e_expense_runnable/expense_runnable_e2e.yaml": _expense_runnable,
    "golden_rebuild/contract_execution/contract_execution.yaml": _contract_execution,
    "golden_rebuild/cm_golden_expense/cm_golden_expense.yaml": _cm_golden,
    "e2e_outcome_external/outcome_external_e2e.yaml": _outcome_external,
    "edit/designer_saved_plan/designer_saved_plan.yaml": _saved_plan,
    "edit/designer_stale_bindings/designer_stale_bindings.yaml": _stale_bindings,
}


def _staged_docs(task_dir: Path, task: dict) -> str:
    folders = [task_dir / "fixtures", task_dir / "_setup"]
    return "\n".join(
        path.read_text(encoding="utf-8")
        for folder in folders
        if folder.is_dir()
        for path in sorted(folder.rglob("*"))
        if path.suffix in STAGED_DOC_SUFFIXES
    )


def test_every_path_to_ga_task_is_covered() -> None:
    tagged = {
        str(path.relative_to(CASE_ROOT))
        for path in CASE_ROOT.rglob("*.yaml")
        if "path-to-ga" in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("tags", [])
    }

    assert tagged == set(TASKS)


@pytest.mark.parametrize("relative", sorted(TASKS))
def test_the_prompt_states_the_facts_its_grader_asserts(relative: str) -> None:
    task = _load_task(relative)
    asserted, helper_facts = TASKS[relative]()
    prompt = task["initial_prompt"]
    helper = " ".join(HELPER.findall(prompt))
    stated = prompt + "\n" + _staged_docs((CASE_ROOT / relative).parent, task)

    missing = [fact for fact in asserted if fact not in stated]
    missing_from_helper = [fact for fact in helper_facts if fact not in helper]

    assert not missing, f"asserted by the grader, stated nowhere the agent reads: {missing}"
    assert not missing_from_helper, f"must be in the helper block: {missing_from_helper}"


GUARD = (
    "Do not delete or overwrite anything this run did not create, except what the task "
    "asks you to change, and do not publish to a shared destination unless the task asks for it."
)


@pytest.mark.parametrize("relative", sorted(TASKS))
def test_the_opener_names_no_harness_and_carries_the_guard(relative: str) -> None:
    opener = " ".join(_load_task(relative)["initial_prompt"].split("\n\n")[0].split())
    assert opener.startswith("You are a coding agent in "), relative
    assert "Studio Web" not in opener, relative
    assert GUARD in opener, relative
