#!/usr/bin/env python3
"""Shared scaffold helpers for uipath-review coded-agent tests.

Writes a minimal-but-valid coded agent project directly (no `uip
codedagent new` / uv venv / package install). The reviewer does
read-only static analysis, so a statically-written project is enough
to exercise the uipath-review pipeline (the `uip codedagent review` CLI
plus the judgment agents-coded-rules.md catalog) fast.

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


# ---------------------------------------------------------------------------
# LangChain (LangGraph) baseline — for coded guardrail review tasks.
#
# A clean, correctly-wired LangChain agent: guardrail symbols imported from
# `uipath_langchain.guardrails` (registers the LangChain adapter), a PII guardrail
# decorating the LLM factory. Guardrail review tasks pass their own `graph_py`
# variant to exercise a specific rule (wrong import, missing/ineffective/misapplied
# guardrail).
# ---------------------------------------------------------------------------

BASELINE_LANGCHAIN_GRAPH = '''from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from uipath_langchain.chat import UiPathChat
from uipath_langchain.guardrails import (
    BlockAction,
    GuardrailExecutionStage,
    PIIDetectionEntity,
    PIIDetectionEntityType,
    PIIValidator,
    guardrail,
)

SYSTEM_PROMPT = (
    "You are a customer-support assistant. Answer the customer's question, "
    "using the lookup_order tool when an order status is requested."
)


class Input(BaseModel):
    message: str = Field(description="The customer's message")
    customer_email: str = Field(description="The customer's email address")


class Output(BaseModel):
    reply: str = Field(description="The reply to send to the customer")


@tool
def lookup_order(order_id: str) -> str:
    """Look up an order's status by its order id."""
    return f"Order {order_id}: shipped"


@guardrail(
    validator=PIIValidator(
        entities=[PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5)],
    ),
    action=BlockAction(),
    name="PII detection",
    stage=GuardrailExecutionStage.PRE,
)
def create_llm():
    return UiPathChat(model="gpt-4o-2024-08-06")


graph = create_agent(
    model=create_llm(),
    tools=[lookup_order],
    system_prompt=SYSTEM_PROMPT,
)
'''

BASELINE_LANGCHAIN_PYPROJECT = '''[project]
name = "langchain-agent"
version = "0.1.0"
description = "A sample LangChain coded agent for guardrail review testing"
requires-python = ">=3.11"
authors = [{ name = "Test Fixture" }]
dependencies = ["uipath", "uipath-langchain", "langchain", "langgraph"]
'''


def write_baseline_langchain_agent(root: Path, *, graph_py: str | None = None) -> None:
    """Write a LangChain (LangGraph) coded agent at `root`.

    Pass `graph_py` to override the entry source (`graph.py`) for a specific
    guardrail-review scenario; defaults to the clean, correctly-wired baseline.
    """
    root.mkdir(parents=True, exist_ok=True)

    (root / "graph.py").write_text(
        graph_py if graph_py is not None else BASELINE_LANGCHAIN_GRAPH,
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        BASELINE_LANGCHAIN_PYPROJECT, encoding="utf-8"
    )
    (root / "langgraph.json").write_text(
        json.dumps(
            {"dependencies": ["."], "graphs": {"agent": "./graph.py:graph"}},
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "uipath.json").write_text(
        json.dumps(
            {
                "$schema": "https://cloud.uipath.com/draft/2024-12/uipath",
                "runtimeOptions": {"isConversational": False},
                "packOptions": {"includeUvLock": True},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
