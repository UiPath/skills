# Project Setup Guide

How to create a valid UiPath Flow project from scratch. Two paths are available: **CLI** (uses `uip` commands) and **JSON** (manual file creation). Both produce the same project structure.

---

## Project Structure

A Flow project requires exactly 2 files:

```
<ProjectName>/
  project.uiproj
  <ProjectName>.flow
```

**`project.uiproj`:**

```json
{
  "Name": "<PROJECT_NAME>",
  "ProjectType": "Flow"
}
```

**`<PROJECT_NAME>.flow`:** The flow definition file. Start from a template in `assets/templates/` (JSON path) or let the CLI scaffold it (`uip flow init`).

---

## CLI Path

Use the CLI when `uip` is available. This handles scaffolding, solution structure, and registry setup automatically.

### Step 1 -- Resolve the `uip` binary

```bash
which uip || npm list -g @uipath/uipcli
```

If not found, install:

```bash
npm install -g @uipath/uipcli
```

Verify with `uip --version`.

### Step 2 -- Check login status

`uip flow debug` and resource operations require authentication. `uip flow init`, `validate`, and `registry` commands work without login.

```bash
uip login status --output json
```

If not logged in and you need cloud features:

```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 3 -- Create a solution and Flow project

Every Flow project lives inside a solution. Check the current directory for existing `.uipx` files. If existing solutions are found, ask the user whether to reuse one or create a new one.

#### 3a. Create a new solution

```bash
uip solution new "<SolutionName>" --output json
```

> **Naming convention:** Use the same name for both the solution and the project unless the user specifies otherwise.

#### 3b. Create the Flow project inside the solution folder

```bash
cd <directory>/<SolutionName> && uip flow init <ProjectName>
```

#### 3c. Add the project to the solution

```bash
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

This scaffolds a complete project inside a solution with all required files.

---

## JSON Path

Use direct file creation when the CLI is not available or when you want full control over the project structure.

### Step 1 -- Create the project directory

```bash
mkdir -p <SolutionName>/<ProjectName>
```

### Step 2 -- Create `project.uiproj`

Write the following to `<SolutionName>/<ProjectName>/project.uiproj`:

```json
{
  "Name": "<PROJECT_NAME>",
  "ProjectType": "Flow"
}
```

### Step 3 -- Copy a template as the `.flow` file

Select a template from `assets/templates/` (see Template Selection Table below) and copy it:

```bash
cp assets/templates/<TEMPLATE>.json <SolutionName>/<ProjectName>/<ProjectName>.flow
```

### Step 4 -- Update the `.flow` file

1. Set `name` to match `<PROJECT_NAME>`.
2. Generate a new UUID for `id`.
3. Update `metadata.createdAt` and `metadata.updatedAt` to the current ISO 8601 timestamp.
4. Modify nodes, edges, and definitions as needed for the target workflow.
5. Regenerate `variables.nodes` using the algorithm below.

---

## Template Selection Table

| Template | When to Use |
|----------|-------------|
| `minimal-flow-template.json` | Simple flows with a manual trigger and script node. Default starting point. |
| `http-flow-template.json` | Flows that primarily make HTTP/REST API calls. |
| `decision-flow-template.json` | Flows with if/else branching logic. |
| `loop-flow-template.json` | Flows that iterate over collections. |
| `connector-flow-template.json` | Flows that use Integration Service connectors. |
| `scheduled-trigger-template.json` | Flows triggered on a recurring schedule (not manual). |
| `multi-agent-template.json` | Flows orchestrating multiple AI agents. |
| `project-scaffold-template.json` | Bare scaffold with minimal boilerplate for building from scratch. |

---

## ID Generation Algorithms

### Node ID Algorithm

1. Take the display label (or custom label) of the node.
2. Split on non-alphanumeric characters.
3. Join as camelCase (first word lowercase, remaining words capitalized).
4. Strip the `"createNew"` prefix if present.
5. Append a numeric suffix starting at `1`, incrementing until the ID is unique within the workflow.
6. Result examples: `sendMessage1`, `httpRequest1`, `decision2`.

> Node IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/` and must not be a JavaScript or Python reserved word.

### Edge ID Algorithm

Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`

- Use `"default"` if a port is null.
- Append `-2`, `-3`, etc. on collision with an existing edge ID.
- Example: `start-output-httpRequest1-input`

### Binding ID Algorithm

Format: `b` + 8 random alphanumeric characters.

Example: `bXk9mNpQr`

---

## `variables.nodes` Regeneration (CRITICAL)

> **Every time a node is added or removed, you MUST regenerate `workflow.variables.nodes` from scratch.** Failing to do this produces a broken flow that will not run. In CLI mode, `uip flow node add` handles this automatically. In JSON mode, you must do it manually.

### Algorithm

1. For each node in `workflow.nodes`:
   - Check if the node instance has `outputs` defined.
   - If not, fall back to the matching definition's `outputDefinition`.
   - For each output key, emit a `NodeVariable`:
     ```json
     {
       "id": "<NODE_ID>.<OUTPUT_KEY>",
       "type": "<OUTPUT_TYPE>",
       "binding": { "nodeId": "<NODE_ID>", "outputId": "<OUTPUT_KEY>" }
     }
     ```
2. Replace `workflow.variables.nodes` entirely with the regenerated array.

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

### Subflow Note

Subflows have their own `variables.nodes` array. Apply the same regeneration algorithm within `subflows.<PARENT_NODE_ID>.variables.nodes` using only the nodes in that subflow. See [subflow-guide.md](subflow-guide.md).

---

## Definition Deduplication

`workflow.definitions` is deduplicated by a `nodeType:version` composite key.

- **When adding a node:** Skip the definition insert if a definition with the same `nodeType` + `version` already exists in the array.
- **When deleting a node:** Remove the definition only if no other node in `workflow.nodes` uses the same `type:typeVersion` combination.

---

## Validation

After creating or modifying a project:

- **CLI:** Run `uip flow validate <ProjectName>.flow --output json`.
- **JSON:** Walk through the validation checklist in [validation-guide.md](validation-guide.md). Optionally also run CLI validate if `uip` is available.
