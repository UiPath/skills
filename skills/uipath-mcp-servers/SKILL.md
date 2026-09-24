---
name: uipath-mcp-servers
description: "UiPath Agent Gateway MCP servers (`uip agenthub mcp` / `uip agenthub mcp-tools`). Register, update, refresh tools, list, get, delete MCP servers: uipath (Orchestrator processes, agents, agentic processes, API workflows as tools), coded (published uipath-mcp Python server package), command (npx/uvx), remote (HTTP MCP URL, Relay), swagger (OpenAPI spec), platform (UiPath service operations, e.g. Test Manager); get the MCP URL a client connects to. For an agent that calls MCP tools→uipath-agents. For `uip mcp serve` (the uip CLI as an MCP server)→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Agent Gateway MCP Servers

Agent Gateway is Orchestrator's hub for MCP servers and A2A agents: [about](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/about-agent-gateway), [MCP server types](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/mcp-server-types). This skill covers its MCP servers. The CLI group is named `agenthub`: `uip agenthub mcp` registers servers, `uip agenthub mcp-tools` manages their tools.

## When to Use This Skill

- Create / update / delete / refresh / list / get an Agent Gateway MCP server: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`.
- Bind Orchestrator processes, agents, agentic processes or API workflows as tools on a `uipath` server.
- Choose the service operations a `platform` server exposes.
- Not this skill: an agent that calls MCP tools → `uipath-agents`; running the `uip` CLI itself as an MCP server (`uip mcp serve`) → `uipath-platform`; A2A agents (`uip agenthub remote-a2a-agent --help`; no skill covers them). No skill covers writing the MCP server itself (`uipath-mcp` Python SDK, FastMCP, self-hosted runtime): see the [uipath-mcp quick start](https://uipath.github.io/uipath-python/mcp/quick_start/).

## Trust the CLI

- `uip agenthub mcp create <TYPE> --print-schema --output json` — payload fields per type.
- `uip agenthub mcp template <TYPE> --output json` — `--file` skeleton (re-case keys: Critical Rule 3).
- `uip agenthub mcp-tools template resource --output json` — resource-tool fields.
- `uip agenthub mcp-tools candidates --category <CATEGORY> --output json` — bindable targets. `<CATEGORY>` ∈ `automation | agent | agentic-process | api-workflow`.
- `uip agenthub mcp get <SLUG> --output json` — `McpUrl` is the endpoint an MCP client connects to.
- `--output-filter <JMESPATH>` on every command (e.g. `--output-filter "Items[].Slug" --output plain`).
- `--dry-run` on every mutating call resolves its inputs and prints the body without sending the mutation. `mcp update`, `refresh-tools` and every `mcp-tools` mutation still read the server (or the catalog) first, so they need auth and a valid slug and folder. Nothing is sent to the service, so its validation (slug, required fields, service and tool names) does not run: a clean dry-run does not guarantee the real call succeeds.

## Critical Rules

These are the things the CLI does not advertise in `--help`.

1. **Slugs are validated by the service, not the CLI.** The service requires `^[a-z0-9-]+$`, length 3-50 (display name 3-100). Without `--slug` the CLI only slugifies `--name` (lowercase, other characters → `-`) and sends it unchecked, so a name that yields a too-short or too-long slug fails at the service. Pass `--slug` explicitly.

2. **Every call that reads or writes a server needs a folder context.** Pass `--folder-path <FOLDER_PATH>` OR `--folder-key <FOLDER_KEY>`, never both — `refresh-tools` included (the CLI resolves the path to the key its endpoint needs). `template`, `mcp create <TYPE> --print-schema` and `mcp-tools candidates` need none. Exception: `mcp list --all-folders` spans every folder you can see (mutually exclusive with the folder flags; folders without Agent Gateway permission are skipped with a `Warning` line) — use it to locate a server, then pass that folder on every follow-up call (`mcp-tools` verbs have no `--all-folders`). Personal workspace folders (`<USER>@<TENANT>'s workspace`) do NOT resolve by name — use `--folder-key`. A name shared by nested folders resolves to the exact full-path match; otherwise the CLI lists the candidates — re-run with `Parent/Child` or `--folder-key`. Discover GUIDs via `uip or folders list --output json`. `create coded` with scalar flags needs `--folder-key`: the payload's required `folderKey` is copied from it, so `--folder-path` leaves it empty (HTTP 400).

