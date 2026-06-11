# Project Lifecycle and CLI Reference

All `uip` commands for low-code agent and solution lifecycle. Use `--output json` on all commands when parsing output.

## Authentication

```bash
uip login --output json          # Interactive OAuth login
uip login status --output json   # Check current auth state
```

See [../authentication.md](../authentication.md) for the full guide.

## Agent Commands

### `uip agent init`

Scaffold a new agent project at the given path.

```bash
uip agent init "<AGENT_NAME>" --output json
```

The `<path>` argument is relative or absolute; the command can run from any directory. Creates agent.json, entry-points.json, project.uiproj, and default eval directories inside the target path. Run `uip agent refresh` after editing to regenerate `entry-points.json` and `bindings_v2.json`.

**Options:**
- `--model <model>` — LLM model to use (default: `gpt-4o-2024-11-20`). This default is stale; override it post-init — discover current tenant models with `uip agent model list` and select per [model-selection-guide.md](model-selection-guide.md). Pass `--model` at init or edit `settings.model` after.
- `--system-prompt <prompt>` — Initial system prompt for the agent
- `--force` — Overwrite existing directory if non-empty
- `--inline-in-flow` — Scaffold an inline agent inside a flow project (see below)

#### Inline mode: `--inline-in-flow`

When `--inline-in-flow` is passed, the `<path>` argument is treated as the flow project directory. The command creates a UUID-named subdirectory containing `agent.json`, `flow-layout.json` (`{}`), and empty `evals/eval-sets/`, `features/`, `resources/` directories. No `entry-points.json`, `project.uiproj`, or evaluator files are created.

```bash
uip agent init "<FLOW_PROJECT_DIR>" --inline-in-flow --output json
```

**Success output:**
```json
{ "Result": "Success", "Code": "LowCodeAgentInitInline", "Data": { "Status": "Inline agent created inside flow project", "Path": "/path/to/FlowProject/<uuid>", "ProjectId": "<uuid>", "Model": "gpt-4o-2024-11-20" } }
```

After scaffolding, add a `uipath.agent.autonomous` node to the flow with `inputs.source = <ProjectId>` and no node instance `model` block. See [capabilities/inline-in-flow/inline-in-flow.md](capabilities/inline-in-flow/inline-in-flow.md) for the full structure.

### `uip agent guardrails list`

List available guardrail validator definitions with their allowed scopes, stages, and parameters.

```bash
uip agent guardrails list --output json
```

Returns an array of validator definitions. Each entry contains:
- `Status` — `"Available"` (licensed, ready to use) or `"Unauthorised"` (user not entitled to use guardrails)
- `Validator` — the `validatorType` string to use in `builtInValidator` guardrails
- `AllowedScopes` — valid values for `selector.scopes`
- `GuardrailStages` — object mapping each scope to its valid execution stages
- `Parameters` — array of parameter definitions (`Type`, `Id`, `Required`)

**Mandatory first step** before adding any built-in validator guardrail. Only use validators with `Status: "Available"`. If a validator is missing from the list, it does not exist on this tenant. If `Status: "Unauthorised"`, user is not entitled to use guardrails — do not add the guardrail, inform user accordingly.

### `uip agent validate`

**Read-only** check of agent project structure and schema. Does not write any files. Run after every bulk of agent edits to catch errors early.

```bash
uip agent validate [path] --output json
```

`path` is optional — defaults to the current directory.

**Options:**
- `--inline-in-flow` — Validate an inline agent inside a flow project. Skips `entry-points.json` and `project.uiproj` checks.

**What it does (standalone mode):**
1. Checks `agent.json` structure: `version === "1.1.0"`, type, UUID, settings (including `mode`), messages, contentTokens consistency.
2. Verifies schema sync between `agent.json` and `entry-points.json` (properties + required[]).
3. Validates `project.uiproj` (`ProjectType === "Agent"`).
4. Storage-version gate — fails with `AgentValidationOutdated` if `storageVersion` is not at the latest. Run `uip agent refresh` to migrate.
5. Validates `agent.json` against the latest Zod schema, eval-sets, evaluators (category/type constraints), and counts resources.
6. Dry-run derived-files generation — compares generated `entry-points.json` and `bindings_v2.json` against on-disk files. Fails with `AgentValidationDrift` if they are out of sync. Run `uip agent refresh` to regenerate.

