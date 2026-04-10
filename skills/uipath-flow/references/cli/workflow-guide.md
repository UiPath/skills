# CLI Workflow Guide

Step-by-step procedures for building and editing UiPath Flow projects using the `uip` CLI. This is the "how to execute" companion to the shared SKILL.md workflow.

For the full command syntax and flag reference, see [commands-reference.md](commands-reference.md).

---

## 1. Prerequisites

### Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
which uip || npm list -g @uipath/uipcli
```

If not found, install:

```bash
npm install -g @uipath/uipcli
```

Verify with `uip --version`.

### Check login status

Many commands work without authentication. Check current state:

```bash
uip login status --output json
```

If not logged in and you need cloud features (debug, process operations, connector/resource registry, IS connections):

```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

**Commands that require login:** `flow debug`, `flow process`, `flow job`, `solution upload`, `is connections`, `is resources`, `is connectors`, registry access to tenant-specific nodes.

**Commands that work without login:** `flow init`, `flow validate`, `flow node add/list`, `flow edge add`, `flow registry pull/list/search/get` (OOTB nodes only), `flow pack`, `solution new`, `solution bundle`, `solution project add`.

---

## 2. Generic Patterns

Reusable command patterns for the most common flow operations.

### Add a node

```bash
uip flow node add <FILE_PATH> <NODE_TYPE> --output json \
  [--input '{"expression": "..."}'] \
  [--label "My Node"] \
  [--position 300,400]
```

The command automatically:
- Adds the node to the `nodes` array
- Adds its definition to the `definitions` array (if not already present)
- Assigns a unique node ID

After adding, list nodes to get the assigned IDs:

```bash
uip flow node list <FILE_PATH> --output json
```

### List nodes

```bash
uip flow node list <FILE_PATH> --output json
```

Returns all nodes with their IDs, types, and labels. Use after `node add` to discover assigned IDs for wiring edges.

### Add an edge

```bash
uip flow edge add <FILE_PATH> <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
  --source-port <PORT> \
  --target-port <PORT>
```

Common port pairs:

| Source node type | `--source-port` | `--target-port` (on target) |
|-----------------|-----------------|----------------------------|
| Trigger | `output` | `input` |
| Script | `success` | `input` |
| Decision (true branch) | `true` | `input` |
| Decision (false branch) | `false` | `input` |
| Loop (body) | `output` | `input` |
| Loop (complete) | `success` | `input` |
| HTTP (default) | `default` | `input` |
| Transform | `success` | `input` |

For the full port reference, see [../edge-wiring-guide.md](../edge-wiring-guide.md).

### Configure a connector node

After adding a connector node with `node add`, configure it with resolved connection and field values:

```bash
uip flow node configure <FILE_PATH> <NODE_ID> \
  --detail '{"connectionId": "<ID>", "folderKey": "<KEY>", "method": "POST", "endpoint": "/issues", "bodyParameters": {"field": "value"}}'
```

The `method` and `endpoint` values come from `connectorMethodInfo` in the `registry get` response. The command populates `inputs.detail` and creates workflow-level `bindings` entries. Use **resolved IDs** from reference resolution, not display names.

### Validate

```bash
uip flow validate <FILE_PATH> --output json
```

Run after every structural change. See section 6 below for the full validation loop.

---

## 3. Shell Quoting Tips

### Problem

`--input` and `--detail` flags accept JSON strings that often contain special characters (quotes, braces, `$vars`, backslashes) that the shell interprets before the CLI receives them.

### Temp file pattern (recommended for complex JSON)

Write the JSON to a temp file, then pass it with command substitution:

```bash
# Write complex JSON to temp file
cat > /tmp/node-input.json << 'ENDJSON'
{"script": "const data = $vars.fetchData.output;\nreturn { count: data.items.length, total: data.items.reduce((a, b) => a + b.amount, 0) };"}
ENDJSON

# Pass via command substitution
uip flow node add <FILE_PATH> core.action.script \
  --input "$(cat /tmp/node-input.json)" --output json
```

The `<< 'ENDJSON'` heredoc syntax (with quotes around the delimiter) prevents shell expansion of `$vars` and other special characters inside the JSON.

### Same pattern for `--detail`

```bash
cat > /tmp/detail.json << 'ENDJSON'
{"connectionId": "7622a703-5d85-4b55-849b-6c02315b9e6e", "folderKey": "123456", "method": "POST", "endpoint": "/issues", "bodyParameters": {"fields.project.key": "ENGCE"}}
ENDJSON

uip flow node configure <FILE_PATH> <NODE_ID> --detail "$(cat /tmp/detail.json)"
```

### Simple JSON (inline is fine)

For short, simple JSON without special characters, inline quoting works:

```bash
uip flow node add <FILE_PATH> core.logic.decision --output json \
  --input '{"expression": "=js:$vars.status === 200"}'
```

---

## 4. What CLI Handles Automatically

When using CLI commands, these operations are managed for you:

| Operation | Handled by |
|-----------|-----------|
| Adding node definition to `definitions` | `uip flow node add` |
| Assigning unique node IDs | `uip flow node add` |
| Setting `targetPort` on edges | `uip flow edge add` |
| Creating `bindings_v2.json` entries for connectors | `uip flow node configure` |
| Populating `inputs.detail` for connectors | `uip flow node configure` |
| Validating JSON structure and cross-references | `uip flow validate` |
| Refreshing node type cache | `uip flow registry pull` |

---

## 5. What CLI Does NOT Support

The CLI does not yet support these operations. Fall back to direct JSON editing of the `.flow` file for these cases. See [../json/authoring-guide.md](../json/authoring-guide.md) for JSON editing patterns.

| Operation | Workaround |
|-----------|-----------|
| **Remove a node** | Delete from `workflow.nodes`, remove referencing edges, clean up definition if last user |
| **Remove an edge** | Delete from `workflow.edges` |
| **Update existing node inputs** (e.g., change a script body) | Edit `inputs` directly in the JSON |
| **Rewire existing edges** | Edit `sourceNodeId`/`targetNodeId`/ports in the JSON |
| **Manage variables** (add/remove/update `variables.globals`) | Edit `variables` section directly |
| **Map outputs on End nodes** | Edit the End node's `outputs` field in JSON |
| **Add `variableUpdates`** | Edit `variables.variableUpdates` in JSON |
| **Update `variables.nodes`** | CLI `node add` does NOT regenerate this -- edit JSON directly |
| **Create subflows** | Edit `subflows` section in JSON |

> **Important:** Even in CLI mode, `variables.nodes` must be regenerated manually after adding/removing nodes. The CLI's `node add` command does not update this array. See [../json/authoring-guide.md](../json/authoring-guide.md) for the regeneration algorithm.

---

## 6. Validation Loop

Run validation after **every** structural change. Do not batch multiple edits before validating.

```
1. Edit the .flow file (add node, add edge, change input, etc.)
2. Run: uip flow validate <FILE_PATH> --output json
3. If Result is "Success" --> done, proceed to next edit
4. If Result is "Failure":
   a. Read the error messages in "Instructions"
   b. Fix the .flow file based on the error
   c. Go to step 2
```

There is no maximum retry count -- every error has a deterministic fix. If the same error persists after a fix attempt, re-read the error message carefully and verify the JSON structure matches the expected format.

### Common error categories

| Error | Cause | Fix |
|-------|-------|-----|
| Missing `targetPort` | Edge created without `targetPort` | Add `targetPort` -- check the node's port table in [../edge-wiring-guide.md](../edge-wiring-guide.md) |
| Missing definition | Node `type:typeVersion` has no matching `definitions` entry | Run `uip flow registry get <NODE_TYPE> --output json` and add `Data.Node` to definitions |
| Invalid node reference | `sourceNodeId` or `targetNodeId` does not match any node ID | Correct the reference to an existing node ID |
| Duplicate IDs | Two nodes or two edges share the same ID | Rename to unique IDs, update all referencing edges |

### What CLI validation does NOT catch

CLI validation is a local JSON + cross-reference check. It does **not** catch:

- **Connector issues** -- wrong connection IDs, expired tokens, misconfigured enriched metadata. Validate connections during Phase 2 planning.
- **Runtime errors** -- external API failures, service unavailability. Only surface during `uip flow debug`.
- **Missing output mappings** -- an End node without `source` for an `out` variable passes validation but produces `null` at runtime.
- **Script logic errors** -- valid syntax with wrong business logic passes validation.
- **Resource availability** -- RPA processes, agents, or apps may not be published. Validation does not check Orchestrator state.
- **Expression correctness** -- `=js:` expressions with valid syntax but incorrect variable references pass validation.

> **validate vs debug:** `uip flow validate` is instant and local -- use it freely. `uip flow debug` uploads and executes the flow with real side effects. Never use `debug` as a validation step.

---

## 7. CLI Output Format

All `uip` commands return structured JSON when `--output json` is specified:

### Success

```json
{
  "Result": "Success",
  "Code": "<CommandCode>",
  "Data": { ... }
}
```

### Failure

```json
{
  "Result": "Failure",
  "Message": "...",
  "Instructions": "Found N error(s): ..."
}
```

Parse the `Result` field to determine success/failure. On failure, the `Instructions` field contains individual error messages.

The `--localstorage-file` warning that appears in some environments is benign and can be ignored.
