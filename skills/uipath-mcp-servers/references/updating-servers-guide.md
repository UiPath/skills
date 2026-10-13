# Updating Agent Gateway MCP Servers

Detail behind [Updating Servers](../SKILL.md#updating-servers). Read it before an `mcp update` with `--file` / `--body`, before sending a `uipath` server's `tools`, and whenever an update is refused.

`uip agenthub mcp update <SLUG> --folder-path <FOLDER_PATH> --print-schema --output json` prints the update fields for the server's type, in camelCase. Only some fields say what leaving them out does (`name`, `version`, `isActive`, `selectedToolNames` and `useAllTools` do not); the table below covers every type. No update payload takes `slug` or `type`.

## What a payload keeps or clears

In every payload an omitted `name`, `version` or `isActive` is kept, and an omitted `description` is cleared. Scalar flags send the stored description back unless `--description` is passed (`--description ""` clears it).

| Type | `--file` / `--body` |
|------|---------------------|
| `uipath` | `{"server": {...}}`, required. An omitted `tools` keeps every tool ([below](#uipath-servers)). |
| `coded` | `processKey` and `folderKey` are required; `folderKey` must be the server's own folder (`mcp get` shows it). |
| `command` | `command` and `arguments` are required. An omitted `environmentVariables` is cleared. |
| `remote` | `uri` is required. Omitted `headers` are cleared. An omitted, null or stored `connectionId` keeps the connection; `"clearConnectionId": true` removes it (not together with `connectionId`). An omitted `useRelay` turns Relay off. |
| `swagger` | No required field. Omitted or null `headers` are kept, and `"headers": ""` removes them all. `swaggerUrl` downloads the spec again; `swaggerContent` replaces the spec and clears the stored URL unless `swaggerUrl` is sent too; either regenerates the tools, and omitting both keeps them. An omitted `useRelay` turns Relay off. |
| `platform` | `server` is required. `selectedToolNames` replaces the whole selection (omitted means none), and an omitted `useAllTools` means false. |

Scalar flags cannot remove every header of a `remote` or `swagger` server, or every variable of a `command` server: `--header` / `--env` always send at least one entry, and an empty value fails with `Expected <key>=<value>, …`. Use a payload instead.

## `uipath` servers

`--name`, `--description` and `--version` change only the server, and so does a payload without `tools`: `{"server": {"name": …, "description": …, "version": …}}`. Every tool is kept, with its id and guardrails. Change tools with `mcp-tools`: `update` for one tool's fields, `create-resource` to add one, `delete` to remove one.

A payload that sends `tools` replaces every tool, and `"tools": []` removes them all. A list that differs from the stored one in any field recreates every tool with a new id and deletes the tools' guardrails, so send `tools` only to replace the tools on purpose. To build it, read every tool with `uip agenthub mcp-tools list --mcp <SLUG> --folder-path <FOLDER_PATH> --limit 1000 --output json` (check that `Total` equals `Count`) and write each under its camelCase name: `Type`→`type`, `Name`→`name`, `McpName`→`mcpName`, `ProcessType`→`processType`, `Description`→`description`, `TargetIdentifier`→`targetIdentifier`, `TargetFolderKey`→`targetFolderKey`, `InputSchema`→`inputSchema`, `OutputSchema`→`outputSchema`, `Metadata`→`metadata`. Leave out `Id`, `ServerId`, `CreatedAt` and `UpdatedAt`. A key left PascalCase is refused ([Rule 3](../SKILL.md#critical-rules)).

## Masked values

`mcp get` shows secret header and variable values as `****`. The service keeps the stored value only when `****` arrives under a name it holds masked, spelled exactly the same. So the CLI accepts `"<NAME>=****"` (flags), or in a payload a `<NAME>:****` line of `headers` or a `<NAME>=****` line of a command server's `environmentVariables`, only under a name `mcp get` shows with a `****` value. It refuses every other `****`, because the service would store `****` as the value:

- `No stored header '<NAME>' has a masked value to keep, …` — no such masked header: pass the real value.
- `Header '<NAME>' is stored as '<STORED_NAME>', …` — spell the name exactly as stored.
- `Header '<NAME>' is stored unmasked, …` — pass the value `mcp get` shows, e.g. the `%ASSETS/<ASSET_NAME>%` reference.

Variables give the same messages with `Variable`. A command payload line written with `:` instead of `=` is not checked: the service drops it, which deletes that variable. `mcp get` masks secrets either way, so it cannot show afterwards whether a secret was kept.

## Moving a server to another host

A `remote` `--uri` on the same origin (scheme, host and port) changes only the path and keeps the headers and the connection. A new URI must be an absolute `http` / `https` URL. A move to another origin is refused while it would send stored credentials there. A payload gets the same refusals, starting `The payload's uri …`.

1. **The server has its own Integration Service connection** (`--uri moves '<SLUG>' to another origin, <ORIGIN>, and the update keeps the stored Integration Service connection, …`). Add `--clear-connection`, or `--connection-id <CONNECTION_ID>` with a connection for the new host. Passing the stored id again is refused. In a payload: `"clearConnectionId": true` or another `connectionId`.
2. **The server has secret (`****`) or asset-backed (`%ASSETS/…%`) headers** (`… without --header the update would send the stored secret or asset-backed header '<NAME>' there.`, or `headers '<A>' and '<B>'`). Pass `--header` for every header to send to the new host. `"<NAME>=****"` or the same `%ASSETS/<ASSET_NAME>%` value keeps one, and the kept value then goes to the new host. A payload that sends `"headers": null` is refused; leave `headers` out to drop them.
3. **Users have per-user connections on the server** (`… keeps the per-user Integration Service connection of one user, …` or `… connections of <N> users, …`). The CLI has no command to remove them: ask the user to remove them in Agent Gateway, then run the update again.

Example: `uip agenthub mcp update <SLUG> --uri <NEW_URI> --header <NAME>=<VALUE> --clear-connection --folder-path <FOLDER_PATH> --output json`.

**`swagger`.** A new `--spec-url`, or a payload `swaggerUrl` / `swaggerContent`, on a server with secret or asset-backed headers is refused without `--header` (payload `headers`), unless it is the stored spec URL: the service would send those headers to the new spec's host and to the API host it names (`--spec-url gives '<SLUG>' a new spec, …`, or `The payload's swaggerUrl …` / `The payload's swaggerContent …`).

Every one of these refusals also fires with `--dry-run`. Do not delete headers or connections to get past one without the user's consent.

## Other refusals

The other `mcp update` refusals and their fixes are in the troubleshooting guide: [Updates](troubleshooting-guide.md#updates), [Platform](troubleshooting-guide.md#platform) and [Input and payloads](troubleshooting-guide.md#input-and-payloads).
