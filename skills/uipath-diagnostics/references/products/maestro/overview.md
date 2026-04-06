# Maestro

Agentic orchestration platform built on top of Orchestrator. Enables BPMN-based process design with human-in-the-loop tasks, AI agent tasks, and service tasks orchestrated across multiple swimlanes.

Maestro processes are designed in Studio Web using a BPMN editor, deployed as solutions to Orchestrator, and managed through the Maestro Instance Management UI.

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
