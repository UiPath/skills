"""Unit tests for ``check_extract_document.py``.

The CLI is faked at :func:`check_extract_document.uip` with envelopes shaped
like ``uip maestro flow ... --output json`` returns them, so nothing here needs
``uip`` on PATH. The ``uip`` wrapper itself is tested by faking
``subprocess.run``.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_extract_document as ced  # noqa: E402
from check_extract_document import main  # noqa: E402

NODE_ID = "extractInvoice1"
ALL_DEFS = {t: {} for t in ced.BUILT_IN_TYPES}


def _field(ref, description="Read it from the page."):
    return {"$ref": f"#/$defs/{ref}", "description": description}


def _schema(groups=None, prompt="Extract the invoice.", defs=None):
    if groups is None:
        groups = {
            "Invoice": {
                "description": "The invoice header.",
                "properties": {
                    "Vendor Name": _field("ft-inferred-text"),
                    "Invoice Number": _field("ft-exact-text", "Drop the No. prefix."),
                    "Invoice Date": _field("ft-date"),
                    "Total": _field("ft-monetary-quantity"),
                },
            },
            "Line Items": {
                "description": "One row per line.",
                "type": ["array", "null"],
                "items": {"properties": {"Quantity": _field("ft-number")}},
            },
        }
    return {
        "prompt": prompt,
        "outputSchema": {"properties": groups, "$defs": ALL_DEFS if defs is None else defs},
    }


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    proj = tmp_path / "InvoiceFieldsSolution" / "InvoiceFields"
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (proj / "InvoiceFields.flow").write_text(json.dumps({"nodes": [], "edges": []}))
    monkeypatch.chdir(tmp_path)
    return proj


def _stub(monkeypatch, *, nodes=None, schema=None, edges=None, variables=None, validate=None):
    """Answer each ``uip`` call from canned ``Data`` (an Exception is raised)."""
    nodes = nodes if nodes is not None else [
        {"Id": "start", "Type": "core.trigger.manual", "Label": "Manual trigger"},
        {"Id": NODE_ID, "Type": ced.EXTRACT_NODE_TYPE, "Label": "Extract Invoice Fields"},
    ]
    answers = {
        ("nodes", "list"): {"Nodes": nodes, "Count": len(nodes)},
        ("nodes", "schema"): {"NodeId": NODE_ID, "Schema": schema or _schema(), "HasDraft": False},
        ("edges", "list"): {"Edges": edges if edges is not None else [
            {"Source": "start:output", "Target": f"{NODE_ID}:input"}
        ]},
        ("variables", "list"): {"Variables": variables if variables is not None else [
            {"Id": "invoice", "Type": "file", "Direction": "in", "TriggerNodeId": "start"},
            {"Id": "start.output", "Type": "object", "NodeId": "start", "OutputId": "output"},
        ]},
        ("validate",): validate if validate is not None else {"Status": "Valid"},
    }

    def fake(*args, timeout=60):
        rest = args[2:]
        for key, data in answers.items():
            if rest[: len(key)] == key:
                if isinstance(data, Exception):
                    raise data
                return data
        raise AssertionError(f"unexpected uip call: {args}")

    monkeypatch.setattr(ced, "uip", fake)


# --- fields ---------------------------------------------------------------


def _fields(*entries):
    return ["--flow", "InvoiceFields", "fields", json.dumps(list(entries))]


STRAY_DATE = {"G": {"description": "d", "properties": {
    "Invoice Date": _field("ft-inferred-text"),
    "Due Date": _field("ft-date"),
    "Vendor Name": _field("ft-inferred-text", "Drop the No. prefix."),
    "Invoice Number": _field("ft-exact-text"),
}}}


def test_fields_pass_when_every_entry_fits_a_field(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(_fields(
        {"name": "vendor"},
        {"name": "number", "type": "ft-exact-text", "says": "prefix"},
        {"name": "invoice date", "type": "ft-date"},
        {"name": "total", "type": "ft-monetary-quantity", "says": "page"},
        {"name": "QUANT|qty", "type": "ft-number"},
    )) == 0
    assert "OK: fields" in capsys.readouterr().out


@pytest.mark.parametrize("entry", [{"type": "ft-boolean"}, {"says": "IBAN"}, {"name": "iban"}])
def test_any_single_key_is_checked(sandbox, monkeypatch, entry):
    _stub(monkeypatch)
    assert main(_fields(entry)) == 1


def test_type_is_checked_on_the_named_field(sandbox, monkeypatch, capsys):
    _stub(monkeypatch, schema=_schema(STRAY_DATE))
    assert main(_fields({"type": "ft-date"})) == 0
    assert main(_fields({"name": "invoice date", "type": "ft-date"})) == 1
    err = capsys.readouterr().err
    assert 'no field fits {"name": "invoice date", "type": "ft-date"}' in err
    assert "'G > Invoice Date' ft-inferred-text" in err


def test_instructions_are_checked_on_the_named_field(sandbox, monkeypatch):
    _stub(monkeypatch, schema=_schema(STRAY_DATE))
    assert main(_fields({"says": "prefix"})) == 0
    assert main(_fields({"name": "number", "says": "prefix"})) == 1


def test_every_missing_entry_is_reported(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(_fields({"name": "vendor"}, {"name": "iban"}, {"type": "ft-boolean"})) == 1
    err = capsys.readouterr().err
    assert '"iban"' in err and '"ft-boolean"' in err and '"vendor"' not in err
    assert "Line Items > Quantity" in err


def test_one_field_cannot_answer_two_entries(sandbox, monkeypatch, capsys):
    groups = {"G": {"description": "d", "properties": {"Vendor Number": _field("ft-exact-text")}}}
    _stub(monkeypatch, schema=_schema(groups))
    assert main(_fields({"name": "vendor"}, {"name": "number"})) == 1
    assert "fits only ['G > Vendor Number'], already used" in capsys.readouterr().err


def test_pairing_is_not_greedy(sandbox, monkeypatch):
    groups = {"G": {"description": "d", "properties": {
        "Invoice Number": _field("ft-exact-text"),
        "Invoice Date": _field("ft-date"),
    }}}
    _stub(monkeypatch, schema=_schema(groups))
    assert main(_fields({"name": "invoice"}, {"name": "number"})) == 0


def test_id_is_checked_on_the_named_field(sandbox, monkeypatch, capsys):
    groups = {"Invoice": {"description": "d", "properties": {
        "Total Amount": {**_field("ft-monetary-quantity"), "x-uipath-field-id": "id-total"},
        "Vendor Name": {**_field("ft-inferred-text"), "x-uipath-field-id": "id-vendor"},
    }}}
    _stub(monkeypatch, schema=_schema(groups))
    assert main(_fields({"name": "^Total Amount$", "id": "id-total"})) == 0
    assert main(_fields({"name": "^Total Amount$", "id": "id-vendor"})) == 1
    assert "'Invoice > Total Amount' ft-monetary-quantity id id-total" in capsys.readouterr().err


def test_group_and_repeats_place_the_field(sandbox, monkeypatch):
    _stub(monkeypatch)
    assert main(_fields({"name": "quant", "repeats": True, "group": "line"})) == 0
    assert main(_fields({"name": "vendor", "repeats": False, "group": "^Invoice$"})) == 0
    assert main(_fields({"name": "quant", "repeats": False})) == 1
    assert main(_fields({"name": "vendor", "repeats": True})) == 1
    assert main(_fields({"name": "vendor", "group": "line"})) == 1


def test_only_fails_on_a_field_no_entry_asks_for(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    every = [{"name": n} for n in ("vendor", "number", "date", "total", "quantity")]
    assert main(["--flow", "InvoiceFields", "fields", "--only", json.dumps(every)]) == 0
    assert main(["--flow", "InvoiceFields", "fields", "--only", json.dumps(every[:4])]) == 1
    assert "'Line Items > Quantity' is a field no entry asks for" in capsys.readouterr().err


@pytest.mark.parametrize("value", [
    "vendor", "[]", "{}", "[{}]", '[{"label": "x"}]', '[{"name": 1}]', '[{"name": "("}]',
    '[{"repeats": "yes"}]', '[{"id": true}]', '[{"group": "["}]',
])
def test_malformed_fields_value_is_a_usage_error(sandbox, value):
    assert main(["--flow", "InvoiceFields", "fields", value]) == 2


def test_fields_takes_one_value(sandbox):
    assert main(["--flow", "InvoiceFields", "fields", '[{"name": "a"}]', '[{"name": "b"}]']) == 2


# --- described, defs -------------------------------------------------------


def test_described_names_each_gap(sandbox, monkeypatch, capsys):
    groups = {"G": {"properties": {"Total": {"$ref": "#/$defs/ft-number"}}}}
    _stub(monkeypatch, schema=_schema(groups, prompt=""))
    assert main(["--flow", "InvoiceFields", "described"]) == 1
    err = capsys.readouterr().err
    assert "overall prompt is empty" in err
    assert "group 'G' has no description" in err
    assert "field 'G > Total' has no description" in err


def test_defs(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "defs"]) == 0
    _stub(monkeypatch, schema=_schema(defs={"ft-date": {}}))
    assert main(["--flow", "InvoiceFields", "defs"]) == 1
    assert "$defs is missing ft-boolean" in capsys.readouterr().err


def test_defs_only_refuses_any_other_type(sandbox, monkeypatch, capsys):
    _stub(monkeypatch, schema=_schema(defs={**ALL_DEFS, "ft-text": {}}))
    assert main(["--flow", "InvoiceFields", "defs"]) == 0
    assert main(["--flow", "InvoiceFields", "defs", "--only"]) == 1
    assert "$defs also has ft-text" in capsys.readouterr().err


def test_only_applies_to_fields_and_defs(sandbox):
    assert main(["--flow", "InvoiceFields", "label", "--only"]) == 2


# --- node, edges, label ---------------------------------------------------


def test_no_extract_node_names_the_types_found(sandbox, monkeypatch, capsys):
    _stub(monkeypatch, nodes=[{"Id": "start", "Type": "core.trigger.manual"}])
    assert main(["--flow", "InvoiceFields", "described"]) == 1
    assert "no Extract document node" in capsys.readouterr().err


def test_node(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "node"]) == 0
    _stub(monkeypatch, nodes=[{"Id": "start", "Type": "core.trigger.manual"}])
    assert main(["--flow", "InvoiceFields", "node"]) == 1
    assert "(node types: core.trigger.manual)" in capsys.readouterr().err


def _stub_each_flow(monkeypatch, nodes_by_flow):
    """Answer ``nodes list`` per flow file name."""
    def fake(*args, timeout=60):
        assert args[2:4] == ("nodes", "list"), args
        return {"Nodes": nodes_by_flow[os.path.basename(args[4])]}
    monkeypatch.setattr(ced, "uip", fake)


def test_no_node_passes_when_nothing_was_built(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["no-node"]) == 0
    assert "no .flow in the sandbox" in capsys.readouterr().out


def test_no_node_passes_on_flows_without_the_node(sandbox, monkeypatch):
    _stub_each_flow(monkeypatch, {"InvoiceFields.flow": [{"Id": "mock1", "Type": "core.logic.mock"}]})
    assert main(["no-node"]) == 0


def test_no_node_reads_every_flow_whatever_its_name(sandbox, monkeypatch, capsys):
    (sandbox.parent.parent / "Scratch.flow").write_text("{}")
    _stub_each_flow(monkeypatch, {
        "InvoiceFields.flow": [{"Id": "start", "Type": "core.trigger.manual"}],
        "Scratch.flow": [{"Id": NODE_ID, "Type": ced.EXTRACT_NODE_TYPE}],
    })
    assert main(["no-node"]) == 1
    assert f"Scratch.flow holds {NODE_ID}, an Extract document node" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["--flow", "InvoiceFields", "no-node"], ["described"]])
def test_flow_is_given_to_every_check_but_no_node(sandbox, argv):
    assert main(argv) == 2


@pytest.mark.parametrize("other", ["uipath.ixp.invoices.1-shared", "uipath.ixp.processor.abc", ced.EXTRACT_NODE_TYPE])
def test_no_other_ixp_node(sandbox, monkeypatch, capsys, other):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "no-other-ixp"]) == 0
    _stub(monkeypatch, nodes=[
        {"Id": NODE_ID, "Type": ced.EXTRACT_NODE_TYPE, "Label": "Extract Invoice Fields"},
        {"Id": "other1", "Type": other, "Label": "Other"},
    ])
    assert main(["--flow", "InvoiceFields", "no-other-ixp"]) == 1
    assert f"other1 is a {other} node" in capsys.readouterr().err


# --- file-ref -------------------------------------------------------------


def _write_inputs(sandbox, inputs):
    node = {"id": NODE_ID, "type": ced.EXTRACT_NODE_TYPE, "inputs": inputs}
    (sandbox / "InvoiceFields.flow").write_text(json.dumps({"nodes": [node], "edges": []}))


@pytest.mark.parametrize("file_ref", [
    "=js:$vars.start.output.invoice",
    {"type": "jsExpression", "expression": "$vars.start.output.invoice", "fieldType": "object"},
])
def test_file_ref_reads_a_declared_file_input(sandbox, monkeypatch, file_ref):
    _stub(monkeypatch)
    _write_inputs(sandbox, {"fileRef": file_ref})
    assert main(["--flow", "InvoiceFields", "file-ref"]) == 0


@pytest.mark.parametrize("file_ref", [
    "=js:$vars.start.output.document", "invoice.pdf", {"type": "literal", "value": "$vars.start.output.invoice"},
])
def test_file_ref_to_anything_else_fails(sandbox, monkeypatch, capsys, file_ref):
    _stub(monkeypatch)
    _write_inputs(sandbox, {"fileRef": file_ref})
    assert main(["--flow", "InvoiceFields", "file-ref"]) == 1
    assert "file inputs: $vars.start.output.invoice" in capsys.readouterr().err


def test_file_ref_needs_the_input_declared_as_a_file(sandbox, monkeypatch, capsys):
    _stub(monkeypatch, variables=[{"Id": "invoice", "Type": "object", "Direction": "in", "TriggerNodeId": "start"}])
    _write_inputs(sandbox, {"fileRef": "=js:$vars.start.output.invoice"})
    assert main(["--flow", "InvoiceFields", "file-ref"]) == 1
    assert "file inputs: none" in capsys.readouterr().err


def test_missing_file_ref(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    _write_inputs(sandbox, {})
    assert main(["--flow", "InvoiceFields", "file-ref"]) == 1
    assert f"{NODE_ID} has no inputs.fileRef" in capsys.readouterr().err


def test_edge_in_and_out(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "edge", "in", "input"]) == 0
    assert main(["--flow", "InvoiceFields", "edge", "out", "error"]) == 1
    assert f"no edge out of {NODE_ID}:error" in capsys.readouterr().err


def test_edge_needs_direction_and_port(sandbox, monkeypatch):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "edge", "input"]) == 1


@pytest.mark.parametrize("label", ["Extract document", "extract", "", "  "])
def test_default_or_empty_label_fails(sandbox, monkeypatch, label):
    _stub(monkeypatch, nodes=[{"Id": NODE_ID, "Type": ced.EXTRACT_NODE_TYPE, "Label": label}])
    assert main(["--flow", "InvoiceFields", "label"]) == 1


def test_descriptive_label_passes(sandbox, monkeypatch):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "label"]) == 0


# --- file checks ----------------------------------------------------------


def test_no_model(sandbox, monkeypatch, capsys):
    assert main(["--flow", "InvoiceFields", "no-model"]) == 0
    (sandbox / "InvoiceFields.flow").write_text('{"modelName": "Invoices", "folderKey": ""}')
    assert main(["--flow", "InvoiceFields", "no-model"]) == 1
    err = capsys.readouterr().err
    assert "sets modelName" in err and "folderKey" not in err


def test_no_sdk(sandbox):
    assert main(["--flow", "InvoiceFields", "no-sdk"]) == 0
    (sandbox / ".flow-sdk").mkdir()
    assert main(["--flow", "InvoiceFields", "no-sdk"]) == 1


def test_missing_flow_lists_what_was_found(sandbox, capsys):
    assert main(["--flow", "Other", "no-sdk"]) == 1
    assert "no discovered .flow file is named Other.flow" in capsys.readouterr().err


# --- validate -------------------------------------------------------------


def test_validate(sandbox, monkeypatch, capsys):
    _stub(monkeypatch)
    assert main(["--flow", "InvoiceFields", "validate"]) == 0
    # validate prints its warnings as one string, not a list
    _stub(monkeypatch, validate={"Status": "Valid", "Warnings": (
        "1 warning(s):\n  - [nodes[extractInvoice1].inputs.fileRef] [EXPRESSION_DIAGNOSTIC] "
        "Property 'invoce' does not exist on type '{ invoice: File; }'."
    )})
    assert main(["--flow", "InvoiceFields", "validate"]) == 1
    assert "EXPRESSION_DIAGNOSTIC" in capsys.readouterr().err


def test_validate_failure_reports_the_cli_errors(sandbox, monkeypatch, capsys):
    _stub(monkeypatch, validate=ced.CheckError("uip maestro flow validate failed: Edge references ghost"))
    assert main(["--flow", "InvoiceFields", "validate"]) == 1
    assert "Edge references ghost" in capsys.readouterr().err


# --- arguments ------------------------------------------------------------


def test_check_values_are_enforced(sandbox):
    assert main(["--flow", "InvoiceFields", "described", "extra"]) == 2
    assert main(["--flow", "InvoiceFields", "fields"]) == 2


# --- the uip wrapper ------------------------------------------------------


def _fake_run(monkeypatch, stdout, returncode=0):
    monkeypatch.setattr(ced.shutil, "which", lambda _: "/usr/bin/uip")
    monkeypatch.setattr(
        ced.subprocess, "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, returncode, stdout, ""),
    )


def test_uip_returns_data(monkeypatch):
    _fake_run(monkeypatch, json.dumps({"Result": "Success", "Data": {"Nodes": []}}))
    assert ced.uip("maestro", "flow", "nodes", "list", "a.flow") == {"Nodes": []}


def test_uip_failure_carries_message_and_instructions(monkeypatch):
    _fake_run(monkeypatch, json.dumps({
        "Result": "Failure",
        "Message": 'Node not found: "x".',
        "Instructions": "Run 'uip maestro flow nodes list <file>'.",
    }), returncode=1)
    with pytest.raises(ced.CheckError, match=r'Node not found: "x"\. Run'):
        ced.uip("maestro", "flow", "nodes", "schema", "get", "a.flow", "--node-id", "x")


def test_uip_without_json(monkeypatch):
    _fake_run(monkeypatch, "error: unknown command 'schema'", returncode=3)
    with pytest.raises(ced.CheckError, match="printed no JSON"):
        ced.uip("maestro", "flow", "nodes", "schema", "get", "a.flow")


def test_uip_not_on_path(monkeypatch):
    monkeypatch.setattr(ced.shutil, "which", lambda _: None)
    with pytest.raises(ced.CheckError, match="not on PATH"):
        ced.uip("maestro", "flow", "validate", "a.flow")
