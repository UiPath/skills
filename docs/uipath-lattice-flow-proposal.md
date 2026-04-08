# Proposal: `uipath-lattice-flow` Skill

| Field | Value |
|---|---|
| **Status** | Draft v4 — CLI source analysis and replaceability assessment added |
| **Date** | 2026-04-07 |
| **Codename** | lattice (7 chars, matching "maestro") |

## Summary

A new skill that teaches coding agents to **read, create, edit, and validate `.flow` files as pure JSON** — no CLI dependency for OOTB flows. The agent manipulates the JSON structure directly using embedded node schemas and example templates.

The name "lattice" reflects the graph of interconnected nodes that a `.flow` file represents.

## Motivation

The existing `uipath-maestro-flow` skill relies heavily on CLI commands (`uip flow node add`, `uip flow registry get`, etc.) for every operation. This creates several friction points:

1. **Definitions blocker** — The `definitions` array must be copied from `registry get` output. This is the #1 source of errors and the #1 reason agents need the CLI.
2. **Registry dependency** — Even for OOTB nodes (which never change), the agent must hit the registry every time.
3. **Offline impossibility** — Without `uip login` and network access, agents cannot author flows at all.
4. **Round-trip overhead** — CLI calls add latency and context window cost for operations that are fundamentally JSON edits.

The 14 OOTB `.registration.json` files in `flow-workbench` contain everything an agent needs — port definitions, input schemas, defaults, BPMN model types. By embedding these as reference docs, the agent can construct valid nodes without the registry.

## Feasibility Analysis

| Capability | maestro-flow (CLI) | lattice-flow (direct JSON) | Feasible? |
|---|---|---|---|
| OOTB nodes (14 types) | `uip flow registry get` + `node add` | Schemas bundled as reference docs — zero CLI calls | Yes |
| Edge wiring | `uip flow edge add` | Agent writes JSON directly using port definitions from schemas | Yes |
| Variables | `uip flow variable add/list/delete` + `variable-update add/list/delete` | Agent writes JSON directly using schema docs | Yes |
| Validation | `uip flow validate` | Agent follows structural rules from schema docs; optional CLI as final check | Yes |
| Dynamic nodes (connectors, resources) | `uip flow registry search/get` + `node configure` | Still needs registry for discovery + schema pull — but JSON construction is direct | Partial |
| Project scaffolding | `uip flow init` | Agent creates the 2 project files directly | Yes |

**Key takeaway from CLI source analysis:** Of the 15 top-level `uip flow` CLI commands, **7 are fully replaceable** with direct JSON manipulation (init, edge, variable, variable-update, binding, plus node list/delete/configure), **3 are partially replaceable** (node add, validate, registry), and the rest are runtime/platform operations out of scope for authoring. The project scaffold is simpler than expected (2 files, not 6), and all ID generation, variable management, and validation algorithms are deterministic and documentable. This confirms the skill is viable.

**The remaining hard constraint:** Dynamic nodes (resources like RPA processes, agents, API workflows) still require `registry pull` + `registry get` to fetch their input/output schemas. Connectors are out of scope. The skill will document the registry interaction for dynamic nodes but cannot eliminate the network dependency for schema discovery.

**Long-term goal:** This skill is intended to **fully replace** `uipath-maestro-flow`. Once dynamic resource node support is complete, `uipath-maestro-flow` will be retired.

## Source Material

The following resources in `flow-workbench` provide the ground truth for this skill:

| Resource | Location | What It Provides |
|---|---|---|
| OOTB node schemas | `packages/registry/src/registry/ootb/*.registration.json` | Complete definition blocks, port configs, input schemas, defaults |
| Zod schema | `packages/flow-schema/src/workflow.ts` | Canonical `.flow` file validation schema |
| flow-core factory API | `packages/flow-core/src/index.ts` | Programmatic workflow construction functions |
| Reference `.flow` files | `coder_eval/tasks/uipath_flow/reference_flows/` | 8 production-quality reference flows (see catalog below) |
| Zod workflow schema | `packages/flow-schema/src/workflow.ts` | All entity types: nodes, edges, variables, bindings, subflows, metadata, connections |
| Node categories | `packages/registry/src/util/categories.ts` | Category IDs, names, sort orders |
| Dynamic node generation | `packages/registry/src/registry/uipath-v1/index.ts` | How platform APIs produce node definitions |
| Flow CLI source code | `cli/packages/flow-tool/src/` | Exact implementation of all `uip flow` commands — JSON manipulation logic, ID generation, validation rules |

## CLI Command Replaceability Analysis

Source: `cli/packages/flow-tool/src/` — the implementation of all `uip flow` commands.

### Summary

There are **15 top-level commands** registered in `tool.ts`. Each has subcommands (e.g., `node add/list/delete/configure`). The table below covers all top-level commands and their subcommands:

| Top-level Command | Subcommands | Replaceable? | Notes |
|---|---|---|---|
| `flow init` | — | **Yes** | Creates only 2 files: `project.uiproj` + `<name>.flow` |
| `flow node` | `add`, `list`, `delete`, `configure` | **Partially** | `list`/`delete`/`configure` are pure JSON. `add` needs manifest from registry cache for dynamic nodes; OOTB manifests are bundled. |
| `flow edge` | `add`, `list`, `delete` | **Yes** | JSON insert/read/filter with port validation |
| `flow variable` | `add`, `list`, `delete` | **Yes** | JSON manipulation of `variables.globals`. Validates ID, direction (`in`/`out`/`inout`), type (`string`/`number`/`boolean`/`object`/`array`/`file`), default value parsing. |
| `flow variable-update` | `add`, `list`, `delete` | **Yes** | JSON manipulation of `variables.variableUpdates`. Links a node completion to a variable assignment expression (`=js:` auto-prefixed). |
| `flow binding` | `add`, `list`, `delete` | **Yes** | JSON manipulation of `workflow.bindings` |
| `flow validate` | — | **Partially** | Structural checks replaceable; full semantic rules in compiled `@uipath/flow-schema` |
| `flow registry` | `pull`, `list`, `search`, `get` | **Partially** | `pull` requires network. `list`/`search` are local cache reads. `get` is local for OOTB/resource, needs IS API for connector enrichment. |
| `flow debug` | — | **No** | Uploads to Studio Web, runs remote debug session |
| `flow pack` | — | **No** | Complex nupkg packaging |
| `flow process` | (subcommands) | **No** | Orchestrator process operations |
| `flow job` | (subcommands) | **No** | Orchestrator job operations |
| `flow instances` | (subcommands) | **No** | Runtime instance operations |
| `flow processes` | (subcommands) | **No** | Runtime process operations |
| `flow incidents` | (subcommands) | **No** | Runtime incident operations |

