# Agent Gateway MCP Server Troubleshooting

Text `uip agenthub` prints in a failure's `Message`, `Instructions` or `Errors` that [SKILL.md](../SKILL.md#troubleshooting) does not list, with its fix. Every failure also carries `Instructions`, and often a `NextCommand`: when no row here matches, follow `Instructions`.

## Input and payloads

| Text | Fix |
|------|-----|
| `HTTP 400: …` with `Errors` | Fix the fields `Errors` lists. Without `Errors`, re-run with `--dry-run` to inspect the resolved body. |
| `Use exactly one input source: …` / `Use exactly one of --file, --body, or scalar options.` | Pass scalar flags or `--file` or `--body`, not a mix. `--no-use-relay`, `--no-use-all-tools`, `--connection-id`, `--clear-connection` and every `mcp-tools` content flag count as scalar flags. |
| `No input provided. …` | Pass scalar flags, `--file <PAYLOAD_FILE>` or `--body <JSON>`. On `mcp create` / `mcp update`, the `NextCommand` (`--print-schema`) lists the fields. |
| `Fix the JSON syntax in …` (Instructions) / `Unexpected end of JSON input` | Fix the JSON; pass `"{}"`, not `""`, for an empty schema. |
| ``MCP server type is immutable. Remove the `type` field from the payload.`` | Remove `type` from the payload. To change the type, delete the server and create it again. |
| `error: unknown command '<TYPE>'` on `mcp create` | `selfhosted` / `process-assistant` cannot be created with the CLI. |
| HTTP 409 `Either SwaggerUrl or SwaggerContent must be provided` | Pass `--spec-url`, or `swaggerContent` in a payload. |

## Folders and slugs

| Text | Fix |
|------|-----|
| `Missing required --folder-key or --folder-path. …` (`refresh-tools`) | Add a folder flag ([Folder Context](../SKILL.md#folder-context)). |
| `--folder-key requires a GUID; use --folder-path for folder names.` | Pass the name as `--folder-path <FOLDER_PATH>`. |
| `Folder name '<NAME>' is ambiguous (<N> matches). …` | Re-run with one of the listed full paths or keys. |
| `Pass either --folder-path or --folder-key, not both.` / `Pass either --all-folders or --folder-key/--folder-path, not both.` | Drop one. |
| `error: unknown option '--folder-path'` | `mcp template`, `mcp-tools template`, `platform-services list` and `platform-tools list` take no folder: drop it. |
| `The FolderKey field is required.` (in `Errors`) on `create coded` | The `--file` / `--body` lacks `folderKey`: add the server folder's GUID, or create with flags, which fill it. |
| HTTP 404 with ``Run `uip agenthub mcp list <FOLDER_FLAG>` to see the server slugs.`` | Wrong folder, or not the slug: find the server with `mcp list --all-folders`. |
| Slug rejected (400, `Errors.Slug`) | Pass `--slug` matching `^[a-z0-9-]+$`, 3-50 characters. |
| `Confirmation required: this will delete … and cannot be undone.` | Ask the user, then add `--yes`. |

## Updates

| Text | Fix |
|------|-----|
| `<FLAGS> apply only to <TYPES> servers; '<SLUG>' is a <TYPE> server.` (`applies` after a single flag: `--uri`, `--process-key`, `--spec-url`) | Run `uip agenthub mcp update <SLUG> --folder-path <FOLDER_PATH> --print-schema --output json` for the fields this type takes. |
| `--service cannot be updated: …` | The service is fixed at creation: create a platform server for the other service. |
| `No stored header '<NAME>' has a masked value to keep, …` / `… is stored as '<STORED_NAME>', …` / `… is stored unmasked, …` | `****` works only under a name `mcp get` shows as `****`, spelled exactly the same ([masked values](updating-servers-guide.md#masked-values)). |
| `The payload's uri moves '<SLUG>' to another origin, …` / `The payload's swaggerUrl gives '<SLUG>' a new spec, …` / `The payload's swaggerContent gives '<SLUG>' a new spec, …` | The payload would send stored credentials to a new host: follow [moving a server](updating-servers-guide.md#moving-a-server-to-another-host). |
| `--uri '<URI>' is not an absolute http or https URL.` / `The payload's uri '<URI>' is not an absolute http or https URL.` | Pass the URI with its scheme and host. |
| `--connection-id and --clear-connection cannot be combined: …` | Pass one of the two. |
| `` `selfhosted` MCP servers are registered by the runtime that serves them and cannot be updated here. `` | Change the server in its runtime and restart the runtime. |

## Refresh

| Text | Fix |
|------|-----|
| `No runtimes available for this MCP server.` | Orchestrator accepted the job start but returned no job: check the server's jobs in Orchestrator (`coded`: its process; `command`: the command and arguments), then refresh again. |
| `HTTP <STATUS>: Orchestrator API Error: …` on `refresh-tools` | Orchestrator refused to start the job (wrong or unpublished process, no robot or license): fix what the message names. |
| `Forbidden (403). …` on `refresh-tools` of a `coded` / `command` server | The caller lacks Jobs.Create in the server's folder. |
| ``Tools on `uipath` MCP servers are manually authored and cannot be refreshed.`` | Add tools with `mcp-tools create-resource`. |
| ``Tools on `selfhosted` MCP servers come from the runtime connected to them …`` | Change the tools in the runtime. |
| `Failed to connect to MCP server: …` / HTTP 504 `Request timeout` | The remote server is unreachable: check the URI, the headers, and Relay for a private host. |

## Platform

| Text | Fix |
|------|-----|
| `Service '<SERVICE_NAME>' is not available or not enabled` / `Platform service '<SERVICE_NAME>' is not offered on this tenant. …` | Pick a `ServiceName` from `platform-services list`, exactly as cased. |
| `Tools not found in service swagger: <NAMES>` / `Tools not found on <SLUG>: <NAMES>.` | Use names from `platform-tools list --service <SERVICE_NAME>`, exactly as cased (`swagger` in the first message is literal). |
| `<SLUG> exposes All tools, so --tool would not change which tools it exposes.` | Add `--no-use-all-tools` to expose only the `--tool` list. |
| `<SLUG> exposes All tools, so a single tool cannot be disabled.` | Run `uip agenthub mcp update <SLUG> --no-use-all-tools --folder-path <FOLDER_PATH> --output json` first. |
| `--tool has no effect with --use-all-tools: …` | Pass one of the two. |
| `--output-filter requires an explicit --limit: …` | Add `--limit 1000` to the platform list. |

## Tools

| Text | Fix |
|------|-----|
| `Conversational agents cannot be used as MCP tools: <NAMES>` | Pick a non-conversational agent. |
| `--target-name requires --category …` / `Ambiguous --target-name …` / `No <CATEGORY> candidate matched name '<NAME>'.` | Pass `--category`; for a resource in another folder pass `--target-folder-*`; or pick an `Id` from `candidates` and pass it as `--target-identifier`. |
| `Found <N> matching tools.` | Several tools matched `--name`: pass a tool id, or `--allow-multiple` to act on every match. `Found 0 matching tools.` (`mcp-tools get`) means none matched: take a name from `mcp-tools list`. |
| `RCS Entities/Search requires the RCS.Search scope. …` (Instructions of a 401 / 403 on `candidates`) | Re-run `uip login`. |

## Network

| Text | Fix |
|------|-----|
| `URL blocked for security reasons: …` (in `Errors`) | A private host without Relay: pass `--use-relay` (a Relay client must reach the host). |
