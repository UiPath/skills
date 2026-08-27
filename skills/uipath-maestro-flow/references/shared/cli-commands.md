# uip maestro flow — CLI Command Reference

All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use.

> For node and edge commands (`node add/remove/list/configure`, `edge add/remove/list`), see the [Author CLI editing strategy](../author/references/editing-operations-cli.md). This file covers project setup, validation, registry, debug, and publishing commands.

<!--skill-flavor:flow-init-command:start-->
## uip maestro flow init

Scaffold a new Flow project directory. Prefer creating the solution first so its name matches the project name (see the [Author greenfield journey — Step 2](../author/references/greenfield.md)):

```bash
uip solution init "<SolutionName>" --output json
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName> --output json
```

Confirm `Data.SolutionRegistration.Status`: `Registered`, `AlreadyRegistered`, `OptedOut`, `Skipped`, `Failed`, or `NotInSolution`. Inside a solution, `flow init` auto-registers the project with the parent `.uipx`. Outside one, it creates `<ProjectName>Solution/<ProjectName>Solution.uipx`, nests the project, and adds `Data.AutoCreatedSolution`. `--skip-solution-registration` opts out with status `OptedOut`; do not manually wire an intentionally opted-out project. Manually wire `Skipped`, `Failed`, or the rare `NotInSolution`:

```bash
uip solution projects add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

Creates `<ProjectName>/` with `project.uiproj`, `<ProjectName>.flow`, `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` inside the solution directory.
<!--skill-flavor:flow-init-command:end-->

## uip maestro flow validate

Validate a `.flow` file locally—no auth or network. Run:

```bash
uip maestro flow validate <path/to/file.flow>
uip maestro flow validate <path/to/file.flow> --output json
uip maestro flow validate <path/to/file.flow> --verbose --output json
uip maestro flow validate <path/to/file.flow> --governance --output json
```

Checks JSON parsing; required fields, including `targetPort` on edges; matching `type:typeVersion` entries in `definitions`; existing node `id` references for `sourceNodeId`/`targetNodeId`; and unique node and edge `id`s. Exit code 0 = valid, 1 = invalid.

`--governance` checks agent nodes against organization policies fetched from the platform and requires `uip login`. If governance data cannot be fetched, the command fails. Omit it for local-only schema validation.

## uip maestro flow format

Run `uip maestro flow format` after validation and before publishing or debugging; stale or hand-written `layout` data can render as misshapen rectangles in Studio Web.

```bash
uip maestro flow format <path/to/file.flow>
uip maestro flow format <path/to/file.flow> --output json
```

Format only layout: arrange nodes horizontally left-to-right while anchoring to the leftmost node's original position; set `size` to canvas shape (`shape: rectangle` inline agents: `{ "width": 288, "height": 96 }`; loops/groups: `{ "width": 560, "height": 320 }`; everything else, including referenced `uipath.core.agent.<guid>`: `{ "width": 96, "height": 96 }`); preserve sticky-note custom sizes; recurse into subflows and rewrite `subflows[<id>].layout`; and backfill missing `position`/`size`. Do not modify node logic, edges, definitions, or variables. JSON output reports `Data.NodesTotal`, `Data.EdgesTotal`, `Data.NodesRepositioned`, `Data.NodesResized`, and `Data.SubflowsTidied`.

## uip maestro flow pack

Pack a Flow project into a `.nupkg` for Orchestrator deployment:

```bash
uip maestro flow pack <project-path> <OutputDir>
uip maestro flow pack <project-path> <OutputDir> --version 2.0.0
uip maestro flow pack <project-path> <OutputDir> --output json
```

Require `content/package-descriptor.json` and `content/operate.json`. Output is `<Name>.flow.Flow.<version>.nupkg`.

<!--skill-flavor:upload-pack-note:start-->
> **Note:** `pack` + `uip solution publish` deploys directly to Orchestrator — the user cannot visualize or edit the flow in Studio Web via this path. Only use this when the user explicitly asks to deploy to Orchestrator. The default publish path is `uip solution upload` (see below). See [uipath-solution](/uipath:uipath-solution) for `solution publish` commands.
<!--skill-flavor:upload-pack-note:end-->

## uip solution resources refresh

<!--skill-flavor:upload-refresh-prereq:start-->
Always run `uip solution resources refresh` before `uip solution upload` or `uip maestro flow debug`. It re-scans solution projects and syncs resource declarations (connections, processes, queues, etc.) from `bindings_v2.json`, creating bindings not yet in the solution and importing matching Orchestrator resources.
<!--skill-flavor:upload-refresh-prereq:end-->

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
```

<!--skill-flavor:upload-solution-dir-note:start-->
`<SolutionDir>` is the solution directory containing the `.uipx` file. The command has no positional solution argument; omit `--solution-folder` only from the solution root.
<!--skill-flavor:upload-solution-dir-note:end-->

## uip solution resources add / remove / edit

Use atomic mutations when adding, deleting, or changing one resource without scanning every project's bindings:

