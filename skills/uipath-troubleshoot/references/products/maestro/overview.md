# Maestro

Agentic orchestration platform built on top of Orchestrator. Maestro supports three process authoring styles, each with its own CLI subcommand:

- **BPMN** (`uip maestro bpmn`) — formal BPMN 2.0 process design with swimlanes, gateways, boundary events, service tasks, and multi-instance markers. Authored in Studio Web's BPMN editor (`.bpmn` files). Best for orchestrating long-running, multi-actor business processes with rich exception flow.
- **Flow** (`uip maestro flow`) — lightweight node-and-edge process design (`.flow` files). Lower ceremony than BPMN; emphasizes connectors, scripts, sub-flows, and human-in-the-loop nodes. Best for connector-heavy automations and quick agent-orchestrated flows.
- **Case Management** (`uip maestro case`) — case-centric workflows with stages, tasks, SLAs, escalations, triggers, and edges (Case definition JSON). Best for human-driven, evolving work where progress is tracked per case rather than per linear process run.

Processes are designed in Studio Web, deployed as solutions to Orchestrator, and managed through the Maestro Instance Management UI.

## Dependencies

- **Orchestrator** — executes child jobs, manages folders/permissions/assets, hosts releases and triggers
- **Studio Web** — BPMN process designer, solution packaging, and publishing
- **Integration Service** — provides connectors (Outlook, Salesforce, etc.) and triggers for event-driven processes
- **AI Trust Layer** — governs agent execution policies, trace TTL, and LLM access
- **Semantic Proxy / LLM Gateway** — routes LLM calls for agent tasks; outage blocks agent execution
- **Data Fabric** — data storage and retrieval for process context, file handling, and context indexes

## Organization Model

```
Organization (cloud.uipath.com)
  └── Tenant
        └── Folder                    ← Resources are folder-scoped
              ├── Solutions           ← Published BPMN packages
              ├── Processes/Releases  ← Deployed entry points
              ├── Instances           ← Running BPMN process instances
              ├── Incidents           ← Faults within instances (not always visible in Orchestrator job state)
              ├── Connections         ← Integration Service connections
              ├── Triggers            ← IS and queue-based triggers
              └── Jobs                ← Child jobs spawned by service tasks
```

## Key Concepts

- **BPMN Process** — the orchestration definition with start events, tasks, gateways, boundary events, and end events
- **Solution** — a deployable package containing one or more BPMN processes, exported from Studio Web
- **Instance** — a running execution of a BPMN process
- **Incident** — a fault within an instance; Maestro captures these even when Orchestrator job state does not reflect them
- **Service Task** — a BPMN task that invokes a child Orchestrator job (robot workflow or agent)
- **Human Task** — a BPMN task that creates an action for a human user
- **Agent Task** — a service task that invokes an AI agent with context and tools
- **Multi-Instance Marker** — a parallel execution marker on a task node; iterates over a collection variable (batch limit: 50)
- **Boundary Event** — error or timer event attached to a task; catches faults or timeouts and redirects flow
- **Exclusive Gateway** — conditional branching based on variable expressions (case-sensitive)
- **bindings_v2.json** — maps folder references and variable bindings for deployed mode
- **debug_overwrites.json** — redirects folder bindings during debug mode (not used in deployed mode)

## CLI

Maestro CLI commands are namespaced by process type. Pick the subcommand that matches the process:

| Process type | Subcommand | Source artifacts | One-liner |
|--------------|------------|------------------|-----------|
| BPMN | `uip maestro bpmn ...` | `.bpmn` files (Studio Web BPMN editor) | Formal BPMN 2.0 with swimlanes, gateways, boundary events, service/human/agent tasks |
| Flow | `uip maestro flow ...` | `.flow` files | Lightweight node-and-edge orchestration; connector-heavy, lower ceremony than BPMN |
| Case | `uip maestro case ...` | Case definition JSON | Case-centric work with stages, tasks, SLAs, escalations, and triggers |

**Identify the process type first** — check the source artifact, the `processType` field on incidents/instances, or ask the user. Running `uip maestro bpmn instance get <id>` against a Flow instance returns no data. Substitute `<type>` below with `bpmn`, `flow`, or `case`.

```
uip maestro <type> process list|get|run                          — list/get/run processes
uip maestro <type> job traces|status <job-key>                   — stream traces or get status for a job
uip maestro <type> instance list [-f <folder-key>]               — list instances. Filters: --process-key, --error-code, --limit, --offset
uip maestro <type> instance get <id> [-f <folder-key>]           — get instance details
uip maestro <type> instance incidents <id> [-f <fk>]             — full incidents with errorDetails and stack traces
uip maestro <type> instance element-executions <id> [-f <fk>]    — element execution history
uip maestro <type> instance variables <id> [-f <fk>]             — instance variables. Filter: --parent-element-id
uip maestro <type> instance asset <id> [-f <fk>]                 — process definition asset (BPMN XML, Flow JSON, Case JSON)
uip maestro <type> instance cursors <id> [-f <fk>]               — current execution cursor positions
uip maestro <type> instance retry <id> [-f <fk>]                 — retry a faulted instance
uip maestro <type> instance pause|resume|cancel <id> [-f <fk>]   — lifecycle control
uip maestro <type> processes incidents <key> [--folder-key <fk>] — incidents across all instances of a process
uip maestro <type> incident summary                              — tenant-level incident SUMMARIES ONLY (no errorDetails)
uip maestro <type> incident get <incident-id>                    — get a single incident by ID
```

Key commands for troubleshooting (substitute `<type>` with `bpmn`, `flow`, or `case`):
- `uip maestro <type> instance incidents <instance-id> -f <folder-key>` — **full incident details** including `errorDetails` with stack traces. Use this, not `incident summary`.
- `uip maestro <type> instance element-executions <instance-id> -f <folder-key>` — what each element did
- `uip maestro <type> processes incidents <process-key> --folder-key <fk>` — incidents across all instances of a process

**WARNING:** `uip maestro <type> incident summary` returns only aggregated summaries (counts, error codes) without `errorDetails`. It does NOT contain stack traces or full error messages. Always use instance-level or process-level incident commands for troubleshooting.

**WARNING:** There is no top-level `uip maestro instance` / `uip maestro process` / `uip maestro incident` command — every operation requires the `bpmn`, `flow`, or `case` segment. Running the old un-namespaced form fails.

## Features

- **BPMN Process Design** — visual process editor in Studio Web with swimlanes, gateways, and markers
- **Solution Deployment** — package and deploy BPMN processes to Orchestrator folders
- **Instance Management** — monitor and manage running process instances and incidents
- **Human-in-the-Loop** — assign tasks to human users with approval/input forms
- **Agent Orchestration** — invoke AI agents as service tasks with context indexes and tools
- **Multi-Instance Parallel Execution** — run tasks in parallel over a collection (batch limit: 50)
- **Integration Service Triggers** — start processes from external events (email, webhook, etc.)
- **Boundary Events** — error and timer handlers on tasks for exception flow
- **Variable Expressions** — JavaScript (Jint) or C# expressions for conditions and transformations
