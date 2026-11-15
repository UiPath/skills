from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent
FLOW_TASKS = SHARED.parent
REFERENCE_CASES = {
    "advisory_billing_invoice_lookup.py": (
        "multi_node/billing_invoice_lookup/BillingInvoiceLookup.reference.flow"
    ),
    "advisory_billing_discrepancy_detector.py": (
        "multi_node/billing_discrepancy_detector/BillingDiscrepancyDetector.reference.flow"
    ),
    "advisory_billing_dispute_analyst.py": (
        "multi_node/billing_dispute_analyst/BillingDisputeAnalyst.reference.flow"
    ),
    "advisory_billing_resolution_writer.py": (
        "multi_node/billing_resolution_writer/BillingResolutionWriter.reference.flow"
    ),
    "advisory_billing_dispute_resolution.py": (
        "multi_node/billing_dispute_resolution/BillingDisputeResolution.reference.flow"
    ),
}


# The native `core.datafabric.read` build of each scenario. Tenant availability
# decides the shape, so a correct build comes in either one and every advisory
# has to grade both — the 2026-09-11 dispute-resolution run scored 0.727 on a
# flow that validated, debugged green, and returned the right answer, because
# the advisory demanded a `connection` binding the native node never has.
#
# The dispute-resolution case IS that run's artifact, kept verbatim. The other
# two are derived from their connector reference below, so the computed filter
# under test stays the reference's and not the test's.
NATIVE_REFERENCE_CASE = (
    "advisory_billing_dispute_resolution.py",
    "multi_node/billing_dispute_resolution/BillingDisputeResolution.native.reference.flow",
)
# Entity -> the column its filter matches on, for `_to_native_reads`.
NATIVE_FILTER_FIELDS = {
    "BillingDisputeERP": "invoiceNumber",
    "BillingDisputeCRM": "accountNumber",
}
# The connector reference spells its filter as one CEQL template,
# `=js:`<column> = '${<expression>}'`` — the interpolation is the value a native
# filter row carries on its own.
CEQL_TEMPLATE = re.compile(r"^=js:`(\w+) = '\$\{(.*)\}'`$", re.DOTALL)


def _to_native_reads(flow: dict) -> dict:
    """Rewrite a connector reference's entity reads as native ones, in place."""
    for node in flow["nodes"]:
        if "uipath-uipath-dataservice." not in str(node.get("type")):
            continue
        detail = node["inputs"]["detail"]
        entity = detail["pathParameters"]["entityName"]
        match = CEQL_TEMPLATE.match(str(detail["queryParameters"]["queryExpression"]))
        assert match, detail["queryParameters"]["queryExpression"]
        column, expression = match.group(1), match.group(2)
        assert column == NATIVE_FILTER_FIELDS[entity], (entity, column)
        node["type"] = "core.datafabric.read"
        node["typeVersion"] = "1.4"
        node["inputs"] = {
            "entityConfig": {
                "entityName": entity,
                "resultMode": "multiple",
                "_recordLimit": 100,
                "_skip": 0,
                "_filters": {
                    "logicalOperator": "AND",
                    "rows": [{"field": column, "operator": "=", "value": f"=js:{expression}"}],
                    "groups": [],
                },
            }
        }
    return flow


def native_build(script: str, tmp_path: Path) -> Path:
    """Write and return a native-shaped build of ``script``'s scenario."""
    source = FLOW_TASKS / REFERENCE_CASES[script]
    target = tmp_path / source.name.replace(".reference", "")
    target.write_text(json.dumps(_to_native_reads(json.loads(source.read_text()))))
    return target


