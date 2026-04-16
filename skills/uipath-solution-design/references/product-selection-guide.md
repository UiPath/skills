# Product Selection Guide

This is the most important decision the SDD makes. Select the wrong product and the implementation plan is wrong. This guide produces a product recommendation from PDD signals, covering all 7 UiPath products.

## Three Levels of Decision

| Level | Decision | Scope |
|---|---|---|
| **1. Product** | Which UiPath product is the primary? Which are integrated components? | All PDDs |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Only when primary is RPA |
| **3. Capabilities** | Which add-on capabilities are needed (HITL, Integration Service, API Workflow as component)? | All products |

## Level 1 — Product Selection

### Decision table

Walk through in priority order. **First match wins** as the primary. All matching signals below the primary become integrated components.

| Priority | Signal in PDD | Primary Product |
|----------|---------------|-----------------|
| 1 | AI reasoning, LLM judgment, tool calling, RAG, knowledge retrieval | Agents |
| 2 | Web dashboard, internal tool, Action Center form as the deliverable | Coded Apps |
| 3 | System-to-system API integration (synchronous, no UI, no bots) | API Workflows |
| 4 | Case lifecycle with stages, SLA tracking, approval gates, task routing | Case Management |
| 5 | Orchestrating MULTIPLE automation types (RPA + agents + apps) | Maestro Flow |
| 6 | Reusable component consumed by other automations (not standalone) | RPA Library |
| 7 | Primary goal is TESTING an application's behavior | RPA Test Automation |
| 8 | None of the above (UI automation, data processing, queue-based) | RPA Process (default) |

> **Ambiguous dual-product PDDs:** If the PDD appears to match two products roughly equally, the priority ordering above is intentional. Present both products in the recommendation with explicit reasoning for each, mark the higher-priority match as the default, and let the user confirm via `AskUserQuestion`.

### Signals per product

#### Agents (Python + agent.json)

**Signals the PDD is describing an Agent:**
- "AI reasoning", "LLM", "GPT", "Claude"
- "Tool calling", "function calling"
- "RAG", "knowledge base", "semantic search", "vector store"
- "Multi-step reasoning", "plan and execute"
- "Natural language interface"
- Agent decides what to do based on user input, not a fixed script

**Required PDD information (may trigger gap-filling Q&A):**
- Framework preference (LangGraph, LlamaIndex, OpenAI Agents, Simple Function)
- Tools the agent will use (external APIs, RPA processes, API workflows)
- Memory / RAG sources if applicable
- Evaluation criteria (trajectory, success metrics)

**Missing-info trigger:** If the PDD has agent signals but lacks framework/tools/evaluation details → use `AskUserQuestion` (see Gap Handling below).

#### Coded Apps (Web)

**Signals the PDD is describing a Coded App:**
- "Dashboard", "web interface", "portal", "internal tool"
- "User submits a form"
- "Review screen" or "approval UI"
- "Action Center custom form"
- Deliverable is a web application users interact with

**Required PDD information (may trigger gap-filling Q&A):**
- Framework (React, Angular, Vue)
- App type (Web standalone vs. Action for automation-triggered)
- Pages / routes / user flows
- State management complexity
- Who calls the app (direct user, HITL form, Action Center task)

**Missing-info trigger:** If the PDD has web-UI signals but lacks framework/pages/flows → use `AskUserQuestion`.

#### API Workflows

**Signals the PDD is describing an API Workflow:**
- System-to-system integration with **no UI** and **no human interaction**
- Synchronous request-response pattern (milliseconds to seconds)
- Pulls, composes, or transforms data across SaaS systems (Workday, Zendesk, Salesforce, ServiceNow, etc.)
- Consumed by agents as a tool, called from Flows, or over HTTP by external systems
- High-throughput requirement (many small, fast operations)
- **No need for attended/unattended robots**

**Key distinction from RPA Library:** Libraries are compile-time reusable components for other automations. API Workflows are runtime-callable services over HTTP, serverless, no bots needed.

