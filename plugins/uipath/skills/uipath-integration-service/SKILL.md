---
name: uipath-integration-service
description: Interact with external services through UiPath Integration Service. Manages connectors, connections, activities, and resources via the CLI. Use when the user says "connect to Salesforce", "list Jira connections", "create a Slack message", "call an API", "use Integration Service", or wants to interact with any third-party service through UiPath.
metadata:
    allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Integration Service Assistant

Interact with external services through UiPath Integration Service — discover connectors, manage connections, explore activities, and execute operations via the `uipcli` CLI. Use `uipcli is <subcommand> --help` to discover available flags and options for any command.

## Prerequisites

- `uipcli` must be authenticated (`uipcli config set`)
- Correct folder context must be set if using folder-scoped connections (`--folder`)

## Core Principles

1. **Always follow the workflow** — Connector → Connection → Ping → Discover → Resolve References → Execute
2. **Never fabricate IDs or values** — Always list real data (command output) before using IDs, keys, or names. Select from command output only.
3. **Resolve reference fields before create/update** — Describe output includes `referenceFields` — list the referenced object to get valid IDs before executing.
4. **Use `--refresh` once if results are unexpected** — The `list` subcommands cache locally. Retry **once** with `--refresh` when: results are empty, a recently created item is missing, or the user says data should exist. If still empty after refresh, inform the user the data does not exist — do not loop.
5. **Always ping** — Verify every connection before use, even if it reports "Enabled"
6. **Prompt, don't assume** — When multiple choices exist (connections, reference values), present options and let the user decide. Only auto-select when there is exactly one valid option.

## CLI Output Format

All `uipcli` commands support `--format <format>` (table, json, yaml, plain).

**Always use `--format json`** for commands whose output you need to parse or act on. JSON output is structured and unambiguous.

---

## Task Navigation

| I need to... | Read these |
|---|---|
| **Understand the full agent workflow** | [references/agent-workflow.md](references/agent-workflow.md) |
| **Work with connectors** (find, list, fallback to HTTP) | [references/connectors.md](references/connectors.md) |
| **Work with connections** (list, create, ping, select) | [references/connections.md](references/connections.md) |
| **Work with activities** (discover actions) | [references/activities.md](references/activities.md) |
| **Work with resources** (CRUD on objects) | [references/resources.md](references/resources.md) |

## Workflow

Follow these steps for every task. For decision trees and edge cases, see [references/agent-workflow.md](references/agent-workflow.md).

## Happy-Path Example

```bash
# 1. Find connector
uipcli is connectors list --filter "salesforce" --format json
# → Key: "uipath-salesforce-sfdc"

# 2. Find connection
uipcli is connections list "uipath-salesforce-sfdc" --format json
# → Id: "abc-123", IsDefault: Yes, State: Enabled

# 3. Ping
uipcli is connections ping "abc-123" --format json
# → Status: Enabled

# 4. Describe the target resource
uipcli is resources describe "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --operation Create --format json
# → requiredFields: [LastName], optionalFields: [FirstName, Email, ...], referenceFields: []

# 5. No referenceFields → skip resolution, go straight to execute

# 6. Execute
uipcli is resources execute create "uipath-salesforce-sfdc" "Contact" \
  --connection-id "abc-123" --body '{"LastName": "Doe", "FirstName": "Jane"}' --format json
```

## How to Present Choices

When multiple options exist, present them clearly:
- **Connections**: "Which connection? 1) Salesforce Prod (default, enabled) 2) Salesforce Dev (enabled)"
- **Reference fields**: "Which department? 1) Engineering (id: 123) 2) Sales (id: 456)"
- **No results after refresh**: "No connections found for this connector. Would you like to create one?"

## Error Recovery

| Problem | Recovery |
|---|---|
| Ping returns non-enabled | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another connection or create new. |
| List returns empty after `--refresh` | Inform user the data does not exist. Do not retry. Suggest checking permissions or folder context. |
| Reference field lookup returns empty | Inform user — the referenced object has no records. Ask if they want to create one or use a different value. |
| Execute fails with validation error | Re-check describe output for required fields. Verify field types and reference IDs are correct. |
| Connector not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md](references/connectors.md). |
