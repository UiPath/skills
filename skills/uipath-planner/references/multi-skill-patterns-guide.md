# Multi-skill Patterns Guide

Use this guide to decide whether a request is single-skill (load one specialist) or multi-skill (emit a plan).

## Routing

Emit a multi-skill plan when a request crosses specialist boundaries, requires another product to exist first, or asks one skill to consume another skill's result. Use one specialist when one skill owns the deliverable end-to-end, the user modifies an existing automation in one project, or the request is read-only, diagnostic, or exploratory.

Single-app UI automation—one project, live app, and workflow—is a single-skill `uipath-rpa` task. `uipath-rpa` owns authoring, live-app exploration, and probing.

Inline nodes are not components. A Flow containing only inline HITL QuickForm, script, connector activity, or inline agent nodes is a single-skill `uipath-maestro-flow` task; the flow author scaffolds and authors those nodes and reads the HITL plugin reference inline. A Flow is multi-skill only when it orchestrates separate buildable projects, such as a standalone RPA process, coded agent, or coded app, each needing its own specialist.

## Pattern 1 — RPA build + deploy to Orchestrator

**When it applies:** Build an RPA workflow and deploy it to Orchestrator.

```
1. uipath-rpa      → create / edit, validate, build the workflow
2. uipath-rpa      → testing (mandatory)
3. uipath-solution → pack, publish, deploy to Orchestrator (`uip solution` lifecycle)
```

`uipath-rpa` does not deploy. For solution-bundled RPA, use `uipath-solution` (`uip solution pack/publish/deploy`). For raw single-package Orchestrator operations not wrapped in `.uipx`, defer to `uipath-platform`.

Attended re-authentication remains in the RPA build task. If the SDD includes §9 *Interactive Authentication / Re-auth Handoff* (human-only login such as hardware token, smart card, or biometric), implement the pause, handoff, and state-verified resume per [attended-reauth-pattern-guide.md](attended-reauth-pattern-guide.md). Pass the handoff contract as business intent; do not create a separate task or describe the activities.

## Pattern 2 — Flow with local resources

**When it applies:** A Flow and its separate buildable components are peer sibling projects under one `.uipx` solution at the current working directory. Components are distinct `.uipx` projects or standalone RPA `.xaml`/`.cs` processes, coded agents, or coded apps. Inline nodes are not components. Scaffold each component in this plan, or use a placeholder contract when it is not built here. `uipath-maestro-flow` owns flow authoring and publication.

```
1. uipath-maestro-flow   → create solution, init flow project
2. <skill per component> → fan out: one task per component, routed by type
                           (rpa → uipath-rpa; agent → uipath-agents; app → uipath-coded-apps)
3. <skill per component> → testing for each component (mandatory)
4. uipath-maestro-flow   → wire all components, validate, finalize
5. uipath-maestro-flow   → testing for the flow (mandatory)
```

## Pattern 3 — Flow with deployed resources

**When it applies:** A Flow consumes standalone Orchestrator tenant resources that are already published or will be published in this session. It references tenant identity, not peer sibling projects under a local solution.

```
1. <component skill>   → scaffold any unbuilt component
2. <component skill>   → testing for the component (mandatory)
3. uipath-solution     → deploy the component to Orchestrator via `uip solution` (RPA always needs uipath-solution; agents self-deploy; coded apps deploy via `uip solution` when the coded-app folder is under a parent `.uipx` — `uip codedapp init` under a solution auto-registers as `Type: "AppV2"`. Only standalone coded apps with no parent `.uipx` self-deploy via `uip codedapp pack` → `uip codedapp publish` → `uip codedapp deploy`.)
4. uipath-maestro-flow → design and wire the flow against the published components, validate, finalize
5. uipath-maestro-flow → testing for the flow (mandatory)
```

`<component skill>` is `uipath-rpa`, `uipath-agents`, or `uipath-coded-apps` by component type.

**BPMN is a peer orchestrator to Flow.** Apply Patterns 2 and 3 to a Maestro BPMN process by substituting `uipath-maestro-bpmn` for `uipath-maestro-flow`. Inline `uipath:*` elements—scriptTask, businessRuleTask, connector, and userTask/HITL—are authored by the BPMN specialist and are not separate components. Only separate buildable RPA processes, coded agents, and coded apps fan out.

## Pattern 4 — Flow deploy to Orchestrator

**When it applies:** The Flow exists and must be deployed to Orchestrator.

```
1. uipath-maestro-flow → validate, `uip maestro flow pack`
2. uipath-maestro-flow → testing (mandatory)
3. uipath-solution     → publish and deploy to Orchestrator via `uip solution`
```

