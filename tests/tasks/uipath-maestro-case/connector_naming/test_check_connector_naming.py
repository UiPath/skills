"""`check_connector_naming` is the only end-to-end guard on connector field names.

It fetches the live contract at grade time and compares every written key against
it byte for byte. That makes its own failure modes silent: a `case spec` call read
as an empty contract turns every assertion vacuous, and `norm()` pairing a wrong
key with the right authority segment hides the mismatch it was meant to report.
Each test below owns one reported condition, so blanking that condition in the
checker turns a test red.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_connector_naming as chk


@pytest.fixture(autouse=True)
def _reset() -> None:
    chk.FAILURES.clear()
    chk.INFRA.clear()


def only() -> str:
    """The one reported problem, so a test that fires two conditions fails loudly."""
    assert len(chk.FAILURES) == 1, chk.FAILURES
    return chk.FAILURES[0]


def block(**over) -> dict:
    base = {
        "inputs": [{"name": "body", "body": {}}],
        "outputs": [],
        "context": [
            {"name": "connectorKey", "value": "uipath-microsoft-outlook365"},
            {"name": "resourceKey", "value": "conn-1"},
            {"name": "connection", "value": "=bindings.b1"},
            {"name": "folderKey", "value": "=bindings.b2"},
        ],
        "bindings": [],
    }
    base.update(over)
    return base


def binding(bid: str, attr: str, **over) -> dict:
    base = {
        "id": bid,
        "name": "conn",
        "type": "connection",
        "resource": "r",
        "resourceKey": "conn-1",
        "default": {"name": "c"},
        "propertyAttribute": attr,
    }
    base.update(over)
    return base


# --- the pairing helpers ------------------------------------------------------


def test_norm_pairs_across_case_and_underscores():
    assert chk.norm("Image_Url") == chk.norm("imageurl")
    assert chk.norm(None) == ""


def test_ci_reads_a_pascalcase_spec_with_camelcase_keys():
    data = {"Outputs": {"ResponseFields": [{"Name": "status"}]}}
    assert chk.ci(data, "outputs", "responsefields")[0]["Name"] == "status"
    assert chk.ci(data, "Outputs", "Missing") is None


def test_authority_names_reads_each_section():
    data = {
        "Inputs": {"BodyFields": [{"Name": "message.subject"}], "QueryParameters": []},
        "Outputs": {"ResponseFields": [{"Name": "status"}]},
        "Filter": {"Fields": [{"Name": "receivedDateTime"}]},
    }
    assert chk.authority_names(data, "inputs") == ["message.subject"]
    assert chk.authority_names(data, "outputs") == ["status"]
    assert chk.authority_names(data, "filter") == ["receivedDateTime"]


def test_top_level_keeps_first_segments_once_and_in_order():
    assert chk.top_level(["a.b", "a.c", "b"]) == ["a", "b"]


def test_connector_nodes_finds_both_node_types_with_their_connector_key():
    plan = {
        "nodes": [
            {
                "type": "execute-connector-activity",
                "displayName": "Send",
                "data": {"context": [{"name": "connectorKey", "value": "k1"}]},
            },
            {
                "type": "wait-for-connector",
                "displayName": "Wait",
                "data": {"context": [{"name": "connectorKey", "value": "k2"}]},
            },
            {"type": "action", "displayName": "Approve", "data": {}},
        ]
    }
    found = [(n, k) for n, k, _ in chk.connector_nodes(plan)]
    assert found == [("Send", "k1"), ("Wait", "k2")]


# --- check_inputs -------------------------------------------------------------


def test_an_input_key_outside_the_contract_is_reported():
    chk.check_inputs("T", block(inputs=[{"body": {"nope": 1}}]), ["message.subject"])
    assert "matches no field in the connector contract" in only()


def test_an_input_key_that_only_differs_by_case_is_reported():
    chk.check_inputs("T", block(inputs=[{"body": {"Message": {}}}]), ["message.subject"])
    assert "should be 'message'" in only()


def test_a_nested_input_key_is_graded_too():
    chk.check_inputs(
        "T",
        block(inputs=[{"body": {"attachment": {"image_URL": 1}}}]),
        ["attachment.image_url"],
    )
    assert "under attachment" in only()


def test_an_array_marker_pairs_with_the_written_array_name():
    chk.check_inputs(
        "T",
        block(inputs=[{"body": {"blocks": [{"text": "x"}]}}]),
        ["blocks[*].text"],
    )
    assert chk.FAILURES == []


def test_a_trigger_envelope_key_is_not_graded_as_a_contract_field():
    chk.check_inputs(
        "T",
        block(inputs=[{"body": {"parameters": {"channel": 1}}}]),
        ["channel"],
    )
    assert chk.FAILURES == []


def test_a_compiled_trigger_filter_is_not_graded_as_a_request_field():
    """The filter envelope carries `expression`, which no contract declares."""
    body = {"filters": {"expression": "(contains(Title,'x'))"}}
    chk.check_inputs("T", block(inputs=[{"body": body}]), ["calendarID"])
    assert chk.FAILURES == []


def test_a_filter_operand_written_as_a_request_field_is_reported():
    body = {"filters": {"expression": "(contains(Title,'x'))"}, "Title": "x"}
    chk.check_inputs("T", block(inputs=[{"body": body}]), ["calendarID"])
    assert "input key 'Title' matches no field" in only()


def test_a_request_that_wrote_nothing_is_reported():
    chk.check_inputs("T", block(inputs=[{"body": {}}]), ["message.subject"])
    assert "no request field was written at all" in only()


def test_a_field_the_sdd_declares_and_the_build_omits_is_reported():
    chk.check_inputs(
        "T",
        block(inputs=[{"body": {"channel": 1}}]),
        ["channel", "messageToSend"],
        "uipath-salesforce-slack",
    )
    assert "declared by the SDD are absent" in only()


# --- check_outputs ------------------------------------------------------------


def payload(props: dict, name: str = "response") -> dict:
    return {"name": name, "body": {"type": "object", "properties": props}}


# --- check_input_containers ---------------------------------------------------

SLACK_INPUTS = {
    "Inputs": {
        "PathParameters": [],
        "QueryParameters": [{"Name": "send_as"}],
        "BodyFields": [{"Name": "channel"}, {"Name": "attachment.title"}],
    }
}


def test_a_query_parameter_written_into_the_body_is_reported():
    chk.check_input_containers(
        "T",
        block(inputs=[
            {"name": "queryParameters", "body": {}},
            {"name": "body", "body": {"channel": "C1", "send_as": "bot"}},
        ]),
        SLACK_INPUTS,
    )
    assert "'send_as' is in body, but the connector contract declares it under queryParameters" in only()


def test_each_input_key_in_its_declared_container_passes():
    chk.check_input_containers(
        "T",
        block(inputs=[
            {"name": "pathParameters", "body": {}},
            {"name": "queryParameters", "body": {"send_as": "bot"}},
            {"name": "body", "body": {"channel": "C1", "attachment": {"title": "t"}}},
        ]),
        SLACK_INPUTS,
    )
    assert chk.FAILURES == []


def test_a_name_two_sections_declare_passes_in_either():
    both = {"Inputs": {"QueryParameters": [{"Name": "channel"}], "BodyFields": [{"Name": "channel"}]}}
    for container in ("queryParameters", "body"):
        chk.check_input_containers(
            "T", block(inputs=[{"name": container, "body": {"channel": "C1"}}]), both,
        )
    assert chk.FAILURES == []
    # ...and still not in a container neither section maps to.
    chk.check_input_containers(
        "T", block(inputs=[{"name": "pathParameters", "body": {"channel": "C1"}}]), both,
    )
    assert "'channel' is in pathParameters, but the connector contract declares it under body / queryParameters" in only()


def test_a_key_no_section_declares_is_left_to_check_inputs():
    chk.check_input_containers(
        "T", block(inputs=[{"name": "body", "body": {"nope": 1}}]), SLACK_INPUTS
    )
    assert chk.FAILURES == []


def test_a_payload_property_set_that_differs_from_the_contract_is_reported():
    chk.check_outputs("T", block(outputs=[payload({"status": {"type": "string"}})]),
                      ["status", "id"])
    assert "property names do not match the contract" in only()


def test_a_property_with_no_type_or_ref_or_items_is_reported():
    chk.check_outputs("T", block(outputs=[payload({"status": {}})]), ["status"])
    assert "carries no type/$ref/items" in only()


def test_a_nested_contract_path_that_does_not_resolve_is_reported():
    chk.check_outputs(
        "T",
        block(outputs=[payload({"message": {"type": "object"}})]),
        ["message.subject"],
    )
    assert "does not resolve through properties/items/$ref" in only()


def test_a_nested_key_written_in_the_wrong_case_is_reported():
    out = payload(
        {"message": {"type": "object", "properties": {"Subject": {"type": "string"}}}}
    )
    chk.check_outputs("T", block(outputs=[out]), ["message.subject"])
    assert "the contract says 'subject'" in only()


def test_the_error_envelope_must_be_lower_cased():
    err = {
        "name": "error",
        "body": {"properties": {k[:1].upper() + k[1:]: {"type": "string"}
                                for k in chk.ERROR_ENVELOPE}},
    }
    chk.check_outputs("T", block(outputs=[err]), ["status"])
    assert "must be lower-cased" in chk.FAILURES[0]


def test_a_missing_response_schema_is_reported():
    chk.check_outputs("T", block(outputs=[]), ["status"])
    assert "no response schema was written at all" in only()


# --- check_definitions --------------------------------------------------------


def test_a_ref_with_no_definitions_key_is_reported():
    blk = block(outputs=[{
        "name": "response",
        "body": {
            "properties": {"profile": {"$ref": "#/definitions/botProfile"}},
            "definitions": {},
        },
    }])
    chk.check_definitions("T", blk, ["profile.name"])
    assert "resolve to no definitions key" in chk.FAILURES[0]


def test_a_definitions_key_the_contract_never_declares_is_reported():
    blk = block(outputs=[{
        "name": "response",
        "body": {
            "properties": {"profile": {"$ref": "#/definitions/invented"}},
            "definitions": {"invented": {"type": "object"}},
        },
    }])
    chk.check_definitions("T", blk, ["profile.name"])
    assert "were invented, not derived" in only()


# --- schema_shape and check_shape ---------------------------------------------


def test_schema_shape_counts_maps_keys_definitions_refs_and_total():
    body = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"$ref": "#/definitions/d"}},
        "definitions": {"d": {"type": "object", "properties": {"c": {"type": "string"}}}},
    }
    maps, keys, defs, refs, total = chk.schema_shape(body)
    assert (maps, keys, defs, refs) == (2, 3, 1, 1)
    assert total > 0


def test_a_stripped_annotation_is_caught_by_the_total_key_count():
    full = {"properties": {"a": {"type": "string", "title": "A"}}}
    thin = {"properties": {"a": {"type": "string"}}}
    assert chk.schema_shape(full)[:4] == chk.schema_shape(thin)[:4]
    assert chk.schema_shape(full)[4] != chk.schema_shape(thin)[4]


def test_a_composed_body_that_lost_content_is_reported():
    cli = [{"Name": "response", "Body": {"properties": {"a": {"type": "string"},
                                                        "b": {"type": "string"}}}}]
    blk = block(outputs=[payload({"a": {"type": "string"}})])
    chk.check_shape("T", blk, cli)
    assert "schema does not match the CLI's structure" in only()


# --- check_filter -------------------------------------------------------------


def test_a_structured_filter_field_in_the_wrong_case_is_reported():
    """One backslash: `json.dumps` re-escapes the loaded value, and two match nothing."""
    blk = block(inputs=[{"body": {"filters": {
        "expressionValue": '=jsonString:{"fieldName":"ReceivedDateTime"}'}}}])
    chk.check_filter("T", blk, ["receivedDateTime"])
    assert "the contract field is 'receivedDateTime'" in only()


def test_a_compiled_filter_expression_in_the_wrong_case_is_reported():
    blk = block(inputs=[{"body": {"filters": {"expression": "ReceivedDateTime > '2026'"}}}])
    chk.check_filter("T", blk, ["receivedDateTime"])
    assert "compiled filter references 'ReceivedDateTime'" in only()


def test_a_node_with_no_filter_contract_is_not_graded():
    chk.check_filter("T", block(), [])
    assert chk.FAILURES == []


# --- check_bindings -----------------------------------------------------------


def roots() -> list:
    return [binding("b1", "ConnectionId"), binding("b2", "folderKey")]


def test_a_task_that_copies_its_connection_binding_onto_itself_is_reported():
    chk.check_bindings("T", block(bindings=[{"id": "b1"}]), roots())
    assert "must not copy the connection or folder binding" in only()


def test_a_copied_connection_row_under_another_id_is_reported():
    chk.check_bindings("T", block(bindings=[{"id": "bX", "resource": "Connection"}]), roots())
    assert "must not copy the connection or folder binding" in only()


def test_the_picker_rows_splice_lists_on_the_task_are_allowed():
    picker = [{"id": "bE1", "resource": "entity", "propertyAttribute": "name"},
              {"id": "bE2", "resource": "entity", "propertyAttribute": "folderKey"}]
    chk.check_bindings("T", block(bindings=picker), roots())
    assert chk.FAILURES == []


def test_an_empty_data_bindings_array_is_allowed():
    chk.check_bindings("T", block(bindings=[]), roots())
    assert chk.FAILURES == []


def test_an_omitted_data_bindings_key_is_allowed():
    # Empty and omitted are the same state: the FE reads per-activity property
    # bindings at data.context[name="metadata"].bindings and never reads
    # data.bindings, and the CLI declares `bindings?:` optional and never emits
    # `[]`. Requiring the key failed every real build this check ever graded.
    blk = block()
    blk.pop("bindings")
    chk.check_bindings("T", blk, roots())
    assert chk.FAILURES == []


def test_a_missing_connection_context_entry_is_reported():
    blk = block(context=[{"name": "resourceKey", "value": "conn-1"}])
    chk.check_bindings("T", blk, roots())
    assert "context[connection] is missing" in only()


def test_an_omitted_folder_key_is_allowed():
    blk = block(context=[{"name": "resourceKey", "value": "conn-1"},
                         {"name": "connection", "value": "=bindings.b1"}])
    chk.check_bindings("T", blk, roots())
    assert chk.FAILURES == []


def test_a_context_entry_that_is_not_a_binding_reference_is_reported():
    blk = block(context=[{"name": "resourceKey", "value": "conn-1"},
                         {"name": "connection", "value": "conn-1"}])
    chk.check_bindings("T", blk, roots())
    assert "should be '=bindings.<id>'" in only()


def test_a_context_entry_pointing_at_no_root_binding_is_reported():
    blk = block(context=[{"name": "resourceKey", "value": "conn-1"},
                         {"name": "connection", "value": "=bindings.gone"}])
    chk.check_bindings("T", blk, roots())
    assert "which is not in the root bindings[]" in only()


def test_a_binding_missing_a_required_field_is_reported():
    b = binding("b1", "ConnectionId")
    del b["resource"]
    chk.check_bindings("T", block(context=[
        {"name": "resourceKey", "value": "conn-1"},
        {"name": "connection", "value": "=bindings.b1"}]), [b])
    assert "is missing required field(s)" in only()


def test_a_binding_with_the_wrong_property_attribute_is_reported():
    chk.check_bindings("T", block(context=[
        {"name": "resourceKey", "value": "conn-1"},
        {"name": "connection", "value": "=bindings.b1"}]),
        [binding("b1", "folderKey")])
    assert "expected 'ConnectionId'" in only()


def test_a_binding_whose_resource_key_is_not_the_nodes_connection_is_reported():
    chk.check_bindings("T", block(context=[
        {"name": "resourceKey", "value": "conn-1"},
        {"name": "connection", "value": "=bindings.b1"}]),
        [binding("b1", "ConnectionId", resourceKey="other")])
    assert "expected the node's connection id" in only()


def test_a_binding_with_an_empty_default_is_reported():
    chk.check_bindings("T", block(context=[
        {"name": "resourceKey", "value": "conn-1"},
        {"name": "connection", "value": "=bindings.b1"}]),
        [binding("b1", "ConnectionId", default={})])
    assert "has an empty default" in only()


# --- fetching the contract ----------------------------------------------------


def run_returning(stdout: str):
    class Done:
        def __init__(self) -> None:
            self.stdout = stdout

    return lambda *a, **k: Done()


def test_a_spec_timeout_is_infra_not_a_build_defect(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="uip", timeout=120)

    monkeypatch.setattr(chk.subprocess, "run", boom)
    assert chk.spec("activity", "t", "c") == {}
    assert "timed out" in chk.INFRA[0]
    assert chk.FAILURES == []


def test_a_missing_uip_binary_is_infra(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("uip")

    monkeypatch.setattr(chk.subprocess, "run", boom)
    assert chk.spec("activity", "t", "c") == {}
    assert "could not run `uip`" in chk.INFRA[0]


def test_a_non_json_spec_response_is_infra(monkeypatch):
    monkeypatch.setattr(chk.subprocess, "run", run_returning("not json"))
    assert chk.spec("activity", "t", "c") == {}
    assert "returned non-JSON" in chk.INFRA[0]


def test_a_failed_spec_envelope_is_infra(monkeypatch):
    monkeypatch.setattr(
        chk.subprocess, "run",
        run_returning(json.dumps({"Result": "Failure", "Message": "not found"})),
    )
    assert chk.spec("activity", "t", "c") == {}
    assert "failed: not found" in chk.INFRA[0]


def test_a_successful_spec_returns_its_data(monkeypatch):
    monkeypatch.setattr(
        chk.subprocess, "run",
        run_returning(json.dumps({"Result": "Success", "Data": {"Identity": {}}})),
    )
    assert chk.spec("activity", "t", "c") == {"Identity": {}}
    assert chk.INFRA == []


# --- main ---------------------------------------------------------------------


def test_a_missing_caseplan_exits_one(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check", str(tmp_path / "gone.json")])
    assert chk.main() == 1
    assert "not found" in capsys.readouterr().out


def test_a_node_with_no_type_id_is_reported(tmp_path, monkeypatch, capsys):
    plan = {"bindings": [], "nodes": [{
        "type": "execute-connector-activity", "displayName": "Send",
        "data": {"context": [{"name": "connectorKey", "value": "k"}]}}]}
    p = tmp_path / "caseplan.json"
    p.write_text(json.dumps(plan))
    monkeypatch.setattr(sys, "argv", ["check", str(p)])
    assert chk.main() == 1
    assert "cannot locate typeId/connectionId" in capsys.readouterr().out


def test_fewer_than_two_graded_connector_tasks_is_reported(tmp_path, monkeypatch, capsys):
    p = tmp_path / "caseplan.json"
    p.write_text(json.dumps({"bindings": [], "nodes": []}))
    monkeypatch.setattr(sys, "argv", ["check", str(p)])
    assert chk.main() == 1
    assert "expected 2 connector tasks" in capsys.readouterr().out


def graded_node(name: str, type_id: str) -> dict:
    return {
        "type": "execute-connector-activity", "displayName": name,
        "data": {
            "typeId": type_id, "bindings": [], "inputs": [{"name": "body", "body": {}}],
            "outputs": [],
            "context": [{"name": "connectorKey", "value": "k"},
                        {"name": "resourceKey", "value": "conn-1"},
                        {"name": "connection", "value": "=bindings.b1"},
                        {"name": "folderKey", "value": "=bindings.b2"}],
        },
    }


def plan_file(tmp_path, nodes: list) -> str:
    p = tmp_path / "caseplan.json"
    p.write_text(json.dumps({
        "bindings": [binding("b1", "ConnectionId"), binding("b2", "folderKey")],
        "nodes": nodes,
    }))
    return str(p)


def spec_failing_on(type_id: str):
    """Succeed for every node but one, so a single unreachable contract is isolated."""
    def run(cmd, *a, **k):
        ok = type_id not in " ".join(cmd)
        return type("Done", (), {
            "stdout": json.dumps({"Result": "Success", "Data": {"Identity": {}}})
            if ok else "not json"
        })()

    return run


def test_one_unreachable_contract_exits_two_so_triage_can_tell_them_apart(
    tmp_path, monkeypatch, capsys
):
    """Needs a third node: the `seen < 2` floor counts only the resolvable ones."""
    nodes = [graded_node("A", "aaaaaaaa-0000-0000-0000-000000000001"),
             graded_node("B", "bbbbbbbb-0000-0000-0000-000000000002"),
             graded_node("C", "cccccccc-0000-0000-0000-000000000003")]
    monkeypatch.setattr(sys, "argv", ["check", plan_file(tmp_path, nodes)])
    monkeypatch.setattr(chk.subprocess, "run",
                        spec_failing_on("cccccccc-0000-0000-0000-000000000003"))
    assert chk.main() == 2
    assert "naming was NOT graded" in capsys.readouterr().out


def test_two_nodes_that_both_fail_to_fetch_exit_one_and_still_print_the_infra_lines(
    tmp_path, monkeypatch, capsys
):
    """The floor fires here, so exit 2 does not. Do not make it skip on infra: the
    floor is what stops a build carrying no connector task from passing."""
    nodes = [graded_node("A", "aaaaaaaa-0000-0000-0000-000000000001"),
             graded_node("B", "bbbbbbbb-0000-0000-0000-000000000002")]
    monkeypatch.setattr(sys, "argv", ["check", plan_file(tmp_path, nodes)])
    # The grader's own catalog pull succeeds; only the two contract fetches fail.
    _uip(monkeypatch, {"pull": json.dumps({"Result": "Success"}), "spec": "not json"})
    assert chk.main() == 1
    out = capsys.readouterr().out
    assert out.count("INFRA:") == 2
    assert "graded 0" in out


def test_a_run_where_every_name_matches_exits_zero(tmp_path, monkeypatch, capsys):
    nodes = [graded_node("A", "aaaaaaaa-0000-0000-0000-000000000001"),
             graded_node("B", "bbbbbbbb-0000-0000-0000-000000000002")]
    monkeypatch.setattr(sys, "argv", ["check", plan_file(tmp_path, nodes)])
    monkeypatch.setattr(
        chk.subprocess, "run",
        run_returning(json.dumps({"Result": "Success", "Data": {"Identity": {}}})),
    )
    assert chk.main() == 0
    assert "PASS: connector field names match" in capsys.readouterr().out


MISPLACED = "'send_as' is in body, but the connector contract declares it under queryParameters"


def run_with_misplaced_key(tmp_path, monkeypatch, capsys, service_type: str | None) -> str:
    """Two nodes that write `send_as` into `body`, against a contract that declares it a
    query parameter. `service_type` turns both into triggers."""
    nodes = [graded_node("A", "aaaaaaaa-0000-0000-0000-000000000001"),
             graded_node("B", "bbbbbbbb-0000-0000-0000-000000000002")]
    for node in nodes:
        node["data"]["inputs"] = [{"name": "body", "body": {"send_as": "bot"}}]
        if service_type:
            node["data"]["serviceType"] = service_type
    monkeypatch.setattr(sys, "argv", ["check", plan_file(tmp_path, nodes)])
    monkeypatch.setattr(
        chk.subprocess, "run",
        run_returning(json.dumps({"Result": "Success", "Data": {"Identity": {}, **SLACK_INPUTS}})),
    )
    chk.main()
    return capsys.readouterr().out


def test_an_activity_with_a_misplaced_key_is_reported_by_main(tmp_path, monkeypatch, capsys):
    assert MISPLACED in run_with_misplaced_key(tmp_path, monkeypatch, capsys, None)


def test_a_trigger_is_not_graded_on_containers(tmp_path, monkeypatch, capsys):
    # A trigger keeps every bucket inside one `body` envelope, so the same plan is not a
    # container defect there.
    out = run_with_misplaced_key(tmp_path, monkeypatch, capsys, "Intsvc.WaitForEvent")
    assert MISPLACED not in out
    assert "is in body, but the connector contract declares it" not in out


def test_the_default_path_also_finds_a_plan_saved_as_caseplan_case(tmp_path, monkeypatch, capsys):
    project = tmp_path / "ConnectorNaming" / "ConnectorNaming"
    project.mkdir(parents=True)
    (project / "caseplan.case").write_text(json.dumps({"bindings": [], "nodes": []}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check"])
    assert chk.main() == 1
    out = capsys.readouterr().out
    assert "not found" not in out
    assert "expected 2 connector tasks" in out


# -- the grader's own catalog pull and its lookup diagnostics -------------------

class _Done:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def _uip(monkeypatch, replies: dict[str, str]) -> list[list[str]]:
    """Answer `uip maestro case <verb>` from `replies` and record each call."""
    calls: list[list[str]] = []

    def run(argv, **_kwargs):
        calls.append(argv)
        return _Done(replies["pull" if "pull" in argv else "spec"])

    monkeypatch.setattr(chk.subprocess, "run", run)
    monkeypatch.setattr(chk, "INFRA", [])
    return calls


def test_the_grader_pulls_the_catalog_itself(monkeypatch):
    calls = _uip(monkeypatch, {"pull": json.dumps({"Result": "Success"})})

    chk.pull_registry()

    assert calls == [["uip", "maestro", "case", "registry", "pull", "--output", "json"]]
    assert chk.INFRA == []


def test_a_failed_pull_is_reported_as_infra(monkeypatch):
    _uip(monkeypatch, {"pull": json.dumps({"Result": "Failure", "Message": "Not logged in"})})

    chk.pull_registry()

    assert chk.INFRA == ["case registry pull failed: Not logged in — the connector catalog may be missing"]


def test_a_failed_spec_reports_the_cli_instructions(monkeypatch):
    _uip(monkeypatch, {"spec": json.dumps({
        "Result": "Failure",
        "Message": "Error fetching connector task spec for typeId t1",
        "Instructions": "No resource index found. Run registry pull first.",
    })})

    assert chk.spec("activity", "t1", "c1") == {}
    assert chk.INFRA == [
        (
            "case spec --type activity t1 failed: Error fetching connector task spec for typeId t1 "
            "(No resource index found. Run registry pull first.) — naming was NOT graded"
        )
    ]