```bash
uip solution resources add --source local --kind <Kind> --name <Name> --output json
uip solution resources add --source remote --kind <Kind> --name <Name> --folder-path <FolderPath> --output json
uip solution resources remove <KEY> --output json
uip solution resources edit <KEY> --patch '{"maxNumberOfRetries":5}' --output json
echo '{"slaInHours":"4"}' | uip solution resources edit <KEY> --patch - --output json
```

`add` is idempotent on `(kind, name, folder)` for local resources and on resource key for remote resources; retries return `Status: "Unchanged"`. `edit` alone mutates an existing resource spec; `refresh` never overwrites and skips resources already in the solution. These commands do not modify `bindings_v2.json`; a later `refresh` re-imports a still-bound resource. See [uipath-solution Step 9–11](/uipath:uipath-solution).

<!--skill-flavor:upload-command-section:start-->
## uip solution upload

Upload a solution directly to Studio Web; require `uip login`:

```bash
uip solution upload <SolutionDir> --output json
```

Pass the solution directory containing the `.uipx` file, or `.` from its root. From a nested project, pass the absolute solution root or `..`; do not pass the solution name again. This uploads to Studio Web for browser visualization, inspection, editing, and publishing.

> **This is the default publish path.** When the user asks to "publish" without specifying where, run `uip solution upload <SolutionDir>` and share the resulting URL.
<!--skill-flavor:upload-command-section:end-->

## uip maestro flow debug

Debug in the cloud through Studio Web + Orchestrator; require `uip login`. Always run `uip maestro flow validate` first, and run `uip solution resources refresh` before debugging:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --attachment <variableId>=<localPath> \
  --attachment <variableId>=<localPath>
```

Pass the project directory containing `project.uiproj` (`<ProjectName>/` from the solution root, or `.` inside it). Use `--inputs` for a JSON object of flow input arguments. Repeat `--attachment <variableId>=<localPath>` to upload files for file-typed inputs; a bare path is rejected.

<a id="attachment-preflight"></a>

#### Pre-flight: `--attachment` binding

The CLI does not validate `<variableId>`; a mismatch can fault at runtime. Read `<flow>.flow`, inspect `variables.globals[]`, and use only entries with `direction:"in"` and `type:"file"`. If none exist, add `{ "id": "<variableId>", "direction": "in", "type": "file", "triggerNodeId": "<triggerId>" }`. In a Script node, read the uploaded name as `$vars.{triggerNodeId}.output.{id}.FullName`. See [variables-and-expressions.md — Runtime shape of a `file` variable](variables-and-expressions.md#file-input).

Run `uip maestro flow debug --help` for other options.

### Reporting the run back to the user

Parse the Studio Web URL and `instanceId` from JSON output, typically `Data.studioWebUrl` and `Data.instanceId`, and report them as the first two lines:

```text
Studio Web URL: <url>
Instance ID: <instanceId>

<run status, node traces, errors, etc.>
```

If either is absent, output its label with `<not returned by CLI>`. Do not place these lines below the run summary.

## uip maestro flow process

Manage deployed Flow processes; require `uip login`:

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
uip maestro flow process run <process-key> <folder-key> --output json \
  --attachment <variableId>=<localPath>
```

`--attachment` must match a `variables.globals[]` entry with `direction:"in"` and `type:"file"`; repeat it for multiple files. If `--inputs` and `--attachment` collide, attachment wins and the CLI logs an override warning. `--validate` accepts pre-uploaded attachment references for file-typed slots although their nominal type is `string`. Run `uip maestro flow process --help` for other subcommands.

## uip maestro flow job

Monitor jobs; require `uip login`:

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

## uip maestro flow hitl add

Add a Human-in-the-Loop QuickForm node to an existing `.flow`; the command writes node JSON, adds the definition once, and updates `variables.nodes`:

```bash
uip maestro flow hitl add <path/to/file.flow> --output json
uip maestro flow hitl add <path/to/file.flow> --label "<label>" --priority High --output json
uip maestro flow hitl add <path/to/file.flow> --assignee <email-or-group> --output json
uip maestro flow hitl add <path/to/file.flow> --label "<label>" --priority High --assignee <email-or-group> \
  --schema '{"inputs":[{"name":"invoiceId","binding":"fetchInvoice.output.invoiceId"}],"outputs":[{"name":"decision","required":true}],"outcomes":[{"name":"Approve"},{"name":"Reject"}]}' \
  --position 474,144 --output json
```

| Flag | Description | Default |
|------|-------------|---------|
| `--label <text>` | Display label | `"Human in the Loop"` |
| `--priority Low\|Medium\|High` | Action Center priority | `Low` |
| `--assignee <email-or-group>` | User email (`staticEmail`) or group (`staticGroupName`) | group (unassigned) |
| `--schema <json>` | Form fields and outcomes | empty form |
| `--position <x,y>` | Canvas position | `0,0` |

`--schema` supports:

```json
{
  "inputs": [{ "name": "invoiceId", "binding": "fetchInvoice.output.invoiceId" }, { "name": "amount", "type": "number", "binding": "fetchInvoice.output.amount" }],
  "outputs": [{ "name": "decision", "required": true }, { "name": "notes" }],
  "inOuts": [{ "name": "emailBody" }],
  "outcomes": [{ "name": "Approve" }, { "name": "Reject" }]
}
```

