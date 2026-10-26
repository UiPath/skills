# Integration Service

Interact with external services through UiPath Integration Service: discover connectors, manage connections, and execute operations with the `uip` CLI.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline in each reference file.

## Prerequisites

- Authenticate `uip` with `uip login`.
- Set folder context for folder-scoped connections with `--folder-key`.

## Core Principles

1. **Always follow the workflow** — Connector → Connection → Ping → Discover → Resolve References → Execute.
2. **Never fabricate IDs or values** — List real data (command output) first and use only IDs, keys, or names from that output.
3. **Resolve reference fields before create/update** — Describe output includes `referenceFields`; list each referenced object to obtain valid IDs before executing.
4. **Use `--refresh` once if results are unexpected** — `list` subcommands cache locally. Retry **once** with `--refresh` when results are empty, a recently created item is missing, or the user says data should exist. If still empty, inform the user the data does not exist; do not loop.
5. **Always ping** — Verify every connection before use, even when it reports "Enabled".
6. **Always ask, never auto-select** — Present connections and reference values for confirmation, even when there is only one. Recommend the default, but let the user confirm.
7. **Always use `--output json`** for commands whose output you need to parse or act on.
8. **Use `--operation` on describe** — `is resources describe` returns a compact summary of all operations and fields. Use `--operation Create` to filter to that operation and reduce output size.

---

## Navigation

| When to load | File | For |
|---|---|---|
| Always (first) | This file | Principles, routing, error recovery |
| Any IS task | [agent-workflow.md](agent-workflow.md) | Workflow and checklist |
| Step 1: connector not found | [connectors.md](connectors.md) | HTTP fallback and response fields |
| Step 2: connection selection | [connections.md](connections.md) | Native + HTTP selection and response fields |
| Step 4: discover activities | [activities.md](activities.md) | Activities, triggers, and activities vs resources |
| Steps 4–6: resources | [resources.md](resources.md) | Describe, CRUD, pagination, vendor errors |
| Step 5: resolve references | [reference-resolution.md](reference-resolution.md) | References, dependencies, inference, required fields |
| Managed HTTP Request authoring | [http-request.md](http-request.md) | Modes, `http-request` CLI helper, and worked example |
| Connector exists, activity does not | [activity-generation.md](activity-generation.md) | Vendor-doc activity generation, capability check, converge loop, min.json, metadata, and its `activity-generation/` references |
| Trigger metadata | [triggers.md](triggers.md) | Trigger objects, field metadata, and workflow |

---

## Display Preferences — Names Over UUIDs

**Always show human-readable names when presenting information. Never surface raw UUIDs or internal keys unless the user explicitly asks for technical details.** Use UUIDs and keys only internally for CLI arguments (`--connection-id`, `--folder-key`, etc.).

| CLI field | Show to user | Use internally (CLI args) |
|---|---|---|
| `Name` | **Yes** — always primary | — |
| `Id` | No — use `Name` | `--connection-id` |
| `ConnectorName` | **Yes** — vendor name | — |
| `ConnectorKey` | No — use `ConnectorName` | first arg to `is connections list` |
| `Folder` | **Yes** — folder name | — |
| `FolderKey` | No — use `Folder` | `--folder-key` |
| `Owner` | **Yes** — owner email | — |

When confirming a selection, present the connection name, connector, default/enabled status, and folder name; present reference values by name (Good: "Using connection **bai.li** (Slack, default, enabled) in **Shared** folder." Bad: "Using connection fb06f30e-cde8-4e4a-a534-29cb485971d4."). Clearly present all options using names, not UUIDs, and always ask for confirmation, including when only one option exists; recommend the default without auto-selecting.

- **Connections**: "Which connection? 1) **Salesforce Prod** (default, enabled, Shared folder) 2) **Salesforce Dev** (enabled, Shared folder)"
- **Reference fields**: "Which department? 1) Engineering 2) Sales"

## Error Recovery

| Problem | Recovery |
|---|---|
| Ping returns non-enabled | Run `is connections edit <id>` to re-authenticate, then ping again. If it still fails, ask the user to choose another connection or create a new one. |
| List returns empty after `--refresh` | Inform the user the data does not exist. Do not retry. Suggest checking permissions or folder context. |
| Reference field lookup returns empty | Inform the user that the referenced object has no records. Ask whether to create one or use a different value. |
| Execute fails with error | Read `Instructions`; the CLI passes through the raw vendor error body. Use it to diagnose and fix. See [agent-workflow.md — Error Recovery](agent-workflow.md#error-recovery). |
| Describe returns error | Metadata gap: skip describe and attempt execute directly. See [resources.md — Describe Failures](resources.md#describe-failures). |
| Create fails with read-only field error | Parse the vendor error in `Instructions` for the field name, remove it from `--body`, and retry. |
| Connector not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md](connectors.md#http-connector-fallback). |
| No trigger objects for operation | Check the operation name (CREATED/UPDATED/DELETED, uppercase). Verify the connector supports events (`hasEvents` in connector list). See [triggers.md](triggers.md). |
| Trigger metadata empty | Check that the object name exactly matches `triggers objects` output. Try with `--connection-id` for custom fields. See [triggers.md](triggers.md). |
| Execute fails with 403 (scope) | The connection is Enabled but lacks optional scopes for this activity. Re-authorize with broader scopes via `is connections edit <id>`. See [connections.md](connections.md). |