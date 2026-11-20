"""flow_io_roles maps seeded values onto agent-chosen inputs and finds outputs by value."""
import json
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


def test_a_whole_word_match_beats_a_substring_in_an_earlier_input():
    flow = _flow([("deadline", "string"), ("lineItem", "number")])
    roles = {"line": {"value": 5, "keywords": ["line"]}}
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=None, file_path=None)
    assert inputs == {"lineItem": 5} and unmapped == []


def test_an_object_role_value_is_not_fed_to_a_boolean_input():
    flow = _flow([("hasAttachments", "boolean")])
    roles = {"attachments": {"value": {"hasAttachments": False}, "keywords": ["attachments"]}}
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=None, file_path=None)
    assert inputs == {} and unmapped == ["attachments"]


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
    assert io.equals_bool(True)("YES") and io.equals_bool(False)(" no ") and not io.equals_bool(True)("No")
    assert io.equals_number(4950, 0.005)("4,950.00") and io.equals_number(0, 0.005)(0)


def test_exact_text_keeps_case_and_unmapped_roles_name_the_inputs():
    assert io.equals_exact("MCS-2026-04872")(" MCS-2026-04872 ")
    assert not io.equals_exact("MCS-2026-04872")("mcs-2026-04872")
    flow = _flow([("invoiceNumber", "string"), ("pdf", "file")])
    assert io.unmapped_error(flow, []) is None
    assert io.unmapped_error(flow, ["account"]) == "could not map account onto inputs ['invoiceNumber', 'pdf']"


def test_an_input_the_grader_could_not_match_is_a_grader_error(capsys):
    """An input the grader failed to match is labelled for triage, not read as the agent's fault."""
    import pytest
    flow = _flow([("invoiceNumber", "string"), ("custRef", "string")])
    with pytest.raises(SystemExit) as exc:
        io.unmapped_error(flow, ["account"], {"invoiceNumber": "MCS-1"})
    assert exc.value.code == io.GRADER_ERROR_EXIT
    assert "possible grader mapping miss, or an unrelated input" in capsys.readouterr().err


def test_an_input_the_flow_never_declared_is_an_agent_failure():
    flow = _flow([("invoiceNumber", "string"), ("pdf", "file")])
    assert io.unmapped_error(flow, ["account"], {"invoiceNumber": "MCS-1"}) == (
        "could not map account onto inputs ['invoiceNumber', 'pdf']")


ESCALATION_ROLES = {
    "subject": {"value": "Outage", "keywords": ["emailsubject", "subject"]},
    "caseRef": {"value": "ESC-1", "keywords": ["casereference", "caseref", "case", "reference"]},
}


def test_a_scalar_input_beside_an_object_input_gets_its_role():
    node = {"id": "s", "inputs": {"script": "return $vars.start.output.email.subject"}}
    flow = _flow([("email", "object"), ("caseReference", "string")], nodes=[node])
    inputs, _, unmapped = io.map_inputs(flow, ESCALATION_ROLES, object_fallback=None, file_path=None)
    assert inputs == {"email": {"subject": "Outage"}, "caseReference": "ESC-1"}
    assert unmapped == []


def test_a_role_only_the_object_fallback_carries_is_not_unmapped():
    flow = _flow([("email", "object")])
    inputs, _, unmapped = io.map_inputs(flow, ESCALATION_ROLES, object_fallback={"caseRef": "ESC-1"},
                                        file_path=None)
    assert inputs == {"email": {"caseRef": "ESC-1"}} and unmapped == []


def test_an_array_input_gets_a_list_role_and_never_a_dict():
    roles = {"lines": {"value": [{"lineNumber": 5}], "keywords": ["lineitems", "lines"]},
             "attached": {"value": False, "keywords": ["attachment"]}}
    flow = _flow([("lineItems", "array"), ("attachments", "array")])
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=None, file_path=None)
    assert inputs == {"lineItems": [{"lineNumber": 5}]}
    assert unmapped == ["attached"]


def test_a_whole_word_match_outranks_one_inside_a_word():
    flow = _flow([("deadline", "string"), ("disputedLineNumber", "number"), ("hasAttachments", "boolean")])
    roles = {"line": {"value": 5, "keywords": ["linenumber", "lineno", "line"]},
             "attached": {"value": True, "keywords": ["attachment"]}}
    inputs, _, _ = io.map_inputs(flow, roles, object_fallback=None, file_path=None)
    assert inputs == {"disputedLineNumber": 5, "hasAttachments": True}


