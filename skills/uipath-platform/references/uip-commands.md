# UiPath CLI (`uip`) Command Reference

> Index of common commands. Use `--help` at any level for full details. Always use `--output json` when parsing output.

## Authentication

| Command | Description |
|---|---|
| `uip login` | Authenticate with UiPath Cloud |
| `uip login status` | Current login status |
| `uip login tenant list` | List tenants |
| `uip login tenant set <name>` | Set active tenant |
| `uip logout` | End session |

## Orchestrator — [Guide](orchestrator-guide.md)

### Folders

| Command |
|---|
| `uip or folders list / create / get / edit / move / delete / runtimes` |

### Jobs — [Guide](jobs-guide.md)

| Command |
|---|
| `uip or jobs list / get / start / stop / restart / resume / logs / traces / healing-data / history` |

### Processes — [Guide](processes-guide.md)

| Command |
|---|
| `uip or processes list / get / create / update-version / rollback` |

### Packages — [Guide](packages-guide.md)

| Command |
|---|
| `uip or packages list / get / versions / entry-points / upload` |
| `uip or feeds list` |
| `uip or attachments download` |

### Machines — [Guide](machines-guide.md)

| Command |
|---|
| `uip or machines list / get / create / edit / delete / assign / unassign` |

### Users & Roles — [Guide](access-control-guide.md)

| Command |
|---|
| `uip or users list / list-in-folder / list-available / get / current / create / edit / delete / assign / unassign / assign-roles` |
| `uip or roles list-permissions / list-roles / get-role / create-role / edit-role / delete-role / list-role-users / set-role-users / list-user-roles / assign` |

### Licenses — [Guide](licenses-guide.md)

| Command |
|---|
| `uip or licenses info / list / toggle` |

## Resources — [Guide](resources/resources-guide.md)

| Command |
|---|
| `uip resources assets list / create` |
| `uip resources queues list / create` |
| `uip resources queue-items list / create` |
| `uip resources storage-buckets list / create` |

## Solution — [Guide](solution-guide.md)

| Command |
|---|
| `uip solution pack / publish / deploy run` |

## Integration Service — [Guide](integration-service/)

| Command |
|---|
| `uip is connectors list / connections list / connections create / connections ping` |

## Test Manager — [Guide](test-manager/test-manager-guide.md)

| Command |
|---|
| `uip tm project list / create` |
| `uip tm testset create / execute` |
| `uip tm testcase create` |
| `uip tm wait / report get` |

## Other

| Command | Description |
|---|---|
| `uip tools list / search / install` | CLI tool extensions |
| `uip rpa --help` | RPA workflow management |
| `uip mcp serve` | Model Context Protocol server |
| `uip codedagents --help` | Python agent development |
