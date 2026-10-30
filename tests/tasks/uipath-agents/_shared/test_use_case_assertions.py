"""Offline unit tests for the use-case assertion helpers (no `uip` required)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.use_case_assertions import (  # noqa: E402
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_existing_project,
    assert_integration_wiring,
    require_input,
    strip_schema,
    attachment_fields,
    find_property,
    is_file_reading_tool,
    require_resource,
    walk_properties,
)

ATTACHMENT = {
    "type": "object",
    "properties": {"ID": {"type": "string"}},
    "required": ["ID"],
    "x-uipath-resource-kind": "JobAttachment",
}


def test_walk_properties_flattens_wrappers_and_array_items():
    schema = {
        "type": "object",
        "properties": {
            "result": {
                "type": "object",
                "properties": {"status": {"type": "string"}, "issues": {"type": "array", "items": {"$ref": "#/definitions/issue"}}},
            }
        },
        "definitions": {"issue": {"type": "object", "properties": {"code": {"type": "string"}}}},
    }
    assert {"result", "status", "issues", "code"} <= set(walk_properties(schema))


def test_find_property_ignores_case_and_separators():
    props = {"needs_human_review": {"type": "boolean"}}
    assert find_property(props, "needsHumanReview")[0] == "needs_human_review"
    assert find_property(props, "other") is None


def test_assert_has_fields_fails_on_missing_field():
    with pytest.raises(SystemExit):
        assert_has_fields({"type": "object", "properties": {"a": {}}}, "out", {"b": []})


def test_assert_enum_accepts_enum_and_oneof_const():
    assert_enum({"type": "string", "enum": ["low", "high"]}, "x", ["low", "high"])
    assert_enum({"type": "string", "oneOf": [{"const": "low"}, {"const": "high"}]}, "x", ["low"])
    with pytest.raises(SystemExit):
        assert_enum({"type": "string"}, "x", ["low"])


def test_assert_enum_accepts_values_listed_in_description():
    node = {"type": "string", "description": "One of: low | normal | high"}
    assert_enum(node, "x", ["low", "normal", "high"])
    with pytest.raises(SystemExit):
        assert_enum(node, "x", ["low", "urgent"])
    # "other" must not match inside "another"
    with pytest.raises(SystemExit):
        assert_enum({"type": "string", "description": "pick another"}, "x", ["other"])


def test_attachment_fields_detects_ref_and_array_items():
    schema = {
        "type": "object",
        "properties": {
            "one": {"$ref": "#/definitions/job-attachment"},
            "many": {"type": "array", "items": {"$ref": "#/definitions/job-attachment"}},
            "text": {"type": "string"},
        },
        "definitions": {"job-attachment": ATTACHMENT},
    }
    assert sorted(attachment_fields(schema)) == ["many", "one"]


def test_assert_inputs_referenced_requires_matching_token():
    agent = {
        "messages": [
            {"role": "system", "content": "s", "contentTokens": []},
            {
                "role": "user",
                "content": "{{input.po.poNumber}}",
                "contentTokens": [{"type": "variable", "rawString": "input.po.poNumber"}],
            },
        ]
    }
    assert_inputs_referenced(agent, ["po"])
    agent["messages"][1]["contentTokens"] = [{"type": "simpleText", "rawString": "{{input.po.poNumber}}"}]
    with pytest.raises(SystemExit):
        assert_inputs_referenced(agent, ["po"])


def test_require_resource_locates_by_content(tmp_path):
    res = tmp_path / "resources" / "Read Invoice"
    res.mkdir(parents=True)
    (res / "resource.json").write_text(
        json.dumps(
            {
                "$resourceType": "tool",
                "type": "internal",
                "id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427",
                "isEnabled": True,
                "properties": {"toolType": "analyze-attachments"},
            }
        )
    )
    path, _ = require_resource(tmp_path, is_file_reading_tool, "file tool")
    assert path.parent.name == "Read Invoice"
    with pytest.raises(SystemExit):
        require_resource(tmp_path, lambda d: d.get("$resourceType") == "escalation", "escalation")


def _is_tool(conn_id):
    return {
        "iconUrl": "https://example.com/icon",
        "properties": {
            "toolPath": "/curated_create_issue",
            "method": "POST",
            "parameters": [],
            "connection": {
                "id": conn_id,
                "name": "jira",
                "isDefault": False,
                "folder": {"key": "f", "path": "f"},
                "solutionProperties": {"resourceKey": conn_id},
            },
        },
    }


def test_integration_wiring_rejects_placeholder_connection_id():
    assert_integration_wiring(_is_tool("f5273a4d-d492-4bcd-a106-5a20bf89a3ef"))
    with pytest.raises(SystemExit):
        assert_integration_wiring(_is_tool("00000000-0000-0000-0000-000000000000"))


def _project(root, sol, agent, project_id, projects):
    (root / sol / agent).mkdir(parents=True)
    (root / sol / agent / "agent.json").write_text(json.dumps({"projectId": project_id}))
    (root / sol / f"{sol}.uipx").write_text(json.dumps({"Projects": [{"ProjectRelativePath": p} for p in projects]}))
    return root / sol / agent


def test_assert_existing_project(tmp_path):
    fixture = _project(tmp_path / "fx", "Sol", "Agent", "id-1", ["Agent/project.uiproj"])
    same = _project(tmp_path / "ok", "Sol", "Agent", "id-1", ["Agent/project.uiproj"])
    assert_existing_project(same, fixture)
    recreated = _project(tmp_path / "re", "Sol", "Agent", "id-2", ["Agent/project.uiproj"])
    with pytest.raises(SystemExit):
        assert_existing_project(recreated, fixture)
    extra = _project(tmp_path / "ex", "Sol", "Agent", "id-1", ["Agent/project.uiproj", "Agent2/project.uiproj"])
    with pytest.raises(SystemExit):
        assert_existing_project(extra, fixture)


def test_require_input_matches_aliases_and_type():
    schema = {"type": "object", "properties": {"supplier_name": {"type": "string"}, "po": {"type": "object"}}}
    assert require_input(schema, "supplier", "supplierName") == "supplier_name"
    assert require_input(schema, "po", "purchaseOrder", "po", type_="object") == "po"
    with pytest.raises(SystemExit):
        require_input(schema, "po", "po", type_="string")
    with pytest.raises(SystemExit):
        require_input(schema, "country", "country")


def test_strip_schema_ignores_text_and_empty_required():
    a = {"type": "object", "properties": {"x": {"type": "string", "description": "d", "title": "t"}}, "required": []}
    assert strip_schema(a) == {"type": "object", "properties": {"x": {"type": "string"}}}
