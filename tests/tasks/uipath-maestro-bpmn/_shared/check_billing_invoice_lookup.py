#!/usr/bin/env python3
"""BillingInvoiceLookup (BPMN): three offline modes, selected by argv[1]:
`server_side_filter`, `bindings`, `advisory`. The live 3x debug check is
`multi_node/billing_invoice_lookup/check_invoice_lookup_run.py`.

The dispatch shape (module-level functions + a DISPATCH dict keyed on
`sys.argv[1]`) mirrors `check_outlook_trigger_inbox.py`, and doubles as the
entry point `tests/_shared/test_criterion_budgets.py` prices per subcommand.

Assertion map:
  curated|generic entity-CRUD classification; entity anywhere in
  inputs/objectName/path; GETBYID/GET(List) equivalence
                    -> query_entity_nodes() / entity_ok() (all modes)

  server_side_filter: the query carries a non-empty filter
                    -> has_nonempty_filter()
                    BPMN has no native Data Fabric node, so only the connector
                    shape applies.

  bindings: no stubbed connection key
                    -> is_real_connection_key(), stubbed-key scan over the
                    packed bindings_v2.json resources. bindings_v2.json is
                    emitted only at PACK time for BPMN (authoring leaves the
                    connection as a symbolic `=bindings.<id>` reference), so
                    the check runs `uip maestro bpmn pack` and reads the zip,
                    modeled on
                    e2e/customer_escalation_triage/check_customer_escalation_package.py.
                    A connection binding is always required (connector only).

  advisory:
  exactly ONE entity-read node
                    -> len(reads) != 1 check
  no raw HTTP fallback
                    -> no Intsvc.HttpExecution node check
  entity slot carries ENTITY
                    -> entity_ok()
  filter COMPUTED from input, not constant
                    -> filter_reference_ids() + derives_from(ref, {input_id}).
                    Does not pin one filter column: no local Data Service
                    connection exists to `describe` the entity's field name,
                    so any input at any depth deriving from the declared input
                    is accepted.
  canonical answer + raw test inputs never appear as literals
                    -> raw substring scan on the .bpmn text
  outputs declared with the contract's names AND types
                    -> declared_outputs()
  outputs READ FROM the query step
                    -> derives_from(output_id, query_out_vars) over the
                    var-source graph built from every `<uipath:output var=
                    source=>`, with transitive derivation through
                    BPMN.Variables copy tasks. A scriptTask's `<bpmn:script>`
                    CDATA `vars.<id>` reads are also followed when its
                    output's `source` starts with `=result` (see
                    build_var_graph()).
  connection binding wired
                    -> connection_binding_wired(): the query's `connection`
                    input is a `=bindings.<id>` reference to a declared
                    resource="Connection" binding.
  connection and folder bindings DISTINCT
                    -> connection_and_folder_distinct(): non-blank, different
                    `default` values (registry-workflow.md section 4). Equal
                    values collapse into one binding and answer 401.
                    bindings_v2.json `resources[]` carries no folder key, so
                    this half is authoring-time only.
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
    query_parameters,
    resolve_project,
)
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import CheckFailure  # noqa: E402

NAME_HINT = "BillingInvoiceLookup"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "BillingDisputeERP"
QUERY_CURATED_OBJECTS = {"queryentityrecordscurated", "queryentityrecords_v3"}

CANONICAL = "MCS-2026-04872"
# Malformed caller forms: a literal of any would let a lookup table pass.
RAW_INPUTS = [
    "2026-04872",
    "mcs-2026-04872",
    "MCS-2026-05128",
    "2026-05128",
    "mcs-2026-05128",
]

LIVE_RUN_DIR = Path("billing-invoice-lookup-live")
FILTER_INPUT_NAMES = {"queryexpression", "where", "filter", "filtergroup", "filtervariables"}



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
    return any(
        name.strip().lower() in FILTER_INPUT_NAMES and value not in ("", "{}", "[]")
        for name, value in query_parameters(task).items()
    )


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
            r
            for r in (doc.get("resources") or [])
            if isinstance(r, dict) and str(r.get("resource") or "").lower() == "connection"
        ]
        # Flow's own check only requires non-empty + non-stub, never an exact
        # count (a connector port always needs >=1, unlike Flow's native-read
        # branch, which this port drops -- see module docstring).
        if not resources:
            fail("packed bindings_v2.json declares no Connection resources")
        stubbed = [r.get("key") for r in resources if not is_real_connection_key(r.get("key"))]
        if stubbed:
            fail(
                "packed bindings_v2.json Connection keys must be real connection ids, "
                f"not unresolved stubs: {stubbed}"
            )
        print(f"OK: {len(resources)} connection binding(s) across bindings_v2.json, all non-stub")


# ── mode: advisory ───────────────────────────────────────────────────────────


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
    the authoring-time half of the connection check; the real-ID half
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
    """Connection and folder bindings must differ: the same value sends the folder key as --connection-id and answers 401.

    Fully visible pre-pack: a folder-scoped connector activity declares TWO bindings
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

    # 1. exactly one entity-read node
    reads = query_entity_nodes(root)
    if len(reads) != 1:
        fail(f"expected exactly ONE Data Service Query Entity Records node, found {len(reads)}")
    query = reads[0]

    # no raw HTTP fallback (F: :71-74)
    http_nodes = [
        task.attrib.get("id")
        for task in (*elements(root, "sendTask"), *elements(root, "serviceTask"))
        if any(
            has_typed_uipath_extension(task, "activity", t)
            for t in ("Intsvc.HttpExecution", "Intsvc.UnifiedHttpRequest")
        )
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
            fail(
                f"the bpmn contains the test input {bad!r} as a literal -- "
                "normalising by matching known inputs generalises to nothing"
            )

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