**Replaceability summary:** Of the 15 top-level commands, **7 are fully replaceable** (init, edge, variable, variable-update, binding + node list/delete/configure), **2 are partially replaceable** (node add, validate, registry), **1 is not replaceable but not needed for authoring** (debug), and **5 are runtime/platform operations** out of scope (pack, process, job, instances, processes, incidents).

### Key Implementation Details

These details from the CLI source code must be documented in the skill's reference guides:

#### Project Scaffold (from `flow init`)

`flow init` creates only **2 files** (not 6 as previously assumed):

**`project.uiproj`:**
```json
{
  "Name": "<name>",
  "ProjectType": "Flow"
}
```

**`<name>.flow`:** A minimal workflow with one `core.trigger.manual` start node at position `{x:256, y:144}`, id `"start"`, empty edges/bindings, one definition entry for the trigger, and `metadata.createdAt`/`updatedAt` timestamps. The flow `id` and the trigger's `model.entryPointId` are both UUIDs.

> Other files (`entry-points.json`, `operate.json`, `package-descriptor.json`, `bindings_v2.json`) are generated at pack/deploy time, not at init.

#### Node ID Generation Algorithm

1. Take the display label (or `--label` override)
2. Split on non-alphanumeric characters
3. Join as camelCase (first word lowercase, rest capitalized)
4. Strip `"createNew"` prefix if present
5. Append numeric suffix starting at `1`, incrementing until unique among existing node IDs
6. Result: `sendMessage1`, `httpRequest1`, `decision2`, etc.

**Constraint:** IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/` and not be a JS/Python reserved word.

#### Edge ID Generation Algorithm

Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`

- Uses `"default"` if a port is null
- Appends `-2`, `-3`, etc. on collision

Example: `start-output-httpRequest1-input`

#### Binding ID Generation

Format: `b` + 8 random alphanumeric characters (e.g., `bXk9mNpQr`)

#### `variables.nodes` Auto-Regeneration (Critical)

**Every time a node is added or removed**, the CLI completely regenerates `workflow.variables.nodes` from scratch:

1. For each node in `workflow.nodes`:
   - Check if the node has `outputs` defined on the instance
   - If not, fall back to the matching definition's `outputDefinition`
   - For each output key, emit a `NodeVariable`:
     ```json
     {
       "id": "<nodeId>.<outputKey>",
       "type": "<outputType>",
       "binding": { "nodeId": "<nodeId>", "outputId": "<outputKey>" }
     }
     ```
2. Replace `workflow.variables.nodes` entirely with the regenerated array

**This means:** when an agent adds a node manually to JSON, they MUST also regenerate `variables.nodes`. The skill's validation checklist must include this step.

#### Definition Deduplication

- `workflow.definitions` is deduped by `nodeType:version` key
- When adding: skip if a definition with the same `nodeType` + `version` already exists
- When deleting a node: remove the definition only if no other node uses the same `type:typeVersion`

#### Variable Commands (from `flow variable`)

`flow variable add` creates a `WorkflowVariable` entry in `variables.globals`:
- Validates ID against `validateIdentifier()` (same rules as node IDs)
- Valid types: `string`, `number`, `boolean`, `object`, `array`, `file`
- Valid directions: `in`, `out`, `inout`
- Parses `--default-value` based on type (string passthrough, number via `parseFloat`, boolean strict `true`/`false`, object/array via `JSON.parse`)
- Optional `--schema` for object/array types (JSON Schema validation)
- Optional `--sub-type` for complex types

`flow variable delete` removes a variable from `variables.globals` by ID.
`flow variable list` returns all variables in `variables.globals`.

#### Variable Update Commands (from `flow variable-update`)

`flow variable-update add` creates a `VariableUpdate` entry in `variables.variableUpdates[nodeId]`:
- Required: `--node-id`, `--variable-id`, `--expression`
- Auto-prefixes expression with `=js:` if missing
- Links a node completion event to a variable assignment

`flow variable-update delete` removes by `nodeId` + `variableId` pair.
`flow variable-update list` returns all updates, optionally filtered by `--node-id`.

#### Binding Deduplication

- Deduped by `resourceKey` + `propertyAttribute` pair
- If a binding with the same key+attr exists, the new one is silently discarded

#### Process/Agent Node Bindings (from `node add`)

When adding a resource node (RPA workflow, agent, API workflow), the CLI:
1. Extracts the GUID from the trailing part of the nodeType
2. Creates two bindings: `name` and `folderPath`
3. Updates `model.context` entries to reference `=bindings.<bindingId>`

This is the mechanism that connects the node to its Orchestrator resource at runtime.

#### Validation Rules (from `flow validate`)

Structural checks the agent can replicate:
1. **Edge references** — all `sourceNodeId`/`targetNodeId` must exist in `workflow.nodes`
2. **Definition coverage** — every node's `type:typeVersion` must have a matching `definitions` entry (warning only)
3. **Unique IDs** — no duplicate node IDs or edge IDs
4. **Zod parse** — `.flow` file must pass the `workflowSchema` Zod validation

Full semantic validation (from compiled `@uipath/flow-schema` built-in rules) cannot be replicated — use `uip flow validate` as a final check when available.

## Reference Flows Catalog

Source: `/home/tmatup/root/coder_eval/tasks/uipath_flow/reference_flows/`

These 8 production-quality flows are the template source for this skill. Each contains a `metadata.yaml` and `reference.flow`.

| Flow | Nodes | Edges | OOTB Node Types | Dynamic Node Types | Complexity |
|---|---|---|---|---|---|
| **calculator-multiply** | 2 | 1 | manual-trigger, script | — | Simple |
| **dice-roller** | 2 | 1 | manual-trigger, script | — | Simple |
| **send-date-email** | 4 | 3 | manual-trigger, script, terminate | outlook-send-email | Simple |
| **sales-pipeline-cleanup** | 5 | 5 | manual-trigger, loop, end | salesforce-list, salesforce-delete | Simple |
| **devconnect-email** | 7 | 6 | manual-trigger, switch, script | outlook(x2), slack, agent | Medium |
| **release-notes-generator** | 10 | 11 | manual-trigger, transform, loop, filter, mock | jira, confluence, slack, agent(x2) | Complex |
| **sales-pipeline-hygiene** | 16 | 14 | manual-trigger, scheduled-trigger, loop, switch, end | salesforce(x3), slack(x2), agent | Complex |
| **hr-onboarding** | 23 | 24 | manual-trigger, decision(x2), merge, delay, terminate, end(x2), script, http, mock(x2) | outlook(x4), slack, process(x4), agent(x2), rpa-workflow | Very Complex |

