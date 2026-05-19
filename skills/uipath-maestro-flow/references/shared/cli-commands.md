# uip maestro flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

> For node and edge commands (`node add/remove/list/configure`, `edge add/remove/list`), see the [Author CLI editing strategy](../author/references/editing-operations-cli.md). This file covers project setup, validation, registry, debug, and publishing commands.

## uip maestro flow init

Scaffold a new Flow project directory. **Always create a solution first** (see the [Author greenfield journey — Step 2](../author/references/greenfield.md)).

```bash
# 1. Create solution first
uip solution init "<SolutionName>" --output json

# 2. Init the flow project inside the solution folder.
#    When run from inside a solution directory, `flow init` auto-registers
#    the project with the parent `.uipx` — no manual `solution project add`
#    is required. Confirm via `Data.SolutionRegistration.Status` in the
#    response (`Registered` or `AlreadyRegistered`).
#
#    Post-MST-10004 the field is ALWAYS present:
#      - "Registered" / "AlreadyRegistered" → done
#      - "NotInSolution" → cd into the solution dir is missing, restart from step 1
#      - "Skipped" / "Failed" → fall through to step 3
#    On pre-MST-10004 CLI versions the field can be absent. Inspect the
#    `.uipx` Projects[] manifest with `cat <SolutionName>.uipx`: proceed if
#    it lists `<ProjectName>/project.uiproj`; otherwise use step 3 when the
#    layout is double-nested, or restart from step 1 when no `.uipx` exists.
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName> --output json

# 3. (Fallback only) Wire the project manually if auto-registration was
#    `Skipped`, `Failed`, or field-absent with a double-nested project whose
#    `.uipx` Projects[] manifest is missing `<ProjectName>/project.uiproj`.
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

Creates `<ProjectName>/` with `project.uiproj`, `<ProjectName>.flow`, `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` inside the solution directory.

## uip maestro flow validate

Validate a `.flow` file locally — no auth, no network.

```bash
uip maestro flow validate <path/to/file.flow>
uip maestro flow validate <path/to/file.flow> --output json
uip maestro flow validate <path/to/file.flow> --verbose --output json

# With governance policy checks (requires login)
uip maestro flow validate <path/to/file.flow> --governance --output json
```

Checks:

- JSON parses correctly
- All required fields present (including `targetPort` on edges)
- Every node `type:typeVersion` has a matching entry in `definitions`
- Edge `sourceNodeId`/`targetNodeId` reference existing node `id`s
- Node `id`s are unique; edge `id`s are unique

Exit code 0 = valid, 1 = invalid.

### `--governance` flag

Validates agent nodes against organization governance policies fetched from the platform. Requires `uip login`. When governance data cannot be fetched (no login, platform unreachable), the command exits with a failure. Omit `--governance` to run local-only schema validation without auth.

## uip maestro flow format

Auto-layout nodes in the `.flow` file. Run after validation passes and before publishing or debugging — without format, hand-written or stale `layout` data can render as misshapen rectangles in Studio Web.

```bash
uip maestro flow format <path/to/file.flow>
uip maestro flow format <path/to/file.flow> --output json
```

Format:
- Arranges nodes horizontally (left-to-right) and anchors to the leftmost node's original position so the user's general layout intent is preserved
- Sets every non-`stickyNote` node's `size` to `{ "width": 96, "height": 96 }` — preserving sticky-note custom sizes
- Recurses into subflows and rewrites `subflows[<id>].layout` for each
- Backfills missing `position`/`size` entries
- Does not modify node logic, edges, definitions, or variables — only layout coordinates

JSON output (`--output json`) reports counts in `Data`: `NodesTotal`, `EdgesTotal`, `NodesRepositioned`, `NodesResized`, `SubflowsTidied`.

## uip maestro flow pack

Pack a Flow project into a `.nupkg` for Orchestrator deployment.

```bash
uip maestro flow pack <ProjectDir> <OutputDir>
uip maestro flow pack <ProjectDir> <OutputDir> --version 2.0.0
uip maestro flow pack <ProjectDir> <OutputDir> --output json
```

Requires `content/package-descriptor.json` and `content/operate.json` in the project. Output: `<Name>.flow.Flow.<version>.nupkg`.

> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the flow in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `uip solution upload` (see below). See [uipath-solution](/uipath:uipath-solution) for `solution publish` commands.

## uip solution resource refresh

Re-scan all projects in the solution and sync resource declarations (connections, processes, queues, etc.) from their `bindings_v2.json` files. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists. **Always run this before `uip solution upload` or `uip maestro flow debug`.**

```bash
uip solution resource refresh <SolutionDir> --output json
```

The argument is the solution directory (containing the `.uipx` file). Defaults to the current directory if omitted.

## uip solution upload

Upload a solution directly to Studio Web. **Requires `uip login`.**

```bash
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory (the folder containing the `.uipx` file) directly — no intermediate bundling step is required. Uploads the solution to Studio Web where the user can visualize, inspect, edit, and publish the flow from the browser.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `uip solution upload <SolutionDir>` to push to Studio Web. Share the resulting URL with the user.

