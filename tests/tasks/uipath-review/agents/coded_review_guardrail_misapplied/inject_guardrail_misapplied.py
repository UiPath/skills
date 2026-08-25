#!/usr/bin/env python3
"""Scaffold a LangChain coded agent with a MISAPPLIED guardrail.

The agent is a synthetic-test-data generator: its only input is `count` (no user
free-text, no real PII in), and its job is to produce fictional records. Yet it
wires a `pii_detection` guardrail — which matches the catalog's `when_not_to_use`
(the LLM never receives real PII; the generated PII is the intended product). `uip
codedagent review` returns it guardrail-clean, so the reviewer must fetch the live
catalog (Audit Mode → Relevance), read `pii_detection`'s `when_not_to_use`, and
cite `CODED_GUARDRAIL_MISAPPLIED`.
"""

import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from coded_scaffold import write_baseline_langchain_agent  # noqa: E402

PROJECT = Path("CodedAgent")

GRAPH = '''from langchain.agents import create_agent
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
    "You generate synthetic customer test records. Produce realistic but entirely "
    "fictional data — names, emails, and phone numbers that do not belong to any "
    "real person. You never receive real customer data."
)


class Input(BaseModel):
    count: int = Field(description="How many synthetic records to generate")


class Output(BaseModel):
    records: list[str] = Field(description="The generated synthetic records")


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
    tools=[],
    system_prompt=SYSTEM_PROMPT,
)
'''


def main() -> None:
    write_baseline_langchain_agent(PROJECT, graph_py=GRAPH)
    print("Scaffolded synthetic-data generator agent carrying a misapplied PII guardrail")


if __name__ == "__main__":
    main()