3. **Payloads are camelCase; CLI output is PascalCase.** The CLI PascalCases every key it prints — `template`, `--print-schema` and the `--dry-run` resolved body included — but reads `--file` / `--body` with camelCase keys (`name`, `slug`, `uri`, `headers`, `processKey`, …) and silently drops any other casing. Lower-case the first letter of every key before submitting a template.

4. **Headers and environment variables are payload lines, not flags.** Put a `remote` server's headers in the payload's `headers` string as newline-separated `Name: value` lines, and a `command` server's variables in `environmentVariables` as newline-separated `KEY=VALUE` lines; submit via `--file` / `--body`. The `--header <NAME>=<VALUE>` and `--env <KEY>=<VALUE>` flags exist, but they send a JSON object the service does not parse: the header arrives malformed and the variables are lost. A header value that is exactly `%ASSETS/<ASSET_NAME>%` is replaced at call time by that Orchestrator asset's value (text, secret, or credential password), read from the server's folder with the caller's token. The asset must hold the whole value (e.g. `Bearer <TOKEN>`): `Bearer %ASSETS/<ASSET_NAME>%` is sent literally. Do NOT invent another syntax.

5. **Verify after every mutation.** After `create` / `update` / `delete` / `refresh-tools`, re-list (`mcp list`, `mcp-tools list --mcp <SLUG>`) or `mcp get <SLUG>` and confirm the expected state.

