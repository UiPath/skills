from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_simulation_crud.py")

# The shape `uip maestro flow eval simulation add --strategy Llm` writes after
# resolving it from an agent node declaring `agentOutputVariables: [{id: result,
# type: string}]`. Captured from a real CLI run (uip 1.204.0).
RESOLVED_SCHEMA = {"type": "object", "properties": {"result": {"type": "string"}}}


def _eval_set(*, output_schema: object, keep_removed: bool = False) -> dict:
    simulations: list[dict] = [
        {
            "componentId": "agent-lookup",
            "componentType": "agent",
            "simulationStrategy": "Llm",
            "simulationInstruction": "Return a plausible lookup result.",
            "outputSchema": output_schema,
        }
    ]
    if keep_removed:
        simulations.append(
            {
                "componentId": "connector-send-email",
                "componentType": "connector",
                "simulationStrategy": "Static",
                "mockValue": {"status": "ok"},
            }
        )
    return {
        "name": "Sim Set",
        "evaluations": [
            {
                "name": "hello",
                "inputs": {"name": "Alice"},
                "expectedOutput": {"greeting": "Hello, Alice!"},
                "simulations": simulations,
            }
        ],
    }


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(tmp_path: Path, doc: dict) -> None:
    (tmp_path / "evaluation-set-sim-set.json").write_text(
        json.dumps(doc), encoding="utf-8"
    )


def test_accepts_the_cli_resolved_schema(tmp_path: Path) -> None:
    _write(tmp_path, _eval_set(output_schema=RESOLVED_SCHEMA))

    result = _run(tmp_path, "--check", "llm-simulation")

    assert result.returncode == 0, result.stdout + result.stderr


def test_rejects_wrong_property_type(tmp_path: Path) -> None:
    _write(
        tmp_path,
        _eval_set(
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "number"}},
            }
        ),
    )

    assert _run(tmp_path, "--check", "llm-simulation").returncode == 1


def test_rejects_null_property(tmp_path: Path) -> None:
    _write(
        tmp_path,
        _eval_set(output_schema={"type": "object", "properties": {"result": None}}),
    )

    assert _run(tmp_path, "--check", "llm-simulation").returncode == 1


def test_rejects_property_under_a_non_object_schema(tmp_path: Path) -> None:
    _write(
        tmp_path,
        _eval_set(
            output_schema={
                "type": "string",
                "properties": {"result": {"type": "string"}},
            }
        ),
    )

    assert _run(tmp_path, "--check", "llm-simulation").returncode == 1


def test_rejects_a_differently_named_output(tmp_path: Path) -> None:
    _write(
        tmp_path,
        _eval_set(
            output_schema={
                "type": "object",
                "properties": {"other": {"type": "string"}},
            }
        ),
    )

    assert _run(tmp_path, "--check", "llm-simulation").returncode == 1


def test_static_absent_rejects_a_surviving_removal_target(tmp_path: Path) -> None:
    _write(
        tmp_path, _eval_set(output_schema=RESOLVED_SCHEMA, keep_removed=True)
    )

    assert _run(tmp_path, "--check", "static-absent").returncode == 1
    assert _run(tmp_path).returncode == 1
