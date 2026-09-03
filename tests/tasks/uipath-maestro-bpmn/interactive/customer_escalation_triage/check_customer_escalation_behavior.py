#!/usr/bin/env python3
"""Run the exact submitted escalation BPMN through live Alpha debug sessions.

The checker intentionally has no local BPMN interpreter. It validates the
submitted source, imports that exact project into one ephemeral solution, runs
hidden business scenarios in the Alpha runtime, inspects variables, element
executions, and incidents, and deletes every returned solution id in a finally
block. Repeated scenarios overwrite the same ephemeral solution rather than
creating tenant clutter.

Cleanup is unconditional by default. Set `BPMN_E2E_CLEANUP=never` only for a
deliberate manual inspection: the run then prints the surviving solution ids
and whoever asked for the Alpha link owns deleting them. Connector side
effects are always cleaned, whatever the policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = Path("CustomerEscalationTriageSolution") / "CustomerEscalationTriage"
BPMN_FILE = PROJECT / "CustomerEscalationTriage.bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
CONNECTION_FOLDER_KEY = "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"
EXPECTED_LIVE_TARGET = {
    "BaseUrl": "https://alpha.uipath.com",
    "Organization": "codereval",
    "Tenant": "DefaultTenant",
}
RUN_NONCE = secrets.token_hex(6)
# Every UpdateExisting scenario seeds a real Jira issue first, and main
# overwrites duplicateIssueKey with that issue's key (padded, to prove the
# process trims it). The table carries this sentinel so nobody reads a fake
# key like "JIRA-42" as the value actually sent.
SEEDED_DUPLICATE_KEY = "__SEEDED_JIRA_KEY_SET_AT_RUNTIME__"
# Durable cleanup journal, relative to the sandbox CWD. The in-band leases
# free resources from a `finally` block, which a SIGKILL on the graded command
# skips entirely. Every created id is therefore appended here the moment it
# exists, so the task's post_run sweep can delete it even if this process is
# killed. See cleanup_customer_escalation.py.
CLEANUP_JOURNAL = Path(".customer-escalation-cleanup.jsonl")
# Per-scenario verdicts, written for the partial-credit json_check criteria.
# One binary run_command over 12 live scenarios cannot tell 11-of-12 from a
# submission that produced nothing, so the matrix records every scenario and
# the task grades outcome families separately. Scenarios keep running after a
# failure: a later family may still pass, and that is exactly the signal a
# single exit code destroys.
SCENARIO_RESULTS = Path(".customer-escalation-results.json")
# Outcome families. Each is graded as its own criterion so a submission that
# gets, say, classification right but attachments wrong scores accordingly.
SCENARIO_BUNDLES = {
    "classification": (
        "mixed-case-sev1-new-two-attachments",
        "whitespace-duplicate-degraded",
        "standard-tier-unavailable-no-workaround-sev2",
        "existing-sev1-jira-available",
    ),
    "precedence": (
        "crm-zero-precedes-agent-and-jira",
        "crm-ambiguous-precedes-agent",
        "invalid-agent-single-match",
    ),
    "fault_recovery": (
        "existing-sev3-jira-unavailable",
        "jira-unavailable-sev2-typed-boundary",
        "jira-unavailable-sev1-typed-boundary",
    ),
    "attachments_and_comms": (
        "informational-auto-send-one-attachment",
        "informational-auto-disabled-high-impact-context",
    ),
}
# Solution cleanup policy. Deleting is the DEFAULT and the unset behaviour:
# an eval run must not leave tenant clutter behind. Set
# BPMN_E2E_CLEANUP=never only for a deliberate manual inspection, when someone
# has asked for the Alpha link; the run then prints the surviving solution ids
# and it is that person's job to delete them. Connector side effects (Jira
# issues, Drive copies, Slack messages) are ALWAYS cleaned regardless: they
# live in shared external sandboxes, not in the solution under inspection.
CLEANUP_POLICY_ENV = "BPMN_E2E_CLEANUP"


def solution_cleanup_policy() -> str:
    """Return `always` (delete, the default) or `never` (preserve)."""

    policy = os.environ.get(CLEANUP_POLICY_ENV, "always").strip().casefold()
    if policy not in {"always", "never"}:
        print(
            f"WARNING {CLEANUP_POLICY_ENV}={policy!r} is not always|never; "
            "falling back to always (delete)"
        )
        return "always"
    return policy
# Timeout budget. The single load-bearing number is the run_command
# `timeout` in customer_escalation_triage.yaml, mirrored here as
# GRADER_TIMEOUT_SECONDS — coder_eval SIGKILLs this process there, and nothing
# below can outlive it. Everything else is derived from the observed worst case
# for one scenario:
#
#   debug (DEBUG_TIMEOUT_SECONDS)                             480s
#   + Jira seed, variables-all, incidents, up to 3 Drive gets,
#     one Jira get, and per-scenario side-effect cleanup        180s
#   = SCENARIO_BUDGET_SECONDS                                   660s
#
# 12 scenarios x 660s = 7920s, inside the 8200s LIVE_RUN_DEADLINE_SECONDS
# below (683s per scenario). The matrix stops at a clean scenario boundary
# rather than mid-scenario, and the remaining window is reserved for the final
# cleanup sweep so an overrun never leaks live resources. The sweep normally
# has almost nothing to do because each scenario cleans up after itself, and
# post_run backstops whatever it still cannot reach.
#
# Adding scenarios means raising GRADER_TIMEOUT_SECONDS and the YAML timeout
# together, which eats into the agent's authoring window — see the arithmetic
# in the task YAML's run_limits.
DEBUG_TIMEOUT_SECONDS = 480
SCENARIO_BUDGET_SECONDS = 660
# MUST match the run_command timeout in customer_escalation_triage.yaml.
GRADER_TIMEOUT_SECONDS = 9600
# 600s of slack under the hard SIGKILL, enforced by
# test_live_checker_keeps_outer_timeout_cleanup_reserve.
LIVE_CLEANUP_DEADLINE_SECONDS = GRADER_TIMEOUT_SECONDS - 600
LIVE_CLEANUP_RESERVE_SECONDS = 800
LIVE_RUN_DEADLINE_SECONDS = (
    LIVE_CLEANUP_DEADLINE_SECONDS - LIVE_CLEANUP_RESERVE_SECONDS
)

ACTIVE_CLI_DEADLINE: float | None = None

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
REQUIRED_CONNECTORS = {
    ("uipath-atlassian-jira", "/curated_create_issue"): "jira_create_id",
    (
        "uipath-atlassian-jira",
        "/curated_edit_issue/{issueIdOrKey}",
    ): "jira_update_id",
    ("uipath-google-drive", "/copyFile"): "drive_copy_id",
    (
        "uipath-salesforce-slack",
        "/send_message_to_channel_v2",
    ): "slack_send_id",
}

class CheckFailure(RuntimeError):
    pass


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_identifier(value: object) -> str:
    """Loose id key used only as a fallback after an exact match fails.

    The runtime has been observed to re-case and re-punctuate variable ids
    between the BPMN source and the PIMS globals map, so lookups fall back to
    this form. It is intentionally lossy — `caseKey` and `case_key` collapse
    to the same key — so every caller must try the exact id first and treat a
    fallback hit that is ambiguous as a failure rather than a match.
    """

    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def resolve_runtime_key(
    mapping: dict[str, Any],
    identifier: str,
    label: str,
) -> Any:
    """Read `identifier` out of a runtime map, exactly where possible."""

    if identifier in mapping:
        return mapping[identifier]
    wanted = normalized_identifier(identifier)
    matches = [
        key for key in mapping if normalized_identifier(key) == wanted
    ]
    if not matches:
        raise CheckFailure(
            f"runtime map is missing {identifier!r} ({label})"
        )
    if len(matches) > 1:
        raise CheckFailure(
            f"{identifier!r} ({label}) matches multiple runtime ids "
            f"{sorted(matches)}; ids must be distinct beyond casing and "
            "punctuation so the graded value is unambiguous"
        )
    return mapping[matches[0]]


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
    business_impact: str | None = None,
    expected: dict[str, Any],
    uses_error_boundary: bool = False,
) -> Scenario:
    correlation = f"EVAL-live-alpha-{RUN_NONCE}-{name}-Exact"
    values = {
        "customerTier": customer_tier,
        "crmMatchCount": crm_matches,
        "serviceState": service_state,
        "workaroundAvailable": workaround,
        "duplicateIssueKey": duplicate_key,
        "attachments": [
            {"name": item, "driveFileId": "__DRIVE_SOURCE_FILE_ID__"}
            for item in attachments
        ],
        "agentOutputValid": agent_valid,
        "jiraAvailable": jira_available,
        "autoSendEnabled": auto_send,
        "businessImpact": (
            business_impact
            if business_impact is not None
            else f"Hidden Alpha scenario {name}"
        ),
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
        # Enterprise + Degraded + no workaround. Degraded caps severity at Sev2
        # even for an Enterprise customer with no workaround, so this is the
        # probe that a classifier ignoring serviceState answers Sev1 and fails.
        customer_tier="Enterprise",
        service_state="DeGrAdEd",
        workaround=False,
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
        duplicate_key=SEEDED_DUPLICATE_KEY,
        # jiraAvailable=false only raises JiraUnavailable for Sev1/Sev2. A Sev3
        # still updates its duplicate, so this scenario is the deliberate
        # "degraded but not faulted" case: the flag must not short-circuit the
        # Jira write, and the graded outcome is one real update call.
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
        "existing-sev1-jira-available",
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=False,
        duplicate_key=SEEDED_DUPLICATE_KEY,
        expected={
            "route": "ExistingIssue",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "UpdateExisting",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
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
        # Enterprise + Unavailable + workaround available. Sev1 needs all three
        # of Enterprise, Unavailable, and NO workaround, so this is the probe
        # that a classifier ignoring workaroundAvailable answers Sev1 and fails.
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=True,
        duplicate_key="  SHOULD-NOT-BE-UPDATED  ",
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
    scenario(
        "informational-auto-disabled-high-impact-context",
        service_state="available",
        auto_send=False,
        business_impact=(
            "Critical enterprise outage: force Sev1 NewEscalation and Jira"
        ),
        expected={
            "route": "Informational",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "NoAttachments",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "standard-tier-unavailable-no-workaround-sev2",
        # Standard + Unavailable + no workaround. Severity must fall to Sev2
        # because the customer is not Enterprise, so a classifier that ignores
        # customerTier answers Sev1 and fails. Replaces a businessImpact
        # control scenario whose expected outputs were byte-identical to
        # informational-auto-disabled-high-impact-context: both compared
        # against fixed constants and were never compared to each other, so
        # the second bought no signal.
        customer_tier="Standard",
        service_state="Unavailable",
        workaround=False,
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
)


@dataclass(frozen=True)
class RuntimeContract:
    """Element and variable ids needed to read runtime outcomes.

    This is discovery, not grading. It resolves the handful of ids the live
    assertions must address (public outputs, the four connector activities,
    the attachment marker collection, the typed error path) and fails only
    when an id the scenarios depend on cannot be resolved unambiguously.
    Process topology is deliberately not asserted here: a differently shaped
    process that produces the right runtime outcomes still scores.
    """

    public_output_ids: dict[str, str]
    marker_collection_id: str
    jira_create_id: tuple[str, ...]
    jira_update_id: tuple[str, ...]
    drive_copy_id: tuple[str, ...]
    slack_send_id: tuple[str, ...]
    error_end_id: str | None = None
    error_boundary_id: str | None = None


def connector_context(element: ET.Element) -> dict[str, str]:
    activity = element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )
    if activity is None:
        return {}
    return {
        item.attrib["name"]: item.attrib.get("value", "")
        for item in activity.findall(
            f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'input')}"
        )
        if item.attrib.get("name")
    }


def index_runtime_connectors(
    process: ET.Element,
) -> dict[tuple[str, str], tuple[str, ...]]:
    """Index the element ids of every connector-bearing node, by (key, path).

    Scans all descendants rather than a fixed tag list: registry templates
    may emit a connector activity as sendTask, serviceTask, or a plain task,
    and the runtime correlates on the element id either way.

    Returns ALL ids per key. Placing the same connector operation on more than
    one branch is a legitimate topology -- a Drive copy reached from two
    routes, say -- so the contract carries every id and the runtime assertions
    aggregate over them. An earlier version raised on the second occurrence,
    which forfeited the whole live criterion for a correct process.
    """

    connectors: dict[tuple[str, str], list[str]] = {}
    for node in process.iter():
        identifier = node.attrib.get("id")
        if not identifier:
            continue
        context = connector_context(node)
        key = (context.get("connectorKey", ""), context.get("path", ""))
        if not all(key):
            continue
        connectors.setdefault(key, []).append(identifier)
    return {key: tuple(ids) for key, ids in connectors.items()}


def load_runtime_contract(path: Path = BPMN_FILE) -> RuntimeContract:
    root = ET.parse(path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure("BPMN must contain one root process")

    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        raise CheckFailure("root process is missing uipath:variables")

    public_output_ids: dict[str, str] = {}
    for variable in variables:
        if local(variable.tag) != "output":
            continue
        name = variable.attrib.get("name")
        identifier = variable.attrib.get("id")
        if not name or not identifier or name not in OUTPUT_TYPES:
            continue
        if name in public_output_ids:
            raise CheckFailure(
                f"public output {name!r} is declared more than once, so its "
                "runtime value cannot be addressed"
            )
        public_output_ids[name] = identifier
    missing_outputs = sorted(set(OUTPUT_TYPES) - set(public_output_ids))
    if missing_outputs:
        raise CheckFailure(
            "public outputs the scenarios read are not declared: "
            f"{missing_outputs}"
        )

    markers = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'subProcess')}")
        if node.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        is not None
    ]
    marker_collection_ids = {
        item.attrib["var"]
        for node in markers
        for item in node.findall(
            f"./{q(BPMN_NS, 'extensionElements')}/"
            f"{q(UIPATH_NS, 'mapping')}/{q(UIPATH_NS, 'output')}"
        )
        if item.attrib.get("custom") == "true"
        and item.attrib.get("type") == "string"
        and item.attrib.get("var")
    }
    if len(marker_collection_ids) != 1:
        raise CheckFailure(
            "expected exactly one per-attachment marker collection to read "
            f"at runtime, found {sorted(marker_collection_ids)}"
        )
    marker_collection_id = next(iter(marker_collection_ids))

    connectors = index_runtime_connectors(process)
    missing_connectors = sorted(set(REQUIRED_CONNECTORS) - set(connectors))
    if missing_connectors:
        raise CheckFailure(
            "connector activities the scenarios read are absent: "
            f"{missing_connectors}"
        )

    error_ends = [
        node.attrib["id"]
        for node in process.findall(f".//{q(BPMN_NS, 'endEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]
    boundaries = [
        node.attrib["id"]
        for node in process.findall(f".//{q(BPMN_NS, 'boundaryEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]

    return RuntimeContract(
        public_output_ids=public_output_ids,
        marker_collection_id=marker_collection_id,
        # The typed error path is optional here: scenarios that raise
        # JiraUnavailable already assert it through the failureReason output,
        # so a process that models the fault differently is not penalised.
        error_end_id=error_ends[0] if len(error_ends) == 1 else None,
        error_boundary_id=boundaries[0] if len(boundaries) == 1 else None,
        **{
            attribute: connectors[key]
            for key, attribute in REQUIRED_CONNECTORS.items()
        },
    )


def run_cli(
    arguments: list[str],
    *,
    timeout: int,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    effective_timeout: float = timeout
    if ACTIVE_CLI_DEADLINE is not None:
        remaining = ACTIVE_CLI_DEADLINE - time.monotonic()
        if remaining <= 0:
            raise CheckFailure(
                "live Alpha operation deadline reached before running "
                f"{' '.join(arguments[:5])}"
            )
        effective_timeout = min(effective_timeout, remaining)
    command = [*arguments, "--output", "json"]
    if log_file is not None:
        command.extend(["--log-file", str(log_file)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=effective_timeout,
    )


@dataclass
class CleanupSignalState:
    termination_requested: bool = False
    cleanup_started: bool = False

    def begin_cleanup(self) -> None:
        self.cleanup_started = True

    def handle(self, _signum: int, _frame: Any) -> None:
        if self.cleanup_started or self.termination_requested:
            self.termination_requested = True
            return
        self.termination_requested = True
        raise KeyboardInterrupt("terminated during live Alpha evaluation")


def collect_cleanup_failures(
    stages: tuple[tuple[str, Any], ...],
    *,
    emit_benchmarks: bool = False,
) -> list[str]:
    failures: list[str] = []
    for label, cleanup in stages:
        started = time.monotonic()
        interrupted = False
        try:
            while True:
                try:
                    failures.extend(cleanup())
                    break
                except KeyboardInterrupt as exc:
                    deadline_expired = (
                        ACTIVE_CLI_DEADLINE is not None
                        and time.monotonic() >= ACTIVE_CLI_DEADLINE
                    )
                    if interrupted or deadline_expired:
                        failures.append(
                            f"{label} cleanup raised unexpectedly: {exc}"
                        )
                        break
                    interrupted = True
        except BaseException as exc:
            failures.append(f"{label} cleanup raised unexpectedly: {exc}")
        finally:
            if emit_benchmarks:
                print(
                    f"BENCHMARK stage=cleanup-{label.replace(' ', '-')} "
                    f"duration_seconds={time.monotonic() - started:.3f}"
                )
    return failures


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


def assert_live_target() -> dict[str, str]:
    completed = run_cli(["uip", "login", "status"], timeout=60)
    _payload, data = payload_data(completed, "read active UiPath login")
    if not isinstance(data, dict):
        raise CheckFailure("UiPath login status returned no data object")
    if str(get_ci(data, "Status", "")).casefold() != "logged in":
        raise CheckFailure("UiPath CLI is not logged in")
    actual = {
        key: str(get_ci(data, key, "")).rstrip("/")
        for key in EXPECTED_LIVE_TARGET
    }
    expected = {
        key: value.rstrip("/")
        for key, value in EXPECTED_LIVE_TARGET.items()
    }
    if actual != expected:
        raise CheckFailure(
            f"live grader must target {expected}, active profile is {actual}"
        )
    return expected


class JournaledSet(set):
    """Set that durably records every addition to the cleanup journal."""

    def __init__(self, kind: str, journal: Path | None = None):
        super().__init__()
        self.kind = kind
        # Resolved per append so a test (or the post_run sweep) can redirect
        # the journal by patching the module constant.
        self.journal = journal

    def add(self, value: Any) -> None:
        super().add(value)
        journal = self.journal if self.journal is not None else CLEANUP_JOURNAL
        try:
            with journal.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps({"kind": self.kind, "value": value}) + "\n"
                )
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            # Cleanup journalling is a backstop; never fail a live scenario
            # because the sandbox filesystem rejected the append.
            pass


class AlphaSolutionLease:
    def __init__(self, solution_file: Path):
        self.solution_file = solution_file
        self.solution_ids: set[str] = JournaledSet("solution")
        self.removed_solution_ids: set[str] = set()
        self.cleaned = False

    def capture_manifest(self) -> None:
        if not self.solution_file.is_file():
            return
        try:
            payload = json.loads(
                self.solution_file.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return
        solution_id = get_ci(payload, "SolutionId")
        if not isinstance(solution_id, str) or not re.fullmatch(
            r"[0-9a-fA-F]{8}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{12}",
            solution_id,
        ):
            return
        self.solution_ids.add(solution_id)
        if solution_id not in self.removed_solution_ids:
            self.cleaned = False

    def cleanup(self) -> list[str]:
        self.capture_manifest()
        if solution_cleanup_policy() == "never":
            for solution_id in sorted(self.solution_ids):
                print(
                    f"PRESERVED Alpha solution {solution_id} "
                    f"({EXPECTED_LIVE_TARGET['BaseUrl']}/"
                    f"{EXPECTED_LIVE_TARGET['Organization']}/"
                    f"{EXPECTED_LIVE_TARGET['Tenant']}) — "
                    f"{CLEANUP_POLICY_ENV}=never was set, so delete it by hand"
                )
            if not self.solution_ids:
                print(
                    f"{CLEANUP_POLICY_ENV}=never was set but no solution id "
                    "was captured, so nothing was preserved"
                )
            self.cleaned = True
            return []
        failures: dict[str, str] = {}
        for _attempt in range(2):
            pending = self.solution_ids - self.removed_solution_ids
            if not pending:
                break
            for solution_id in sorted(pending):
                completed: subprocess.CompletedProcess[str] | None = None
                try:
                    completed = run_cli(
                        [
                            "uip",
                            "solution",
                            "delete",
                            solution_id,
                            "--yes",
                        ],
                        timeout=180,
                    )
                    _payload, _data = payload_data(
                        completed,
                        f"delete Alpha solution {solution_id}",
                    )
                except Exception as exc:
                    # A local SolutionId exists immediately after
                    # `solution init`. If import/upload fails before Alpha sees
                    # it, deletion returns 404 because no remote resource
                    # exists. Treat that as an idempotent cleanup success.
                    if (
                        completed is not None
                        and delete_target_is_absent(
                            completed,
                            "solution",
                            solution_id,
                        )
                    ):
                        self.removed_solution_ids.add(solution_id)
                        failures.pop(solution_id, None)
                    else:
                        failures[solution_id] = str(exc)
                else:
                    self.removed_solution_ids.add(solution_id)
                    failures.pop(solution_id, None)
        pending = self.solution_ids - self.removed_solution_ids
        self.cleaned = not pending
        return [
            failures.get(
                solution_id,
                f"delete Alpha solution {solution_id} did not complete",
            )
            for solution_id in sorted(pending)
        ]


@dataclass(frozen=True)
class LiveEnvironment:
    jira_connection_id: str
    drive_connection_id: str
    slack_connection_id: str
    jira_project_key: str = "CE"
    jira_issue_type_id: str = "11457"
    jira_reporter_account_id: str = (
        "712020:b53bf3dc-8817-419e-99e1-5670aeb7ffe6"
    )
    slack_channel_id: str = "C01H4SPS77W"
    drive_destination_folder_id: str = "0AKHXBGF_5DaVUk9PVA"
    drive_source_file_ids: tuple[str, str] = (
        "1YlblU34Vd6RvCkamYw5BWejdX8ES-Zzy",
        "1tj2Pn1vIL0s6IB8W4eA5vwA10heyTwyS",
    )


def discover_live_environment() -> LiveEnvironment:
    listed = run_cli(
        ["uip", "is", "connections", "list", "--all-folders"],
        timeout=180,
    )
    _payload, rows = payload_data(listed, "discover connector connections")
    if not isinstance(rows, list):
        raise CheckFailure("connector discovery returned no list")
    wanted = {
        "uipath-atlassian-jira": (
            "is-sandboxes-test@uipath.com-uipath-sandbox-380"
        ),
        "uipath-google-drive": "is.sandboxes.test@gmail.com",
        "uipath-salesforce-slack": "is-sandboxes",
    }
    ids: dict[str, str] = {}
    for connector_key, name in wanted.items():
        matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and get_ci(row, "ConnectorKey") == connector_key
            and get_ci(row, "Name") == name
            and get_ci(row, "FolderKey") == CONNECTION_FOLDER_KEY
            and str(get_ci(row, "State") or "").casefold() == "enabled"
        ]
        if len(matches) != 1:
            raise CheckFailure(
                f"expected one enabled {connector_key} connection named "
                f"{name!r}, found {len(matches)}"
            )
        identifier = get_ci(matches[0], "Id")
        if not isinstance(identifier, str):
            raise CheckFailure(f"{connector_key} connection has no id")
        ids[connector_key] = identifier

    for connector_key, connection_id in ids.items():
        pinged = run_cli(
            ["uip", "is", "connections", "ping", connection_id],
            timeout=120,
        )
        payload_data(pinged, f"ping {connector_key} connection")

    environment = LiveEnvironment(
        jira_connection_id=ids["uipath-atlassian-jira"],
        drive_connection_id=ids["uipath-google-drive"],
        slack_connection_id=ids["uipath-salesforce-slack"],
    )
    require_distinct_drive_source_fixtures(environment)
    return environment


def scenario_inputs(
    case: Scenario,
    environment: LiveEnvironment,
    *,
    duplicate_key: str | None = None,
) -> dict[str, Any]:
    inputs = json.loads(json.dumps(case.inputs))
    inputs.update(
        {
            "jiraProjectKey": environment.jira_project_key,
            "jiraIssueTypeId": environment.jira_issue_type_id,
            "jiraReporterAccountId": environment.jira_reporter_account_id,
            "slackChannelId": environment.slack_channel_id,
            "driveDestinationFolderId": (
                environment.drive_destination_folder_id
            ),
        }
    )
    attachments = inputs["attachments"]
    if len(attachments) > len(environment.drive_source_file_ids):
        raise CheckFailure(
            f"{case.name}: {len(attachments)} attachment inputs exceed the "
            f"{len(environment.drive_source_file_ids)} live Drive fixtures"
        )
    for index, attachment in enumerate(attachments):
        attachment["driveFileId"] = environment.drive_source_file_ids[index]
    if duplicate_key is not None:
        inputs["duplicateIssueKey"] = duplicate_key
    if inputs["duplicateIssueKey"] == SEEDED_DUPLICATE_KEY:
        raise CheckFailure(
            f"{case.name}: duplicateIssueKey is still the seed sentinel, so "
            "the seeded Jira key was never substituted"
        )
    return inputs


def recursive_strings(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            values.extend(recursive_strings(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(recursive_strings(item))
    return values


def recursive_values(value: Any, wanted_key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).casefold() == wanted_key.casefold():
                values.append(item)
            values.extend(recursive_values(item, wanted_key))
    elif isinstance(value, list):
        for item in value:
            values.extend(recursive_values(item, wanted_key))
    return values


def delete_target_is_absent(
    completed: subprocess.CompletedProcess[str],
    resource_kind: str,
    target_id: str,
) -> bool:
    detail = f"{completed.stdout}\n{completed.stderr}".casefold()
    absence_markers = ("404", "not found", "does not exist")
    if not any(marker in detail for marker in absence_markers):
        return False
    resource_markers = {
        "solution": ("solution not found", "solution does not exist"),
        "slack message": (
            "message_not_found",
            "message not found",
            "message does not exist",
        ),
        "drive file": ("file not found", "file does not exist"),
        "jira issue": ("issue not found", "issue does not exist"),
    }
    if any(
        marker in detail
        for marker in resource_markers.get(resource_kind, ())
    ):
        return True

    labels = {
        "solution": "solution",
        "slack message": "message",
        "drive file": "file",
        "jira issue": "issue",
    }
    label = labels.get(resource_kind)
    if label is None:
        return False
    # An echoed target ID elsewhere in a generic 404 (for example an OAuth
    # connection failure followed by a request path) is not deletion proof.
    # Trust only a resource phrase that names the exact target before saying
    # that target is absent.
    return (
        re.search(
            rf"\b{re.escape(label)}\b[^\r\n]{{0,120}}"
            rf"{re.escape(target_id.casefold())}[^\r\n]{{0,120}}"
            r"(?:not found|does not exist|404)",
            detail,
        )
        is not None
    )


class ConnectorSideEffectLease:
    def __init__(self, environment: LiveEnvironment):
        self.environment = environment
        self.jira_issue_ids: set[str] = JournaledSet("jira_issue")
        self.drive_file_ids: set[str] = JournaledSet("drive_file")
        self.slack_messages: set[tuple[str, str]] = JournaledSet(
            "slack_message"
        )
        self.pending_jira_seeds: dict[str, str] = {}

    def begin_jira_seed(self, case_name: str, summary: str) -> None:
        self.pending_jira_seeds[summary] = case_name

    def resolve_jira_seed(self, summary: str) -> None:
        self.pending_jira_seeds.pop(summary, None)

    def cleanup(self) -> list[str]:
        failures: list[str] = []
        for _attempt in range(2):
            failures = self._cleanup_once()
            if not failures:
                break
        return failures

    def _cleanup_once(self) -> list[str]:
        failures: list[str] = []
        for summary, case_name in list(self.pending_jira_seeds.items()):
            try:
                recover_seed_jira_issues(
                    case_name,
                    summary,
                    self.environment,
                    self,
                    require_issue_key=False,
                )
            except BaseException as exc:
                failures.append(str(exc))

        for channel_id, timestamp in sorted(self.slack_messages):
            completed: subprocess.CompletedProcess[str] | None = None
            try:
                completed = run_cli(
                    [
                        "uip",
                        "is",
                        "resources",
                        "run",
                        "delete",
                        "uipath-salesforce-slack",
                        "ChatDeleteTimestamp_POST",
                        "--connection-id",
                        self.environment.slack_connection_id,
                        "--query",
                        json.dumps(
                            {
                                "conversationId": channel_id,
                                "timestampId": timestamp,
                            },
                            separators=(",", ":"),
                        ),
                        "--yes",
                    ],
                    timeout=120,
                )
                payload_data(completed, f"delete Slack message {timestamp}")
            except Exception as exc:
                if completed is not None and delete_target_is_absent(
                    completed,
                    "slack message",
                    timestamp,
                ):
                    self.slack_messages.discard((channel_id, timestamp))
                else:
                    failures.append(str(exc))
            else:
                self.slack_messages.discard((channel_id, timestamp))

        for file_id in sorted(self.drive_file_ids):
            completed = None
            try:
                completed = run_cli(
                    [
                        "uip",
                        "is",
                        "resources",
                        "run",
                        "delete",
                        "uipath-google-drive",
                        "DeleteFileorFolder",
                        "--connection-id",
                        self.environment.drive_connection_id,
                        "--query",
                        json.dumps(
                            {"fileId": file_id},
                            separators=(",", ":"),
                        ),
                        "--yes",
                    ],
                    timeout=120,
                )
                payload_data(completed, f"delete Drive file {file_id}")
            except Exception as exc:
                if completed is not None and delete_target_is_absent(
                    completed,
                    "drive file",
                    file_id,
                ):
                    self.drive_file_ids.discard(file_id)
                else:
                    failures.append(str(exc))
            else:
                self.drive_file_ids.discard(file_id)

        for issue_id in sorted(self.jira_issue_ids):
            completed = None
            try:
                completed = run_cli(
                    [
                        "uip",
                        "is",
                        "resources",
                        "run",
                        "delete",
                        "uipath-atlassian-jira",
                        "issue",
                        "--connection-id",
                        self.environment.jira_connection_id,
                        "--query",
                        json.dumps(
                            {"issueId": issue_id},
                            separators=(",", ":"),
                        ),
                        "--yes",
                    ],
                    timeout=120,
                )
                payload_data(completed, f"delete Jira issue {issue_id}")
            except Exception as exc:
                if completed is not None and delete_target_is_absent(
                    completed,
                    "jira issue",
                    issue_id,
                ):
                    self.jira_issue_ids.discard(issue_id)
                else:
                    failures.append(str(exc))
            else:
                self.jira_issue_ids.discard(issue_id)
        return failures


def create_seed_jira_issue(
    case: Scenario,
    environment: LiveEnvironment,
    lease: ConnectorSideEffectLease,
) -> str:
    summary = f"Live update seed {RUN_NONCE} for {case.name}"
    lease.begin_jira_seed(case.name, summary)
    body = {
        "fields": {
            "project": {"key": environment.jira_project_key},
            "issuetype": {"id": environment.jira_issue_type_id},
            "reporter": {"id": environment.jira_reporter_account_id},
            "summary": summary,
            "description": "Awaiting exact BPMN correlation write-back",
        }
    }
    try:
        created = run_cli(
            [
                "uip",
                "is",
                "resources",
                "run",
                "create",
                "uipath-atlassian-jira",
                "curated_create_issue",
                "--connection-id",
                environment.jira_connection_id,
                "--body",
                json.dumps(body, separators=(",", ":")),
            ],
            timeout=180,
        )
    except KeyboardInterrupt:
        try:
            recover_seed_jira_issues(
                case.name,
                summary,
                environment,
                lease,
                attempts=2,
            )
        except Exception:
            pass
        raise
    except Exception as exc:
        recovered_keys = recover_seed_jira_issues(
            case.name, summary, environment, lease
        )
        raise CheckFailure(
            f"{case.name}: Jira seed call failed; cleanup recovery found "
            f"{len(recovered_keys)} exact issue(s)"
        ) from exc

    try:
        payload = parse_json_output(
            created.stdout or created.stderr,
            f"{case.name} seed Jira issue",
        )
    except CheckFailure as exc:
        recovered_keys = recover_seed_jira_issues(
            case.name, summary, environment, lease
        )
        raise CheckFailure(
            f"{exc}; cleanup recovery found "
            f"{len(recovered_keys)} exact issue(s)"
        ) from exc

    data = get_ci(payload, "Data")
    issue_id = get_ci(data, "id")
    issue_key = get_ci(data, "key")
    if isinstance(issue_id, str):
        lease.jira_issue_ids.add(issue_id)
        lease.resolve_jira_seed(summary)
    elif isinstance(issue_key, str):
        lease.jira_issue_ids.add(issue_key)
        lease.resolve_jira_seed(summary)
    try:
        payload_data(created, f"{case.name} seed Jira issue")
    except CheckFailure as exc:
        recovered_keys = recover_seed_jira_issues(
            case.name, summary, environment, lease
        )
        raise CheckFailure(
            f"{exc}; cleanup recovery found "
            f"{len(recovered_keys)} exact issue(s)"
        ) from exc

    if isinstance(issue_id, str) and isinstance(issue_key, str):
        return issue_key
    recovered_keys = recover_seed_jira_issues(
        case.name, summary, environment, lease
    )
    if len(recovered_keys) == 1:
        return recovered_keys[0]
    raise CheckFailure(
        f"{case.name}: Jira seed returned no exact top-level id/key and "
        f"recovery found {len(recovered_keys)} issues: {data!r}"
    )


def recover_seed_jira_issues(
    case_name: str,
    summary: str,
    environment: LiveEnvironment,
    lease: ConnectorSideEffectLease,
    *,
    attempts: int = 5,
    require_issue_key: bool = True,
) -> tuple[str, ...]:
    exact: dict[str, str] = {}
    found_cleanup_handle = False
    jql = (
        f'project = "{environment.jira_project_key}" '
        f'AND summary ~ "\\"{summary}\\""'
    )
    last_error: BaseException | None = None
    for attempt in range(attempts):
        try:
            searched = run_cli(
                [
                    "uip",
                    "is",
                    "resources",
                    "run",
                    "list",
                    "uipath-atlassian-jira",
                    "issue_search_get",
                    "--connection-id",
                    environment.jira_connection_id,
                    "--query",
                    json.dumps(
                        {"jql": jql, "pageSize": 20},
                        separators=(",", ":"),
                    ),
                ],
                timeout=30,
            )
            _payload, data = payload_data(
                searched,
                f"{case_name} recover seed Jira issue",
            )
            items = get_ci(data, "items")
            if not isinstance(items, list):
                raise CheckFailure(
                    f"{case_name}: Jira seed recovery returned no items"
                )
            for item in items:
                fields = get_ci(item, "fields")
                if get_ci(fields, "summary") != summary:
                    continue
                issue_id = get_ci(item, "id")
                issue_key = get_ci(item, "key")
                if isinstance(issue_id, str):
                    lease.jira_issue_ids.add(issue_id)
                    found_cleanup_handle = True
                    if isinstance(issue_key, str):
                        exact[issue_id] = issue_key
                elif isinstance(issue_key, str):
                    lease.jira_issue_ids.add(issue_key)
                    found_cleanup_handle = True
                    exact[issue_key] = issue_key
            last_error = None
        except Exception as exc:
            last_error = exc
        if exact or (found_cleanup_handle and not require_issue_key):
            break
        if attempt + 1 < attempts:
            time.sleep(2)
    if not found_cleanup_handle:
        detail = (
            f": {last_error}"
            if last_error is not None
            else " before the visibility deadline"
        )
        raise CheckFailure(
            f"{case_name}: Jira seed cleanup recovery found no exact issue"
            f"{detail}"
        ) from last_error
    lease.resolve_jira_seed(summary)
    if require_issue_key and not exact:
        raise CheckFailure(
            f"{case_name}: Jira seed recovery found a cleanup identifier "
            "but no issue key for the update scenario"
        )
    return tuple(sorted(exact.values()))


def incident_records(incidents_data: Any) -> list[Any] | None:
    """Normalise `debug-instance incidents` into a list of records.

    The CLI has returned both a bare list and a paged `{"Items": [...]}`
    envelope for this endpoint; either is accepted so a shape change does not
    read as a scenario failure. Returns None when the payload is neither.
    """

    if isinstance(incidents_data, list):
        return incidents_data
    for key in ("Items", "Incidents", "Results", "Value"):
        items = get_ci(incidents_data, key)
        if isinstance(items, list):
            return items
    if isinstance(incidents_data, dict) and not incidents_data:
        return []
    return None


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
    if not isinstance(globals_map, dict):
        raise CheckFailure(
            f"runtime root scope Globals is not a map: {globals_map!r}"
        )
    return {
        name: resolve_runtime_key(globals_map, identifier, name)
        for name, identifier in contract.public_output_ids.items()
    }


def element_output_records(
    variables_data: Any,
    element_ids: str | tuple[str, ...],
) -> list[Any]:
    """Collect Outputs for one element id, or across several equivalent ids."""

    if isinstance(element_ids, str):
        element_ids = (element_ids,)
    wanted = set(element_ids)
    return _element_output_records(variables_data, wanted)


def _element_output_records(
    variables_data: Any,
    wanted: set[str],
) -> list[Any]:
    records: list[Any] = []
    scopes = get_ci(variables_data, "Variables", [])
    if not isinstance(scopes, list):
        return records
    for scope in scopes:
        for element in get_ci(scope, "Elements", []):
            if get_ci(element, "ElementId") in wanted:
                records.append(get_ci(element, "Outputs", {}))
    return records


def runtime_variable_values(
    variables_data: Any,
    variable_id: str,
) -> list[Any]:
    values: list[Any] = []
    wanted = normalized_identifier(variable_id)
    scopes = get_ci(variables_data, "Variables", [])
    if not isinstance(scopes, list):
        return values
    for scope in scopes:
        globals_map = get_ci(scope, "Globals", {})
        if not isinstance(globals_map, dict):
            continue
        for key, value in globals_map.items():
            if normalized_identifier(key) == wanted:
                values.append(value)
    return values


def connector_response_values(outputs: list[Any], name: str) -> list[Any]:
    """Read only top-level response fields, never same-named nested metadata."""
    values: list[Any] = []
    for output in outputs:
        response = get_ci(output, "response")
        if isinstance(response, dict):
            value = get_ci(response, name)
            if value is not None:
                values.append(value)
    return values


def capture_connector_outputs_for_cleanup(
    variables_data: Any,
    contract: RuntimeContract,
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
) -> None:
    jira_outputs = element_output_records(
        variables_data, contract.jira_create_id
    )
    jira_ids = [
        value
        for value in connector_response_values(jira_outputs, "id")
        if isinstance(value, str)
    ]
    jira_keys = [
        value
        for value in connector_response_values(jira_outputs, "key")
        if isinstance(value, str)
    ]
    side_effects.jira_issue_ids.update(jira_ids or jira_keys)

    drive_outputs = element_output_records(
        variables_data, contract.drive_copy_id
    )
    protected_drive_ids = {
        *environment.drive_source_file_ids,
        environment.drive_destination_folder_id,
    }
    side_effects.drive_file_ids.update(
        value
        for value in connector_response_values(drive_outputs, "id")
        if isinstance(value, str) and value not in protected_drive_ids
    )

    slack_outputs = element_output_records(
        variables_data, contract.slack_send_id
    )
    for output in slack_outputs:
        response = get_ci(output, "response")
        timestamp = get_ci(response, "ts")
        channel_id = get_ci(response, "channel")
        if isinstance(timestamp, str) and isinstance(channel_id, str):
            side_effects.slack_messages.add((channel_id, timestamp))



def variables_all_with_cleanup_recovery(
    instance_id: str,
    case_name: str,
    contract: RuntimeContract,
    environment: LiveEnvironment,
    solution_lease: AlphaSolutionLease,
    side_effects: ConnectorSideEffectLease,
) -> tuple[Any, Any]:
    def read_and_capture(label: str) -> tuple[Any, Any]:
        completed = run_cli(
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
        payload = parse_json_output(
            completed.stdout or completed.stderr,
            label,
        )
        data = get_ci(payload, "Data")
        if data is not None:
            capture_connector_outputs_for_cleanup(
                data,
                contract,
                environment,
                side_effects,
            )
        return payload_data(completed, label)

    try:
        return read_and_capture(f"{case_name} variables-all")
    except BaseException:
        # The debug call may have created connector side effects even when the
        # first variables query fails. Retry once without masking the original
        # failure so the outer finally can still delete every discovered id.
        try:
            read_and_capture(f"{case_name} variables-all cleanup recovery")
        except BaseException:
            pass
        raise


def read_jira_issue_fields(
    issue_key: str,
    environment: LiveEnvironment,
) -> dict[str, Any]:
    fetched = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "get",
            "uipath-atlassian-jira",
            "issue",
            "--connection-id",
            environment.jira_connection_id,
            "--query",
            json.dumps({"issueId": issue_key}, separators=(",", ":")),
        ],
        timeout=120,
    )
    _payload, data = payload_data(fetched, f"read Jira issue {issue_key}")
    if not isinstance(data, dict):
        raise CheckFailure(f"Jira issue {issue_key} returned no object")
    returned_key = get_ci(data, "key")
    if returned_key != issue_key:
        raise CheckFailure(
            f"Jira read returned key {returned_key!r}, expected {issue_key!r}"
        )
    fields = get_ci(data, "fields")
    if not isinstance(fields, dict):
        raise CheckFailure(f"Jira issue {issue_key} returned no fields object")
    return fields


def assert_jira_issue_contract(
    issue_key: str,
    correlation: str,
    environment: LiveEnvironment,
    *,
    require_summary: bool,
) -> None:
    fields = read_jira_issue_fields(issue_key, environment)
    required_correlation_fields = ["description"]
    if require_summary:
        required_correlation_fields.append("summary")
    for field_name in required_correlation_fields:
        value = get_ci(fields, field_name)
        if not any(
            correlation in item for item in recursive_strings(value)
        ):
            raise CheckFailure(
                f"Jira issue {issue_key} field {field_name!r} does not "
                f"contain correlation {correlation!r}"
            )
    if require_summary:
        summary_text = " ".join(
            recursive_strings(get_ci(fields, "summary"))
        ).casefold()
        missing_terms = {
            term
            for term in ("customer", "escalation")
            if term not in summary_text
        }
        if missing_terms:
            raise CheckFailure(
                f"Jira issue {issue_key} summary is missing required terms "
                f"{sorted(missing_terms)}"
            )

    project = get_ci(fields, "project", {})
    issue_type = get_ci(fields, "issuetype", {})
    reporter = get_ci(fields, "reporter", {})
    expected_fields = {
        "project.key": (
            get_ci(project, "key"),
            environment.jira_project_key,
        ),
        "issuetype.id": (
            get_ci(issue_type, "id"),
            environment.jira_issue_type_id,
        ),
        "reporter.accountId": (
            get_ci(reporter, "accountId"),
            environment.jira_reporter_account_id,
        ),
    }
    mismatches = {
        name: {"actual": actual, "expected": expected}
        for name, (actual, expected) in expected_fields.items()
        if actual != expected
    }
    if mismatches:
        raise CheckFailure(
            f"Jira issue {issue_key} has incorrect remote fields: "
            f"{mismatches}"
        )


def read_drive_file(
    file_id: str,
    environment: LiveEnvironment,
) -> dict[str, Any]:
    fetched = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "get",
            "uipath-google-drive",
            "File",
            "--connection-id",
            environment.drive_connection_id,
            "--query",
            json.dumps({"filesId": file_id}, separators=(",", ":")),
        ],
        timeout=120,
    )
    _payload, data = payload_data(fetched, f"read Drive file {file_id}")
    if not isinstance(data, dict) or get_ci(data, "id") != file_id:
        raise CheckFailure(
            f"Drive read did not return exact file {file_id}: {data!r}"
        )
    return data


def require_distinct_drive_source_fixtures(
    environment: LiveEnvironment,
) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for file_id in environment.drive_source_file_ids:
        source = read_drive_file(file_id, environment)
        checksum = get_ci(source, "md5Checksum")
        if not isinstance(checksum, str) or not checksum:
            raise CheckFailure(
                f"Drive source fixture {file_id} returned no MD5 checksum"
            )
        checksums[file_id] = checksum
    if len(set(checksums.values())) != len(checksums):
        raise CheckFailure(
            "live Drive source fixtures must have distinct MD5 checksums"
        )
    return checksums


def attachment_marker_order(
    case: Scenario,
    variables_data: Any,
    contract: RuntimeContract,
) -> tuple[str, ...]:
    marker_values = runtime_variable_values(
        variables_data, contract.marker_collection_id
    )
    expected = list(case.attachment_iterations)
    # A subprocess-scoped collection can surface in both the subprocess scope
    # and the root scope, so accept repeats as long as every copy agrees.
    distinct = [
        value
        for index, value in enumerate(marker_values)
        if value not in marker_values[:index]
    ]
    if distinct != [expected]:
        raise CheckFailure(
            f"{case.name}: live attachment marker collection expected "
            f"{expected!r}, got {marker_values!r}"
        )
    return tuple(expected)


def assert_ordered_drive_copies(
    case: Scenario,
    marker_order: tuple[str, ...],
    outputs: list[Any],
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
) -> None:
    if marker_order != case.attachment_iterations:
        raise CheckFailure(
            f"{case.name}: live attachment marker order expected "
            f"{list(case.attachment_iterations)!r}, got {list(marker_order)!r}"
        )
    if len(outputs) != len(case.attachment_iterations):
        raise CheckFailure(
            f"{case.name}: Drive copy returned {len(outputs)} records for "
            f"{len(case.attachment_iterations)} attachments: {outputs!r}"
        )
    if len(marker_order) > len(environment.drive_source_file_ids):
        raise CheckFailure(
            f"{case.name}: marker count exceeds live Drive source fixtures"
        )
    unmatched_sources: list[tuple[str, str, str]] = []
    for index, attachment_name in enumerate(marker_order):
        source_id = environment.drive_source_file_ids[index]
        source_file = read_drive_file(source_id, environment)
        source_checksum = get_ci(source_file, "md5Checksum")
        if not isinstance(source_checksum, str) or not source_checksum:
            raise CheckFailure(
                f"Drive source fixture {source_id} returned no MD5 checksum"
            )
        unmatched_sources.append(
            (attachment_name, source_id, source_checksum)
        )
    correlation = case.inputs["correlationId"]
    for output in outputs:
        response = get_ci(output, "response")
        file_id = get_ci(response, "id")
        if not isinstance(file_id, str):
            raise CheckFailure(
                f"{case.name}: Drive iteration returned no file id: "
                f"{output!r}"
            )
        protected_drive_ids = {
            *environment.drive_source_file_ids,
            environment.drive_destination_folder_id,
        }
        if file_id in protected_drive_ids:
            raise CheckFailure(
                f"{case.name}: Drive copy returned protected fixture or "
                f"destination id {file_id!r}"
            )
        side_effects.drive_file_ids.add(file_id)
        response_strings = recursive_strings(response)
        remote = read_drive_file(file_id, environment)
        remote_name = get_ci(remote, "name")
        candidates = [
            source
            for source in unmatched_sources
            if isinstance(remote_name, str)
            and correlation in remote_name
            and source[0] in remote_name
            and any(
                correlation in value and source[0] in value
                for value in response_strings
            )
        ]
        candidate_names = {candidate[0] for candidate in candidates}
        if not candidates or len(candidate_names) != 1:
            raise CheckFailure(
                f"{case.name}: Drive response {file_id} does not match "
                f"exactly one pending marker from "
                f"{[item[0] for item in unmatched_sources]!r}: "
                f"{output!r}; remote={remote!r}"
            )
        attachment_name, source_id, source_checksum = candidates[0]
        unmatched_sources.remove(candidates[0])
        parents = get_ci(remote, "parents", [])
        if (
            not isinstance(remote_name, str)
            or correlation not in remote_name
            or attachment_name not in remote_name
            or not isinstance(parents, list)
            or environment.drive_destination_folder_id not in parents
            or get_ci(remote, "md5Checksum") != source_checksum
        ):
            raise CheckFailure(
                f"{case.name}: remote Drive copy {file_id} does not prove "
                f"ordered name, destination, and source content for "
                f"{attachment_name!r} from {source_id}: {remote!r}"
            )
    if unmatched_sources:
        raise CheckFailure(
            f"{case.name}: Drive responses did not cover marker items "
            f"{[item[0] for item in unmatched_sources]!r}"
        )


def assert_slack_send(
    case: Scenario,
    outputs: list[Any],
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
) -> None:
    response_pairs: list[tuple[str, str]] = []
    for output in outputs:
        response = get_ci(output, "response")
        timestamp = get_ci(response, "ts")
        channel_id = get_ci(response, "channel")
        if isinstance(timestamp, str) and isinstance(channel_id, str):
            response_pairs.append((channel_id, timestamp))
    if len(response_pairs) != 1:
        raise CheckFailure(
            f"{case.name}: Slack send returned no unique channel/timestamp: "
            f"{outputs!r}"
        )
    actual_channel, timestamp = response_pairs[0]
    side_effects.slack_messages.add((actual_channel, timestamp))
    messages = [
        value
        for value in connector_response_values(outputs, "message")
        if isinstance(value, dict)
    ]
    if actual_channel != environment.slack_channel_id or len(messages) != 1:
        raise CheckFailure(
            f"{case.name}: Slack response does not prove the exact "
            f"destination and message: {outputs!r}"
        )
    message_text = get_ci(messages[0], "text")
    message_timestamp = get_ci(messages[0], "ts")
    required_tokens = (
        case.inputs["correlationId"],
        case.outputs["route"],
        case.outputs["severity"],
    )
    if (
        not isinstance(message_text, str)
        or any(token not in message_text for token in required_tokens)
        or message_timestamp != timestamp
    ):
        raise CheckFailure(
            f"{case.name}: Slack API response does not contain the exact "
            f"correlation, route, severity, and timestamp: {messages[0]!r}"
        )


def assert_scenario(
    case: Scenario,
    contract: RuntimeContract,
    debug_data: Any,
    variables_data: Any,
    incidents_data: Any,
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
    *,
    update_issue_key: str | None,
) -> None:
    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in {"Completed", "Successful"}:
        raise CheckFailure(
            f"{case.name}: Alpha final status was {final_status!r}"
        )
    incidents = incident_records(incidents_data)
    if incidents is None:
        raise CheckFailure(
            f"{case.name}: incidents response is neither a list nor an "
            f"item envelope: {incidents_data!r}"
        )
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

    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = [
        get_ci(item, "ElementId")
        for item in executions
        if isinstance(item, dict)
    ]
    executed_set = set(executed_ids)
    # Reaching a terminal Completed status with the expected public outputs
    # already proves the process ran end to end, so no root-node execution
    # trace is required here.
    error_nodes = {
        identifier
        for identifier in (contract.error_end_id, contract.error_boundary_id)
        if identifier
    }
    if error_nodes and case.uses_error_boundary:
        if not error_nodes <= executed_set:
            raise CheckFailure(
                f"{case.name}: typed JiraUnavailable path did not execute "
                f"{sorted(error_nodes - executed_set)}"
            )
    elif error_nodes and error_nodes & executed_set:
        raise CheckFailure(
            f"{case.name}: unexpectedly executed JiraUnavailable error path"
        )

    # Counts sum across every element id bound to the same connector
    # operation: the process may place one operation on several branches, and
    # only one of them should execute per run.
    expected_counts = (
        (
            "Jira create",
            contract.jira_create_id,
            1 if case.outputs["jiraAction"] == "CreateIssue" else 0,
        ),
        (
            "Jira update",
            contract.jira_update_id,
            1 if case.outputs["jiraAction"] == "UpdateExisting" else 0,
        ),
        (
            "Slack send",
            contract.slack_send_id,
            1 if case.outputs["slackAction"] == "PostAlert" else 0,
        ),
    )
    for label, element_ids, expected_count in expected_counts:
        actual_count = sum(
            executed_ids.count(element_id) for element_id in element_ids
        )
        if actual_count != expected_count:
            raise CheckFailure(
                f"{case.name}: {label} {list(element_ids)} expected "
                f"{expected_count} executions, got {actual_count}"
            )
    # PIMS summarizes a marker body's static element in the root trace; prove
    # the iteration cardinality below from per-run outputs and remote files.
    drive_trace_count = sum(
        executed_ids.count(element_id) for element_id in contract.drive_copy_id
    )
    if case.outputs["attachmentAction"] == "SaveToDrive":
        if drive_trace_count < 1:
            raise CheckFailure(
                f"{case.name}: live trace never reached Drive copy"
            )
    elif drive_trace_count:
        raise CheckFailure(
            f"{case.name}: no-copy path unexpectedly reached Drive copy"
        )

    correlation = case.inputs["correlationId"]
    if case.outputs["jiraAction"] == "CreateIssue":
        outputs = element_output_records(
            variables_data, contract.jira_create_id
        )
        keys = [
            value
            for value in connector_response_values(outputs, "key")
            if isinstance(value, str)
        ]
        ids = [
            value
            for value in connector_response_values(outputs, "id")
            if isinstance(value, str)
        ]
        if not keys:
            raise CheckFailure(
                f"{case.name}: Jira create returned no issue key: {outputs!r}"
            )
        side_effects.jira_issue_ids.add(ids[0] if ids else keys[0])
        assert_jira_issue_contract(
            keys[0],
            correlation,
            environment,
            require_summary=True,
        )
    elif case.outputs["jiraAction"] == "UpdateExisting":
        if not update_issue_key:
            raise CheckFailure(f"{case.name}: update scenario has no seed issue")
        assert_jira_issue_contract(
            update_issue_key,
            correlation,
            environment,
            require_summary=False,
        )

    if case.outputs["attachmentAction"] == "SaveToDrive":
        marker_order = attachment_marker_order(
            case, variables_data, contract
        )
        outputs = element_output_records(
            variables_data, contract.drive_copy_id
        )
        assert_ordered_drive_copies(
            case,
            marker_order,
            outputs,
            environment,
            side_effects,
        )

    if case.outputs["slackAction"] == "PostAlert":
        outputs = element_output_records(
            variables_data, contract.slack_send_id
        )
        assert_slack_send(case, outputs, environment, side_effects)


def tail_log(path: Path, limit: int = 5000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[-limit:]


def diagnostic_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


def logged_instance_id(*diagnostics: Any) -> str | None:
    texts = [diagnostic_text(value) for value in diagnostics]
    structured_ids: list[str] = []
    fallback_texts: list[str] = []
    for text in texts:
        if not text.strip():
            continue
        try:
            payload = parse_json_output(text, "debug diagnostic")
        except CheckFailure:
            fallback_texts.append(text)
            continue
        data = get_ci(payload, "Data")
        instance_id = get_ci(data, "InstanceId")
        if isinstance(instance_id, str) and instance_id:
            structured_ids.append(instance_id)
        for field in ("Message", "Instructions"):
            trusted_diagnostic = get_ci(payload, field)
            if isinstance(trusted_diagnostic, str):
                fallback_texts.append(trusted_diagnostic)
    unique_structured = list(dict.fromkeys(structured_ids))
    if unique_structured:
        return (
            unique_structured[0]
            if len(unique_structured) == 1
            else None
        )

    matches: list[str] = []
    pattern = re.compile(
        r"""(?ix)
        (?<![A-Za-z0-9_])
        instance(?:[\s_-]*id)
        ["']?\s*[:=]\s*["']?
        ([A-Za-z0-9][A-Za-z0-9._:-]{2,})
        """
    )
    for text in fallback_texts:
        matches.extend(match.group(1) for match in pattern.finditer(text))
    unique = list(dict.fromkeys(matches))
    return unique[-1] if len(unique) == 1 else None


def read_debug_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def debug_instance_terminal_or_absent_state(
    completed: subprocess.CompletedProcess[str],
    instance_id: str,
) -> str | None:
    detail = f"{completed.stdout}\n{completed.stderr}".casefold()
    try:
        payload = parse_json_output(
            completed.stdout or completed.stderr,
            "cancel debug instance response",
        )
    except CheckFailure:
        payload = None
    data = get_ci(payload, "Data")
    returned_id = get_ci(data, "InstanceId")
    returned_status = str(get_ci(data, "Status", "")).casefold()
    if (
        returned_id == instance_id
        and returned_status
        in {"completed", "faulted", "cancelled", "canceled", "failed"}
    ):
        return "terminal"
    match = re.search(
        r"\b(?:debug\s+)?instance\b[^\r\n]{0,100}"
        rf"{re.escape(instance_id.casefold())}[^\r\n]{{0,100}}"
        r"(?P<state>not found|does not exist|already completed|"
        r"has completed|already cance(?:led|lled)|not active)",
        detail,
    )
    if match is None:
        return None
    return (
        "absent"
        if match.group("state") in {"not found", "does not exist"}
        else "terminal"
    )


def debug_instance_is_terminal_or_absent(
    completed: subprocess.CompletedProcess[str],
    instance_id: str,
) -> bool:
    return (
        debug_instance_terminal_or_absent_state(
            completed,
            instance_id,
        )
        is not None
    )


def cancel_debug_instance_for_recovery(
    instance_id: str,
    case_name: str,
) -> tuple[list[str], bool]:
    last_failure = ""
    for _attempt in range(2):
        completed: subprocess.CompletedProcess[str] | None = None
        try:
            completed = run_cli(
                [
                    "uip",
                    "maestro",
                    "bpmn",
                    "debug-instance",
                    "cancel",
                    instance_id,
                ],
                timeout=180,
            )
            payload_data(
                completed,
                f"{case_name} cancel debug instance {instance_id}",
            )
        except Exception as exc:
            if completed is not None:
                state = debug_instance_terminal_or_absent_state(
                    completed,
                    instance_id,
                )
                if state is not None:
                    return [], state == "absent"
            last_failure = str(exc)
        else:
            return [], False
    return (
        [
            last_failure
            or f"{case_name}: could not cancel debug instance {instance_id}"
        ],
        False,
    )


def best_effort_capture_instance_outputs(
    instance_id: str,
    case_name: str,
    contract: RuntimeContract,
    environment: LiveEnvironment,
    solution_lease: AlphaSolutionLease,
    side_effects: ConnectorSideEffectLease,
) -> list[str]:
    failures, instance_absent = cancel_debug_instance_for_recovery(
        instance_id,
        case_name,
    )
    if instance_absent:
        return failures
    try:
        variables_all_with_cleanup_recovery(
            instance_id,
            f"{case_name} debug recovery",
            contract,
            environment,
            solution_lease,
            side_effects,
        )
    except BaseException as exc:
        failures.append(str(exc))
    # Successful deletes are removed from the lease; failed ones stay pending
    # for the outer-finally retry.
    try:
        failures.extend(side_effects.cleanup())
    except BaseException as exc:
        failures.append(str(exc))
    return failures



class LiveRunLease:
    """Tracks debug instances and nonce-bearing effects until cleanup."""

    def __init__(
        self,
        *,
        contract: RuntimeContract,
        environment: LiveEnvironment,
        solution_lease: AlphaSolutionLease,
        side_effects: ConnectorSideEffectLease,
    ):
        self.contract = contract
        self.environment = environment
        self.solution_lease = solution_lease
        self.side_effects = side_effects
        self.pending_correlations: dict[str, str] = {}
        self.active_instances: dict[str, tuple[str, str]] = {}

    def begin(self, case_name: str, correlation: str) -> None:
        self.pending_correlations[correlation] = case_name

    def register(
        self,
        instance_id: str,
        case_name: str,
        correlation: str,
    ) -> None:
        self.active_instances[instance_id] = (case_name, correlation)

    def complete(self, instance_id: str, correlation: str) -> None:
        self.active_instances.pop(instance_id, None)
        self.pending_correlations.pop(correlation, None)

    def cleanup(self) -> list[str]:
        failures: list[str] = []

        for instance_id, (case_name, _correlation) in list(
            self.active_instances.items()
        ):
            instance_failures = best_effort_capture_instance_outputs(
                instance_id,
                case_name,
                self.contract,
                self.environment,
                self.solution_lease,
                self.side_effects,
            )
            failures.extend(instance_failures)
            if not instance_failures:
                self.active_instances.pop(instance_id, None)

        for correlation in list(self.pending_correlations):
            if not any(
                active_correlation == correlation
                for _case_name, active_correlation
                in self.active_instances.values()
            ):
                # No logged instance id means the run never reached the point
                # where its StartEvent could be continued, so there is no
                # instance to inspect or clean up.
                self.pending_correlations.pop(correlation, None)
        return failures


def run_debug_with_cleanup_recovery(
    arguments: list[str],
    *,
    log_file: Path,
    case_name: str,
    contract: RuntimeContract,
    environment: LiveEnvironment,
    solution_lease: AlphaSolutionLease,
    side_effects: ConnectorSideEffectLease,
    live_run_lease: LiveRunLease,
    correlation: str,
) -> tuple[subprocess.CompletedProcess[str], Any, Any, str]:
    solution_lease.capture_manifest()
    try:
        completed = run_cli(
            arguments,
            timeout=DEBUG_TIMEOUT_SECONDS,
            log_file=log_file,
        )
    except subprocess.TimeoutExpired as exc:
        diagnostic_id = logged_instance_id(
            exc.stdout,
            exc.stderr,
            read_debug_log(log_file),
        )
        instance_id = diagnostic_id
        if instance_id is not None:
            live_run_lease.register(
                instance_id,
                case_name,
                correlation,
            )
            recovery_failures = best_effort_capture_instance_outputs(
                instance_id,
                case_name,
                contract,
                environment,
                solution_lease,
                side_effects,
            )
            if recovery_failures:
                raise CheckFailure(
                    f"{case_name}: debug timed out and cleanup recovery "
                    f"failed: {'; '.join(recovery_failures)}"
                ) from exc
        raise

    raw_output = completed.stdout or completed.stderr
    try:
        payload = parse_json_output(raw_output, f"{case_name} debug")
    except CheckFailure as parse_error:
        diagnostic_id = logged_instance_id(
            completed.stdout,
            completed.stderr,
            read_debug_log(log_file),
        )
        instance_id = diagnostic_id
        if instance_id is not None:
            live_run_lease.register(
                instance_id,
                case_name,
                correlation,
            )
            recovery_failures = best_effort_capture_instance_outputs(
                instance_id,
                case_name,
                contract,
                environment,
                solution_lease,
                side_effects,
            )
            if recovery_failures:
                raise CheckFailure(
                    f"{parse_error}; cleanup recovery failed: "
                    f"{'; '.join(recovery_failures)}"
                ) from parse_error
        raise

    debug_data = get_ci(payload, "Data", {})
    instance_id = get_ci(debug_data, "InstanceId")
    if not isinstance(instance_id, str) or not instance_id:
        diagnostic_id = logged_instance_id(
            completed.stdout,
            completed.stderr,
            read_debug_log(log_file),
        )
        recovered_id = diagnostic_id
        if recovered_id is not None:
            live_run_lease.register(
                recovered_id,
                case_name,
                correlation,
            )
            recovery_failures = best_effort_capture_instance_outputs(
                recovered_id,
                case_name,
                contract,
                environment,
                solution_lease,
                side_effects,
            )
            if recovery_failures:
                raise CheckFailure(
                    f"{case_name}: debug returned no instance id and cleanup "
                    f"recovery failed: {'; '.join(recovery_failures)}"
                )
        raise CheckFailure(
            f"{case_name}: debug returned no instance id "
            f"(exit {completed.returncode}); log: {tail_log(log_file)}"
        )
    live_run_lease.register(instance_id, case_name, correlation)
    return completed, payload, debug_data, instance_id


def write_scenario_results(results: dict[str, dict[str, Any]]) -> None:
    """Persist per-scenario verdicts plus per-family rollups.

    The live matrix is graded twice over: once strictly (every scenario must
    pass) and once per outcome family, so a submission that gets classification
    right but attachments wrong is scored differently from one that never ran.
    Written even when the run fails, so partial credit survives.
    """

    families: dict[str, Any] = {}
    for family, names in SCENARIO_BUNDLES.items():
        verdicts = [results.get(name) for name in names]
        ran = [item for item in verdicts if item is not None]
        families[family] = {
            "total": len(names),
            "ran": len(ran),
            "passed": sum(1 for item in ran if item.get("passed")),
            "all_passed": len(ran) == len(names)
            and all(item.get("passed") for item in ran),
        }
    payload = {
        "scenarios_total": len(SCENARIOS),
        "scenarios_ran": len(results),
        "scenarios_passed": sum(
            1 for item in results.values() if item.get("passed")
        ),
        "families": families,
        "scenarios": results,
    }
    try:
        SCENARIO_RESULTS.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(f"wrote per-scenario verdicts to {SCENARIO_RESULTS}")
    except OSError as exc:
        # Never fail the run over the side-channel used for partial credit.
        print(f"WARNING could not write {SCENARIO_RESULTS}: {exc}")


def main() -> int:
    global ACTIVE_CLI_DEADLINE
    checker_started_monotonic = time.monotonic()
    execution_deadline = (
        checker_started_monotonic + LIVE_RUN_DEADLINE_SECONDS
    )
    cleanup_deadline = (
        checker_started_monotonic + LIVE_CLEANUP_DEADLINE_SECONDS
    )
    stage_started = time.monotonic()
    print(
        "BENCHMARK stage=structural-preflight "
        f"duration_seconds={time.monotonic() - stage_started:.3f}"
    )
    if not BPMN_FILE.is_file():
        raise CheckFailure(f"missing {BPMN_FILE}")
    contract = load_runtime_contract()
    original_hash = sha256(BPMN_FILE)
    checker_hash = sha256(Path(__file__).resolve())
    target = assert_live_target()
    print(
        "LIVE EVIDENCE: "
        f"target={target['BaseUrl']}/{target['Organization']}/"
        f"{target['Tenant']} checker_sha256={checker_hash} "
        f"bpmn_sha256={original_hash}"
    )

    stage_started = time.monotonic()
    validate = run_cli(
        ["uip", "maestro", "bpmn", "validate", str(BPMN_FILE)],
        timeout=180,
    )
    payload_data(validate, "offline BPMN validation")
    print(
        "BENCHMARK stage=offline-validation "
        f"duration_seconds={time.monotonic() - stage_started:.3f}"
    )
    stage_started = time.monotonic()
    environment = discover_live_environment()
    print(
        "BENCHMARK stage=connector-discovery "
        f"duration_seconds={time.monotonic() - stage_started:.3f}"
    )
    side_effects = ConnectorSideEffectLease(environment)

    with tempfile.TemporaryDirectory(
        prefix="customer-escalation-live-alpha-"
    ) as directory:
        root = Path(directory)
        solution_dir = root / "CustomerEscalationLiveAlphaEval"
        stage_started = time.monotonic()
        initialized = run_cli(
            ["uip", "solution", "init", str(solution_dir)],
            timeout=120,
        )
        payload_data(initialized, "initialize ephemeral solution")
        print(
            "BENCHMARK stage=solution-init "
            f"duration_seconds={time.monotonic() - stage_started:.3f}"
        )
        solution_files = list(solution_dir.glob("*.uipx"))
        if len(solution_files) != 1:
            raise CheckFailure("solution init did not create exactly one .uipx")
        solution_file = solution_files[0]
        lease = AlphaSolutionLease(solution_file)
        live_runs = LiveRunLease(
            contract=contract,
            environment=environment,
            solution_lease=lease,
            side_effects=side_effects,
        )
        cleanup_failures: list[str] = []
        scenario_results: dict[str, dict[str, Any]] = {}
        pending_error: BaseException | None = None

        previous_signal_handlers = {
            signum: signal.getsignal(signum)
            for signum in (signal.SIGTERM, signal.SIGINT)
        }
        cleanup_signal_state = CleanupSignalState()

        for signum in previous_signal_handlers:
            signal.signal(signum, cleanup_signal_state.handle)
        try:
            ACTIVE_CLI_DEADLINE = execution_deadline
            stage_started = time.monotonic()
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
            print(
                "BENCHMARK stage=solution-import "
                f"duration_seconds={time.monotonic() - stage_started:.3f}"
            )

            for index, case in enumerate(SCENARIOS, start=1):
                scenario_started = time.monotonic()
                # Stop before a scenario that cannot finish inside the
                # budget rather than after it has already overrun: a
                # part-run scenario is indistinguishable from a real
                # failure in the score.
                remaining = execution_deadline - time.monotonic()
                if remaining < SCENARIO_BUDGET_SECONDS:
                    raise CheckFailure(
                        "BUDGET OVERRUN, NOT A SCENARIO FAILURE: only "
                        f"{remaining:.0f}s of the {LIVE_RUN_DEADLINE_SECONDS}s "
                        f"run budget remained before scenario {index}/"
                        f"{len(SCENARIOS)} ({case.name}), under the "
                        f"{SCENARIO_BUDGET_SECONDS}s per-scenario budget. "
                        f"Scenarios 1-{index - 1} passed. Raise the "
                        "run_command timeout in "
                        "customer_escalation_triage.yaml (and the derived "
                        "deadlines here) or shorten the matrix; entering "
                        "graceful cleanup."
                    )
                log_file = root / f"{index:02d}-{case.name}.log"
                update_issue_key = None
                if case.outputs["jiraAction"] == "UpdateExisting":
                    seed_started = time.monotonic()
                    update_issue_key = create_seed_jira_issue(
                        case,
                        environment,
                        side_effects,
                    )
                    print(
                        f"BENCHMARK scenario={case.name} stage=jira-seed "
                        "duration_seconds="
                        f"{time.monotonic() - seed_started:.3f}"
                    )
                inputs = scenario_inputs(
                    case,
                    environment,
                    duplicate_key=(
                        f"  {update_issue_key}\t "
                        if update_issue_key is not None
                        else None
                    ),
                )
                correlation = case.inputs["correlationId"]
                live_runs.begin(case.name, correlation)
                debug_started = time.monotonic()
                (
                    debug,
                    debug_payload,
                    debug_data,
                    instance_id,
                ) = run_debug_with_cleanup_recovery(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug",
                        str(imported_project),
                        "--poll-interval",
                        "500",
                        "--inputs",
                        json.dumps(inputs, separators=(",", ":")),
                    ],
                    log_file=log_file,
                    case_name=case.name,
                    contract=contract,
                    environment=environment,
                    solution_lease=lease,
                    side_effects=side_effects,
                    live_run_lease=live_runs,
                    correlation=correlation,
                )
                print(
                    f"BENCHMARK scenario={case.name} stage=debug "
                    "duration_seconds="
                    f"{time.monotonic() - debug_started:.3f}"
                )

                evidence_started = time.monotonic()
                _variables_payload, variables_data = (
                    variables_all_with_cleanup_recovery(
                        instance_id,
                        case.name,
                        contract,
                        environment,
                        lease,
                        side_effects,
                    )
                )

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
                _incidents_payload, incidents_data = payload_data(
                    incidents,
                    f"{case.name} incidents",
                )
                print(
                    f"BENCHMARK scenario={case.name} "
                    "stage=runtime-evidence "
                    "duration_seconds="
                    f"{time.monotonic() - evidence_started:.3f}"
                )

                assertion_started = time.monotonic()
                try:
                    assert_scenario(
                        case,
                        contract,
                        debug_data,
                        variables_data,
                        incidents_data,
                        environment,
                        side_effects,
                        update_issue_key=update_issue_key,
                    )
                except CheckFailure as exc:
                    # Record and keep going. A failed scenario must not hide
                    # the verdict of the nine that come after it.
                    detail = (
                        f"{exc}; debug exit={debug.returncode}; "
                        f"debug={json.dumps(debug_payload)[:5000]}; "
                        f"variables={json.dumps(variables_data)[:5000]}; "
                        f"incidents={json.dumps(incidents_data)[:3000]}; "
                        f"log={tail_log(log_file)}"
                    )
                    scenario_results[case.name] = {
                        "passed": False,
                        "error": detail[:4000],
                    }
                    print(f"FAIL live Alpha {index}/{len(SCENARIOS)}: "
                          f"{case.name}: {exc}")
                else:
                    scenario_results[case.name] = {"passed": True}
                side_effect_cleanup = side_effects.cleanup()
                if side_effect_cleanup:
                    cleanup_failures.append(
                        f"{case.name}: connector cleanup failed: "
                        f"{'; '.join(side_effect_cleanup)}"
                    )
                live_runs.complete(instance_id, correlation)
                print(
                    f"BENCHMARK scenario={case.name} "
                    "stage=assert-and-cleanup "
                    "duration_seconds="
                    f"{time.monotonic() - assertion_started:.3f}"
                )
                elapsed = time.monotonic() - scenario_started
                scenario_results[case.name]["duration_seconds"] = round(
                    elapsed, 3
                )
                if scenario_results[case.name]["passed"]:
                    print(
                        f"PASS live Alpha {index}/{len(SCENARIOS)}: "
                        f"{case.name} duration_seconds={elapsed:.3f}"
                    )
        except BaseException as exc:
            pending_error = exc
        finally:
            cleanup_signal_state.begin_cleanup()
            ACTIVE_CLI_DEADLINE = cleanup_deadline
            cleanup_stages = (
                ("debug instance", live_runs.cleanup),
                ("connector side effect", side_effects.cleanup),
                ("Alpha solution", lease.cleanup),
            )
            try:
                cleanup_failures.extend(
                    collect_cleanup_failures(
                        cleanup_stages,
                        emit_benchmarks=True,
                    )
                )
            finally:
                for signum, previous in previous_signal_handlers.items():
                    signal.signal(signum, previous)
                ACTIVE_CLI_DEADLINE = None

        if (
            cleanup_signal_state.termination_requested
            and pending_error is None
        ):
            pending_error = KeyboardInterrupt(
                "terminated during live Alpha evaluation"
            )
        write_scenario_results(scenario_results)
        if cleanup_failures:
            detail = "; ".join(cleanup_failures)
            if pending_error is not None:
                raise CheckFailure(
                    f"{pending_error}; Alpha cleanup also failed: {detail}"
                ) from pending_error
            raise CheckFailure(f"Alpha cleanup failed: {detail}")
        if pending_error is not None:
            raise pending_error

        failed = sorted(
            name
            for name, result in scenario_results.items()
            if not result.get("passed")
        )
        if failed:
            raise CheckFailure(
                f"{len(failed)} of {len(SCENARIOS)} live Alpha scenarios "
                f"failed: {failed}. Per-scenario verdicts and per-family "
                f"partial credit are in {SCENARIO_RESULTS}."
            )
        deleted = ", ".join(sorted(lease.solution_ids))
        print(
            f"PASS: {len(SCENARIOS)} exact-artifact Alpha scenarios; "
            f"ephemeral solution deleted ({deleted}); "
            "total_duration_seconds="
            f"{time.monotonic() - checker_started_monotonic:.3f}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
