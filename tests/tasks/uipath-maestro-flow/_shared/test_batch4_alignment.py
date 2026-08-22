"""Regression coverage for Batch 4 same-ground checker routing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flow_check import assert_no_flow_files  # noqa: E402

TASK_ROOT = Path(__file__).resolve().parent.parent


def _write_flow(path: Path, nodes: list[dict], **extra) -> None:
    path.write_text(json.dumps({"nodes": nodes, "edges": [], **extra}), encoding="utf-8")


def _run(relative: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASK_ROOT / relative)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_no_flow_assertion_accepts_empty_sandbox(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert_no_flow_files()


def test_no_flow_assertion_rejects_nested_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "Solution" / "Project"
    nested.mkdir(parents=True)
    _write_flow(nested / "Unexpected.flow", [])

    with pytest.raises(SystemExit, match="Unexpected .flow"):
        assert_no_flow_files()


def test_flow_contains_expect_none_cli(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "flow_contains.py"), "--expect-none"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_ixp_project_selection_accepts_root_sdk_emit(tmp_path: Path) -> None:
    row = tmp_path / "skill-flow-ixp-e2e-project-selection" / "aviation"
    row.mkdir(parents=True)
    model = "aviation-investigation-final-report-demo-a42b1d4d-ixp"
    _write_flow(
        row / "Aviation.flow",
        [
            {
                "id": "extract",
                "type": f"uipath.ixp.{model}.extract",
                "inputs": {"modelName": model},
            }
        ],
    )

    result = _run("ixp/check_project_selection.py", cwd=row)

    assert result.returncode == 0, result.stderr or result.stdout


def test_ixp_project_selection_rejects_mismatched_model(tmp_path: Path) -> None:
    row = tmp_path / "skill-flow-ixp-e2e-project-selection" / "birth-certificate"
    row.mkdir(parents=True)
    _write_flow(
        row / "Birth.flow",
        [
            {
                "id": "extract",
                "type": "uipath.ixp.wrong-model.extract",
                "inputs": {"modelName": "wrong-model"},
            }
        ],
    )

    result = _run("ixp/check_project_selection.py", cwd=row)

    assert result.returncode == 1


@pytest.mark.parametrize("typed_envelopes", [False, True])
def test_batch_transform_checker_accepts_equivalent_expression_shapes(
    tmp_path: Path, typed_envelopes: bool
) -> None:
    attachment = (
        {
            "type": "jsExpression",
            "expression": "$vars.trigger.output.csvFile",
            "fieldType": "string",
        }
        if typed_envelopes
        else "=js:$vars.trigger.output.csvFile"
    )
    output_source = (
        {"type": "literal", "expression": "=response", "fieldType": "string"}
        if typed_envelopes
        else "=response"
    )
    result_source = (
        {
            "type": "jsExpression",
            "expression": "$vars.batch.output",
            "fieldType": "string",
        }
        if typed_envelopes
        else "=js:$vars.batch.output"
    )
    _write_flow(
        tmp_path / "BatchTransformDemo.flow",
        [
            {"id": "trigger", "type": "core.trigger.manual"},
            {
                "id": "batch",
                "type": "uipath.pattern.batch-transform",
                "typeVersion": "1.0",
                "inputs": {
                    "attachment": attachment,
                    "prompt": "Classify each row",
                    "outputColumns": [
                        {"name": "Category", "description": "classification"}
                    ],
                },
                "outputs": {"output": {"source": output_source}},
            },
            {
                "id": "end",
                "type": "core.control.end",
                "outputs": {"result": {"source": result_source}},
            },
        ],
        variables={
            "globals": [
                {
                    "id": "csvFile",
                    "direction": "in",
                    "type": "file",
                    "triggerNodeId": "trigger",
                },
                {"id": "result", "direction": "out", "type": "file"},
            ]
        },
    )

    result = _run(
        "context-grounding/batch_transform/check_batch_transform_flow.py",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize("typed_envelopes", [False, True])
def test_summarize_checker_accepts_equivalent_expression_shapes(
    tmp_path: Path, typed_envelopes: bool
) -> None:
    attachment = (
        {
            "type": "jsExpression",
            "expression": "$vars.trigger.output.documentFile",
            "fieldType": "string",
        }
        if typed_envelopes
        else "=js:$vars.trigger.output.documentFile"
    )
    output_source = (
        {"type": "literal", "expression": "=response", "fieldType": "string"}
        if typed_envelopes
        else "=response"
    )

    def output_mapping(field: str):
        expression = f"$vars.summary_node.output.content.{field}"
        if typed_envelopes:
            return {
                "type": "jsExpression",
                "expression": expression,
                "fieldType": "string",
            }
        return f"=js:{expression}"

    _write_flow(
        tmp_path / "SummarizeDemo.flow",
        [
            {"id": "trigger", "type": "core.trigger.manual"},
            {
                "id": "summary_node",
                "type": "uipath.pattern.deep-rag",
                "typeVersion": "1.0",
                "inputs": {
                    "attachment": attachment,
                    "prompt": "Summarize the document",
                    "returnCitations": True,
                },
                "outputs": {"output": {"source": output_source}},
            },
            {
                "id": "end",
                "type": "core.control.end",
                "outputs": {
                    "summary": {
                        "source": output_mapping("Text")
                    },
                    "citations": {
                        "source": output_mapping("Citations")
                    },
                },
            },
        ],
        variables={
            "globals": [
                {
                    "id": "documentFile",
                    "direction": "in",
                    "type": "file",
                    "triggerNodeId": "trigger",
                },
                {"id": "summary", "direction": "out", "type": "string"},
                {"id": "citations", "direction": "out", "type": "array"},
            ]
        },
    )

    result = _run(
        "context-grounding/summarize/check_summarize_flow.py",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout
