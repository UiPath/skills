#!/usr/bin/env python3
"""Research orchestrator with delegation, tool-selection and settings defects."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    equality_evaluator,
    string_props,
    trajectory_evaluator,
    write_baseline_lowcode_agent,
    write_bindings,
    write_evals,
    write_tool,
)

SYSTEM = """You are a market research orchestrator that produces a one-page competitor report for the product team.

You have research_agent, summary_agent, web_lookup and web_search.

Collect facts about the competitor, write the report, translate the final report into French, and save the final report to the ReportsArchive storage bucket.

If you cannot find facts after three searches, write the report with what you have and say which sections are incomplete.

Return the report in `report`."""

USER = "Competitor: {{input.competitor}}"

INPUT_SCHEMA = {
    "type": "object",
    "properties": string_props({"competitor": "Name of the competitor company to research."}),
    "required": ["competitor"],
}

OUTPUT_SCHEMA = {"type": "object", "properties": string_props({"report": "One-page competitor report in Markdown."})}

TOOLS = [
    ("research_agent", "Researches a topic.", "agent"),
    ("summary_agent", "Summarizes research on a topic.", "agent"),
    ("web_lookup", "Look up information about a topic on the web.", "process"),
    ("web_search", "Search the web for information about a topic.", "process"),
]


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA, output_schema=OUTPUT_SCHEMA,
                settings={"model": "gpt-4o-mini-2024-07-18", "maxIterations": 2, "temperature": 0.4,
                          "maxTokens": 8192})
    bindings = [
        write_tool(project, name, desc, {"topic": "Topic or question to research."}, required=["topic"],
                   outputs={"result": "Result text."}, tool_type=kind)
        for name, desc, kind in TOOLS
    ]
    write_bindings(project, bindings)
    write_evals(
        project,
        [equality_evaluator("Report exact match"),
         trajectory_evaluator("Delegation trajectory", "Pass when research is delegated before the report is written.")],
        [
            {"name": f"c{i}", "inputs": {"competitor": c}, "expectedOutput": {"report": f"# {c}"},
             "expectedAgentBehavior": "Delegates research, then writes the report."}
            for i, c in enumerate(["Contoso", "Fabrikam", "Northwind", "Tailspin", "Litware"])
        ],
    )
    print("Injected orchestrator scenario")


if __name__ == "__main__":
    main()