### Template Selection

| Template to create | Source flow | Why |
|---|---|---|
| `minimal-flow-template.json` | dice-roller | Smallest valid flow (2 nodes, 1 edge) |
| `project-scaffold-template.json` | calculator-multiply | Has global input variables — good scaffold with inputs |
| `decision-flow-template.json` | devconnect-email | Switch/branching with multiple paths |
| `loop-flow-template.json` | sales-pipeline-cleanup | Cleanest loop pattern |
| `http-flow-template.json` | hr-onboarding (subset) | HTTP request node with downstream handling |
| `scheduled-trigger-template.json` | sales-pipeline-hygiene | Scheduled trigger pattern |
| `connector-flow-template.json` | send-date-email | Simplest script-to-connector pattern |
| `multi-agent-template.json` | release-notes-generator | Agent nodes with loop and data transforms |

## .flow Schema Entity Types

Source: `@uipath/flow-schema` (`packages/flow-schema/src/workflow.ts`)

The `flow-schema-guide.md` reference doc must document **all** entity types in the `.flow` file, not just nodes and edges. The full entity inventory:

### Top-Level: `Workflow`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` (identifier pattern) | Required | Unique workflow ID |
| `version` | `string` (semver) | Required | e.g., `"1.0.0"` |
| `name` | `string` (min 1 char) | Required | Human-readable name |
| `description` | `string` | Optional | |
| `runtime` | `'maestro' \| 'api-function'` | Optional | Defaults to `'maestro'` |
| `nodes` | `NodeInstance[]` | Required | All workflow nodes |
| `edges` | `EdgeInstance[]` | Required | All connections between nodes |
| `definitions` | `NodeManifest[]` | Required | Cached node definitions |
| `bindings` | `any[]` | Optional | UiPath artifact bindings |
| `variables` | `WorkflowVariables` | Optional | Workflow-level variables |
| `connection` | `WorkflowConnection` | Optional | Execution/debug connection config |
| `metadata` | `Metadata` | Optional | Authoring metadata |
| `subflows` | `Record<string, SubflowEntry>` | Optional | Keyed by parent node ID |

### `NodeInstance`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` | Required | Unique node identifier |
| `type` | `string` | Required | e.g., `'core.action.script'`, `'uipath.connector.*'` |
| `typeVersion` | `string` | Required | e.g., `'1.0.0'` |
| `display` | `{ label?, description? }` | Optional | Display overrides |
| `inputs` | `Record<string, unknown>` | Optional | Input field values |
| `outputs` | `Record<string, Record<string, unknown>>` | Optional | Output mappings (user-authored `source` expressions) |
| `model` | `object` | Optional | BPMN type, serviceType, bindings, context |
| `variableUpdates` | `Record<string, unknown>[]` | Optional | Variable assignment expressions |
| `parentId` | `string` | Optional | ID of parent loop node |
| `ui` | `{ position: {x, y}, size?: {width, height} }` | Optional | Canvas position/size |

### `EdgeInstance`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` | Required | Unique edge identifier |
| `sourceNodeId` | `string` | Required | Source node ID |
| `sourcePort` | `string` | Required | Handle ID on source node (defaults to `'default'`) |
| `targetNodeId` | `string` | Required | Target node ID |
| `targetPort` | `string` | Required | Handle ID on target node (defaults to `'default'`) |
| `data` | `Record<string, string>` | Optional | e.g., `{ label: '...' }` |

### `NodeManifest` (Definition entry)

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodeType` | `string` | Required | Must match a node's `type` field |
| `version` | `string` (min 1) | Required | |
| `category` | `string` | Optional | e.g., `'data-operations'`, `'control-flow'` |
| `display` | `{ label: string }` | Optional | |
| `handleConfiguration` | `Array<{ handles: HandleConfig[] }>` | Required | Port/handle definitions |
| `inputDefinition` | `Record<string, unknown>` | Optional | JSON Schema for inputs |
| `inputDefaults` | `Record<string, unknown>` | Optional | Default input values |
| `outputDefinition` | `Record<string, unknown>` | Optional | Output schemas |
| `tags` | `string[]` | Optional | |
| `sortOrder` | `number` | Optional | |
| `form` | `object` | Optional | Properties panel layout |
| `model` | `{ type, serviceType?, expansion?, ... }` | Optional | BPMN mapping and extensions |

### `HandleConfig` (Port definition within a manifest)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` | Required | Unique handle ID (e.g., `'input'`, `'success'`, `'true'`) |
| `type` | `'target' \| 'source'` | Required | |
| `handleType` | `string` | Required | |
| `label` | `string` | Optional | Supports templates: `{inputs.trueLabel \|\| 'True'}` |
| `repeat` | `string` | Optional | Dynamic handles: `"inputs.branches"` creates N handles |
| `constraints` | `ConnectionConstraint` | Optional | Connection validation rules |

### `ConnectionConstraint`

| Field | Type | Required | Notes |
|---|---|---|---|
| `minConnections` | `number` | Optional | |
| `maxConnections` | `number` | Optional | |
| `forbiddenSources` | `HandleTarget[]` | Optional | e.g., `[{ nodeType: "uipath.agent.resource.*" }]` |
| `forbiddenTargets` | `HandleTarget[]` | Optional | |
| `forbiddenTargetCategories` | `string[]` | Optional | |
| `allowedTargetCategories` | `string[]` | Optional | |
| `customValidation` | `string` | Optional | Template expression evaluating to boolean |
| `validationMessage` | `string` | Optional | |

### `WorkflowVariables`

| Field | Type | Required | Notes |
|---|---|---|---|
| `globals` | `WorkflowVariable[]` | Optional | Workflow-level inputs/outputs |
| `nodes` | `NodeVariable[]` | Optional | Node output capture variables |
| `variableUpdates` | `Record<string, VariableUpdate[]>` | Optional | Per-node assignments, keyed by nodeId |

### `WorkflowVariable` (Global variable)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` (min 1) | Required | Used in expressions as `$vars.{id}` |
| `direction` | `'in' \| 'out' \| 'inout'` | Required | `in`=external input, `out`=workflow output, `inout`=mutable state |
| `type` | `string` | Required | Default: `'string'`. Also: `'number'`, `'object'`, `'array'` |
| `subType` | `string` | Optional | Array item type |
| `schema` | `Record<string, unknown>` | Optional | JSON Schema for complex types |
| `defaultValue` | `unknown` | Optional | Only for `direction='in'` |
| `description` | `string` | Optional | |
| `triggerNodeId` | `string` | Optional | Root workflow `direction='in'` only |

