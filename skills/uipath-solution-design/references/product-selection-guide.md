# Product Selection Guide

This is the most important decision the SDD makes. Select the wrong product and the implementation plan is wrong. This guide produces a product recommendation from PDD signals, covering all 7 UiPath products.

## Three Levels of Decision

| Level | Decision | Scope |
|---|---|---|
| **1. Product** | Which UiPath product is the primary? Which are integrated components? | All PDDs |
| **2. Authoring mode** | XAML, Coded C#, or Hybrid | Only when primary is RPA |
| **3. Capabilities** | Which add-on capabilities are needed (HITL, Integration Service, API Workflow as component)? | All products |

## Level 1 — Product Selection

### Decision tree

Walk through in order. First match wins as the **primary**. All matching signals below the primary become **integrated components**.

```text
1. Does the PDD describe AI reasoning, LLM judgment, tool calling, RAG, or knowledge retrieval?
   YES → Primary: Agents
   NO  → continue

2. Does the PDD describe a web dashboard, internal tool, or Action Center form as the deliverable?
   YES → Primary: Coded Apps
   NO  → continue

3. Does the PDD describe system-to-system API integration (synchronous, no UI, no bots)?
   YES → Primary: API Workflows
   NO  → continue

4. Does the PDD describe case lifecycle with stages, SLA tracking, approval gates, or task routing?
   YES → Primary: Case Management
   NO  → continue

5. Does the PDD describe orchestrating MULTIPLE automation types (RPA + agents + apps)?
   YES → Primary: Maestro Flow
   NO  → continue

6. Is the process meant to be REUSED as a component by other automations (not standalone)?
   YES → Primary: RPA Library
   NO  → continue

7. Is the primary goal TESTING an application's behavior?
   YES → Primary: RPA Test Automation
   NO  → continue

8. Default → Primary: RPA Process
```

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
| RPA Process, Library, Test Automation | `rpa-sdd-template.md` |
| Maestro Flow | `flow-sdd-template.md` |
| Case Management | `case-sdd-template.md` |
| Agents | `agent-sdd-template.md` |
| Coded Apps | `coded-app-sdd-template.md` |
| API Workflows | `api-workflow-sdd-template.md` |

## Gap Handling for Agent / Coded App

When the primary product is Agents or Coded Apps and the PDD is missing required information (listed in the signals above):

1. Use `AskUserQuestion` with a single prompt: "The PDD describes [product]-specific capabilities, but requirements are missing for [list gaps]. Should I proceed with [product] and ask follow-up questions to fill the gaps, or use a different product?"
2. Options: "Proceed with [product]" / "Use a different product"
3. If user chooses to proceed → use `AskUserQuestion` again with a batch of 4-6 product-specific gap-filling questions
4. If user chooses a different product → use `AskUserQuestion` to pick the fallback (RPA Process, Flow, Case Management, Stop)
5. Re-run product selection with the fallback as primary

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
```

Wait for user confirmation before proceeding to Phase 2. If the user disagrees with the primary, re-run the decision tree with their preference.
