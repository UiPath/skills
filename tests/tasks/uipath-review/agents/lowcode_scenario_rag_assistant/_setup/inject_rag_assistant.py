#!/usr/bin/env python3
"""HR knowledge assistant with retrieval and grounding defects."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    equality_evaluator,
    string_props,
    trajectory_evaluator,
    write_baseline_lowcode_agent,
    write_bindings,
    write_context_index,
    write_evals,
    write_tool,
)

SYSTEM = """You are an HR assistant that answers employee questions about benefits, leave and expenses.

Use the knowledge indexes to find information. Call lookup_employee when the answer depends on the employee's department or tenure.

Employees with more than 3 years of tenure get the Gold leave tier.

For expense questions, apply the current expense approval thresholds and tell the employee which manager tier must sign.

Write a clear answer in `answer` and list the document titles you used in `sources`."""

USER = "Employee {{input.employee_id}} asks: {{input.question}}"

INPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({
        "employee_id": "Employee ID: E followed by six digits, for example E004211.",
        "question": "The employee's question in plain text.",
    }),
    "required": ["employee_id", "question"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({
        "answer": "Answer to the employee's question.",
        "sources": "Comma-separated titles of the documents used.",
    }),
}


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA,
                output_schema=OUTPUT_SCHEMA, settings={"temperature": 0.2, "maxTokens": 2048})
    write_context_index(project, "PolicyIndex", "Company documents.", "hr-policies",
                        "Search query", threshold=0, result_count=20)
    write_context_index(project, "HandbookIndex", "Company documents and guides.", "hr-handbook",
                        "Search query", threshold=0, result_count=20)
    write_context_index(project, "DemoIndex", "", "A demo index", "Search query",
                        threshold=0, result_count=20)
    binding = write_tool(
        project,
        "lookup_employee",
        "Look up an employee record by employee ID and return department, tenure in years and manager. "
        "Read-only. Use it when the answer depends on the employee's department or tenure.",
        {"employee_id": "Employee ID: E followed by six digits, for example E004211."},
        required=["employee_id"],
        outputs={"department": "Department name", "tenure_years": "Tenure in whole years", "manager": "Manager name"},
    )
    write_bindings(project, [binding])
    write_evals(
        project,
        [equality_evaluator("Answer exact match"),
         trajectory_evaluator("Retrieval trajectory", "Pass when the agent searches the right index.")],
        [
            {"name": "leave-gold", "inputs": {"employee_id": "E004211", "question": "Which leave tier do I have?"},
             "expectedOutput": {"answer": "Gold"}, "expectedAgentBehavior": "Calls lookup_employee, then answers Gold."},
            {"name": "payslip", "inputs": {"employee_id": "E004212", "question": "Where is my March payslip?"},
             "expectedOutput": {"answer": "In the payroll portal."},
             "expectedAgentBehavior": "Searches PayrollIndex for the employee's payslip location."},
            {"name": "parental", "inputs": {"employee_id": "E004213", "question": "How long is parental leave?"},
             "expectedOutput": {"answer": "16 weeks."}, "expectedAgentBehavior": "Searches PolicyIndex."},
            {"name": "unknown", "inputs": {"employee_id": "E004214", "question": "What is the office wifi password?"},
             "expectedOutput": {"answer": "Not covered by HR policies."}, "expectedAgentBehavior": "Searches both indexes."},
            {"name": "travel", "inputs": {"employee_id": "E004215", "question": "Can I book business class?"},
             "expectedOutput": {"answer": "Only for flights over 8 hours."}, "expectedAgentBehavior": "Searches PolicyIndex."},
        ],
    )
    print("Injected RAG assistant scenario")


if __name__ == "__main__":
    main()