def run_script(script: str, *args: Path | str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SHARED / script), *(str(arg) for arg in args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(("script", "relative_flow"), REFERENCE_CASES.items())
def test_advisories_accept_repo_reference_flows(script: str, relative_flow: str) -> None:
    result = run_script(script, FLOW_TASKS / relative_flow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_advisories_accept_the_native_dispute_resolution_build() -> None:
    """Regression lock for the 2026-09-11 run: the flow this artifact came from
    validated, debugged green, and returned the right answer, and the advisory
    failed it for having no `connection` binding — which the native node never
    has (data-fabric/planning.md — Native node vs Data Service connector)."""
    script, relative_flow = NATIVE_REFERENCE_CASE
    result = run_script(script, FLOW_TASKS / relative_flow)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "native entity read" in result.stdout


@pytest.mark.parametrize(
    "script",
    ["advisory_billing_invoice_lookup.py", "advisory_billing_discrepancy_detector.py"],
)
def test_advisories_accept_native_derived_builds(script: str, tmp_path: Path) -> None:
    result = run_script(script, native_build(script, tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "native read" in result.stdout


def test_native_anti_hardcode_guard_survives(tmp_path: Path) -> None:
    """The whole point of these gates: a filter that writes the answer in
    satisfies every behaviour rung while querying nothing. Shape must not be a
    way around it."""
    target = native_build("advisory_billing_invoice_lookup.py", tmp_path)
    flow = json.loads(target.read_text())
    for node in flow["nodes"]:
        rows = ((node.get("inputs") or {}).get("entityConfig") or {}).get("_filters", {}).get("rows")
        for row in rows or []:
            row["value"] = "MCS-2026-04872"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode != 0
    assert "$vars" in result.stdout + result.stderr


def _native_rows(flow: dict) -> list[dict]:
    """Every native read's root filter rows, for a test to mutate in place."""
    return [
        ((node.get("inputs") or {}).get("entityConfig") or {})["_filters"]["rows"]
        for node in flow["nodes"]
        if (node.get("inputs") or {}).get("entityConfig")
    ]


def _run_invoice_native(tmp_path: Path, mutate) -> subprocess.CompletedProcess:
    target = native_build("advisory_billing_invoice_lookup.py", tmp_path)
    flow = json.loads(target.read_text())
    mutate(flow)
    target.write_text(json.dumps(flow))
    return run_script("advisory_billing_invoice_lookup.py", target)


def test_native_filter_with_no_rows_fails(tmp_path: Path) -> None:
    """An unfiltered read is the client-side-filter build the gate exists to name."""

    def mutate(flow):
        for rows in _native_rows(flow):
            rows.clear()

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "no `entityConfig._filters` rows" in result.stdout + result.stderr


def test_native_filter_no_rows_message_follows_result_mode(tmp_path: Path) -> None:
    """A `single` read's failure is an over-match fault, not 100 arbitrary rows."""

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if config:
                config["resultMode"] = "single"
                config["_filters"]["rows"].clear()

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "over-match" in result.stdout + result.stderr


def test_native_filter_unsupported_operator_fails(tmp_path: Path) -> None:
    """The serializer refuses the WHOLE query, so the node emits nothing and
    every downstream `$vars` reference breaks."""

    def mutate(flow):
        for rows in _native_rows(flow):
            for row in rows:
                row["operator"] = "not in"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "'not in'" in result.stdout + result.stderr


def test_native_filter_blank_value_fails(tmp_path: Path) -> None:
    """Reachable only past the references check, so the valid row stays: an
    expression switched on and left blank is refused rather than dropped."""

    def mutate(flow):
        for rows in _native_rows(flow):
            rows.append({"field": "status", "operator": "=", "value": "   "})

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "blank value" in result.stdout + result.stderr


def test_native_filter_self_reference_fails(tmp_path: Path) -> None:
    """A query cannot wait on the record it is being run to fetch."""

    def mutate(flow):
        for rows in _native_rows(flow):
            rows.append({"field": "status", "operator": "=", "value": "=js:$self.Id"})

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "$self" in result.stdout + result.stderr


def test_native_filter_in_a_nested_group_is_found(tmp_path: Path) -> None:
    """`_filters` is a grouped model, so the computed row may sit in a group."""

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if not config:
                continue
            rows = config["_filters"]["rows"]
            config["_filters"] = {
                "logicalOperator": "AND",
                "rows": [],
                "groups": [{"logicalOperator": "OR", "rows": list(rows), "groups": []}],
            }

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_filter_reached_through_a_script_hop(tmp_path: Path) -> None:
    """The prompt asks to normalise the input and THEN look up, and a native row
    is a single `value`, so the normalisation lands in a Script the row reads.
    Section 6 of this advisory already tolerates the hop for outputs."""

    def mutate(flow):
        flow["nodes"].append(
            {
                "id": "normalizeInvoice",
                "type": "core.action.script",
                "inputs": {"value": "=js:$vars.start.output.invoiceNumber.trim().toUpperCase()"},
            }
        )
        for rows in _native_rows(flow):
            for row in rows:
                row["value"] = "=js:$vars.normalizeInvoice.output.value"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


AMBIGUOUS_SCRIPTS = [
    pytest.param(
        "const n = String($vars.start.output.invoiceNumber).trim(); "
        "if (n) { return { value: n }; } else { return { value: 'NONE' }; }",
        id="two-returns",
    ),
    pytest.param(
        "try { return { value: String($vars.start.output.invoiceNumber).trim() }; } "
        "catch (e) { return { value: '' }; }",
        id="try-catch",
    ),
    pytest.param(
        "let v;\nv = String($vars.start.output.invoiceNumber).trim();\nreturn { value: v };",
        id="deferred-let",
    ),
    pytest.param(
        "const n = String($vars.start.output.invoiceNumber).trim(); "
        "['a'].map(t => { const n = t.toUpperCase(); return n; }); return { value: n };",
        id="shadowed-name",
    ),
]


@pytest.mark.parametrize("script", AMBIGUOUS_SCRIPTS)
def test_native_filter_hop_through_ambiguous_script(tmp_path: Path, script: str) -> None:
    def mutate(flow):
        flow["nodes"].append(_script("normalizeInvoice", script))
        for rows in _native_rows(flow):
            for row in rows:
                row["value"] = "=js:$vars.normalizeInvoice.output.value"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_filter_hop_to_constant_same_named_output_fails(tmp_path: Path) -> None:
    def mutate(flow):
        flow["nodes"].append(_script("normalizeInvoice", CONSTANT_SAME_NAMED_SCRIPT))
        for rows in _native_rows(flow):
            for row in rows:
                row["value"] = "=js:$vars.normalizeInvoice.output.invoiceNumber"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "reaches $vars.…invoiceNumber" in result.stdout + result.stderr


def test_native_filter_reference_in_a_comment_fails(tmp_path: Path) -> None:
    def mutate(flow):
        for rows in _native_rows(flow):
            for row in rows:
                row["value"] = "=js:/* $vars.start.output.invoiceNumber */ 'MCS-9999-00000'"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "reaches $vars.…invoiceNumber" in result.stdout + result.stderr


def test_native_filter_hop_to_nothing_still_fails(tmp_path: Path) -> None:
    """Following the hop must not degrade into accepting any `$vars` reference."""

    def mutate(flow):
        flow["nodes"].append(
            {"id": "constant", "type": "core.action.script", "inputs": {"value": "MCS-9999-00000"}}
        )
        for rows in _native_rows(flow):
            for row in rows:
                row["value"] = "=js:$vars.constant.output.value"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "invoiceNumber" in result.stdout + result.stderr


def _run_invoice_connector(tmp_path: Path, mutate) -> subprocess.CompletedProcess:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]
    flow = json.loads(source.read_text())
    mutate(flow)
    target = tmp_path / source.name.replace(".reference", "")
    target.write_text(json.dumps(flow))
    return run_script("advisory_billing_invoice_lookup.py", target)


def _connector_query(flow: dict, expression: str, *producers: dict) -> None:
    """Point the connector read's queryExpression at ``expression``, fed by ``producers``."""
    flow["nodes"].extend(producers)
    for node in flow["nodes"]:
        detail = (node.get("inputs") or {}).get("detail")
        if detail and "queryExpression" in (detail.get("queryParameters") or {}):
            detail["queryParameters"]["queryExpression"] = expression


def _script(node_id: str, script: str) -> dict:
    return {"id": node_id, "type": "core.action.script", "inputs": {"script": script}}


CONSTANT_SAME_NAMED_SCRIPT = "return { invoiceNumber: \"MCS-9999-00000\" };"
NORMALIZE_SCRIPT = (
    "const n = String($vars.start.output.invoiceNumber).trim().toUpperCase(); "
    "return { value: n.startsWith('MCS-') ? n : 'MCS-' + n };"
)


def test_connector_query_built_by_a_script_hop(tmp_path: Path) -> None:
    """Advisory policy, not skill guidance: normalising in a Script that returns
    the CEQL string is the hop the native branch already accepts."""

    def mutate(flow):
        _connector_query(
            flow,
            "=js:$vars.buildQuery.output.queryExpression",
            _script(
                "buildQuery",
                "const n = String($vars.start.output.invoiceNumber).trim().toUpperCase(); "
                "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            ),
        )

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_connector_query_built_two_hops_from_the_input(tmp_path: Path) -> None:
    def mutate(flow):
        _connector_query(
            flow,
            "=js:$vars.buildQuery.output.queryExpression",
            _script("normalizeInvoice", NORMALIZE_SCRIPT),
            _script(
                "buildQuery",
                "return { queryExpression: `invoiceNumber = '${$vars.normalizeInvoice.output.value}'` };",
            ),
        )

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", AMBIGUOUS_SCRIPTS)
def test_connector_hop_through_ambiguous_script(tmp_path: Path, script: str) -> None:
    script = script.replace("value: n", "value: \"invoiceNumber = '\" + n + \"'\"")
    script = script.replace("value: v", "value: \"invoiceNumber = '\" + v + \"'\"")
    script = script.replace(
        "value: String($vars.start.output.invoiceNumber).trim()",
        "value: \"invoiceNumber = '\" + String($vars.start.output.invoiceNumber).trim() + \"'\"",
    )
    result = _run_invoice_connector(
        tmp_path,
        lambda flow: _connector_query(
            flow, "=js:$vars.buildQuery.output.value", _script("buildQuery", script)
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("expression", "script"),
    [
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "return { queryExpression: `invoiceNumber = '${n.startsWith(\"MCS-\") ? n : `MCS-${n}`}'` };",
            id="nested-template",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "const f = (o) => o.v;\n"
            "return { queryExpression: `invoiceNumber = '${f({ v: n })}'` };",
            id="braces-in-interpolation",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "let n = \"\"; n += $vars.start.output.invoiceNumber; "
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="compound-assignment",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "return { /* CEQL filter */ queryExpression: "
            "\"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="comment-before-key",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "return { \"queryExpression\": \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="double-quoted-key",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "return { /* CEQL */ 'queryExpression': \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="single-quoted-key",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "return { queryExpression: \"\", ...{ queryExpression: "
            "\"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" } };",
            id="overriding-spread",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const supplied = String($vars.start.output.invoiceNumber ?? \"\").trim().toUpperCase();\n"
            "const normalized = supplied.startsWith(\"MCS-\") ? supplied : `MCS-${supplied}`;\n"
            "// CEQL escapes a single quote by doubling it.\n"
            "const queryExpression = \"invoiceNumber = '\" + normalized.replace(/'/g, \"''\") + \"'\";\n"
            "return { normalized, queryExpression };",
            id="shorthand-entry-through-bindings",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output[\"queryExpression\"]",
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="bracket-access",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "const ok = (() => { return /'/.test(n) })();\n"
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="regex-after-return",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "const ok = /[/]'/.test(n);\n"
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="regex-char-class-slash",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const hasQuote = (s) => /'/.test(s);\n"
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="regex-after-arrow",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "if (!n) { throw new Error('empty'); } else /'/.test(n);\n"
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="regex-after-else",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const n = $vars.start.output.invoiceNumber;\n"
            "if (!n) { return { queryExpression: \"invoiceNumber = ''\" }; }\n"
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="guard-clause",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "return { ['queryExpression']: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="computed-key",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            "const { output: { invoiceNumber: n } } = $vars.start;\n"
            "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
            id="nested-destructuring",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression.trim()",
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="method-on-hop",
        ),
        pytest.param(
            "=js:`${$vars.buildQuery.output.queryExpression}`",
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="hop-in-template",
        ),
        pytest.param(
            "=js:String($vars.buildQuery.output.queryExpression)",
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            id="hop-in-call",
        ),
    ],
)
def test_connector_hop_spellings_pass(tmp_path: Path, expression: str, script: str) -> None:
    result = _run_invoice_connector(
        tmp_path, lambda flow: _connector_query(flow, expression, _script("buildQuery", script))
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("expression", "producers"),
    [
        pytest.param("invoiceNumber = 'MCS-9999-00000'", (), id="literal"),
        pytest.param("=js:$vars.start.output.accountNumber", (), id="unrelated-reference"),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (_script("buildQuery", "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000'\" };"),),
            id="producer-ignores-input",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "const n = $vars.start.output.invoiceNumber; "
                    "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000'\" };",
                ),
            ),
            id="dead-read",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "const n = \"MCS-9999-00000\", unused = $vars.start.output.invoiceNumber; "
                    "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" };",
                ),
            ),
            id="dead-read-comma-declarators",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "const n = \"MCS-9999-00000\"\n"
                    "const unused = $vars.start.output.invoiceNumber\n"
                    "return { queryExpression: \"invoiceNumber = '\" + n + \"'\" }",
                ),
            ),
            id="dead-read-no-semicolons",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "return { erp: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
                ),
            ),
            id="absent-output",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script("normalizeInvoice", CONSTANT_SAME_NAMED_SCRIPT),
                _script(
                    "buildQuery",
                    "return { queryExpression: \"invoiceNumber = '\" + "
                    "$vars.normalizeInvoice.output.invoiceNumber + \"'\" };",
                ),
            ),
            id="constant-same-named-output",
        ),
        pytest.param(
            "=js:\"invoiceNumber = '\" + $vars.normalizeInvoice.output.invoiceNumber + \"'\"",
            (_script("normalizeInvoice", CONSTANT_SAME_NAMED_SCRIPT),),
            id="constant-same-named-output-direct",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000'\" "
                    "/* from $vars.start.output.invoiceNumber */ };",
                ),
            ),
            id="reference-in-entry-comment",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000' -- $vars.start.output.invoiceNumber\" };",
                ),
            ),
            id="reference-in-entry-string",
        ),
        pytest.param(
            "=js:/* $vars.start.output.invoiceNumber */ \"invoiceNumber = 'MCS-9999-00000'\"",
            (),
            id="reference-in-direct-comment",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "const n = $vars.start.output.invoiceNumber; let tries = 0; tries += 1; "
                    "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000'\" };",
                ),
            ),
            id="dead-read-beside-a-reassignment",
        ),
        pytest.param(
            "=js:$vars.buildQuery.output.queryExpression",
            (
                _script(
                    "buildQuery",
                    "const n = $vars.start.output.invoiceNumber; "
                    "[n].map(x => { return { queryExpression: \"invoiceNumber = '\" + x + \"'\" }; }); "
                    "return { queryExpression: \"invoiceNumber = 'MCS-9999-00000'\" };",
                ),
            ),
            id="callback-return",
        ),
    ],
)
def test_connector_query_not_from_the_input_fails(
    tmp_path: Path, expression: str, producers: tuple
) -> None:
    """Following the hop must not degrade into accepting any `$vars` reference."""
    result = _run_invoice_connector(tmp_path, lambda flow: _connector_query(flow, expression, *producers))
    assert result.returncode != 0
    assert "neither it nor a node it reads" in result.stdout + result.stderr