## uip maestro flow debug

Debug a Flow in the cloud via Studio Web + Orchestrator. **Requires `uip login`.**

```bash
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json

# Pass input arguments to the flow
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir. Always run `uip maestro flow validate` first.

Use `--inputs` to pass a JSON object of input arguments when the flow has input parameters (e.g. trigger inputs or workflow arguments).

Run `uip maestro flow debug --help` to discover additional options.

### Reporting the run back to the user

The CLI response includes a **Studio Web URL** (where the user can inspect the run) and an **instanceId** (for log/trace correlation). Parse both from the JSON output — typically `Data.studioWebUrl` and `Data.instanceId` — and **always show them as the first two lines of the summary** you report back to the user:

```
Studio Web URL: <url>
Instance ID: <instanceId>

<run status, node traces, errors, etc.>
```

If either value is not present in the response, emit the label with `<not returned by CLI>` rather than dropping the line. Do not bury these values below the run summary — the user should see them immediately without scrolling.

## uip maestro flow process

Manage deployed Flow processes in Orchestrator. **Requires `uip login`.**

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json
```

Run `uip maestro flow process --help` for all subcommands and options.

## uip maestro flow job

Monitor Flow jobs. **Requires `uip login`.**

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

## uip maestro flow hitl add

Add a Human-in-the-Loop QuickForm node to an existing `.flow` file. Writes the node JSON, adds the definition entry (once), and updates `variables.nodes` automatically.

```bash
# Minimal — adds a bare node with no schema fields
uip maestro flow hitl add <path/to/file.flow> --output json

# With label and priority
uip maestro flow hitl add <path/to/file.flow> \
  --label "Invoice Review" \
  --priority High \
  --output json

# With assignee (email or group name)
uip maestro flow hitl add <path/to/file.flow> \
  --assignee reviewer@company.com \
  --output json

uip maestro flow hitl add <path/to/file.flow> \
  --assignee finance-approvers \
  --output json

# With full schema (inputs, outputs, outcomes)
uip maestro flow hitl add <path/to/file.flow> \
  --label "Invoice Review" \
  --priority High \
  --assignee finance-approvers \
  --schema '{"inputs":[{"name":"invoiceId","binding":"fetchInvoice.output.invoiceId"},{"name":"amount","type":"number","binding":"fetchInvoice.output.amount"}],"outputs":[{"name":"decision","required":true}],"outcomes":[{"name":"Approve"},{"name":"Reject"}]}' \
  --position 474,144 \
  --output json
```

| Flag | Description | Default |
|------|-------------|---------|
| `--label <text>` | Display label for the node | `"Human in the Loop"` |
| `--priority Low\|Medium\|High` | Task priority in Action Center | `Low` |
| `--assignee <email-or-group>` | User email (`staticEmail`) or group name (`staticGroupName`) | group (unassigned) |
| `--schema <json>` | JSON object describing form fields and outcomes — see schema format below | empty form |
| `--position <x,y>` | Canvas position | `0,0` |

### `--schema` JSON format

```json
{
  "inputs":  [{ "name": "invoiceId", "binding": "fetchInvoice.output.invoiceId" },
              { "name": "amount", "type": "number", "binding": "fetchInvoice.output.amount" }],
  "outputs": [{ "name": "decision", "required": true },
              { "name": "notes" }],
  "inOuts":  [{ "name": "emailBody" }],
  "outcomes":[{ "name": "Approve" }, { "name": "Reject" }]
}
```

