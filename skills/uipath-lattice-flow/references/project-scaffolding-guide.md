# Project Scaffolding Guide

How to create a valid UiPath Flow project from scratch, including ID generation algorithms and the critical `variables.nodes` regeneration procedure.

---

## Project Structure

A Flow project requires only 2 files:

**`project.uiproj`:**

```json
{
  "Name": "<PROJECT_NAME>",
  "ProjectType": "Flow"
}
```

**`<PROJECT_NAME>.flow`:** Start from a template in `assets/templates/`. The minimal template (`minimal-flow-template.json`) contains a manual trigger and a script node.

---

## ID Generation Algorithms

### Node ID Algorithm

1. Take the display label (or custom label) of the node
2. Split on non-alphanumeric characters
3. Join as camelCase (first word lowercase, remaining words capitalized)
4. Strip the `"createNew"` prefix if present
5. Append a numeric suffix starting at `1`, incrementing until the ID is unique within the workflow
6. Result examples: `sendMessage1`, `httpRequest1`, `decision2`

> Node IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/` and must not be a JavaScript or Python reserved word.

### Edge ID Algorithm

Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`

- Use `"default"` if a port is null
- Append `-2`, `-3`, etc. on collision with an existing edge ID
- Example: `start-output-httpRequest1-input`

### Binding ID Algorithm

Format: `b` + 8 random alphanumeric characters.

Example: `bXk9mNpQr`

---

## `variables.nodes` Regeneration (Critical)

> **Every time a node is added or removed, you MUST regenerate `workflow.variables.nodes` from scratch.** Failing to do this produces a broken flow that will not run.

### Algorithm

1. For each node in `workflow.nodes`:
   - Check if the node instance has `outputs` defined
   - If not, fall back to the matching definition's `outputDefinition`
   - For each output key, emit a `NodeVariable`:
     ```json
     {
       "id": "<NODE_ID>.<OUTPUT_KEY>",
       "type": "<OUTPUT_TYPE>",
       "binding": { "nodeId": "<NODE_ID>", "outputId": "<OUTPUT_KEY>" }
     }
     ```
2. Replace `workflow.variables.nodes` entirely with the regenerated array

### Concrete Example

Given a flow with a manual trigger node (`start`) that has one output (`output`) and a script node (`myScript`) that has two outputs (`output`, `error`), the regenerated `variables.nodes` array is:

```json
"nodes": [
  {
    "id": "start.output",
    "type": "object",
    "description": "Trigger output",
    "binding": { "nodeId": "start", "outputId": "output" }
  },
  {
    "id": "myScript.output",
    "type": "object",
    "description": "Script result",
    "binding": { "nodeId": "myScript", "outputId": "output" }
  },
  {
    "id": "myScript.error",
    "type": "object",
    "description": "Error output",
    "binding": { "nodeId": "myScript", "outputId": "error" }
  }
]
```

---

## Definition Deduplication

`workflow.definitions` is deduplicated by a `nodeType:version` composite key.

- **When adding a node:** Skip the definition insert if a definition with the same `nodeType` + `version` already exists in the array
- **When deleting a node:** Remove the definition only if no other node in `workflow.nodes` uses the same `type:typeVersion` combination

---

## Step-by-Step: Create a New Project

1. Create the project directory:
   ```bash
   mkdir <PROJECT_NAME>
   ```
2. Create `project.uiproj` with the following content:
   ```json
   {
     "Name": "<PROJECT_NAME>",
     "ProjectType": "Flow"
   }
   ```
3. Copy the closest template from `assets/templates/` as `<PROJECT_NAME>.flow`:
   ```bash
   cp assets/templates/minimal-flow-template.json <PROJECT_NAME>/<PROJECT_NAME>.flow
   ```
4. Update the `name` field in the `.flow` file to match `<PROJECT_NAME>`
5. Generate a new UUID for the `id` field
6. Update `metadata.createdAt` and `metadata.updatedAt` to the current ISO 8601 timestamp
7. Modify nodes, edges, and definitions as needed for the target workflow
8. Regenerate `variables.nodes` using the algorithm in the Regeneration section above
9. Run the validation checklist to confirm the flow is structurally correct
