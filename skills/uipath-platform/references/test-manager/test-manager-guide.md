# Test Manager Tool Guide

CLI tool for UiPath Test Manager (`uip tm`). Use `uip tm --help` and `uip tm <group> --help` to discover all commands and options.

> **Always use `--output json`** when calling commands programmatically.

## Overview

All commands require authentication (`uip login`). Command groups:

- `project` — Test project CRUD and folder assignment
- `testset` — Test set CRUD, assign test cases, execute
- `testcase` — Test case CRUD, link/unlink automations
- `execution` — Retry failed executions
- `wait` — Wait for execution to complete
- `result` / `report` / `attachment` — Download results, reports, and attachments

---

## Key Commands

| Command | Description |
|---------|-------------|
| `uip tm project list` | List test projects |
| `uip tm project create --name <name> --project-key <key>` | Create test project |
| `uip tm testset create --project-key <key> --name <name>` | Create test set |
| `uip tm testset add-testcases --test-set-key <key> --test-case-keys <keys>` | Add test cases to set (comma-separated, e.g. `INV:1,INV:2`) |
| `uip tm testset execute --test-set-key <key>` | Execute a test set |
| `uip tm testcase create --project-key <key> --name <name>` | Create test case |
| `uip tm testcase link-automation --project-key <key> --test-case-key <key> ...` | Link Orchestrator automation to test case |
| `uip tm wait --execution-id <uuid>` | Wait for execution to complete (default timeout: 1800s) |
| `uip tm report get --execution-id <uuid>` | Get execution report |
| `uip tm attachment download --execution-id <uuid>` | Download execution attachments |
| `uip tm execution retry --execution-id <uuid>` | Retry failed execution |

> Keys use the format `PROJECT:ID` (e.g., `INV:42`).

---

## Common Patterns

### Create and Run Tests

```bash
uip tm project create --name "Invoice Tests" --project-key "INV" --output json
uip tm testcase create --project-key "INV" --name "Validate Invoice" --output json
uip tm testset create --project-key "INV" --name "Regression" --output json
uip tm testset add-testcases --test-set-key "INV:1" --test-case-keys "INV:1" --output json
uip tm testset execute --test-set-key "INV:1" --output json
uip tm wait --execution-id "<EXEC_ID>" --output json
uip tm report get --execution-id "<EXEC_ID>" --output json
```

### Review Failed Tests

```bash
uip tm report get --execution-id "<EXEC_ID>" --output json
uip tm attachment download --execution-id "<EXEC_ID>" --only-failed --result-path ./failed/ --output json
uip tm execution retry --execution-id "<EXEC_ID>" --output json
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Project key conflict | Use a unique project key |
| Invalid test-set-key format | Use format `PROJECTKEY:NUMBER` (e.g., `INV:42`) |
| Execution not found | Verify the execution ID from `testset execute` output |
| RBAC error on project update | Check tenant RBAC settings and user roles |
| Test set has no assigned test cases | Add test cases with `testset add-testcases` before executing |
| HTTP 403 Forbidden | User lacks permissions on the target folder — check folder access in Orchestrator |
| No attachments found | Test case automation didn't produce screenshots/logs |

> If a command fails unexpectedly:
> 1. Verify the command syntax: `uip tm <command> --help`
> 2. Check authentication: `uip login status`
> 3. As a last resort, update the tool: `uip tools install @uipath/test-manager-tool`
