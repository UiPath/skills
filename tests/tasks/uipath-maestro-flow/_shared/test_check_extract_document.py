"""Unit tests for ``check_extract_document.py``, on ``.flow`` files written to a tmp sandbox."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_extract_document import EXTRACT_NODE_TYPE, main  # noqa: E402

NODE_ID = "extractInvoice1"
FILE_INPUT = {"id": "invoice", "direction": "in", "type": "file", "triggerNodeId": "start"}


def _flow(file_ref="=js:$vars.start.output.invoice", globals_=(FILE_INPUT,), extra_nodes=(), edges=None):
    nodes = [
        {"id": "start", "type": "core.trigger.manual"},
        {"id": NODE_ID, "type": EXTRACT_NODE_TYPE, "inputs": {"fileRef": file_ref}},
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


def test_edge_with_bad_values_fails(write):
    write(_flow())
    assert _run("edge", "sideways", "input") == 1


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
