# Integration Service

Interact with external services through UiPath Integration Service using the `uip` CLI to discover connectors, manage connections, and execute operations.

> Full syntax: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific patterns appear in the referenced files.

## Prerequisites

- Authenticate with `uip login`.
- Use `--folder-key` for folder-scoped connections.

## Core Principles

1. Follow: Connector → Connection → Ping → Discover → Resolve References → Execute.
2. Never fabricate IDs or values. List real data first and select IDs, keys, and names only from command output.
3. Resolve `referenceFields` before create/update by listing each referenced object to obtain valid IDs.
4. Use `--refresh` once when results are empty, recently created data is missing, or the user says data should exist. If still empty, inform the user the data does not exist; do not loop.
5. Ping every connection before use, even when it reports "Enabled".
6. Always ask before selecting connections or reference values, including when there is only one option. Recommend the default, but let the user confirm.
7. Use `--output json` whenever command output must be parsed or acted on.
8. Use `--operation Create` with `is resources describe` to limit output to the Create operation; without it, describe returns a compact summary of all operations and fields.

## Navigation

| When to load | File | For |
|---|---|---|
| Always (first) | This file | Principles, routing, error recovery |
| Any IS task | [agent-workflow.md](agent-workflow.md) | Step-by-step workflow and checklist |
| Step 1: connector not found | [connectors.md](connectors.md) | HTTP fallback and connector response fields |
| Step 2: connection selection | [connections.md](connections.md) | Native + HTTP selection logic and response fields |
| Step 4: discover activities | [activities.md](activities.md) | Activity discovery, trigger activities, activities vs resources |
| Steps 4–6: resources | [resources.md](resources.md) | Describe, CRUD execution, pagination, vendor error recovery |
| Step 5: resolve references | [reference-resolution.md](reference-resolution.md) | Simple references, dependency chains, inference, required-field validation |
| Managed HTTP Request authoring | [http-request.md](http-request.md) | Connector/manual modes, `http-request` CLI helper, worked example |
| Trigger metadata | [triggers.md](triggers.md) | Trigger objects, field metadata, and workflow |

## Display Preferences — Names Over UUIDs

Show human-readable names; never surface raw UUIDs or internal keys unless the user explicitly requests technical details. Use UUIDs and keys internally for CLI arguments such as `--connection-id` and `--folder-key`.

| CLI field | Show to user | Use internally |
|---|---|---|
| `Name` | Yes; primary identifier | — |
| `Id` | No; use `Name` | `--connection-id` |
| `ConnectorName` | Yes; vendor name | — |
| `ConnectorKey` | No; use `ConnectorName` | First argument to `is connections list` |
| `Folder` | Yes; folder name | — |
| `FolderKey` | No; use `Folder` | `--folder-key` |
| `Owner` | Yes; owner email | — |

When confirming, use names: “Using connection **Salesforce Prod** (default, enabled) in **Shared** folder.” For multiple choices, show names plus relevant status, folder, and vendor details; do not show UUIDs. For references, show values by name, such as “Which department? 1) Engineering 2) Sales.”

## Error Recovery

| Problem | Recovery |
|---|---|
| Ping returns non-enabled | Run `is connections edit <id>` to re-authenticate, then ping again. If it still fails, ask the user to choose another connection or create one. |
| List is empty after `--refresh` | Inform the user the data does not exist; do not retry. Suggest checking permissions or folder context. |
| Reference lookup is empty | Inform the user that the referenced object has no records and ask whether to create one or use another value. |
| Execute fails | Read `Instructions`, which contains the raw vendor error body, and diagnose/fix it. See [agent-workflow.md — Error Recovery](agent-workflow.md#error-recovery). |
| Describe returns an error | Skip describe and attempt execution directly. See [resources.md — Describe Failures](resources.md#describe-failures). |
| Create fails with a read-only field error | Parse the vendor error in `Instructions`, remove the named field from `--body`, and retry. |
| Connector not found | Fall back to the HTTP connector (`uipath-uipath-http`). See [connectors.md](connectors.md#http-connector-fallback). |
| No trigger objects for an operation | Check the operation name (`CREATED`/`UPDATED`/`DELETED`, uppercase) and verify `hasEvents` in connector list output. See [triggers.md](triggers.md). |
| Trigger metadata is empty | Match the object name exactly to `triggers objects` output and try `--connection-id` for custom fields. See [triggers.md](triggers.md). |
| Execute fails with 403 (scope) | Re-authorize the Enabled connection with broader scopes via `is connections edit <id>`. See [connections.md](connections.md). |