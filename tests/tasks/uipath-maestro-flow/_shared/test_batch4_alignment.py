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
    path.write_text(
        json.dumps({"nodes": nodes, "edges": [], **extra}), encoding="utf-8"
    )


def _run(relative: str, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASK_ROOT / relative), *args],
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
        [
            sys.executable,
            str(Path(__file__).parent / "flow_contains.py"),
            "--expect-none",
        ],
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


# coder-eval 1.x runs graders from the bare workspace (/work), so e2e_02 passes
# the row id as argv[1]; these run from a cwd that names no row.
def _ixp_flow(path: Path, model: str, type_slug: str) -> None:
    _write_flow(
        path,
        [{"id": "extract", "type": f"uipath.ixp.{type_slug}.extract", "inputs": {"modelName": model}}],
    )


def test_ixp_project_selection_argv_accepts_matching_row(tmp_path: Path) -> None:
    model = "aviation-investigation-final-report-demo-a42b1d4d-ixp"
    _ixp_flow(tmp_path / "Aviation.flow", model, model)

    result = _run("ixp/check_project_selection.py", tmp_path, "aviation")

    assert result.returncode == 0, result.stderr or result.stdout


def test_ixp_project_selection_argv_rejects_mismatched_model(tmp_path: Path) -> None:
    _ixp_flow(tmp_path / "Birth.flow", "wrong-model", "wrong-model")

    result = _run("ixp/check_project_selection.py", tmp_path, "birth-certificate")

    assert result.returncode == 1


def test_ixp_project_selection_unknown_argv_does_not_fall_back_to_cwd(tmp_path: Path) -> None:
    row = tmp_path / "aviation"
    row.mkdir()
    model = "aviation-investigation-final-report-demo-a42b1d4d-ixp"
    _ixp_flow(row / "Aviation.flow", model, model)

    result = _run("ixp/check_project_selection.py", row, "bogus")

    assert result.returncode == 2
    assert "unknown dataset row" in result.stderr


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


def _write_summarize_flow(
    path: Path,
    typed_envelopes: bool = False,
    type_version: str = "1.0",
    carried_versions: tuple[str, ...] = ("1.0",),
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
        path,
        [
            {"id": "trigger", "type": "core.trigger.manual"},
            {
                "id": "summary_node",
                "type": "uipath.pattern.deep-rag",
                "typeVersion": type_version,
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
                    "summary": {"source": output_mapping("Text")},
                    "citations": {"source": output_mapping("Citations")},
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
        definitions=[
            {"nodeType": "uipath.pattern.deep-rag", "version": v}
            for v in carried_versions
        ],
    )


def _run_summarize(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return _run("context-grounding/summarize/check_summarize_flow.py", cwd=tmp_path)


@pytest.mark.parametrize("typed_envelopes", [False, True])
def test_summarize_checker_accepts_equivalent_expression_shapes(
    tmp_path: Path, typed_envelopes: bool
) -> None:
    _write_summarize_flow(tmp_path / "SummarizeDemo.flow", typed_envelopes)
    result = _run_summarize(tmp_path)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_summarize_checker_reads_version_from_carried_definition(
    tmp_path: Path, version: str
) -> None:
    _write_summarize_flow(
        tmp_path / "SummarizeDemo.flow",
        type_version=version,
        carried_versions=(version,),
    )
    result = _run_summarize(tmp_path)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize(
    ("type_version", "carried", "message"),
    [
        ("1.1", ("1.0",), "must equal"),
        ("1.0", (), "carries no"),
        ("1.0.0", ("1.0.0",), "MAJOR.MINOR"),
        ("0.9", ("0.9",), ">= 1.0"),
    ],
)
def test_summarize_checker_rejects_bad_type_version(
    tmp_path: Path, type_version: str, carried: tuple[str, ...], message: str
) -> None:
    _write_summarize_flow(
        tmp_path / "SummarizeDemo.flow",
        type_version=type_version,
        carried_versions=carried,
    )
    result = _run_summarize(tmp_path)
    assert result.returncode != 0
    assert message in (result.stderr + result.stdout)