### `NodeVariable` (Node output variable)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` (min 1) | Required | Used in expressions as `$vars.{id}` |
| `type` | `string` | Required | Default: `'string'` |
| `subType` | `string` | Optional | |
| `schema` | `Record<string, unknown>` | Optional | |
| `description` | `string` | Optional | |
| `binding` | `ArgumentBinding` | Required | Which node output provides the value |

### `ArgumentBinding`

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodeId` | `string` | Required | Source node ID |
| `outputId` | `string` | Required | Output port ID on the source node |

### `VariableUpdate`

| Field | Type | Required | Notes |
|---|---|---|---|
| `variableId` | `string` | Required | Target `WorkflowVariable` ID |
| `expression` | `string` | Required | e.g., `"=js:$vars.counter + 1"` |

### `SubflowEntry`

| Field | Type | Required | Notes |
|---|---|---|---|
| `nodes` | `NodeInstance[]` | Required | Child nodes |
| `edges` | `EdgeInstance[]` | Required | Edges between child nodes |
| `variables` | `WorkflowVariables` | Optional | Subflow-scoped variables |

### `WorkflowConnection`

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `'cloud' \| 'local'` | Required | |
| `environment` | `'cloud' \| 'staging' \| 'alpha'` | Optional | Cloud only |
| `organizationId` | `string` | Optional | Cloud only |
| `tenantId` | `string` | Optional | Cloud only |
| `tenantName` | `string` | Optional | Cloud only |
| `localUrl` | `string` (URL) | Optional | Local only |

### `Metadata`

| Field | Type | Required | Notes |
|---|---|---|---|
| `createdAt` | `string` (ISO 8601) | Required | |
| `updatedAt` | `string` (ISO 8601) | Required | |
| `author` | `string` | Optional | |
| `tags` | `string[]` | Optional | |
| `description` | `string` | Optional | |

### Key Constants and Validation Rules

| Constant | Value | Usage |
|---|---|---|
| `VALID_IDENTIFIER_PATTERN` | `/^[a-zA-Z_][a-zA-Z0-9_]*$/` | Node/variable IDs |
| `RESERVED_WORDS` | JS/Python reserved words | Blocked from use as IDs |
| `BINDINGS_PATH_PREFIX` | `'=bindings.'` | Prefix for binding expressions |
| Expression prefix | `=js:` | Required for all Jint expressions |
| Template syntax | `{{...}}` | Mustache-style in handle labels |

## Proposed Skill Structure

```
skills/uipath-lattice-flow/
├── SKILL.md                              # Skill definition
├── references/
│   ├── flow-schema-guide.md              # Full .flow JSON schema — all entity types documented above
│   ├── project-scaffolding-guide.md      # How to create the 6 project files from scratch
│   ├── edge-wiring-guide.md              # Edge rules, port mappings, standard ports by node type
│   ├── variables-guide.md                # Variables, expressions, output mapping, scoping
│   ├── subflow-guide.md                  # Subflow structure, isolated scope, input/output passing
│   ├── dynamic-nodes/                    # Phase 2: Dynamic resource node guides
│   │   ├── resource-node-guide.md        #   Shared structure, model object, static vs registry fields
│   │   ├── rpa-workflow-guide.md         #   RPA workflow specifics + examples from reference flows
│   │   ├── agent-guide.md                #   Agent specifics + examples from reference flows
│   │   ├── api-workflow-guide.md         #   API workflow specifics + construction pattern
│   │   └── agentic-process-guide.md     #   Agentic process specifics + construction pattern
│   ├── bindings-guide.md                 # bindings_v2.json format (empty for resource-only flows)
│   ├── validation-checklist.md           # Structural validation rules (manual pre-flight)
│   └── nodes/                            # One file per OOTB node type
│       ├── trigger-manual.md             # core.trigger.manual
│       ├── trigger-scheduled.md          # core.trigger.scheduled
│       ├── action-script.md              # core.action.script
│       ├── action-http.md                # core.action.http
│       ├── action-hitl.md                # core.action.hitl
│       ├── logic-decision.md             # core.logic.decision
│       ├── logic-switch.md               # core.logic.switch
│       ├── logic-loop.md                 # core.logic.loop
│       ├── logic-while.md                # core.logic.while
│       ├── logic-foreach.md              # core.logic.foreach
│       ├── logic-merge.md                # core.logic.merge
│       ├── logic-mock.md                 # core.logic.mock (placeholder)
│       ├── action-blank.md               # core.action.blank
│       ├── control-end.md                # core.event.end
│       └── control-terminate.md          # core.event.terminate
├── assets/
│   └── templates/
│       ├── minimal-flow-template.json    # Smallest valid flow (dice-roller: 2 nodes, 1 edge)
│       ├── project-scaffold-template.json # Project with input variables (calculator-multiply)
│       ├── decision-flow-template.json   # Switch/branching pattern (devconnect-email subset)
│       ├── loop-flow-template.json       # Loop pattern (sales-pipeline-cleanup subset)
│       ├── http-flow-template.json       # HTTP request with handling (hr-onboarding subset)
│       ├── scheduled-trigger-template.json # Scheduled trigger (sales-pipeline-hygiene subset)
│       ├── connector-flow-template.json  # Script-to-connector pattern (send-date-email)
│       └── multi-agent-template.json     # Agent nodes with loop + transforms (release-notes-generator subset)
```

### File Descriptions

#### SKILL.md

The skill definition with frontmatter, critical rules, and two workflows (new flow, edit existing flow). See the [SKILL.md Draft](#skillmd-draft) section below.

#### Reference Docs

| File | Purpose | Source Material |
|---|---|---|
| `flow-schema-guide.md` | Complete `.flow` JSON schema — all entity types (Workflow, NodeInstance, EdgeInstance, NodeManifest, HandleConfig, ConnectionConstraint, WorkflowVariables, WorkflowVariable, NodeVariable, ArgumentBinding, VariableUpdate, SubflowEntry, WorkflowConnection, Metadata), validation rules, constants, expression syntax | `@uipath/flow-schema` Zod schemas (see entity inventory above) |
| `project-scaffolding-guide.md` | How to create a valid project directory (`.flow` + `project.uiproj` — only 2 files needed). ID generation algorithms for nodes, edges, and bindings. `variables.nodes` regeneration rules. | `flow init` source code (`cli/packages/flow-tool/src/commands/init.ts`) |
| `edge-wiring-guide.md` | Standard ports by node type, edge JSON format, connection rules, constraint validation | `handleConfiguration` from `.registration.json` files |
| `variables-guide.md` | Variable declaration (in/out/inout), type system, `=js:` expressions, output mapping on End nodes, `variableUpdates` | `@uipath/flow-schema` variable schemas + maestro-flow's existing `variables-and-expressions.md` |
| `subflow-guide.md` | Subflow JSON structure, isolated scope, input/output passing, Start/End node requirements | Example subflow `.flow` files from test-data |
| `dynamic-nodes/resource-node-guide.md` | Shared structure for all resource nodes — `model` object template, handle config, static vs registry fields, registry CLI commands | flow-core `resource-type-metadata.ts`, `node-manifest-builder.ts` |
| `dynamic-nodes/rpa-workflow-guide.md` | RPA-specific: serviceType, category, icon, construction from registry output, full example from hr-onboarding | hr-onboarding reference flow |
| `dynamic-nodes/agent-guide.md` | Agent-specific: serviceType, category, icon, construction pattern, examples from devconnect-email and release-notes-generator | Reference flows + flow-core |
| `dynamic-nodes/api-workflow-guide.md` | API workflow-specific: serviceType, category, construction pattern | flow-core `orchestrator.ts` |
| `dynamic-nodes/agentic-process-guide.md` | Agentic process-specific: serviceType (`Orchestrator.StartAgenticProcess`), category, construction pattern | flow-core `resource-type-metadata.ts` |
| `bindings-guide.md` | `bindings_v2.json` format — empty for resource-only flows, populated only for connector nodes (out of scope) | IS activity guide from maestro-flow |
| `validation-checklist.md` | Numbered checklist of structural rules: edge references exist, definition coverage, unique IDs, `variables.nodes` regenerated, `targetPort` present on all edges. Full semantic validation still needs `uip flow validate`. | `flow-validate-service.ts` source + Zod schema constraints |

#### Node Reference Docs (14 files)

Each node doc follows a consistent structure:

```markdown
# <Node Display Name>