**Does NOT write files.** Strict read-only. Run `uip agent refresh` before validate to apply migrations and regenerate derived files.

**With `--inline-in-flow`:** Steps 2, 3, and entry-points drift check are skipped.

**Success output:**
```json
{ "Result": "Success", "Code": "AgentValidation", "Data": { "Status": "Valid", "Model": "...", "StorageVersion": "50.0.0", "Validated": { "agent": true, "resources": 2, "evalSets": 1, "evaluators": 2 } } }
```

**Failure output:**
```json
{ "Result": "Failure", "Code": "AgentValidationFailed", "Message": "Validation failed with N error(s)", "Data": { "Errors": ["agent.json → settings.mode: missing — must be \"standard\" or \"advanced\""] } }
```

### `uip agent refresh`

Applies pending schema migrations and regenerates derived files (`entry-points.json`, `bindings_v2.json`). Runs static validation before writing anything — files are only written if all checks pass.

```bash
uip agent refresh [path] --output json
```

**What it does:**
1. Runs all static validation checks.
2. Writes migrated `agent.json` (and related files) to disk if migration is needed.
3. Regenerates `entry-points.json` from `agent.json` inputSchema/outputSchema (preserving the existing `uniqueId`).
4. Regenerates `bindings_v2.json` from `resources/{ResourceName}/resource.json` files, features, and guardrail escalations.

**With `--inline-in-flow`:** Skips `entry-points.json`/`project.uiproj` checks. Agent capability bindings are merged into the parent flow project's `bindings_v2.json`.

**Workflow:** run `uip agent refresh` to apply writes and regenerate derived files, then `uip agent validate` to verify the project is clean. For routine edits with no schema migration pending, refresh is still needed to keep `entry-points.json` and `bindings_v2.json` in sync.

### `uip agent memory`

Manage low-code agent memory space features and seed items. These commands write `features/{FeatureName}/feature.json`; run refresh and validate afterwards to regenerate bindings.

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

For discovery, retrieval settings, memory item types, and troubleshooting, see [capabilities/memory/memory.md](capabilities/memory/memory.md).

## Solution Commands

### Create Solution

```bash
uip solution init "<SOLUTION_NAME>" --output json
```

### Register Project with Solution

`uip agent init` **auto-registers** the project with the parent `.uipx` when run from inside a solution directory (pass `--skip-solution-registration` to skip auto-registration). Verify via `Data.SolutionRegistration.Status` in the `agent init` response. The full set of statuses:

- `Registered` / `AlreadyRegistered` — registered (added now / already present). **You are done.**
- `OptedOut` — `--skip-solution-registration` was passed; registration was intentionally skipped. No action needed (register later with the fallback if you change your mind).
- `NotInSolution` — no parent `.uipx` was found (`init` ran outside a solution). Use the fallback if you want it in a solution.
- `Skipped` — a candidate solution was found but registration wasn't safe (e.g. multiple `.uipx`, or project outside the solution dir). Resolve, then use the fallback.
- `Failed` — registration was attempted but errored (`.uipx` read/parse/write). Use the fallback.

```bash
# Fallback — when Status is NotInSolution / Skipped / Failed (not needed for OptedOut).
uip solution project add "<AGENT_PROJECT_DIR>" [solutionFile] --output json
```

Run from the solution directory. The first argument is the path to the agent project folder (positional, not `--project-path`). The optional second argument is the path to the `.uipx` solution file — if omitted, the CLI searches up from the project path to find the nearest `.uipx` automatically.

### Upload to Studio Web

Upload sends the solution to Studio Web. Accepts a solution directory (containing `.uipx`), a `.uipx` file, or a `.uis` file.

```bash
uip solution upload . --output json
```

### Pack Solution for Orchestrator

```bash
uip solution pack "<SOLUTION_PATH>" "<OUTPUT_DIR>" -v "<VERSION>" --output json
```

Produces a `.zip` package. Run from any directory.

### Publish Package to Orchestrator

```bash
uip solution publish "<PACKAGE_PATH>" --output json
```

Publishes the `.zip` to Orchestrator. Requires login.

### Deploy Solution

