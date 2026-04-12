# JSON Workflow Guide

Step-by-step procedures for building and editing UiPath Flow projects by directly authoring `.flow` JSON. This is the "how to execute" companion to the shared SKILL.md workflow.

For ID generation algorithms and editing patterns, see [authoring-guide.md](authoring-guide.md). For the full `.flow` schema, see [../flow-schema.md](../flow-schema.md).

---

## 1. Template-First Approach

**Always start from a template.** Never construct `.flow` JSON from memory.

Pick the closest template from `assets/templates/`, copy it as `<PROJECT_NAME>.flow`, then modify it. Templates contain valid scaffolding with correct definitions, edges, and variable structures that would be tedious and error-prone to write from scratch.

### Template Selection

| Pattern | Template |
|---|---|
| Minimal (trigger + script) | `minimal-flow-template.json` |
| With input variables | `project-scaffold-template.json` |
| Decision/branching | `decision-flow-template.json` |
| Loop iteration | `loop-flow-template.json` |
| HTTP request | `http-flow-template.json` |
| Scheduled trigger | `scheduled-trigger-template.json` |
| Script + connector | `connector-flow-template.json` |
| Data pipeline (transform + loop + filter) | `data-pipeline-template.json` |

### After copying the template

1. Update the `name` field to match `<PROJECT_NAME>`.
2. Generate a new UUID for the `id` field.
3. Update `metadata.createdAt` and `metadata.updatedAt` to the current ISO 8601 timestamp.
4. Modify nodes, edges, and definitions as needed for the target workflow.

---

## 2. Project Setup

A Flow project requires only 2 files:

**`project.uiproj`:**

```json
{
  "Name": "<PROJECT_NAME>",
  "ProjectType": "Flow"
}
```

**`<PROJECT_NAME>.flow`:** Copied and modified from a template (section 1 above).

### Creating the project

1. Create the project directory:
   ```bash
   mkdir <PROJECT_NAME>
   ```
2. Create `project.uiproj` with the content above.
3. Copy the closest template:
   ```bash
   cp assets/templates/<TEMPLATE_NAME>.json <PROJECT_NAME>/<PROJECT_NAME>.flow
   ```
4. Update `name`, `id`, and `metadata` timestamps in the `.flow` file.

> If working inside an existing solution, create the project directory inside the solution directory (alongside the `.uipx` file).

---

## 3. Generic Add Node Pattern

Follow these steps for every node you add to the flow.

1. **Read the node's reference doc** from `../nodes/<type>.md` to get the definition block, port table, and required inputs.

