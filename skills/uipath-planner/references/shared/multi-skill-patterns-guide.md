# Multi-skill Patterns Guide

Which specialist owns what, and the common request shapes that span more than one of them. Use this guide when assigning tasks to specialists and when deciding whether a request is single-skill (load one specialist directly) or multi-skill (emit a plan).

## Skill capability map — which specialist owns what

What each specialist owns, for the plans `decompose` writes; genomes take their Build With names from [skill-mapping-guide.md](skill-mapping-guide.md). **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows (XAML and C# coded): create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end, including live-app exploration and probing. | No (relies on Studio) | **No** — defer to `uipath-solution` for `.uipx` multi-project, `uipath-platform` for single non-solution packages |
| `uipath-agents` | AI agents — code-based (LangGraph / LlamaIndex / OpenAI Agents) and low-code (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-functions` | Coded Functions — Python (`uip function new -l py`; Pydantic typed I/O) or TypeScript/JavaScript (`-l ts / js`, TypeScript default; `defineFunction` + schema-first typed I/O) — atomic deterministic logic: transforms, custom-auth API calls, ERP/IS-connection queries. Runs serverless or on an RPA robot; a JS/TS function is delivered as a run-as-job function or an HTTP endpoint (Coded App backends) — one calling mode per function. Invoked from Maestro (Flow/BPMN), agents-as-tools, Orchestrator API, or its HTTP trigger. No LLM/agent loop (that → `uipath-agents`) | Yes (`uip login`) | **Yes** — `uip function pack/publish` |
| `uipath-rules` | Business Rules projects — one `.dmn` decision table (DMN 1.5) per project: `uip rules init`, `refresh`, `validate`, `debug`. Called by BPMN business rule tasks, Case `business-rule` tasks, and RPA | Yes (`uip login` for `debug`) | **No** — `uip solution pack/publish/deploy` via `uipath-solution` |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution`; non-solution single package → `uipath-platform` |
| `uipath-maestro-bpmn` | `.bpmn` files — standards-based BPMN 2.0 process orchestration (gateways, events, boundary timeouts, subprocesses, multi-instance) over RPA, agents, APIs, HITL. Authors its own inline userTask/HITL nodes. | Yes (`uip login`) | **Yes** — packages, uploads, publishes/deploys, and runs via `uip maestro bpmn`; Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution` |
| `uipath-maestro-case` | Case Management authoring — `caseplan.case` from an SDD (`case pack` compiles it to `caseplan.case.bpmn`; authoring `.bpmn` directly is `uipath-maestro-bpmn`) | Yes (`uip login`) | **Partial** — publishes to Studio Web and Orchestrator itself; `.uipx` solution deploy → `uipath-solution` |
| `uipath-api-workflow` | API Workflows (JSON `document.dsl`): author, run locally (`uip api-workflow run`), connector activities | Yes (`uip login`) | **No** — `uip solution pack/publish` via `uipath-solution` |
| `uipath-human-in-the-loop` | HITL node authoring — approval gates, escalations, write-back validation inside **Flow** projects. Coded-agent HITL → `uipath-agents`; BPMN / Case / RPA own theirs inline (userTask / task type / Action Center) | No (authoring only) | **No** — ships inside the host project |
| `uipath-platform` | Auth (`uip login`), Orchestrator (folders, processes, jobs, machines, users, roles), resources (assets, queues, storage buckets + bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), Data Fabric entities/records/files/choice-sets (`uip df`), traces, licensing | Yes (auth hub) | **Yes** — for every project outside a solution (`Packaging: standalone`) and Orchestrator-side post-deploy ops |
| `uipath-ixp` | Document Understanding / IXP — extraction from semi-structured documents (invoices, forms): taxonomy, model, classify / extract / validate. Standalone project, or the extraction step a primary consumes | Yes (`uip login`) | **Partial** — model publish/tag via `uip ixp`; consumed by the host project |
| `uipath-connector-builder` | Integration Service **custom connector** authoring (REST+JSON) on disk via `uip is connectors builder` — build a connector when the catalog has none for a required integration, for any project type, RPA included. See [Integration mechanism](component-placement-guide.md#integration-mechanism--connection-before-raw-api-call) | Yes (`uip login`) | **Yes** — import/publish is deployment (`uip is connectors`) |
| `uipath-mcp-servers` | UiPath AgentHub MCP server registration (6 types: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`) and resource-tool authoring on `uipath`-type servers (`automation`, `agent`, `agentic-process`, `api-workflow`). Wraps Orchestrator resources, external HTTP MCP endpoints, OpenAPI specs, published coded agents, local subprocess commands, or first-party UiPath services as MCP tools. NOT for FastMCP / Python `mcp` SDK work. | Yes (`uip login`) | **Yes** — registration is deployment (posts directly to AgentHub) |
| `uipath-solution` | `uip solution` lifecycle (init, pack, publish, deploy, activate) for `.uipx` solutions. | Yes (`uip login`) | **Yes** — for every project inside a solution (`Packaging: solution`) |

## When to emit a multi-skill plan

Emit a multi-skill plan when the request clearly spans more than one specialist. Single-skill tasks (e.g., "create a workflow that sends an email") go directly to the specialist — no plan needed.

A request is **multi-skill** when at least one of the following is true:

- Build + deploy crosses skill boundaries (RPA build → platform deploy)
- A target product cannot exist without other products built first (Flow needs RPA processes that don't exist yet)
- The user wants the result of one skill to be consumed by another (Agent uses RPA processes as tools)

A request is **single-skill** when:

- The deliverable is owned end-to-end by one skill (e.g., "create a UiPath RPA workflow that fills a form" — one project, one app, one workflow)
- The user is modifying an existing automation in a single project
- The request is read-only / diagnostic / exploration only

> **Important:** Single-app UI automation (one project, one live app, one workflow) is **not** a multi-skill pattern — it's a single-skill `uipath-rpa` task. `uipath-rpa` owns UI automation authoring end-to-end, including live-app exploration and probing.

> **Important — inline nodes are not components.** A Flow whose only "components" are **inline nodes** (HITL QuickForm, script, connector activity, inline agent) is a **single-skill** `uipath-maestro-flow` task, **not** a multi-skill plan. The flow author journey scaffolds the solution and authors every inline node itself — it reads the HITL plugin reference inline; it does not hand off to `uipath-human-in-the-loop` as a separate task. Counting inline pieces as separate skills ("solution + flow + human-in-the-loop") is a mis-classification. A flow only becomes **multi-skill** (Pattern 2/3) when it orchestrates **separate buildable projects** — distinct `.uipx` projects such as a standalone RPA process, a coded agent, or a coded app, each of which needs its own specialist.

## Pattern 1 — RPA build + deploy to Orchestrator

**When it applies:** user wants to build an RPA workflow and deploy it to Orchestrator (most common production flow).

```
1. uipath-rpa      → create / edit, validate, build the workflow
2. uipath-rpa      → testing (mandatory)
3. uipath-platform → publish the package and create the process   (project outside a solution — Packaging: standalone)
   uipath-solution → pack, publish, deploy the `.uipx`             (project inside a solution — Packaging: solution)
```

`uipath-rpa` does not deploy. The deploy skill follows the project, never a default: outside a solution → `uipath-platform`; inside a solution → `uipath-solution`.

> **Attended re-auth handoff is inside the RPA build step, not a separate skill.** When the request needs an attended re-auth handoff (human-only login — hardware token, smart card, biometric), the `uipath-rpa` build task implements the pause/handoff/state-verified-resume per [attended-reauth-pattern-guide.md](../design/attended-reauth-pattern-guide.md). Pass the handoff contract as business intent; do not split it into its own task or describe the activities.

## Pattern 2 — Flow with local resources

**When it applies:** Flow and the components it orchestrates are peer sibling projects under one `.uipx` solution at the current working directory. **Components here means separate buildable projects** (a standalone RPA `.xaml`/`.cs` process, a coded agent, a coded app) — each scaffolded as a distinct project routed to its own specialist. Inline flow nodes are **not** components (see the blockquote above); `uipath-maestro-flow` authors them itself in steps 1/4. Each component is scaffolded as part of this plan (or replaced by a placeholder contract when not built here). Where the flow is authored and published during the build is `uipath-maestro-flow`'s own workflow — not a plan field.

```
1. uipath-maestro-flow   → create solution, init flow project
2. <skill per component> → fan out: one task per component, routed by type
                           (rpa → uipath-rpa; agent → uipath-agents; app → uipath-coded-apps)
3. <skill per component> → testing for each component (mandatory)
4. uipath-maestro-flow   → wire all components, validate, finalize
5. uipath-maestro-flow   → testing for the flow (mandatory)
```

`<component skill>` is `uipath-rpa`, `uipath-agents`, or `uipath-coded-apps` depending on the component type.

## Pattern 3 — Flow with deployed resources

**When it applies:** Flow references components that exist as standalone Orchestrator tenant resources — already published, or to be published as part of this session. The flow consumes them by tenant identity, not as peer sibling projects under a local solution.

```
1. <component skill>   → scaffold any unbuilt component
2. <component skill>   → testing for the component (mandatory)
3. uipath-solution     → deploy the component to Orchestrator via `uip solution` (RPA always needs uipath-solution; agents self-deploy; coded apps deploy via `uip solution` when the coded-app folder is under a parent `.uipx` — `uip codedapp init` under a solution auto-registers as `Type: "AppV2"`. Only standalone coded apps with no parent `.uipx` self-deploy via `uip codedapp pack` → `uip codedapp publish` → `uip codedapp deploy`.)
4. uipath-maestro-flow → design and wire the flow against the published components, validate, finalize
5. uipath-maestro-flow → testing for the flow (mandatory)
```

<!--skill-flavor:bpmn-peer-orchestrator:start-->
> **BPMN is a peer orchestrator to Flow.** The same Pattern 2/3 structure applies to a Maestro BPMN process — swap `uipath-maestro-bpmn` for `uipath-maestro-flow`. As with Flow, inline elements (script tasks, business rules, connectors, human tasks/HITL) are authored by the BPMN specialist itself and are NOT separate components — only separate buildable projects (standalone RPA process, coded agent, coded app) fan out.
<!--skill-flavor:bpmn-peer-orchestrator:end-->

## Pattern 4 — Flow deploy to Orchestrator

**When it applies:** the flow exists; user wants it deployed to Orchestrator.

```
1. uipath-maestro-flow → validate, `uip maestro flow pack`
2. uipath-maestro-flow → testing (mandatory)
3. uipath-solution     → publish and deploy to Orchestrator via `uip solution`
```

Orchestrator deploy of the wrapping `.uipx` solution requires `uipath-solution`. For a non-solution single package (no `.uipx` wrapper), route the deploy step to `uipath-platform` instead.

## Pattern 5 — Agent that uses RPA processes as tools

**When it applies:** the request is for an agent whose tools are RPA processes that need to be created and published.

```
1. uipath-rpa      → create and validate the RPA process(es) the agent will call
2. uipath-rpa      → testing for the RPA processes (mandatory)
3. uipath-solution → deploy the RPA process(es) to Orchestrator via `uip solution`
4. uipath-agents   → create the agent, bind the published processes as tools
5. uipath-agents   → testing for the agent (mandatory)
6. uipath-agents   → deploy
```

## Pattern 6 — Build an AgentHub MCP server

**When it applies:** the request is to register an AgentHub MCP server that wraps a coded agent or uses Orchestrator-asset-backed auth that does not exist yet. Pure `uipath-mcp-servers` work — `uipath` servers with resource tools, `command` / `platform` servers, or `remote` / `swagger` servers with auth assets already in place — is single-skill; go straight to `uipath-mcp-servers`.

Wrapping a not-yet-built coded agent (server type `coded`):

```
1. uipath-agents      → develop and publish the coded agent (deploys end-to-end as an Orchestrator process)
2. uipath-mcp-servers → register the coded MCP server against the published process key
```

Orchestrator assets needed for `remote` / `swagger` Bearer / header substitution that don't exist yet:

```
1. uipath-platform    → create the Orchestrator asset(s) holding the auth values
2. uipath-mcp-servers → register the server with asset-substituted headers
```

## Pattern composition for Solutions

A multi-project plan emits one pattern segment per project, then sequences them so that integrated components are built before their consumers:

1. Build all leaf resources (libraries, custom connectors, IXP models, Coded Functions, callable API Workflows, RPA processes used as agent tools).
2. Run testing for each leaf.
3. Deploy leaf resources to Orchestrator.
4. Build orchestrators (Flows, parent agents, Cases) using the published leaf references.
5. Run testing for each orchestrator.
6. Deploy orchestrators.
7. End-to-end validation.

## Anti-patterns

1. **Splitting a single-app UI automation into a "discovery" task plus an "authoring" task.** `uipath-rpa` owns end-to-end authoring including target configuration and live-app exploration. One task, one skill.
2. **Skipping the dedicated Testing task per generation skill.** Testing is mandatory and lives at the patterns level — every generation step in every pattern is followed by a testing step.
3. **Deploying via `uipath-rpa` or `uipath-maestro-flow`.** Deployment of `.uipx`-wrapped solutions to Orchestrator goes through `uipath-solution` (`uip solution pack/publish/deploy`); for non-solution single-package Orchestrator ops, defer to `uipath-platform`. The build skills do not deploy.
4. **Building Flow nodes that reference resources before the resources exist.** Use Pattern 2 (local resources, mocked then wired) or Pattern 3 (build and deploy components first, then reference). Never reference an unpublished resource by ID.