@pytest.mark.parametrize(
    "script",
    [
        pytest.param(
            "return { queryExpression: 'invoiceNumber = ' + $vars.start.output.invoiceNumber };",
            id="js-quotes-around-unquoted-value",
        ),
        pytest.param(
            "const p = \"MCS-\"; const n = $vars.start.output.invoiceNumber; "
            "return { queryExpression: 'invoiceNumber = ' + p + n, note: \"done\" };",
            id="js-quotes-between-double-quoted-literals",
        ),
        pytest.param(
            "const n = String($vars.start.output.invoiceNumber).replace(/'/g, \"''\"); "
            "return { queryExpression: \"invoiceNumber = \" + n };",
            id="unrelated-quote-literal",
        ),
        pytest.param(
            "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber };",
            id="no-closing-quote",
        ),
        pytest.param(
            "const n = $vars.start.output.invoiceNumber; console.log(\"invoiceNumber = '\" + n + \"'\"); "
            "return { queryExpression: 'invoiceNumber = ' + n };",
            id="quote-only-in-a-log",
        ),
        pytest.param(
            "const n = String($vars.start.output.invoiceNumber).replace(/'/g, \"''\"); "
            "return { queryExpression: \"invoiceNumber = '\" + n };",
            id="escaped-value-no-closing-quote",
        ),
        pytest.param(
            "return { queryExpression: `invoiceNumber = '${String($vars.start.output.invoiceNumber)"
            ".replace(/'/g, \"''\")}` };",
            id="template-quote-only-in-interpolation",
        ),
        pytest.param(
            "const n = $vars.start.output.invoiceNumber; let tries = 0; tries += 1; "
            "console.log(\"invoiceNumber = '\" + n + \"'\"); return { queryExpression: 'invoiceNumber = ' + n };",
            id="quote-only-in-a-log-beside-a-reassignment",
        ),
        pytest.param(
            "const n = $vars.start.output.invoiceNumber; "
            "if (!n) { return { queryExpression: \"invoiceNumber = ''\" }; } "
            "return { queryExpression: 'invoiceNumber = ' + n };",
            id="guard-clause-unquoted",
        ),
        pytest.param(
            "const n = $vars.start.output.invoiceNumber; "
            "const unused = (() => { return { queryExpression: \"invoiceNumber = '\" + n + \"'\" }; })(); "
            "return { queryExpression: 'invoiceNumber = ' + n };",
            id="iife-return",
        ),
        pytest.param(
            "const n = $vars.start.output.invoiceNumber;\n"
            "const isUrl = (s) => /^https?:\\/\\//.test(s); return { queryExpression: 'invoiceNumber = ' + n };\n"
            "const msg = \"invoiceNumber = '\" + n + \"'\";",
            id="regex-with-slashes-after-arrow",
        ),
        pytest.param(
            "return { queryExpression: \"invoiceNumber = ''\" + $vars.start.output.invoiceNumber };",
            id="empty-quoted-literal",
        ),
    ],
)
@pytest.mark.parametrize(
    "expression",
    [
        pytest.param("=js:$vars.buildQuery.output.queryExpression", id="dot"),
        pytest.param("=js:$vars.buildQuery.output['queryExpression']", id="bracket"),
    ],
)
def test_connector_hop_with_unquoted_ceql_fails(tmp_path: Path, script: str, expression: str) -> None:
    """A quote somewhere upstream is not a quoted CEQL value; unquoted, the RHS
    parses as subtraction server-side and 400s."""

    def mutate(flow):
        _connector_query(flow, expression, _script("buildQuery", script))

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode != 0
    assert "single-quoted" in result.stdout + result.stderr


