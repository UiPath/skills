"""Regression tests for semantic parity across live and SDK Flow artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


TASK_ROOT = Path(__file__).resolve().parent.parent


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _run(relative: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASK_ROOT / relative)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _filter_tree() -> dict:
    return {
        "groupOperator": 1,
        "index": 0,
        "filters": [
            {"id": "active", "operator": "Equals", "value": {"value": True}},
            {"id": "score", "operator": "GreaterThanOrEqual", "value": {"value": 8.5}},
            {"id": "viewCount", "operator": "GreaterThanOrEqual", "value": {"value": 1000}},
            {"id": "title", "operator": "Equals", "value": {"value": "FilterFixture-Matrix"}},
            {"id": "description", "operator": "Contains", "value": {"value": "sci-fi"}},
            {"id": "releaseDate", "operator": "LessThan", "value": {"value": "2025-01-01"}},
            {"id": "lastUpdated", "operator": "GreaterThanOrEqual", "value": {"value": "2024-01-01"}},
            {"id": "externalId", "operator": "Equals", "value": {"value": "7f4d8f1e-5c2b-4a6e-9d31-2b7c8e0f1a45"}},
            {"id": "description", "operator": "IsNull", "value": {"value": None}},
        ],
        "groups": [],
    }


def _query_detail(representation: str, *, start: int, ascending: bool) -> dict:
    detail = {
        "bodyParameters": {"_sortFieldName": "score"},
        "queryParameters": {
            "queryExpression": (
                "active = true OR score >= 8.5 OR viewCount >= 1000 OR "
                "title = 'FilterFixture-Matrix' OR description LIKE '%sci-fi%' OR "
                "releaseDate < '2025-01-01' OR lastUpdated >= '2024-01-01' OR "
                "externalId = '7f4d8f1e-5c2b-4a6e-9d31-2b7c8e0f1a45' OR description IS NULL"
            ),
            "start": start,
            "limit": 2,
            "isAscending": ascending,
        },
    }
    if representation == "sdk":
        detail["filter"] = _filter_tree()
    elif representation == "live":
        detail["configuration"] = "=jsonString:" + json.dumps(
            {"essentialConfiguration": {"savedFilterTrees": {"queryExpression": _filter_tree()}}}
        )
    return detail


@pytest.mark.parametrize("representation", ["live", "sdk"])
def test_smoke_query_accepts_both_filter_tree_locations(
    tmp_path: Path, representation: str
) -> None:
    details = [
        _query_detail(representation, start=0, ascending=True),
        _query_detail(representation, start=2, ascending=True),
        _query_detail(representation, start=0, ascending=False),
    ]
    _write_json(
        tmp_path / "queries.flow",
        {
            "nodes": [
                {
                    "type": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
                    "inputs": {"detail": detail},
                }
                for detail in details
            ]
        },
    )

    result = _run("connector_features/datafabric_connector/check_smoke_query_filter.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


def test_smoke_query_rejects_runtime_text_without_contains_operator(tmp_path: Path) -> None:
    details = [
        _query_detail("runtime-only", start=0, ascending=True),
        _query_detail("runtime-only", start=2, ascending=True),
        _query_detail("runtime-only", start=0, ascending=False),
    ]
    _write_json(
        tmp_path / "queries.flow",
        {
            "nodes": [
                {
                    "type": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
                    "inputs": {"detail": detail},
                }
                for detail in details
            ]
        },
    )

    result = _run("connector_features/datafabric_connector/check_smoke_query_filter.py", tmp_path)

    assert result.returncode != 0
    assert "multiline" in result.stderr


def _lifecycle_flow(representation: str, *, query_entity: str = "ContractRegistry") -> dict:
    def entity_detail(name: str, extra: dict | None = None) -> dict:
        value = ({"entityName": name} if representation == "sdk"
                 else {"pathParameters": {"entityName": name}})
        value.update(extra or {})
        return value

    return {
        "nodes": [
            {
                "id": "created",
                "type": "uipath.connector.trigger.uipath-uipath-dataservice.record-created",
                "inputs": {"detail": {
                    "objectName": "ContractRegistry",
                    "filterExpression": "dueDate < '2026-08-04'",
                }},
            },
            {
                "id": "query",
                "type": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
                "inputs": {"detail": entity_detail(query_entity, {"queryParameters": {
                    "queryExpression": "dueDate < '2026-08-04'", "limit": 100,
                }})},
            },
            {
                "id": "updated",
                "type": "uipath.connector.trigger.uipath-uipath-dataservice.record-updated",
                "inputs": {"detail": {"objectName": "FileUploadVerify_20260618"}},
            },
            {
                "id": "get",
                "type": "uipath.connector.uipath-uipath-dataservice.get-entity-record-by-id",
                "inputs": {"detail": entity_detail("FileUploadVerify_20260618", {
                    "queryParameters": {"recordId": "=js:$vars.updated.output.Id"},
                })},
            },
            {
                "id": "delete",
                "type": "uipath.connector.uipath-uipath-dataservice.delete-entity-record",
                "inputs": {"detail": entity_detail("FileUploadVerify_20260618", {
                    "queryParameters": {"recordId": "=js:$vars.get.output.Id"},
                })},
            },
        ]
    }


@pytest.mark.parametrize("representation", ["live", "sdk"])
def test_trigger_lifecycle_accepts_both_entity_locations(
    tmp_path: Path, representation: str
) -> None:
    _write_json(tmp_path / "lifecycle.flow", _lifecycle_flow(representation))

    result = _run("connector_features/datafabric_connector/check_trigger_lifecycle.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


def test_trigger_lifecycle_rejects_wrong_query_entity(tmp_path: Path) -> None:
    _write_json(tmp_path / "lifecycle.flow", _lifecycle_flow("sdk", query_entity="Other"))

    result = _run("connector_features/datafabric_connector/check_trigger_lifecycle.py", tmp_path)

    assert result.returncode != 0
    assert "Query Entity Records" in result.stderr


def _where_plan() -> dict:
    return {
        "filter": {
            "groupOperator": 0,
            "filters": [
                {"id": "displayName", "operator": "Equals", "value": {"value": "active"}}
            ],
        }
    }


@pytest.mark.parametrize("representation", ["live", "sdk"])
def test_ceql_where_accepts_curated_and_generic_groups_operations(
    tmp_path: Path, representation: str
) -> None:
    if representation == "live":
        connector = {
            "type": "uipath.connector.uipath-microsoft-azureactivedirectory.list-groups",
            "inputs": {"detail": {}},
        }
    else:
        connector = {
            "type": "uipath.connector.uipath-microsoft-azureactivedirectory.list-all-records",
            "inputs": {"detail": {"objectName": "groups", "endpoint": "/groups"}},
        }
    _write_json(tmp_path / "where_detail.json", _where_plan())
    _write_json(
        tmp_path / "CeqlWhereTest.flow",
        {"nodes": [connector, {"type": "core.logic.terminate"}], "edges": []},
    )

    result = _run("connector_features/check_ceql_where_flow.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


def test_ceql_where_rejects_generic_operation_for_another_object(tmp_path: Path) -> None:
    _write_json(tmp_path / "where_detail.json", _where_plan())
    _write_json(
        tmp_path / "CeqlWhereTest.flow",
        {
            "nodes": [
                {
                    "type": "uipath.connector.uipath-microsoft-azureactivedirectory.list-all-records",
                    "inputs": {"detail": {"objectName": "users", "endpoint": "/users"}},
                },
                {"type": "core.logic.terminate"},
            ],
            "edges": [],
        },
    )

    result = _run("connector_features/check_ceql_where_flow.py", tmp_path)

    assert result.returncode != 0
    assert "list-groups" in result.stderr