```bash
uip solution deploy run \
  --name "<DEPLOYMENT_NAME>" \
  --package-name "<SOLUTION_NAME>" \
  --package-version "<VERSION>" \
  --folder-name "<FOLDER_NAME>" \
  --parent-folder-path "<ORCHESTRATOR_FOLDER>" \
  --output json
```

Creates the folder, provisions resources, and activates the deployment in one call. A successful run returns `Status: DeploymentSucceeded` and `ActivationStatus: SuccessfulActivate`. Pass `--skip-activate` to opt out of auto-activation (legacy behaviour — leaves the deployment in `Inactive (Ready to activate)`).

### Activate Existing Deployment

Run only when `--skip-activate` was passed during deploy, or to retry a failed auto-activation after fixing the underlying cause (e.g. missing config).

```bash
uip solution deploy activate "<DEPLOYMENT_NAME>" --output json
```

### Uninstall Deployment

```bash
uip solution deploy uninstall "<DEPLOYMENT_NAME>" --output json
```

### Bundle for Upload

```bash
uip solution bundle . -d ./dist --output json
```

## Resource Discovery

`uip solution resource list` queries the Resource Catalog Service for all resources visible to the tenant and returns a compact JSON list. Use it as the first step of any tool-authoring flow — it replaces `uip or folders list` and `uip or processes list`, and covers Action Center apps and Context Grounding indexes too.

Two supported invocations:

```bash
# Local (in-solution): --kind and --search not allowed.
uip solution resource list [solutionPath] --source local --output json

# Remote (Orchestrator / RCS): --kind and --search supported.
uip solution resource list [solutionPath] --source remote [--kind <kind>] [--search <term>] --output json
```

**Flags:**
- `--source <all|local|remote>` — default `all`. `local` lists resources already in the solution; `remote` queries Orchestrator / RCS.
- `--kind <kind>` — filter by resource kind. Supported: `Queue`, `Asset`, `Bucket`, `Process`, `Connection`, `App`, `Index`. **Only valid with `--source remote`.**
- `--search <term>` — substring match on the resource name (case-insensitive). **Only valid with `--source remote`.**

> **`--kind` and `--search` only work with `--source remote`.** With `--source local` or `--source all` (default), both flags must be omitted — list everything and filter `.Data[]` client-side by `Kind` and `Name`.

**Output row:**

```jsonc
{
  "Source": "Remote",              // "Local" (already in this solution) or "Remote"
  "Key": "<guid>",                 // kind-specific: release Key (Process), index GUID (Index), app id (App), connection id (Connection), ...
  "Name": "<display name>",
  "Kind": "Process",               // matches --kind
  "Type": "agent",                 // subtype: process/agent/api/processOrchestration/webApp for Process; Workflow Action/Coded/CodedAction for App; connector key for Connection; orchestratorBucket for Bucket
  "Folder": "Shared/MyFolder",     // fully-qualified folder path
  "FolderKey": "<folder-guid>"     // folder GUID — refresh writes it into debug_overwrites.json
}
```

**Kind-specific Type values:**

| Kind | `Type` values | What it means |
|------|---------------|---------------|
| `Process` | `process` | RPA (XAML workflow) |
| `Process` | `agent` | Low-code / coded agent |
| `Process` | `api` | API workflow |
| `Process` | `processOrchestration` | Agentic process |
| `Process` | `webApp` | Deployed Apps — ignore when looking for runnable tools; use `--kind App` for escalations |
| `App` | `Workflow Action` | Action Center app (backs escalations) |
| `App` | `Coded` / `CodedAction` | Coded Apps — not supported as escalations today |
| `Connection` | `uipath-<connector-key>` | Integration Service connection — the `Type` IS the connector key |
| `Bucket` | `orchestratorBucket` | Orchestrator storage bucket |

**What `resource list` does not return:** argument schemas, action schemas, data source types, authentication details, package versions, or feed ids. For `Process` and `Index` resources, follow up with `uip solution resource get <KEY> --output json` and read `Data.spec` for the full configuration. For other kinds (`App`, `Connection`, `Bucket`), see the kind-specific capability files. `resource list` is the identification step — it tells you *that* a resource exists and *where*.

## End-to-End Example — New Standalone Agent

The canonical happy-path walkthrough for creating, configuring, validating, and deploying a new standalone agent.

### Step 0 — Resolve `uip` binary