@pytest.mark.parametrize(
    "expression",
    [
        pytest.param("=js:$vars.buildQuery.output.queryExpression + \" AND status = 'open'\"", id="quoted-suffix"),
        pytest.param("=js:$vars.buildQuery.output.queryExpression /* ' */", id="quote-in-comment"),
    ],
)
def test_connector_quote_beside_an_unquoted_hop_fails(tmp_path: Path, expression: str) -> None:
    """A quote in the direct expression does not quote the value the hop builds."""
    script = "return { queryExpression: 'invoiceNumber = ' + $vars.start.output.invoiceNumber };"
    result = _run_invoice_connector(
        tmp_path, lambda flow: _connector_query(flow, expression, _script("buildQuery", script))
    )
    assert result.returncode != 0
    assert "single-quoted" in result.stdout + result.stderr


def test_connector_hop_carrying_the_answer_fails(tmp_path: Path) -> None:
    """An inner return can satisfy the reference and quote checks while the
    returned query is the canonical answer, written in."""
    script = (
        "const n = $vars.start.output.invoiceNumber; "
        "[n].map(() => { return { queryExpression: \"invoiceNumber = '\" + n + \"'\" }; }); "
        "return { queryExpression: \"invoiceNumber = 'MCS-2026-04872'\" };"
    )
    result = _run_invoice_connector(
        tmp_path,
        lambda flow: _connector_query(
            flow, "=js:$vars.buildQuery.output.queryExpression", _script("buildQuery", script)
        ),
    )
    assert result.returncode != 0
    assert "carries the literal 'MCS-2026-04872'" in result.stdout + result.stderr


def test_literal_scan_reads_inside_a_double_quoted_script_string() -> None:
    sys.path.insert(0, str(SHARED))
    from advisory_flow_utils import carries_literal

    script = "return { queryExpression: \"invoiceNumber = 'MCS-2026-04872'\" };"
    assert carries_literal({"nodes": [{"inputs": {"script": script}}]}, "MCS-2026-04872")


def test_script_trace_past_the_inline_cap_is_ambiguous() -> None:
    """Each ternary triples the inlined text; past the cap the trace falls back
    instead of building a multi-megabyte string."""
    sys.path.insert(0, str(SHARED))
    from advisory_flow_utils import script_output

    lines = ["const v0 = $vars.start.output.invoiceNumber;"]
    lines += [f"const v{i} = v{i - 1} ? v{i - 1} : v{i - 1};" for i in range(1, 11)]
    lines.append("return { queryExpression: \"invoiceNumber = '\" + v10 + \"'\" };")
    assert script_output(_script("buildQuery", "\n".join(lines)), "queryExpression") is None


