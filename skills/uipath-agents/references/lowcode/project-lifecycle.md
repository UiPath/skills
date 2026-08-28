# Project Lifecycle and CLI Reference

Use `--output json` on every command whose output is parsed. Route all solution lifecycle operations through `uip solution`; never call Automation.Solutions REST endpoints directly.

## Authentication

```bash
uip login --output json          # Interactive OAuth login
uip login status --output json   # Check current auth state
```

See [../authentication.md](../authentication.md).

## Agent Commands

### `uip agent init`

Run from any directory to scaffold at a relative or absolute path. It creates `agent.json`, `entry-points.json`, `project.uiproj`, and default eval directories. Run `uip agent refresh` after edits to regenerate `entry-points.json` and `bindings_v2.json`.

```bash
uip agent init "<AGENT_NAME>" --output json
```

By default, projects are placed in solutions: inside a solution they register with the parent `.uipx`; outside one, the CLI creates `<Name>Solution/<Name>Solution.uipx` and places the project at `<Name>Solution/<Name>/`, returning `Data.AutoCreatedSolution`. `--skip-solution-registration` opts out of discovery, auto-scaffolding, and registration, uses the bare path, and returns `SolutionRegistration.Status: OptedOut`.

Options:

- `--conversational` — initialize a conversational agent; otherwise initialize an autonomous agent.
- `--model <model>` — select the model. Defaults are `gpt-5.4` for autonomous and `anthropic.claude-sonnet-4-5-20250929-v1:0` for conversational. Run `uip agent model list`, select per [model-selection-guide.md](model-selection-guide.md), and pass `--model` or edit `settings.model` after init.
- `--system-prompt <prompt>` — initial system prompt.
- `--force` — overwrite an existing non-empty directory.
- `--inline-in-flow` — scaffold an inline autonomous agent inside a flow project; inline conversational agents are not enabled.

#### Inline mode: `--inline-in-flow`

Treat `<path>` as the flow project directory. Create a UUID-named subdirectory containing `agent.json`, `flow-layout.json` (`{}`), and empty `evals/eval-sets/`, `features/`, and `resources/` directories. Do not create `entry-points.json`, `project.uiproj`, or evaluator files.

```bash
uip agent init "<FLOW_PROJECT_DIR>" --inline-in-flow --output json
```

Success output:

```json
{ "Result": "Success", "Code": "LowCodeAgentInitInline", "Data": { "Status": "Inline agent created inside flow project", "Path": "/path/to/FlowProject/<uuid>", "ProjectId": "<uuid>", "Model": "gpt-4o-2024-11-20" } }
```

After scaffolding, add a `uipath.agent.autonomous` node to the flow with `inputs.source = <ProjectId>` and no node instance `model` block. See [capabilities/inline-in-flow/inline-in-flow.md](capabilities/inline-in-flow/inline-in-flow.md).

### `uip agent guardrails list`

Run this mandatory first step before adding any built-in validator guardrail:

```bash
uip agent guardrails list --output json
```

Use only definitions with `Status: "Available"`. The response contains `Status` (`"Available"` or `"Unauthorised"`), `Validator`, `AllowedScopes`, `GuardrailStages` (scope-to-stage mapping), and `Parameters` (`Type`, `Id`, `Required`). If a validator is absent, it does not exist on the tenant. If `Status: "Unauthorised"`, do not add it and inform the user that they are not entitled to use guardrails.

### `uip agent validate`

Run this strict, read-only check after every bulk of agent edits; it writes no files.

```bash
uip agent validate [path] --output json
```

`path` defaults to the current directory. Run with `--inline-in-flow` to validate an inline agent and skip `entry-points.json` and `project.uiproj` checks.

Checks:

1. `agent.json`: `version === "1.1.0"`, type, UUID, settings including `mode`, messages, and `contentTokens` consistency.
2. `agent.json`/`entry-points.json` schema sync: properties and `required[]`.
3. `project.uiproj` (`ProjectType === "Agent"`).
4. Fail with `AgentValidationOutdated` when `storageVersion` is not latest; run `uip agent refresh`.
5. Latest Zod schema, eval-sets, evaluators (category/type constraints), and resource counts.
6. Dry-run derived-file generation; fail with `AgentValidationDrift` when generated `entry-points.json` or `bindings_v2.json` differs from disk; run `uip agent refresh`.

