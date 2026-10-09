# Agent Gateway MCP Server Tools

Detail behind [Tools](../SKILL.md#tools-uip-agenthub-mcp-tools). Every verb that takes `--mcp` needs the server's exact slug and its folder ([Folder Context](../SKILL.md#folder-context)).

Which sections apply depends on the server's type:

| Server type | Sections |
|-------------|----------|
| `uipath` | [Binding resources](#binding-resources-on-a-uipath-server), [Changing and removing tools](#changing-and-removing-tools-on-a-uipath-server), [Listing and reading](#listing-and-reading-tools-on-any-server) |
| `platform` | [Platform selection](#platform-selection-on-a-platform-server), [Listing and reading](#listing-and-reading-tools-on-any-server) |
| `coded`, `command`, `remote`, `swagger` | [Listing and reading](#listing-and-reading-tools-on-any-server) only: their tools come from `refresh-tools` ([Rule 7](../SKILL.md#critical-rules)), and no `mcp-tools` verb changes them |

## Binding resources on a `uipath` server

`create-resource` flags: `--mcp <SLUG>`, `--name`, `--description`, `--category <CATEGORY>`, `--target-identifier <RESOURCE_ID>` or `--target-name <NAME>`, `--target-folder-key` / `--target-folder-path`, `--input-schema`, `--output-schema`, `--metadata`, `--file` / `--body`, `--dry-run`, and the server's folder. Each call creates one tool.

1. Discover targets: `uip agenthub mcp-tools candidates --category <CATEGORY> --name <SUBSTR> --output json`. It returns one page (`--limit`, default 50, and `--offset`): when `Total` exceeds `Count`, narrow it with `--name` or page on. Each `Items[]` row has `Id` (the `--target-identifier`), `Name`, `Description`, `Folder {Key, Name}`, `EntityType`, `EntitySubType`. `candidates` is tenant-wide unless you pass a folder flag, which only narrows the search. `--category agent` also lists conversational agents, which the service refuses as tools (`Conversational agents cannot be used as MCP tools: …`).
2. Create: pass `--target-identifier <RESOURCE_ID>` and the row's `Folder.Key` as `--target-folder-key`.

Defaults the service rejects or that surprise:

- Without `--description` the CLI sends an empty string, which the service rejects: always pass it.
- Without `--category` the tool's `processType` is `resource`: always pass it. `--target-name` requires it.
- `--name` falls back to `--target-name`.
- No content flag (`--name`, `--description`, `--category`, `--target-name`, `--target-identifier`, `--input-schema`, `--output-schema`, `--metadata`) can be combined with `--file` / `--body`, on `create-raw` too (`Use exactly one of --file, --body, or scalar options.`). `--target-folder-*` can, and then overrides the payload's `targetFolderKey`.

Target folder, in order of precedence: an explicit `--target-folder-path` / `--target-folder-key` (never both), then the `--target-name` candidate's folder, then the server folder. A `--file` / `--body` payload keeps its own `targetFolderKey` (always set it), which only an explicit `--target-folder-*` overrides.

`--target-name <NAME>` resolves through the catalog within `--category`, searching only the `--target-folder-*` folder when you pass one and the server's own folder otherwise: for a resource in another folder, pass that folder or use `--target-identifier`. An exact (case-sensitive) name match wins; without one, every catalog hit counts, so a single partial match is bound silently: check the result's `TargetIdentifier`. Several matches fail (`Ambiguous --target-name '<NAME>' (<N> matches). Pass --target-identifier <guid>.`, candidates in `Data.candidates`), and so does none (`No <CATEGORY> candidate matched name '<NAME>'.`).

`--metadata`, `--input-schema`, `--output-schema` are optional JSON strings. Build each in a file and pass `--metadata "$(cat metadata.json)"`; do NOT assemble multi-KB JSON inline. Pass `--output-schema "{}"` when the target has no response fields: an empty string fails with `Unexpected end of JSON input`.

`--file` / `--body` take camelCase only: `type`, `name`, `mcpName`, `processType`, `description`, `targetIdentifier`, `targetFolderKey`, `inputSchema`, `outputSchema`, `metadata`. The first six are required, for example `{"type": 0, "name": "<NAME>", "processType": "agent", "description": "<DESCRIPTION>", "targetIdentifier": "<RESOURCE_ID>", "targetFolderKey": "<RESOURCE_FOLDER_KEY>"}`: `type` is 0, `targetIdentifier` and `targetFolderKey` are the candidate row's `Id` and `Folder.Key` (GUIDs), and `processType` is the resource's `--category` value (`automation`, `agent`, `agentic-process`, `api-workflow`). The service does not check `processType` against the target, so set it to match. `mcp-tools template resource` (and `template raw`, the same one) prints this payload with `processType` `automation` whatever you bind: set `processType` and the two ids, and fill in `description`, which it leaves empty. A key in another case (`TargetIdentifier`) is refused ([Rule 3](../SKILL.md#critical-rules)). `mcpName`, the name MCP clients see, is optional; when omitted, the service derives it from `name`. `create-raw` ignores its scalar flags and sends an empty body: use it only with `--file` / `--body`. `--continue-on-error` / `--fail-fast` are deprecated no-ops.

The result is the stored tool (`Id`, `McpName`, `TargetIdentifier`, `TargetFolderKey`, …).

## Changing and removing tools on a `uipath` server

- Select a tool by id (`mcp-tools update <TOOL_ID>`) or by `--name <SUBSTR>`: a case-insensitive substring match, where a tool named exactly that (case-sensitive) wins over the others. Not both. Several matches with no exact one fail (`Found <N> matching tools.`, candidates in `Data.candidates`) unless `--allow-multiple`, which acts on every match.
- `mcp-tools update` sends only the fields you pass: `--rename`, `--description`, `--target-identifier`, `--target-folder-*`, `--input-schema`, `--output-schema`, `--metadata`, or `--file` / `--body`.
- `--rename` changes the tool's `Name`, not its `McpName`, the name MCP clients see. `type`, `processType` and `mcpName` cannot be updated: delete and recreate the tool.
- A new `--target-identifier` without `--target-folder-*` sets `targetFolderKey` to the server folder: pass the target's folder when it lives elsewhere. A `--target-folder-*` flag alone is not an update (`No input provided. …`): pass it with `--target-identifier`.
- `uip agenthub mcp-tools delete <TOOL_ID> --mcp <SLUG> --folder-path <FOLDER_PATH> --yes --output json`, only after the user confirms (several ids may follow). `--name <SUBSTR>` selects as above instead, and with `--allow-multiple` deletes every match. It refuses without `--yes`, even with `--dry-run`, and stops at the first failed delete.

## Platform selection on a `platform` server

`uip agenthub mcp-tools enable --mcp <SLUG> --name <TOOL_NAME> --folder-path <FOLDER_PATH> --output json` (repeat `--name`, or pass a JSON array of names with `--file` / `--body`) adds the tools to the current selection; `disable` removes them and keeps the rest. Tool names come from `uip agenthub platform-tools list --service <SERVICE_NAME>`.

- On an All tools server, `enable` sends nothing: it only checks that the names exist (`Tools not found on <SLUG>: <NAMES>.` otherwise). `disable` is refused (`<SLUG> exposes All tools, so a single tool cannot be disabled.`): run `uip agenthub mcp update <SLUG> --no-use-all-tools --folder-path <FOLDER_PATH> --output json` first, which keeps every current tool selected.
- On a curated server, a name the service does not define fails, also with `--dry-run`: `enable` with `Tools not found in service swagger: <NAMES>`, `disable` with `Tools not found in the <SERVICE_NAME> service: <NAMES>.` A `disable` of a name the service defines but the server does not select succeeds and changes nothing. An empty name is refused (`A tool name cannot be empty.`).
- Both return the server without its selection: confirm with `uip agenthub mcp-tools list --mcp <SLUG> --folder-path <FOLDER_PATH> --output json`.

## Listing and reading tools on any server

- `mcp-tools list --mcp <SLUG>`: `--name <SUBSTR>` filters, `--limit` (default 50) and `--offset` page client-side. `Total` counts the matches, `Count` the rows printed: the list is complete only when they are equal. A slug that does not exist is a 404, not an empty list.
- On a `platform` server, `list` shows every tool of the service when All tools is on, and the selection otherwise.
- `mcp-tools get <TOOL_ID> --mcp <SLUG>` reads one tool (it ignores `--name`). `get --name <SUBSTR>` selects as `update` does and fails on no match, or several with no exact one (`Found <N> matching tools.`); with `--allow-multiple` it returns every match as a list, an empty one when nothing matches. On a `platform` server use `get --name`: its tools are not stored, so `get <TOOL_ID>` returns 404.
- `mcp-tools get` without an id or `--name` is refused before any read.