2. **Add the definition** to `workflow.definitions` -- copy the definition block verbatim. Skip this step if a definition with the same `nodeType:version` already exists (see [authoring-guide.md -- Definition Deduplication](authoring-guide.md#3-definition-deduplication)).

3. **Generate a unique node ID** using the [ID generation algorithm](authoring-guide.md#node-id-algorithm).

4. **Add the node instance** to `workflow.nodes`:
   ```json
   {
     "id": "<NODE_ID>",
     "type": "<NODE_TYPE>",
     "typeVersion": "<VERSION>",
     "display": { "label": "<DISPLAY_LABEL>" },
     "inputs": { ... },
     "ui": { "position": { "x": <X>, "y": <Y> } }
   }
   ```

5. **Add edges** connecting the new node to its neighbors. Use the port IDs from the node's reference doc. Generate edge IDs per the [edge ID algorithm](authoring-guide.md#edge-id-algorithm). See [../edge-wiring-guide.md](../edge-wiring-guide.md) for the full port reference.

6. **Regenerate `workflow.variables.nodes`** -- rebuild the entire array from scratch per [authoring-guide.md -- variables.nodes Regeneration](authoring-guide.md#2-variablesnodes-regeneration-critical).

7. **Run the validation checklist** in [../validation-guide.md](../validation-guide.md).

---

## 4. Generic Remove Node Pattern

1. **Remove the node** from `workflow.nodes`.

2. **Remove all edges** from `workflow.edges` where `sourceNodeId` or `targetNodeId` matches the removed node's `id`.

3. **Remove the definition** from `workflow.definitions` only if no other node in `workflow.nodes` uses the same `type:typeVersion`.

4. **Rewire edges** if the removed node was between two other nodes:
   - Add a new edge from the upstream node to the downstream node.
   - Generate the edge ID per the [edge ID algorithm](authoring-guide.md#edge-id-algorithm).
   - Use correct port IDs for both source and target.

5. **Regenerate `workflow.variables.nodes`.**

6. **Run the validation checklist.**

---

## 5. Generic Add Edge Pattern

1. **Check both nodes' port tables** in their reference docs (`../nodes/<type>.md`) or the [port quick reference](../edge-wiring-guide.md).

2. **Generate the edge ID:** `{sourceId}-{sourcePort}-{targetId}-{targetPort}`. Append `-2`, `-3`, etc. on collision.

3. **Add the edge** to `workflow.edges`:
   ```json
   {
     "id": "<EDGE_ID>",
     "sourceNodeId": "<SOURCE_NODE_ID>",
     "sourcePort": "<SOURCE_PORT>",
     "targetNodeId": "<TARGET_NODE_ID>",
     "targetPort": "<TARGET_PORT>"
   }
   ```

4. **Run the validation checklist.** All four fields are required -- missing `targetPort` is the #1 validation failure.

---

## 6. Post-Edit Checklist

After every structural edit (add/remove node, add/remove edge, change inputs), perform these steps:

1. **Regenerate `variables.nodes`** -- rebuild the entire array from scratch if any node was added or removed. See [authoring-guide.md -- variables.nodes Regeneration](authoring-guide.md#2-variablesnodes-regeneration-critical).

2. **Check output mappings** -- every `out` variable in `workflow.variables.globals` must have a `source` expression in every reachable End node's `outputs`.

3. **Check definition coverage** -- every unique `type:typeVersion` in `workflow.nodes` must have a matching `definitions` entry.

4. **Check definition deduplication** -- no two definitions should share the same `nodeType:version`.

5. **Update `metadata.updatedAt`** to the current ISO 8601 timestamp.

6. **Run the full 17-item validation checklist** in [../validation-guide.md](../validation-guide.md).

7. **(Optional) CLI validation** -- if `uip` is available, run as a final check:
   ```bash
   uip flow validate <FILE_PATH> --output json
   ```

---

## 7. When to Use CLI Even in JSON Mode

Some operations require the `uip` CLI regardless of authoring mode. Use CLI for these, then continue JSON editing for everything else.

### Dynamic resource nodes (always CLI)

RPA workflows, agents, API workflows, and agentic processes are tenant-specific. Their definitions are not bundled -- you must fetch them from the registry:

```bash
uip flow registry pull --force
uip flow registry search "<NAME>" --output json
uip flow registry get "<NODE_TYPE>" --output json
```

Copy the `Data.Node` definition from the `registry get` response into `workflow.definitions`. See [../dynamic-nodes/resource-node-guide.md](../dynamic-nodes/resource-node-guide.md) for the full procedure.

### Connector nodes (always CLI)

Connector nodes require connection binding, enriched metadata, and reference field resolution -- all via CLI:

```bash
# List and verify connections
uip is connections list "<CONNECTOR_KEY>" --output json
uip is connections ping "<CONNECTION_ID>" --output json

# Get enriched definition with connection
uip flow registry get <NODE_TYPE> --connection-id <CONNECTION_ID> --output json

# Describe resource and resolve references
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<ID>" --operation Create --output json
uip is resources execute list "<CONNECTOR_KEY>" "<RESOURCE>" \
  --connection-id "<ID>" --output json
```

See [../connectors/connector-guide.md](../connectors/connector-guide.md) for the full 6-step connector workflow.

### Validation (recommended)

While the manual 17-item checklist catches structural issues, CLI validation runs a full Zod schema + cross-reference check that cannot be replicated by manual inspection:

```bash
uip flow validate <FILE_PATH> --output json
```

### Debug and publish (always CLI)

Testing and publishing require CLI regardless of authoring mode:

```bash
# Debug (requires user consent)
UIPCLI_LOG_LEVEL=info uip flow debug <PROJECT_DIR>

# Publish to Studio Web
uip solution bundle <SOLUTION_DIR> --output .
uip solution upload <SOLUTION_NAME>.uis --output json
```
