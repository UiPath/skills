#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject CODED_ERROR_HANDLING.

Overwrites main.py so the entry point makes an external LLM call
(`await llm.ainvoke(...)`) with no try/except, fallback, retry, or
error-state surfacing. The judgment rule fires on risky external-call
sites left unguarded — identifying the boundary and its (missing) handling
requires reading the code, not a regex.
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
from coded_scaffold import write_baseline_function_agent  # noqa: E402

MAIN_PY = '''from pydantic import BaseModel, Field
from uipath.tracing import traced
from uipath_langchain.chat_models import UiPathChat


class Input(BaseModel):
    message: str = Field(description="The message to process")


class Output(BaseModel):
    result: str = Field(description="The processed result")


@traced()
async def main(input: Input) -> Output:
    """Process the input message with an LLM and return the result."""
    llm = UiPathChat(model="gpt-4o-2024-11-20")
    response = await llm.ainvoke(input.message)
    return Output(result=response.content)
'''


def main() -> None:
    root = Path("CodedAgent")
    write_baseline_function_agent(root)
    (root / "main.py").write_text(MAIN_PY, encoding="utf-8")
    print("Injected unguarded external LLM call (await llm.ainvoke with no try/except)")


if __name__ == "__main__":
    main()
