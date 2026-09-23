#!/usr/bin/env python3
"""BillingInvoiceLookup (BPMN): four modes, one per Flow checker script.

Ported from `uipath-maestro-flow/multi_node/billing_invoice_lookup/`:
`check_billing_invoice_lookup.py` (live 3x debug), `check_server_side_filter.py`
(advisory), `_shared/check_bindings_no_stubs.py` (advisory), and
`_shared/advisory_billing_invoice_lookup.py` (advisory structural gate). Kept
as ONE file with a mode-dispatch positional argument (`lookup` /
`server_side_filter` / `bindings` / `advisory`) per BATCH1/PORTING-BRIEF
instructions -- no new `_shared` module. The dispatch shape (module-level
functions + a DISPATCH dict keyed on `sys.argv[1]`) mirrors
`check_outlook_trigger_inbox.py`, and doubles as the entry point
`tests/_shared/test_criterion_budgets.py` prices per subcommand.

Assertion map (Flow -> BPMN):
  F check_billing_invoice_lookup.py:45   assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
                                          -> query_entity_nodes() non-empty (lookup)
  F check_billing_invoice_lookup.py:47-50 read_flow_input_vars()/var = in_vars[0]
                                          -> declared_input_names(root)[0] (lookup)
  F check_billing_invoice_lookup.py:52-58 CASES loop, run_debug(inputs=...), assert_output_value x2
                                          -> CASES loop, bpmn_live.run_debug(project, inputs, log, timeout=180)
                                             + assert_output_value() over output_leaves() (lookup)
  I                locate/parse .bpmn; ephemeral solution init + `solution projects
                    import` + sha256 pin; `bpmn debug` returns an instance id, not
                    inline variables; `debug-instance variables-all`/`incidents` reads
                    replace the single inline debug payload
                                          -> LIVE-ADDENDUM canonical live pattern
                                             (mirrors e2e/jira_get_issue/_shared/check_jira_get_issue.py) (lookup)
  T                curated|generic entity-CRUD classification; entity anywhere in
                    inputs/objectName/path; GETBYID/GET(List) equivalence
                    (BATCH1-ADDENDUM)         -> query_entity_nodes() / entity_ok() (all modes)

  F check_server_side_filter.py:65-80, advisory_flow_utils.has_filter/filters_server_side
                                          -> has_nonempty_filter() (server_side_filter)
                    DROPPED: the native core.datafabric.read branch -- BPMN has
                    no native Data Fabric node (BATCH1-ADDENDUM); only the
                    connector shape applies here.

  F _shared/check_bindings_no_stubs.py:45-47,67-80 is_real_key/UUID/STUB_UUID,
                    invalid_ids() over bindings[].resourceKey/default
                                          -> is_real_connection_key(), stubbed-key scan (bindings)
                    DROPPED: the "no bindings file needed" branch for a native
                    entity read -- this port always uses the connector, so a
                    Connection resource is always required (BATCH1-ADDENDUM).
                    I  bindings_v2.json is emitted only at PACK time for BPMN
                    (authoring leaves the connection as a symbolic
                    `=bindings.<id>` reference, unlike Flow's compiler, which
                    resolved it straight into the node) -> `uip maestro bpmn
                    pack` + zip read, modeled on
                    e2e/customer_escalation_triage/check_customer_escalation_package.py
                    (PORTING-BRIEF's pointer)

  F advisory_billing_invoice_lookup.py:64-67   exactly ONE entity-read node
                                          -> len(reads) != 1 check (advisory)
  F advisory_billing_invoice_lookup.py:71-74   no raw HTTP fallback
                                          -> no Intsvc.HttpExecution node check (advisory)
  F advisory_billing_invoice_lookup.py:76-79   entity slot carries ENTITY
                                          -> entity_ok() (advisory)
  F advisory_billing_invoice_lookup.py:82      filter COMPUTED from input, not constant
                                          -> filter_reference_ids() + derives_from(ref, {input_id}) (advisory)
                    T  does not pin the filter to one named column (Flow's
                    `column="invoiceNumber"`): no local Data Service connection
                    exists to `describe` the entity's real filter field name
                    (BATCH1-ADDENDUM), so any input at any depth that derives
                    from the declared input is accepted.
  F advisory_billing_invoice_lookup.py:85-96   canonical answer + raw test inputs
                    never appear as literals -> raw substring scan on the .bpmn
                    text (I: re-homed from Flow's `_authored_values` walk over
                    JSON to a whole-file text scan, matching this suite's own
                    convention in check_jira_get_issue.py's `JIRA_KEY not in raw`
                    / `issue_key not in raw` checks) (advisory)
  F advisory_billing_invoice_lookup.py:98-108  outputs declared with contract's
                    names AND types -> declared_outputs() (advisory)
  F advisory_billing_invoice_lookup.py:110-127 outputs READ FROM the query step
                    -> derives_from(output_id, query_out_vars) over the
                    var-source graph built from every `<uipath:output var=
                    source=>` in the document, T: transitive derivation through
                    BPMN.Variables copy tasks (BATCH1-ADDENDUM), extended here
                    to also follow a scriptTask's own `<bpmn:script>` CDATA
                    `vars.<id>` reads when its output's `source` starts with
                    `=result` (a script's return value cannot be traced through
                    `source=` alone -- see build_var_graph()) (advisory)
  F advisory_billing_invoice_lookup.py:130-141 `assert_read_resolves` -- SPLIT
                    across two artifact stages, since BPMN resolves a
                    connection binding in two steps Flow's compiler collapsed
                    into one:
                    (a) connection/folder DISTINCT, non-blank `default`
                    values -- fully visible in the raw authored .bpmn (the
                    registry-workflow.md §4 two-binding shape), so checked
                    here in `advisory` mode as connection_and_folder_distinct().
                    This directly ports the Flow assertion's failure mode
                    ("the two collapse into one binding... answering 401").
                    (b) the connection id is a REAL (non-stub) tenant uuid --
                    Flow's compiler baked the resolved connection straight into
                    the node's own `inputs.detail`; a hand-authored .bpmn keeps
                    it SYMBOLIC (`=bindings.<id>`) even when correct, so there
                    is no real id to inspect until pack time. Carried instead
                    by the `bindings` mode (packed bindings_v2.json), which is
                    where BPMN actually materializes a resolved connection
                    value. Note bindings_v2.json's `resources[]` never carries
                    a folder key at all -- "Only the ConnectionId binding
                    becomes a bindings_v2.json resource" (registry-workflow.md
                    §4) -- so the folder side of the distinctness check has no
                    packed carrier and stays authoring-time-only (a), not
                    duplicated in (b).
                    What IS checkable at the authoring stage -- that the
                    query's `connection` input is a `=bindings.<id>` reference
                    resolving to a declared `resource="Connection"` binding --
                    is asserted here
                    as `connection_binding_wired()`.
  DROPPED          require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / uniqueness rules beyond the
                    one Flow itself asserted -- not in Flow; `bpmn validate`
                    criterion covers structure.

No tenant re-read is performed outside the `lookup` mode's own live sequence,
matching Flow's own grader (the query result IS the tenant re-read).
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
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import (  # noqa: E402
    NS,
    all_node_values,
    context_inputs,
    context_value,
    elements,
    fail,
    find_bpmn_file,
    has_typed_uipath_extension,
    parse_bpmn,
    resolve_project,
)
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    get_ci,
    incident_records,
    payload_data,
    root_scope,
    run_cli,
    sha256,
)

NAME_HINT = "BillingInvoiceLookup"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "BillingDisputeERP"
QUERY_CURATED_OBJECTS = {"queryentityrecordscurated", "queryentityrecords_v3"}

EXPECTED_INVOICE = "MCS-2026-04872"
EXPECTED_LINE_COUNT = 8
CANONICAL = EXPECTED_INVOICE
# raw input form the caller might send -> human label for failure messages
# (verbatim from Flow's check_billing_invoice_lookup.py CASES).
CASES = [
    ("2026-04872", "missing MCS- prefix"),
    ("mcs-2026-04872", "wrong casing"),
    (" MCS-2026-04872", "leading whitespace"),
]
# The malformed forms the offline CASES above drive -- carried as a literal
# would let a lookup-table pass every case (advisory_billing_invoice_lookup.py).
RAW_INPUTS = ["2026-04872", "mcs-2026-04872"]

FILTER_INPUT_NAMES = {"queryexpression", "where", "filter", "filtergroup", "filtervariables"}

LIVE_RUN_DIR = Path("billing-invoice-lookup-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

# Worst-case wall clock, priced the way _shared/test_criterion_budgets.py
# prices a run_debug(...) call inside a static loop: bpmn_live.debug_budget(180)
# x 3 (the module-level CASES list) = 540s, which the guard multiplies
# automatically. The guard prices only run_debug calls; the surrounding CLI
# round trips run once (solution init, solution import) or three times
# (variables-all, incidents per case) and are added by hand here, the same way
# e2e/jira_get_issue/_shared/check_jira_get_issue.py documents its own
# arithmetic:
#   90 (solution init) + 180 (solution import)
#   + 3 x (180 debug + 120 variables-all + 120 incidents)
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60)
#   = 90 + 180 + 1260 + 60 = 1590
# billing_invoice_lookup.yaml raises this criterion's timeout from Flow's 1200
# to 1590 to cover it -- the LIVE-ADDENDUM-sanctioned deviation for the extra
# CLI round trips a `bpmn debug` sequence needs per case that
# `flow_check.run_debug`'s single inline call did not. The guard's own
# arithmetic only requires >= 540 + 60 = 600s, comfortably inside 1590.


# ── shared XML helpers (copied from check_df_smoke_query_filter.py /
#    check_df_contractregistry_crud_filters.py -- no new _shared module) ─────


def input_val(inp: ET.Element) -> str:
    return inp.attrib.get("value") or (inp.text or "")


def output_vars(task: ET.Element) -> list[str]:
    return [out.attrib["var"] for out in task.findall(".//uipath:output", NS) if out.attrib.get("var")]


def entity_ok(task: ET.Element) -> bool:
    """BATCH1-ADDENDUM: entity anywhere in path/query/body inputs or context path."""
    if context_value(task, "objectName").strip().lower() == ENTITY.lower():
        return True
    values = all_node_values(task) + [context_value(task, "path")]
    return any(v and ENTITY in v for v in values)


def query_entity_nodes(root: ET.Element) -> list[ET.Element]:
    """Curated OR generic entity-CRUD classification (BATCH1-ADDENDUM)."""
    nodes = []
    for task in elements(root, "sendTask"):
        if not has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        object_name = context_value(task, "objectName").strip().lower()
        operation = context_value(task, "operation").strip().lower()
        method = context_value(task, "method").strip().upper()
        is_curated = object_name in QUERY_CURATED_OBJECTS
        is_dynamic_list = object_name == ENTITY.lower() and (operation == "list" or method == "GET")
        if is_curated or is_dynamic_list:
            nodes.append(task)
    return nodes


def parse_json_maybe(value: str):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def find_saved_filter_trees(node, out: list) -> None:
    if isinstance(node, dict):
        sft = node.get("savedFilterTrees")
        if isinstance(sft, dict) and "queryExpression" in sft:
            out.append(sft["queryExpression"])
        for value in node.values():
            find_saved_filter_trees(value, out)
    elif isinstance(node, list):
        for item in node:
            find_saved_filter_trees(item, out)


def filter_leaves_from_tree(tree, leaves: list) -> None:
    if not isinstance(tree, dict):
        return
    leaves.extend(tree.get("filters") or [])
    for child in tree.get("groups") or []:
        filter_leaves_from_tree(child, leaves)


def structured_filter_leaves(parsed_json) -> list:
    trees: list = []
    find_saved_filter_trees(parsed_json, trees)
    leaves: list = []
    for tree in trees:
        filter_leaves_from_tree(tree, leaves)
    return leaves


# ── mode: lookup (F: check_billing_invoice_lookup.py) ────────────────────────


def _variable_children(root: ET.Element, tag: str) -> list[ET.Element]:
    variables = root.find(".//uipath:variables", NS)
    if variables is None:
        return []
    wanted = f"{{{NS['uipath']}}}{tag}"
    return [child for child in variables if child.tag == wanted]


def declared_input_names(root: ET.Element) -> list[str]:
    return [c.attrib.get("name") for c in _variable_children(root, "input") if c.attrib.get("name")]


def declared_outputs(root: ET.Element) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for c in _variable_children(root, "output"):
        name = c.attrib.get("name")
        if name:
            result[name] = (c.attrib.get("id", ""), c.attrib.get("type", ""))
    return result


def input_id_for_name(root: ET.Element, name: str) -> str | None:
    for c in _variable_children(root, "input"):
        if (c.attrib.get("name") or "").strip().lower() == name.lower():
            return c.attrib.get("id")
    return None


def _leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from _leaves(v)
    elif value is not None:
        yield value


def output_leaves(variables_data: object) -> list:
    """Value leaves of the root scope's Globals AND every element's Outputs.

    A root public output has read back null even when correctly mapped
    (LIVE-ADDENDUM), so the search is not scoped to one declared output
    variable -- mirrors check_jira_get_issue.py's collect_output_haystack, but
    keeps each leaf's native type so a numeric expectation is not spuriously
    matched by a digit embedded in an unrelated string (flow_check.assert_output_value's
    own reason for exact numeric equality, not substring, on numerics).
    """
    leaves = list(_leaves(get_ci(root_scope(variables_data), "Globals", {})))
    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            leaves.extend(_leaves(get_ci(element, "Outputs", {})))
    return leaves


def assert_output_value(leaves: list, expected) -> bool:
    """F: flow_check.assert_output_value -- exact-equal numerics, case-insensitive substring strings."""
    for v in leaves:
        if v == expected:
            return True
        if isinstance(expected, str) and isinstance(v, str) and expected.lower() in v.lower():
            return True
    return False


def lookup() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    if not query_entity_nodes(root):
        fail("bpmn does not reference a Data Service Query Entity Records connector node (Intsvc.ActivityExecution)")
    print(f"OK: bpmn references a Query Entity Records node against {ENTITY}")

    input_names = declared_input_names(root)
    if not input_names:
        fail("process declares no public uipath:input variable for the invoice number")
    var_name = input_names[0]

    project_dir = resolve_project(os.path.basename(bpmn_path), exclude_under=[LIVE_RUN_DIR])
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "BillingInvoiceLookupLiveEval"
    try:
        initialized = run_cli(["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT)
        payload_data(initialized, "initialize ephemeral solution")
        solution_files = sorted(solution_dir.glob("*.uipx"))
        if len(solution_files) != 1:
            raise CheckFailure(
                f"solution init produced {len(solution_files)} .uipx files in "
                f"{solution_dir}, expected exactly one"
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

        for raw_value, label in CASES:
            inputs = {var_name: raw_value}
            print(f"[{label}] debug inputs: {inputs}")
            debug_data, instance_id = bpmn_live.run_debug(
                imported_project,
                inputs,
                LIVE_RUN_DIR / f"debug-{label.replace(' ', '-')}.log",
                timeout=180,
            )
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
                raise CheckFailure(
                    f"[{label}] final status was {final_status!r}" + ("; " + "; ".join(detail) if detail else "")
                )
            if incidents_list is None:
                raise CheckFailure(f"[{label}] incidents response has an unknown shape: {incidents_data!r}")
            if incidents_list:
                raise CheckFailure(f"[{label}] unexpected incidents: {incidents_list}")

            leaves = output_leaves(variables_data)
            if not assert_output_value(leaves, EXPECTED_INVOICE):
                raise CheckFailure(f"[{label}] no output equals expected {EXPECTED_INVOICE!r}")
            if not assert_output_value(leaves, EXPECTED_LINE_COUNT):
                raise CheckFailure(f"[{label}] no output equals expected {EXPECTED_LINE_COUNT!r}")
            print(f"OK: [{label}] instance {instance_id} -> {EXPECTED_INVOICE}, {EXPECTED_LINE_COUNT} line items")
    except CheckFailure as error:
        fail(str(error))

    print(f"OK: all {len(CASES)} malformed forms normalized and queried correctly")


# ── mode: server_side_filter (F: check_server_side_filter.py) ────────────────


def has_nonempty_filter(task: ET.Element) -> bool:
    for inp in context_inputs(task):
        name = (inp.attrib.get("name") or "").strip().lower()
        value = input_val(inp)
        if name in FILTER_INPUT_NAMES and str(value).strip() not in ("", "{}", "[]"):
            return True
        parsed = parse_json_maybe(value)
        if parsed is not None and structured_filter_leaves(parsed):
            return True
    return False


def server_side_filter() -> None:
    path, root = parse_bpmn(NAME_HINT)
    nodes = query_entity_nodes(root)
    if not nodes:
        fail("no entity-read node (Data Service Query Entity Records connector activity)")
    unfiltered = [task.attrib.get("id") for task in nodes if not has_nonempty_filter(task)]
    if unfiltered:
        fail(
            f"no server-side filter on {', '.join(unfiltered)} -- entity fetched whole and "
            "filtered client-side; breaks silently past the page limit"
        )
    print(f"OK: {path} -- query filters server-side")


# ── mode: bindings (F: _shared/check_bindings_no_stubs.py) ───────────────────

UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STUB_UUID_PATTERN = re.compile(r"^0{8}-0{4}-0{4}-0{4}-")


def is_real_connection_key(value) -> bool:
    rendered = str(value or "").strip()
    return bool(UUID_PATTERN.fullmatch(rendered)) and not STUB_UUID_PATTERN.match(rendered)


def bindings() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    project_dir = resolve_project(os.path.basename(bpmn_path), exclude_under=[LIVE_RUN_DIR])
    with tempfile.TemporaryDirectory(prefix="bpmn-eval-pack-") as output_dir:
        result = subprocess.run(
            ["uip", "maestro", "bpmn", "pack", str(project_dir), output_dir, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=150,
        )
        if result.returncode != 0:
            fail(f"pack exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}")
        try:
            payload = bpmn_live.parse_json_output(result.stdout, "pack")
        except CheckFailure as exc:
            fail(str(exc))
        if not isinstance(payload, dict) or str(payload.get("Result", "")).casefold() != "success":
            fail(f"pack JSON did not report Success: {payload}")

        packages = list(Path(output_dir).glob("*.nupkg"))
        if len(packages) != 1:
            fail(f"expected exactly one .nupkg, found: {[p.name for p in packages]}")
        package = packages[0]
        if package.stat().st_size <= 0 or not zipfile.is_zipfile(package):
            fail(f"packed file is not a valid non-empty archive: {package.name}")

        with zipfile.ZipFile(package) as archive:
            by_basename = {Path(name).name: name for name in archive.namelist()}
            if "bindings_v2.json" not in by_basename:
                fail("packed archive has no bindings_v2.json")
            doc = json.loads(archive.read(by_basename["bindings_v2.json"]))

        resources = [
            r for r in (doc.get("resources") or []) if isinstance(r, dict) and str(r.get("resource") or "").lower() == "connection"
        ]
        # Flow's own check only requires non-empty + non-stub, never an exact
        # count (a connector port always needs >=1, unlike Flow's native-read
        # branch, which this port drops -- see module docstring).
        if not resources:
            fail("packed bindings_v2.json declares no Connection resources")
        stubbed = [r.get("key") for r in resources if not is_real_connection_key(r.get("key"))]
        if stubbed:
            fail(f"packed bindings_v2.json Connection keys must be real connection ids, not unresolved stubs: {stubbed}")
        print(f"OK: {len(resources)} connection binding(s) across bindings_v2.json, all non-stub")


# ── mode: advisory (F: _shared/advisory_billing_invoice_lookup.py) ───────────


def build_var_graph(root: ET.Element) -> tuple[dict[str, str], dict[str, set]]:
    """var_sources: var -> raw `source=` text, from every `<uipath:output var=
    source=>` in the document (mapping tasks and connector activity outputs
    alike -- T: transitive derivation through BPMN.Variables copy tasks,
    BATCH1-ADDENDUM). extra_refs supplements it for a scriptTask output whose
    `source` is opaque (`=result.response...`, so it carries no `vars.` token
    of its own): the real data dependency lives inside that scriptTask's own
    `<bpmn:script>` CDATA (structural-bpmn.md's Jint contract: `vars.<id>` dot
    access), so those refs are attached to that output's var id.
    """
    var_sources: dict[str, str] = {}
    for out in root.findall(".//uipath:output", NS):
        var = out.attrib.get("var")
        source = out.attrib.get("source")
        if var and source and var not in var_sources:
            var_sources[var] = source

    extra_refs: dict[str, set] = {}
    for task in elements(root, "scriptTask"):
        script_el = task.find("bpmn:script", NS)
        script_text = (script_el.text or "") if script_el is not None else ""
        script_refs = set(re.findall(r"vars\.([A-Za-z0-9_]+)", script_text))
        if not script_refs:
            continue
        for out in task.findall(".//uipath:output", NS):
            var = out.attrib.get("var")
            source = (out.attrib.get("source") or "").strip().lower()
            if var and source.startswith("=result"):
                extra_refs.setdefault(var, set()).update(script_refs)
    return var_sources, extra_refs


def derives_from(var_id: str, targets: set, var_sources: dict, extra_refs: dict, hops: int = 3) -> bool:
    if var_id in targets:
        return True
    if hops <= 0:
        return False
    refs = set(re.findall(r"vars\.([A-Za-z0-9_]+)", var_sources.get(var_id, "")))
    refs |= extra_refs.get(var_id, set())
    return any(derives_from(ref, targets, var_sources, extra_refs, hops - 1) for ref in refs)


def filter_reference_ids(task: ET.Element) -> set:
    ids: set = set()
    for inp in context_inputs(task):
        value = input_val(inp)
        ids.update(re.findall(r"vars\.([A-Za-z0-9_]+)", value))
        parsed = parse_json_maybe(value)
        if parsed is not None:
            ids.update(re.findall(r"vars\.([A-Za-z0-9_]+)", json.dumps(parsed)))
    return ids


def connection_binding_wired(root: ET.Element, task: ET.Element) -> bool:
    """The query's `connection` input is `=bindings.<id>` and that id is a
    declared `resource="Connection"` binding (registry-workflow.md §4). This is
    the authoring-time half of Flow's `assert_read_resolves`; the real-ID half
    is checked by the `bindings` mode after packing (see module docstring)."""
    connection_ref = context_value(task, "connection")
    match = re.match(r"^=bindings\.([A-Za-z0-9_]+)$", connection_ref.strip())
    if not match:
        return False
    binding_id = match.group(1)
    return any(
        binding.attrib.get("id") == binding_id
        and binding.attrib.get("resource") == "Connection"
        and binding.attrib.get("propertyAttribute") == "ConnectionId"
        for binding in root.findall(".//uipath:binding", NS)
    )


def connection_and_folder_distinct(root: ET.Element, task: ET.Element) -> bool | None:
    """F: advisory_billing_invoice_lookup.py's `assert_read_resolves` distinctness
    half -- "the two collapse into one binding at FIL emission and the live
    dispatch sends the folder key as --connection-id, answering 401". Fully
    visible pre-pack: a folder-scoped connector activity declares TWO bindings
    sharing one `resourceKey` (registry-workflow.md §4), so this compares their
    `default` values directly in the authored XML. Returns None when the
    activity is not folder-scoped (no sibling folderKey binding) -- nothing to
    compare, not a failure.
    """
    connection_ref = context_value(task, "connection")
    match = re.match(r"^=bindings\.([A-Za-z0-9_]+)$", connection_ref.strip())
    if not match:
        return None
    bindings = root.findall(".//uipath:binding", NS)
    conn = next((b for b in bindings if b.attrib.get("id") == match.group(1)), None)
    if conn is None:
        return None
    resource_key = conn.attrib.get("resourceKey")
    folder = next(
        (
            b
            for b in bindings
            if b.attrib.get("resourceKey") == resource_key and b.attrib.get("propertyAttribute") == "folderKey"
        ),
        None,
    )
    if folder is None:
        return None
    conn_default = (conn.attrib.get("default") or "").strip()
    folder_default = (folder.attrib.get("default") or "").strip()
    if not conn_default or not folder_default:
        return False
    return conn_default != folder_default


def advisory() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    # 1. exactly one entity-read node (F: advisory_billing_invoice_lookup.py:64-67)
    reads = query_entity_nodes(root)
    if len(reads) != 1:
        fail(f"expected exactly ONE Data Service Query Entity Records node, found {len(reads)}")
    query = reads[0]

    # no raw HTTP fallback (F: :71-74)
    http_nodes = [
        task.attrib.get("id")
        for task in (*elements(root, "sendTask"), *elements(root, "serviceTask"))
        if any(has_typed_uipath_extension(task, "activity", t) for t in ("Intsvc.HttpExecution", "Intsvc.UnifiedHttpRequest"))
    ]
    if http_nodes:
        fail(f"the process calls Data Service over raw HTTP ({http_nodes}); use the connector action")

    # 2. entity slot carries the seeded entity (F: :76-79)
    if not entity_ok(query):
        fail(f"the read does not address {ENTITY!r} in any path/query/body input or context path")

    # 3. filter COMPUTED from the input, not a constant (F: :82)
    input_names = declared_input_names(root)
    input_id = input_id_for_name(root, "invoiceNumber")
    if input_id is None:
        fail(f"process declares public inputs {input_names}; the contract asks for `invoiceNumber`")
    var_sources, extra_refs = build_var_graph(root)
    filter_refs = filter_reference_ids(query)
    if not any(derives_from(ref, {input_id}, var_sources, extra_refs) for ref in filter_refs):
        fail(
            f"the query's filter does not derive from the declared invoiceNumber input "
            f"(vars.{input_id}); refs found on the node: {sorted(filter_refs)}"
        )

    # 4. the ANSWER is nowhere in the file, and neither is a lookup table (F: :85-96)
    if CANONICAL in raw:
        fail(f"the bpmn contains the literal {CANONICAL!r} -- the invoice number must be COMPUTED, never written in")
    for bad in RAW_INPUTS:
        if bad in raw:
            fail(f"the bpmn contains the test input {bad!r} as a literal -- normalising by matching known inputs generalises to nothing")

    # 5. outputs declared with the contract's names AND types (F: :98-108)
    outputs = declared_outputs(root)
    for name, want in (("matchedInvoiceNumber", "string"), ("lineItemCount", "number")):
        if name not in outputs:
            fail(f"process declares public outputs {sorted(outputs)}; the contract asks for {name}")
        if outputs[name][1] != want:
            fail(f"output {name} is declared {outputs[name][1]!r}; the contract asks for {want}")

    # 6. both outputs are READ FROM the query step (F: :110-127)
    query_out_vars = set(output_vars(query))
    if not query_out_vars:
        fail("the Query Entity Records node has no <uipath:output var=...> for downstream nodes to reference")
    for name in ("matchedInvoiceNumber", "lineItemCount"):
        out_id = outputs[name][0]
        if not derives_from(out_id, query_out_vars, var_sources, extra_refs):
            fail(
                f"public output {name!r} does not derive from the Query Entity Records node's own "
                f"output (vars.{{{', '.join(sorted(query_out_vars))}}}) -- the value must come FROM the query step"
            )

    # 7. connection binding wired, and (when folder-scoped) resolves to a
    #    DISTINCT folder key (authoring-time half of :130-141; see module docstring)
    if not connection_binding_wired(root, query):
        fail(
            "the query's `connection` input is not a `=bindings.<id>` reference to a declared "
            "resource=\"Connection\" propertyAttribute=\"ConnectionId\" binding"
        )
    distinct = connection_and_folder_distinct(root, query)
    if distinct is False:
        fail(
            "the connection binding's `default` and its folderKey binding's `default` are the same "
            "value (or blank) -- the folder binding needs the connection's FOLDER key, not its "
            "connection id (measured live: the two collapse into one binding and the dispatch sends "
            "the folder key as --connection-id, answering 401)"
        )

    print(
        f"OK: {bpmn_path} -- 1 Query Entity Records node on {ENTITY!r}; filter computed from vars; "
        "outputs read from query; connection binding wired"
        + ("" if distinct is None else " with a distinct folder key")
    )


DISPATCH = {
    "lookup": lookup,
    "server_side_filter": server_side_filter,
    "bindings": bindings,
    "advisory": advisory,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
