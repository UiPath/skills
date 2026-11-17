#!/usr/bin/env python3
"""Order-status agent with write, destructive and admin tools."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    equality_evaluator,
    string_props,
    write_baseline_lowcode_agent,
    write_bindings,
    write_escalation,
    write_evals,
    write_tool,
)

SYSTEM = """You are a customer service agent that answers customer questions about the status of their orders.

Use the tools to help the customer. You can use search_customers, send_email, delete_customer_record, validate_refund and submit_refund when needed.

Reply in `reply`."""

USER = "Customer message: {{input.message}}"

INPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({"message": "The customer's message in plain text."}),
    "required": ["message"],
}

OUTPUT_SCHEMA = {"type": "object", "properties": string_props({"reply": "Reply to send to the customer."})}

TOOLS = [
    ("search_customers",
     "Search customer records by name or email and return profile, home address, phone and order history. "
     "Use it to find the customer who sent the message.",
     {"query": "Customer name or email address."}, ["query"]),
    ("send_email", "Send an email.", {"to": "", "subject": "", "body": ""}, ["to", "subject", "body"]),
    ("delete_customer_record",
     "Permanently delete a customer record and all related orders. This cannot be undone.",
     {"record_ref": ""}, ["record_ref"]),
    ("validate_refund",
     "Check whether an order is eligible for a refund and return the eligible amount.",
     {"order_id": "Order ID: ORD- followed by eight digits."}, ["order_id"]),
    ("submit_refund",
     "Submit a refund by adding an item to the Refunds Orchestrator queue. The Refunds process pays it out.",
     {"order_id": "Order ID: ORD- followed by eight digits.", "amount": ""}, ["order_id", "amount"]),
]


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA,
                output_schema=OUTPUT_SCHEMA, settings={"temperature": 0.3, "maxTokens": 2048})
    bindings = [write_tool(project, name, desc, inputs, required=req) for name, desc, inputs, req in TOOLS]
    write_bindings(project, bindings)
    write_escalation(project, "SupervisorReview",
                     "Always escalate every response to a supervisor regardless of intent.",
                     "supervisor@example.com")
    write_evals(
        project,
        [equality_evaluator("Reply exact match")],
        [
            {"name": f"status-{i}", "inputs": {"message": msg}, "expectedOutput": {"reply": reply}}
            for i, (msg, reply) in enumerate([
                ("Where is order ORD-00001234?", "Your order ORD-00001234 shipped yesterday."),
                ("Has my refund for ORD-00004321 been paid?", "The refund was paid on Monday."),
                ("Please delete my account.", "I have passed your request to our team."),
                ("Can I change my delivery address?", "Yes, reply with the new address."),
                ("Is ORD-00005555 delayed?", "Yes, it ships next week."),
            ])
        ],
    )
    print("Injected ops actions scenario")


if __name__ == "__main__":
    main()