`inputs` are read-only context fields and use the full `$vars` binding path; `outputs` are human-filled and default `variable` to the field name; `inOuts` are editable pre-filled fields; `outcomes` are button labels, with the first primary and later outcomes ending the flow unless rewired.

Success output:

```json
{ "Result": "Success", "Code": "HitlNodeAdded", "Data": { "NodeId": "invoiceReview1", "NodeType": "uipath.human-in-the-loop.quick-form", "Label": "Invoice Review", "DefinitionAdded": true } }
```

After adding, wire the `completed` port; an unwired `completed` blocks the flow. See the [Author HITL plugin reference](../author/references/plugins/hitl/impl.md).

## uip maestro flow instance / uip maestro flow incident

See the [Diagnose troubleshooting guide](../diagnose/references/troubleshooting-guide.md) for the diagnostic workflow and `instance`/`incident` command reference.

## uip maestro flow node / uip maestro flow edge

See the [Author CLI editing strategy](../author/references/editing-operations-cli.md) for `node add/remove/list/configure` and `edge add/remove/list` syntax, flags, and auto-managed behaviors.

## uip maestro flow eval

Evaluation surface: evaluator, eval-set, and data-point CRUD; Studio Web run start/status/results/list/compare. Local CRUD needs no login; `eval run *` requires `uip login` and a Flow solution already in Studio Web.
<!--skill-flavor:upload-safety-eval-surface-note:start-->
**Never auto-run `uip solution upload` to satisfy the Studio Web prerequisite** — see [evaluate/references/upload-safety.md](../evaluate/references/upload-safety.md).
<!--skill-flavor:upload-safety-eval-surface-note:end-->

```bash
uip maestro flow eval add <name> --set <set> [flags] --output json
uip maestro flow eval list --set <set> --path <flow_project> --output json
uip maestro flow eval remove <id> --set <set> --path <flow_project> --output json
uip maestro flow eval set add <name> [--evaluators <refs>] [--entry-point <id>] --path <flow_project> --output json
uip maestro flow eval set list --path <flow_project> --output json
uip maestro flow eval set remove <id> --path <flow_project> --output json
uip maestro flow eval evaluator add <name> --type <type> [--model <m>] [--target-key <k>] [--prompt <p>] --path <flow_project> --output json
uip maestro flow eval evaluator list --path <flow_project> --output json
uip maestro flow eval evaluator remove <id> --path <flow_project> --output json
uip maestro flow eval run start <name> --set <set> [--entry-point <e>] [--wait [--timeout <s>]] --path <flow_project> --output json
uip maestro flow eval run status <run_id> --set <set> --path <flow_project> --output json
uip maestro flow eval run results <run_id> --set <set> [--only-failed] [--verbose] [--export-format json|csv] --path <flow_project> --output json
uip maestro flow eval run list --set <set> --path <flow_project> --output json
uip maestro flow eval run compare <run_a> --compare-to <run_b> --set <set> --path <flow_project> --output json
```

Evaluators: `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `strict-json`, `trajectory`, `trajectory-simulation`. For full flag tables, evaluator details, eval-set JSON shape, and run-safety rule, see the [Evaluate capability](../evaluate/CAPABILITY.md).

## uip maestro flow registry

Manage the local node-type cache. No auth is required for OOTB nodes; login is required for tenant-specific connector nodes:

```bash
uip maestro flow registry pull
uip maestro flow registry list --output json
uip maestro flow registry search <keyword> --output json
uip maestro flow registry get <node-type> --output json
```

The cache expires after 30 minutes. `registry search` returns a flat `Data` array with PascalCase fields. Use its `NodeType` with `registry get` and later `node add`.

```json
{ "Data": [{ "NodeType": "uipath.connector.uipath-salesforce-sfdc.list-records", "Category": "connector.196536", "DisplayName": "List Records", "Description": "(Salesforce) List records in Salesforce", "Version": "1.0.0", "Tags": "connector, activity", "AvailableOnTenant": true }] }
```

Treat `AvailableOnTenant` as a usability gate: `true` permits `registry get <NodeType>` or `node add <NodeType>`; `false` means the node is not enabled or available for the tenant. Do not use unsupported flags such as `--include-unavailable`; choose an enabled alternative, use `--local` for in-solution resources, or report unavailability.

`registry get` returns `Data.Node` verbatim for the `.flow` `definitions` array. Preserve its manifest casing, predominantly camelCase (`nodeType`, `inputDefinition`, `supportsErrorHandling`, `form`); filter with `--output-filter "Node.inputDefinition"`, not `Node.InputDefinition`.

Run `uip maestro flow registry <subcommand> --help` for additional options such as `--force`, `--filter`, and `--connection-id`.

## Connector commands (binding and reference resolution)

See the relevant guide in `nodes/` for connector CLI commands and configuration workflow.

## Global options (all commands)

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover available options.