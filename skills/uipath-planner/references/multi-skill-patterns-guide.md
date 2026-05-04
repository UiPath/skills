# Multi-skill Patterns Guide

Common request shapes that span more than one specialist skill. Use this guide when deciding whether a request is single-skill (load one specialist directly) or multi-skill (emit a plan).

> **Legacy projects:** if the project is legacy (`.NET Framework 4.6.1`, XAML-only, `targetFramework: "Legacy"` or missing in `project.json`), substitute `uipath-rpa-legacy` for `uipath-rpa` in every pattern below.

## When to emit a multi-skill plan

Emit a multi-skill plan when the request clearly spans more than one specialist. Single-skill tasks (e.g., "create a workflow that sends an email") go directly to the specialist — no plan needed.

A request is **multi-skill** when at least one of the following is true:

- Build + deploy crosses skill boundaries (RPA build → platform deploy)
- A target product cannot exist without other products built first (Flow needs RPA processes that don't exist yet)
- Build + verify against a live app crosses skill boundaries (RPA build → interact verify → RPA fix)
- The user wants the result of one skill to be consumed by another (Agent uses RPA processes as tools)

A request is **single-skill** when:

- The deliverable is owned end-to-end by one skill (e.g., "create a UiPath RPA workflow that fills a form" — one project, one app, one workflow)
- The user is modifying an existing automation in a single project
- The request is read-only / diagnostic / exploration only

> **Important:** Single-app UI automation (one project, one live app, one workflow) is **not** a multi-skill pattern — it's a single-skill `uipath-rpa` task. `uipath-rpa` owns UI automation authoring end-to-end. Do NOT plan a separate "uipath-interact discovery" step for it.

## Pattern 1 — RPA build + deploy to Orchestrator

**When it applies:** user wants to build an RPA workflow and deploy it to Orchestrator (most common production flow).

```
1. uipath-rpa      → create / edit, validate, build the workflow
2. uipath-rpa      → testing (mandatory)
3. uipath-platform → pack, publish, deploy to Orchestrator
```

`uipath-rpa` does not deploy. Deploy to Orchestrator always goes through `uipath-platform`.

## Pattern 2 — Flow with missing resources

**When it applies:** the request is for a Maestro Flow that orchestrates RPA processes / agents / apps that **do not exist yet**.

```
1. uipath-maestro-flow → design the flow, mock placeholders for missing resources
2. uipath-rpa          → create the missing RPA process(es)
3. uipath-rpa          → testing for the new RPA processes (mandatory)
4. uipath-platform     → publish the RPA process(es) to Orchestrator
5. uipath-maestro-flow → replace mocks with published resources, validate, publish
6. uipath-maestro-flow → testing for the flow (mandatory)
```

Replace steps 2–4 with `uipath-agents` if the missing resource is an agent (with the testing task as part of the agent flow).

## Pattern 3 — Flow deploy to Orchestrator

**When it applies:** the flow exists; user wants it deployed to Orchestrator (not Studio Web).

```
1. uipath-maestro-flow → validate, `uip maestro flow pack`
2. uipath-maestro-flow → testing (mandatory)
3. uipath-platform     → publish and deploy to Orchestrator
```

`uipath-maestro-flow` publishes to Studio Web by default; Orchestrator deploy requires `uipath-platform`.

## Pattern 4 — Build + verify UI automation on the live app

**When it applies:** user wants to build a UI automation AND observe it running on the live app for diagnostic purposes.

```
1. uipath-rpa      → build the workflow end-to-end
2. uipath-rpa      → testing (mandatory)
3. uipath-interact → observe the live app, capture screenshots / snapshots to diagnose issues
4. uipath-rpa      → apply fixes from findings; repeat 3–4 as needed
```

## Pattern 5 — Verify or fix existing automation against a running app

**When it applies:** an automation already exists; the user wants to investigate a UI issue against the live app and fix it.

```
1. uipath-interact → interact with the live app, identify the UI issue
2. uipath-rpa      → fix the automation based on uipath-interact findings
3. uipath-rpa      → testing for the fix (mandatory)
```

## Pattern 6 — Agent that uses RPA processes as tools

**When it applies:** the request is for an agent whose tools are RPA processes that need to be created and published.

```
1. uipath-rpa      → create and validate the RPA process(es) the agent will call
2. uipath-rpa      → testing for the RPA processes (mandatory)
3. uipath-platform → deploy the RPA process(es) to Orchestrator
4. uipath-agents   → create the agent, bind the published processes as tools
5. uipath-agents   → testing for the agent (mandatory)
6. uipath-agents   → deploy
```

## Pattern routing for PDD-driven lane

When deriving tasks from an SDD, the planner picks a pattern based on the SDD's project list:

| SDD shape | Pattern(s) used |
|---|---|
| Single RPA project, no deploy mention | Pattern: simple `uipath-rpa` build + testing |
| Single RPA project, deploy to Orchestrator | Pattern 1 |
| RPA Master Project (multiple sub-projects, queue-connected) | Pattern 1 applied per sub-project, then cross-project deploy via `uipath-platform` |
| Solution with Flow + RPA + Agents | Pattern 2 expanded across all included products |
| Solution overview SDD | Compose multiple patterns; respect cross-product integration order from §Cross-Project Data Flow |
| API Workflow (single product) | API Workflow specialist + `uipath-platform` for deploy + testing |

Cross-project integration order (general rule): **dependencies before dependents**. Build callable resources (RPA processes, API Workflows, agents-as-tools) before the products that consume them (Flows, Cases, parent agents).

## Pattern composition for Solutions

Solution-scope SDDs produce a unified project list. The planner walks the list and emits one pattern segment per project, then sequences them so that integrated components are built before their consumers:

1. Build all leaf resources (libraries, callable API Workflows, RPA processes used as agent tools).
2. Run testing for each leaf.
3. Deploy leaf resources to Orchestrator.
4. Build orchestrators (Flows, parent agents, Cases) using the published leaf references.
5. Run testing for each orchestrator.
6. Deploy orchestrators.
7. End-to-end validation.

## Anti-patterns

1. **Routing UI automation through `uipath-interact` for element discovery or selector work.** `uipath-rpa` is the sole workflow authoring skill. `uipath-interact` is only for live-app interaction and post-build verification.
2. **Splitting a single-app UI automation into a "discovery" task plus an "authoring" task.** `uipath-rpa` owns end-to-end authoring including target configuration. One task, one skill.
3. **Skipping the dedicated Testing task per generation skill.** Testing is mandatory and lives at the patterns level — every generation step in every pattern is followed by a testing step.
4. **Deploying via `uipath-rpa` or `uipath-maestro-flow`.** Deployment to Orchestrator always goes through `uipath-platform`. The build skills do not deploy.
5. **Building Flow nodes that reference resources before the resources exist.** Use Pattern 2: mock placeholders, build resources, then replace mocks. Never reference an unpublished resource by ID.