```bash
which uip || npm root -g 2>/dev/null | xargs -I{} echo {}/uip/bin/uip
```

If not found: `npm install -g @uipath/cli`

### Step 1 — Check login status

```bash
uip login status --output json
```

If not logged in, prompt the user to run `uip login`.

### Step 2 — Create solution and scaffold agent

All commands run from the same working directory — no `cd` needed. Pass paths explicitly.

```bash
uip solution init "<SOLUTION_NAME>" --output json
# `agent init` auto-registers the project in the parent `.uipx` because
# the agent path lives inside the solution directory. Confirm via
# `Data.SolutionRegistration.Status` in the response (`Registered` or
# `AlreadyRegistered`).
uip agent init "<SOLUTION_NAME>/<AGENT_NAME>" --output json
# (fallback only — run if Data.SolutionRegistration.Status is `NotInSolution` / `Skipped` / `Failed`;
#  `OptedOut` means `--skip-solution-registration` was passed and registration was skipped on purpose)
# uip solution project add "<SOLUTION_NAME>/<AGENT_NAME>" --output json
```

When the fallback is needed, `uip solution project add` automatically finds the nearest `.uipx` by searching up from the agent path.

### Step 3 — Configure agent.json

Read [agent-definition.md](agent-definition.md) for the full schema.

1. Set `settings.model` — discover with `uip agent model list`, select per [model-selection-guide.md](model-selection-guide.md) (override the scaffold default `gpt-4o-2024-11-20`)
2. Set `settings.temperature` (0 for deterministic)
3. Write system prompt in `messages[0].content` + rebuild `contentTokens` — structure it per [agent-prompting-guide.md](agent-prompting-guide.md) (skeleton, tool-call criteria, output contract), not a placeholder
4. Write user message template in `messages[1].content` using `{{input.fieldName}}` + rebuild `contentTokens`

### Step 4 — Define input/output schemas

1. Add fields to `agent.json` → `inputSchema` and `outputSchema`
2. Mirror in `entry-points.json`
3. Refresh (writes migrated files + regenerates `entry-points.json` and `bindings_v2.json`): `uip agent refresh "<SOLUTION_NAME>/<AGENT_NAME>" --output json`
4. Validate: `uip agent validate "<SOLUTION_NAME>/<AGENT_NAME>" --output json`

### Step 5 — Publish to Studio Web or deploy to Orchestrator

Ask the user before proceeding. There are two separate paths:

**Studio Web** (default — for visual editing and sharing):
```bash
uip solution upload . --output json
```

**Orchestrator** (for production deployment — only when explicitly requested):
```bash
uip solution pack . ./dist -v "1.0.0" --output json
uip solution publish ./dist/<SOLUTION_NAME>.1.0.0.zip --output json
uip solution deploy run --name "<NAME>" --package-name "<SOLUTION_NAME>" --package-version "1.0.0" --output json
```

## Versioning

Solutions use semantic versioning: `MAJOR.MINOR.PATCH`

```bash
# Pack with specific version
uip solution pack ./MySolution ./output -v "1.2.0" --output json

# Publish the versioned package to Orchestrator
uip solution publish ./output/MySolution.1.2.0.zip --output json

# Check published packages
uip solution packages list --output json
```

Version strategy:
- `PATCH`: bug fixes, prompt tweaks
- `MINOR`: new tools, new agents added
- `MAJOR`: breaking changes to I/O schema

## Environment Promotion

To promote from dev to production:

```bash
# 1. Pack solution
uip solution pack ./MySolution ./output -v "2.0.0" --output json

# 2. Publish to Orchestrator
uip solution publish ./output/MySolution.2.0.0.zip --output json

# 3. Deploy to production folder
uip solution deploy run \
  --name "MySolution-Prod" \
  --package-name "MySolution" \
  --package-version "2.0.0" \
  --folder-name "MySolution" \
  --parent-folder-path "Production" \
  --output json
```

## Conversational Deployment Notes

The deploy flow above applies to conversational agents (`metadata.isConversational: true`). Conversational-specific additions:

1. **External Application setup before frontend clients can connect.** Conversational agents are reached over a WebSocket session from a frontend client (typically a UiPath Coded App). Required External App configuration:
   - **Type:** Non-Confidential application (PKCE flow, no client secret)
   - **Scopes:** `ConversationalAgents` (required), `Traces.Api` (recommended), and applicable `UiPath.Orchestrator` scopes (e.g., `OR.Execution OR.Folders OR.Jobs OR.Users` or broader `OR.Default`) when the agent uses tools that hit Orchestrator
   - **Redirect URI:** the app's base URL (not a `/callback` sub-path — UiPath Coded Apps hosting does not support SPA sub-route fallback). Local dev: `http://localhost:5173`. Deployed: `https://<org>.uipath.host/<app-name>`.

2. **Frontend client integration.** For OAuth + PKCE setup and WebSocket client patterns (session lifecycle, exchange / message / content-part / tool-call event hierarchy), defer to the `uipath-coded-apps` skill. This skill (`uipath-agents`) does not own frontend integration.

## Quick Reference

All solution lifecycle operations go through `uip solution` CLI. Never call Automation.Solutions REST endpoints directly.

| Task | Command | Run From | Terminal states |
|------|---------|----------|-----------------|
| Login check | `uip login status --output json` | Any directory | — |
| Create solution | `uip solution init "<NAME>" --output json` | Any directory | — |
| Scaffold agent | `uip agent init "<NAME>" --output json` | Solution directory | — |
| Scaffold inline agent | `uip agent init "<FLOW_PROJECT_DIR>" --inline-in-flow --output json` | Any directory | — |
| Verify project registration | Check `Data.SolutionRegistration.Status` from `agent init` response (`Registered` / `AlreadyRegistered` = done; `OptedOut` = `--skip-solution-registration` passed) | Solution directory | — |
| Register project (fallback) | `uip solution project add "<PATH>" --output json` — when `agent init` returned `NotInSolution` / `Skipped` / `Failed` | Solution directory | — |
| Refresh + regenerate derived files | `uip agent refresh [path] --output json` | Agent dir or any with path | — |
| Validate (strict read-only) | `uip agent validate [path] --output json` | Agent dir or any with path | — |
| Add memory space feature | `uip agent memory add <FeatureName> --memory-space <Name> --folder-path <Folder> --path <AgentDir> --output json` | Any directory | Writes `features/<FeatureName>/feature.json`; run refresh/validate after |
| Seed memory item | `uip agent memory item add <FeatureName> <key> <value> --memory-type episodic --feedback-id <FEEDBACK_ID> --path <AgentDir> --output json` | Any directory | Updates existing item with same key |
| List guardrail validators | `uip agent guardrails list --output json` | Any directory | — |
| Discover resources | `uip solution resource list --kind <Kind> --source remote [--search <term>] --output json` | Solution directory | — |
| Refresh resources | `uip solution resource refresh --output json` | Solution directory | — |
| Add one resource (local stub or remote import) | `uip solution resource add --source local\|remote --kind <Kind> --name <NAME> [--folder-path <FOLDER>] --output json` | Solution directory | Idempotent on `(kind, name, folder)` for local, on key for remote |
| Remove one resource by key | `uip solution resource remove <KEY> --output json` | Solution directory | Offline; doesn't touch `bindings_v2.json` |
| Edit one resource's spec | `uip solution resource edit <KEY> --patch '{...}' --output json` | Solution directory | Only command that mutates an existing resource; `refresh` never overwrites. Unknown/reference/read-only props silently ignored. JSON is the only input — types preserved verbatim |
| Upload to Studio Web | `uip solution upload . --output json` | Solution directory | — |
| Pack | `uip solution pack . ./dist -v "1.0.0" --output json` | Solution directory | — |
| Publish | `uip solution publish ./dist/<PKG>.zip --output json` | Any directory | — |
| Deploy | `uip solution deploy run --name ... --output json` | Any directory | `DeploymentSucceeded`, `DeploymentFailed`, `ValidationFailed` |
| Activate | `uip solution deploy activate "<NAME>" --output json` | Any directory | `SuccessfulActivate`, `FailedActivate` |
| Uninstall | `uip solution deploy uninstall "<NAME>" --output json` | Any directory | `SuccessfulUninstall`, `FailedUninstall` |
| Deploy status | `uip solution deploy status <pipeline-deployment-id> --output json` | Any directory | — |
| List deployments | `uip solution deploy list --output json` | Any directory | — |
