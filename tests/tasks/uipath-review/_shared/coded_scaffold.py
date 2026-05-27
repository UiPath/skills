#!/usr/bin/env python3
"""Shared scaffold helpers for uipath-review coded-agent tests.

Writes a minimal-but-valid coded agent project directly (no `uip
codedagent new` / uv venv / package install). The reviewer does
read-only static analysis, so a statically-written project is enough
to exercise the agents-coded-rules.md catalog deterministically and
fast.

The baseline FUNCTION (Simple Function) agent mirrors what
`uip codedagent new` + `uip codedagent init` produce:
  - main.py        Input/Output Pydantic models + async def main
  - pyproject.toml [project] metadata, no [build-system]
  - uipath.json    functions.main = "main.py:main"
  - entry-points.json  one entrypoint with input/output schemas
  - bindings.json  v2.0 envelope, zero resources
"""

import json
from pathlib import Path

BASELINE_MAIN_PY = '''from pydantic import BaseModel, Field
from uipath.tracing import traced


class Input(BaseModel):
    message: str = Field(description="The message to process")


class Output(BaseModel):
    result: str = Field(description="The processed result")


@traced()
async def main(input: Input) -> Output:
    """Process the input message and return a result."""
    return Output(result=input.message)
'''

BASELINE_PYPROJECT = '''[project]
name = "coded-agent"
version = "0.1.0"
description = "A sample coded function agent for review testing"
requires-python = ">=3.11"
authors = [{ name = "Test Fixture" }]
dependencies = ["uipath"]
'''


def write_baseline_function_agent(root: Path) -> None:
    """Write a clean FUNCTION (Simple Function) coded agent at `root`."""
    root.mkdir(parents=True, exist_ok=True)

    (root / "main.py").write_text(BASELINE_MAIN_PY, encoding="utf-8")
    (root / "pyproject.toml").write_text(BASELINE_PYPROJECT, encoding="utf-8")

    (root / "uipath.json").write_text(
        json.dumps(
            {
                "$schema": "https://cloud.uipath.com/draft/2024-12/uipath",
                "runtimeOptions": {"isConversational": False},
                "packOptions": {
                    "fileExtensionsIncluded": [],
                    "filesIncluded": [],
                    "filesExcluded": [],
                    "directoriesExcluded": [".venv"],
                    "includeUvLock": True,
                },
                "functions": {"main": "main.py:main"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (root / "entry-points.json").write_text(
        json.dumps(
            {
                "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
                "$id": "entry-points.json",
                "entryPoints": [
                    {
                        "filePath": "main",
                        "uniqueId": "11111111-1111-4111-1111-111111111111",
                        "type": "agent",
                        "input": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The message to process",
                                }
                            },
                            "required": ["message"],
                        },
                        "output": {
                            "type": "object",
                            "properties": {
                                "result": {
                                    "type": "string",
                                    "description": "The processed result",
                                }
                            },
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (root / "bindings.json").write_text(
        json.dumps({"version": "2.0", "resources": []}, indent=2),
        encoding="utf-8",
    )
