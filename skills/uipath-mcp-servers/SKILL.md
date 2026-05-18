---
name: uipath-mcp-servers
description: "UiPath AgentHub MCP server registration + tool authoring via `uip agenthub mcp` (six server types: uipath / coded / command / remote / platform / swagger) and `uip agenthub mcp-tools` (three tool kinds: is-activity / resource / raw on `uipath`-type servers). For Integration Service activity authoring→load `references/is-activity-workflow.md`. For Python MCP servers / coded-agent integration→uipath-agents. For raw IS CLI→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath AgentHub MCP Servers

Register AgentHub MCP servers via `uip agenthub mcp`. Author tools on `uipath`-type servers via `uip agenthub mcp-tools`.

> **`mcp` here means an AgentHub MCP-server resource, not the MCP wire protocol.** Slugs like `inbox-mcp` / `team-helper` name AgentHub server registrations, not local repos. `uipath-mcp-python` (`@uipath/mcp`) is a separate server-implementation SDK — different task, see `uipath-agents`.

## When to Use This Skill

- Create / update / delete / refresh / list / get an AgentHub MCP server (any of: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`).
- Author / list / get / enable / disable / delete tools on a `uipath`-type server (`is-activity`, `resource`, `raw`).
- **For `is-activity` tools (Integration Service connector activities), load [references/is-activity-workflow.md](references/is-activity-workflow.md) end-to-end before authoring.** It owns the Pre-flight, cascade, `designTimeLookups`, `ActivityMetadata` schema, and connector-specific troubleshooting.
- Skip: Python MCP server implementation (FastMCP / `@uipath/mcp`) → `uipath-agents`. Raw IS CLI outside MCP tooling → `uipath-platform`.

## Trust the CLI

The CLI is the source of truth for shapes and flags. Use it instead of guessing:

- `uip agenthub mcp create <type> --print-schema --output json` — payload shape for any server type.
- `uip agenthub mcp template <type> --output json` — ready-to-edit `--file` skeleton.
- `uip agenthub mcp-tools template <kind> --output json` — tool payload skeleton (is-activity / resource / raw).
- `uip agenthub mcp-tools candidates --category <kind> --output json` — discover bindable targets. `<kind>` ∈ `automation | agent | agentic-process | api-workflow | is-activity`.
- `--output-filter <JMESPath>` on every command — extract specific fields without walking JSON by hand (e.g. `--output-filter "Data.items[].slug" --output plain`).
- `--dry-run` on every mutating call — resolve and inspect the body before POST. Note: `--dry-run` skips some server-side validation, so a clean dry-run is not a guaranteed real POST.

## Critical Rules

These are the things the CLI does not advertise in `--help`.

1. **Slug regex.** Backend enforces `^[a-z0-9-]+$`, length 3-50. Lowercase, digits, hyphens — no underscores, dots, or uppercase. CLI validates client-side before POST.

2. **Folder context is required on every AgentHub call.** Pass `--folder-path <name>` OR `--folder-key <guid>`, never both. `--folder-path` resolves via Orchestrator SDK. Personal workspace folders (`<user>@<tenant>'s workspace`) do NOT resolve by name — use `--folder-key <guid>`. Common names (`Shared`) can be ambiguous across nested folders; the CLI returns the candidate list with GUIDs — pick one and re-run with `--folder-key`. Discover GUIDs via `uip or folders list --output json`. **`refresh-tools` always requires `--folder-key` specifically** (endpoint is `/mcp/{folderKey}/{slug}/refresh-tools`).

3. **Verify after every mutation.** After `create` / `update` / `delete` / `refresh-tools`, re-list (`mcp list`, `mcp-tools list --mcp <slug>`) or `mcp get <slug>` and confirm the expected state.

4. **`refresh-tools` behavior depends on server type.**
   - `coded` / `command` — async, returns HTTP 202 + runtime id. Surface the runtime id; never claim refreshed before a follow-up `mcp-tools list --mcp <slug>` confirms.
   - `remote` / `platform` / `swagger` — sync, returns 200 after a synchronous fetch+upsert.
   - `uipath` / `selfhosted` — rejected locally; tools are manually authored via `mcp-tools create-*`. CLI emits a `NextCommand` hint to author instead.

5. **`mcp delete` looks up by slug, not GUID.** Passing a GUID returns 404.

## Server Types

`uip agenthub mcp create` takes six type subcommands. All share `--name <display>`, `--slug <kebab>`, `--description`, `--version`, `--file`/`--body`/`--print-schema`, `--dry-run`, `--folder-path`/`--folder-key`, `--tenant`, `--login-validity`. The differentiating flag picks the integration shape:

| Type | Differentiating flag | When to use | Tool surface |
|------|---------------------|-------------|--------------|
| `uipath`   | _(none)_              | AgentHub-hosted server you'll fill with `mcp-tools create-*`. | Authored via `uip agenthub mcp-tools create-*`. `refresh-tools` rejected. |
| `coded`    | `--process-key <key>` (+ `--folder-key` for the process) | Wrap an existing coded-agent process (published to Orchestrator) as an MCP server. | Discovered via `refresh-tools` (async 202). |
| `command`  | `--command <cmd>` + `--arg <arg>` (repeatable) + `--env <k=v>` (repeatable) | Spawn a local subprocess as an MCP server. | Discovered via `refresh-tools` (async 202). |
| `remote`   | `--uri <url>` + `--header <k=v>` (repeatable) + `--use-relay` | Point at an existing HTTP MCP server. Bearer/header values can be Orchestrator asset references; `AssetReferenceSubstitutor` resolves them at runtime via the caller's token + folder context. Do NOT invent a credential-store syntax. | Discovered via `refresh-tools` (sync 200). |
| `platform` | `--service <name>` + `--tool <name>` (repeatable; selects exposed platform tools) | Bind to a first-party UiPath service. | Discovered via `refresh-tools` (sync 200). |
| `swagger`  | `--spec-url <url>` (+ `--use-relay`)   | Register an OpenAPI/Swagger spec as MCP tools. Same asset substitution as `remote`. | Discovered from the spec via `refresh-tools` (sync 200). |

Headers/auth on `remote` and `swagger` are payload fields, not scalar flags. Read the shape from `--print-schema` (or `template <type>`), submit via `--file <payload.json>` or `--body '<json>'`.

`mcp update <slug>` dispatches by existing server type — flag shape mirrors `create <type>`. Verify with `mcp get <slug> --output json`.

`mcp template <type>` also accepts `process-assistant` and `selfhosted` — these have templates but NO `create` subcommand (backend enum only; skip).

## Tool Kinds (`uipath`-type servers only)

`uip agenthub mcp-tools create-{is-activity | resource | raw}`. Shared flags: `--mcp <slug>` (parent server), `--name`, `--description`, `--target-identifier <guid>` / `--target-name <name>` (resolve target via RCS — only for non-`activity` categories), `--target-folder-key <guid>` (target connection/resource's folder; for IS-activity the CLI derives this from the connection), `--category`, `--input-schema`, `--output-schema`, `--metadata`, `--continue-on-error` (default) / `--fail-fast`, `--file`/`--body`, `--dry-run`. Differ in metadata shape, discovery path, and validation strictness.

| Kind | Discovery | Validation | When to use |
|------|-----------|------------|-------------|
| `is-activity` | `mcp-tools candidates --category is-activity` + `is resources describe` | Connector schema | Wrap an Integration Service connector activity as an MCP tool. **Load [references/is-activity-workflow.md](references/is-activity-workflow.md) end-to-end** — extra Critical Rules, Pre-flight, `ActivityMetadata` schema, and IS-specific troubleshooting apply. |
| `resource`    | `mcp-tools candidates --category <kind>` (kind ∈ `automation` / `agent` / `agentic-process` / `api-workflow`) | Resource schema | Bind an Orchestrator resource. Pass `--target-identifier <resource-id>`. Read metadata shape from `mcp-tools template resource --output json`. |
| `raw`         | None | None | Free-form JSON tool — caller owns correctness end-to-end. No discovery, no schema validation, no reference-value labeling. Read the skeleton from `mcp-tools template raw --output json`. |

Stringify `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`). Pass `--output-schema "{}"` when the underlying target has no response fields — empty string is rejected with `Unexpected end of JSON input`.

Other `mcp-tools` verbs (`list --mcp <slug>`, `get`, `enable`, `disable`, `delete`, `update`) are self-documenting via `--help`. Use them for the Critical Rule 3 verify step.

## Troubleshooting (generic)

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **`InvalidFolderKey: "--folder-key requires a GUID; use --folder-path for folder names"`** — switch to `--folder-path <name>`.
- **`No folder named '<personal workspace>' was found. Did you mean: Shared?`** — personal workspaces are unresolvable by name; pass `--folder-key <guid>` (Critical Rule 2).
- **`ConflictingInput: "Pass either --folder-path or --folder-key, not both."`** — drop one.
- **Slug rejected with validation error** — backend enforces `^[a-z0-9-]+$`, length 3-50 (Critical Rule 1).
- **`mcp delete <guid>` returns 404** — `mcp delete` looks up by slug, not GUID (Critical Rule 5).
- **`refresh-tools` returns 202 with a runtime id** — `coded` / `command` refreshes are async (Critical Rule 4). Surface the runtime id; verify via follow-up `mcp-tools list --mcp <slug>`.

Tool-kind-specific troubleshooting lives with the workflow that owns it — IS-activity troubleshooting is in [references/is-activity-workflow.md](references/is-activity-workflow.md).
