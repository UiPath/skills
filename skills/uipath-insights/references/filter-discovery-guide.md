# Filter Discovery Commands

The `filter-*` commands list folders, processes, queues, and machines with recent Insights activity. Use them to resolve an exact scope before a Jobs request. They do not filter Jobs output.

Pass the returned values to `jobs` commands: `FolderKey` to `--folder-key`, `ProcessName` to `--process-name`, `MachineName` to `--machine-name`. There is no key-based flag for processes or machines, and `jobs` has no queue filter at all. Every `jobs` command also needs a time range, which these commands do not supply; see [`jobs-commands-guide.md`](jobs-commands-guide.md).

Keys inside `Data` are PascalCase on the wire. Read `FolderKey`, not `folderKey`.

## Shared Options

```text
--limit <number>     Rows to return, 1 to 10000 (default 50)
--offset <number>    Rows to skip before returning results (default 0)
--output <format>    Output format: table, json, yaml, plain (always use json)
```

## Rules

1. **No time flags.** `--time-range`, `--started-after`, and `--started-before` are rejected as unknown options. Do not add them.
2. **The 30-day window is fixed.** The backend applies a recent-activity window the caller cannot change. A resource idle for longer than 30 days is absent from every result.
3. **`--limit` and `--offset` page the CLI's own copy of the list, not the backend's.** `--limit` defaults to 50, so a 50-row result is a full page rather than a complete list. Read `Pagination.Total` and `Pagination.HasMore` to tell the difference.
4. **Results are permission-bounded.** Folders, processes, and queues are limited to folders the caller can access. Machines are tenant-wide.

## Errors

`filter-*` failures use three `Result` values. Branch on `Result`, not on `ErrorCode` alone.

| `Result` | `ErrorCode` | Exit | Cause |
|---|---|---|---|
| `ValidationError` | `invalid_argument` | 3 | A flag the command does not accept, or a bad value. Commander rejects it before the command runs |
| `AuthenticationError` | `authentication_required` | 2 | 401, or no usable session before any request is sent |
| `Failure` | `permission_denied` | 1 | 403. The caller has no permission on the folders in scope |
| `Failure` | `rate_limited` | 1 | 429. Report it and stop |
| `Failure` | `server_error` | 1 | 5xx backend fault |
| `Failure` | `network_error` | 1 | DNS, socket, proxy, or TLS failure |
| `Failure` | `unknown_error` | 1 | A malformed or misaligned response from the service |

Every failure also carries `Retry`; branch on it as described in SKILL.md Critical Rule 8.

## Commands

### filter-folders list

List folders with recent Insights activity that are visible to the current caller.

```bash
uip insights filter-folders list --output json
```

**Key Data fields:** `FolderName`, `FolderKey`

**Use when:** User asks which folders have recent activity, or a Jobs request needs an exact folder key.

### filter-processes list

List processes with recent Insights activity in visible folders.

```bash
uip insights filter-processes list --output json
```

**Key Data fields:** `ProcessName`, `FolderKey`

**Use when:** User asks which processes are active, or a Jobs request needs the exact process name and folder pairing.

### filter-queues list

List queues with recent Insights activity in visible folders.

```bash
uip insights filter-queues list --output json
```

**Key Data fields:** `QueueName`, `FolderKey`

**Use when:** User needs an exact queue and folder pairing for scope discovery. Do not present the output as queue item metrics.

### filter-machines list

List machines with recent Insights activity, tenant-wide.

```bash
uip insights filter-machines list --output json
```

**Key Data fields:** `MachineName`, `MachineKey`

**Use when:** User asks which machines recently reported activity, or a Jobs request needs an exact machine name.

## Discovery Workflow

1. Run the matching `filter-*` command.
2. If `Pagination.HasMore` is true, either raise `--limit` to fetch the remainder in one call, or page with `--offset` in separate invocations. One invocation per page, no shell loop and no variables:

   ```bash
   uip insights filter-folders list --limit 10000 --output json   # whole list in one call
   uip insights filter-folders list --limit 50 --offset 50 --output json   # or page
   ```

   When paging, stop once `HasMore` is false, or after ten pages. If rows remain after ten pages, report how many were retrieved and that more exist.
3. Match the user's words against the returned name fields.
4. If one row matches, use its exact name or key.
5. If several rows match, ask the user to choose.
6. If no row matches across all pages, report that no visible candidate had activity in the last 30 days. Do not report that the resource does not exist.

For a folder that may exist without recent Insights activity, hand off to `uipath-platform` for the full visible Orchestrator inventory (`uip or folders list --output json`). The folder key is the `Key` field there, not `FolderKey`.
