#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject CODED_PII_IN_TRACES.

Overwrites main.py with a `@traced()` helper whose parameters clearly carry
PII (email_body, customer_email) and that lacks `hide_input=` /
`input_processor=`. The judgment rule fires when traced functions receive
PII-suggesting fields without redaction — inferring "is this PII" from
parameter names is a semantic read, not a regex.
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


class Input(BaseModel):
    customer_email: str = Field(description="Customer email address")
    email_body: str = Field(description="Body of the customer email")


class Output(BaseModel):
    summary: str = Field(description="Summary of the email")


@traced()
def summarize_email(email_body: str, customer_email: str) -> str:
    """Summarize the customer email for triage."""
    return email_body[:100]


@traced()
async def main(input: Input) -> Output:
    """Summarize an incoming customer email."""
    return Output(summary=summarize_email(input.email_body, input.customer_email))
'''


def main() -> None:
    root = Path("CodedAgent")
    write_baseline_function_agent(root)
    (root / "main.py").write_text(MAIN_PY, encoding="utf-8")
    print("Injected @traced helper with PII params (email_body/customer_email) and no hide_input")


if __name__ == "__main__":
    main()