**Type:** `core.action.script`
**Category:** data-operations
**BPMN Model:** `bpmn:ScriptTask`

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Single incoming connection |
| right | `success` | source | Output after execution |

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `script` | string | Yes | `""` | JavaScript body (must `return { key: value }`) |

## Definition Block

Copy this verbatim into the `definitions` array:

```json
{ ... exact content from .registration.json ... }
```

## Node Instance Example

```json
{
  "id": "myScript",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  ...
}
```

## Common Mistakes
- Returning a scalar instead of an object from the script
- ...
```

#### Templates (8 files)

Sourced from the 8 reference flows in `coder_eval/tasks/uipath_flow/reference_flows/`, distilled to minimal working examples with dynamic nodes stripped to OOTB-only where possible.

| Template | Source Flow | Nodes | Pattern |
|---|---|---|---|
| `minimal-flow-template.json` | dice-roller | 2 | Start -> Script (smallest valid flow) |
| `project-scaffold-template.json` | calculator-multiply | 2 | Start -> Script with global input variables |
| `decision-flow-template.json` | devconnect-email | ~5 | Switch/branching with multiple paths |
| `loop-flow-template.json` | sales-pipeline-cleanup | ~4 | Loop iteration pattern |
| `http-flow-template.json` | hr-onboarding subset | ~4 | HTTP request with response handling |
| `scheduled-trigger-template.json` | sales-pipeline-hygiene | ~3 | Scheduled trigger + basic flow |
| `connector-flow-template.json` | send-date-email | ~3 | Script output feeding a connector |
| `multi-agent-template.json` | release-notes-generator subset | ~5 | Agent nodes with loop + data transforms |

## SKILL.md Draft

```yaml
---
name: uipath-lattice-flow
description: "[PREVIEW] Direct .flow JSON authoring — create, edit, validate UiPath Flow projects (.flow files). OOTB node schemas bundled. For XAML or C# workflows→uipath-rpa."
---
```

```markdown
# Direct Flow Authoring

Build and edit UiPath Flow projects by writing .flow JSON directly. OOTB node schemas are bundled — no CLI or registry calls needed for standard flows.

## When to Use This Skill

- Creating or editing .flow files as JSON
- Working offline or without the uip CLI installed
- Building flows using OOTB nodes (triggers, scripts, HTTP, decisions, loops, etc.)
- Rapid prototyping of flow structures
- Understanding the .flow file format in detail

## Critical Rules

1. **Always start from a template** — never construct .flow JSON from memory. Pick the closest template from `assets/templates/` and modify it.
2. **Copy definition blocks verbatim** from the node reference docs in `references/nodes/`. Never hand-write or modify definition entries.
3. **Every edge must have `targetPort`** — validation rejects edges without it. Check the target node's port table.
4. **Every `out` variable must be mapped on every reachable End node** — missing output mappings cause silent runtime failures.
5. **For dynamic nodes (connectors, resources), use the registry** — read `references/dynamic-nodes-guide.md`. OOTB schemas do not cover tenant-specific nodes.
6. **Run the validation checklist after every edit** — walk through `references/validation-checklist.md` before declaring the flow complete.
7. **Use `=js:` prefix for all expressions** — the runtime uses a Jint-based JavaScript engine (ES2020 subset).
8. **Script nodes must `return` an object** — `return { key: value }`, not a bare scalar.
9. **Do not edit generated files** — only edit `<ProjectName>.flow` and `bindings_v2.json`. Other project files (`entry-points.json`, `operate.json`, `package-descriptor.json`) are managed by the CLI.
10. **Node and edge IDs must be unique** within the flow. Use descriptive, kebab-case IDs.

## Workflow: New Flow

1. **Scaffold the project** — Read `references/project-scaffolding-guide.md` and create the project directory structure.
2. **Pick a template** — Choose the closest template from `assets/templates/` and copy it as `<ProjectName>.flow`.
3. **Plan your nodes** — Identify which node types you need. Read the reference doc for each in `references/nodes/`.
4. **Add nodes** — For each node, copy the definition block into `definitions` and add the node instance to `nodes`.
5. **Wire edges** — Connect nodes using the port IDs from each node's reference doc.
6. **Add variables** — Declare inputs/outputs in `variables.globals`. Map outputs on End nodes.
7. **Validate** — Walk through `references/validation-checklist.md`.
8. **(Optional) CLI validation** — If `uip` is available, run `uip flow validate <file> --output json` for a final check.

## Workflow: Edit Existing Flow

1. **Read the .flow file** — understand the current structure.
2. **Read the relevant node reference doc** — check ports, inputs, and definition format.
3. **Make the JSON edit** — add/modify/remove nodes, edges, or variables.
4. **Validate** — walk through `references/validation-checklist.md`.

## Reference Navigation

