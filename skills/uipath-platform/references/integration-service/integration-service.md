# Integration Service

Interact with external services through UiPath Integration Service — discover connectors, manage connections, and execute operations via the `uip` CLI.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline in each reference file.

## Prerequisites

- `uip` must be authenticated (`uip login`)
- Correct folder context must be set if using folder-scoped connections (`--folder`)

## Core Principles

1. **Always follow the workflow** — Connector → Connection → Ping → Discover → Resolve References → Execute
2. **Never fabricate IDs or values** — Always list real data (command output) before using IDs, keys, or names. Select from command output only.
3. **Resolve reference fields before create/update** — Describe output includes `referenceFields` — list the referenced object to get valid IDs before executing.
4. **Use `--refresh` once if results are unexpected** — The `list` subcommands cache locally. Retry **once** with `--refresh` when: results are empty, a recently created item is missing, or the user says data should exist. If still empty after refresh, inform the user the data does not exist — do not loop.
5. **Always ping** — Verify every connection before use, even if it reports "Enabled"
6. **Always ask, never auto-select** — Always present connections and reference values to the user for confirmation, even if there is only one option. Recommend the default but let the user confirm.
7. **Always use `--output json`** for commands whose output you need to parse or act on.
8. **Use `--operation` on describe** — `is resources describe` returns a compact summary of all operations and fields. Use `--operation Create` to filter to just that operation and reduce output size.

---

## Navigation

| When to load | File | For |
|---|---|---|
| Always (first) | This file | Principles, routing, error recovery |
| Any IS task | [agent-workflow.md](agent-workflow.md) | Step-by-step workflow with checklist |
| Step 1: connector not found | [connectors.md](connectors.md) | HTTP fallback, connector response fields |
| Step 2: connection selection | [connections.md](connections.md) | Selection logic (native + HTTP), response fields |
| Step 4: discover activities | [activities.md](activities.md) | Activity discovery, trigger activities, activities vs resources |
| Steps 4–6: resources | [resources.md](resources.md) | Describe, execute CRUD, pagination, vendor error recovery |
| Step 5: resolve references | [reference-resolution.md](reference-resolution.md) | Simple refs, dependency chains, inferring, required field validation |
| Trigger metadata | [triggers.md](triggers.md) | Trigger objects, trigger field metadata, trigger workflow |

---

## How to Present Choices

When multiple options exist, present them clearly:
- **Connections**: "Which connection? 1) Salesforce Prod (default, enabled) 2) Salesforce Dev (enabled)"
- **Reference fields**: "Which department? 1) Engineering (id: 123) 2) Sales (id: 456)"

## Error Recovery

| Problem | Recovery |
|---|---|
| Ping returns non-enabled | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another connection or create new. |
| List returns empty after `--refresh` | Inform user the data does not exist. Do not retry. Suggest checking permissions or folder context. |
| Reference field lookup returns empty | Inform user — the referenced object has no records. Ask if they want to create one or use a different value. |
| Execute fails with error | Read `Instructions` — the CLI passes through the raw vendor error body. Use it to diagnose and fix. See [agent-workflow.md — Error Recovery](agent-workflow.md#error-recovery). |
| Describe returns error | Metadata gap — skip describe, attempt execute directly. See [resources.md — Describe Failures](resources.md#describe-failures). |
| Create fails with read-only field error | Parse the vendor error in `Instructions` for the field name. Remove it from `--body` and retry. |
| Connector not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md](connectors.md#http-connector-fallback). |
| No trigger objects for operation | Check operation name (CREATED/UPDATED/DELETED, uppercase). Verify connector supports events (`hasEvents` in connector list). See [triggers.md](triggers.md). |
| Trigger metadata empty | Check object name matches exactly from `triggers objects` output. Try with `--connection-id` for custom fields. See [triggers.md](triggers.md). |
| Execute fails with 403 (scope) | Connection is Enabled but lacks optional scopes for this activity. Re-authorize with broader scopes via `is connections edit <id>`. See [connections.md](connections.md). |
