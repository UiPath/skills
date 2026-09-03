# Planning Phase 1: Discovery & Architectural Design

Discover capabilities, then design flow topology: node types, edges, inputs, and outputs. Produce a **mermaid diagram** and structured tables for review before implementation.

> **Registry rules:** `registry search` and `registry list` are allowed for discovery. Run `registry get` once for every OOTB action node type used (`core.action.http`, `core.action.http.v2`, `core.action.script`, `core.action.transform`, queue actions, etc.); this provides real schemas, ports, and required fields. Defer `registry get` for connector nodes requiring `--connection-id` and resource nodes requiring `--local` or published-resource resolution to [Planning Phase 2: Implementation](planning-impl.md).

## Before You Build: Is Maestro the Right Home?

Run this gate before designing topology. Maestro fits long-running cases requiring one durable instance, multiple waits, branching, parallelism, SLAs, cross-product composition, or per-case visibility. A single-wait, mostly linear process may be simpler as a queue + Action Center state machine; if so, stop and hand off to [/uipath:uipath-rpa](/uipath:uipath-rpa) + [/uipath:uipath-platform](/uipath:uipath-platform).

Ask: **Where does the case live now, and where should it live between steps?**

| Factor | Maestro flow | Queue + Action Center |
| --- | --- | --- |
| Waits | Several waits, branches, or parallel paths | One human or external wait |
| Visibility | Need exact current case location | Queue status is sufficient |
| Topology | Branching, fan-out/merge, SLAs | Mostly linear |
| Ownership | Team accepts orchestration as an artifact | RPA-only team with queue infrastructure |
| Composition | RPA, agents, connectors, humans | RPA + Action Center |
| Overhead | Justified by lifecycle complexity | Not justified for one-shot work |

