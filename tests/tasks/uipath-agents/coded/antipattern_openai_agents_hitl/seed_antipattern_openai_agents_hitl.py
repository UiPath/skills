#!/usr/bin/env python3
"""Seed the broken OpenAI Agents HITL project for the brownfield edit task."""

from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd() / "triage-broken"


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "pyproject.toml").write_text(
        """[project]
name = "triage-broken"
version = "0.0.1"
description = "Triage bot (in-flight edit)"
authors = [{ name = "Test" }]
requires-python = ">=3.11"
dependencies = ["uipath", "uipath-openai-agents"]

[dependency-groups]
dev = ["uipath-dev"]
""",
        encoding="utf-8",
    )
    (ROOT / "main.py").write_text(
        """from agents import Agent, RunContextWrapper
from pydantic import BaseModel
from langgraph.types import interrupt


class CustomerCtx(BaseModel):
    customer_id: str


def _maybe_pause(ctx: RunContextWrapper[CustomerCtx]) -> str:
    decision = interrupt({"prompt": "Approve handoff?", "customer": ctx.context.customer_id})
    return decision.get("status", "pending")


billing = Agent[CustomerCtx](
    name="billing",
    instructions="Handle billing questions.",
)

technical = Agent[CustomerCtx](
    name="technical",
    instructions="Handle technical questions.",
)


def main() -> Agent[CustomerCtx]:
    return Agent[CustomerCtx](
        name="triage",
        instructions="Route to billing or technical, but call _maybe_pause first.",
        handoffs=[billing, technical],
    )
""",
        encoding="utf-8",
    )
    (ROOT / "openai_agents.json").write_text(
        '{"agents": {"agent": "./main.py:main"}}\n',
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
