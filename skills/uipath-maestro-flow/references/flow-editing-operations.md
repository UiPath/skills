# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Two implementation strategies are available — choose one per operation and follow the corresponding guide.

## Strategy Guides

| Strategy | Guide | When to use |
|----------|-------|-------------|
| **CLI** | [flow-editing-operations-cli.md](flow-editing-operations-cli.md) | Node and edge CRUD. Automatic definition management, variable wiring, and cleanup. |
| **Direct JSON** | [flow-editing-operations-json.md](flow-editing-operations-json.md) | Variable management, subflows, output mapping, in-place input updates. Full control. |

---

## Strategy Selection Matrix

Use this table to determine which strategy to follow for each operation.

| Operation | CLI | Direct JSON | Notes |
|-----------|-----|-------------|-------|
| **Add a node** | Yes | Yes | CLI auto-manages definitions and variables |
| **Delete a node** | Yes | Yes | CLI auto-cascades edge/definition/variable cleanup |
| **Add an edge** | Yes | Yes | CLI auto-sets `targetPort` |
| **Delete an edge** | Yes | Yes | Equivalent complexity |
| **Update node inputs** | Delete + re-add | In-place edit | JSON is simpler for input-only changes |
| **Configure connector node** | `node configure` | Manual `inputs.detail` + `bindings_v2.json` | CLI handles binding automatically |
| **Add workflow variable** | Not supported | Yes | Edit `variables.globals` |
| **Add variable update** | Not supported | Yes | Edit `variables.variableUpdates` |
| **Map outputs on End node** | Not supported | Yes | Edit node `outputs` object |
| **Create a subflow** | Not supported | Yes | Edit `subflows` object |
| **Replace trigger type** | Delete + re-add | In-place edit | JSON is simpler for trigger swaps |
| **Replace mock with resource** | Delete + re-add | Delete + re-add | Both require registry lookup |
| **Insert node between two** | 3 CLI commands | 3 JSON edits | Equivalent complexity |
| **Insert a decision branch** | 4 CLI commands | 4 JSON edits | Equivalent complexity |

### Mixing strategies

You can mix CLI and JSON strategies within the same flow build. Common pattern:

1. Use **CLI** for adding/deleting nodes and edges (avoids manual definition management)
2. Use **Direct JSON** for variables, variableUpdates, output mapping, and subflows

---

## Shared Rules

These apply regardless of which strategy you use.

### Definitions

- Every unique `type:typeVersion` pair in `nodes` must have a matching entry in `definitions`
- Definitions come from `uip flow registry get <NODE_TYPE> --output json` — copy the `Data.Node` object
- **Never hand-write definitions** — hand-written definitions cause validation failures
- One definition per unique type, not one per node instance

### Layout

- Flow uses a horizontal canvas — place nodes left-to-right with increasing `x` values
- Use a consistent `y` baseline (e.g., `y: 144`) for linear flows
- Offset `y` for branch paths (e.g., true branch at `y: 44`, false branch at `y: 244`)
- Space nodes ~200px apart on the x-axis

### Edge rules

- `targetPort` is required on every edge — validate rejects edges without it
- See [flow-file-format.md — Standard ports](flow-file-format.md) for port names by node type
- Dynamic ports: decision (`true`/`false`), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`output`/`success`/`loopBack`)

### Validation

- Run `uip flow validate <ProjectName>.flow --output json` **once** after all edits complete
- Do not validate after each individual edit — intermediate states are expected to be invalid
- Validation checks: JSON schema, definitions coverage, edge references, unique IDs
- Validation does NOT check: connector configuration, connection health, expression correctness, required field completeness

### Expression prefix rules

- Use `=js:` on **value expressions**: end node output `source`, variable updates, HTTP input fields, node `inputs` values
- Do NOT use `=js:` on **condition expressions**: decision `expression`, switch case `expression`, HTTP branch `conditionExpression` — these are always evaluated as JS automatically

See [variables-and-expressions.md](variables-and-expressions.md) for the full expression reference.

---

## Quick Reference — Operation to Guide

| I need to... | Go to |
|---|---|
| Add/delete nodes or edges | [CLI guide](flow-editing-operations-cli.md) or [JSON guide](flow-editing-operations-json.md) |
| Change a node's inputs | [JSON guide — Update node inputs](flow-editing-operations-json.md#update-node-inputs) or [CLI guide — Update node inputs](flow-editing-operations-cli.md#update-node-inputs-expression-script-body-label-etc) |
| Configure a connector node | [CLI guide — Configure a connector node](flow-editing-operations-cli.md#configure-a-connector-node) or [JSON guide — Connector Node Configuration](flow-editing-operations-json.md#connector-node-configuration-direct-json) |
| Manage variables | [JSON guide — Variable Operations](flow-editing-operations-json.md#variable-operations) |
| Map outputs on End nodes | [JSON guide — Add output mapping](flow-editing-operations-json.md#add-output-mapping-on-an-end-node) |
| Create a subflow | [JSON guide — Create a subflow](flow-editing-operations-json.md#create-a-subflow) |
| Replace a mock placeholder | [CLI guide — Replace a mock](flow-editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) or [JSON guide — Replace a mock](flow-editing-operations-json.md#replace-a-mock-with-a-real-resource-node) |
| Replace a trigger type | [CLI guide — Replace trigger](flow-editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) or [JSON guide — Replace trigger](flow-editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) |
| Understand the `.flow` JSON schema | [flow-file-format.md](flow-file-format.md) |
| Look up CLI flags and syntax | [flow-commands.md](flow-commands.md) |
| Work with variables and expressions | [variables-and-expressions.md](variables-and-expressions.md) |