A single-wait lifecycle is valid queue + Action Center; multi-wait, branched, or visibility-critical lifecycles favor Maestro. For existing RPA projects, keep executors and lift only orchestration; see [brownfield.md — Converting an existing project to Maestro](brownfield.md#converting-an-existing-project-to-maestro).

## Process

1. Analyze the user's requirements.
2. **Discover capabilities** when connector or resource nodes are needed; run `registry search` / `registry list` (see [Capability Discovery](#capability-discovery)).
3. Select node types from the [Plugin Index](#plugin-index); read each relevant `planning.md` for heuristics, ports, and key inputs.
4. Define edges using [Wiring Rules](#wiring-rules) and plugin port documentation.
5. Identify suspected inputs and outputs for every node.
6. Generate a mermaid diagram.
7. Validate mermaid syntax using [Mermaid Validation Rules](#mermaid-validation-rules).
8. Present the plan for review.
9. Iterate until approved, then hand off to [Planning Phase 2: Implementation](planning-impl.md).

## Capability Discovery

Run discovery when connector or resource nodes are needed; skip it for OOTB-only flows. Discovery confirms connectors, operations, and published or in-solution resources before topology selection.

```bash
# Registry should already be refreshed (greenfield.md Step 3 runs `registry pull`)
uip maestro flow registry search <keyword> --output json
uip maestro flow registry search outlook --output json
uip maestro flow registry search "invoice process" --output json
uip maestro flow registry search agent --output json
uip maestro flow registry list --output json

# Run `get` for every OOTB action node type used:
uip maestro flow registry get core.action.script --output json
# Repeat for transform, queue actions, and every other OOTB action type.
# `core.action.http.v2` is a managed-HTTP connector node, not OOTB; discover it via
# [http/planning.md](plugins/http/planning.md).
```

Without `uip login`, the registry shows OOTB nodes only. If connectors or resources are required, run `uip login status --output json` first. For sibling projects in the same `.uipx` solution, run from the flow project directory:

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry search "<keyword>" --local --output json
```

Prefer in-solution resources over mocks. `--local` omits `AvailableOnTenant`; an empty `search --local` is not authoritative, so confirm with `list --local` before treating a resource as absent.

### Check Connector Connections

For every discovered connector, follow [plugins/connector/planning.md](plugins/connector/planning.md). Never guess a connector key; use the key from registry search. Run:

```bash
uip is connections list "<connector-key>" --all-folders --output json
```

`--all-folders` is mandatory; plain `uip is connections list "<connector-key>"` is forbidden for discovery. Record a connection only when `IsDefault: Yes` and `State: Enabled`.

Treat an empty result as suspicious. Treat it as a real absence only when: (a) the key came from `registry search`, (b) `--all-folders` was used, and (c) a `--refresh` retry was also empty. Only then put the gap in **Open Questions**; do not ask about connection creation before verification. See [connector/impl.md](plugins/connector/impl.md) for the shared empty-result recovery path.

Record:

- **Connectors:** existence, available operations from node type names, and healthy connection availability. Defer field details to Phase 2.
- **Resources:** check `list --local` or `search --local` first, then tenant registry; record whether each RPA process, agent, or flow exists. Defer schemas to Phase 2.
- **Gaps:** use `core.action.http.v2` manual mode when no connector exists; use `--local` resources when unpublished but in solution; use `core.logic.mock` when a resource is neither in solution nor published; flag connectors lacking connections after verified empty results.

Run `registry get` for OOTB actions during discovery. Defer connector `registry get --connection-id` and resource `registry get --local` or published resolution to Phase 2.

## Plugin Index

Read the relevant plugin `planning.md` when selecting a type.

### Triggers

| Node Type | Plugin | Select when |
| --- | --- | --- |
| `core.trigger.manual` | inline | On-demand user or API start |
| `core.trigger.scheduled` | [scheduled-trigger](plugins/scheduled-trigger/planning.md) | Recurring schedule |
| IS connector trigger | [connector-trigger](plugins/connector-trigger/planning.md) | External event; type `uipath.connector.trigger.<key>.<trigger>` |
| `core.trigger.voice` | [inline-voice-agent](plugins/inline-voice-agent/planning.md) | Flow starts when a phone call arrives on a bound number (inbound voice topology) |

Every flow has exactly one trigger, first in topology. IS connector triggers replace manual or scheduled triggers. `core.trigger.manual` has no inputs and output port `output`.

### Actions

| Node Type | Plugin | Select when |
| --- | --- | --- |
| `core.action.script` | [script](plugins/script/planning.md) | Custom logic, computation, formatting, transformation |
| `core.action.http.v2` | [http](plugins/http/planning.md) | REST API; connector or manual mode; replaces deprecated `core.action.http` |
| `core.action.transform` | [transform](plugins/transform/planning.md) | Declarative map, filter, or group-by |
| Wait for events | [connector-trigger](plugins/connector-trigger/planning.md) | Mid-flow external event; type `uipath.connector.event.<key>.<event>` with `input` |
| `uipath.pattern.batch-transform` | [batch-transform](plugins/batch-transform/planning.md) | Append LLM-generated columns to CSV rows; gated by `canvas.nodes.batch-transform` |
| `uipath.pattern.deep-rag` (Summarize) | [summarize](plugins/summarize/planning.md) | Synthesis/Q&A over one document with optional citations; gated by `canvas.nodes.summarize` |
| `core.logic.delay` | [delay](plugins/delay/planning.md) | Duration or date wait |
| `core.action.queue.create` | [queue](plugins/queue/planning.md) | Fire-and-forget robot work |
| `core.action.queue.create-and-wait` | [queue](plugins/queue/planning.md) | Robot work with result wait |
| `core.datafabric.read` | [data-fabric](plugins/data-fabric/planning.md) | Read one record or a filtered list from a Data Fabric entity; gated by `canvas.nodes.read-entity` |
| `core.datafabric.create` | [data-fabric](plugins/data-fabric/planning.md) | Insert a record and return the stored row; gated by `canvas.nodes.create-entity` |
| `core.datafabric.update` | [data-fabric](plugins/data-fabric/planning.md) | Patch named columns on one record; gated by `canvas.nodes.update-entity` |
| `core.datafabric.delete` | [data-fabric](plugins/data-fabric/planning.md) | Delete one record; gated by `canvas.nodes.delete-entity` |
| `uipath.human-in-the-loop.quick-form` | [hitl](plugins/hitl/planning.md) | Inline human review, approval, or data entry |
| `uipath.conversational.voice.create-outgoing-call` | [inline-voice-agent](plugins/inline-voice-agent/planning.md) | Dial an outbound phone call and emit its `callContext` (outbound voice topology) |
| `uipath.conversational.voice.end-call` | [inline-voice-agent](plugins/inline-voice-agent/planning.md) | End the active call in a voice flow |

### Control Flow

| Node Type | Plugin | Select when |
| --- | --- | --- |
| `core.logic.decision` | [decision](plugins/decision/planning.md) | Binary boolean branch |
| `core.logic.switch` | [switch](plugins/switch/planning.md) | Three or more ordered cases |
| `core.logic.loop` | [loop](plugins/loop/planning.md) | Iterate collection |
| `core.logic.merge` | [merge](plugins/merge/planning.md) | Synchronize parallel branches |
| `core.control.end` | [end](plugins/end/planning.md) | Graceful completion; one per terminal path |
| `core.logic.terminate` | [terminate](plugins/terminate/planning.md) | Immediate fatal abort |
| `core.subflow` | [subflow](plugins/subflow/planning.md) | Reusable isolated-scope group |

### Connector Nodes

Connector nodes are Integration Service nodes, not built-in. They appear after `uip login` and `uip maestro flow registry pull`. Use [connector](plugins/connector/planning.md) when a pre-built connector exists. In Phase 1 record `connector: <service-name>` and intended operation; Phase 2 resolves exact type, connection, and fields.

### Agent Nodes

| Type | Plugin | Select when |
| --- | --- | --- |
| `uipath.agent.autonomous` | [inline-agent](plugins/inline-agent/planning.md) | Low-code agent scaffolded inside this flow via `uip agent init --inline-in-flow`, tightly coupled, not independently reused |
| `uipath.core.agent.{key}` | [agent](plugins/agent/planning.md) | Separate in-solution or published agent, reusable and independently versioned |
| `uipath.agent.voice` | [inline-voice-agent](plugins/inline-voice-agent/planning.md) | AI agent that converses in real time on a live phone call — an inline conversational agent (`settings.voice` in its `agent.json`) wired to a `callContext` |

See [inline-agent/planning.md — Inline vs Published Agent Decision Table](plugins/inline-agent/planning.md#inline-vs-published-agent-decision-table).

### Resource Nodes

| Category | Type | Plugin |
| --- | --- | --- |
| RPA Process | `uipath.core.rpa-workflow.{key}` | [rpa](plugins/rpa/planning.md) |
| Agent | `uipath.core.agent.{key}` | [agent](plugins/agent/planning.md) |
| Agentic Process | `uipath.core.agentic-process.{key}` | [agentic-process](plugins/agentic-process/planning.md) |
| Flow | `uipath.core.flow.{key}` | [flow](plugins/flow/planning.md) |
| API Workflow | `uipath.core.api-workflow.{key}` | [api-workflow](plugins/api-workflow/planning.md) |
| Human Task | `uipath.core.human-task.{key}` | [hitl](plugins/hitl/planning.md) |
| Document Extraction | `uipath.ixp.{modelName}.{fullyQualifiedName}` | [ixp](plugins/ixp/planning.md) |

IxP has a two-segment tail, unlike other resource types' single `{key}` tail; both segments are sanitized at registry emit time. See [plugins/ixp/planning.md](plugins/ixp/planning.md).

### Placeholders

Use `core.logic.mock` for TBD steps, missing resources, or prototypes; it has `input` -> `output`.

## Selecting External Service Nodes

Prefer, in order:

1. A curated Integration Service connector ([connector](plugins/connector/planning.md)).
2. `core.action.http.v2` connector mode when the connector lacks the activity, or manual mode for APIs without connectors ([http](plugins/http/planning.md)).
3. An RPA workflow only when there is no API, such as a desktop app or terminal ([rpa](plugins/rpa/planning.md)).

**Data Fabric is not on this ladder.** Reading or writing records in a UiPath Data Fabric entity is not an external-service call: use the native `core.datafabric.*` nodes ([data-fabric](plugins/data-fabric/planning.md)), which need no Integration Service connection. The `uipath-uipath-dataservice` connector activities are the fallback — take them only when the native node's tenant flag is off, when the entity is federated (the native writes require a native entity), or when you need an operation the four nodes do not cover.

## Standard Port Reference

Every edge requires `sourcePort` and `targetPort`.

| Node Type | Inputs | Outputs |
| --- | --- | --- |
| `core.trigger.manual` | — | `output` |
| `core.trigger.scheduled` | — | `output` |
| `uipath.connector.trigger.*` | — | `output` |
| `core.trigger.voice` | — | `output` |
| `uipath.connector.event.*` | `input` | `output`, `error` |
| `core.action.script` | `input` | `success`, `error` |
| `core.action.http.v2` | `input` | `default`, `error`, `branch-{id}` dynamic per `inputs.branches` |
| `core.action.transform` | `input` | `output`, `error` |
| `uipath.pattern.batch-transform` | `input` | `output`, `error` |
| `uipath.pattern.deep-rag` | `input` | `output`, `error` |
| `core.logic.delay` | `input` | `output` |
| `core.logic.decision` | `input` | `true`, `false` |
| `core.logic.switch` | `input` | `case-{id}` dynamic per case, `default` |
| `core.logic.loop` | outer `input`; inner `continue`, `break` | outer `success`, `error`; inner `start` |
| `core.logic.merge` | multiple `input` | `output` |
| `core.control.end` | `input` | — |
| `core.logic.terminate` | `input` | — |
| `core.subflow` | `input` | `output`, `error` |
| `core.logic.mock` | `input` | `output` |
| `uipath.agent.autonomous` | `input` | `success`, `error`, `tool`, `context`, `escalation` |
| `uipath.agent.voice` | `input` | `success`, `error`, `tool`, `context`, `escalation` |
| `uipath.conversational.voice.create-outgoing-call` | `input` | `success`, `error` |
| `uipath.conversational.voice.end-call` | `input` | `success`, `error` |
| `uipath.core.agent.*` | `input` | `output`, `error` |
| `uipath.core.rpa-workflow.*` | `input` | `output`, `error` |
| `uipath.core.human-task.*` | `input` | `output`, `error` |
| `uipath.core.flow.*` | `input` | `output`, `error` |
| `uipath.core.agentic-process.*` | `input` | `output`, `error` |
| `uipath.core.api-workflow.*` | `input` | `output`, `error` |
| `uipath.ixp.*` | `input` | `success`, `error` |
| `uipath.connector.*` | `input` | `output`, `error` |
| `core.action.queue.create` | `input` | `success` |
| `core.action.queue.create-and-wait` | `input` | `success` |
| `core.datafabric.read` | `input` | `output` |
| `core.datafabric.create` | `input` | `output` |
| `core.datafabric.update` | `input` | `output` |
| `core.datafabric.delete` | `input` | `output` (sequencing only — the node produces no data) |
| `uipath.human-in-the-loop.quick-form` | `input` | `completed` |
| `uipath.core.human-task.{key}` | `input` | `output` |

`error` is an implicit source port on action nodes with `supportsErrorHandling: true`, off by default. Wire it only when requirements specify failure behavior; otherwise the node faults the flow. This differs from HTTP `inputs.branches` and content-based decision/switch routing. See [Implicit error port on action nodes](../shared/file-format.md#implicit-error-port-on-action-nodes).

## Wiring Rules

1. Connect source output ports to target input ports.
2. Triggers have no input and are sources only.
3. End/Terminate nodes have no output and are targets only.
4. Every non-trigger node has at least one incoming edge.
5. Every non-terminal node has at least one outgoing edge.
6. Decisions have exactly one `true` and one `false` edge.
7. Switches have one edge per case and optionally `default`.
8. A loop's inner `start` feeds the body, the last body node returns to `continue`, and outer `success` continues after all iterations.
9. Merge accepts one input per parallel path.
10. Do not create cycles except through Loop's `continue` handle.
11. No dangling nodes: every node appears in the edge table as source or target.
12. Add an `error` edge only for a specified failure fallback. Do not set `inputs.errorHandlingEnabled: true` without an error edge. When an error edge exists, set `inputs.errorHandlingEnabled: true`; CLI edge-add/format commands do this automatically, while direct JSON edits must include it. See [Implicit error port on action nodes](../shared/file-format.md#implicit-error-port-on-action-nodes).

Error handlers must produce a distinguishable failure terminal: a distinct End mapping an error/status `out`, `core.logic.terminate`, or a recovery path that rejoins only after valid data is obtained. Never route failure into the happy path or success End. Use Decision/Switch for successful-content routing, not failure detection. Plan required error edges in Phase 1.

## Common Topology Patterns

- **Linear:** `Trigger -> Action A -> Action B -> End`
- **Conditional:** `Trigger -> Fetch -> Decision`; connect `true` and `false` to separate paths and terminals.
- **Parallel:** `Trigger -> Prepare`; fork to actions; join at `Merge`; continue to End.
- **Loop:** `Trigger -> Fetch List -> Loop`; `start` enters the body, the body returns to `continue`, and `success` exits to summary and End.
- **Mixed orchestration:** Maestro owns state, waits, branches, and SLAs; RPA performs mechanical legacy-system work; agents reason; humans approve. Reference separate published or in-solution artifacts rather than rebuilding them in the flow.
- **Scheduled batch:** `Scheduled Trigger -> HTTP -> Loop`; loop body creates queue items; outer success summarizes and ends.

### No-API Source

A source with no API or connector cannot trigger Maestro directly. Use a scheduled RPA bot outside the flow to scrape it and add queue items or upload bucket files; the Maestro flow consumes the queue or scheduled bucket drop. Queue is best for separate cases; bucket is best for batches. Polling latency is at least the scraper interval; real-time is unavailable. Prefer a connector trigger when an event, webhook, or connector exists. The scraper belongs to [/uipath:uipath-rpa](/uipath:uipath-rpa) with scheduling from [/uipath:uipath-platform](/uipath:uipath-platform); only the consuming flow belongs here.

## Output Format

Generate `<SolutionName>.uipath.flow.arch.plan.md` in the **solution directory**, the folder containing `.uipx`, not the project subfolder. The plan covers the entire solution.

### 1. Summary

Write 2–3 sentences describing the end-to-end flow.

### 2. Flow Diagram (Mermaid)

Use a complete diagram with all nodes, edges, branches, and port labels. Use `graph LR`, never `graph TD` or `flowchart`. Use `subgraph` for flows with 10+ nodes. Labels must be plain alphanumeric and spaces only: no `>`, `<`, `(`, `)`, `[`, `]`, `{`, `}`, `:`, `;`, `?`, `&`, or quotes. Do not put node types in labels. Use only `(text)`, `[text]`, and `{text}` shapes: triggers and terminals rounded, actions/connectors/placeholders rectangular, decisions/switches diamonds. Do not use quotes inside delimiters.

### 3. Node Table

| # | Node ID | Name | Category | Node Type | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | trigger | Manual Trigger | trigger | `core.trigger.manual` | — | Trigger event | — |

Include one row per node. Use short alphanumeric or underscore IDs matching the diagram. Inputs are best guesses; use `<PLACEHOLDER>` for URLs, IDs, and connection details Phase 2 must resolve. Outputs describe values downstream nodes consume via `$vars.{nodeId}.*`. Notes identify Phase 2 concerns.

### 4. Edge Table

| # | Source Node | Source Port | Target Node | Target Port | Condition/Label |
| --- | --- | --- | --- | --- | --- |
| 1 | trigger | output | nextNode | input | — |

Every node except the trigger must be a target; every node except End/Terminate must be a source. Ports must match [Standard Port Reference](#standard-port-reference). Include error edges exactly when requirements specify failure fallbacks, and ensure they reach a distinguishable failure terminal.

### 5. Inputs & Outputs

| Direction | Name | Type | Description |
| --- | --- | --- | --- |
| `in` | inputName | `string` | Input description |
| `out` | outputName | `number` | Output description |
| `inout` | stateName | `array` | State description |

Include all flow inputs, outputs, and inout state.

### 6. Connector Summary (omit if no connectors)

| Node ID | Service | Intended Operation | Phase 2 Action |
| --- | --- | --- | --- |
| nodeId | Service | Operation | Resolve connector key, bind connection, resolve IDs and fields |

### 7. Open Questions (omit if none)

Prefix each item with `**[REQUIRED]**` or `**[OPTIONAL]**`. Include unresolved user decisions and verified missing connections/resources.

## Mermaid Validation Rules

Before presenting the plan, validate every rule:

1. First line is `graph LR`, not `flowchart`.
2. Node IDs contain only `[a-zA-Z0-9_]`; use `fetchData`, not `fetch-data` or `fetch.data`.
3. IDs must not start with or equal reserved words: `end`, `subgraph`, `graph`, `flowchart`, `direction`, `click`, `style`, `classDef`, `class`, `linkStyle`, `callback`, `default`. Avoid IDs such as `endWarm`, `defaultPath`, and `styleNode`.
4. Labels have no quotes or prohibited special characters; replace `>` / `<` with words like over/under.
5. Shapes are only `(text)`, `[text]`, and `{text}`. Do NOT use `([text])` (stadium), `{{text}}` (hexagon), or other extended shapes.
6. Edges use `-->` or `-->|label|`; empty labels such as `-->||` are invalid. Write `A -->|success| B`, not `A -->success B` or `A --success--> B`.
7. Subgraph IDs are unique and do not collide with node IDs.
8. Every `subgraph` has a matching `end`.
9. Do not use semicolons.
10. Do not put blank lines inside the mermaid block.
11. Every defined node is connected; every node-table node appears in the diagram; every edge-table edge appears in the diagram.
12. Decisions show `true` and `false`; switches show every case and optional `default`; loops show the body and `continue`; parallel branches fork and converge at Merge.

## Node Selection Heuristics

- **External service:** curated `uipath.connector.<key>.<operation>` -> [connector](plugins/connector/planning.md); connector without activity -> `core.action.http.v2` connector mode; no connector but REST API -> `core.action.http.v2` manual mode; no API -> [rpa](plugins/rpa/planning.md) or `core.logic.mock` if unpublished.
- **Branch:** two paths -> [decision](plugins/decision/planning.md); three or more -> [switch](plugins/switch/planning.md); HTTP response-status branch -> [http](plugins/http/planning.md) built-in branches.
- **Transform:** map/filter/group-by -> [transform](plugins/transform/planning.md); custom computation or strings -> [script](plugins/script/planning.md).
- **End:** normal completion -> [end](plugins/end/planning.md); fatal abort -> [terminate](plugins/terminate/planning.md).
- **Wait:** duration or date -> [delay](plugins/delay/planning.md); external robot result -> [queue](plugins/queue/planning.md) `create-and-wait`.
- **Human:** approval or data entry -> [hitl](plugins/hitl/planning.md), or `core.logic.mock` if unavailable.
- **Agent:** tightly coupled low-code agent inside flow -> [inline-agent](plugins/inline-agent/planning.md), `uipath.agent.autonomous`; coded or separate in-solution/published agent -> [agent](plugins/agent/planning.md), `uipath.core.agent.{key}`.
- **LLM over CSV/document:** CSV row columns -> [batch-transform](plugins/batch-transform/planning.md), `uipath.pattern.batch-transform`; one-document synthesis/Q&A/citations -> [summarize](plugins/summarize/planning.md), `uipath.pattern.deep-rag`; multi-step tool reasoning -> inline or published agent; ordinary reshaping -> transform.
- **Document extraction:** variable-layout PDF, scan, photo, or attachment -> [ixp](plugins/ixp/planning.md), `uipath.ixp.{modelName}.{fullyQualifiedName}`; structured source -> script or transform; free-form reasoning -> agent; untrained IxP model -> `core.logic.mock` plus Open Question.
- **Missing capability:** use `core.logic.mock`; identify the needed artifact and owning skill (`uipath-rpa` for desktop/browser or coded C# workflows, `uipath-agents` for agents). Phase 2 replaces the mock if published.

## Handoff to Phase 2

After explicit user approval, [Planning Phase 2: Implementation](planning-impl.md) must:

1. Validate every node type with `uip maestro flow registry get`; read each plugin's `impl.md`.
2. Resolve connector and resource nodes using relevant `impl.md` files, including [connector](plugins/connector/impl.md) and [rpa](plugins/rpa/impl.md).
3. Confirm resources are published and obtain definitions.
4. Validate required fields against user values.
5. Replace `<PLACEHOLDER>` values with resolved IDs.
6. Replace `core.logic.mock` nodes with real resources when available.
7. Finalize implementation-ready details.

**Do not proceed to Phase 2 until the user explicitly approves the architectural plan.**