"""Unit tests for ``check_extract_document.py``, on ``.flow`` files written to a tmp sandbox."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_extract_document import BUILT_IN_TYPES, EXTRACT_NODE_TYPE, main  # noqa: E402

NODE_ID = "extractInvoice1"
FILE_INPUT = {"id": "invoice", "direction": "in", "type": "file", "triggerNodeId": "start"}
ALL_DEFS = {t: {} for t in BUILT_IN_TYPES}


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
    return {"prompt": prompt, "outputSchema": {"properties": groups, "$defs": ALL_DEFS if defs is None else defs}}


def _flow(file_ref="=js:$vars.start.output.invoice", globals_=(FILE_INPUT,), extra_nodes=(), edges=None, schema=None):
    inputs = {"fileRef": file_ref, "schemaDocument": _schema() if schema is None else schema}
    nodes = [
        {"id": "start", "type": "core.trigger.manual"},
        {"id": NODE_ID, "type": EXTRACT_NODE_TYPE, "inputs": inputs},
        *extra_nodes,
    ]
    if edges is None:
        edges = [{"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": NODE_ID, "targetPort": "input"}]
    return {"nodes": nodes, "edges": edges, "variables": {"globals": list(globals_)}}


@pytest.fixture()
def write(tmp_path, monkeypatch):
    proj = tmp_path / "InvoiceReaderSolution" / "InvoiceReader"
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    monkeypatch.chdir(tmp_path)
    return lambda flow: (proj / "InvoiceReader.flow").write_text(json.dumps(flow))


def _run(*args):
    return main(["--flow-name", "InvoiceReader", *args])


def test_file_ref_to_a_declared_input_passes(write):
    write(_flow())
    assert _run("file-ref") == 0


def test_file_ref_as_js_expression_object_passes(write):
    write(_flow(file_ref={"type": "jsExpression", "expression": "$vars.start.output.invoice"}))
    assert _run("file-ref") == 0


@pytest.mark.parametrize(
    "file_ref, globals_",
    [
        ("=js:$vars.start.output.invoice", ()),
        ("=js:$vars.start.output.invoce", (FILE_INPUT,)),
        ("=js:$vars.start.output.invoice", ({**FILE_INPUT, "type": "string"},)),
        (None, (FILE_INPUT,)),
    ],
    ids=["undeclared", "typo", "not-a-file", "missing"],
)
def test_file_ref_to_no_declared_file_input_fails(write, capsys, file_ref, globals_):
    write(_flow(file_ref=file_ref, globals_=globals_))
    assert _run("file-ref") == 1
    assert "reads no declared file input" in capsys.readouterr().err


def test_edge_in_passes_on_the_named_port(write):
    write(_flow())
    assert _run("edge", "in", "input") == 0
    assert _run("edge", "out", "output") == 1


def test_unwired_node_fails_edge_in(write, capsys):
    write(_flow(edges=[]))
    assert _run("edge", "in", "input") == 1
    assert f"no edge into {NODE_ID}:input (edges: none)" in capsys.readouterr().err


@pytest.mark.parametrize("values", [("sideways", "input"), ("in",), ()])
def test_edge_with_bad_values_is_a_usage_error(write, values):
    write(_flow())
    assert _run("edge", *values) == 2


def test_no_other_ixp_fails_on_a_published_model_node(write, capsys):
    write(_flow(extra_nodes=[{"id": "invoiceModel", "type": "uipath.ixp.invoices"}]))
    assert _run("no-other-ixp") == 1
    assert "invoiceModel (uipath.ixp.invoices)" in capsys.readouterr().err


def test_no_other_ixp_fails_on_a_second_extract_document_node(write):
    write(_flow(extra_nodes=[{"id": "extractInvoice2", "type": EXTRACT_NODE_TYPE}]))
    assert _run("no-other-ixp") == 1


def test_lone_extract_document_node_passes_no_other_ixp(write):
    write(_flow())
    assert _run("no-other-ixp") == 0


def test_flow_without_the_node_fails_every_check(write, capsys):
    write({"nodes": [{"id": "start", "type": "core.trigger.manual"}], "edges": []})
    assert _run("file-ref") == 1
    assert "no Extract document node" in capsys.readouterr().err


def test_other_flow_name_fails(write, capsys):
    write(_flow())
    assert main(["--flow-name", "Other", "file-ref"]) == 1
    assert "no discovered .flow file is named Other.flow" in capsys.readouterr().err


def _fields(*entries, only=False):
    return _run("fields", *(["--only"] if only else []), json.dumps(list(entries)))


STRAY_DATE = {"G": {"description": "d", "properties": {
    "Invoice Date": _field("ft-inferred-text"),
    "Due Date": _field("ft-date"),
    "Vendor Name": _field("ft-inferred-text", "Drop the No. prefix."),
    "Invoice Number": _field("ft-exact-text"),
}}}


def test_fields_pass_when_every_entry_fits_a_field(write, capsys):
    write(_flow())
    assert _fields(
        {"name": "vendor"},
        {"name": "number", "type": "ft-exact-text", "says": "prefix"},
        {"name": "invoice date", "type": "ft-date"},
        {"name": "total", "type": "ft-monetary-quantity", "says": "page"},
        {"name": "QUANT|qty", "type": "ft-number"},
    ) == 0
    assert "OK: fields" in capsys.readouterr().out


@pytest.mark.parametrize("entry", [{"type": "ft-boolean"}, {"says": "IBAN"}, {"name": "iban"}])
def test_any_single_key_is_checked(write, entry):
    write(_flow())
    assert _fields(entry) == 1


def test_type_and_instructions_are_checked_on_the_named_field(write, capsys):
    write(_flow(schema=_schema(STRAY_DATE)))
    assert _fields({"type": "ft-date"}) == 0
    assert _fields({"says": "prefix"}) == 0
    assert _fields({"name": "number", "says": "prefix"}) == 1
    assert _fields({"name": "invoice date", "type": "ft-date"}) == 1
    err = capsys.readouterr().err
    assert 'no field fits {"name": "invoice date", "type": "ft-date"}' in err
    assert "'G > Invoice Date' ft-inferred-text" in err


def test_every_missing_entry_is_reported(write, capsys):
    write(_flow())
    assert _fields({"name": "vendor"}, {"name": "iban"}, {"type": "ft-boolean"}) == 1
    err = capsys.readouterr().err
    assert '"iban"' in err and '"ft-boolean"' in err and 'fits {"name": "vendor"}' not in err
    assert "Line Items > Quantity" in err


def test_id_is_checked_on_the_named_field(write, capsys):
    write(_flow(schema=_schema({"Invoice": {"description": "d", "properties": {
        "Total Amount": {**_field("ft-monetary-quantity"), "x-uipath-field-id": "id-total"},
        "Vendor Name": {**_field("ft-inferred-text"), "x-uipath-field-id": "id-vendor"},
    }}})))
    assert _fields({"name": "^Total Amount$", "id": "id-total"}) == 0
    assert _fields({"name": "^Total Amount$", "id": "id-vendor"}) == 1
    assert "'Invoice > Total Amount' ft-monetary-quantity id id-total" in capsys.readouterr().err


def test_only_fails_on_a_field_no_entry_asks_for(write, capsys):
    write(_flow())
    every = [{"name": n} for n in ("vendor", "number", "date", "total", "quantity")]
    assert _fields(*every, only=True) == 0
    assert _fields(*every[:4], only=True) == 1
    assert "'Line Items > Quantity' is a field no entry asks for" in capsys.readouterr().err


@pytest.mark.parametrize("value", [
    "vendor", "[]", "{}", "[{}]", '[{"label": "x"}]', '[{"name": 1}]', '[{"name": "("}]',
    '[{"id": true}]', '[{"says": "["}]', '[{"group": "Invoice"}]',
])
def test_malformed_fields_value_is_a_usage_error(write, value):
    write(_flow())
    assert _run("fields", value) == 2


def test_fields_takes_one_value(write):
    write(_flow())
    assert _run("fields", '[{"name": "a"}]', '[{"name": "b"}]') == 2


def test_described_names_each_gap(write, capsys):
    write(_flow(schema=_schema({"G": {"properties": {"Total": {"$ref": "#/$defs/ft-number"}}}}, prompt="")))
    assert _run("described") == 1
    err = capsys.readouterr().err
    assert "overall prompt is empty" in err
    assert "group 'G' has no description" in err
    assert "field 'G > Total' has no description" in err


def test_described_passes_a_fully_described_taxonomy(write):
    write(_flow())
    assert _run("described") == 0


def test_defs(write, capsys):
    write(_flow())
    assert _run("defs") == 0
    write(_flow(schema=_schema(defs={"ft-date": {}})))
    assert _run("defs") == 1
    assert "$defs is missing ft-boolean" in capsys.readouterr().err


def test_defs_only_refuses_any_other_type(write, capsys):
    write(_flow(schema=_schema(defs={**ALL_DEFS, "ft-text": {}})))
    assert _run("defs") == 0
    assert _run("defs", "--only") == 1
    assert "$defs also has ft-text" in capsys.readouterr().err


def test_only_applies_to_fields_and_defs(write):
    write(_flow())
    assert _run("described", "--only") == 2


def test_checks_without_values_refuse_them(write):
    write(_flow())
    assert _run("described", "extra") == 2


def _seeded_schema():
    """A taxonomy shaped like the InvoiceReader fixture: ids, required lists, config."""
    schema = _schema()
    schema["config"] = {"model": {"family": "gemini"}}
    invoice = schema["outputSchema"]["properties"]["Invoice"]
    invoice["x-uipath-field-group-id"] = "id-group"
    invoice["required"] = list(invoice["properties"])
    for n, field in enumerate(invoice["properties"].values()):
        field["x-uipath-field-id"] = f"id-{n}"
    return schema


def _rename(schema, old, new):
    invoice = schema["outputSchema"]["properties"]["Invoice"]
    invoice["properties"] = {new if k == old else k: v for k, v in invoice["properties"].items()}
    invoice["required"] = [new if k == old else k for k in invoice["required"]]
    return schema


@pytest.fixture()
def original(tmp_path):
    path = tmp_path / "original.flow"
    path.write_text(json.dumps(_flow(schema=_seeded_schema())))
    return str(path)


def test_unchanged_passes_the_same_taxonomy(write, original):
    write(_flow(schema=_seeded_schema()))
    assert _run("unchanged", original) == 0


def test_unchanged_passes_only_the_requested_rename(write, original):
    write(_flow(schema=_rename(_seeded_schema(), "Total", "Total Amount")))
    assert _run("unchanged", original, "Total=Total Amount") == 0
    assert _run("unchanged", original) == 1


def test_unchanged_ignores_the_order_of_required(write, original):
    schema = _seeded_schema()
    schema["outputSchema"]["properties"]["Invoice"]["required"].reverse()
    write(_flow(schema=schema))
    assert _run("unchanged", original) == 0


def _change_prompt(schema):
    schema["prompt"] = "Extract everything."


def _change_type(schema):
    schema["outputSchema"]["properties"]["Invoice"]["properties"]["Total Amount"]["$ref"] = "#/$defs/ft-number"


def _change_instructions(schema):
    schema["outputSchema"]["properties"]["Invoice"]["properties"]["Vendor Name"]["description"] = "The vendor."


def _rename_group_and_drop_its_id(schema):
    groups = schema["outputSchema"]["properties"]
    header = groups.pop("Invoice")
    del header["x-uipath-field-group-id"]
    groups["Header"] = header


def _drop_field_id(schema):
    del schema["outputSchema"]["properties"]["Invoice"]["properties"]["Total Amount"]["x-uipath-field-id"]


def _change_config(schema):
    schema["config"]["model"]["family"] = "gpt"


def _add_def(schema):
    schema["outputSchema"]["$defs"]["ft-text"] = {}


@pytest.mark.parametrize("change, named", [
    (_change_prompt, "prompt was"),
    (_change_type, "Total Amount.$ref was"),
    (_change_instructions, "Vendor Name.description was"),
    (_rename_group_and_drop_its_id, "outputSchema.properties.Invoice was dropped"),
    (_drop_field_id, "Total Amount.x-uipath-field-id was dropped"),
    (_change_config, "config.model.family was"),
    (_add_def, "$defs.ft-text was added"),
])
def test_unchanged_names_each_other_change(write, original, capsys, change, named):
    schema = _rename(_seeded_schema(), "Total", "Total Amount")
    change(schema)
    write(_flow(schema=schema))
    assert _run("unchanged", original, "Total=Total Amount") == 1
    assert named in capsys.readouterr().err


def test_unchanged_rename_of_a_field_the_original_lacks_fails(write, original, capsys):
    write(_flow(schema=_seeded_schema()))
    assert _run("unchanged", original, "Grand Total=Total Amount") == 1
    assert "the original taxonomy has no field named 'Grand Total'" in capsys.readouterr().err


@pytest.mark.parametrize("values", [(), ("orig.flow", "Total"), ("orig.flow", "=Total Amount")])
def test_unchanged_with_bad_values_is_a_usage_error(write, values):
    write(_flow())
    assert _run("unchanged", *values) == 2