def test_connector_hop_forwarded_through_an_alias(tmp_path: Path) -> None:
    def mutate(flow):
        _connector_query(
            flow,
            "=js:$vars.forward.output.queryExpression",
            _script(
                "buildQuery",
                "return { queryExpression: \"invoiceNumber = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            ),
            _script(
                "forward",
                "const q = $vars.buildQuery.output.queryExpression; return { queryExpression: q };",
            ),
        )

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_connector_hop_on_the_wrong_column_names_the_column(tmp_path: Path) -> None:
    def mutate(flow):
        _connector_query(
            flow,
            "=js:$vars.buildQuery.output.queryExpression",
            _script(
                "buildQuery",
                "return { queryExpression: \"customerId = '\" + $vars.start.output.invoiceNumber + \"'\" };",
            ),
        )

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode != 0
    assert "`invoiceNumber = '<value>'`" in result.stdout + result.stderr


def test_connector_hop_cross_wired_outputs_fail(tmp_path: Path) -> None:
    """One Script builds both queries; each read must take the entry built from
    its own input, not the one the other read needs."""
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_discrepancy_detector.py"]
    flow = json.loads(source.read_text())
    flow["nodes"].append(
        _script(
            "buildQueries",
            "const inv = $vars.start.output.invoiceNumber; const acc = $vars.start.output.accountNumber; "
            "return { erp: \"invoiceNumber = '\" + inv + \"'\", crm: \"accountNumber = '\" + acc + \"'\" };",
        )
    )
    for node in flow["nodes"]:
        detail = (node.get("inputs") or {}).get("detail") or {}
        query = detail.get("queryParameters") or {}
        if "queryExpression" not in query:
            continue
        key = "crm" if detail["pathParameters"]["entityName"] == "BillingDisputeERP" else "erp"
        query["queryExpression"] = f"=js:$vars.buildQueries.output.{key}"
    target = tmp_path / source.name.replace(".reference", "")
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_discrepancy_detector.py", target)
    assert result.returncode != 0
    assert "neither it nor a node it reads" in result.stdout + result.stderr


def test_native_read_beside_a_connector_write_is_not_a_mix(tmp_path: Path) -> None:
    """Each native op has its own tenant flag, so `read-entity` on with
    `create-entity` off is a real configuration, not a half-migrated flow."""

    def mutate(flow):
        flow["nodes"].append(
            {
                "id": "auditWrite",
                "type": "uipath.connector.uipath-uipath-dataservice.create-entity-record",
                "inputs": {},
            }
        )

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_blank_folder_key_fails(tmp_path: Path) -> None:
    """It is the key's PRESENCE that switches the emitted target to the
    folder-qualified form, so a blank one emits that form with no folder."""

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if config:
                config["_folderKey"] = ""

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "leaves it blank" in result.stdout + result.stderr


def test_native_filter_on_the_wrong_column_fails(tmp_path: Path) -> None:
    """The right value on the wrong column queries nothing useful, and checking
    only the value let it through."""

    def mutate(flow):
        for rows in _native_rows(flow):
            for row in rows:
                row["field"] = "accountNumber"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "'invoiceNumber'" in result.stdout + result.stderr


def test_native_filter_column_case_is_tolerated(tmp_path: Path) -> None:
    """A column whose CASE is wrong is a different defect, caught live. Failing
    it here is the over-strictness this file keeps paying for."""

    def mutate(flow):
        for rows in _native_rows(flow):
            for row in rows:
                row["field"] = "InvoiceNumber"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_filter_legacy_in_operator_is_accepted(tmp_path: Path) -> None:
    """`is any of` is the legacy spelling of `in` and the platform still reads
    it, so rejecting it fails a filter the serializer accepts."""

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if config:
                config["resultMode"] = "multiple"
                for row in config["_filters"]["rows"]:
                    row["operator"] = "is any of"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_entity_binding_without_a_default_fails(tmp_path: Path) -> None:
    """The row's whole purpose is to carry the value packaging overrides with, so
    matching the metadata and skipping `default` reports success on a pair that
    overrides nothing."""
    key = "erp-resource-key"

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if config:
                config["_folderKey"] = FOLDER_KEY
                config["_resourceKey"] = key
        flow["bindings"] = [
            _entity_row("Entity", key, attribute, default=None)
            for attribute in ("name", "folderKey")
        ]

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "carry no `default`" in result.stdout + result.stderr


def test_native_non_uuid_folder_key_fails(tmp_path: Path) -> None:
    """`_folderKey` is the entity's `folderId`, so the emitted folder-qualified
    target cannot resolve a value of another shape."""

    def mutate(flow):
        for node in flow["nodes"]:
            config = (node.get("inputs") or {}).get("entityConfig")
            if config:
                config["_folderKey"] = "Shared/uipath-maestro-flow/BillingDispute"

    result = _run_invoice_native(tmp_path, mutate)
    assert result.returncode != 0
    assert "not a folder id" in result.stdout + result.stderr


def test_server_side_filter_rejects_a_row_with_no_predicate(tmp_path: Path) -> None:
    """`rows: [{}]` is a non-empty list the serializer emits nothing from, so
    list non-emptiness is not the question."""
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    flow = _native_flow()
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_filters"] = {"logicalOperator": "AND", "rows": [{}], "groups": []}
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode != 0
    assert "no server-side filter" in result.stdout + result.stderr


def test_entity_read_shapes_match_the_structural_gates() -> None:
    """Two discriminators describe the same two shapes: this module's for the
    advisories, `flow_check.ENTITY_QUERY_HINTS` for the structural gates. A
    comment asking to "keep the two in step" is not a guard."""
    sys.path.insert(0, str(SHARED))
    import advisory_flow_utils
    import flow_check

    hints = flow_check.ENTITY_QUERY_HINTS
    assert len(hints) == 2, hints
    assert advisory_flow_utils.NATIVE_READ_TYPE in hints
    connector_type = advisory_flow_utils.CONNECTOR_READ_PREFIX + "query-entity-records"
    assert any(hint in connector_type for hint in hints), (hints, connector_type)


def test_bindings_checker_accepts_a_valid_connection_pair(tmp_path: Path) -> None:
    flow = json.loads((FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]).read_text())
    cwd = _project(tmp_path, flow, CONNECTION_BINDINGS, "BillingInvoiceLookup")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "(connector)" in result.stdout


