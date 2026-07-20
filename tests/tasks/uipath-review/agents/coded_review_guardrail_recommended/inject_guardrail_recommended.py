#!/usr/bin/env python3
"""Scaffold a LangChain coded agent that handles PII but wires NO guardrail.

The input schema carries `customer_email` and `ssn` and the agent takes free-text
user input, so the catalog's `pii_detection` (and `prompt_injection`) use cases
match — but no guardrail is wired. `uip codedagent review` returns the agent
guardrail-clean (nothing to flag deterministically), so the reviewer must fetch
the live catalog (Recommend Mode) and emit `CODED_GUARDRAIL_RECOMMENDED`.
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
    print("Scaffolded LangChain agent handling PII (email, ssn) with no guardrail wired")


if __name__ == "__main__":
    main()