**Required PDD information:**
- Input schema (JSON) — parameters the caller provides
- Output schema (JSON) — data returned
- Connectors or HTTP endpoints to call
- Performance expectations (latency, throughput)

#### Case Management

**Signals the PDD is describing Case Management:**
- "Stages" or "phases" in the process
- "Approval gate" that blocks progression
- "SLA" or "service level agreement"
- "Escalation" on time or condition
- "Case" as a first-class concept (invoice case, ticket case, claim case)
- BPMN-style multi-lane flow
- Tasks that can run in parallel within a lane

**Required PDD information:**
- Stage definitions with entry/exit conditions
- Task definitions per stage
- SLA rules (time-based or condition-based)
- Escalation rules

#### Maestro Flow

**Signals the PDD is describing a Flow:**
- Orchestrating multiple automation types (RPA + agents + apps)
- Conditional routing between automations
- Data transformations between steps (filter, map, group-by)
- Scheduled triggers
- Subflows for reusable grouped logic
- "Flow" or "pipeline" terminology

**Required PDD information:**
- Node sequence with conditional branches
- Variables passed between nodes
- External systems involved
- Trigger type (manual, scheduled, event)

#### RPA Library

**Signals the PDD is describing a Library:**
- "Reusable component" for other projects
- "Standard activity" used across multiple processes
- Not a complete end-to-end process
- Public workflows meant to appear as activities in other projects
- Distributed via NuGet

**Required PDD information:**
- Public workflow signatures (inputs, outputs)
- Dependencies
- Intended consumers

#### RPA Test Automation

**Signals the PDD is describing Test Automation:**
- Primary goal is validating application behavior
- Test cases with assertions
- Test Manager integration
- Data-driven testing with variations
- Regression test suite

**Required PDD information:**
- Application(s) under test
- Test case list
- Expected outcomes per test

#### RPA Process (default)

**Signals:**
- UI-heavy automation (web forms, desktop apps, Excel, email)
- Data processing between applications
- Attended or unattended execution
- Queue-based transactional processing
- Standard end-to-end business process

**This is the default when no other product matches.**

## Level 2 — Authoring Mode (RPA only)

Applies only when Level 1 selected RPA Process, Library, or Test Automation. Skip otherwise.

| Process Characteristic | Recommended Mode |
|---|---|
| Primarily UI automation (clicking, typing, reading screens) | **XAML** |
| Simple linear or transactional flow (REFramework) | **XAML** |
| Heavy use of pre-built activity packages (SAP, Salesforce, Excel) | **XAML** |
| Significant data transformation (parsing, regex, hashing, aggregation) | **Coded C#** |
| REST API integrations (HTTP calls, pagination, auth tokens) | **Coded C#** |
| Complex branching logic (5+ decision paths) | **Coded C#** |
| Custom data models needed (typed DTOs, enums) | **Coded C#** |
| UI automation AND complex data logic | **Hybrid** |
| Multiple applications with different interaction patterns | **Hybrid** |

The skill that builds the workflows owns the final, detailed decision — this is a directional recommendation.

## Level 2.5 — Project Decomposition (RPA only)

Applies only when Level 1 selected RPA Process. Skip for Library, Test Automation, and all non-RPA products.

Most real-world RPA processes require multiple projects connected by Orchestrator queues — not a single monolithic project. This decision determines whether the SDD describes one project or a **Master Project** (multiple queue-connected sub-projects).

### Decision table

Walk through the signals. **If 2 or more signals match → Master Project.** If 0-1 match → Single Project.

