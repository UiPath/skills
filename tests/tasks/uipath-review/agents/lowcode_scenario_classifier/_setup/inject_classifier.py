#!/usr/bin/env python3
"""Email classifier with closed-class output, settings and eval defects."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    llm_judge_evaluator,
    string_props,
    write_baseline_lowcode_agent,
    write_evals,
)

SYSTEM = """You are an email routing agent for customer support. Read the email and pick the queue that must handle it.

Classify into: Billing, Technical, Cancellation, Feedback.

Billing is for invoices, charges and refunds. Technical is for errors and outages. Cancellation is for requests to end a subscription. Feedback is for praise and suggestions.

If the email is empty, return Feedback. Return JSON with `category`."""

USER = """Email subject: {{input.email_subject}}
Email body: {{input.email_body}}

Example of correct output: {"category": "Billing"}"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({
        "email_subject": "Subject line of the customer email.",
        "email_body": "Plain-text body of the customer email.",
    }),
    "required": ["email_subject", "email_body"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["Billing", "Technical", "Cancellation"],
            "description": "Support queue that must handle the email.",
        },
    },
    "required": ["category"],
}

SETTINGS = {"temperature": 0.9, "maxTokens": 16384, "maxIterations": 3}

BODY = "I was charged twice for my March invoice and the app also showed an error when I tried to pay."


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA,
                output_schema=OUTPUT_SCHEMA, settings=SETTINGS)
    write_evals(
        project,
        [llm_judge_evaluator("Category similarity", "Score 0-100 by semantic similarity to the expected category.")],
        [
            {"name": "double-charge", "inputs": {"email_subject": "Charged twice", "email_body": BODY},
             "expectedOutput": {"category": "Billing"}},
            {"name": "double-charge-2", "inputs": {"email_subject": "Charged twice!", "email_body": BODY + " Please help."},
             "expectedOutput": {"category": "Technical"}},
            {"name": "login-error", "inputs": {"email_subject": "Login error",
             "email_body": "The app shows error 500 when I sign in."}, "expectedOutput": {"category": "Technical"}},
        ],
    )
    print("Injected classifier scenario")


if __name__ == "__main__":
    main()
