# UiPath CLI (uip) Command Reference

> **Quick reference index.** This lists only the most common commands. Every tool group has many more subcommands — use `--help` at any level to discover them (e.g., `uip or --help`, `uip resource --help`, `uip tm testcase --help`).

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

Manage folders, jobs, and processes. See [orchestrator-guide.md](orchestrator-guide.md). Use `uip or --help` for all subcommands.

| Command | Description |
|---|---|
| `uip or folders list` | List all folders |
| `uip or folders create <name>` | Create a folder |
| `uip or jobs start <folder-id> <release-key>` | Start a job |
| `uip or processes list <folder-id>` | List processes in a folder |

---

## Resource (`resource`)

Manage assets, queues, and storage buckets. See [resources/resources-guide.md](resources/resources-guide.md). Use `uip resource --help` for all subcommands.

| Command | Description |
|---|---|
| `uip resource assets list <folder-id>` | List assets |
| `uip resource assets create <folder-id> <name> <value>` | Create an asset |
| `uip resource queues list <folder-id>` | List queues |
| `uip resource queues create <folder-id> <name>` | Create a queue |
| `uip resource queue-items list <folder-id>` | List queue items |
| `uip resource queue-items create <folder-id> <queue-name>` | Add item to queue |
| `uip resource storage-buckets list <folder-id>` | List storage buckets |
| `uip resource storage-buckets create <folder-id> <name>` | Create a bucket |

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