def test_native_half_authored_folder_scope_fails(tmp_path: Path) -> None:
    """`_folderKey` switches the emitted target to the folder-qualified form, so
    without `_resourceKey` and both Entity binding rows the name and folder
    serialize as source-org literals: it packages and breaks on deploy."""
    target = native_build("advisory_billing_invoice_lookup.py", tmp_path)
    flow = json.loads(target.read_text())
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_folderKey"] = FOLDER_KEY
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode != 0
    assert "_resourceKey" in result.stdout + result.stderr


def test_native_lowercase_entity_binding_row_fails(tmp_path: Path) -> None:
    """`resource` is the capitalized "Entity"; packaging never turns a lowercase
    row into a binding resource, so the deploy side gets no override at all."""
    target = native_build("advisory_billing_invoice_lookup.py", tmp_path)
    flow = json.loads(target.read_text())
    key = "orders-resource-key"
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_folderKey"] = FOLDER_KEY
            config["_resourceKey"] = key
    flow["bindings"] = [_entity_row("entity", key, attribute) for attribute in ("name", "folderKey")]
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode != 0
    assert "Entity" in result.stdout + result.stderr


def test_native_folder_scope_with_both_binding_rows_passes(tmp_path: Path) -> None:
    target = native_build("advisory_billing_invoice_lookup.py", tmp_path)
    flow = json.loads(target.read_text())
    key = "erp-resource-key"
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_folderKey"] = FOLDER_KEY
            config["_resourceKey"] = key
    flow["bindings"] = [_entity_row("Entity", key, attribute) for attribute in ("name", "folderKey")]
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "folder-scoped entity" in result.stdout


def test_mixed_entity_read_shapes_fail(tmp_path: Path) -> None:
    """One shape per flow. Two means a set of reads was left behind, and the
    count assertions downstream would report something else."""
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_discrepancy_detector.py"]
    flow = json.loads(source.read_text())
    native = next(node for node in flow["nodes"] if "uipath-uipath-dataservice." in str(node.get("type")))
    native["type"] = "core.datafabric.read"
    target = tmp_path / "BillingDiscrepancyDetector.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_discrepancy_detector.py", target)
    assert result.returncode != 0
    assert "mixes both entity-read shapes" in result.stdout + result.stderr


def _project(tmp_path: Path, flow: dict, bindings: dict, name: str) -> Path:
    """A generated-solution tree as the two billing checkers walk it: one flow
    and one bindings file under the cwd they are run from."""
    project = tmp_path / "proj"
    project.mkdir(parents=True, exist_ok=True)
    (project / f"{name}.flow").write_text(json.dumps(flow))
    (project / "bindings_v2.json").write_text(json.dumps(bindings))
    return tmp_path


def _native_flow() -> dict:
    return json.loads((FLOW_TASKS / NATIVE_REFERENCE_CASE[1]).read_text())


FOLDER_KEY = "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"


def _entity_row(resource: str, key: str, attribute: str, default: str | None = "Orders") -> dict:
    """A Data Fabric entity binding row. `default` is the value packaging
    substitutes, so a row without one matches and overrides nothing."""
    row = {"resource": resource, "resourceKey": key, "propertyAttribute": attribute}
    if default is not None:
        row["default"] = FOLDER_KEY if attribute == "folderKey" else default
    return row


