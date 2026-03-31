# Flow Orchestration Guide

How to use Flow as a higher-level composer that orchestrates RPA processes, agents, apps, other flows, and API workflows together.

> **Flow is not just a scripting engine.** Its primary value is connecting different UiPath automation types into end-to-end business processes. This guide covers how to reference, create, and wire external resources as flow nodes.

---

## Resource Node Types

Flow can invoke six types of external resources as nodes. Each has a unique node type pattern, service type, and category.

| Resource Type | Node Type Pattern | Service Type | Category | Description |
|---|---|---|---|---|
| **RPA Process** | `uipath.core.rpa-workflow.{key}` | `Orchestrator.StartJob` | `rpa-workflow` | Run a published RPA workflow (XAML or coded) |
| **Agent** | `uipath.core.agent.{key}` | `Orchestrator.StartAgentJob` | `agent` | Run a published AI agent |
| **Agentic Process** | `uipath.core.agentic-process.{key}` | `Orchestrator.StartAgenticProcess` | `agentic-process` | Run a published orchestration process |
| **Flow** | `uipath.core.flow.{key}` | `Orchestrator.StartAgenticProcess` | `flow` | Run another published flow as a subprocess |
| **API Workflow** | `uipath.core.api-workflow.{key}` | `Orchestrator.ExecuteApiWorkflowAsync` | `api-workflow` | Call a published API function |
| **Web App (Human Task)** | `uipath.core.human-task.{key}` | `Actions.HITL` | `human-task` | Pause for human input via a UiPath App |

### How to Discover Resource Nodes

After `uip login`, resource nodes from your tenant appear in the registry:

```bash
uip flow registry pull --force
uip flow registry search process --output json    # Find RPA processes
uip flow registry search agent --output json      # Find agents
uip flow registry search flow --output json       # Find sub-flows
```

To get the full node definition with input/output schemas:

```bash
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

The `{key}` is the resource's unique identifier from Orchestrator (typically a GUID or slug).

---

## Built-in Agent Nodes

In addition to published agent resources, Flow has two built-in agent node types:

| Node Type | Description | Use Case |
|---|---|---|
| `uipath.agent.autonomous` | Autonomous agent that reasons and acts independently | Classification, triage, summarization, multi-step reasoning |
| `uipath.agent.conversational` | Conversational agent for interactive dialogues | Chat-based workflows, user Q&A |

These are OOTB nodes (available without publishing anything). Discover them via:

```bash
uip flow registry search "uipath.agent" --output json
```

### Agent Node vs Script Node Decision

| Situation | Use |
|---|---|
| Deterministic logic, known rules | Script node |
| Ambiguous input, needs reasoning | Agent node |
| Data transformation, filtering | Script or Transform node |
| Natural language generation | Agent node |
| Classification with fuzzy categories | Agent node |

---

## Referencing Published Resources

When a resource is already published to Orchestrator, add it as a node in the flow.

### Step 1 — Find the resource in the registry

```bash
uip flow registry pull --force
uip flow registry search "<resource-name>" --output json
```

### Step 2 — Get the full node definition

```bash
uip flow registry get "<node-type>" --output json
```

This returns the definition with `inputDefinition` (required inputs, types) and `outputDefinition` (what the node produces).

### Step 3 — Add the node to the flow

```bash
uip flow node add flow_files/<Project>.flow "<node-type>" --output json \
  --input '{"documentPath": "/invoices/batch1"}' \
  --label "Process Invoices"
```

### Step 4 — Wire edges and validate

```bash
uip flow edge add flow_files/<Project>.flow <upstreamId> <resourceNodeId> --output json
uip flow validate flow_files/<Project>.flow --output json
```

### Resource Node JSON Structure

When editing JSON directly, a resource node looks like this:

```json
{
  "id": "processInvoices",
  "type": "uipath.core.rpa-workflow.invoice-process-abc123",
  "typeVersion": "1.0.0",
  "ui": { "position": { "x": 400, "y": 200 } },
  "display": { "label": "Process Invoices" },
  "inputs": {
    "documentPath": "=js:$vars.fileLocation",
    "batchSize": 50
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartJob",
    "version": "v2",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Process",
      "resourceKey": "invoice-process-abc123",
      "orchestratorType": "process",
      "values": {
        "name": "Invoice Processor",
        "folderPath": "Finance/Automation"
      }
    }
  }
}
```

### Resource Node Outputs

All resource nodes produce two outputs accessible via `$vars`:

- `$vars.{nodeId}.output` — The resource's return value (structure depends on the resource)
- `$vars.{nodeId}.error` — Error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

---

## Creating New Resources ("Create New" Workflow)

When the flow plan requires a resource that does not exist yet (e.g., an RPA process for a desktop app, or an agent for classification), follow this workflow:

### Step 1 — Identify the gap during planning

While building the flow plan (Step 5 in SKILL.md), identify nodes that need resources not yet published. Mark them as **placeholders** in the plan:

```markdown
| # | Name | Category | Node Type | Description |
|---|---|---|---|---|
| 3 | Extract Invoice Data | rpa-workflow | **[CREATE NEW]** | Desktop automation to extract fields from PDF invoices |
| 5 | Classify Document | agent | **[CREATE NEW]** | AI agent to classify document type |
```

### Step 2 — Add mock placeholders in the flow

Use `core.logic.mock` nodes as temporary stand-ins:

```bash
uip flow node add flow_files/<Project>.flow core.logic.mock --output json \
  --label "Extract Invoice Data [TODO: RPA]" \
  --position 400,200
