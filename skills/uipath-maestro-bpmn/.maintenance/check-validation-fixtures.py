#!/usr/bin/env python3
"""Validate the synthetic Maestro BPMN fixture corpus.

The checker intentionally stays dependency-free so contributors and CI can run
it without access to PO.FrontEnd or private exported BPMN. It validates the
public contract shape these fixtures are meant to preserve.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "validation"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
UIPATH_NS = "http://uipath.org/schema/bpmn"

NODE_TYPES = {
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "manualTask",
    "businessRuleTask",
    "scriptTask",
    "callActivity",
    "subProcess",
    "adHocSubProcess",
    "exclusiveGateway",
    "inclusiveGateway",
    "parallelGateway",
    "eventBasedGateway",
    "complexGateway",
}

GENERATION_EXCLUDED_BPMN_TAGS = {
    "adHocSubProcess",
    "cancelEventDefinition",
    "compensateEventDefinition",
    "complexGateway",
    "conditionalEventDefinition",
    "escalationEventDefinition",
    "linkEventDefinition",
    "manualTask",
    "multipleEventDefinition",
    "parallelMultipleEventDefinition",
    "signalEventDefinition",
    "transaction",
}

ALLOWED_RETRY_ATTRS = {
    "version",
    "maxRetryCount",
    "retryBackoff",
    "retryAllErrors",
    "retryBackoffType",
    "maxDuration",
    "exponentialBase",
}

ALLOWED_ERROR_MAPPING_ATTRS = {"version"}
ALLOWED_ERROR_ATTRS = {"id", "errorRef", "priority", "condition", "detail", "retryable"}
SPECIAL_RUNTIME_VARS = {"error"}

ALLOWED_URLS = (
    "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "http://www.omg.org/spec/BPMN/20100524/DI",
    "http://www.omg.org/spec/DD/20100524/DC",
    "http://www.omg.org/spec/DD/20100524/DI",
    "http://www.w3.org/2001/XMLSchema-instance",
    "http://uipath.org/schema/bpmn",
    "http://uipath.com/synthetic/maestro-bpmn/",
)

SERVICE_TYPE_WRAPPERS = {
    "A2A.AgentExecution": {"wrapper": {"serviceTask"}, "extension": "activity"},
    "Orchestrator.ExecuteApiWorkflowAsync": {
        "wrapper": {"serviceTask"},
        "extension": "activity",
    },
    "Orchestrator.BusinessRules": {
        "wrapper": {"businessRuleTask"},
        "extension": "activity",
    },
    "Orchestrator.CreateAndWaitForQueueItem": {
        "wrapper": {"serviceTask"},
        "extension": "activity",
    },
    "Orchestrator.StartCaseMgmtProcess": {
        "wrapper": {"callActivity"},
        "extension": "activity",
    },
    "Orchestrator.StartCaseMgmtProcessAsync": {
        "wrapper": {"callActivity"},
        "extension": "activity",
    },
    "Intsvc.WaitForEvent": {
        "wrapper": {"receiveTask", "intermediateCatchEvent", "boundaryEvent"},
        "extension": "event",
    },
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def ns(tag: str) -> str:
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return ""


def build_parent_map(root: ET.Element) -> dict[int, ET.Element]:
    parents: dict[int, ET.Element] = {}
    for parent in root.iter():
        for child in parent:
            parents[id(child)] = parent
    return parents


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.projects = 0
        self.bpmn_files = 0
        self.contract_hits: set[str] = set()

    def error(self, path: Path, message: str) -> None:
        self.errors.append(f"{path.relative_to(ROOT)}: {message}")

    def validate(self) -> int:
        if not FIXTURES.is_dir():
            print(f"ERROR: fixtures directory not found: {FIXTURES}", file=sys.stderr)
            return 2

        for project in sorted(p for p in FIXTURES.iterdir() if p.is_dir()):
            self.projects += 1
            self.validate_project(project)

        self.validate_contract_coverage()
        regression_errors = self.validate_regressions()
        self.errors.extend(regression_errors)

        for err in self.errors:
            print(f"ERROR: {err}")
        print(
            f"validation_fixture_projects={self.projects} "
            f"bpmn_files={self.bpmn_files} errors={len(self.errors)}"
        )
        return 1 if self.errors else 0

    def validate_project(self, project: Path) -> None:
        expected = [
            "project.uiproj",
            "bindings_v2.json",
            "entry-points.json",
            "operate.json",
            "package-descriptor.json",
        ]
        for name in expected:
            if not (project / name).is_file():
                self.error(project, f"missing {name}")

        bpmn_files = sorted(project.glob("*.bpmn"))
        if len(bpmn_files) != 1:
            self.error(project, f"expected exactly one .bpmn file, found {len(bpmn_files)}")
            return

        bpmn = bpmn_files[0]
        self.bpmn_files += 1
        text = bpmn.read_text(encoding="utf-8")
        self.validate_public_safety(bpmn, text)

        try:
            tree = ET.parse(bpmn)
        except ET.ParseError as exc:
            self.error(bpmn, f"XML parse failed: {exc}")
            return

        root = tree.getroot()
        self.validate_bpmn_document(bpmn, root)
        self.validate_package_files(project, bpmn.name, root)

    def validate_regressions(self) -> list[str]:
        errors: list[str] = []
        errors.extend(self.validate_gateway_misnamed_repro())
        errors.extend(self.validate_bindings_version_repro())
        errors.extend(self.validate_script_result_response_repro())
        return errors

    def validate_gateway_misnamed_repro(self) -> list[str]:
        """Assert single-BPMN package metadata fails when the BPMN basename drifts."""

        fixture = FIXTURES / "gateway-boundary-error"
        if not fixture.is_dir():
            return [
                "regression gateway-misnamed-repro: "
                "source fixture gateway-boundary-error is missing"
            ]

        with tempfile.TemporaryDirectory(prefix="gateway-misnamed-repro-", dir=ROOT) as tmp:
            project = Path(tmp) / "gateway-boundary-error"
            shutil.copytree(fixture, project)
            original_bpmn = project / "gateway-boundary-error.bpmn"
            renamed_bpmn = project / "gateway-misnamed-repro.bpmn"
            original_bpmn.rename(renamed_bpmn)

            regression = Validator()
            regression.validate_project(project)
            basename_errors = [
                err
                for err in regression.errors
                if "main basename does not match single BPMN file basename" in err
            ]
            if basename_errors:
                return []

            details = "; ".join(regression.errors) or "no validation error"
            return [
                "regression gateway-misnamed-repro failed: expected basename validation "
                "error for a copied project whose single BPMN file no longer matches "
                "the project directory name; "
                f"observed: {details}"
            ]

    def validate_bindings_version_repro(self) -> list[str]:
        """Assert bindings_v2.json without version is rejected."""

        fixture = FIXTURES / "linear-process"
        if not fixture.is_dir():
            return [
                "regression bindings-version-repro: "
                "source fixture linear-process is missing"
            ]

        with tempfile.TemporaryDirectory(prefix="bindings-version-repro-", dir=ROOT) as tmp:
            project = Path(tmp) / "linear-process"
            shutil.copytree(fixture, project)
            bindings_path = project / "bindings_v2.json"
            data = json.loads(bindings_path.read_text(encoding="utf-8"))
            data.pop("version", None)
            bindings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

            regression = Validator()
            regression.validate_project(project)
            if any("version must be 2.0" in err for err in regression.errors):
                return []

            details = "; ".join(regression.errors) or "no validation error"
            return [
                "regression bindings-version-repro failed: expected bindings_v2.json "
                f"version validation error; observed: {details}"
            ]

    def validate_script_result_response_repro(self) -> list[str]:
        """Assert script output mappings cannot read result fields above response."""

        fixture = FIXTURES / "subprocess-multi-instance"
        if not fixture.is_dir():
            return [
                "regression script-result-response-repro: "
                "source fixture subprocess-multi-instance is missing"
            ]

        with tempfile.TemporaryDirectory(prefix="script-result-response-repro-", dir=ROOT) as tmp:
            project = Path(tmp) / "subprocess-multi-instance"
            shutil.copytree(fixture, project)
            bpmn = project / "subprocess-multi-instance.bpmn"
            text = bpmn.read_text(encoding="utf-8")
            text = text.replace('source="=result.response"', 'source="=result.outcome"', 1)
            bpmn.write_text(text, encoding="utf-8")

            regression = Validator()
            regression.validate_project(project)
            expected = "BPMN.ScriptTask output source must read result.response"
            if any(expected in err for err in regression.errors):
                return []

            details = "; ".join(regression.errors) or "no validation error"
            return [
                "regression script-result-response-repro failed: expected script output "
                f"result.response validation error; observed: {details}"
            ]

    def validate_public_safety(self, path: Path, text: str) -> None:
        patterns = {
            "email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "local absolute path": r"(/Users/|/home/|C:\\\\Users\\\\)",
            "guid-like identifier": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        }
        for label, pattern in patterns.items():
            if re.search(pattern, text):
                self.error(path, f"contains {label}")

        for match in re.finditer(r"https?://[^\s\"'>]+", text):
            url = match.group(0)
            if not any(url.startswith(allowed) for allowed in ALLOWED_URLS):
                self.error(path, f"contains non-allowlisted URL {url}")

    def validate_bpmn_document(self, path: Path, root: ET.Element) -> None:
        if local(root.tag) != "definitions" or ns(root.tag) != BPMN_NS:
            self.error(path, "root element is not bpmn:definitions")

        if (
            root.attrib.get("targetNamespace", "").startswith("http://uipath.com/synthetic/")
            is False
        ):
            self.error(path, "targetNamespace must be synthetic")

        elements_by_id = {
            elem.attrib["id"]: elem
            for elem in root.iter()
            if "id" in elem.attrib
            and ns(elem.tag) in {BPMN_NS, BPMNDI_NS}
            and local(elem.tag) != "BPMNShape"
            and local(elem.tag) != "BPMNEdge"
        }

        processes = root.findall(f"{{{BPMN_NS}}}process")
        executable = [p for p in processes if p.attrib.get("isExecutable") == "true"]
        if len(executable) != 1:
            self.error(path, f"expected one executable process, found {len(executable)}")
            return
        process = executable[0]

        bindings = self.collect_root_bindings(process)
        variables = self.collect_variables(process)
        self.validate_diagram(path, root, elements_by_id)
        self.validate_sequence_flows(path, root, elements_by_id)
        self.validate_start_events(path, process)
        self.validate_entry_points(path, process)
        self.validate_gateway_conditions(path, root, bindings, variables)
        self.validate_generation_exclusions(path, root)
        self.validate_error_events(path, root, elements_by_id)
        self.validate_error_handling(path, root, elements_by_id, bindings, variables)
        self.validate_message_events(path, root, elements_by_id)
        self.validate_multi_instance(path, root, variables)
        self.validate_uipath_extensions(path, root, bindings, variables)
        self.record_contract_coverage(root)

    def validate_generation_exclusions(self, path: Path, root: ET.Element) -> None:
        for elem in root.iter():
            if ns(elem.tag) != BPMN_NS:
                continue
            kind = local(elem.tag)
            if kind in GENERATION_EXCLUDED_BPMN_TAGS:
                self.error(path, f"uses generation-excluded BPMN tag {kind}")

        for loop in root.findall(f".//{{{BPMN_NS}}}standardLoopCharacteristics"):
            self.error(
                path,
                f"uses generation-excluded BPMN tag {local(loop.tag)}",
            )

    def record_contract_coverage(self, root: ET.Element) -> None:
        for version in root.findall(f".//{{{UIPATH_NS}}}migrationVersion"):
            value = version.attrib.get("version")
            if value:
                self.contract_hits.add(f"migration:{value}")

        for script_version in root.findall(f".//{{{UIPATH_NS}}}scriptVersion"):
            value = script_version.attrib.get("value")
            if value:
                self.contract_hits.add(f"scriptVersion:{value}")

        if root.findall(f".//{{{UIPATH_NS}}}caseManagement"):
            self.contract_hits.add("preserve:caseManagement")
        if root.findall(f".//{{{UIPATH_NS}}}Activity"):
            self.contract_hits.add("preserve:generic-uipath-Activity")

        for bpmn_elem in root.iter():
            if ns(bpmn_elem.tag) != BPMN_NS:
                continue
            wrapper = local(bpmn_elem.tag)
            extension = bpmn_elem.find(f"{{{BPMN_NS}}}extensionElements")
            if extension is None:
                continue
            for extension_kind in ("activity", "event"):
                for payload in extension.findall(f"{{{UIPATH_NS}}}{extension_kind}"):
                    type_elem = payload.find(f"{{{UIPATH_NS}}}type")
                    if type_elem is None:
                        continue
                    service_type = type_elem.attrib.get("value")
                    if service_type:
                        self.contract_hits.add(f"{wrapper}:{service_type}")

    def validate_contract_coverage(self) -> None:
        # Public-safe XML shells from the current registry surface plus
        # preserve-only imported payloads. CLI-owned Intsvc.* entries are
        # represented with synthetic binding shells only; connector-specific
        # schemas and generated package resources remain outside this fixture.
        expected = {
            "userTask:Actions.HITL",
            "serviceTask:Orchestrator.StartJob",
            "serviceTask:Orchestrator.StartAgentJob",
            "serviceTask:A2A.AgentExecution",
            "serviceTask:Orchestrator.ExecuteApiWorkflowAsync",
            "businessRuleTask:Orchestrator.BusinessRules",
            "sendTask:Orchestrator.CreateQueueItem",
            "serviceTask:Orchestrator.CreateAndWaitForQueueItem",
            "callActivity:Orchestrator.StartAgenticProcess",
            "callActivity:Orchestrator.StartAgenticProcessAsync",
            "callActivity:Orchestrator.StartCaseMgmtProcess",
            "callActivity:Orchestrator.StartCaseMgmtProcessAsync",
            "intermediateThrowEvent:Maestro.SendMessageEvent",
            "serviceTask:Maestro.CasePlanScheduler",
            "serviceTask:Maestro.CaseManagerGuardrails",
            "serviceTask:Maestro.CaseRulesEvaluator",
            "receiveTask:Intsvc.WaitForEvent",
            "startEvent:Intsvc.EventTrigger",
            "serviceTask:Intsvc.ActivityExecution",
            "serviceTask:Intsvc.AsyncExecution",
            "serviceTask:Intsvc.SyncAgentExecution",
            "serviceTask:Intsvc.AsyncAgentExecution",
            "serviceTask:Intsvc.SyncWorkflowExecution",
            "serviceTask:Intsvc.AsyncWorkflowExecution",
            "sendTask:Intsvc.HttpExecution",
            "sendTask:Intsvc.UnifiedHttpRequest",
            "startEvent:Intsvc.TimerTrigger",
            "preserve:caseManagement",
            "preserve:generic-uipath-Activity",
            "migration:5",
            "migration:11",
            "migration:11.5",
            "scriptVersion:v2",
            "scriptVersion:v3",
        }
        missing = sorted(expected - self.contract_hits)
        if missing:
            self.errors.append(
                "fixtures/validation: missing XML contract coverage for " + ", ".join(missing)
            )

    def collect_root_bindings(self, process: ET.Element) -> dict[str, ET.Element]:
        result: dict[str, ET.Element] = {}
        for binding in process.findall(
            f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}bindings/{{{UIPATH_NS}}}binding"
        ):
            result[binding.attrib["id"]] = binding
        return result

    def collect_variables(self, root: ET.Element) -> dict[str, set[str]]:
        variables: dict[str, set[str]] = {
            "root": set(),
            "all": set(),
            "writable": set(),
            "names": set(),
        }
        root_variables = root.find(
            f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}variables"
        )
        for vars_elem in root.findall(f".//{{{UIPATH_NS}}}variables"):
            for child in list(vars_elem):
                var_id = child.attrib.get("id")
                if child.attrib.get("name"):
                    variables["names"].add(child.attrib["name"])
                if var_id:
                    variables["all"].add(var_id)
                    if vars_elem is root_variables:
                        variables["root"].add(var_id)
                    if local(child.tag) in {"inputOutput", "output"}:
                        variables["writable"].add(var_id)
        return variables

    def validate_diagram(
        self, path: Path, root: ET.Element, elements_by_id: dict[str, ET.Element]
    ) -> None:
        planes = root.findall(f".//{{{BPMNDI_NS}}}BPMNPlane")
        if not planes:
            self.error(path, "missing BPMNPlane")
            return
        for plane in planes:
            ref = plane.attrib.get("bpmnElement")
            if ref not in elements_by_id:
                self.error(path, f"BPMNPlane references missing element {ref}")

        shape_refs = {
            shape.attrib.get("bpmnElement")
            for shape in root.findall(f".//{{{BPMNDI_NS}}}BPMNShape")
        }
        edge_refs = {
            edge.attrib.get("bpmnElement") for edge in root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge")
        }

        for elem_id, elem in elements_by_id.items():
            kind = local(elem.tag)
            if kind in NODE_TYPES and elem_id not in shape_refs:
                self.error(path, f"missing BPMNShape for {elem_id}")
            if kind == "sequenceFlow" and elem_id not in edge_refs:
                self.error(path, f"missing BPMNEdge for {elem_id}")

        for edge in root.findall(f".//{{{BPMNDI_NS}}}BPMNEdge"):
            if len(edge.findall(f"{{{DI_NS}}}waypoint")) < 2:
                self.error(path, f"BPMNEdge {edge.attrib.get('id')} has fewer than two waypoints")

    def validate_sequence_flows(
        self, path: Path, root: ET.Element, elements_by_id: dict[str, ET.Element]
    ) -> None:
        for flow in root.findall(f".//{{{BPMN_NS}}}sequenceFlow"):
            source = elements_by_id.get(flow.attrib.get("sourceRef", ""))
            target = elements_by_id.get(flow.attrib.get("targetRef", ""))
            if source is None or target is None:
                self.error(
                    path, f"sequenceFlow {flow.attrib.get('id')} has missing source or target"
                )
                continue
            if local(source.tag) == "endEvent":
                self.error(path, f"sequenceFlow {flow.attrib.get('id')} starts at an end event")
            if local(target.tag) == "startEvent":
                self.error(path, f"sequenceFlow {flow.attrib.get('id')} targets a start event")

    def validate_start_events(self, path: Path, process: ET.Element) -> None:
        scopes = [process] + process.findall(f".//{{{BPMN_NS}}}subProcess")
        for scope in scopes:
            starts = [c for c in list(scope) if local(c.tag) == "startEvent"]
            blank = [
                s
                for s in starts
                if not any(local(c.tag).endswith("EventDefinition") for c in list(s))
            ]
            if len(blank) > 1:
                self.error(path, f"scope {scope.attrib.get('id')} has multiple blank start events")
            if scope.attrib.get("triggeredByEvent") == "true" and len(starts) != 1:
                self.error(
                    path,
                    f"event subprocess {scope.attrib.get('id')} must have exactly one start event",
                )

    def validate_entry_points(self, path: Path, process: ET.Element) -> None:
        entry_ids: dict[str, str] = {}
        root_starts = [c for c in list(process) if local(c.tag) == "startEvent"]
        for start in root_starts:
            ep = start.find(f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}entryPointId")
            if ep is None:
                continue
            value = ep.attrib.get("value")
            if not value:
                self.error(path, f"start event {start.attrib.get('id')} has empty entryPointId")
            elif value in entry_ids:
                self.error(path, f"duplicate entryPointId {value}")
            else:
                entry_ids[value] = start.attrib["id"]

        for var in process.findall(
            f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}variables/{{{UIPATH_NS}}}input"
        ):
            element_id = var.attrib.get("elementId")
            if element_id and element_id not in {s.attrib["id"] for s in root_starts}:
                self.error(
                    path,
                    f"entry input variable {var.attrib.get('name')} references non-root start {element_id}",
                )

    def validate_gateway_conditions(
        self,
        path: Path,
        root: ET.Element,
        bindings: dict[str, ET.Element],
        variables: dict[str, set[str]],
    ) -> None:
        for gateway in root.findall(f".//{{{BPMN_NS}}}exclusiveGateway"):
            outgoing = [
                child.text for child in gateway.findall(f"{{{BPMN_NS}}}outgoing") if child.text
            ]
            if len(outgoing) < 2:
                continue
            default = gateway.attrib.get("default")
            if default and default not in outgoing:
                self.error(
                    path, f"exclusiveGateway {gateway.attrib.get('id')} default is not outgoing"
                )
            for flow_id in outgoing:
                if flow_id == default:
                    continue
                flow = root.find(f".//{{{BPMN_NS}}}sequenceFlow[@id='{flow_id}']")
                if flow is not None and flow.find(f"{{{BPMN_NS}}}conditionExpression") is None:
                    self.error(path, f"gateway flow {flow_id} is missing conditionExpression")
                elif flow is not None:
                    condition = flow.find(f"{{{BPMN_NS}}}conditionExpression")
                    if condition is not None:
                        self.validate_expression_value(
                            path,
                            condition.text or "",
                            bindings,
                            variables,
                            f"conditionExpression {flow_id}",
                        )

    def validate_error_events(
        self, path: Path, root: ET.Element, elements_by_id: dict[str, ET.Element]
    ) -> None:
        for event_def in root.findall(f".//{{{BPMN_NS}}}errorEventDefinition"):
            ref = event_def.attrib.get("errorRef")
            if ref and ref not in elements_by_id:
                self.error(path, f"errorEventDefinition references missing error {ref}")

        for boundary in root.findall(f".//{{{BPMN_NS}}}boundaryEvent"):
            attached = boundary.attrib.get("attachedToRef")
            if attached not in elements_by_id:
                self.error(
                    path,
                    f"boundaryEvent {boundary.attrib.get('id')} references missing activity {attached}",
                )

    def validate_error_handling(
        self,
        path: Path,
        root: ET.Element,
        elements_by_id: dict[str, ET.Element],
        bindings: dict[str, ET.Element],
        variables: dict[str, set[str]],
    ) -> None:
        for retry in root.findall(f".//{{{UIPATH_NS}}}retry"):
            for attr in retry.attrib:
                if attr not in ALLOWED_RETRY_ATTRS:
                    self.error(path, f"uipath:retry uses unsupported attribute {attr}")

            max_retry = retry.attrib.get("maxRetryCount")
            if max_retry and not max_retry.isdigit():
                self.error(path, "uipath:retry maxRetryCount must be an integer")

            retry_all = retry.attrib.get("retryAllErrors")
            if retry_all and retry_all not in {"true", "false"}:
                self.error(path, "uipath:retry retryAllErrors must be true or false")

            for error_def in retry.findall(f"{{{UIPATH_NS}}}errorDefinition"):
                ref = error_def.attrib.get("errorRef")
                if ref and ref not in elements_by_id:
                    self.error(path, f"uipath:retry errorDefinition references missing error {ref}")

        for mapping in root.findall(f".//{{{UIPATH_NS}}}errorMapping"):
            for attr in mapping.attrib:
                if attr not in ALLOWED_ERROR_MAPPING_ATTRS:
                    self.error(path, f"uipath:errorMapping uses unsupported attribute {attr}")

            for error in mapping.findall(f"{{{UIPATH_NS}}}error"):
                for attr in error.attrib:
                    if attr not in ALLOWED_ERROR_ATTRS:
                        self.error(
                            path,
                            f"uipath:errorMapping error uses unsupported attribute {attr}",
                        )

                ref = error.attrib.get("errorRef")
                if ref and ref not in elements_by_id:
                    self.error(path, f"uipath:errorMapping references missing error {ref}")

                priority = error.attrib.get("priority")
                if priority is not None and not priority.isdigit():
                    self.error(path, "uipath:errorMapping priority must be an integer")

                retryable = error.attrib.get("retryable")
                if retryable and retryable not in {"true", "false"}:
                    self.error(path, "uipath:errorMapping retryable must be true or false")

                self.validate_expression_value(
                    path,
                    error.attrib.get("condition", ""),
                    bindings,
                    variables,
                    f"errorMapping {error.attrib.get('id')}",
                )

    def validate_message_events(
        self, path: Path, root: ET.Element, elements_by_id: dict[str, ET.Element]
    ) -> None:
        for event_def in root.findall(f".//{{{BPMN_NS}}}messageEventDefinition"):
            ref = event_def.attrib.get("messageRef")
            if ref and ref not in elements_by_id:
                self.error(path, f"messageEventDefinition references missing message {ref}")

    def validate_multi_instance(
        self, path: Path, root: ET.Element, variables: dict[str, set[str]]
    ) -> None:
        parent_map = build_parent_map(root)
        for loop in root.findall(f".//{{{BPMN_NS}}}multiInstanceLoopCharacteristics"):
            marker = loop.attrib.get("isSequential")
            if marker not in {"true", "false"}:
                self.error(
                    path,
                    f"multiInstanceLoopCharacteristics {loop.attrib.get('id')} "
                    "must set isSequential to true or false",
                )

            metadata = loop.find(
                f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}loopCharacteristics"
            )
            if metadata is None:
                self.error(
                    path,
                    f"multiInstanceLoopCharacteristics {loop.attrib.get('id')} "
                    "missing uipath:loopCharacteristics",
                )
                continue

            input_collection = metadata.attrib.get("inputCollection", "")
            collection_vars = self.expression_variable_ids(input_collection)
            has_declared_collection = any(
                var_id in variables["all"] for var_id in collection_vars
            )
            if not collection_vars or not has_declared_collection:
                self.error(
                    path,
                    f"multi-instance inputCollection references undeclared variable "
                    f"{input_collection}",
                )

            input_element = metadata.attrib.get("inputElement")
            if not input_element:
                self.error(
                    path,
                    f"multi-instance inputElement is missing on {loop.attrib.get('id')}",
                )
            elif local(parent_map.get(id(loop), ET.Element("")).tag) == "subProcess":
                if input_element != "iterator[0]":
                    self.error(
                        path,
                        f"multi-instance subprocess inputElement must be iterator[0], "
                        f"found {input_element}",
                    )
            elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\])?", input_element):
                self.error(path, f"multi-instance inputElement has invalid shape {input_element}")

            self.validate_expression_value(
                path,
                input_collection,
                {},
                variables,
                f"multi-instance inputCollection {loop.attrib.get('id')}",
            )
            self.validate_expression_value(
                path,
                metadata.attrib.get("filterCondition", ""),
                {},
                variables,
                f"multi-instance filterCondition {loop.attrib.get('id')}",
            )

            completion = loop.find(f"{{{BPMN_NS}}}completionCondition")
            if completion is not None:
                self.validate_expression_value(
                    path,
                    completion.text or "",
                    {},
                    variables,
                    f"multi-instance completionCondition {loop.attrib.get('id')}",
                )

    def expression_variable_ids(self, value: str) -> set[str]:
        return set(re.findall(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)", value))

    def extract_expressions(self, value: str) -> list[str]:
        if not value:
            return []
        expressions: list[str] = []
        stripped = value.strip()
        if stripped.startswith("="):
            expressions.append(stripped)
        expressions.extend(match.group(1).strip() for match in re.finditer(r'"(=[^"]+)"', value))
        return expressions

    def validate_expression_value(
        self,
        path: Path,
        value: str,
        bindings: dict[str, ET.Element],
        variables: dict[str, set[str]],
        label: str,
    ) -> None:
        for expression in self.extract_expressions(value):
            if self.contains_assignment(expression):
                self.error(path, f"{label} may contain assignment: {expression}")

            for binding_ref in re.findall(r"\bbindings\.([A-Za-z0-9_]+)", expression):
                if binding_ref not in bindings:
                    self.error(
                        path,
                        f"{label} references undeclared binding {binding_ref}",
                    )

            for var_ref in self.expression_variable_ids(expression):
                if var_ref not in variables["all"] and var_ref not in SPECIAL_RUNTIME_VARS:
                    self.error(path, f"{label} references undeclared variable id {var_ref}")

            for var_name in sorted(variables["names"], key=len, reverse=True):
                if re.search(rf"={re.escape(var_name)}(?=$|[^A-Za-z0-9_])", expression):
                    self.error(
                        path,
                        f"{label} uses bare variable name {var_name}; use vars.<variableId>",
                    )

    def contains_assignment(self, value: str) -> bool:
        return "=" in value and re.search(r"(?<![=!<>])=(?!=)", value[1:]) is not None

    def validate_uipath_extensions(
        self,
        path: Path,
        root: ET.Element,
        bindings: dict[str, ET.Element],
        variables: dict[str, set[str]],
    ) -> None:
        parent_map = build_parent_map(root)
        for elem in root.iter():
            if ns(elem.tag) != UIPATH_NS:
                continue
            if local(elem.tag) in {"activity", "event"}:
                self.validate_activity_or_event(path, elem, bindings, parent_map)
            if local(elem.tag) == "mapping":
                self.validate_script_mapping(path, elem, parent_map)
            if local(elem.tag) == "output":
                target = elem.attrib.get("var") or elem.attrib.get("target")
                if target and target not in variables["writable"]:
                    self.error(path, f"uipath:output targets non-writable variable id {target}")

            for attr_name, attr_value in elem.attrib.items():
                self.validate_expression_value(
                    path,
                    attr_value,
                    bindings,
                    variables,
                    f"uipath:{local(elem.tag)} @{attr_name}",
                )
            self.validate_expression_value(
                path,
                elem.text or "",
                bindings,
                variables,
                f"uipath:{local(elem.tag)} text",
            )

    def validate_script_mapping(
        self,
        path: Path,
        elem: ET.Element,
        parent_map: dict[int, ET.Element],
    ) -> None:
        type_elem = elem.find(f"{{{UIPATH_NS}}}type")
        mapping_type = type_elem.attrib.get("value") if type_elem is not None else None
        extension_elements = parent_map.get(id(elem))
        bpmn_parent = parent_map.get(id(extension_elements))
        is_script_parent = bpmn_parent is not None and local(bpmn_parent.tag) == "scriptTask"
        if mapping_type != "BPMN.ScriptTask" and not is_script_parent:
            return

        for output in elem.findall(f"{{{UIPATH_NS}}}output"):
            source = output.attrib.get("source", "")
            if source.startswith("=result.") and not source.startswith("=result.response"):
                self.error(
                    path,
                    "BPMN.ScriptTask output source must read result.response "
                    f"or result.response.<field>, found {source}",
                )

    def validate_activity_or_event(
        self,
        path: Path,
        elem: ET.Element,
        bindings: dict[str, ET.Element],
        parent_map: dict[int, ET.Element],
    ) -> None:
        type_elem = elem.find(f"{{{UIPATH_NS}}}type")
        service_type = type_elem.attrib.get("value") if type_elem is not None else None
        if not service_type:
            self.error(path, "uipath activity/event missing type")
            return

        extension_kind = local(elem.tag)
        extension_elements = parent_map.get(id(elem))
        wrapper = local(parent_map.get(id(extension_elements), ET.Element("")).tag)
        expected = SERVICE_TYPE_WRAPPERS.get(service_type)
        if expected is not None:
            if extension_kind != expected["extension"]:
                self.error(
                    path,
                    f"{service_type} must use uipath:{expected['extension']}, found "
                    f"uipath:{extension_kind}",
                )
            if wrapper not in expected["wrapper"]:
                self.error(
                    path,
                    f"{service_type} must use BPMN wrapper "
                    f"{sorted(expected['wrapper'])}, found {wrapper or 'unknown'}",
                )

        context = elem.find(f"{{{UIPATH_NS}}}context")
        if context is None:
            self.error(path, f"{service_type} missing context")
            return
        context_inputs = {
            child.attrib.get("name"): child.attrib.get("value", "")
            for child in list(context)
            if local(child.tag) == "input"
        }

        if service_type.startswith("Intsvc."):
            connection_backed = {
                "Intsvc.ActivityExecution",
                "Intsvc.WaitForEvent",
                "Intsvc.EventTrigger",
                "Intsvc.AsyncExecution",
                "Intsvc.SyncAgentExecution",
                "Intsvc.AsyncAgentExecution",
                "Intsvc.SyncWorkflowExecution",
                "Intsvc.AsyncWorkflowExecution",
            }
            operation_backed = {
                "Intsvc.ActivityExecution",
                "Intsvc.AsyncExecution",
                "Intsvc.SyncAgentExecution",
                "Intsvc.AsyncAgentExecution",
                "Intsvc.SyncWorkflowExecution",
                "Intsvc.AsyncWorkflowExecution",
            }
            connection = context_inputs.get("connection", "")
            if service_type in connection_backed:
                match = re.fullmatch(r"=bindings\.([A-Za-z0-9_]+)", connection)
                if not match or match.group(1) not in bindings:
                    self.error(path, f"{service_type} missing generated connection binding")
                if "connectorKey" not in context_inputs:
                    self.error(path, f"{service_type} missing connectorKey")
            if service_type in operation_backed:
                for required in ("activity", "operation"):
                    if required not in context_inputs:
                        self.error(path, f"{service_type} missing {required}")
            if service_type in {"Intsvc.EventTrigger", "Intsvc.WaitForEvent"}:
                for required in ("trigger", "eventName"):
                    if required not in context_inputs:
                        self.error(path, f"{service_type} missing {required}")

        if service_type == "Orchestrator.StartAgentJob":
            direct_inputs = {
                child.attrib.get("name"): child
                for child in list(elem)
                if local(child.tag) == "input"
            }
            direct_outputs = [
                child for child in list(elem) if local(child.tag) == "output"
            ]
            if "JobArguments" not in direct_inputs:
                self.error(path, "Orchestrator.StartAgentJob missing direct JobArguments input")
            if not any(
                output.attrib.get("name") == "Process response"
                and output.attrib.get("type") == "Orchestrator.RunJob"
                and output.attrib.get("var")
                for output in direct_outputs
            ):
                self.error(
                    path,
                    "Orchestrator.StartAgentJob missing direct Process response output",
                )

    def validate_package_files(self, project: Path, bpmn_name: str, root: ET.Element) -> None:
        data: dict[str, object] = {}
        for name in (
            "project.uiproj",
            "bindings_v2.json",
            "entry-points.json",
            "operate.json",
            "package-descriptor.json",
        ):
            path = project / name
            if not path.is_file():
                return
            try:
                data[name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.error(path, f"JSON parse failed: {exc}")
                return

        if Path(str(data["project.uiproj"].get("main", ""))).name != bpmn_name:  # type: ignore[union-attr]
            self.error(
                project / "project.uiproj",
                "main basename does not match single BPMN file basename",
            )
        if data["project.uiproj"].get("ProjectType") != "ProcessOrchestration":  # type: ignore[union-attr]
            self.error(project / "project.uiproj", "ProjectType must be ProcessOrchestration")
        if "projectType" in data["project.uiproj"] or "name" in data["project.uiproj"]:  # type: ignore[operator]
            self.error(project / "project.uiproj", "uses lowercase project metadata keys")
        if Path(str(data["operate.json"].get("main", ""))).name != bpmn_name:  # type: ignore[union-attr]
            self.error(
                project / "operate.json",
                "main basename does not match single BPMN file basename",
            )
        if data["operate.json"].get("contentType") != "ProcessOrchestration":  # type: ignore[union-attr]
            self.error(project / "operate.json", "contentType must be ProcessOrchestration")

        bindings_file = data["bindings_v2.json"]
        if not isinstance(bindings_file, dict):
            self.error(project / "bindings_v2.json", "must be a JSON object")
            return
        if bindings_file.get("version") != "2.0":
            self.error(project / "bindings_v2.json", "version must be 2.0")
        if not isinstance(bindings_file.get("resources"), list):
            self.error(project / "bindings_v2.json", "resources must be an array")
            return

        descriptor_content = set(data["package-descriptor.json"].get("content", []))  # type: ignore[union-attr]
        for required in (
            f"content/{bpmn_name}",
            "content/bindings_v2.json",
            "content/entry-points.json",
            "content/operate.json",
        ):
            if required not in descriptor_content:
                self.error(project / "package-descriptor.json", f"missing content entry {required}")

        process = root.find(f"{{{BPMN_NS}}}process")
        if process is None:
            return
        root_bindings = self.collect_root_bindings(process)
        package_bindings = {
            resource.get("id")
            for resource in data["bindings_v2.json"].get("resources", [])  # type: ignore[union-attr]
        }
        package_resources = {
            resource.get("id"): resource
            for resource in data["bindings_v2.json"].get("resources", [])  # type: ignore[union-attr]
            if isinstance(resource, dict)
        }
        for binding_id in root_bindings:
            if binding_id not in package_bindings:
                self.error(
                    project / "bindings_v2.json", f"missing resource for binding {binding_id}"
                )
            else:
                self.validate_binding_resource(
                    project / "bindings_v2.json",
                    root_bindings[binding_id],
                    package_resources[binding_id],
                )

        entry_points = data["entry-points.json"].get("entryPoints", [])  # type: ignore[union-attr]
        package_eps = {ep.get("id"): ep for ep in entry_points}
        expected_schemas = self.expected_entry_point_schemas(process)
        for start in [c for c in list(process) if local(c.tag) == "startEvent"]:
            ep = start.find(f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}entryPointId")
            if ep is None:
                continue
            ep_id = ep.attrib.get("value")
            file_path = f"/content/{bpmn_name}#{start.attrib.get('id')}"
            if ep_id not in package_eps:
                self.error(project / "entry-points.json", f"missing entry point {ep_id}")
            elif package_eps[ep_id].get("filePath") != file_path:
                self.error(project / "entry-points.json", f"entry point {ep_id} has wrong filePath")
            elif ep_id in expected_schemas:
                expected_input, expected_output = expected_schemas[ep_id]
                actual = package_eps[ep_id]
                if actual.get("inputSchema") != expected_input:
                    self.error(
                        project / "entry-points.json",
                        f"entry point {ep_id} inputSchema differs from BPMN variables",
                    )
                if actual.get("outputSchema") != expected_output:
                    self.error(
                        project / "entry-points.json",
                        f"entry point {ep_id} outputSchema differs from BPMN variables",
                    )

        self.validate_intsvc_package_enrichment(
            project / "bindings_v2.json", root, root_bindings, package_resources
        )

    def expected_entry_point_schemas(
        self, process: ET.Element
    ) -> dict[str, tuple[dict[str, object], dict[str, object]]]:
        root_variables = process.find(f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}variables")
        inputs_by_start: dict[str, dict[str, object]] = {}
        outputs: dict[str, object] = {}
        event_start_ids = {
            start.attrib["id"]
            for start in [c for c in list(process) if local(c.tag) == "startEvent"]
            if start.find(f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}event") is not None
            and "id" in start.attrib
        }
        if root_variables is not None:
            for variable in list(root_variables):
                name = variable.attrib.get("name")
                if not name:
                    continue
                schema = self.variable_schema(variable)
                element_id = variable.attrib.get("elementId")
                if local(variable.tag) == "input" and element_id:
                    inputs_by_start.setdefault(element_id, {})[name] = schema
                elif (
                    local(variable.tag) == "inputOutput"
                    and element_id
                    and element_id not in event_start_ids
                ):
                    inputs_by_start.setdefault(element_id, {})[name] = schema
                elif local(variable.tag) == "output":
                    outputs[name] = schema

        expected: dict[str, tuple[dict[str, object], dict[str, object]]] = {}
        for start in [c for c in list(process) if local(c.tag) == "startEvent"]:
            ep = start.find(f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}entryPointId")
            if ep is None or not ep.attrib.get("value"):
                continue
            expected[ep.attrib["value"]] = (
                {"type": "object", "properties": inputs_by_start.get(start.attrib["id"], {})},
                {"type": "object", "properties": outputs},
            )
        return expected

    def variable_schema(self, variable: ET.Element) -> dict[str, object]:
        var_type = variable.attrib.get("type", "string")
        if var_type == "jsonSchema":
            try:
                schema = json.loads(variable.text or "{}")
            except json.JSONDecodeError:
                return {"type": "object"}
            if isinstance(schema, dict):
                schema.pop("$schema", None)
                return schema
            return {"type": "object"}

        type_map = {
            "boolean": "boolean",
            "integer": "integer",
            "number": "number",
            "array": "array",
            "object": "object",
            "json": "object",
            "string": "string",
        }
        return {"type": type_map.get(var_type, "string")}

    def validate_binding_resource(
        self, path: Path, binding: ET.Element, resource: dict[str, object]
    ) -> None:
        binding_id = binding.attrib.get("id")
        expected_kind = binding.attrib.get("type")
        if resource.get("name") != binding.attrib.get("name"):
            self.error(path, f"resource {binding_id} name differs from BPMN binding")
        if expected_kind and resource.get("kind") != expected_kind:
            self.error(path, f"resource {binding_id} kind differs from BPMN binding")
        if binding.attrib.get("resourceKey") and resource.get("resourceKey") != binding.attrib.get(
            "resourceKey"
        ):
            self.error(path, f"resource {binding_id} resourceKey differs from BPMN binding")
        if binding.attrib.get("resource") and resource.get("resource") != binding.attrib.get(
            "resource"
        ):
            self.error(path, f"resource {binding_id} resource differs from BPMN binding")
        if binding.attrib.get("resourceSubType") and resource.get(
            "resourceSubType"
        ) != binding.attrib.get("resourceSubType"):
            self.error(path, f"resource {binding_id} resourceSubType differs from binding")
        if binding.attrib.get("propertyAttribute") and resource.get(
            "propertyAttribute"
        ) != binding.attrib.get("propertyAttribute"):
            self.error(path, f"resource {binding_id} propertyAttribute differs from binding")

        metadata = resource.get("metadata")
        if not isinstance(metadata, dict):
            self.error(path, f"resource {binding_id} metadata must be an object")
            return
        if metadata.get("BindingsVersion") != "v1":
            self.error(path, f"resource {binding_id} metadata.BindingsVersion must be v1")
        if metadata.get("DisplayLabel") != binding.attrib.get("name"):
            self.error(path, f"resource {binding_id} metadata.DisplayLabel differs from binding")

        expected_subtype = binding.attrib.get("resourceSubType") or binding.attrib.get("type")
        if metadata.get("SubType") != expected_subtype:
            self.error(path, f"resource {binding_id} metadata.SubType differs from binding")

    def validate_intsvc_package_enrichment(
        self,
        path: Path,
        root: ET.Element,
        bindings: dict[str, ET.Element],
        package_resources: dict[object, dict[str, object]],
    ) -> None:
        for elem in root.iter():
            if ns(elem.tag) != UIPATH_NS or local(elem.tag) not in {"activity", "event"}:
                continue
            type_elem = elem.find(f"{{{UIPATH_NS}}}type")
            service_type = type_elem.attrib.get("value") if type_elem is not None else ""
            if not service_type.startswith("Intsvc."):
                continue

            context = elem.find(f"{{{UIPATH_NS}}}context")
            if context is None:
                self.error(path, f"{service_type} missing context")
                continue
            context_inputs = {
                child.attrib.get("name"): child.attrib.get("value", "")
                for child in list(context)
                if local(child.tag) == "input"
            }
            connector_key = context_inputs.get("connectorKey")
            for name, value in context_inputs.items():
                binding_id = self.binding_expression_id(value)
                if not binding_id:
                    continue
                binding = bindings.get(binding_id)
                resource = package_resources.get(binding_id)
                if binding is None or resource is None:
                    continue
                metadata = resource.get("metadata")
                if not isinstance(metadata, dict):
                    continue
                if name in {"connection", "trigger"} and connector_key:
                    if metadata.get("Connector") != connector_key:
                        self.error(
                            path,
                            f"{service_type} {name} resource {binding_id} connector metadata differs",
                        )
                    if metadata.get("SolutionsSupport") != "Required":
                        self.error(
                            path,
                            f"{service_type} {name} resource {binding_id} must require solutions support",
                        )
                if binding.attrib.get("propertyAttribute") and name not in {
                    "connection",
                    "trigger",
                }:
                    parent_id = self.binding_expression_id(context_inputs.get("trigger", ""))
                    parent = package_resources.get(parent_id)
                    expected_parent = (
                        parent.get("resourceKey") if isinstance(parent, dict) else None
                    )
                    if expected_parent and metadata.get("ParentResourceKey") != expected_parent:
                        self.error(
                            path,
                            f"{service_type} property resource {binding_id} has wrong parent key",
                        )

            if (
                service_type in {"Intsvc.ActivityExecution", "Intsvc.AsyncExecution"}
                and elem.find(f"{{{UIPATH_NS}}}inputSchema") is None
            ):
                self.error(path, f"{service_type} missing generated inputSchema")

    def binding_expression_id(self, value: str) -> str | None:
        match = re.fullmatch(r"=bindings\.([A-Za-z0-9_]+)", value)
        return match.group(1) if match else None


if __name__ == "__main__":
    sys.exit(Validator().validate())