| # | Signal in PDD | What it means |
|---|---|---|
| 1 | Process has distinct stages with different characteristics (e.g., email ingestion vs. data extraction vs. output generation) | Each stage becomes a separate project that can be developed, tested, and scaled independently |
| 2 | Transactional processing where items can fail independently and must be retried per item | Queue-based retry requires Performer projects consuming from Orchestrator queues using REFramework |
| 3 | Document Understanding or AI extraction with human validation (Action Centre) | DU + validation is a distinct processing stage that benefits from its own project and queue |
| 4 | Different processing speeds per stage (e.g., fast email download vs. slow DU extraction) | Independent projects allow different robot counts per stage for throughput balancing |
| 5 | Reporting requirements (Excel report, email summary, dashboard data) | Dedicated Reporting project reads from a reporting queue populated by all other stages |
| 6 | Multiple output channels from a single input (e.g., XML to MQ + files to FTP + report to email) | Separate Performer per output channel avoids coupling unrelated integrations |

### Common decomposition patterns

#### Dispatcher / Performer (most common)

Use when the process collects items from a source (email, folder, spreadsheet, API) and then processes each item transactionally.

```text
[Dispatcher] → Queue → [Performer] → Reporting Queue → [Reporting]
```

- **Dispatcher**: collects items, creates queue items with all required data. Runs as a simple sequence (no REFramework).
- **Performer**: processes one transaction item at a time. Uses **REFramework** for retry, logging, and state management.
- **Reporting** (optional): reads from a reporting queue, generates reports. Runs on a schedule or after Performer completes.

#### Dispatcher / DU Performer / Output Performer

Use when the process has Document Understanding with human validation as a middle stage.

```text
[Dispatcher] → DU Queue → [DU Performer] → Output Queue → [Output Performer]
                                ↓                              ↓
                          Action Centre                  Reporting Queue
                                                               ↓
                                                         [Reporting]
```

- **Dispatcher**: downloads emails/files, creates queue items.
- **DU Performer**: runs DU extraction, sends low-confidence items to Action Centre, pushes validated results to the output queue. Uses REFramework.
- **Output Performer**: generates output (XML, CSV, API calls), uploads to target systems. Uses REFramework.
- **Reporting**: aggregates outcomes from all stages.

### Output of this decision

Produce:

1. **Pattern**: Single Project or Master Project (name the pattern: Dispatcher/Performer, Dispatcher/DU/Output, etc.)
2. **Sub-projects** (if Master Project): table with project name, role, input queue, output queue, framework choice
3. **Queue schema**: queue names, which project produces, which consumes, and what data fields go in `SpecificContent`

| # | Project Name | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|
| 1 | `<NAME>_Dispatcher` | Collect items from source, dispatch to processing queue | Sequence | — | `<QUEUE_1>` |
| 2 | `<NAME>_Performer` | Process each transaction item | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 3 | `<NAME>_Reporting` | Generate reports from processing outcomes | Sequence | `<REPORTING_QUEUE>` | — |

### REFramework guidance

REFramework is the standard UiPath framework for transactional processes. It provides: Init → Get Transaction → Process Transaction → End Process states, with built-in retry, exception handling, and logging.

| Project Role | Framework | Why |
|---|---|---|
| Performer (queue-based) | **REFramework** | Built-in transaction retry, state management, exception routing |
| Dispatcher (collects and pushes items) | **Sequence** | Simple linear flow — no transaction retry needed |
| Reporting (reads queue, generates output) | **Sequence** or **REFramework** | Sequence if simple aggregation; REFramework if items can fail independently |
| Single Project (no queues) | **Sequence** or **REFramework** | REFramework if processing multiple items with per-item retry; Sequence if simple linear |

When REFramework is selected for a project, the project structure in §11 of the RPA template must use the REFramework folder layout (Init, GetTransactionData, Process states) instead of a custom framework.

## Level 3 — Capability Add-ons

These are capabilities added to the primary product, not standalone products. When detected, flag them in the appropriate template section and create implementation tasks that will route to the correct skill.

### HITL (Human-in-the-Loop)

**Scope:** Adds approval gates, exception escalation, and write-back validation to **Flow, Maestro, or Coded Agents** (not RPA, Case Management, or Coded Apps).

**Signals the PDD needs HITL:**
- "Approval before..."
- "Human reviews..."
- "If confidence is low, escalate..."
- "Validate before writing back..."
- "Fills in missing data..."