- `inputs` — read-only context fields shown to the reviewer; `binding` is the full `$vars` path (e.g. `fetchInvoice.output.invoiceId`)
- `outputs` — fields the human fills in; `variable` defaults to the field name
- `inOuts` — pre-filled editable fields (human can modify before submitting)
- `outcomes` — button labels; first is primary (Approve path); subsequent ones end the flow unless you re-wire them

### Success output

```json
{ "Result": "Success", "Code": "HitlNodeAdded", "Data": { "NodeId": "invoiceReview1", "NodeType": "uipath.human-in-the-loop", "Label": "Invoice Review", "DefinitionAdded": true } }
```

After adding, wire the `completed` port to the next node — an unwired `completed` blocks the flow indefinitely. See the [Author HITL plugin reference](../author/references/plugins/hitl/impl.md) for edge format.

## uip maestro flow instance / uip maestro flow incident

See the [Diagnose troubleshooting guide](../diagnose/references/troubleshooting-guide.md) for the full diagnostic workflow and command reference for `instance` and `incident` subcommands.

## uip maestro flow node / uip maestro flow edge

See the [Author CLI editing strategy](../author/references/editing-operations-cli.md) for complete `node add/remove/list/configure` and `edge add/remove/list` syntax, flags, and auto-managed behaviors.

## uip maestro flow eval

Evaluation surface — evaluator CRUD, eval set CRUD, data point CRUD, Studio Web run start/status/results/list/compare. Local CRUD requires no login; `eval run *` requires `uip login` and a Flow solution that already exists in Studio Web. **Never auto-run `uip solution upload` to satisfy the Studio Web prerequisite** — see [evaluate/references/upload-safety.md](../evaluate/references/upload-safety.md).

```bash
# Data points (test cases) — inline inside eval set JSON
uip maestro flow eval add <name>    --set <set> [flags]  --output json
uip maestro flow eval list          --set <set> --path <flow_project> --output json
uip maestro flow eval remove <id>   --set <set> --path <flow_project> --output json

# Eval sets
uip maestro flow eval set add <name> [--evaluators <refs>] [--entry-point <id>] --path <flow_project> --output json
uip maestro flow eval set list      --path <flow_project> --output json
uip maestro flow eval set remove <id> --path <flow_project> --output json

# Evaluators (7 types: exact-match, json-similarity, contains, llm-judge-output|strict-json|trajectory|trajectory-simulation)
uip maestro flow eval evaluator add <name> --type <type> [--model <m>] [--target-key <k>] [--prompt <p>] --path <flow_project> --output json
uip maestro flow eval evaluator list      --path <flow_project> --output json
uip maestro flow eval evaluator remove <id> --path <flow_project> --output json

# Runs (require uip login + solution in Studio Web)
uip maestro flow eval run start <name>   --set <set> [--entry-point <e>] [--wait [--timeout <s>]] --path <flow_project> --output json
uip maestro flow eval run status <run_id> --set <set> --path <flow_project> --output json
uip maestro flow eval run results <run_id> --set <set> [--only-failed] [--verbose] [--export-format json|csv] --path <flow_project> --output json
uip maestro flow eval run list           --set <set> --path <flow_project> --output json
uip maestro flow eval run compare <run_a> --compare-to <run_b> --set <set> --path <flow_project> --output json
```

For full flag tables, evaluator type details, eval set JSON shape, and the run-safety rule, see the [Evaluate capability](../evaluate/CAPABILITY.md).

## uip maestro flow registry

Manage the local node type cache. No auth required for OOTB nodes; login for tenant-specific connector nodes.

```bash
uip maestro flow registry pull                             # refresh local cache (expires after 30 min)
uip maestro flow registry list --output json               # list all cached node types
uip maestro flow registry search <keyword> --output json   # search by name, tag, or category
uip maestro flow registry get <nodeType> --output json     # get full schema for a node type
```

The `Data.Node` object from `registry get` is what you paste into your `.flow` file's `definitions` array.

Run `uip maestro flow registry <subcommand> --help` for additional options (e.g., `--force`, `--filter`, `--connection-id`).

## Connector commands (binding and reference resolution)

See the relevant node guide in `nodes/` for connector CLI commands and the configuration workflow.

## Global options (all commands)

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options.