Use `uipath-solution` for deployment of the wrapping `.uipx` solution. For a non-solution single package, route deployment to `uipath-platform`.

## Pattern 5 — Agent using RPA processes as tools

**When it applies:** The Agent's tools are RPA processes that must be created and published.

```
1. uipath-rpa      → create and validate the RPA process(es) the agent will call
2. uipath-rpa      → testing for the RPA processes (mandatory)
3. uipath-solution → deploy the RPA process(es) to Orchestrator via `uip solution`
4. uipath-agents   → create the agent, bind the published processes as tools
5. uipath-agents   → testing for the agent (mandatory)
6. uipath-agents   → deploy
```

## Pattern 6 — Build an AgentHub MCP server

**When it applies:** Register an AgentHub MCP server wrapping a coded agent or requiring Orchestrator-backed authentication that does not yet exist. Pure `uipath-mcp-servers` work—`uipath` servers with resource tools, `command` / `platform` servers, or `remote` / `swagger` servers whose auth assets already exist—is single-skill and goes directly to `uipath-mcp-servers`.

For a not-yet-built coded agent (`coded` server):

```
1. uipath-agents      → develop and publish the coded agent (deploys end-to-end as an Orchestrator process)
2. uipath-mcp-servers → register the coded MCP server against the published process key
```

For missing Orchestrator assets used by `remote` / `swagger` Bearer or header substitution:

```
1. uipath-platform    → create the Orchestrator asset(s) holding the auth values
2. uipath-mcp-servers → register the server with asset-substituted headers
```

## Pattern routing for PDD-driven work

| SDD shape | Pattern(s) used |
|---|---|
| Single RPA project, no deploy mention | Simple `uipath-rpa` build + testing |
| Single RPA project, deploy to Orchestrator | Pattern 1 |
| Single-host SDD with absorbed components (RPA-primary consuming an IXP model, custom connector, or API Workflow in-process) | Leaf-first: build and test each consumed component via `uipath-ixp` / `uipath-connector-builder` / `uipath-api-workflow`, deploy leaves, then the host project per Pattern 1 — no orchestrator task |
| RPA Master Project (multiple sub-projects, queue-connected) | Pattern 1 per sub-project, then cross-project deploy via `uipath-solution` in one `.uipx` |
| Solution with Flow + RPA + Agents, components built fresh | Pattern 2 expanded across included products |
| Solution with Flow consuming pre-published Orchestrator resources | Pattern 3 |
| BPMN orchestrating components built fresh | Pattern 2, substituting `uipath-maestro-bpmn` for `uipath-maestro-flow` |
| BPMN consuming pre-published Orchestrator resources | Pattern 3, substituting `uipath-maestro-bpmn` |
| Solution overview SDD | Compose multiple patterns and respect §Cross-Project Data Flow |
| API Workflow (single product) | `uipath-api-workflow` + `uipath-solution` for deploy + testing |
| Agent with RPA tools in §3 Tools | Pattern 5 |

Deploy routing is constraint-gated. If the delivery model blocks Solutions (`.uipx`) per [platform-availability-guide.md](platform-availability-guide.md)—standalone, Automation Suite older than 2.2510, or user exclusion—replace every `uipath-solution` deploy/publish step with per-package Orchestrator publishing routed to `uipath-platform`.

Build dependencies before dependents: callable resources (RPA processes, API Workflows, and agents-as-tools) precede consumers (Flows, Cases, and parent agents).

## Pattern composition for Solutions

For a solution-scope SDD, create one unified project list, apply the relevant pattern to each project, and sequence integrated components as follows:

1. Build all leaf resources (libraries, custom connectors, IXP models, Coded Functions, callable API Workflows, and RPA processes used as agent tools).
2. Run testing for each leaf.
3. Deploy leaf resources to Orchestrator.
4. Build orchestrators (Flows, parent agents, and Cases) using published leaf references.
5. Run testing for each orchestrator.
6. Deploy orchestrators.
7. Perform end-to-end validation.

## Anti-patterns

1. **Do not split single-app UI automation into discovery and authoring.** `uipath-rpa` owns end-to-end authoring, target configuration, and live-app exploration; use one task and one skill.
2. **Do not skip the dedicated Testing task per generation skill.** Testing is mandatory and follows every generation step in every pattern.
3. **Do not deploy via `uipath-rpa` or `uipath-maestro-flow`.** Deploy `.uipx`-wrapped solutions through `uipath-solution` (`uip solution pack/publish/deploy`); defer non-solution single-package Orchestrator operations to `uipath-platform`. Build skills do not deploy.
4. **Do not build Flow nodes that reference resources before those resources exist.** Use Pattern 2 with mocked-then-wired resources or Pattern 3 with components built and deployed first; never reference an unpublished resource by ID.