| I need to... | Read this |
|---|---|
| Understand the .flow JSON format | [references/flow-schema-guide.md](references/flow-schema-guide.md) |
| Create a new project from scratch | [references/project-scaffolding-guide.md](references/project-scaffolding-guide.md) |
| Wire nodes together | [references/edge-wiring-guide.md](references/edge-wiring-guide.md) |
| Add variables and expressions | [references/variables-guide.md](references/variables-guide.md) |
| Create a subflow | [references/subflow-guide.md](references/subflow-guide.md) |
| Use RPA workflow, agent, or API workflow nodes | [references/dynamic-nodes/](references/dynamic-nodes/) — resource node guides |
| Understand bindings_v2.json | [references/bindings-guide.md](references/bindings-guide.md) |
| Validate my flow | [references/validation-checklist.md](references/validation-checklist.md) |
| Look up a specific node type | [references/nodes/](references/nodes/) — one file per OOTB node |

## Anti-Patterns

- **Never guess a definition block** — always copy from the node reference doc (OOTB) or registry output (dynamic). Guessed definitions have wrong port schemas and cause validation failures.
- **Never skip the validation checklist** — common errors (missing targetPort, duplicate IDs, orphaned edges) are easy to miss in raw JSON.
- **Never construct dynamic resource nodes without the registry** — RPA workflow, agent, and API workflow nodes need registry data for inputDefinition and outputDefinition. Use `references/dynamic-nodes/`.
- **Never use `console.log` in script nodes** — `console` is not available in the Jint runtime. Use `return { debug: value }` to inspect values.
- **Never reference parent-scope `$vars` inside a subflow** — subflows have isolated scope. Pass values explicitly via subflow inputs.
```

## Key Differences from maestro-flow

| Aspect | maestro-flow (being replaced) | lattice-flow (replacement) |
|---|---|---|
| Primary approach | CLI commands (`uip flow node add`, etc.) | Direct JSON manipulation |
| Node schemas | Fetched from registry at runtime | Bundled as reference docs (OOTB); registry for dynamic |
| Definitions array | Must `registry get` every time | Pre-baked in node reference docs |
| Planning model | 2-phase (architectural -> implementation) | Template-first (pick template -> customize) |
| Dynamic nodes | Full CLI workflow | Registry guide included (deferred priority) |
| Offline capable | No (needs registry + auth) | Yes, for OOTB flows |
| Validation | `uip flow validate` (required) | Structural checklist + optional CLI validation |
| Schema documentation | Minimal (nodes/edges only) | Full entity coverage (all Zod schema types) |

## Replacement Strategy

`uipath-lattice-flow` is intended to **fully replace** `uipath-maestro-flow`.

### Phase 1: OOTB Nodes (initial release)

Ship with full support for the 14 OOTB node types. All schemas bundled, templates from reference flows, full entity documentation. Both skills coexist briefly during transition.

### Phase 2: Dynamic Resource Nodes

Add support for dynamic resource nodes in this order:

1. **RPA Workflow** (`uipath.core.rpa-workflow.*`) — most common resource type in reference flows
2. **Agent** (`uipath.core.agent.*`) — used in 4 of 8 reference flows
3. **API Workflow** (`uipath.core.api-workflow.*`) — same pattern as RPA, different serviceType
4. **Agentic Process** (`uipath.core.agentic-process.*`) — same pattern, `Orchestrator.StartAgenticProcess`

At this point, maestro-flow is retired and its `description` is updated to redirect: `"Retired→uipath-lattice-flow"`.

### Phase 3: Cleanup

Remove `uipath-maestro-flow` from the repo. Update `uipath-planner` routing table.

> **Connectors** (`uipath.connector.*`) are out of scope for this proposal. They have a fundamentally different architecture (IS connections, enriched metadata, reference field resolution) and can be addressed in a future phase.

## Dynamic Resource Nodes — Architecture

Dynamic resource nodes (RPA Workflow, Agent, API Workflow) share a common structure. Understanding this is critical for Phase 2.

### Shared Structure

All three types share identical `handleConfiguration`, `supportsErrorHandling`, and `debug` fields. They differ only in `model.serviceType`, `model.bindings.resourceSubType`, `model.bindings.orchestratorType`, `display.icon`, and `category`:

| Field | RPA Workflow | Agent | API Workflow | Agentic Process |
|---|---|---|---|---|
| `model.serviceType` | `Orchestrator.StartJob` | `Orchestrator.StartAgentJob` | `Orchestrator.ExecuteApiWorkflowAsync` | `Orchestrator.StartAgenticProcess` |
| `model.bindings.resourceSubType` | `Process` | `Agent` | `Api` | `ProcessOrchestration` |
| `model.bindings.orchestratorType` | `process` | `agent` | `api` | `agentic-process` |
| `model.bindings.resource` | `process` | `process` | `process` | `process` |
| `category` | `rpa-workflow` | `agent` | `api-workflow` | `agentic-process` |
| `display.icon` | `rpa` | `autonomous-agent` | `api` | `agentic-process` |
| Node type pattern | `uipath.core.rpa-workflow.{entityKey}` | `uipath.core.agent.{entityKey}` | `uipath.core.api-workflow.{entityKey}` | `uipath.core.agentic-process.{entityKey}` |

The `{entityKey}` is the Orchestrator Release Key GUID (lowercased, non-alphanumeric chars replaced with `-`).

### `model` Object — Complete Shape

```json
{
  "type": "bpmn:ServiceTask",
  "serviceType": "<see table above>",
  "version": "v2",
  "bindings": {
    "resource": "process",
    "resourceSubType": "<Process|Agent|Api>",
    "resourceKey": "<orchestrator-release-key-guid>",
    "orchestratorType": "<process|agent|api>",
    "values": {
      "name": "<ProcessName>",
      "folderPath": "<FolderPath>"
    }
  },
  "projectId": "<optional-orchestrator-project-guid>",
  "context": [
    { "name": "name", "type": "string", "value": "=bindings.bXXXXX", "default": "<ProcessName>" },
    { "name": "folderPath", "type": "string", "value": "=bindings.bYYYYY", "default": "<FolderPath>" },
    { "name": "_label", "type": "string", "value": "<ProcessName>" }
  ]
}
```

### Handle Configuration (Same for All Resource Types)

```json
"handleConfiguration": [
  { "position": "left", "handles": [
    { "id": "input", "type": "target", "handleType": "input" }
  ]},
  { "position": "right", "handles": [
    { "id": "output", "type": "source", "handleType": "output" },
    { "id": "error", "label": "Error", "type": "source", "handleType": "output",
      "visible": "{inputs.errorHandlingEnabled}", "constraints": { "maxConnections": 1 } }
  ]}
]
```

### Inputs and Outputs

Inputs and outputs are **resource-specific** — they come from the Orchestrator process's argument definitions. This is why the registry is still required: the agent cannot know what arguments a published RPA workflow accepts without querying the platform.

**Node instance `inputs`** — keyed by argument name:
```json
"inputs": {
  "in_SenderEmailID": "{{ $vars.manualTrigger1.output.prehireemail }}",
  "in_WaitDurationInSeconds": 180
}
```

**Definition `inputDefinition`** — JSON Schema for arguments:
```json
"inputDefinition": {
  "type": "object",
  "properties": {
    "in_SenderEmailID": { "type": "string" },
    "in_WaitDurationInSeconds": { "type": "number" }
  }
}
```

**Definition `outputDefinition`** — output variable schemas:
```json
"outputDefinition": {
  "out_EmailContent": { "type": "string", "source": "=out_EmailContent", "var": "out_EmailContent" },
  "error": { "type": "object", "source": "=Error", "var": "error", "schema": { ... } }
}
```

### What's Static vs What Needs the Registry

| Information | Static? | Notes |
|---|---|---|
| `handleConfiguration` | Yes | Same for all resource types |
| `model.serviceType` | Yes | Derived from resource type (see table) |
| `model.bindings` structure | Yes | Template is fixed; values come from registry |
| `display.icon`, `iconBackground` | Yes | Fixed per resource type |
| `supportsErrorHandling` | Yes | Always `true` |
| `debug.runtime` | Yes | Always `"bpmnEngine"` |
| `resourceKey` (GUID) | **No** | Must query registry/orchestrator |
| Process name, folder path | **No** | Must query registry |
| `inputDefinition` (argument types) | **No** | Must query orchestrator for each process |
| `outputDefinition` (return types) | **No** | Must query orchestrator |
| `form` (properties panel) | **No** | Derived from inputDefinition |

### What the Skill Will Provide for Dynamic Nodes

1. **Base template reference doc** — the static parts of a resource node definition, parameterized by resource type. Agent fills in the blanks from registry output.
2. **Registry interaction guide** — exact CLI commands to discover resources and fetch their schemas:
   ```bash
   uip flow registry pull --force
   uip flow registry search "<name>" --output json
   uip flow registry get "uipath.core.rpa-workflow.<key>" --output json
   ```
3. **Step-by-step construction guide** — how to take registry output and construct the node instance + definition entry in the `.flow` file.
4. **No `bindings_v2.json` needed** — resource nodes resolve via `model.bindings`, not `bindings_v2.json`. The bindings file only applies to connector nodes (out of scope).

### Proposed Reference Docs for Phase 2

```
references/
├── dynamic-nodes/
│   ├── resource-node-guide.md        # Shared structure, model object, static fields
│   ├── rpa-workflow-guide.md         # RPA-specific: serviceType, category, examples from hr-onboarding
│   ├── agent-guide.md                # Agent-specific: serviceType, category, examples from devconnect/release-notes
│   ├── api-workflow-guide.md         # API-specific: serviceType, category, construction pattern
│   └── agentic-process-guide.md     # Agentic process-specific: serviceType, category, construction pattern
```

## Example Prompts (Same Results, Different Approach)

These prompts would activate `uipath-lattice-flow` and produce the same `.flow` file content as `uipath-maestro-flow`:

**Creating flows:**
- "Create a new UiPath Flow that sends a Slack message when an email arrives" (OOTB nodes only -> lattice; if Slack connector needed -> hands off to maestro)
- "Build a .flow project that runs a script and branches based on the result"
- "Initialize a Flow project with a scheduled trigger that runs every hour"

**Editing flows:**
- "Add a decision branch after the HTTP node in my .flow file"
- "Add a script node that transforms the API response"
- "Wire a new node between the filter and the end node"

**Operations:**
- "Validate my .flow file"
- "Show me the schema for a decision node"
- "What ports does the HTTP Request node have?"

## Build Plan

### Phase 1: OOTB Nodes

#### 1a. Foundation (SKILL.md + schema + scaffolding + validation)
1. Write `SKILL.md` with frontmatter and workflows
2. Write `flow-schema-guide.md` — all entity types from `@uipath/flow-schema`
3. Write `project-scaffolding-guide.md` from `uip flow init` output analysis
4. Write `validation-checklist.md` from `uip flow validate` error categories + Zod constraints
5. Create `minimal-flow-template.json` and `project-scaffold-template.json` from reference flows

#### 1b. Node references (14 OOTB node docs)
6. Convert each `.registration.json` into an agent-readable markdown doc
7. Extract definition blocks, port tables, input schemas, examples
8. Create `edge-wiring-guide.md` summarizing all ports across all nodes

#### 1c. Variables, subflows, remaining templates
9. Write `variables-guide.md` (reuse content from maestro-flow + Zod schema)
10. Write `subflow-guide.md` from reference flow examples
11. Create remaining 6 templates from reference flows
12. Write `bindings-guide.md` (minimal — `bindings_v2.json` is empty for OOTB-only flows)

#### 1d. Integration
13. Update CODEOWNERS
14. Update README.md skill catalog

### Phase 2: Dynamic Resource Nodes

#### 2a. RPA Workflow support
15. Write `references/dynamic-nodes/resource-node-guide.md` — shared structure, static vs registry fields
16. Write `references/dynamic-nodes/rpa-workflow-guide.md` — RPA-specific fields, examples from hr-onboarding reference flow
17. Update SKILL.md critical rules and workflows for resource nodes

#### 2b. Agent support
18. Write `references/dynamic-nodes/agent-guide.md` — agent-specific fields, examples from devconnect-email and release-notes-generator reference flows

#### 2c. API Workflow support
19. Write `references/dynamic-nodes/api-workflow-guide.md` — API-specific fields, construction pattern

#### 2d. Agentic Process support
20. Write `references/dynamic-nodes/agentic-process-guide.md` — agentic-process-specific fields, construction pattern

#### 2e. Retire maestro-flow
21. Update `uipath-maestro-flow` description to redirect: `"Retired→uipath-lattice-flow"`
22. Update `uipath-planner` routing table

### Phase 3: Cleanup
23. Remove `uipath-maestro-flow` from the repo

## Verification Strategy

How to verify the skill produces correct `.flow` files and is effective for coding agents.

### Method 1: Reference Flow Reproduction (Primary)

Give the agent a natural-language prompt for each of the 8 reference flows. The agent uses the new skill to build the `.flow` file from scratch. Compare the output against the reference `.flow` file.

**Test prompts by reference flow:**

| # | Reference Flow | Test Prompt | Phase |
|---|---|---|---|
| 1 | **dice-roller** | "Create a Flow project that simulates rolling a 6-sided die using JavaScript and returns the result." | Phase 1 (OOTB only) |
| 2 | **calculator-multiply** | "Create a Flow project that takes two number inputs `a` and `b`, multiplies them, and returns the result." | Phase 1 (OOTB only) |
| 3 | **send-date-email** | "Create a Flow that gets the current date/time via a script node, then sends it in an email via Outlook." | Phase 2 (connector) |
| 4 | **sales-pipeline-cleanup** | "Create a Flow that fetches all task records from Salesforce and deletes each one in a loop." | Phase 2 (connector) |
| 5 | **devconnect-email** | "Create a Flow that reads the newest Outlook email, uses an AI agent to classify it (needs response / take action / other), sends a Slack DM if it needs attention, and tags the email in Outlook." | Phase 2 (agent + connector) |
| 6 | **release-notes-generator** | "Create a Flow that searches Jira for recently closed issues, uses an AI agent to filter which ones need release notes, generates release notes with a second agent, publishes to a Confluence page, and sends a Slack notification." | Phase 2 (agent + connector) |
| 7 | **sales-pipeline-hygiene** | "Create a Flow with a weekly scheduled trigger that scans open Salesforce opportunities, uses an AI agent to score risk per opportunity, escalates high-risk deals to a Slack channel with a follow-up task, DMs medium-risk deal owners, and writes risk levels back to Salesforce." | Phase 2 (agent + connector) |
| 8 | **hr-onboarding** | "Create an end-to-end HR onboarding Flow: send a job offer email, wait for reply, use an agent to decide acceptance, run document validation and background check (mock if not available), create a pre-hire record, in parallel create a Coupa purchase requisition + Jira IT ticket + Slack notification, get training recommendations from an agent, route through human-in-the-loop review, and schedule a calendar event." | Phase 2 (full) |

**Phase 1 can verify prompts 1-2 immediately.** Prompts 3-8 require Phase 2 (dynamic nodes). Each prompt should be run independently in a fresh session.

### Method 2: Structural Diff

Automated comparison of generated `.flow` vs reference `.flow`, ignoring non-deterministic fields:

**Fields to ignore in comparison:**
- `id` (workflow UUID) — generated fresh each time
- `nodes[*].id` — ID generation produces equivalent but not identical IDs
- `edges[*].id` — derived from node IDs
- `nodes[*].ui.position` — layout is non-deterministic
- `nodes[*].ui.size` — may vary
- `metadata.createdAt` / `metadata.updatedAt` — timestamps
- `model.entryPointId` — UUID generated at init
- `model.projectId` — Orchestrator project GUID (dynamic nodes)
- `model.context[*].value` — binding IDs are random (`bXk9mNpQr`)
- `bindings[*].id` — random binding IDs

**Fields that MUST match:**
- `nodes[*].type` and `nodes[*].typeVersion` — exact node types
- `edges[*].sourceNodeId`, `sourcePort`, `targetNodeId`, `targetPort` — topology
- `nodes[*].inputs` — input values and expressions
- `nodes[*].outputs` — output mappings
- `definitions[*].nodeType` — definition coverage
- `variables.globals` — variable declarations (id, direction, type)
- `variables.variableUpdates` — update expressions
- Node count and edge count

A comparison script could normalize both files (strip ignored fields, sort arrays by type/id) and diff the result.

### Method 3: Validation Pass Rate

For each generated `.flow` file, run `uip flow validate` and track:

| Metric | Target |
|---|---|
| Passes `uip flow validate` on first attempt | 100% for OOTB flows |
| Passes with ≤1 manual fix | 100% for all flows |
| Correct node count | 100% |
| Correct edge count (topology matches) | 100% |
| All definitions present | 100% |
| All `variables.nodes` entries generated | 100% |

### Method 4: Edit Verification

Start from a reference flow and ask the agent to make targeted edits. Verify the edit is structurally correct.

**Example edit prompts:**
- "Add a decision node after the script node in dice-roller that checks if the roll is greater than 3"
- "Add an `out` variable called `result` to calculator-multiply and map it on the End node"
- "Remove the Slack notification node from devconnect-email and rewire the edges"
- "Add a delay node of 30 seconds between the HTTP request and the decision in hr-onboarding"
- "Convert the manual trigger in sales-pipeline-hygiene to a scheduled trigger running every 2 hours"

Each edit should pass `uip flow validate` and produce the expected structural change when diffed against the original.

### Method 5: Round-Trip Test

1. Agent reads a reference `.flow` file and produces a natural-language description
2. A second agent session receives only the description (not the file) and builds the flow from scratch
3. Compare the output against the original reference

This tests whether the skill's documentation is sufficient for an agent to reconstruct a flow from a specification alone, without seeing the JSON.

### Verification Timeline

| Phase | Methods | Reference Flows Testable |
|---|---|---|
| Phase 1 complete | Methods 1-5 | dice-roller, calculator-multiply (OOTB only) |
| Phase 2a (RPA) | Methods 1-5 | + hr-onboarding (RPA nodes) |
| Phase 2b (Agent) | Methods 1-5 | + devconnect-email, release-notes-generator, sales-pipeline-hygiene |
| Phase 2c-d (API/Agentic) | Methods 1-5 | All 8 reference flows (connector nodes may need stubs) |

## Resolved Questions

1. **Scope of dynamic nodes** — RPA workflow, Agent, and API workflow nodes are in scope (Phase 2), in that priority order. Connectors are **out of scope** for this proposal.
2. **Template source** — Using the 8 reference flows from `coder_eval/tasks/uipath_flow/reference_flows/` (not the 23 test files from flow-workbench).
3. **Long-term direction** — Lattice-flow will **fully replace** maestro-flow. Three-phase replacement strategy defined above.
4. **Schema coverage** — `flow-schema-guide.md` will document **all** entity types from `@uipath/flow-schema` (Workflow, NodeInstance, EdgeInstance, NodeManifest, HandleConfig, ConnectionConstraint, WorkflowVariables, WorkflowVariable, NodeVariable, ArgumentBinding, VariableUpdate, SubflowEntry, WorkflowConnection, Metadata), not just nodes and edges.
5. **Dynamic node phasing** — RPA Workflow first (most common), then Agent (used in 4/8 reference flows), then API Workflow (same pattern, different serviceType). All share a common base structure documented in `resource-node-guide.md`.

## Resolved Open Questions

1. **`blank-node` (`core.action.blank`)** — Include in node docs (15 OOTB nodes total instead of 14).
2. **`stickyNote`** — Document as a non-functional annotation element in `flow-schema-guide.md`, not as a node reference doc.
3. **Agent nodes (`uipath.agent.autonomous`, `uipath.agent.conversational`)** — Treat as dynamic. They require login and are covered in Phase 2 under the agent guide.
4. **Agentic Process (`uipath.core.agentic-process.*`)** — Include in Phase 2 alongside RPA/Agent/API.