```

### Step 3 — Tell the user which skill to use

In your completion output, list each placeholder and the skill needed:

| Placeholder | Resource Type | Skill to Use |
|---|---|---|
| Extract Invoice Data | RPA Process | `uipath-rpa-workflows` (XAML, needs Studio) or `uipath-coded-workflows` (C#, CLI-only) |
| Classify Document | Agent | `uipath-coded-agents` (Python) |
| Review Form | Web App | `uipath-coded-apps` (.NET/React) |

### Step 4 — Create the resource using the appropriate skill

Switch to the relevant skill to create and publish the resource:

- **RPA Process** — Use `uipath-coded-workflows` to create a C# coded workflow, or `uipath-rpa-workflows` for XAML (requires Studio Desktop)
- **Agent** — Use `uipath-coded-agents` to create a Python agent
- **Web App** — Use `uipath-coded-apps` to create a .NET/React app
- **Sub-Flow** — Create another flow project using the same `uipath-flow` skill

After creating and publishing the resource, it will appear in the Orchestrator resource catalog.

### Step 5 — Replace mock with real resource node

Once published, discover the new resource and replace the mock:

```bash
# Refresh registry to pick up newly published resource
uip flow registry pull --force

# Find the new resource
uip flow registry search "Invoice" --output json

# Get its definition
uip flow registry get "uipath.core.rpa-workflow.{key}" --output json
```

Then edit the `.flow` JSON:
1. Remove the mock node from `nodes`
2. Add the real resource node (with correct `type`, `inputs`, `model`)
3. Update all edges that referenced the mock node's ID
4. Add node variables to `variables.nodes` — see [variables-and-expressions.md — Node Variables](variables-and-expressions.md) for the schema
5. Validate: `uip flow validate`

> **NEVER invoke other skills automatically.** Always tell the user what's needed and let them decide when to switch skills. The flow skill's job is to identify gaps and provide clear handoff instructions.

---

## Queue Integration

Flow can create queue items in Orchestrator queues, enabling work distribution to robots.

| Node Type | Description |
|---|---|
| `core.action.queue.create` | Create a queue item and continue immediately |
| `core.action.queue.create-and-wait` | Create a queue item and wait for it to be processed |

### Queue Node Inputs

```json
{
  "inputs": {
    "queue": "InvoiceProcessingQueue",
    "itemData": "=js:JSON.stringify({ orderId: $vars.order.id, amount: $vars.order.total })",
    "priority": "High",
    "reference": "=js:$vars.order.id",
    "deferDate": "2026-04-01T10:00:00Z",
    "dueDate": "2026-04-07T17:00:00Z"
  }
}
```

| Input | Required | Description |
|---|---|---|
| `queue` | Yes | Orchestrator queue name |
| `itemData` | No | JSON payload for the queue item |
| `priority` | No | `Low`, `Normal` (default), `High` |
| `reference` | No | Tracking reference string |
| `deferDate` | No | ISO 8601 — earliest time to process |
| `dueDate` | No | ISO 8601 — deadline for processing |

### When to Use Queue Nodes

| Scenario | Use |
|---|---|
| Fire-and-forget work distribution | `core.action.queue.create` |
| Need the processed result before continuing | `core.action.queue.create-and-wait` |
| Direct process invocation with known inputs | Resource node (`uipath.core.rpa-workflow.*`) |

---

## Human Task / Web App Integration

Human task nodes (`uipath.core.human-task.{key}`) pause the flow and present a UiPath App to a human user for input. The flow resumes when the user submits the form.

### Use Cases

- Approval workflows (manager approval before processing)
- Data validation (human reviews extracted data before submission)
- Exception handling (human resolves items the automation cannot handle)

### Wiring Pattern

```
[Automation nodes] → [Human Task] → [Continue with human's input]
```

The human task node's output (`$vars.{nodeId}.output`) contains the form data submitted by the user.

---

## Orchestration Patterns

### Linear Pipeline with Mixed Resources

```
Manual Trigger → Script (prepare) → RPA Process (extract) → Agent (classify) → Script (transform) → End
```

### Fan-Out to Queue

```
Manual Trigger → Script (split batch) → Loop → Queue Create (per item) → End Loop → End
```

### Human-in-the-Loop

```
Manual Trigger → RPA Process (extract) → Human Task (review) → Decision (approved?) →
  true: Script (submit) → End
  false: End
```

### Sub-Flow Composition

```
Manual Trigger → Flow (validate data) → Decision (valid?) →
  true: Flow (process data) → End
  false: Script (log error) → Terminate
```