**How to flag:** In the Flow / Maestro / Agent template, add a "HITL Touchpoints" line in the relevant section (node table, agent description). In the implementation plan, add a task "Add HITL node per §X" — this will route to the `uipath-human-in-the-loop` skill at execution.

### Integration Service

**Scope:** Adds connector activities (Salesforce, Jira, ServiceNow, Slack, etc.) to RPA, Flow, Case Management, or Agents.

**Signals the PDD needs Integration Service:**
- Third-party SaaS system mentioned (not a custom web app): Salesforce, Jira, ServiceNow, Slack, HubSpot, Workday, Zendesk, etc.
- "Create a ticket in...", "Post a message to...", "Read records from..."

**How to flag:** In the Application Inventory section, list the connector explicitly. In the implementation plan, add a task "Configure X connector" — this will route to the `uipath-platform` skill at execution.

### API Workflow (as integrated component)

**Scope:** When API Workflow is NOT the primary but is called by the primary (Flow, Agent, Case Management, another API Workflow).

**Signals:**
- The primary product invokes a callable system-to-system integration
- Input/output is structured JSON, not UI

**How to flag:** In the primary product's template, list API Workflow invocations in the relevant section (Flow nodes, Agent tools, Case tasks). In the implementation plan, add a task "Create API Workflow X" — future API Workflow skill will handle; for now, reference the API Workflow template.

## Template Mapping

Based on the Level 1 primary, select the template:

| Primary Product | Template |
|---|---|
| RPA Process, Library, Test Automation | `../assets/templates/rpa-sdd-template.md` |
| Maestro Flow | `../assets/templates/flow-sdd-template.md` |
| Case Management | `../assets/templates/case-sdd-template.md` |
| Agents | `../assets/templates/agent-sdd-template.md` |
| Coded Apps | `../assets/templates/coded-app-sdd-template.md` |
| API Workflows | `../assets/templates/api-workflow-sdd-template.md` |

## Gap Handling for Agent / Coded App

When the primary product is Agents or Coded Apps and the PDD is missing required information (listed in the signals above):

1. Use `AskUserQuestion` with the numbered-choice format:

> The PDD describes <PRODUCT>-specific capabilities, but requirements are missing for: <LIST_GAPS>.
>
> 1. **Proceed with <PRODUCT>** *(recommended)* — I will ask follow-up questions to fill the gaps
> 2. **Use a different product** — I will ask which product to use instead

2. If user chooses **option 1** → use `AskUserQuestion` again with a batch of 4-6 product-specific gap-filling questions (numbered, with defaults where possible)

3. If user chooses **option 2** → use `AskUserQuestion` for the fallback:

> Which product should I use instead?
>
> 1. **RPA Process** — standard UI/data automation
> 2. **Maestro Flow** — orchestrate multiple automations
> 3. **Case Management** — staged lifecycle with SLA
> 4. **Stop** — do not generate an SDD

4. Re-run product selection with the fallback as primary

Do not auto-fallback. The user must choose explicitly.

## Presenting the Recommendation

In the Phase 1 summary, include a dedicated section:

```markdown
## Recommended Product
**Primary:** <PRODUCT>
**Integrated components:** <PRODUCT_1>, <PRODUCT_2>, ... (or "None")
**Reasoning:**
- <SIGNAL_FROM_PDD> → <PRODUCT_MAPPING>
- ...
**Alternatives considered:**
- <REJECTED_PRODUCT> — rejected because <REASON>
- ...

## Project Architecture (RPA only)
**Pattern:** <SINGLE_PROJECT / MASTER_PROJECT_PATTERN_NAME>
**Sub-projects:** <PROJECT_TABLE_OR_N/A>
**Queue schema:** <QUEUE_TABLE_OR_N/A>
**Decomposition signals matched:** <LIST_MATCHED_SIGNALS_FROM_LEVEL_2.5>
```

Wait for user confirmation before proceeding to Phase 2. If the user disagrees with the primary, re-run the decision tree with their preference.
