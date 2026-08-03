---
name: uipath-mcp-servers
description: "UiPath AgentHub MCP server registration + resource-tool authoring via `uip agenthub mcp` (six server types: uipath / coded / command / remote / platform / swagger) and `uip agenthub mcp-tools` on `uipath`-type servers. For Python MCP servers / coded-agent integration→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath AgentHub MCP Servers

Register AgentHub MCP servers via `uip agenthub mcp`. Author tools on `uipath`-type servers via `uip agenthub mcp-tools`.

> **`mcp` here means an AgentHub MCP-server resource, not the MCP wire protocol.** Slugs like `inbox-mcp` / `team-helper` name AgentHub server registrations, not local repos. `uipath-mcp-python` (`@uipath/mcp`) is a separate server-implementation SDK — different task, see `uipath-agents`.

## When to Use This Skill

- Create / update / delete / refresh / list / get an AgentHub MCP server (any of: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`).
- Author resource tools on a `uipath`-type server; list / get / enable / disable / delete its tools.
- Skip: Python MCP server implementation (FastMCP / `@uipath/mcp`) → `uipath-agents`.

## Trust the CLI

The CLI is the source of truth for shapes and flags. Use it instead of guessing:

- `uip agenthub mcp create <type> --print-schema --output json` — payload shape for any server type.
- `uip agenthub mcp template <type> --output json` — ready-to-edit `--file` skeleton.
- `uip agenthub mcp-tools template resource --output json` — resource-tool payload skeleton.
- `uip agenthub mcp-tools candidates --category <kind> --output json` — discover bindable targets. `<kind>` ∈ `automation | agent | agentic-process | api-workflow`.
- `--output-filter <JMESPath>` on every command — extract specific fields without walking JSON by hand (e.g. `--output-filter "Data.items[].slug" --output plain`).
- `--dry-run` on every mutating call — resolve and inspect the body before POST. Note: `--dry-run` skips some server-side validation, so a clean dry-run is not a guaranteed real POST.

## Critical Rules

These are the things the CLI does not advertise in `--help`.

1. **Slug regex.** Backend enforces `^[a-z0-9-]+$`, length 3-50. Lowercase, digits, hyphens — no underscores, dots, or uppercase. CLI validates client-side before POST.

2. **Folder context is required on every AgentHub call.** Pass `--folder-path <name>` OR `--folder-key <guid>`, never both. Exception: `mcp list --all-folders` spans every folder you can see (mutually exclusive with the folder flags; folders without AgentHub permission are skipped with a `Warning` line) — use it to locate a server when its folder is unknown, then pass that folder explicitly on every follow-up call (`mcp-tools` verbs have no `--all-folders`). `--folder-path` resolves via Orchestrator SDK. Personal workspace folders (`<user>@<tenant>'s workspace`) do NOT resolve by name — use `--folder-key <guid>`. Common names (`Shared`) can be ambiguous across nested folders; the CLI returns the candidate list with GUIDs — pick one and re-run with `--folder-key`. Discover GUIDs via `uip or folders list --output json`. **`refresh-tools` always requires `--folder-key` specifically** (endpoint is `/mcp/{folderKey}/{slug}/refresh-tools`).

3. **Verify after every mutation.** After `create` / `update` / `delete` / `refresh-tools`, re-list (`mcp list`, `mcp-tools list --mcp <slug>`) or `mcp get <slug>` and confirm the expected state.

4. **`refresh-tools` behavior depends on server type.**
   - `coded` / `command` — async, returns HTTP 202 + runtime id. Surface the runtime id; never claim refreshed before a follow-up `mcp-tools list --mcp <slug>` confirms.
   - `remote` / `platform` / `swagger` — sync, returns 200 after a synchronous fetch+upsert.
   - `uipath` / `selfhosted` — rejected locally; resource tools are manually authored via `mcp-tools create-resource`. CLI emits a `NextCommand` hint to author instead.

5. **`mcp delete` looks up by slug, not GUID.** Passing a GUID returns 404.

## Server Types

`uip agenthub mcp create` takes six type subcommands. All share `--name <display>`, `--slug <kebab>`, `--description`, `--version`, `--file`/`--body`/`--print-schema`, `--dry-run`, `--folder-path`/`--folder-key`, `--tenant`, `--login-validity`. The differentiating flag picks the integration shape:

| Type | Differentiating flag | When to use | Tool surface |
|------|---------------------|-------------|--------------|
| `uipath`   | _(none)_              | AgentHub-hosted server you'll fill with resource tools. | Authored via `uip agenthub mcp-tools create-resource`. `refresh-tools` rejected. |
| `coded`    | `--process-key <key>` (+ `--folder-key` for the process) | Wrap an existing coded-agent process (published to Orchestrator) as an MCP server. | Discovered via `refresh-tools` (async 202). |
| `command`  | `--command <cmd>` + `--arg <arg>` (repeatable) + `--env <k=v>` (repeatable) | Spawn a local subprocess as an MCP server. | Discovered via `refresh-tools` (async 202). |
| `remote`   | `--uri <url>` + `--header <k=v>` (repeatable) + `--use-relay` | Point at an existing HTTP MCP server. Bearer/header values can be Orchestrator asset references; `AssetReferenceSubstitutor` resolves them at runtime via the caller's token + folder context. Do NOT invent a credential-store syntax. | Discovered via `refresh-tools` (sync 200). |
| `platform` | `--service <name>` (lowercase service id, e.g. `orchestrator` — the CLI `--help` example's capitalized `Orchestrator` is rejected with HTTP 400) + `--tool <name>` (repeatable; selects exposed platform tools) | Bind to a first-party UiPath service. | Discovered via `refresh-tools` (sync 200). |
| `swagger`  | `--spec-url <url>` (+ `--use-relay`)   | Register an OpenAPI/Swagger spec as MCP tools. Same asset substitution as `remote`. | Discovered from the spec via `refresh-tools` (sync 200). |

Headers/auth on `remote` and `swagger` are payload fields, not scalar flags. Read the shape from `--print-schema` (or `template <type>`), submit via `--file <payload.json>` or `--body '<json>'`.

`mcp update <slug>` dispatches by existing server type — flag shape mirrors `create <type>`. Verify with `mcp get <slug> --output json`.

`mcp template <type>` also accepts `process-assistant` and `selfhosted` — these have templates but NO `create` subcommand (backend enum only; skip).

## Resource Tools (`uipath`-type servers only)

Run `uip agenthub mcp-tools create-resource`. Flags: `--mcp <slug>` (parent server), `--name`, `--description`, `--target-identifier <guid>` / `--target-name <name>` (resolve target via RCS), `--folder-key <guid>` / `--folder-path <name>` (MCP server folder context), `--target-folder-key <guid>` / `--target-folder-path <name>` (the Orchestrator resource's folder when it differs from the server's; resolves to the tool's `targetFolderKey`; never both; omit to default to the candidate's folder (`--target-name`) or the server folder; the explicit flag wins, including over a `--file`/`--body` payload field), `--category`, `--input-schema`, `--output-schema`, `--metadata`, `--continue-on-error` (default) / `--fail-fast`, `--file`/`--body`, `--dry-run`.

| Kind | Discovery | Validation | When to use |
|------|-----------|------------|-------------|
| `resource`    | `mcp-tools candidates --category <kind>` (kind ∈ `automation` / `agent` / `agentic-process` / `api-workflow`) | Resource schema | Bind an Orchestrator resource. Pass `--target-identifier <resource-id>`. Read metadata shape from `mcp-tools template resource --output json`. `candidates` is tenant-wide — each item carries its `folder {key, name}`; present the folder alongside the name when the user picks. `--target-name` lookup searches the server folder by default; resource in a different folder → pass `--target-folder-path` / `--target-folder-key` (scopes the lookup AND sets the tool's `targetFolderKey`); with `--target-identifier`, pass the same flags when the resource's folder differs from the server's. |

Stringify `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`). Build each JSON in a file and pass it as `--metadata "$(jq -c . metadata.json)"` (likewise input/output schema) — do **not** assemble multi-KB JSON inline in the command. Pass `--output-schema "{}"` when the underlying target has no response fields — empty string is rejected with `Unexpected end of JSON input`.

Other `mcp-tools` verbs (`list --mcp <slug>`, `get`, `enable`, `disable`, `delete`, `update`) are self-documenting via `--help`. Use them for the Critical Rule 3 verify step. `update` also accepts `--target-folder-key` / `--target-folder-path`: retargeting via `--target-identifier` defaults the tool's `targetFolderKey` to the server folder — pass the explicit flag when the new target lives elsewhere (wins over the default and over a `--file`/`--body` payload field).

## Troubleshooting (generic)

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **`InvalidFolderKey: "--folder-key requires a GUID; use --folder-path for folder names"`** — switch to `--folder-path <name>`.
- **`No folder named '<personal workspace>' was found. Did you mean: Shared?`** — personal workspaces are unresolvable by name; pass `--folder-key <guid>` (Critical Rule 2).
- **`ConflictingInput: "Pass either --folder-path or --folder-key, not both."`** — drop one.
- **Slug rejected with validation error** — backend enforces `^[a-z0-9-]+$`, length 3-50 (Critical Rule 1).
- **`mcp delete <guid>` returns 404** — `mcp delete` looks up by slug, not GUID (Critical Rule 5).
- **`refresh-tools` returns 202 with a runtime id** — `coded` / `command` refreshes are async (Critical Rule 4). Surface the runtime id; verify via follow-up `mcp-tools list --mcp <slug>`.
