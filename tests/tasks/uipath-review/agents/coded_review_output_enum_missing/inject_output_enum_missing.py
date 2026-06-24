#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject
CODED_OUTPUT_ENUM_MISSING_ON_CLASSIFIER.

Overwrites main.py with a classifier whose output field `classification` is
a bare `str` (no Literal / Enum / pattern) even though the agent maps to a
small fixed set (Billing / Technical / Account). The judgment rule fires
when an output field is classifier-shaped by name AND the agent's logic maps
to an enumerated set — recognizing the classifier shape is a semantic read.
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
    email_body: str = Field(description="The support email to triage")


class Output(BaseModel):
    classification: str = Field(description="One of: Billing, Technical, or Account")


@traced()
async def main(input: Input) -> Output:
    """Classify the support email into exactly one of: Billing, Technical, Account."""
    text = input.email_body.lower()
    if "invoice" in text or "charge" in text:
        label = "Billing"
    elif "password" in text or "error" in text:
        label = "Technical"
    else:
        label = "Account"
    return Output(classification=label)
'''


def main() -> None:
    root = Path("CodedAgent")
    write_baseline_function_agent(root)
    (root / "main.py").write_text(MAIN_PY, encoding="utf-8")
    print("Injected classifier with bare-str output field 'classification' (no Literal/Enum)")


if __name__ == "__main__":
    main()
