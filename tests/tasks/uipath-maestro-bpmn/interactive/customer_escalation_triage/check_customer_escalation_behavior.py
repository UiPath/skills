#!/usr/bin/env python3
"""Run the exact submitted escalation BPMN through live Alpha debug sessions.

The checker intentionally has no local BPMN interpreter. It validates the
submitted source, imports that exact project into one ephemeral solution, runs
hidden business scenarios in the Alpha runtime, inspects variables, element
executions, and incidents, and deletes every returned solution id in a finally
block. Repeated scenarios overwrite the same ephemeral solution rather than
creating tenant clutter.
"""

from __future__ import annotations

import hashlib
import json
import re
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = Path("CustomerEscalationTriage")
BPMN_FILE = PROJECT / "CustomerEscalationTriage.bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"

INPUT_TYPES = {
    "customerTier": "string",
    "crmMatchCount": "integer",
    "serviceState": "string",
    "workaroundAvailable": "boolean",
    "duplicateIssueKey": "string",
    "attachments": "array",
    "agentOutputValid": "boolean",
    "jiraAvailable": "boolean",
    "autoSendEnabled": "boolean",
    "businessImpact": "string",
    "correlationId": "string",
}
OUTPUT_TYPES = {
    "route": "string",
    "severity": "string",
    "engineeringNeeded": "boolean",
    "jiraAction": "string",
    "attachmentAction": "string",
    "slackAction": "string",
    "responseMode": "string",
    "caseKey": "string",
    "lastAttachmentName": "string",
    "failureReason": "string",
}


