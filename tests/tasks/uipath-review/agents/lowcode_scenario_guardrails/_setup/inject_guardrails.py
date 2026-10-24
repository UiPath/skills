#!/usr/bin/env python3
"""Notification agent with format-invalid and semantically wrong guardrails."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    builtin_guardrail,
    equality_evaluator,
    stable_id,
    string_props,
    write_baseline_lowcode_agent,
    write_bindings,
    write_evals,
    write_tool,
)

SYSTEM = """You are an account notification agent. You receive structured account data from the billing system and send the customer one notification email about their balance.

## Steps
1. Read the account fields in the user message.
2. Write a short, polite email that states the balance and the due date.
3. Call send_customer_email once with the customer's email address, a subject and the body.

## Scope
Only send balance notifications. Do not include the SSN in the email. If the balance is zero, do not send an email and return `sent: false`.

## Output format
Return JSON with `sent` (true or false) and `subject`."""

USER = """Customer: {{input.full_name}}
Email: {{input.customer_email}}
SSN: {{input.ssn}}
Balance: {{input.account_balance}}
Due date: {{input.due_date}}"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({
        "full_name": "Customer full name from the billing system.",
        "customer_email": "Customer email address from the billing system.",
        "ssn": "Customer social security number from the billing system.",
        "account_balance": "Open balance with currency, for example 120.00 USD.",
        "due_date": "Payment due date, ISO 8601 YYYY-MM-DD.",
    }),
    "required": ["full_name", "customer_email", "ssn", "account_balance", "due_date"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "sent": {"type": "boolean", "description": "True when the email was sent."},
        "subject": {"type": "string", "description": "Subject of the sent email."},
    },
}

PII_PARAMS = [
    {"$parameterType": "enum-list", "id": "entities", "value": ["Email", "Person"]},
    {"$parameterType": "map-enum", "id": "entityThresholds", "value": {"Email": 0.5, "Person": 0.5}},
]

GUARDRAILS = [
    builtin_guardrail("PII block on email tool", "pii_detection", ["Tool"],
                      {"$actionType": "block", "reason": "PII detected."}, parameters=PII_PARAMS,
                      match_names=["send_customer_email"]),
    builtin_guardrail("Prompt injection on system data", "prompt_injection", ["Llm"],
                      {"$actionType": "block", "reason": "Prompt injection detected."},
                      parameters=[{"$parameterType": "number", "id": "threshold", "value": 0.5}]),
    builtin_guardrail("Made-up validator", "totally_made_up_validator", ["Agent"],
                      {"$actionType": "block", "reason": "Blocked."}),
    {
        "$guardrailType": "custom",
        "id": stable_id("guardrail", "Custom bad operator"),
        "name": "Custom bad operator",
        "description": "Blocks subjects that resemble spam.",
        "enabledForEvals": True,
        "selector": {"scopes": ["Tool"], "matchNames": ["send_customer_email"]},
        "action": {"$actionType": "block", "reason": "Spam-like subject."},
        "rules": [{"$ruleType": "word", "fieldSelector": {"$selectorType": "all"},
                   "operator": "resembles", "value": "FREE MONEY"}],
    },
]


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA, output_schema=OUTPUT_SCHEMA,
                settings={"temperature": 0.3, "maxTokens": 1024, "maxIterations": 3}, guardrails=GUARDRAILS)
    binding = write_tool(
        project,
        "send_customer_email",
        "Send one email to a customer through the company mail service. Use it once per run to deliver the "
        "balance notification.",
        {"to": "Customer email address.", "subject": "Email subject line.", "body": "Plain-text email body."},
        required=["to", "subject", "body"],
        outputs={"message_id": "ID of the sent message."},
    )
    write_bindings(project, [binding])
    write_evals(
        project,
        [equality_evaluator("Sent exact match")],
        [
            {"name": f"acct{i}", "inputs": {"full_name": "Test Customer", "customer_email": f"c{i}@example.com",
             "ssn": "NNN-NN-NNNN", "account_balance": bal, "due_date": "<DUE_DATE>"},
             "expectedOutput": {"sent": sent}}
            for i, (bal, sent) in enumerate([("120.00 USD", True), ("0.00 USD", False), ("5.10 EUR", True),
                                             ("990.00 GBP", True), ("0.00 EUR", False)])
        ],
    )
    print("Injected guardrails scenario")


if __name__ == "__main__":
    main()
