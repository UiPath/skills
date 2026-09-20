#!/usr/bin/env python3
"""BillingDiscrepancyDetector (BPMN): detector / bindings / advisory checks.

Ported from Flow `multi_node/billing_discrepancy_detector/`: same scenario
(two independent Data Service reads -- BillingDisputeERP and
BillingDisputeCRM -- fanned out from the trigger/start and rejoined at a
merge/join before an overcharge computation), same three graded scripts
(`check_billing_discrepancy_detector.py`, `_shared/check_bindings_no_stubs.py`,
`_shared/advisory_billing_discrepancy_detector.py`), collapsed here into ONE
module with a `detector` / `bindings` / `advisory` dispatch (per
PORTING-BRIEF: "no new shared utility module" for this batch) so the three
YAML criteria share one script, invoked as:

    check_billing_discrepancy_detector.py detector    (live; weight 5.0)
    check_billing_discrepancy_detector.py bindings     (advisory; weight 1.0)
    check_billing_discrepancy_detector.py advisory     (advisory; weight 1.0)

Translated from a JSON node/edge walk to an XML walk over the registry-driven
`Intsvc.ActivityExecution` connector shell (registry-workflow.md §3-4) and the
BPMN live-debug surface (`_shared/bpmn_live.py`, LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`).

Assertion map (Flow -> BPMN):
  F check_billing_discrepancy_detector.py:42       assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
                                                    -> detector(): query_entity_nodes() non-empty
  F check_billing_discrepancy_detector.py:43       assert_flow_has_node_type(["core.logic.merge"])
                                                    -> detector(): find_join_gateways() non-empty
  F check_billing_discrepancy_detector.py:46       run_debug(inputs=INPUTS, timeout=240)
                                                    -> detector(): LIVE-ADDENDUM canonical pattern (ephemeral
                                                       solution init + import + sha256 pin + bpmn_live.run_debug +
                                                       debug-instance variables-all/incidents)
  F check_billing_discrepancy_detector.py:48-51    assert_output_value(payload, 1610/1/"MCS-2026-04872"/"Enterprise")
                                                    -> detector(): assert_output_value() over collect_output_leaves()
                                                       (root scope Globals + every element's Outputs, per
                                                       LIVE-ADDENDUM: a root public output has read back null)
  F advisory_billing_discrepancy_detector.py:71-89 two entity-read nodes, one per entity (ERP/CRM)
                                                    -> advisory(): query_entity_nodes() + entity_of()
  F advisory_billing_discrepancy_detector.py:91-101 exactly one merge, bpmn:ParallelGateway join
                                                    -> advisory(): find_join_gateways() (exactly one gateway with
                                                       >=2 incoming flows)
  F advisory_billing_discrepancy_detector.py:102-107 merge fed by >=2 distinct sources, continues downstream
                                                    -> advisory(): distinct incoming sourceRefs + outgoing flow check
  F advisory_billing_discrepancy_detector.py:108-110 fork exists (some node has >=2 outgoing edges)
                                                    -> advisory(): has_fork() (generic -- not pinned to a gateway
                                                       type, matching Flow's own generic node-degree check)
  F advisory_billing_discrepancy_detector.py:112-144 the two queries are MUTUALLY UNREACHABLE, both reachable
                                                       from the (single) trigger
                                                    -> advisory(): graph.reachable()/reaches_blocked() -- an F use
                                                       of `_shared/graph.py` `reaches`, per PORTING-BRIEF, because
                                                       Flow asserts this unreachability itself
  F advisory_billing_discrepancy_detector.py:146-151 both filters computed, each from its own input
                                                       (ERP<-invoiceNumber, CRM<-accountNumber)
                                                    -> advisory(): reads_field() over the variable-derivation graph
  F advisory_billing_discrepancy_detector.py:153-160 no answer literal (1610/2590/4200/Enterprise)
                                                    -> advisory(): carries_literal() (scoped to bpmn:process,
                                                       excluding bpmndi diagram coordinates)
  F advisory_billing_discrepancy_detector.py:162-173 declared contract: in-globals present, out-globals present
                                                       with the contract's type
                                                    -> advisory(): declared_id() presence + declared type checks
  F advisory_billing_discrepancy_detector.py:175-195 each output sourced from its own side (tier<-CRM,
                                                       matchedInvoiceNumber<-ERP, both numbers<-ERP)
                                                    -> advisory(): sourced_from() over the variable-derivation graph
  F advisory_billing_discrepancy_detector.py:197-198 each read resolves to the tenant it is pointed at
                                                       (connection/folder PAIR of distinct real uuids)
                                                    -> advisory(): assert_connection_resolves() over the declared
                                                       <uipath:bindings> block
  F check_bindings_no_stubs.py:91-142              bindings*.json Connection resources are non-stub, and a
                                                       connector node without one fails
                                                    -> bindings(): packed bindings_v2.json Connection resources
                                                       (mirrors e2e/customer_escalation_triage/
                                                       check_customer_escalation_package.py)
  I  locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                                    -> bpmn_check.find_bpmn_file()/parse_bpmn()/resolve_project()
  I  ephemeral solution init + `solution projects import` + sha256 pin of the imported bytes -- `bpmn debug`
     runs against an imported project, unlike `flow debug`, which runs directly against the discovered project
                                                    -> LIVE-ADDENDUM canonical pattern (mirrors
                                                       e2e/jira_get_issue/_shared/check_jira_get_issue.py)
  I  `uip maestro bpmn pack` + zip read of bindings_v2.json (BPMN has no bare generated bindings.json outside a
     pack/refresh -- registry-workflow.md §4)
                                                    -> bindings(): mirrors check_customer_escalation_package.py
  T  curated|generic entity-CRUD objectName classification (BATCH1-ADDENDUM)
                                                    -> query_entity_nodes()
  T  transitive variable derivation through BPMN.Variables copy tasks (Grading contract's allowed T list)
                                                    -> build_variable_graph()/trace() (var-id graph, name-matched,
                                                       not node-id/hop-bounded like Flow's $vars.<node>.output)
  DROPPED  require_no_private_connector_values / require_sequence_integrity / require_di_for_visible_elements
           (not in Flow; the `bpmn validate` criterion covers structure)

No native Data Fabric shape exists on the BPMN side of this port
(BATCH1-ADDENDUM: "Build this with the UiPath Data Service Integration Service
connector... for every entity operation" -- BPMN has no `core.datafabric.*`
analogue), so `entity_reads`'s NATIVE_READ branch from Flow's
advisory_flow_utils has no BPMN carrier and is not ported.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared import bpmn_live  # noqa: E402
from _shared import graph  # noqa: E402
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    find_bpmn_file,
    parse_bpmn,
    resolve_project,
)
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    get_ci,
    incident_records,
    payload_data,
    root_scope,
    run_cli,
    sha256,
)

NAME_HINT = "BillingDiscrepancyDetector"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
# Query Entity Records curated/preview spellings (BATCH1-ADDENDUM).
QUERY_OBJECT_NAMES = {"queryentityrecordscurated", "queryentityrecords_v3"}
ERP = "BillingDisputeERP"
CRM = "BillingDisputeCRM"
FORBIDDEN_LITERALS = ["1610", "2590", "4200", "Enterprise"]
OUT_CONTRACT = {
    "totalOvercharge": "number",
    "discrepancyCount": "number",
    "matchedInvoiceNumber": "string",
    "accountTier": "string",
}
IN_CONTRACT = [
    "invoiceNumber",
    "accountNumber",
    "disputedLineNumber",
    "disputedUnitPrice",
    "disputedQuantity",
]

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STUB_UUID_RE = re.compile(r"^0{8}-0{4}-0{4}-0{4}-")
VAR_REF = re.compile(r"vars\.([A-Za-z_][\w]*)")


def is_real_uuid(value) -> bool:
    rendered = str(value or "").strip()
    return bool(UUID_RE.fullmatch(rendered)) and not STUB_UUID_RE.match(rendered)


# ── connector-activity XML helpers (BATCH1-ADDENDUM shapes) ──────────────────


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def activity_root(task: ET.Element) -> ET.Element | None:
    return task.find(".//uipath:activity", NS)


def all_inputs(task: ET.Element) -> list[ET.Element]:
    root = activity_root(task)
    if root is None:
        return []
    return root.findall(".//uipath:input", NS)


def input_val(inp: ET.Element) -> str:
    return inp.attrib.get("value") or (inp.text or "")


def context_value(task: ET.Element, name: str) -> str:
    for inp in all_inputs(task):
        if inp.attrib.get("name") == name:
            return input_val(inp)
    return ""


def query_entity_nodes(root: ET.Element) -> list[ET.Element]:
    """Every sendTask carrying a Query Entity Records op, curated OR generic."""
    nodes = []
    for task in elements(root, "sendTask"):
        if not has_type(task, ACTIVITY_TYPE):
            continue
        if connector_context(task).get("connectorKey") != CONNECTOR_KEY:
            continue
        object_name_l = context_value(task, "objectName").strip().lower()
        operation_l = context_value(task, "operation").strip().lower()
        method_u = context_value(task, "method").strip().upper()
        is_curated = object_name_l in QUERY_OBJECT_NAMES
        is_generic = object_name_l in {ERP.lower(), CRM.lower()} and (
            operation_l in ("list", "retrieve") or method_u == "GET"
        )
        if is_curated or is_generic:
            nodes.append(task)
    return nodes


def entity_of(task: ET.Element) -> str | None:
    """The entity a query node addresses (BATCH1-ADDENDUM: any input value or
    the context path -- the skill does not pin where entityName lands)."""
    path_value = context_value(task, "path").lower()
    input_values = {input_val(inp).strip().lower() for inp in all_inputs(task)}
    matches = [
        entity
        for entity in (ERP, CRM)
        if entity.lower() in input_values or entity.lower() in path_value
    ]
    return matches[0] if len(matches) == 1 else None


def find_join_gateways(root: ET.Element) -> list[tuple[ET.Element, list[ET.Element]]]:
    """(gateway, incoming flows) for every bpmn:parallelGateway with >=2 incoming."""
    flows = elements(root, "sequenceFlow")

    def in_flows(node_id: str) -> list[ET.Element]:
        return [f for f in flows if attr(f, "targetRef") == node_id]

    return [
        (gw, in_flows(attr(gw, "id")))
        for gw in elements(root, "parallelGateway")
        if len(in_flows(attr(gw, "id"))) >= 2
    ]


def has_fork(root: ET.Element) -> bool:
    """Any node with >=2 outgoing sequence flows (Flow's own generic check --
    not pinned to a gateway type)."""
    counts = Counter(attr(f, "sourceRef") for f in elements(root, "sequenceFlow"))
    return any(count >= 2 for count in counts.values())


def reaches_blocked(root: ET.Element, source: str, target: str, blocked: str) -> bool:
    return target in graph.reachable(root, source, blocked={blocked})


# ── variable-derivation graph (var id -> name, var id -> derives-from ids) ───


def build_variable_graph(root: ET.Element):
    """(name_by_id, derives_from, var_written_by).

    `name_by_id` comes from every declared `<uipath:variables>` entry
    (input/inputOutput/output). `derives_from`/`var_written_by` come from
    every `<uipath:output var="..." source="...">` anywhere in the document
    (a connector activity's own output, or a BPMN.Variables mapping's copy) --
    the T translation of Flow's node-id `$vars.<node>.output` dependency graph
    onto BPMN's var-id addressing.
    """
    name_by_id: dict[str, str] = {}
    for var in root.findall(".//uipath:variables/*", NS):
        var_id = var.attrib.get("id")
        name = var.attrib.get("name")
        if var_id and name:
            name_by_id[var_id] = name.strip().lower()

    owner_tags = {
        f"{{{graph.BPMN_NS}}}{tag}"
        for tag in (
            "startEvent",
            "endEvent",
            "task",
            "sendTask",
            "receiveTask",
            "serviceTask",
            "scriptTask",
            "userTask",
            "businessRuleTask",
            "subProcess",
            "callActivity",
        )
    }
    parents = graph.parent_map(root)

    def owner_of(element: ET.Element) -> str | None:
        node = element
        while node in parents:
            node = parents[node]
            if node.tag in owner_tags and node.attrib.get("id"):
                return node.attrib["id"]
        return None

    derives_from: dict[str, set[str]] = defaultdict(set)
    var_written_by: dict[str, set[str]] = defaultdict(set)
    for out in root.iter(f"{{{NS['uipath']}}}output"):
        var_id = out.attrib.get("var")
        if not var_id:
            continue
        owner = owner_of(out)
        if owner:
            var_written_by[var_id].add(owner)
        derives_from[var_id].update(VAR_REF.findall(out.attrib.get("source") or ""))
    return name_by_id, derives_from, var_written_by


def trace(start_ids, derives_from, predicate) -> bool:
    seen: set[str] = set()
    stack = list(start_ids)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if predicate(current):
            return True
        stack.extend(derives_from.get(current, ()))
    return False


def reads_field(task: ET.Element, field_lower: str, name_by_id, derives_from) -> bool:
    refs: set[str] = set()
    for inp in all_inputs(task):
        refs.update(VAR_REF.findall(input_val(inp)))
    return trace(refs, derives_from, lambda v: name_by_id.get(v) == field_lower)


def declared_id(root: ET.Element, tag: str, name_lower: str) -> str | None:
    for var in root.findall(f".//uipath:variables/uipath:{tag}", NS):
        if (var.attrib.get("name") or "").strip().lower() == name_lower:
            return var.attrib.get("id")
    return None


def declared_type(root: ET.Element, tag: str, var_id: str) -> str | None:
    for var in root.findall(f".//uipath:variables/uipath:{tag}", NS):
        if var.attrib.get("id") == var_id:
            return var.attrib.get("type")
    return None


def sourced_from(root, output_name, task_id, derives_from, var_written_by):
    out_id = declared_id(root, "output", output_name.lower())
    if not out_id:
        return False, None
    return trace({out_id}, derives_from, lambda v: task_id in var_written_by.get(v, set())), out_id


def carries_literal(process_el: ET.Element, forbidden: str) -> bool:
    """Search only the process subtree (excludes bpmndi diagram coordinates,
    which can coincidentally collide with a small forbidden number)."""
    token = re.compile(rf"(?<![\w-]){re.escape(forbidden)}(?![\w-])")
    for el in process_el.iter():
        for value in el.attrib.values():
            if token.search(str(value)):
                return True
        if el.text and token.search(el.text):
            return True
    return False


def declared_bindings(root: ET.Element) -> dict[str, ET.Element]:
    return {
        b.attrib.get("id"): b
        for b in root.findall(".//uipath:bindings/uipath:binding", NS)
        if b.attrib.get("id")
    }


def resolve_binding_ref(bindings_by_id: dict[str, ET.Element], ref: str) -> ET.Element | None:
    match = re.fullmatch(r"=bindings\.([\w-]+)", (ref or "").strip())
    return bindings_by_id.get(match.group(1)) if match else None


def assert_connection_resolves(task: ET.Element, label: str, bindings_by_id) -> str:
    """F advisory_billing_discrepancy_detector.py:197-198: connection/folder
    PAIR of distinct real uuids -- the connector-shape half of
    `assert_read_resolves` (the native half has no BPMN carrier, see module
    docstring)."""
    connection_ref = context_value(task, "connection")
    conn_binding = resolve_binding_ref(bindings_by_id, connection_ref)
    if conn_binding is None:
        fail(
            f"the {label} query's context 'connection' is {connection_ref!r}, which does not "
            "resolve to a declared <uipath:binding resource=\"Connection\">"
        )
    conn_value = conn_binding.attrib.get("default") or conn_binding.attrib.get("resourceKey")
    if not is_real_uuid(conn_value):
        fail(
            f"the {label} query's connection binding {conn_binding.attrib.get('id')!r} "
            f"default/resourceKey is {conn_value!r}, not a real connection id"
        )

    folder_ref = context_value(task, "folderKey")
    folder_binding = resolve_binding_ref(bindings_by_id, folder_ref)
    if folder_binding is None:
        fail(
            f"the {label} query's context 'folderKey' is {folder_ref!r}, which does not resolve "
            "to a declared <uipath:binding> (a folder-scoped connector activity needs a paired "
            "folder binding -- registry-workflow.md §4)"
        )
    folder_value = folder_binding.attrib.get("default") or folder_binding.attrib.get("resourceKey")
    if not is_real_uuid(folder_value):
        fail(
            f"the {label} query's folder binding {folder_binding.attrib.get('id')!r} "
            f"default/resourceKey is {folder_value!r}, not a real folder id"
        )
    if conn_value == folder_value:
        fail(
            f"the {label} query's connection and folder bindings both resolve to the SAME uuid "
            f"({conn_value}) -- the folder binding needs the connection's FOLDER key, not its id"
        )
    return f"connection={conn_value[:8]}... folder={folder_value[:8]}..."


# ── advisory: STRUCTURAL shape (weight 1.0, pass_threshold 0.0) ─────────────


def advisory() -> None:
    path, root = parse_bpmn(NAME_HINT)
    process = root.find("bpmn:process", NS)
    if process is None:
        fail(f"{path}: no bpmn:process element found")

    # 1. two entity-read nodes, one per entity.
    nodes = query_entity_nodes(root)
    if len(nodes) != 2:
        fail(
            f"expected exactly TWO Data Service query-entity-records connector nodes "
            f"(ERP + CRM), found {len(nodes)}"
        )
    by_entity: dict[str, ET.Element] = {}
    for task in nodes:
        entity = entity_of(task)
        if entity is None:
            fail(
                f"query node {attr(task, 'id')!r} does not clearly address exactly one of "
                f"{ERP!r}/{CRM!r} in any input value or context path"
            )
        if entity in by_entity:
            fail(f"both query nodes address {entity!r}; the scenario needs one {ERP} and one {CRM}")
        by_entity[entity] = task
    missing = [e for e in (ERP, CRM) if e not in by_entity]
    if missing:
        fail(f"no query node addresses {missing}; entities queried: {sorted(by_entity)}")
    erp, crm = by_entity[ERP], by_entity[CRM]
    erp_id, crm_id = attr(erp, "id"), attr(crm, "id")

    # 2. exactly one join, a real join, continuing downstream; a fork exists.
    joins = find_join_gateways(root)
    if len(joins) != 1:
        fail(
            f"expected exactly one bpmn:parallelGateway acting as a join (>=2 incoming flows), "
            f"found {len(joins)}"
        )
    join_gw, incoming = joins[0]
    join_id = attr(join_gw, "id")
    sources = sorted({attr(f, "sourceRef") for f in incoming})
    if len(sources) < 2:
        fail(f"join gateway {join_id!r} is fed by {len(sources)} distinct source(s) ({sources})")
    if not [f for f in elements(root, "sequenceFlow") if attr(f, "sourceRef") == join_id]:
        fail(f"join gateway {join_id!r} has no outgoing sequence flow; the joined path must continue")
    if not has_fork(root):
        fail("no fork found: no node has >=2 outgoing sequence flows, so nothing fans out before the join")

    # 3. the two queries are on MUTUALLY UNREACHABLE branches, both reachable
    #    from the (single) start event.
    if reaches_blocked(root, erp_id, crm_id, join_id) or reaches_blocked(root, crm_id, erp_id, join_id):
        first, second = (
            (erp_id, crm_id) if reaches_blocked(root, erp_id, crm_id, join_id) else (crm_id, erp_id)
        )
        fail(
            f"{second!r} is downstream of {first!r} -- the two lookups are CHAINED with a join "
            "bolted on, not a fan-out from the start event"
        )
    starts = elements(root, "startEvent")
    if len(starts) != 1:
        fail(f"a process has exactly one root start event, found {len(starts)}")
    start_id = attr(starts[0], "id")
    reachable_from_start = graph.reachable(root, start_id)
    for node_id in (erp_id, crm_id):
        if node_id not in reachable_from_start:
            fail(f"query node {node_id!r} is not reachable from the start event {start_id!r}")

    # 4. both filters computed, each from its own input.
    name_by_id, derives_from, var_written_by = build_variable_graph(root)
    for label, task, field in ((ERP, erp, "invoicenumber"), (CRM, crm, "accountnumber")):
        if not reads_field(task, field, name_by_id, derives_from):
            fail(
                f"the {label} query node does not reference the {field} input (directly, or "
                "transitively through a BPMN.Variables copy task) in any of its inputs"
            )

    # 5. none of the answers is written in.
    for bad in FORBIDDEN_LITERALS:
        if carries_literal(process, bad):
            fail(
                f"the process carries the literal {bad!r}. Every one of the answers "
                f"({', '.join(FORBIDDEN_LITERALS)}) has to come from the tenant"
            )

    # 6. the declared contract, and where each output comes from.
    for name in IN_CONTRACT:
        if declared_id(root, "input", name.lower()) is None:
            fail(f"the process declares no public input named {name!r}")
    for name, want in OUT_CONTRACT.items():
        out_id = declared_id(root, "output", name.lower())
        if out_id is None:
            fail(f"the process declares no public output named {name!r}")
        got = declared_type(root, "output", out_id)
        if got != want:
            fail(f"output {name!r} is declared type {got!r}; the contract asks for {want!r}")

    ok, out_id = sourced_from(root, "accountTier", crm_id, derives_from, var_written_by)
    if not ok:
        fail(f"output 'accountTier' (var {out_id!r}) does not derive from {crm_id!r} -- the tier comes from {CRM}")
    ok, out_id = sourced_from(root, "matchedInvoiceNumber", erp_id, derives_from, var_written_by)
    if not ok:
        fail(
            f"output 'matchedInvoiceNumber' (var {out_id!r}) does not derive from {erp_id!r} -- "
            f"the matched invoice comes from {ERP}"
        )
    for name in ("totalOvercharge", "discrepancyCount"):
        ok, out_id = sourced_from(root, name, erp_id, derives_from, var_written_by)
        if not ok:
            fail(
                f"output {name!r} (var {out_id!r}) does not derive from {erp_id!r} -- the contracted "
                f"amount it is computed from lives in the {ERP} rows"
            )

    # 7. each read resolves to the tenant it is pointed at.
    bindings_by_id = declared_bindings(root)
    resolutions = [
        assert_connection_resolves(task, label, bindings_by_id)
        for label, task in ((ERP, erp), (CRM, crm))
    ]

    print(
        f"OK: {path} -- {ERP}={erp_id!r} and {CRM}={crm_id!r} on mutually unreachable branches from "
        f"{start_id!r}, converging on parallelGateway join {join_id!r} ({len(sources)} sources, "
        "continues downstream); both filters computed from their own inputs; no answer literals; "
        f"outputs {sorted(OUT_CONTRACT)} each sourced from its own side; {'; '.join(resolutions)}"
    )


# ── bindings: no-stub advisory (weight 1.0, pass_threshold 0.0) ─────────────


def bindings() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    root = ET.parse(bpmn_path).getroot()
    needs_connection = any(connector_context(node).get("connectorKey") for node in root.iter())

    project_dir = resolve_project(os.path.basename(bpmn_path), exclude_under=[LIVE_RUN_DIR])
    with tempfile.TemporaryDirectory(prefix="billing-pack-") as out_dir:
        packed = subprocess.run(
            ["uip", "maestro", "bpmn", "pack", str(project_dir), out_dir, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if packed.returncode != 0:
            fail(f"uip maestro bpmn pack failed (exit {packed.returncode}): {packed.stdout}\n{packed.stderr}")
        try:
            payload = bpmn_live.parse_json_output(packed.stdout, "pack")
        except CheckFailure as error:
            fail(str(error))
        if not isinstance(payload, dict) or str(payload.get("Result", "")).casefold() != "success":
            fail(f"pack JSON did not report Success: {payload}")

        packages = list(Path(out_dir).glob("*.nupkg"))
        if len(packages) != 1:
            fail(f"expected exactly one .nupkg, found: {[p.name for p in packages]}")
        with zipfile.ZipFile(packages[0]) as archive:
            by_basename = {Path(name).name: name for name in archive.namelist()}
            if "bindings_v2.json" not in by_basename:
                if needs_connection:
                    fail(
                        "packed archive has no bindings_v2.json, but the process carries a "
                        "connector node that needs a connection binding"
                    )
                print("no bindings_v2.json, and no connector node that needs one")
                return
            bindings_doc = json.loads(archive.read(by_basename["bindings_v2.json"]))

    resources = bindings_doc.get("resources")
    if not isinstance(resources, list):
        fail(f"bindings_v2.json has no resources array: {bindings_doc}")
    connections = [r for r in resources if isinstance(r, dict) and r.get("resource") == "Connection"]
    if not connections:
        if needs_connection:
            fail("bindings_v2.json declares no Connection resources, but the process carries a connector node")
        print("no Connection resources, and no connector node that needs one")
        return
    stubbed = [r.get("key") for r in connections if not is_real_uuid(r.get("key"))]
    if stubbed:
        fail(f"bindings_v2.json Connection keys must be real connection ids, not unresolved stubs: {stubbed}")
    print(f"{len(connections)} connection binding(s) in bindings_v2.json, all populated with non-stub values")


# ── detector: live run (weight 5.0) ─────────────────────────────────────────

INPUTS = {
    "invoiceNumber": "MCS-2026-04872",
    "accountNumber": "ACCT-98201-NE",
    "disputedLineNumber": 5,
    "disputedUnitPrice": 300,
    "disputedQuantity": 14,
}
EXPECTED_OUTPUTS = (1610, 1, "MCS-2026-04872", "Enterprise")

LIVE_RUN_DIR = Path("billing-discrepancy-detector-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

# Worst-case wall clock this checker's `detector` criterion can spend, priced
# the way _shared/test_criterion_budgets.py prices a run_debug(...) call: the
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480). The
# surrounding CLI steps (solution init/import, variables-all, incidents) are
# not priced by that guard, so their sum is added by hand here, mirroring
# e2e/jira_get_issue and multi_node/slack_weather_pipeline:
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (600) does not cover this; raised to 1050 in
# billing_discrepancy_detector.yaml (documented deviation, sanctioned by
# LIVE-ADDENDUM: the budget is a property of the CLI surface, not of what is
# graded).


def _leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from _leaves(v)
    elif value is not None:
        yield value


def collect_output_leaves(variables_data) -> list:
    """Value leaves of the root scope's Globals AND every element's Outputs.

    A root public output has been observed to read back null even when
    correctly mapped (LIVE-ADDENDUM), so the search is not scoped to one
    declared output variable -- mirrors Flow's own assert_output_value(),
    which flattens the whole debug payload's declared outputs.
    """
    leaves = list(_leaves(get_ci(root_scope(variables_data), "Globals", {})))
    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            leaves.extend(_leaves(get_ci(element, "Outputs", {})))
    return leaves


def assert_output_value(leaves: list, expected) -> None:
    """F check_billing_discrepancy_detector.py:48-51 (assert_output_value):
    numeric exact match; string case-insensitive substring."""
    for value in leaves:
        if value == expected:
            return
        if isinstance(expected, str) and isinstance(value, str) and expected.lower() in value.lower():
            return
    raise CheckFailure(f"no output equals expected {expected!r}; outputs: {str(leaves)[:1000]}")


def detector() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    root = ET.parse(bpmn_path).getroot()

    if len(query_entity_nodes(root)) < 2:
        fail(
            "expected at least two Data Service query-entity-records connector nodes "
            f"(found {len(query_entity_nodes(root))})"
        )
    if not find_join_gateways(root):
        fail("no bpmn:parallelGateway acts as a join (>=2 incoming flows)")

    project_dir = resolve_project(os.path.basename(bpmn_path), exclude_under=[LIVE_RUN_DIR])
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "BillingDiscrepancyDetectorLiveEval"
    initialized = run_cli(["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT)
    payload_data(initialized, "initialize ephemeral solution")
    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        raise CheckFailure(
            f"solution init produced {len(solution_files)} .uipx files in {solution_dir}, expected exactly one"
        )
    solution_file = solution_files[0]
    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(project_dir.resolve()),
            "--solutionFile",
            str(solution_file),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / os.path.basename(bpmn_path)) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    print(f"debug inputs: {INPUTS}")
    debug_data, instance_id = bpmn_live.run_debug(imported_project, INPUTS, LIVE_RUN_DIR / "debug.log")
    print(f"OK: debug completed (instance {instance_id})")

    final_status = get_ci(debug_data, "FinalStatus")
    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    incidents_list = incident_records(incidents_data)

    if final_status not in COMPLETED_STATUSES:
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if incidents_list:
            detail.append(f"incidents: {json.dumps(incidents_list)[:1500]}")
        raise CheckFailure(f"final status was {final_status!r}" + ("; " + "; ".join(detail) if detail else ""))
    if incidents_list is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents_list:
        raise CheckFailure(f"unexpected incidents: {incidents_list}")
    print(f"OK: bpmn debug completed (FinalStatus={final_status}, no incidents)")

    leaves = collect_output_leaves(variables_data)
    for expected in EXPECTED_OUTPUTS:
        assert_output_value(leaves, expected)
    print("OK: overcharge=1610, count=1, invoice MCS-2026-04872, tier Enterprise")
    print("PASS: all BillingDiscrepancyDetector checks passed")


_MODES = {"detector": detector, "bindings": bindings, "advisory": advisory}


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "detector"
    handler = _MODES.get(mode)
    if handler is None:
        sys.exit(f"FAIL: unknown mode {mode!r}; expected one of {sorted(_MODES)}")
    handler()


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
