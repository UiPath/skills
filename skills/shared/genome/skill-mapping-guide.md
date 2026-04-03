# Skill Mapping Guide

When populating the Build With section of a genome, map each workflow step to one skill from the table below. Assign one skill per step. If a step mixes concerns (e.g., UI interaction and data processing), split it into two steps, each with its own skill. Orchestration (queues, multi-step flows) is its own step, not a top-level annotation.

## Skill Mapping Table

| Automation Type | Skill | When to Recommend |
|-----------------|-------|-------------------|
| UI automation (desktop apps, browser interaction), Document Understanding, activity-based RPA workflows | `uipath-rpa-workflows` | Step involves UI interaction with desktop or web applications, PDF/document processing with Document Understanding, or activity-based workflow composition |
| Business logic, API calls, data processing, complex C# logic, Integration Service connectors from code | `uipath-coded-workflows` | Step involves programmatic logic, REST API integration, data transformation, or complex business rules best expressed in C# |
| Orchestration of multiple automations, queue management, multi-step flows, scheduling, human-in-the-loop | `uipath-maestro-flow` | Step involves coordinating other automations, managing Orchestrator queues, or defining multi-step orchestration flows |
| AI/ML agents, Python-based automation, LLM integration | `uipath-coded-agents` | Step involves AI agent behavior, Python scripting, or LLM-powered decision making |
| Web applications, user-facing forms and dashboards | `uipath-coded-apps` | Step involves building a web UI for user interaction, forms, or dashboards |

## Decision Tree for Ambiguous Cases

1. If the step primarily interacts with a desktop or web UI (clicking, typing, reading screen elements) -> `uipath-rpa-workflows`
2. If the step is pure data/logic with no UI (API call, calculation, data mapping) -> `uipath-coded-workflows`
3. If the step coordinates multiple automations or manages queues -> `uipath-maestro-flow`
4. If the step involves AI/ML or Python -> `uipath-coded-agents`
5. If the step builds a user-facing web interface -> `uipath-coded-apps`
6. If a step mixes UI + logic (e.g., read from web, process data, write to another app) -> split into two steps, one per skill
7. When in doubt between `uipath-rpa-workflows` and `uipath-coded-workflows`, prefer `uipath-rpa-workflows` if Document Understanding or UI selectors are involved, `uipath-coded-workflows` otherwise

## Common Combinations

Typical automations combine multiple skills. Each skill handles one or more workflow steps.

**Invoice processing:**
- `uipath-rpa-workflows` — Document Understanding extraction from PDF invoices
- `uipath-coded-workflows` — Validation logic against PO records, business rule checks
- `uipath-maestro-flow` — End-to-end orchestration with exception queues

**Email triage:**
- `uipath-rpa-workflows` — Email reading, attachment handling, routing actions
- `uipath-coded-workflows` — Classification logic, entity extraction

**Simple data transfer (Excel to web form):**
- `uipath-rpa-workflows` — Single skill handles both Excel reading and web form filling

**AI-powered form processing:**
- `uipath-coded-agents` — LLM-powered document analysis and decision making
- `uipath-coded-apps` — Web UI for user review and approval