6. **`mcp update` replaces; it does not patch.** Read [Updating Servers](#updating-servers) before any `mcp update`, `mcp-tools enable` or `mcp-tools disable`: on a `uipath` server a scalar `mcp update` deletes every tool, on `coded` / `command` / `remote` / `swagger` it fails (use `--file` / `--body`), and on a `platform` server these verbs rewrite the tool selection.

7. **`refresh-tools` behavior depends on server type.**
   - `coded` / `command` — async, returns HTTP 202 + runtime id. Surface the runtime id; never claim refreshed before a follow-up `mcp-tools list --mcp <SLUG>` confirms.
   - `remote` / `swagger` — sync 200 after fetching and storing the tools. `platform` — sync 200; reloads the service definition.
   - `uipath` / `selfhosted` — rejected locally; `uipath` tools are authored via `mcp-tools create-resource`. CLI emits a `NextCommand` hint.

8. **Deletes take a slug and `--yes`.** `mcp delete` looks up by slug; a GUID returns 404. `mcp delete` and `mcp-tools delete` refuse to run without `--yes` (even with `--dry-run`) and never prompt — confirm with the user before passing it.

## Server Types

`uip agenthub mcp create <TYPE>` shares `--name`, `--slug`, `--description`, `--version`, `--file` / `--body` / `--print-schema`, `--dry-run`, `--folder-path` / `--folder-key`, `--login-validity`.

| Type | Type-specific flags | When to use | Tools from |
|------|---------------------|-------------|------------|
| `uipath`   | _(none)_ | Server you fill with tools bound to Orchestrator resources. | `mcp-tools create-resource` |
| `coded`    | `--process-key <PROCESS_KEY>` (+ `--folder-key`, Rule 2) | Published coded MCP **server** package (`uipath-mcp` Python SDK; Orchestrator process type `MCPServer`). Not a coded agent. | `refresh-tools` (async) |
| `command`  | `--command <CMD>` + `--arg <ARG>` (repeatable) | Local stdio server (`npx` / `uvx`) run as a serverless job. Env vars: Rule 4. | `refresh-tools` (async) |
| `remote`   | `--uri <URL>` + `--use-relay` | Existing HTTP MCP server; `--use-relay` reaches an on-premise host through Relay. Headers: Rule 4. | `refresh-tools` (sync) |
| `swagger`  | `--spec-url <URL>` | OpenAPI / Swagger spec; one tool per operation. No `--use-relay` flag (set `useRelay` in `--file`); the CLI cannot send swagger headers. | `refresh-tools` (sync) |
| `platform` | `--service <SERVICE_ID>` + `--tool <OPERATION_ID>` (repeatable) | Operations of a first-party UiPath service. | the `--tool` selection |

**`coded`.** `--process-key` is the process (release) `Key` GUID from `uip or processes list --folder-key <FOLDER_KEY> --process-type MCPServer --output json` — not its `ProcessKey` field (the package name). The process must be in the server's folder: Orchestrator starts it there. The service does not check the process on create, so a wrong one surfaces only at `refresh-tools`.

**`platform`.**
- `--service` takes the service id exactly as the service lists it (case-sensitive), e.g. `testmanager`. Production today: `casemanagementcontrol`, `testmanager`, `testmanagerperformancetesting`, `testmanagerExternal`, `docsai`; staging and alpha add `orchestrator` and others; the set depends on the cloud. The CLI cannot list services: when the user has not named one, ask — never assume `orchestrator`. The CLI's own `--help` example (`--service Orchestrator`) is wrong, and the `ServiceName: "swagger"` in `mcp template platform` is a placeholder, not a service id.
- `--tool` takes the service's operation names — its OpenAPI operationIds, case-sensitive (e.g. `Get_test_sets`, `Get_test_cases` on `testmanager`). The CLI cannot list them either; ask the user.
- `mcp-tools list --mcp <SLUG>` shows the current selection; change it only as [Updating Servers](#updating-servers) describes.
- Platform MCP must be enabled on the tenant; otherwise platform create / update return HTTP 404.

**`selfhosted` / `process-assistant`.** `mcp template` accepts both, but the CLI cannot create either. A self-hosted server is created by the `uipath-mcp` Python runtime registering itself when it starts; the CLI can `list` / `get` / `delete` it, and `mcp update` fails on it. `process-assistant` is a legacy value.

## Updating Servers

`mcp update <SLUG>` reads the server's type and sends a full replacement, so a `--file` / `--body` payload must carry every field you want to keep (camelCase, no `type` key). Its flags mirror `create <TYPE>` minus `--slug`; what they do depends on the type.

| Type | `mcp update` today |
|------|--------------------|
| `uipath` | A scalar update deletes every tool: the PUT replaces the tool list and scalar flags send none. Edit tools with `mcp-tools update`. Change server fields only via `--file` with `server` plus every existing tool in `tools`, each field copied exactly (camelCase), then confirm with `mcp-tools list`. Any difference in `tools` recreates every tool with new ids and deletes the tools' guardrails. |
| `platform` | Scalar flags send only what you pass: exactly the `--tool` list (none → no tools); the description is cleared unless `--description` is passed; "all tools" is turned off; `--service` is ignored. `mcp-tools enable --name <OPERATION_ID>` leaves only the `--name` values selected; `disable` leaves none — the CLI does not read the current selection. To change it: `mcp update <SLUG> --tool <OPERATION_ID_1> --tool <OPERATION_ID_2> --description "<DESCRIPTION>"` with the full list. |
| `coded`, `command`, `remote`, `swagger` | Scalar flags fail with `MCP server type is immutable…`, even with `--dry-run`: the CLI copies the fetched `type` into the body. Use `--file` / `--body`. Required: `coded` `processKey` + `folderKey`; `command` `command` + `arguments`; `remote` `uri`. `mcp get` shows a `remote` server's `uri` as `Arguments` and its headers as `EnvironmentVariables`. An omitted `description`, `environmentVariables` (`command`) or `headers` (`remote`) is cleared, and an omitted `useRelay` turns Relay off. `****` values copied from `mcp get` keep their stored value. |
| `selfhosted` | Scalar flags fail the same way; `--file` / `--body` fails with `Unsupported MCP type`. |

## Tools (`uip agenthub mcp-tools`)

| Verb | Works on |
|------|----------|
| `create-resource`, `create-raw`, `update`, `delete` | `uipath` servers only |
| `enable`, `disable` | `platform` servers only ([Updating Servers](#updating-servers)) |
| `list`, `get --name <NAME>` | every type |
| `get <TOOL_ID>` | every type except `platform` (404: its tools are not stored) |
| `template`, `candidates` | no server needed |

`create-resource` flags: `--mcp <SLUG>`, `--name`, `--description` (required by the service), `--category <CATEGORY>`, `--target-identifier <RESOURCE_ID>` / `--target-name <NAME>` (RCS lookup), `--folder-key` / `--folder-path` (server folder), `--target-folder-key` / `--target-folder-path`, `--input-schema`, `--output-schema`, `--metadata`, `--file` / `--body`, `--dry-run`.

- Discover targets with `mcp-tools candidates --category <CATEGORY>` and pass `--target-identifier <RESOURCE_ID>`. `candidates` is tenant-wide unless you pass a folder flag; each item carries its `Folder {Key, Name}` — present the folder alongside the name when the user picks.
- Target folder: `--target-name` searches the server folder by default. When the resource lives in another folder, pass `--target-folder-path` / `--target-folder-key` (never both): it scopes the lookup AND sets the tool's `targetFolderKey`, and wins over the candidate's folder, the server folder and a `--file` / `--body` field. With `--target-identifier`, pass it whenever the resource's folder differs from the server's.
- `--metadata`, `--input-schema`, `--output-schema` are optional JSON strings. Build each in a file and pass `--metadata "$(jq -c . metadata.json)"` — do **not** assemble multi-KB JSON inline. Pass `--output-schema "{}"` when the target has no response fields; an empty string fails with `Unexpected end of JSON input`.
- `mcp-tools update` patches only the fields passed. Retargeting via `--target-identifier` defaults `targetFolderKey` to the server folder — pass `--target-folder-key` / `--target-folder-path` when the new target lives elsewhere.

## Troubleshooting

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **HTTP 400: fields your `--file` contains are "required"** — keys are not camelCase (Rule 3).
- **`InvalidFolderKey: "--folder-key requires a GUID; use --folder-path for folder names"`** — switch to `--folder-path <FOLDER_PATH>`.
- **`No folder named '<PERSONAL_WORKSPACE>' was found. Did you mean: Shared?`** — pass `--folder-key <FOLDER_KEY>` (Rule 2).
- **`ConflictingInput: "Pass either --folder-path or --folder-key, not both."`** — drop one.
- **`The FolderKey field is required.` on `create coded`** — pass `--folder-key`, not `--folder-path` (Rule 2).
- **Slug rejected** — Rule 1. **`mcp delete <GUID>` 404 / `Confirmation required: …`** — Rule 8. **`refresh-tools` 202 + runtime id** — expected for `coded` / `command` (Rule 7).
- **``MCP server type is immutable. Remove the `type` field from the payload.``** — a scalar `mcp update` on `coded` / `command` / `remote` / `swagger` / `selfhosted`, or a `--file` / `--body` with a `type` key: use a payload without `type` ([Updating Servers](#updating-servers)).
- **`This command requires a <EXPECTED_TYPE> MCP server; <SLUG> is <TYPE>.`** — the `mcp-tools` verb does not apply to that type ([Tools](#tools-uip-agenthub-mcp-tools)). On a `coded` / `command` / `remote` / `swagger` server, follow the `NextCommand`. On a `platform` server, do NOT run the suggested `mcp-tools enable`: it clears the selection. Change it only as [Updating Servers](#updating-servers) describes.
- **`Service '<SERVICE_ID>' is not available or not enabled`** — wrong id (case-sensitive) or not offered in this cloud; ask the user which service.
- **`Tools not found in service swagger: <NAMES>`** — `--tool` values must be the service's operation names, exactly as cased.
- **HTTP 404 on `create platform`, a platform `mcp update`, or `mcp-tools enable` / `disable`** — Platform MCP is not enabled on the tenant.