def test_an_all_lowercase_id_still_maps_by_the_fragment_inside_it():
    flow = _flow([("invoicenumber", "string"), ("disputedlinenumber", "number")])
    inputs, _, unmapped = io.map_inputs(flow, DETECTOR_ROLES, object_fallback=None, file_path=None)
    assert inputs == {"invoicenumber": "MCS-2026-04872", "disputedlinenumber": 5}
    assert sorted(unmapped) == ["account", "price", "quantity"]


def test_ties_go_to_the_closer_name_whatever_the_declaration_order():
    for order in ([("invoiceLine", "number"), ("invoice", "string")],
                  [("invoice", "string"), ("invoiceLine", "number")]):
        inputs, _, _ = io.map_inputs(_flow(order), DETECTOR_ROLES, object_fallback=None, file_path=None)
        assert inputs == {"invoice": "MCS-2026-04872", "invoiceLine": 5}


_SPELLED_ROLES = {
    "invoice number": {"value": "MCS-1", "keywords": ["invoicenumber", "invoice"]},
    "line no": {"value": 5, "keywords": ["lineno", "line"]},
}


def test_an_object_read_through_an_alias_is_fed_every_role_under_its_names():
    node = {"id": "s", "inputs": {"script": "const d = $vars.start.output.dispute; return d.invoiceNumber"}}
    flow = _flow([("dispute", "object")], nodes=[node])
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert unmapped == []
    assert inputs["dispute"]["invoiceNumber"] == "MCS-1" and inputs["dispute"]["lineNo"] == 5
    assert inputs["dispute"]["invoicenumber"] == "MCS-1" and inputs["dispute"]["line"] == 5


def test_an_object_read_by_destructuring_is_fed_every_role_under_its_names():
    node = {"id": "s", "inputs": {"script": "const { invoiceNumber, lineNo } = $vars.start.output.dispute;"}}
    flow = _flow([("dispute", "object")], nodes=[node])
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert unmapped == []
    assert inputs["dispute"]["invoiceNumber"] == "MCS-1" and inputs["dispute"]["lineNo"] == 5


def test_a_lone_free_text_submission_gets_every_role_as_json():
    flow = _flow([("invoicePdf", "file"), ("disputeSubmission", "string")])
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path="inv.pdf")
    assert unmapped == []
    sent = json.loads(inputs["disputeSubmission"])
    assert sent["invoiceNumber"] == "MCS-1" and sent["invoicenumber"] == "MCS-1"


def test_a_free_text_submission_carries_the_callers_fallback_fields():
    flow = _flow([("invoicePdf", "file"), ("disputeSubmission", "string")])
    fallback = {"disputedLineItems": [{"lineNumber": 5}]}
    inputs, _, _ = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=fallback, file_path="inv.pdf")
    sent = json.loads(inputs["disputeSubmission"])
    assert sent["disputedLineItems"] == [{"lineNumber": 5}] and sent["invoiceNumber"] == "MCS-1"


def test_a_role_is_spelled_in_camel_case_from_its_name():
    assert io.spelled_object(_SPELLED_ROLES)["lineNo"] == 5


def test_a_lone_text_input_that_is_not_a_submission_gets_nothing():
    flow = _flow([("notes", "string")])
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert inputs == {} and sorted(unmapped) == ["invoice number", "line no"]


def test_a_lone_text_input_described_as_a_claim_gets_the_json():
    flow = _flow([("text", "string")])
    flow["variables"]["globals"][0]["description"] = "The customer claim as text"
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert unmapped == [] and json.loads(inputs["text"])["invoiceNumber"] == "MCS-1"


def test_two_unmatched_text_inputs_still_report_the_roles():
    flow = _flow([("notes", "string"), ("summary", "string")])
    _, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert sorted(unmapped) == ["invoice number", "line no"]


def test_an_object_with_resolved_paths_gets_no_spelling_fallback():
    node = {"id": "s", "inputs": {"script": "return $vars.start.output.dispute.invoiceNumber"}}
    flow = _flow([("dispute", "object")], nodes=[node])
    inputs, _, unmapped = io.map_inputs(flow, _SPELLED_ROLES, object_fallback=None, file_path=None)
    assert inputs["dispute"] == {"invoiceNumber": "MCS-1"} and unmapped == ["line no"]
