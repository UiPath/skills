"""flow_io_roles maps seeded values onto agent-chosen inputs and finds outputs by value."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import flow_io_roles as io  # noqa: E402

DETECTOR_ROLES = {
    "invoice": {"value": "MCS-2026-04872", "keywords": ["invoice"]},
    "account": {"value": "ACCT-98201-NE", "keywords": ["account", "acct", "customer"]},
    "line": {"value": 5, "keywords": ["line"]},
    "price": {"value": 300, "keywords": ["price", "rate"]},
    "quantity": {"value": 14, "keywords": ["quantity", "qty"]},
}


def _flow(inputs, outputs=(), nodes=()):
    return {
        "nodes": list(nodes),
        "variables": {"globals": [
            *({"id": i, "direction": "in", "type": t} for i, t in inputs),
            *({"id": o, "direction": "out", "type": t} for o, t in outputs),
        ]},
    }


def test_scalar_inputs_map_by_meaning_and_take_the_declared_type():
    flow = _flow([("invoiceNo", "string"), ("acct", "string"), ("disputedLineNumber", "number"),
                  ("billedUnitPrice", "number"), ("qty", "string")])
    inputs, attachments, unmapped = io.map_inputs(flow, DETECTOR_ROLES, object_fallback=None, file_path=None)
    assert inputs == {"invoiceNo": "MCS-2026-04872", "acct": "ACCT-98201-NE", "disputedLineNumber": 5,
                      "billedUnitPrice": 300, "qty": "14"}
    assert attachments == {} and unmapped == []


def test_a_role_no_input_means_is_reported_unmapped():
    flow = _flow([("invoiceNumber", "string")])
    _, _, unmapped = io.map_inputs(flow, DETECTOR_ROLES, object_fallback=None, file_path=None)
    assert sorted(unmapped) == ["account", "line", "price", "quantity"]


def test_an_object_input_is_built_from_the_paths_the_flow_reads():
    node = {"id": "s", "inputs": {"script": "return $vars.start.output.submission.customer.acctNo + "
                                            "$vars.start.output.submission.invoice?.number"}}
    flow = _flow([("pdf", "file"), ("submission", "object")], nodes=[node])
    roles = {"account": {"value": "ACCT-1", "keywords": ["acct", "account"]},
             "invoice": {"value": "MCS-1", "keywords": ["invoice", "number"]}}
    fallback = {"lines": [{"lineNumber": 2}]}
    inputs, attachments, _ = io.map_inputs(flow, roles, object_fallback=fallback, file_path="/x.pdf")
    assert attachments == {"pdf": "/x.pdf"}
    assert inputs["submission"] == {"lines": [{"lineNumber": 2}], "customer": {"acctNo": "ACCT-1"},
                                    "invoice": {"number": "MCS-1"}}


def test_outputs_are_found_by_value_and_exclude_inputs():
    flow = _flow([("invoiceNumber", "string")], [("overcharge", "number"), ("tier", "string"),
                                                  ("emailDraft", "object")])
    payload = {"variables": {"globals": {
        "invoiceNumber": "MCS-2026-04872", "overcharge": 1610, "tier": "Enterprise",
        "emailDraft": {"subject": "Invoice", "body": "USD 1,610.00 credited"}}}}
    outs = io.out_values(flow, payload)
    assert "invoiceNumber" not in outs
    assert io.find_out(outs, io.equals_number(1610, 0.005)) == ["overcharge"]
    assert io.find_out(outs, io.equals_text("enterprise")) == ["tier"]
    assert any("USD 1,610.00" in t for t in io.texts(outs["emailDraft"][1]))


def test_booleans_and_numeric_strings_compare_by_value():
    assert io.equals_bool(True)("true") and not io.equals_bool(True)(1)
    assert io.equals_number(4950, 0.005)("4,950.00") and io.equals_number(0, 0.005)(0)


def test_exact_text_keeps_case_and_unmapped_roles_name_the_inputs():
    assert io.equals_exact("MCS-2026-04872")(" MCS-2026-04872 ")
    assert not io.equals_exact("MCS-2026-04872")("mcs-2026-04872")
    flow = _flow([("invoiceNumber", "string"), ("pdf", "file")])
    assert io.unmapped_error(flow, []) is None
    assert io.unmapped_error(flow, ["account"]) == "could not map account onto inputs ['invoiceNumber', 'pdf']"