With `--inline-in-flow`, skip checks 2, 3, and the entry-points drift check. Run `uip agent refresh` before validation to apply migrations and regenerate derived files.

Success output:

```json
{ "Result": "Success", "Code": "AgentValidation", "Data": { "Status": "Valid", "Model": "...", "StorageVersion": "50.0.0", "Validated": { "agent": true, "resources": 2, "evalSets": 1, "evaluators": 2 } } }
```

Failure output:

```json
{ "Result": "Failure", "Code": "AgentValidationFailed", "Message": "Validation failed with N error(s)", "Data": { "Errors": ["agent.json → settings.mode: missing — must be \"standard\" or \"advanced\""] } }
```

### `uip agent refresh`

Run refresh to apply migrations and regenerate derived files; it runs static validation before writing and writes only when all checks pass.

```bash
uip agent refresh [path] --output json
```

It:

1. Runs all static validation checks.
2. Writes migrated `agent.json` and related files when needed.
3. Regenerates `entry-points.json` from `agent.json` `inputSchema`/`outputSchema`, preserving the existing `uniqueId`.
4. Regenerates `bindings_v2.json` from `resources/{ResourceName}/resource.json`, features, and guardrail escalations.

With `--inline-in-flow`, skip `entry-points.json`/`project.uiproj` checks and merge agent capability bindings into the parent flow project's `bindings_v2.json`. Run refresh, then validate. Refresh remains required after routine edits to synchronize `entry-points.json` and `bindings_v2.json`.

### Common refresh / validate errors

Resolve errors at the source:

| Error in `Data.Errors[]` | Cause | Fix |
|---|---|---|
| `resources/<Folder>/resource.json: folder must be named after the resource name "<Name>" (found "<Folder>")` | The folder must exactly equal the resource `name`, case- and whitespace-sensitive (`Count Sources`, not `CountSources`). | Rename the folder to match `name` verbatim, including spaces. |
| `resources/<Name>/resource.json: Invalid input` (no field path) | A required tool-resource field is missing or malformed; most commonly the required `guardrail` object is absent. Every tool resource requires it in schema V21+. | Add `"guardrail": { "policies": [] }`. If present, diff against a CLI-generated resource from `uip agent tool add`. |

### `uip agent memory`

These commands write `features/{FeatureName}/feature.json`; run refresh and validate afterward.

```bash
uip agent memory add SupportRecall \
  --memory-space "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json

uip agent memory list --path "<AGENT_PROJECT_DIR>" --output json
uip agent memory remove SupportRecall --path "<AGENT_PROJECT_DIR>" --output json

uip agent memory item add SupportRecall customer-tier gold \
  --memory-type episodic \
  --feedback-id "<FEEDBACK_ID>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json

uip agent memory item list SupportRecall --path "<AGENT_PROJECT_DIR>" --output json
uip agent memory item remove SupportRecall customer-tier --path "<AGENT_PROJECT_DIR>" --output json
```

See [capabilities/memory/memory.md](capabilities/memory/memory.md) for discovery, retrieval settings, memory item types, and troubleshooting.

### `uip agent debug`

