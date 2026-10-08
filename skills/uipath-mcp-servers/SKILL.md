---
name: uipath-mcp-servers
description: "UiPath Agent Gateway MCP servers (`uip agenthub mcp` / `uip agenthub mcp-tools`). Register, update, refresh tools, list, get, delete MCP servers: uipath (Orchestrator processes, agents, agentic processes, API workflows as tools), coded (published uipath-mcp Python server package), command (npx/uvx), remote (HTTP MCP URL, Relay), swagger (OpenAPI spec), platform (UiPath service operations, e.g. Test Manager); get the MCP URL a client connects to. For an agent that calls MCP tools→uipath-agents. For `uip mcp serve` (the uip CLI as an MCP server)→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Agent Gateway MCP Servers

Agent Gateway is Orchestrator's hub for MCP servers and A2A agents: [about](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/about-agent-gateway), [MCP server types](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/mcp-server-types). This skill covers its MCP servers. The CLI group is named `agenthub`: `uip agenthub mcp` manages servers, `uip agenthub mcp-tools` manages their tools.

## When to Use This Skill

**Servers — `uip agenthub mcp`, plus `uip agenthub platform-services` / `platform-tools` to look up `platform` names:**

- Create, update, delete, list or get an MCP server of any type ([Server Types](#server-types) says when to use each), and refresh its tools.
- Get the `McpUrl` an MCP client connects to.
- Find the UiPath services and tool names a `platform` server can expose.

**Tools — `uip agenthub mcp-tools`:**

- Bind Orchestrator processes, agents, agentic processes or API workflows as tools on a `uipath` server; edit or remove those tools.
- Add or remove tools on a `platform` server.
- List or get the tools of any server.

**Not this skill:** an agent that calls MCP tools → `uipath-agents`; running the `uip` CLI itself as an MCP server (`uip mcp serve`) → `uipath-platform`; A2A agents (`uip agenthub remote-a2a-agent --help`; no skill covers them). No skill covers writing the MCP server itself (`uipath-mcp` Python SDK, FastMCP, self-hosted runtime): see the [uipath-mcp quick start](https://uipath.github.io/uipath-python/mcp/quick_start/).

## Critical Rules

These are the things the CLI does not advertise in `--help`.

1. **Pass slugs exactly as `mcp list` prints them.** On create the CLI does not validate the slug: without `--slug` it sends `--name` lowercased with other characters turned into `-`, which can still be under 3 or over 50 characters. The service requires `^[a-z0-9-]+$`, 3-50 characters (display name 3-100), so always pass `--slug`. The service reads a server by display name before slug, so `mcp get`, `mcp update`, `refresh-tools` and every `mcp-tools ... --mcp` refuse an argument that reads back another slug (`'<INPUT>' resolves to the MCP server '<SLUG>' …`). Never pass a display name or a GUID: `mcp delete` returns 404 for anything but the slug.

2. **Give every server command its folder.** Pass `--folder-key <FOLDER_KEY>` (a GUID) or `--folder-path <FOLDER_PATH>` (a name or `Parent/Child`), never both, as [Folder Context](#folder-context) lists per command. A 404 on a slug usually means the wrong folder: find the server with `mcp list --all-folders` and pass its `FolderKey`.

3. **Payloads are camelCase; everything else the CLI prints is PascalCase.** `--file` / `--body` keys must be the API's camelCase names (`name`, `slug`, `uri`, `headers`, `processKey`, `targetIdentifier`, …): the CLI drops any other casing without an error. A dropped required field fails with HTTP 400, but a payload whose fields are all optional (`mcp-tools update`, a `swagger` `mcp update`) succeeds without the change, and on `mcp update` a dropped `description` is cleared (a swagger update also turns Relay off). `mcp template` prints a camelCase payload: edit it and send it as it is. `--print-schema` describes the payload in camelCase; it is not one. `mcp get`, `mcp list`, every create / update result, `mcp-tools list`, `mcp-tools template` and the `--dry-run` plan print PascalCase: put a copied value under the camelCase name `--print-schema` gives. `mcp get` also shows a remote server's URI as `Arguments` and remote / swagger headers as `EnvironmentVariables`.

4. **Set headers and environment variables with the flags.** Use `--header <NAME>=<VALUE>` on `remote` / `swagger` and `--env <KEY>=<VALUE>` on `command`, once per entry, on `create` and `update`. The CLI sends the newline-separated `Name:Value` / `KEY=VALUE` lines the service stores and refuses a repeated name or a value with a line break. A header value of exactly `%ASSETS/<ASSET_NAME>%` is replaced at call time by that Orchestrator asset's value, read from the server's folder. The asset must hold the whole value (e.g. `Bearer <TOKEN>`): `Bearer %ASSETS/<ASSET_NAME>%` is sent literally. Do NOT invent another syntax. Orchestrator gives the asset's value to Agent Gateway in the portal and to jobs, but not for a CLI login: `refresh-tools` from the CLI on such a server fails with 403 ([troubleshooting](references/troubleshooting-guide.md#refresh)). On `mcp update`, `--header` / `--env` replace every stored entry; keep a secret by passing `"<NAME>=****"` with the name spelled exactly as `mcp get` shows it with a `****` value.

5. **Confirm each mutation from its result.** `mcp create` / `mcp update` return the stored server, `mcp-tools create-resource` / `create-raw` / `update` the stored tool, and `delete` reports `Deleted: true` only after every delete succeeded. `mcp-tools enable` / `disable` return the server without its selection: confirm with `uip agenthub mcp-tools list --mcp <SLUG> --folder-path <FOLDER_PATH> --limit 1000 --output-filter "{Names: Items[].Name, Total: Total, Count: Count}" --output json` (unfiltered rows carry each tool's schemas). `mcp get` shows secrets as `****` either way, so it cannot prove a masked value was kept. `refresh-tools` is confirmed by its `Data.Status` (Rule 7), not by re-listing tools.

6. **Scalar flags keep; a payload replaces.** With scalar flags, `mcp update` reads the server and sends back every stored field you do not change. A `--file` / `--body` payload is sent as it is: each field it leaves out is kept or cleared as the [payload table](references/updating-servers-guide.md#what-a-payload-keeps-or-clears) says. An omitted `description` is always cleared, and a `platform` payload without `selectedToolNames` / `useAllTools` clears the selection and turns All tools off; `--print-schema` does not say this for every field. On a `uipath` server the CLI refuses any update without a `tools` list, scalar flags included (older service releases delete every tool on such an update). Read [Updating Servers](#updating-servers) before any `mcp update`.

7. **`refresh-tools` depends on the server type.** A new `coded`, `command` or `remote` server has no tools until it runs: run it after `mcp create`, and after a `remote` `--uri` change (the stored tools still come from the old URI). It needs the folder, also with `--dry-run`.
   - `coded` / `command`: `Data: {RuntimeId, Status: "Started"}`. Agent Gateway started the server as an Orchestrator job (`uip or jobs get <RUNTIME_ID> --output json`); the tool list changes only when that job registers its tools. Report the `RuntimeId`; never claim the tools are refreshed.
   - `remote` / `swagger`: `Data: {Status: "Refreshed"}`, and the tools are already stored: remote tools are fetched from its URI; swagger tools are regenerated from its `swaggerUrl`, downloaded again with the stored headers (or from the stored spec when it has no URL).
   - `platform`: `Data: {Status: "Refreshed"}`. The service drops its cached service definition; the selection is kept.
   - `uipath` / `selfhosted`: refused. `uipath` tools come from `mcp-tools create-resource`; `selfhosted` tools from the runtime that serves it.

8. **Deletes take a slug, the folder and `--yes`.** `mcp delete` and `mcp-tools delete` refuse to run without `--yes`, also with `--dry-run`, and never prompt: confirm with the user before passing it. List what you will delete first (`mcp list --limit 1000`, `Total` equal to `Count`; a prefix is `--output-filter "Items[?starts_with(Slug, '<PREFIX>')].Slug"`), show each slug with its `Name`, and delete only the servers the user confirmed from that list. `mcp delete` takes one slug per call: run it for each, then list again. `mcp delete --dry-run` does not check that the server exists. `mcp-tools delete --name <SUBSTR>` matches by case-insensitive substring and needs `--allow-multiple` when several tools match, which it then deletes all: prefer tool ids from `mcp-tools list`.

9. **List platform names; never guess them.** Take `--service` from `platform-services list` and `--tool` from `platform-tools list`, exactly as cased, one name per `--tool` flag ([the `platform` steps](#server-types)). Services differ per environment: never assume `orchestrator`. Pass `--tool` or `--use-all-tools`, not both; with neither, the server has no tools.

10. **Never route stored credentials around a refusal.** `mcp update` refuses to move a `remote` server to another origin (scheme, host or port), or a `swagger` server to another spec, while that would send its stored connection token or secret headers there. Follow the refusal's `Instructions` ([moving a server](references/updating-servers-guide.md#moving-a-server-to-another-host)); do not delete headers or connections to get past it without the user's consent.

## Folder Context

| Command | Folder input |
|---------|--------------|
| `mcp list` | one of `--folder-key`, `--folder-path`, `--all-folders`, required |
| `mcp get`, `mcp create <TYPE>`, `mcp update` (incl. `--print-schema`, `--dry-run`), `mcp delete`, `mcp refresh-tools` | `--folder-key` or `--folder-path`, required |
| every `mcp-tools` verb that takes `--mcp` | the server's folder, required; `create-resource`, `create-raw` and `update` also take `--target-folder-key` / `--target-folder-path` for a target in another folder |
| `mcp-tools candidates` | optional: tenant-wide without one |
| `mcp create <TYPE> --print-schema` | none (folder flags are ignored) |
| `mcp template`, `mcp-tools template`, `platform-services list`, `platform-tools list` | none: a folder flag fails as `unknown option` |

- Find folders with `uip or folders list --output json`: pass a row's `Key` as `--folder-key` or its `Path` as `--folder-path`.
- Personal workspace folders (`<USER_EMAIL>'s workspace`) do NOT resolve by name: use `--folder-key`.
- A name shared by nested folders resolves to the folder whose full path matches exactly; otherwise the CLI lists the candidates: re-run with `Parent/Child` or `--folder-key`.
- `mcp list --all-folders` lists the servers in every folder you can read, each row with its `FolderKey` (`mcp-tools` has no `--all-folders`). Folders it cannot read are reported only on stderr.
- A scalar `create coded` fills the payload's `folderKey` from either folder flag; a coded `--file` / `--body` must carry `folderKey` itself.

## Trust the CLI

- `uip agenthub mcp create <TYPE> --print-schema --output json` — create payload fields per type. No login, no folder.
- `uip agenthub mcp template <TYPE> --output json` — create `--file` skeleton: edit the values, send it as it is.
- `uip agenthub mcp update <SLUG> --folder-path <FOLDER_PATH> --print-schema --output json` — update fields for that server's type. It reads the server, so it needs a login, the folder and the exact slug. Only some fields say what leaving them out does: the [payload table](references/updating-servers-guide.md#what-a-payload-keeps-or-clears) covers every one.
- `platform` names come from `uip agenthub platform-services list` and `uip agenthub platform-tools list`: run them as the [`platform` steps](#server-types) give them.
- `uip agenthub mcp-tools candidates --category <CATEGORY> --output json` — Orchestrator resources that can become tools on a `uipath` server. `<CATEGORY>` ∈ `automation | agent | agentic-process | api-workflow`; `--category` exists only for `uipath` server tools (`candidates`, `create-resource`, `create-raw`).
- `uip agenthub mcp get <SLUG> --folder-path <FOLDER_PATH> --output json` — `McpUrl` is the endpoint an MCP client connects to. To show a server the user names, find its `Slug` by `Name` in `mcp list`, then `mcp get` it and list its tools (Rule 5).
- `mcp get` / `mcp list` print `Type` as a number: 0 `uipath`, 1 `command`, 2 `coded`, 3 `selfhosted`, 4 `remote`, 6 `platform`, 7 `swagger`. `Status` 1 is connected, 0 disconnected. A tool's `Type` is a different number. Null fields are left out: no `ConnectionId` means no Integration Service connection. A `swagger` server's spec URL is not in `mcp get`, only in its create / update result (`SwaggerUrl`).
- `--output-filter <JMESPATH>` works on every command, over the keys it prints: PascalCase (`Items[].Slug`), camelCase on `mcp template` and `--print-schema` (`uri`). The result is cased the same way, so a filter cannot turn output into payload keys. `mcp list` and `mcp-tools list` filter only the current page (default `--limit 50`): pass `--limit 1000` and check that `Total` equals `Count`. `platform-services list` / `platform-tools list` refuse a filter without `--limit`.
- `--dry-run` runs the CLI's checks and prints the plan (`Code: DryRun`) without the mutation. `mcp update`, `refresh-tools` and `mcp-tools` mutations still read the server (login, exact slug, folder), and every `mcp update` refusal fires in a dry run too. The service's validation never runs, so a clean dry run does not guarantee the real call succeeds.
- A failure prints `ErrorCode`, `Retry`, `Message`, `Instructions`, and when they apply `NextCommand` (values shell-quoted), `Errors` (fields a 400 rejected) and `Context.HttpStatus`. Act on `ErrorCode`, `Retry` and `Instructions`, not on the exit code. `NextCommand` usually repeats your folder flag, but some name only the verb (`mcp-tools enable --mcp <SLUG>` on a `platform` server, `mcp-tools create-resource --mcp <SLUG> --folder-key <GUID>` on a `uipath` one): add the folder and the required flags before running it.
- Most `--help` examples omit the folder flag (`mcp delete --dry-run` also omits `--yes`, the `mcp-tools update` examples omit `--mcp`), and their output keys are cased differently from the real output: take casing from Rule 3, not from the examples.

## Server Types

`uip agenthub mcp create <TYPE>` shares `--name`, `--slug`, `--description`, `--version`, `--file` / `--body` / `--print-schema`, `--dry-run`, `--folder-path` / `--folder-key`, `--login-validity`. Use exactly one of scalar flags, `--file` or `--body`. The CLI checks no required field (`--print-schema` lists them); the service answers 400 with `Errors`, except a `swagger` create with neither `--spec-url` nor `swaggerContent`, which fails with HTTP 409 `Either SwaggerUrl or SwaggerContent must be provided`.

| Type | Type-specific flags | When to use | Tools from | More in |
|------|---------------------|-------------|------------|---------|
| `uipath`   | _(none)_ | A server you fill with tools that run Orchestrator processes, agents, agentic processes or API workflows. | `mcp-tools create-resource` | [Tools](#tools-uip-agenthub-mcp-tools), [binding](references/tools-guide.md#binding-resources-on-a-uipath-server), [`uipath` updates](references/updating-servers-guide.md#uipath-servers) |
| `coded`    | `--process-key <PROCESS_KEY>` | A published coded MCP **server** package (`uipath-mcp` Python SDK; process type `MCPServer`), started as a job in the server's folder. Not a coded agent. | `refresh-tools` (async) | [payload](references/updating-servers-guide.md#what-a-payload-keeps-or-clears), [refresh errors](references/troubleshooting-guide.md#refresh) |
| `command`  | `--command <CMD>`, `--arg <ARG>` (repeatable, at least one), `--env <KEY>=<VALUE>` (repeatable) | A stdio MCP server Agent Gateway starts as a command (`npx` / `uvx` + package) in a serverless job. | `refresh-tools` (async) | [masked values](references/updating-servers-guide.md#masked-values), [refresh errors](references/troubleshooting-guide.md#refresh) |
| `remote`   | `--uri <URL>`, `--header <NAME>=<VALUE>` (repeatable), `--connection-id <CONNECTION_ID>`, `--use-relay` | An HTTP MCP server hosted elsewhere: a vendor's, or one inside the company network through Relay. | `refresh-tools` (sync) | [masked values](references/updating-servers-guide.md#masked-values), [moving a server](references/updating-servers-guide.md#moving-a-server-to-another-host), [network errors](references/troubleshooting-guide.md#network) |
| `swagger`  | `--spec-url <URL>`, `--header <NAME>=<VALUE>` (repeatable), `--use-relay` | A REST API with an OpenAPI document: one tool per operation. | the spec, on create and `refresh-tools` (sync) | [payload](references/updating-servers-guide.md#what-a-payload-keeps-or-clears), [moving a server](references/updating-servers-guide.md#moving-a-server-to-another-host), [network errors](references/troubleshooting-guide.md#network) |
| `platform` | `--service <SERVICE_NAME>`, then `--tool <TOOL_NAME>` (repeatable) or `--use-all-tools` | A first-party UiPath service (e.g. Test Manager): a chosen tool set, or every tool including ones added later. | the selection, or All tools | [platform selection](references/tools-guide.md#platform-selection-on-a-platform-server), [platform errors](references/troubleshooting-guide.md#platform) |

- **`coded`:** `--process-key` is the process (release) `Key` GUID from `uip or processes list --folder-key <FOLDER_KEY> --process-type MCPServer --output json`, not its `ProcessKey` field (the package name). The process must be in the server's folder, and the service does not check it on create: a wrong key surfaces only when the server runs. `mcp template coded` has placeholder `processKey` / `folderKey`: replace both with GUIDs.
- **`command`:** the service splits `arguments` on spaces, so one `--arg` value cannot contain a space.
- **`remote` / `swagger`:** without `--use-relay` the service blocks private hosts (`URL blocked for security reasons: …`); with it, any absolute `http(s)` URL is reached through Relay (swagger: the spec download and the API calls). On `mcp update`, `--use-relay` / `--no-use-relay` switch Relay; without either the setting is kept. `--connection-id` (remote) is the GUID of an Integration Service connection whose token authenticates the calls: an OAuth connection of connector `uipath-uipath-mcp`, from `uip is connections list <CONNECTOR_KEY> --all-folders --output json` with that connector key.
- **`swagger`:** needs the tenant's Swagger MCP feature (otherwise HTTP 404). `--header` values go with the spec download and every API call. An inline spec (`swaggerContent`) goes only in `--file` / `--body`. `--filter` is accepted but not sent. The create result includes the whole spec: filter it (`--output-filter "{Slug: Slug, McpUrl: McpUrl}"`).
- **`platform`:**
  1. `uip agenthub platform-services list --output json` — match the user's wording to `DisplayName`; pass its `ServiceName`. Several names can share the words (`Test Manager`, `Test Manager External`, `Test Manager Performance Testing`): take the exact match, otherwise ask.
  2. `uip agenthub platform-tools list --service <SERVICE_NAME> --limit 1000 --output-filter "{Names: Items[].Name, Total: Total}" --output json` — the tool names. Unfiltered rows carry JSON Schemas and run to hundreds of KB; `--name <SUBSTR>` searches and returns full rows with `Description`. Read the `Description` of each candidate before picking tools for a request ("list test cases": `Get_test_cases`, not `Get_Automated_Test_Cases_For_Folder`), and tell the user the exact names you picked.
  3. `uip agenthub mcp create platform --name <NAME> --slug <SLUG> --service <SERVICE_NAME> --tool <TOOL_NAME> --tool <TOOL_NAME> --folder-path <FOLDER_PATH> --output json`, or `--use-all-tools` instead of `--tool`.
  4. `uip agenthub mcp-tools list --mcp <SLUG> --folder-path <FOLDER_PATH> --limit 1000 --output-filter "{Names: Items[].Name, Total: Total, Count: Count}" --output json` — the tools it exposes (on an All tools server, every tool of the service).

  `mcp get` shows the service as `Arguments` and the mode as `UseAllTools`. Without Platform MCP on the tenant the two lists fail with `Platform MCP is not enabled on this tenant.`, while `create platform` and a platform `mcp update` return a bare HTTP 404.
- **`selfhosted` / `process-assistant`:** `mcp template` accepts both, but `mcp create` has no such type. A self-hosted server registers itself when the `uipath-mcp` Python runtime starts; the CLI can `list` / `get` / `delete` it and refuses `mcp update` and `refresh-tools` on it. `process-assistant` is a legacy value.

## Updating Servers

`mcp update <SLUG>` reads the server, then sends that type's full update body. Scalar flags change only what they name and cannot be combined with `--file` / `--body`; a payload must carry every field to keep, in camelCase, without `type`. Every type except `uipath` takes `--name`, `--description` and `--version`. A flag the type does not take is refused (`<FLAGS> apply only to <TYPES> servers; '<SLUG>' is a <TYPE> server.`, `applies` after a single flag), and so is `--service`.

| Type | Change it with |
|------|----------------|
| `uipath` | Server fields only through `--file` / `--body` with `{"server": {...}, "tools": [...]}`, every existing tool included. Change tools with `mcp-tools`. |
| `coded` | `--process-key`; `folderKey` stays the server's own folder. |
| `command` | `--command`, `--arg` (replaces all arguments), `--env` (replaces all variables; Rule 4). |
| `remote` | `--uri`, `--header` (replaces all; Rule 4), `--use-relay` / `--no-use-relay`, `--connection-id <CONNECTION_ID>` or `--clear-connection` (with neither, the connection is kept). |
| `swagger` | `--spec-url` (downloads the spec again, regenerates the tools), `--header` (replaces all), `--use-relay` / `--no-use-relay`. |
| `platform` | `--tool` (replaces the whole selection), `--use-all-tools` / `--no-use-all-tools`; without them the selection and mode are kept. On an All tools server, `--tool` needs `--no-use-all-tools`. |
| `selfhosted`, `process-assistant` | Refused. |

Payload fields per type, the `uipath` tools list, masked values and moving a server to another host: [references/updating-servers-guide.md](references/updating-servers-guide.md).

## Tools (`uip agenthub mcp-tools`)

| Verb | Works on |
|------|----------|
| `create-resource`, `create-raw`, `update`, `delete` | `uipath` servers only |
| `enable`, `disable` | `platform` servers only |
| `list`, `get --name <NAME>` | every type |
| `get <TOOL_ID>` | every type except `platform` (404: its tools are not stored) |
| `template`, `candidates` | no server needed |

- **Bind a resource:** pick a row from `mcp-tools candidates --category <CATEGORY> --name <SUBSTR> --output json` (one page, default 50: narrow with `--name`; show the row's `Folder.Name` next to its `Name`), then `uip agenthub mcp-tools create-resource --mcp <SLUG> --name <NAME> --description "<DESCRIPTION>" --category <CATEGORY> --target-identifier <RESOURCE_ID> --target-folder-key <RESOURCE_FOLDER_KEY> --folder-path <FOLDER_PATH> --output json`, with the row's `Id` and `Folder.Key`. Always pass `--description` (the service requires one; when the row has none, write one from the request) and `--category`. `candidates --name` matches substrings (`EchoAgent` also finds `Coded copy of EchoAgent`): take the row whose `Name` matches exactly, and when none or several do, show each `Name` with its `Folder.Name` and ask. A wrong row still creates a working tool, so check that the result's `TargetIdentifier` is the row's `Id`.
- **Platform selection:** `uip agenthub mcp-tools enable` / `disable --mcp <SLUG> --name <TOOL_NAME> --folder-path <FOLDER_PATH> --output json` (repeat `--name`) add or remove those tools and keep the rest. On an All tools server `enable` changes nothing and `disable` is refused: run `uip agenthub mcp update <SLUG> --no-use-all-tools --folder-path <FOLDER_PATH> --output json` first, which keeps every tool selected. `disable` of a name that is not selected, a typo included, succeeds and changes nothing: list the tools first, and when the name is not among them, tell the user instead of running it.
- **Edit a tool:** a tool's own fields change with `mcp-tools update <TOOL_ID>`; `mcp update` changes the server's. Take the id from `mcp-tools list`: `--name` matches substrings with no preference for an exact name. Only `uipath` tools can be edited: the tools of every other type come from their source (URI, spec, command, package, service), and `refresh-tools` rebuilds them from it.
- `mcp-tools template` prints PascalCase (Rule 3); `create-raw` ignores its scalar flags, so use it only with `--file` / `--body`. `mcp-tools update --rename` changes `Name`, not `McpName`, the name MCP clients see.

Flags, defaults, target folders, `update`, `delete`, `get` and paging: [references/tools-guide.md](references/tools-guide.md). Most of it is for `uipath` and `platform` servers; for the other types only its listing section applies.

## Troubleshooting

- **HTTP 400: fields your `--file` contains are "required"** — keys are not camelCase, typically copied from `mcp get`, `mcp-tools list` or `mcp-tools template` (Rule 3). On `create-resource` without `--description`: pass `--description`.
- **`AgentHub requires a folder context. …`** — add a folder flag ([Folder Context](#folder-context)). **`No folder named '<NAME>' was found.`** — a typo, or a personal workspace: pass its `Key` as `--folder-key`.
- **`'<INPUT>' resolves to the MCP server '<SLUG>', …`** — pass the stored `<SLUG>` (Rule 1); if `<INPUT>` is another server's slug, rename `<SLUG>` first. **HTTP 404 on a slug** — wrong folder, or not the slug (Rules 1, 2).
- **`An update of the uipath server '<SLUG>' must carry its tools: …`** — follow [the guide](references/updating-servers-guide.md#uipath-servers), or change tools with `mcp-tools`.
- **`--uri moves '<SLUG>' to another origin, …`** / **`--spec-url gives '<SLUG>' a new spec, …`** (or `The payload's …` for a `--file` / `--body`) — Rule 10.
- **`This command requires a <EXPECTED_TYPE> MCP server; <SLUG> is <TYPE>.`** — the `mcp-tools` verb does not apply to that type. On `coded` / `command` / `remote` / `swagger`, run the `NextCommand` (`refresh-tools`). On `platform`, its `NextCommand` names `mcp-tools enable` without `--name` or the folder: add both.
- **`Platform MCP is not enabled on this tenant.`**, or HTTP 404 on `create platform` — the feature is off on this tenant: use another tenant or server type.

## Reference Navigation

- [references/updating-servers-guide.md](references/updating-servers-guide.md) — payload fields per type, `uipath` server updates, masked values, moving a server to another host.
- [references/tools-guide.md](references/tools-guide.md) — `mcp-tools` on `uipath` servers (bind, update, delete, target folders) and `platform` servers (selection); listing and reading tools on any type.
- [references/troubleshooting-guide.md](references/troubleshooting-guide.md) — every other `uip agenthub` message, with its fix.

## What NOT to Do

- Do NOT guess a platform service or tool name, or assume `orchestrator` (Rule 9).
- Do NOT paste PascalCase CLI output into a payload as it is (Rule 3).
- Do NOT pass a display name or a GUID where a slug goes (Rule 1).
- Do NOT pass `--yes` before the user confirms the delete (Rule 8).
- Do NOT report a `coded` / `command` refresh as done when it returned `Status: "Started"` (Rule 7).
- Do NOT copy a `--help` example without adding the folder flag it omits.
