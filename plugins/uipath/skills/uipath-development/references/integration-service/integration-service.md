# Integration Service

Interact with external services through UiPath Integration Service — discover connectors, manage connections, and execute operations via the `uipcli` CLI.

> Full command syntax and options: [uipcli-commands.md — Integration Service](../uipcli-commands.md#integration-service-is). Domain-specific usage patterns are shown inline in each reference file.

## Prerequisites

- `uipcli` must be authenticated (`uipcli login`)
- Correct folder context must be set if using folder-scoped connections (`--folder`)

## Core Principles

1. **Always follow the workflow** — Connector → Connection → Ping → Discover → Resolve References → Execute
2. **Never fabricate IDs or values** — Always list real data (command output) before using IDs, keys, or names. Select from command output only.
3. **Resolve reference fields before create/update** — Describe output includes `referenceFields` — list the referenced object to get valid IDs before executing.
4. **Use `--refresh` once if results are unexpected** — The `list` subcommands cache locally. Retry **once** with `--refresh` when: results are empty, a recently created item is missing, or the user says data should exist. If still empty after refresh, inform the user the data does not exist — do not loop.
5. **Always ping** — Verify every connection before use, even if it reports "Enabled"
6. **Prompt, don't assume** — When multiple choices exist (connections, reference values), present options and let the user decide. Only auto-select when there is exactly one valid option.
7. **Always use `--format json`** for commands whose output you need to parse or act on.

---

## Navigation

| When to load | File | For |
|---|---|---|
| Always (first) | This file | Principles, routing, error recovery |
| Any IS task | [agent-workflow.md](agent-workflow.md) | Step-by-step workflow with checklist |
| Step 1: connector not found | [connectors.md](connectors.md) | HTTP fallback, connector response fields |
| Step 2: connection selection | [connections.md](connections.md) | Selection logic (native + HTTP), response fields |
| Step 4: discover activities | [activities.md](activities.md) | Activity discovery, activities vs resources |
| Steps 4–6: resources | [resources.md](resources.md) | Describe, resolve references, execute CRUD |

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
| Execute fails with validation error | Re-check describe output for required fields. Verify field types and reference IDs are correct. |
| Describe returns empty `availableOperations` | Metadata gap — do **not** retry with `--refresh`. Skip describe, attempt execute directly. See [resources.md — Describe Failures](resources.md#describe-failures). |
| Create fails with `INVALID_FIELD_FOR_INSERT_UPDATE` | Field is read-only/auto-generated. Remove it from `--body`, use alternative writable field, and retry. See [resources.md — Read-Only Field Recovery](resources.md#read-only-field-recovery). |
| Connector not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md](connectors.md#http-connector-fallback). |