class CheckFailure(RuntimeError):
    pass


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_identifier(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def get_ci(value: Any, key: str, default: Any = None) -> Any:
    if not isinstance(value, dict):
        return default
    wanted = key.casefold()
    for candidate, item in value.items():
        if str(candidate).casefold() == wanted:
            return item
    return default


def parse_json_output(text: str, label: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    raise CheckFailure(f"{label} returned invalid JSON: {stripped[:1200]}")


def exact_type(value: Any, declared_type: str) -> bool:
    if declared_type == "string":
        return type(value) is str
    if declared_type == "boolean":
        return type(value) is bool
    if declared_type == "integer":
        return type(value) is int
    if declared_type == "number":
        return type(value) in (int, float)
    if declared_type == "array":
        return type(value) is list
    if declared_type == "object":
        return type(value) is dict
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Scenario:
    name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    attachment_iterations: tuple[str, ...] = ()
    uses_error_boundary: bool = False


def scenario(
    name: str,
    *,
    customer_tier: str = "Standard",
    crm_matches: int = 1,
    service_state: str = "Available",
    workaround: bool = True,
    duplicate_key: str = "",
    attachments: tuple[str, ...] = (),
    agent_valid: bool = True,
    jira_available: bool = True,
    auto_send: bool = False,
    expected: dict[str, Any],
    uses_error_boundary: bool = False,
) -> Scenario:
    correlation = f"EVAL/live-alpha/{name}#Exact"
    values = {
        "customerTier": customer_tier,
        "crmMatchCount": crm_matches,
        "serviceState": service_state,
        "workaroundAvailable": workaround,
        "duplicateIssueKey": duplicate_key,
        "attachments": [{"name": item} for item in attachments],
        "agentOutputValid": agent_valid,
        "jiraAvailable": jira_available,
        "autoSendEnabled": auto_send,
        "businessImpact": f"Hidden Alpha scenario {name}",
        "correlationId": correlation,
    }
    complete_expected = dict(expected)
    complete_expected["caseKey"] = correlation
    return Scenario(
        name=name,
        inputs=values,
        outputs=complete_expected,
        attachment_iterations=attachments
        if expected["attachmentAction"] == "SaveToDrive"
        else (),
        uses_error_boundary=uses_error_boundary,
    )


SCENARIOS = (
    scenario(
        "mixed-case-sev1-new-two-attachments",
        customer_tier="eNtErPrIsE",
        service_state="uNaVaIlAbLe",
        workaround=False,
        attachments=("outage.png", "trace.zip"),
        expected={
            "route": "NewEscalation",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "SaveToDrive",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "trace.zip",
            "failureReason": "",
        },
    ),
    scenario(
        "whitespace-duplicate-degraded",
        customer_tier="Enterprise",
        service_state="DeGrAdEd",
        workaround=True,
        duplicate_key="   \t ",
        auto_send=True,
        expected={
            "route": "NewEscalation",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "existing-sev3-jira-unavailable",
        service_state="AVAILABLE",
        duplicate_key="  JIRA-42  ",
        jira_available=False,
        auto_send=True,
        expected={
            "route": "ExistingIssue",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "UpdateExisting",
            "attachmentAction": "NoAttachments",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "crm-zero-precedes-agent-and-jira",
        crm_matches=0,
        service_state="Unavailable",
        workaround=False,
        agent_valid=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmNotFound",
        },
    ),
    scenario(
        "crm-ambiguous-precedes-agent",
        crm_matches=3,
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmAmbiguous",
        },
    ),
    scenario(
        "invalid-agent-single-match",
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "InvalidAgentOutput",
        },
    ),
    scenario(
        "jira-unavailable-sev2-typed-boundary",
        service_state="Unavailable",
        workaround=True,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "jira-unavailable-sev1-typed-boundary",
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "informational-auto-send-one-attachment",
        service_state="available",
        attachments=("receipt.pdf",),
        auto_send=True,
        expected={
            "route": "Informational",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "SaveToDrive",
            "slackAction": "NoAlert",
            "responseMode": "Send",
            "lastAttachmentName": "receipt.pdf",
            "failureReason": "",
        },
    ),
)


@dataclass(frozen=True)
class RuntimeContract:
    public_output_ids: dict[str, str]
    root_end_id: str
    parallel_split_id: str
    parallel_join_id: str
    marker_id: str
    error_end_id: str
    error_boundary_id: str


def direct_flow_counts(
    process: ET.Element,
) -> tuple[dict[str, int], dict[str, int]]:
    incoming: dict[str, int] = {}
    outgoing: dict[str, int] = {}
    for flow in process.findall(f"./{q(BPMN_NS, 'sequenceFlow')}"):
        source = flow.attrib["sourceRef"]
        target = flow.attrib["targetRef"]
        outgoing[source] = outgoing.get(source, 0) + 1
        incoming[target] = incoming.get(target, 0) + 1
    return incoming, outgoing


def load_runtime_contract(path: Path = BPMN_FILE) -> RuntimeContract:
    root = ET.parse(path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure("BPMN must contain one root process")

    root_ends = process.findall(f"./{q(BPMN_NS, 'endEvent')}")
    if len(root_ends) != 1:
        raise CheckFailure("live contract requires exactly one root end event")
    root_end_id = root_ends[0].attrib["id"]

    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        raise CheckFailure("root process is missing uipath:variables")
    public_inputs: dict[str, tuple[str, str]] = {}
    public_outputs: dict[str, tuple[str, str]] = {}
    for variable in variables:
        name = variable.attrib.get("name")
        identifier = variable.attrib.get("id")
        value_type = variable.attrib.get("type")
        element_id = variable.attrib.get("elementId")
        if not name or not identifier or not value_type:
            continue
        if local(variable.tag) == "input":
            public_inputs[name] = (value_type, element_id or "")
        elif local(variable.tag) == "output":
            public_outputs[name] = (value_type, element_id or "")

    if {
        name: item[0] for name, item in public_inputs.items()
    } != INPUT_TYPES:
        raise CheckFailure("public input declarations do not match the contract")
    if {
        name: item[0] for name, item in public_outputs.items()
    } != OUTPUT_TYPES:
        raise CheckFailure("public output declarations do not match the contract")
    if any(item[1] != root_end_id for item in public_outputs.values()):
        raise CheckFailure(
            "every public output must bind to the sole root completion end"
        )

    public_output_ids = {
        variable.attrib["name"]: variable.attrib["id"]
        for variable in variables
        if local(variable.tag) == "output"
        and variable.attrib.get("name") in OUTPUT_TYPES
    }

    incoming, outgoing = direct_flow_counts(process)
    parallels = process.findall(f"./{q(BPMN_NS, 'parallelGateway')}")
    splits = [
        item for item in parallels if outgoing.get(item.attrib["id"], 0) == 3
    ]
    joins = [
        item for item in parallels if incoming.get(item.attrib["id"], 0) == 3
    ]
    if len(splits) != 1 or len(joins) != 1:
        raise CheckFailure("expected one three-way parallel split and join")

    markers = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'scriptTask')}")
        if node.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        is not None
    ]
    if len(markers) != 1:
        raise CheckFailure(
            "expected one sequential multi-instance ScriptTask marker"
        )

    error_ends = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'endEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]
    boundaries = [
        node
        for node in process.findall(f"./{q(BPMN_NS, 'boundaryEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]
    if len(error_ends) != 1 or len(boundaries) != 1:
        raise CheckFailure("expected one typed error end and boundary")

    return RuntimeContract(
        public_output_ids=public_output_ids,
        root_end_id=root_end_id,
        parallel_split_id=splits[0].attrib["id"],
        parallel_join_id=joins[0].attrib["id"],
        marker_id=markers[0].attrib["id"],
        error_end_id=error_ends[0].attrib["id"],
        error_boundary_id=boundaries[0].attrib["id"],
    )


def run_cli(
    arguments: list[str],
    *,
    timeout: int,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [*arguments, "--output", "json"]
    if log_file is not None:
        command.extend(["--log-file", str(log_file)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def payload_data(
    completed: subprocess.CompletedProcess[str],
    label: str,
    *,
    require_success: bool = True,
) -> tuple[Any, Any]:
    payload = parse_json_output(
        completed.stdout or completed.stderr,
        label,
    )
    if require_success and (
        completed.returncode != 0
        or str(get_ci(payload, "Result", "")).casefold() != "success"
    ):
        message = get_ci(payload, "Message", "")
        instructions = get_ci(payload, "Instructions", "")
        raise CheckFailure(
            f"{label} failed (exit {completed.returncode}): "
            f"{message} {instructions}".strip()
        )
    return payload, get_ci(payload, "Data")


class AlphaSolutionLease:
    def __init__(self, solution_file: Path):
        self.solution_file = solution_file
        self.solution_ids: set[str] = set()
        self.cleaned = False

    def capture_payload(self, payload: Any) -> None:
        if isinstance(payload, list):
            for item in payload:
                self.capture_payload(item)
            return
        if not isinstance(payload, dict):
            return
        for key, value in payload.items():
            if str(key).casefold() == "solutionid" and isinstance(value, str):
                self.solution_ids.add(value)
            elif isinstance(value, (dict, list)):
                self.capture_payload(value)

    def capture_manifest(self) -> None:
        if not self.solution_file.is_file():
            return
        try:
            self.capture_payload(
                json.loads(self.solution_file.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            pass

    def cleanup(self) -> list[str]:
        if self.cleaned:
            return []
        self.capture_manifest()
        failures: list[str] = []
        for solution_id in sorted(self.solution_ids):
            completed = run_cli(
                ["uip", "solution", "delete", solution_id, "--yes"],
                timeout=180,
            )
            try:
                payload, _data = payload_data(
                    completed,
                    f"delete Alpha solution {solution_id}",
                )
                self.capture_payload(payload)
            except CheckFailure as exc:
                # A local SolutionId exists immediately after `solution init`.
                # If import/upload fails before Alpha sees it, deletion returns
                # 404 because there is no remote resource to clean up.
                detail = f"{completed.stdout}\n{completed.stderr}"
                if "404" not in detail and "Not Found" not in detail:
                    failures.append(str(exc))
        self.cleaned = True
        return failures


def root_scope(variables_data: Any) -> dict[str, Any]:
    scopes = get_ci(variables_data, "Variables", [])
    roots = [
        scope
        for scope in scopes
        if get_ci(scope, "ParentElementId") is None
    ]
    if len(roots) != 1:
        raise CheckFailure(
            f"variables-all returned {len(roots)} root scopes, expected one"
        )
    return roots[0]


def root_public_outputs(
    scope: dict[str, Any],
    contract: RuntimeContract,
) -> dict[str, Any]:
    globals_map = get_ci(scope, "Globals", {})
    by_id = {
        normalized_identifier(key): value
        for key, value in globals_map.items()
    }
    results: dict[str, Any] = {}
    for name, identifier in contract.public_output_ids.items():
        key = normalized_identifier(identifier)
        if key not in by_id:
            raise CheckFailure(
                f"runtime root globals are missing public output id "
                f"{identifier!r} ({name})"
            )
        results[name] = by_id[key]
    return results


def marker_outputs(
    scope: dict[str, Any],
    marker_id: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for element in get_ci(scope, "Elements", []):
        if (
            get_ci(element, "ElementId") != marker_id
            or get_ci(element, "IsMarker") is not True
        ):
            continue
        response = get_ci(get_ci(element, "Outputs", {}), "Response")
        name = response if type(response) is str else get_ci(response, "Name")
        if type(name) is not str:
            raise CheckFailure(
                f"marker {marker_id} returned a non-string attachment name"
            )
        values.append(name)
    return tuple(values)


def assert_scenario(
    case: Scenario,
    contract: RuntimeContract,
    debug_data: Any,
    variables_data: Any,
    incidents_data: Any,
) -> None:
    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in {"Completed", "Successful"}:
        raise CheckFailure(
            f"{case.name}: Alpha final status was {final_status!r}"
        )
    if not isinstance(incidents_data, list):
        raise CheckFailure(
            f"{case.name}: incidents response is not a list: "
            f"{incidents_data!r}"
        )
    incidents = incidents_data
    if incidents:
        raise CheckFailure(f"{case.name}: unexpected incidents: {incidents}")

    scope = root_scope(variables_data)
    actual_outputs = root_public_outputs(scope, contract)
    for name, expected in case.outputs.items():
        actual = actual_outputs.get(name)
        declared_type = OUTPUT_TYPES[name]
        if not exact_type(actual, declared_type):
            raise CheckFailure(
                f"{case.name}: output {name} expected exact type "
                f"{declared_type}, got {type(actual).__name__}: {actual!r}"
            )
        if actual != expected:
            raise CheckFailure(
                f"{case.name}: output {name} expected {expected!r}, "
                f"got {actual!r}"
            )

    iterations = marker_outputs(scope, contract.marker_id)
    if iterations != case.attachment_iterations:
        raise CheckFailure(
            f"{case.name}: attachment iterations expected "
            f"{case.attachment_iterations!r}, got {iterations!r}"
        )

    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = {
        get_ci(item, "ElementId")
        for item in executions
        if isinstance(item, dict)
    }
    required = {
        contract.parallel_split_id,
        contract.parallel_join_id,
        contract.root_end_id,
    }
    missing = required - executed_ids
    if missing:
        raise CheckFailure(
            f"{case.name}: live execution missed required root nodes "
            f"{sorted(missing)}"
        )
    error_nodes = {contract.error_end_id, contract.error_boundary_id}
    if case.uses_error_boundary:
        if not error_nodes <= executed_ids:
            raise CheckFailure(
                f"{case.name}: typed JiraUnavailable path did not execute "
                f"{sorted(error_nodes - executed_ids)}"
            )
    elif error_nodes & executed_ids:
        raise CheckFailure(
            f"{case.name}: unexpectedly executed JiraUnavailable error path"
        )


def tail_log(path: Path, limit: int = 5000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[-limit:]


def main() -> int:
    if not BPMN_FILE.is_file():
        raise CheckFailure(f"missing {BPMN_FILE}")
    contract = load_runtime_contract()
    original_hash = sha256(BPMN_FILE)

    validate = run_cli(
        ["uip", "maestro", "bpmn", "validate", str(BPMN_FILE)],
        timeout=180,
    )
    payload_data(validate, "offline BPMN validation")

    with tempfile.TemporaryDirectory(
        prefix="customer-escalation-live-alpha-"
    ) as directory:
        root = Path(directory)
        solution_dir = root / "CustomerEscalationLiveAlphaEval"
        initialized = run_cli(
            ["uip", "solution", "init", str(solution_dir)],
            timeout=120,
        )
        payload_data(initialized, "initialize ephemeral solution")
        solution_files = list(solution_dir.glob("*.uipx"))
        if len(solution_files) != 1:
            raise CheckFailure("solution init did not create exactly one .uipx")
        solution_file = solution_files[0]
        lease = AlphaSolutionLease(solution_file)
        cleanup_failures: list[str] = []
        pending_error: BaseException | None = None

        previous_sigterm = signal.getsignal(signal.SIGTERM)

        def stop_on_sigterm(_signum: int, _frame: Any) -> None:
            raise KeyboardInterrupt("terminated during live Alpha evaluation")

        signal.signal(signal.SIGTERM, stop_on_sigterm)
        try:
            imported = run_cli(
                [
                    "uip",
                    "solution",
                    "projects",
                    "import",
                    str(PROJECT.resolve()),
                    "--solutionFile",
                    str(solution_file),
                ],
                timeout=180,
            )
            payload_data(imported, "import exact BPMN project")
            imported_project = solution_dir / PROJECT.name
            imported_bpmn = imported_project / BPMN_FILE.name
            if sha256(imported_bpmn) != original_hash:
                raise CheckFailure(
                    "solution import changed the submitted BPMN bytes"
                )

            for index, case in enumerate(SCENARIOS, start=1):
                log_file = root / f"{index:02d}-{case.name}.log"
                debug = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug",
                        str(imported_project),
                        "--poll-interval",
                        "500",
                        "--inputs",
                        json.dumps(case.inputs, separators=(",", ":")),
                    ],
                    timeout=480,
                    log_file=log_file,
                )
                debug_payload = parse_json_output(
                    debug.stdout or debug.stderr,
                    f"{case.name} debug",
                )
                lease.capture_payload(debug_payload)
                lease.capture_manifest()
                debug_data = get_ci(debug_payload, "Data", {})
                instance_id = get_ci(debug_data, "InstanceId")
                if not isinstance(instance_id, str):
                    raise CheckFailure(
                        f"{case.name}: debug returned no instance id "
                        f"(exit {debug.returncode}); log: {tail_log(log_file)}"
                    )

                variables = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug-instance",
                        "variables-all",
                        instance_id,
                    ],
                    timeout=180,
                )
                variables_payload, variables_data = payload_data(
                    variables,
                    f"{case.name} variables-all",
                )
                lease.capture_payload(variables_payload)

                incidents = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug-instance",
                        "incidents",
                        instance_id,
                    ],
                    timeout=180,
                )
                incidents_payload, incidents_data = payload_data(
                    incidents,
                    f"{case.name} incidents",
                )
                lease.capture_payload(incidents_payload)

                try:
                    assert_scenario(
                        case,
                        contract,
                        debug_data,
                        variables_data,
                        incidents_data,
                    )
                except CheckFailure as exc:
                    raise CheckFailure(
                        f"{exc}; debug exit={debug.returncode}; "
                        f"debug={json.dumps(debug_payload)[:5000]}; "
                        f"variables={json.dumps(variables_data)[:5000]}; "
                        f"incidents={json.dumps(incidents_data)[:3000]}; "
                        f"log={tail_log(log_file)}"
                    ) from exc
                print(
                    f"PASS live Alpha {index}/{len(SCENARIOS)}: {case.name}"
                )
        except BaseException as exc:
            pending_error = exc
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
            cleanup_failures = lease.cleanup()

        if cleanup_failures:
            detail = "; ".join(cleanup_failures)
            if pending_error is not None:
                raise CheckFailure(
                    f"{pending_error}; Alpha cleanup also failed: {detail}"
                ) from pending_error
            raise CheckFailure(f"Alpha cleanup failed: {detail}")
        if pending_error is not None:
            raise pending_error

        deleted = ", ".join(sorted(lease.solution_ids))
        print(
            f"PASS: {len(SCENARIOS)} exact-artifact Alpha scenarios; "
            f"ephemeral solution deleted ({deleted})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