Debug autonomous agents only; conversational agents are unsupported. Confirm user consent before running because debug uploads the enclosing solution to Studio Web and executes the agent for real, per [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 8.

```bash
uip agent debug <AGENT_PROJECT_DIR> --inputs '{"input":"..."}' --output json
```

The command uploads and runs in one step. It returns `Code: "AgentDebug"` with `Data.State`, `Data.Output`, and `Data.TraceId`. A `Faulted` run returns `Result: "Failure"` (exit 1); inspect it with `uip traces spans get <TraceId> --output json`. See [debug.md](debug.md).

## Solution Commands

```bash
uip solution init "<SOLUTION_NAME>" --output json
uip solution upload . --output json
uip solution pack "<SOLUTION_PATH>" "<OUTPUT_DIR>" -v "<VERSION>" --output json
uip solution publish "<PACKAGE_PATH>" --output json
```

Upload accepts a solution directory containing `.uipx`, a `.uipx`, or a `.uis`; pack produces a `.zip` and may run from any directory; publish requires login.

Deploy, activate, and uninstall:

```bash
uip solution deploy run \
  --name "<DEPLOYMENT_NAME>" \
  --package-name "<SOLUTION_NAME>" \
  --package-version "<VERSION>" \
  --folder-name "<FOLDER_NAME>" \
  --parent-folder-path "<ORCHESTRATOR_FOLDER>" \
  --output json

uip solution deploy activate "<DEPLOYMENT_NAME>" --output json
uip solution deploy uninstall "<DEPLOYMENT_NAME>" --output json
```

Deploy creates the folder, provisions resources, and activates in one call. Success returns `Status: DeploymentSucceeded` and `ActivationStatus: SuccessfulActivate`. Pass `--skip-activate` for legacy behavior, leaving `Inactive (Ready to activate)`. Run activate only after `--skip-activate` or to retry failed auto-activation after fixing its cause.

Bundle:

```bash
uip solution bundle . -d ./dist --output json
```

## Register Project with Solution

`uip agent init` registers projects inside a solution with the parent `.uipx`; outside one it creates `<Name>Solution/<Name>Solution.uipx` and nests at `<Name>Solution/<Name>/`, returning `Data.AutoCreatedSolution` (`{ Name, Path, SolutionFile }`) and `SolutionRegistration.Status: Registered`. Re-running is idempotent and reuses the `.uipx` (`AlreadyRegistered`). If a non-empty directory exists at the typed path, leave it untouched and place the project at `<Name>Solution/<Name>/`. `--skip-solution-registration` places the project at the bare path with `Status: OptedOut`.

Check `Data.SolutionRegistration.Status`:

- `Registered` / `AlreadyRegistered` — registered; done.
- `OptedOut` — intentionally skipped; no action needed.
- `Skipped` — unsafe discovery, such as multiple `.uipx` files or a project outside the solution; resolve and use the fallback.
- `Failed` — `.uipx` read/parse/write error; use the fallback.
- `NotInSolution` — no parent `.uipx` and auto-scaffold did not run; use the fallback if desired.

Use this fallback only for `Skipped`, `Failed`, or `NotInSolution`:

```bash
uip solution projects add "<AGENT_PROJECT_DIR>" [solutionFile] --output json
```

Run from the solution directory. The first argument is the project folder, not `--project-path`; the optional second argument is the `.uipx`. If omitted, search upward from the project path for the nearest `.uipx`.

## Resource Discovery

Run `uip solution resources list` as the first step of tool authoring. It queries Resource Catalog Service resources visible to the tenant and replaces `uip or folders list` and `uip or processes list`; it covers Action Center apps and Context Grounding indexes.

```bash
uip solution resources list --solution-folder <SOLUTION_DIR> --source local --output json
uip solution resources list --solution-folder <SOLUTION_DIR> --source remote [--kind <kind>] [--search <term>] --output json
```

`--source <all|local|remote>` defaults to `all`. Use `--kind` values `Queue`, `Asset`, `Bucket`, `Process`, `Connection`, `App`, and `Index`; use `--search` for case-insensitive substring matching. Use `--kind` and `--search` only with `--source remote`; with `local` or `all`, omit them and filter `.Data[]` client-side by `Kind` and `Name`.

Each output row contains:

```jsonc
{
  "Source": "Remote",
  "Key": "<guid>",
  "Name": "<display name>",
  "Kind": "Process",
  "Type": "agent",
  "Folder": "Shared/MyFolder",
  "FolderKey": "<folder-guid>"
}
```

`Source` is `Local` or `Remote`; `Key` is kind-specific (release key for `Process`, index GUID for `Index`, app id for `App`, connection id for `Connection`, and so on); `Folder` is fully qualified; `FolderKey` is the folder GUID and refresh writes it into `debug_overwrites.json`. Treat `resources list` as identification only: it does not return argument schemas, action schemas, data source types, authentication details, package versions, or feed ids. For `Process` and `Index`, run `uip solution resources get <KEY> --output json` and read `Data.spec`; for other kinds, use the kind-specific capability files.

Kind-specific `Type` values:

| Kind | `Type` values | Meaning |
|---|---|---|
| `Process` | `process` | RPA (XAML workflow) |
| `Process` | `agent` | Low-code / coded agent |
| `Process` | `api` | API workflow |
| `Process` | `processOrchestration` | Agentic process |
| `Process` | `webApp` | Deployed Apps; ignore for runnable tools and use `--kind App` for escalations |
| `App` | `Workflow Action` | Action Center app backing escalations |
| `App` | `Coded` / `CodedAction` | Coded Apps; unsupported as escalations today |
| `Connection` | `uipath-<connector-key>` | Integration Service connection; `Type` is the connector key |
| `Bucket` | `orchestratorBucket` | Orchestrator storage bucket |

## End-to-End Example — New Standalone Agent

### Step 0 — Resolve `uip` binary

```bash
which uip || npm root -g 2>/dev/null | xargs -I{} echo {}/uip/bin/uip
```

If absent, run `npm install -g @uipath/cli`.

### Step 1 — Check login status

Run:

```bash
uip login status --output json
```

If not logged in, prompt the user to run `uip login`.

### Step 2 — Create solution and scaffold agent

Run from one working directory and pass paths explicitly:

```bash
uip solution init "<SOLUTION_NAME>" --output json
uip agent init "<SOLUTION_NAME>/<AGENT_NAME>" --output json
```

Confirm `Data.SolutionRegistration.Status`: `Registered` or `AlreadyRegistered` means done. Run the fallback only for `NotInSolution`, `Skipped`, or `Failed`; `OptedOut` means registration was intentionally skipped.

```bash
uip solution projects add "<SOLUTION_NAME>/<AGENT_NAME>" --output json
```

Explicit `uip solution init` is optional. `uip agent init "<AGENT_NAME>"` outside a solution auto-scaffolds `<AGENT_NAME>Solution/<AGENT_NAME>/` and returns `Data.AutoCreatedSolution`; use explicit solution creation when the solution name should differ from the agent name. The fallback finds the nearest `.uipx` upward from the agent path.

### Step 3 — Configure agent.json

Read [agent-definition.md](agent-definition.md); schemas differ for autonomous and conversational agents.

1. Set `settings.model`: run `uip agent model list`, select per [model-selection-guide.md](model-selection-guide.md), and override stale scaffold defaults (`gpt-5.4` autonomous; `anthropic.claude-sonnet-4-5-20250929-v1:0` conversational).
2. Set `settings.temperature` (use 0 for deterministic behavior).
3. Write the system prompt in `messages[0].content`, rebuild `contentTokens`, and structure it per [prompting/agent-prompting-guide.md](prompting/agent-prompting-guide.md): skeleton, tool-call criteria, and output contract; do not leave a placeholder.
4. For autonomous agents, write `messages[1].content` using `{{input.fieldName}}` and rebuild `contentTokens`. For conversational agents, leave the user message template blank; actual conversation messages supply it.

### Step 4 — Define input/output schemas

1. Add fields to `agent.json` `inputSchema` and `outputSchema`; `outputSchema` changes apply only to autonomous agents.
2. Mirror them in `entry-points.json`.
3. Run `uip agent refresh "<SOLUTION_NAME>/<AGENT_NAME>" --output json`.
4. Run `uip agent validate "<SOLUTION_NAME>/<AGENT_NAME>" --output json`.

### Step 5 — Publish to Studio Web or deploy to Orchestrator

Ask the user before proceeding. Studio Web is for visual editing and sharing; Orchestrator is for production and requires explicit request.

```bash
uip solution upload . --output json
```

```bash
uip solution pack . ./dist -v "1.0.0" --output json
uip solution publish ./dist/<SOLUTION_NAME>_1.0.0.zip --output json
uip solution deploy run --name "<NAME>" --package-name "<SOLUTION_NAME>" --package-version "1.0.0" --output json
```

## Versioning

Use semantic versioning `MAJOR.MINOR.PATCH`:

```bash
uip solution pack ./MySolution ./output -v "1.2.0" --output json
uip solution publish ./output/MySolution_1.2.0.zip --output json
uip solution packages list --output json
```

- `PATCH`: bug fixes and prompt tweaks.
- `MINOR`: new tools or agents.
- `MAJOR`: breaking I/O-schema changes.

## Environment Promotion

```bash
uip solution pack ./MySolution ./output -v "2.0.0" --output json
uip solution publish ./output/MySolution_2.0.0.zip --output json
uip solution deploy run \
  --name "MySolution-Prod" \
  --package-name "MySolution" \
  --package-version "2.0.0" \
  --folder-name "MySolution" \
  --parent-folder-path "Production" \
  --output json
```

## Quick Reference

| Task | Command | Run From | Terminal states |
|---|---|---|---|
| Login check | `uip login status --output json` | Any directory | — |
| Create solution | `uip solution init "<NAME>" --output json` | Any directory | — |
| Scaffold agent | `uip agent init "<NAME>" --output json` | Any directory; auto-scaffolds `<NAME>Solution/` outside a solution | — |
| Scaffold inline agent | `uip agent init "<FLOW_PROJECT_DIR>" --inline-in-flow --output json` | Any directory | — |
| Verify registration | Check `Data.SolutionRegistration.Status`; `Registered` / `AlreadyRegistered` = done; `OptedOut` = `--skip-solution-registration` | Solution directory | — |
| Register fallback | `uip solution projects add "<PATH>" --output json` for `Skipped` / `Failed` / `NotInSolution` | Solution directory | — |
| Refresh | `uip agent refresh [path] --output json` | Agent directory or any directory with path | — |
| Validate | `uip agent validate [path] --output json` | Agent directory or any directory with path | — |
| Debug | `uip agent debug <AgentDir> --inputs '{...}' --output json` | Agent directory | `Successful`, `Faulted`, `Stopped` |
| Add memory space | `uip agent memory add <FeatureName> --memory-space <Name> --folder-path <Folder> --path <AgentDir> --output json` | Any directory | Writes `features/<FeatureName>/feature.json`; refresh/validate afterward |
| Seed memory item | `uip agent memory item add <FeatureName> <key> <value> --memory-type episodic --feedback-id <FEEDBACK_ID> --path <AgentDir> --output json` | Any directory | Updates existing item with same key |
| List guardrails | `uip agent guardrails list --output json` | Any directory | — |
| Discover resources | `uip solution resources list --kind <Kind> --source remote [--search <term>] --output json` | Solution directory | — |
| Refresh resources | `uip solution resources refresh --output json` | Solution directory | — |
| Add resource | `uip solution resources add --source local\|remote --kind <Kind> --name <NAME> [--folder-path <FOLDER>] --output json` | Solution directory | Idempotent on `(kind, name, folder)` for local and on key for remote |
| Remove resource | `uip solution resources remove <KEY> --output json` | Solution directory | Offline; does not touch `bindings_v2.json` |
| Edit resource spec | `uip solution resources edit <KEY> --patch '{...}' --output json` | Solution directory | Only command that mutates an existing resource; `refresh` never overwrites. Unknown/reference/read-only properties are silently ignored; JSON is the only input and types are preserved verbatim |
| Upload | `uip solution upload . --output json` | Solution directory | — |
| Pack | `uip solution pack . ./dist -v "1.0.0" --output json` | Solution directory | — |
| Publish | `uip solution publish ./dist/<PKG>.zip --output json` | Any directory | — |
| Deploy | `uip solution deploy run --name ... --output json` | Any directory | `DeploymentSucceeded`, `DeploymentFailed`, `ValidationFailed` |
| Activate | `uip solution deploy activate "<NAME>" --output json` | Any directory | `SuccessfulActivate`, `FailedActivate` |
| Uninstall | `uip solution deploy uninstall "<NAME>" --output json` | Any directory | `SuccessfulUninstall`, `FailedUninstall` |
| Deploy status | `uip solution deploy status <pipeline-deployment-id> --output json` | Any directory | — |
| List deployments | `uip solution deploy list --output json` | Any directory | — |