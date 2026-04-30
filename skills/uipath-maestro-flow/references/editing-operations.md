# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Two implementation strategies are available — choose one per operation and follow the corresponding guide.

## Default Strategy

> **Default to Direct JSON for all `.flow` edits.** Use CLI only when the user explicitly requests CLI, or for connector, connector-trigger, or inline-agent nodes (see carve-out rows in the matrix below).

| Strategy | Guide | When to use |
|----------|-------|-------------|
| **Direct JSON** (default) | [editing-operations-json.md](editing-operations-json.md) | Default for all `.flow` edits — node/edge CRUD, variables, subflows, output mapping, in-place input updates. |
| **CLI** (opt-in / carve-outs) | [editing-operations-cli.md](editing-operations-cli.md) | Connector, connector-trigger, and inline-agent nodes (carve-outs); or when the user explicitly requests CLI. |

---

## Strategy Selection Matrix

Use this table to determine which strategy to follow for each operation. **Direct JSON is the default**; use CLI only for the carve-out rows or when the user explicitly opts in.

| Operation | Default | Alternative | Notes |
|-----------|---------|-------------|-------|
| Add a node | **Direct JSON** | CLI (opt-in) | CLI still auto-manages definitions/variables when opted in. |
| Add a HITL QuickForm node | **Direct JSON** | CLI (opt-in) via `uip maestro flow hitl add` | Dedicated command also handles definition + `variables.nodes`. Wire `completed` port after. See [hitl/impl.md](plugins/hitl/impl.md). |
| Delete a node | **Direct JSON** | CLI (opt-in) | |
| Add an edge | **Direct JSON** | CLI (opt-in) | Remember `targetPort` (Rule #6). |
| Delete an edge | **Direct JSON** | CLI (opt-in) | |
| Update node inputs | **Direct JSON** | — | In-place edit; preserves node ID and `$vars`. |
| Add/edit workflow variable | **Direct JSON** | — | JSON-only; CLI does not support. |
| Add variable update | **Direct JSON** | — | JSON-only; CLI does not support. |
| Map outputs on End node | **Direct JSON** | — | JSON-only. |
| Create a subflow | **Direct JSON** | — | JSON-only. |
| Replace trigger (non-connector) | **Direct JSON** | CLI (opt-in) | |
| Replace mock with real resource (non-connector) | **Direct JSON** | CLI (opt-in) | |
| Insert node between two existing nodes | **Direct JSON** | CLI (opt-in) | |
| Insert a decision branch | **Direct JSON** | CLI (opt-in) | |
| Remove a node and reconnect | **Direct JSON** | CLI (opt-in) | |
| **Configure a connector node** | **CLI** (carve-out) | Direct JSON (fallback) | `uip maestro flow node configure --detail` auto-populates `inputs.detail` + `bindings_v2.json`. |
| **Configure a connector trigger** | **CLI** (carve-out) | Direct JSON (fallback) | Same as above. |
| **Add an inline agent node** | **CLI** (carve-out) | — | Scaffolded via `uip agent init --inline-in-flow`. |

### Mixing strategies

The default strategy is Direct JSON. Mixing is still common: for connector, connector-trigger, or inline-agent nodes, use the CLI as documented in their respective plugin `impl.md`. For everything else, use Direct JSON unless the user explicitly asks for CLI.

---

## Shared Rules

These apply regardless of which strategy you use.

### Definitions

- Every unique `type:typeVersion` pair in `nodes` must have a matching entry in `definitions`
- Definitions come from `uip maestro flow registry get <NODE_TYPE> --output json` — copy the `Data.Node` object
- **Never hand-write definitions** — hand-written definitions cause validation failures
- One definition per unique type, not one per node instance

### Layout

- Layout (`layout.nodes`, `subflows[<id>].layout`) is owned by `uip maestro flow tidy` — do not hand-compute coordinates
- When authoring a node, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); tidy rewrites it on save
- Run `uip maestro flow tidy <file>.flow` after edits and before publish/debug — see [commands.md](shared/commands.md#uip-maestro-flow-tidy)

### Edge rules

- `targetPort` is required on every edge — validate rejects edges without it
- See [file-format.md — Standard ports](shared/file-format.md) for port names by node type
- Dynamic ports: decision (`true`/`false`), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`output`/`success`/`loopBack`)

### Validation

- Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete
- Do not validate after each individual edit — intermediate states are expected to be invalid
- Validation checks: JSON schema, definitions coverage, edge references, unique IDs
- Validation does NOT check: connector configuration, connection health, expression correctness, required field completeness

### Expression prefix rules

- Use `=js:` on **value expressions**: end node output `source`, variable updates, HTTP input fields, node `inputs` values
- Do NOT use `=js:` on **condition expressions**: decision `expression`, switch case `expression`, HTTP branch `conditionExpression` — these are always evaluated as JS automatically

See [variables-and-expressions.md](shared/variables-and-expressions.md) for the full expression reference.

---

## Quick Reference — Operation to Guide

| I need to... | Go to |
|---|---|
| Add/delete nodes or edges | [JSON guide](editing-operations-json.md) (default) or [CLI guide](editing-operations-cli.md) (opt-in) |
| Change a node's inputs | [JSON guide — Update node inputs](editing-operations-json.md#update-node-inputs) |
| Configure a connector node | [CLI guide — Configure a connector node](editing-operations-cli.md#configure-a-connector-node) (carve-out) or [JSON guide — Connector Node Configuration](editing-operations-json.md#connector-node-configuration-direct-json) (fallback) |
| Manage variables | [JSON guide — Variable Operations](editing-operations-json.md#variable-operations) |
| Map outputs on End nodes | [JSON guide — Add output mapping](editing-operations-json.md#add-output-mapping-on-an-end-node) |
| Create a subflow | [JSON guide — Create a subflow](editing-operations-json.md#create-a-subflow) |
| Replace a mock placeholder (non-connector) | [JSON guide — Replace a mock](editing-operations-json.md#replace-a-mock-with-a-real-resource-node) (default) or [CLI guide — Replace a mock](editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) (opt-in) |
| Replace a trigger type (non-connector) | [JSON guide — Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) (default) or [CLI guide — Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) (opt-in) |
| Replace a trigger type (connector trigger) | [CLI guide — Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) (carve-out) |
| Understand the `.flow` JSON schema | [file-format.md](shared/file-format.md) |
| Look up CLI flags and syntax | [commands.md](shared/commands.md) |
| Work with variables and expressions | [variables-and-expressions.md](shared/variables-and-expressions.md) |
