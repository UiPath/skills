from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SINGLE_NODE = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    ("task", "flow_name", "node_type", "inputs"),
    [
        (
            "transform_map",
            "TransformMapDemo.flow",
            "core.action.transform.map",
            {
                "collection": "$vars.people",
                "operations": [
                    {
                        "type": "map",
                        "config": {
                            "mappings": [{"field": "name", "transformation": "uppercase"}]
                        },
                    }
                ],
            },
        ),
        (
            "transform_filter",
            "TransformFilterDemo.flow",
            "core.action.transform.filter",
            {
                "collection": "$vars.items",
                "operations": [
                    {
                        "type": "filter",
                        "config": {
                            "filters": [
                                {"field": "amount", "condition": "greater_equal", "value": 100}
                            ]
                        },
                    }
                ],
            },
        ),
        (
            "transform_group_by",
            "TransformGroupByDemo.flow",
            "core.action.transform.group-by",
            {
                "collection": "$vars.employees",
                "operations": [
                    {
                        "type": "groupBy",
                        "config": {
                            "groupByField": "department",
                            "aggregations": [{"operation": "count", "alias": "headcount"}],
                        },
                    }
                ],
            },
        ),
    ],
)
def test_transform_checkers_accept_sdk_literal_output_envelopes(
    tmp_path: Path, task: str, flow_name: str, node_type: str, inputs: dict
) -> None:
    flow = {
        "nodes": [
            {
                "id": "transform",
                "type": node_type,
                "typeVersion": "1.0.0",
                "inputs": inputs,
                "outputs": {
                    "output": {
                        "source": {
                            "type": "literal",
                            "expression": "=result.response",
                            "fieldType": "string",
                        }
                    },
                    "error": {
                        "source": {
                            "type": "literal",
                            "expression": "=Error",
                            "fieldType": "string",
                        }
                    },
                },
            }
        ]
    }
    (tmp_path / flow_name).write_text(json.dumps(flow))

    result = subprocess.run(
        [sys.executable, str(SINGLE_NODE / task / f"check_{task}_flow.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
