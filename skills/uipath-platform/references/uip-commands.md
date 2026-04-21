# UiPath CLI (uip) Command Reference

> **Quick reference index.** Use `--help` only as a fallback when something doesn't work as expected.

**Global flags for list commands:**
- `--limit <N>` / `--offset <N>` — Pagination. Check `Pagination.HasMore` in output; fetch next page if true.
- `--all-fields` — (Orchestrator tool only) Return full API response instead of curated fields. Use when you need fields not in the default output.
- `--output json` — Always use this when calling programmatically.

---

## Authentication

| Command | Description |
|---|---|
| `uip login` | Authenticate with UiPath Cloud |
| `uip login status` | Show current login status |
| `uip login tenant list` | List available tenants |
| `uip login tenant set <name>` | Set active tenant |
| `uip logout` | End session and clear tokens |

---

## Orchestrator (`or`)

Manage folders, jobs, processes, machines, users, packages, and more. See [orchestrator-guide.md](orchestrator-guide.md). Use `uip or --help` for all subcommands.

| Command | Description |
|---|---|
| `uip or folders list` | List folders the current user has access to |
| `uip or folders list --all` | List all folders in tenant (Standard + Solution). Supports `--type`, `--name`, `--path`, `--top-level`, `--order-by` |
| `uip or folders create <name>` | Create a folder |
| `uip or processes list` | List processes in folder (`--folder-path`) |
| `uip or processes create <name>` | Create process binding |
| `uip or jobs start <process-key>` | Start a job (`--folder-path`, `--input-arguments`) |
| `uip or jobs list` | List jobs (`--folder-path`, `--state`, `--process-name`) |
| `uip or jobs stop <key>` | Stop a running job |
| `uip or machines list` | List machines — tenant-wide or per-folder (`--folder-path`) |
| `uip or machines assign <key>` | Assign machine to folder |
| `uip or users list` | List users (`--username`, `--email`, `--key`) |
| `uip or users set-unattended-execution <key>` | Configure unattended robot for user |
| `uip or packages list` | List automation packages in feed |
| `uip or packages upload <file>` | Upload .nupkg to feed |
| `uip or packages download <key>` | Download .nupkg (`--destination`, key: `PackageId:Version`) |
| `uip or settings list` | List tenant settings |
| `uip or roles list-roles` | List all roles |
| `uip or licenses info` | Get license information |
| `uip or audit-logs list` | View audit logs |

---

## Resource (`resource`)

Manage assets, queues, triggers, storage buckets, libraries, and webhooks. See [resources/resources-guide.md](resources/resources-guide.md). Use `uip resource --help` for all subcommands.

| Command | Description |
|---|---|
| `uip resource assets list` | List assets (`--folder-path`) |
| `uip resource assets create <name>` | Create an asset (`--folder-path`, `--type`) |
| `uip resource queues list` | List queues (`--folder-path`) |
| `uip resource queues create <name>` | Create a queue |
| `uip resource queue-items list` | List queue items (`--folder-path`, `--queue-name`) |
| `uip resource queue-items add <queue-key> <ref>` | Add item to queue |
| `uip resource triggers list` | List triggers (`--type time\|queue\|api`, `--folder-path`) |
| `uip resource triggers create` | Create trigger (`--type`, `--name`, `--cron`, etc.) |
| `uip resource storage-buckets list` | List storage buckets (`--folder-path`) |
| `uip resource storage-buckets create <name>` | Create a bucket |
| `uip resource libraries list` | List libraries in tenant feed |
| `uip resource libraries download <key>` | Download library .nupkg |
| `uip resource webhooks list` | List webhooks |
| `uip resource webhooks create` | Create webhook (`--name`, `--url`, `--events`) |

---

## Solution (`solution`)

Create, pack, publish, and deploy solutions. See [solution-guide.md](solution-guide.md). Use `uip solution --help` for all subcommands.

| Command | Description |
|---|---|
| `uip solution pack <solutionPath> <outputPath>` | Pack solution into .zip |
| `uip solution publish <packagePath>` | Publish solution package |
| `uip solution deploy run` | Deploy a solution |

---

## Integration Service (`is`)

Manage connectors, connections, and resources. See [integration-service/](integration-service/). Use `uip is --help` for all subcommands.

| Command | Description |
|---|---|
| `uip is connectors list` | List all connectors |
| `uip is connections list [connector-key]` | List connections |
| `uip is connections create <connector-key>` | Create a connection |
| `uip is connections ping <connection-id>` | Test connection health |

---

## Test Manager (`tm`)

Manage test projects, test sets, test cases, and executions. See [test-manager/test-manager-guide.md](test-manager/test-manager-guide.md). Use `uip tm --help` for all subcommands.

| Command | Description |
|---|---|
| `uip tm project list` | List test projects |
| `uip tm project create` | Create test project |
| `uip tm testset create` | Create test set |
| `uip tm testset execute` | Execute a test set |
| `uip tm testcase create` | Create test case |
| `uip tm wait` | Wait for execution to complete |
| `uip tm report get` | Get execution report |

---

## Tools Management (`tools`)

| Command | Description |
|---|---|
| `uip tools list` | List installed tools |
| `uip tools search` | Search available tools |
| `uip tools install <package-name>` | Install a tool |

---

## Other Tool Groups

Use `--help` to explore these:

| Group | Command | Description |
|---|---|---|
| **RPA** | `uip rpa --help` | RPA workflow management (XAML) |
| **MCP** | `uip mcp serve` | Start Model Context Protocol server |
| **Coded Agents** | `uip codedagent --help` | Python-based agent development |