CONNECTION_BINDINGS = {
    "version": "2.0",
    "resources": [
        {
            "resource": "connection",
            "key": "data-fabric",
            "value": {
                "ConnectionId": {"defaultValue": "d61e5d0e-04af-4f93-95cc-151d81fa08dc"},
                "FolderKey": {"defaultValue": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c"},
            },
        }
    ],
}
# What a native build actually writes: resources for the IxP model, the API
# workflow and the context index, and no `connection` row at all. Named for what
# it lacks, because the connector cases below reuse it to mean "the row is gone".
NON_CONNECTION_BINDINGS = {
    "version": "2.0",
    "resources": [
        {"resource": "process", "key": "p", "value": {"name": {"defaultValue": "FinancialPostingFunction"}}}
    ],
}


def test_bindings_checker_accepts_a_native_build_with_no_connection(tmp_path: Path) -> None:
    """A flow whose only external calls are native reads has no Integration
    Service connection to bind, so `declares no bindings at all` is wrong there."""
    cwd = _project(tmp_path, _native_flow(), NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no connection to bind" in result.stdout


def test_bindings_checker_accepts_a_native_build_with_no_bindings_file(tmp_path: Path) -> None:
    """What the 2026-09-11 eval actually produced. A pure Data Fabric flow
    references no packaged resource, so the CLI writes no bindings file at all,
    and both native billing tasks died on `assert candidates` one line before the
    connection check could apply. The fixture that supplied an empty-of-
    connections file did not reproduce this: that shape never occurs."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / "BillingInvoiceLookup.flow").write_text(json.dumps(_native_flow()))

    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no bindings file, and no connector node that needs one" in result.stdout


def test_bindings_checker_requires_a_file_for_a_connector_build(tmp_path: Path) -> None:
    """The other half: a connector flow with no bindings file at all is the
    missing-connection regression, not a native build."""
    project = tmp_path / "proj"
    project.mkdir()
    flow = json.loads((FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]).read_text())
    (project / "BillingInvoiceLookup.flow").write_text(json.dumps(flow))

    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode != 0
    assert "carries a connector node that needs one" in result.stdout + result.stderr


def test_bindings_checker_fails_when_it_finds_no_flow(tmp_path: Path) -> None:
    """Relaxing the bindings-file requirement must not let a checker that ran in
    the wrong tree report success on an empty directory."""
    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode != 0
    assert "neither a generated bindings file nor a .flow" in result.stdout + result.stderr


def test_bindings_checker_still_requires_one_for_a_connector_build(tmp_path: Path) -> None:
    """The regression the check exists for: a connector build that dropped its
    connection row deploys and faults with [102010]."""
    flow = json.loads((FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]).read_text())
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingInvoiceLookup")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode != 0
    assert "declares no bindings at all" in result.stdout + result.stderr


def test_bindings_checker_rejects_a_stub_connection_on_a_native_build(tmp_path: Path) -> None:
    """Zero connection rows is fine; a row that is there and wrong is not."""
    stub = json.loads(json.dumps(CONNECTION_BINDINGS))
    stub["resources"][0]["value"]["ConnectionId"]["defaultValue"] = "00000000-0000-0000-0000-000000000001"
    cwd = _project(tmp_path, _native_flow(), stub, "BillingDisputeResolution")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode != 0
    assert "stub or empty bindings" in result.stdout + result.stderr


def test_server_side_filter_accepts_native_rows(tmp_path: Path) -> None:
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    cwd = _project(tmp_path, _native_flow(), NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_server_side_filter_rejects_an_empty_native_filter(tmp_path: Path) -> None:
    """The `_filters` container is always present, so its emptiness is what
    separates a server-side filter from fetching the entity whole."""
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    flow = _native_flow()
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_filters"] = {"logicalOperator": "AND", "rows": [], "groups": []}
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode != 0
    assert "no server-side filter" in result.stdout + result.stderr


def test_billing_advisories_use_the_shared_entity_read_discriminator() -> None:
    """The tests above exercise the helpers, not the call sites. Without this,
    reverting any advisory to the connector-only prefix keeps the suite green on
    its connector reference and silently restores the 2026-09-11 failure."""
    for script in (
        "advisory_billing_invoice_lookup.py",
        "advisory_billing_discrepancy_detector.py",
        "advisory_billing_dispute_resolution.py",
    ):
        source = (SHARED / script).read_text(encoding="utf-8")
        assert "entity_reads(nodes)" in source, script


def test_literal_scan_ignores_canvas_descriptions_and_uuid_segments(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_discrepancy_detector.py"]
    flow = json.loads(source.read_text())
    flow["nodes"][0]["position"] = {"x": 1610, "y": 4200}
    flow["nodes"][0]["description"] = "Enterprise-tier customers"
    for node in flow["nodes"]:
        detail = (node.get("inputs") or {}).get("detail")
        if detail:
            detail["connectionId"] = "3f2a91cc-1610-4b7e-a111-123456789abc"
    target = tmp_path / "BillingDiscrepancyDetector.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_discrepancy_detector.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_multi_end_error_binding_does_not_override_success_binding(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_resolution_writer.py"]
    flow = json.loads(source.read_text())
    flow["nodes"].append(
        {
            "id": "errorEnd",
            "type": "core.control.end",
            "outputs": {"emailSubject": "failed", "emailBody": "failed"},
        }
    )
    flow["edges"].append(
        {
            "sourceNodeId": "resolutionWriter",
            "sourcePort": "error",
            "targetNodeId": "errorEnd",
            "targetPort": "input",
        }
    )
    target = tmp_path / "BillingResolutionWriter.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_resolution_writer.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_output_provenance_follows_multiple_reader_hops(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]
    flow = json.loads(source.read_text())
    end = next(node for node in flow["nodes"] if node.get("type") == "core.control.end")
    flow["nodes"].extend(
        [
            {"id": "format1", "type": "core.action.script", "inputs": {"value": "$vars.erpQuery.output"}},
            {"id": "format2", "type": "core.action.script", "inputs": {"value": "$vars.format1.output"}},
        ]
    )
    for output in end["outputs"].values():
        output["source"] = {
            "type": "jsExpression",
            "expression": "$vars.format2.output.value",
            "fieldType": "string",
        }
    flow["edges"] = [
        edge
        for edge in flow["edges"]
        if not (edge.get("sourceNodeId") == "erpQuery" and edge.get("targetNodeId") == end["id"])
    ]
    flow["edges"].extend(
        [
            {"sourceNodeId": "erpQuery", "sourcePort": "success", "targetNodeId": "format1"},
            {"sourceNodeId": "format1", "sourcePort": "success", "targetNodeId": "format2"},
            {"sourceNodeId": "format2", "sourcePort": "success", "targetNodeId": end["id"]},
        ]
    )
    target = tmp_path / "BillingInvoiceLookup.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_bindings_checker_uses_relative_exclusions_and_rejects_any_bad_key(tmp_path: Path) -> None:
    cwd = tmp_path / "sdk"
    project = cwd / "project"
    project.mkdir(parents=True)
    bindings = project / "bindings.json"
    bindings.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "id": "connection",
                        "resource": "connection",
                        "resourceKey": "DataFabricConn",
                        "default": "00000000-0000-0000-0000-000000000001",
                    }
                ]
            }
        )
    )
    bad = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert bad.returncode != 0
    assert "connection" in bad.stdout + bad.stderr

    bindings.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "id": "connection",
                        "resource": "connection",
                        "resourceKey": "d61e5d0e-04af-4f93-95cc-151d81fa08dc",
                        "default": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c",
                    }
                ]
            }
        )
    )
    good = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert good.returncode == 0, good.stdout + good.stderr


def test_bindings_checker_accepts_v2_symbolic_key_with_real_values(tmp_path: Path) -> None:
    bindings = tmp_path / "bindings_v2.json"
    bindings.write_text(
        json.dumps(
            {
                "resources": [
                    {
                        "resource": "connection",
                        "key": "data-fabric",
                        "value": {
                            "ConnectionId": {"defaultValue": "d61e5d0e-04af-4f93-95cc-151d81fa08dc"},
                            "FolderKey": {"defaultValue": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c"},
                        },
                    }
                ]
            }
        )
    )
    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_bindings_checker_prefers_solution_flow_over_root_scratch(tmp_path: Path) -> None:
    checker = FLOW_TASKS / "bindings" / "check_bindings.py"
    project = tmp_path / "BindingsMulti" / "BindingsMulti"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    good = {"nodes": [], "bindings": []}
    (project / "BindingsMulti.flow").write_text(json.dumps(good))
    (tmp_path / "BindingsMulti.flow").write_text(json.dumps({"nodes": []}))

    result = subprocess.run(
        [sys.executable, str(checker), "structure", "**/BindingsMulti*.flow"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert str(project.relative_to(tmp_path)) in result.stdout


def test_inline_agent_ignores_staging_trees(tmp_path: Path) -> None:
    valid = {
        "settings": {"model": "gpt-4.1"},
        "messages": [{"role": "system", "content": "A sufficiently detailed production system prompt for this agent."}],
        "outputSchema": {"properties": {"result": {"type": "string"}}},
    }
    real = tmp_path / "Solution" / "Flow" / "agent-id" / "agent.json"
    real.parent.mkdir(parents=True)
    real.write_text(json.dumps(valid))
    for stale_root in (tmp_path / ".agent-builder", tmp_path / "_outputs"):
        stale_root.mkdir()
        (stale_root / "agent.json").write_text("{}")

    result = run_script("check_inline_agent.py", "**/agent.json", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Solution" in result.stdout


def test_inline_agent_scoped_checks_preserve_artifact_outcomes(tmp_path: Path) -> None:
    agent = tmp_path / "agent-id" / "agent.json"
    agent.parent.mkdir()
    agent.write_text(json.dumps({"settings": {"model": "gpt-4.1"}}))

    exists = run_script(
        "check_inline_agent.py", "--check", "exists", "**/agent.json", cwd=tmp_path
    )
    model = run_script(
        "check_inline_agent.py", "--check", "model", "**/agent.json", cwd=tmp_path
    )

    assert exists.returncode == 0, exists.stdout + exists.stderr
    assert model.returncode == 0, model.stdout + model.stderr


def test_inline_agent_model_scope_rejects_scaffold_default(tmp_path: Path) -> None:
    agent = tmp_path / "agent-id" / "agent.json"
    agent.parent.mkdir()
    agent.write_text(json.dumps({"settings": {"model": "gpt-4o-2024-11-20"}}))

    result = run_script(
        "check_inline_agent.py", "--check", "model", "**/agent.json", cwd=tmp_path
    )

    assert result.returncode != 0
    assert "not overridden" in result.stdout


def test_reachability_excludes_the_loop_back_edge() -> None:
    """A loop body must not reach the End nodes that follow the loop.

    The back edge from the last body node into the loop container closes a
    cycle, so a naive walk would go body -> loop -> after -> end. Excluding it
    is the whole point of the filter in `successful_end_ids`, and it keyed off
    `loopBack` — a handle `core.logic.loop` has never declared and that
    `flow validate` rejects. The real inner target handles are `continue` and
    `break`, so the filter never fired on any valid flow.
    """
    sys.path.insert(0, str(SHARED))
    from advisory_flow_utils import LOOP_BACK_PORTS, successful_end_ids

    assert {"continue", "break"} <= LOOP_BACK_PORTS

    nodes = [
        {"id": "loop1", "type": "core.logic.loop"},
        {"id": "body", "type": "core.action.script"},
        {"id": "after", "type": "core.action.script"},
        {"id": "end1", "type": "core.control.end"},
    ]
    edges = [
        {"sourceNodeId": "loop1", "sourcePort": "start", "targetNodeId": "body", "targetPort": "input"},
        {"sourceNodeId": "body", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "continue"},
        {"sourceNodeId": "loop1", "sourcePort": "success", "targetNodeId": "after", "targetPort": "input"},
        {"sourceNodeId": "after", "sourcePort": "success", "targetNodeId": "end1", "targetPort": "input"},
    ]

    assert successful_end_ids(nodes, edges, "body") == set()
    assert successful_end_ids(nodes, edges, "loop1") == {"end1"}


def test_reachability_excludes_the_loop_break_edge() -> None:
    """`break` is the other inner target handle and closes the same cycle."""
    sys.path.insert(0, str(SHARED))
    from advisory_flow_utils import successful_end_ids

    nodes = [
        {"id": "loop1", "type": "core.logic.loop"},
        {"id": "body", "type": "core.action.script"},
        {"id": "end1", "type": "core.control.end"},
    ]
    edges = [
        {"sourceNodeId": "loop1", "sourcePort": "start", "targetNodeId": "body", "targetPort": "input"},
        {"sourceNodeId": "body", "sourcePort": "success", "targetNodeId": "loop1", "targetPort": "break"},
        {"sourceNodeId": "loop1", "sourcePort": "success", "targetNodeId": "end1", "targetPort": "input"},
    ]

    assert successful_end_ids(nodes, edges, "body") == set()


def test_resolution_writer_advisory_accepts_connector_mode_http_proxy(tmp_path: Path) -> None:
    """The Slack contract also accepts a connector-mode HTTP proxy send node, not
    only the native connector node. Exercises the previously-unexercised proxy
    branch of ``is_slack_send`` — where an unimported ``json`` once hid — because
    the parametrized reference case feeds only the native-node flow."""
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_resolution_writer.py"]
    flow = json.loads(source.read_text())
    slack = next(n for n in flow["nodes"] if n["id"] == "postResolution")
    slack["type"] = "core.action.http.v2"
    slack["inputs"] = {
        "detail": {
            "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
            "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
            "method": "POST",
            "endpoint": "/send_message_to_channel_v2",
            "queryParameters": {"send_as": "user"},
            "bodyParameters": {
                "authentication": "connector",
                "targetConnector": "uipath-salesforce-slack",
                "channel": "C0B2FDZD1M3",
                "messageToSend": "=js:`${$vars.start.output.correlationId}: ${$vars.resolutionWriter.output.body}`",
            },
        }
    }
    target = tmp_path / "BillingResolutionWriter.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_resolution_writer.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_resolution_writer_advisory_rejects_proxy_send_without_bound_connection(tmp_path: Path) -> None:
    """A connector-mode HTTP proxy with no bound connection must be refused — it
    passes an ids-only shape check but the live rung's assert_slack_message_posted
    rejects it ("no connected send node found")."""
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_resolution_writer.py"]
    flow = json.loads(source.read_text())
    slack = next(n for n in flow["nodes"] if n["id"] == "postResolution")
    slack["type"] = "core.action.http.v2"
    slack["inputs"] = {
        "detail": {
            "method": "POST",
            "endpoint": "/send_message_to_channel_v2",
            "queryParameters": {"send_as": "user"},
            "bodyParameters": {
                "authentication": "connector",
                "targetConnector": "uipath-salesforce-slack",
                "channel": "C0B2FDZD1M3",
                "messageToSend": "=js:`${$vars.start.output.correlationId}: ${$vars.resolutionWriter.output.body}`",
            },
        }
    }
    target = tmp_path / "BillingResolutionWriter.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_resolution_writer.py", target)
    assert result.returncode != 0
    assert "Slack" in (result.stdout + result.stderr)


def test_managed_http_v2_counts_as_raw_http(tmp_path: Path) -> None:
    """The guide steers URL calls to `core.action.http.v2`; an exact-type match
    on `core.action.http` lets that bypass through."""

    def mutate(flow: dict) -> None:
        flow["nodes"].append({"id": "rawHttp", "type": "core.action.http.v2"})

    result = _run_invoice_connector(tmp_path, mutate)
    assert result.returncode != 0
    assert "raw HTTP" in result.stdout + result.stderr
