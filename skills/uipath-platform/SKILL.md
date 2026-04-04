---
name: uipath-platform
description: "UiPath development environment assistant — authentication, Orchestrator management (folders, jobs, processes, packages, machines, users, roles, licenses, assets, queues, storage buckets), solution lifecycle (pack, publish, deploy), Integration Service, Test Manager, and CLI tools. TRIGGER when: User asks about UiPath platform operations (authentication, Orchestrator, folders, assets, robots, queues, packages, processes, jobs, machines, users, roles, licenses, storage buckets); User asks about solution lifecycle (pack, publish, deploy, activate); User references Integration Service connectors or connections; User wants to manage resources (assets, queues, storage buckets); User wants to use Test Manager; User wants to use uip CLI commands; User asks about environment setup, credentials, or tenant configuration. DO NOT TRIGGER when: User is writing or editing workflow code (use uipath-coded-workflows or uipath-rpa-workflows instead), or asking how to automate a specific task within a workflow."
metadata: 
   allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Development Environment Assistant

## Auth Token Location

CLI stores credentials at **`~/.uipath/.auth`** after login:
```
UIPATH_URL=https://alpha.uipath.com
UIPATH_ORG_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

Reuse for direct REST API calls when CLI lacks coverage.

## Quick Start

### 1. Authenticate

```bash
uip login --output json
```

Custom authority (e.g., alpha.uipath.com):
```bash
uip login --authority "https://alpha.uipath.com/identity_" --it --output json
```

CI/CD (non-interactive):
```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --output json
```

### 2. Select Tenant

```bash
uip login tenant list --output json
uip login tenant set "<TENANT_NAME>" --output json
```

### 3. Explore Orchestrator

```bash
uip or folders list --output json
```

### 4. Choose Operation from Task Navigation

## Task Navigation

| I need to... | Read |
|---|---|
| **Authenticate / manage tenants** | [uip-commands.md](references/uip-commands.md) |
| **Manage folders** | [orchestrator-guide.md](references/orchestrator-guide.md) |
| **Manage jobs** (start, stop, monitor, logs, traces) | [jobs-guide.md](references/jobs-guide.md) |
| **Manage processes** (create, update, rollback) | [processes-guide.md](references/processes-guide.md) |
| **Manage packages** (upload, versions, entry points) | [packages-guide.md](references/packages-guide.md) |
| **Manage machines** (create, assign, runtimes) | [machines-guide.md](references/machines-guide.md) |
| **Manage users and roles** | [access-control-guide.md](references/access-control-guide.md) |
| **Manage licenses** | [licenses-guide.md](references/licenses-guide.md) |
| **Manage resources** (assets, queues, storage buckets) | [resources-guide.md](references/resources/resources-guide.md) |
| **Set up triggers / schedules / webhooks** (UI only) | [orchestrator-guide.md - UI-Only](references/orchestrator-guide.md#ui-only-operations-no-cli-support) |
| **Create / pack / publish / deploy solutions** | [solution-guide.md](references/solution-guide.md) |
| **Use Test Manager** | [test-manager-guide.md](references/test-manager/test-manager-guide.md) |
| **Use Integration Service** | [integration-service.md](references/integration-service/integration-service.md) |
| **Full CLI reference** | [uip-commands.md](references/uip-commands.md) |
| **Build/run coded workflows** | [/uipath-coded-workflows](/uipath-coded-workflows:uipath-coded-workflows) |

## Resolving UiPath Studio

1. Check for running instance: `rpa-tool list-instances --output json`
2. Try default: `rpa-tool start-studio --output json`
3. If that fails — **ask the user** for the Studio path. Do not search the filesystem.
4. With path: `rpa-tool start-studio --studio-dir "<STUDIO_DIR>" --output json`

## CLI Overview

| Group | Prefix | Description |
|---|---|---|
| Authentication | `login`, `logout` | OAuth2, client credentials, tenant management |
| Orchestrator | `or` | Folders, jobs, processes, packages, machines, users, roles, licenses |
| Resources | `resources` | Assets, queues, queue items, storage buckets |
| Solutions | `solution` | Pack, publish, deploy |
| Integration Service | `is` | Connectors, connections |
| Test Manager | `tm` | Projects, test sets, executions, reports |
| Tools | `tools` | CLI extensions |

### Global Options

| Option | Description |
|---|---|
| `--output json` | **Always use** when parsing output |
| `--verbose` | Debug logging |
| `--help` | Command help |

> **Known issue:** Some `uip or` subcommands ignore `--output json` in interactive terminals. Parse table output as fallback.

## Deployment Lifecycle

```
Develop → Validate (uip rpa get-errors) → Pack (uip solution pack) → Login → Publish → Deploy
```

- **Error 2818** "no runtimes configured" — assign machine templates with Unattended runtimes to the folder.
- **REST API fallback** — use token from `~/.uipath/.auth`. See [orchestrator-guide.md - REST API](references/orchestrator-guide.md#rest-api-fallback).

## References

- [CLI Command Reference](references/uip-commands.md)
- [Orchestrator Guide](references/orchestrator-guide.md)
- [Resources Guide](references/resources/resources-guide.md)
- [Solution Guide](references/solution-guide.md)
- [Test Manager Guide](references/test-manager/test-manager-guide.md)
- [Integration Service](references/integration-service/integration-service.md)
