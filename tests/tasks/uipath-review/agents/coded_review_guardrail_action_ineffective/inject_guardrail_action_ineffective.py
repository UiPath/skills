#!/usr/bin/env python3
"""Scaffold a LangChain coded agent with an INEFFECTIVE guardrail action.

The agent receives PII (`ssn`, `customer_email`) and wires a `pii_detection`
guardrail on the LLM factory — but with `LogAction`, which only records the
violation and does not stop the PII from reaching the LLM. `uip codedagent review`
returns it guardrail-clean (the action is a real SDK class, well-formed), so the
reviewer must fetch the live catalog (Audit Mode → Actionability) and emit
`CODED_GUARDRAIL_ACTION_INEFFECTIVE` — PII protection at this scope needs a
blocking action, not log.
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
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from uipath_langchain.chat import UiPathChat
from uipath_langchain.guardrails import (
    GuardrailExecutionStage,
    LogAction,
    PIIDetectionEntity,
    PIIDetectionEntityType,
    PIIValidator,
    guardrail,
)
from uipath_langchain.guardrails.actions import LoggingSeverityLevel

SYSTEM_PROMPT = (
    "You are a customer-support assistant. Help the customer with their account "
    "questions using the lookup_account tool."
)


class Input(BaseModel):
    message: str = Field(description="The customer's free-text message")
    customer_email: str = Field(description="The customer's email address")
    ssn: str = Field(description="The customer's social security number")


class Output(BaseModel):
    reply: str = Field(description="The reply to send to the customer")


@tool
def lookup_account(account_id: str) -> str:
    """Look up an account by its id."""
    return f"Account {account_id}: active"


@guardrail(
    validator=PIIValidator(
        entities=[
            PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5),
            PIIDetectionEntity(PIIDetectionEntityType.US_SSN, 0.5),
        ],
    ),
    action=LogAction(severity_level=LoggingSeverityLevel.WARNING),
    name="PII detection",
    stage=GuardrailExecutionStage.PRE,
)
def create_llm():
    return UiPathChat(model="gpt-4o-2024-08-06")


graph = create_agent(
    model=create_llm(),
    tools=[lookup_account],
    system_prompt=SYSTEM_PROMPT,
)
'''


def main() -> None:
    write_baseline_langchain_agent(PROJECT, graph_py=GRAPH)
    print("Scaffolded LangChain agent with a PII guardrail using LogAction (ineffective at Llm scope)")


if __name__ == "__main__":
    main()
