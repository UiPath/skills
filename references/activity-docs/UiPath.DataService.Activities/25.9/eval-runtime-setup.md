# Eval Runtime Setup — UiPath.DataService.Activities

> **Status**: Future scope. This document describes the CLI-based harness setup, record pre-population, runtime validation, and cleanup procedures that apply once workflow execution (`rpa-legacy debug`) is included in the evaluation pipeline.

---

## Entity Isolation Strategy

Each test execution gets a uniquely named entity to prevent parallel run collisions:

```bash
ENTITY_NAME="EvalEnt_$(date +%s%3N)"   # e.g., EvalEnt_1745000000000
df entities create "$ENTITY_NAME" \
  --body '{ "fields": [...] }' \
  --tenant CodingAgentsEvals
# → returns EntityId passed into agent prompt
```

## Record Pre-population

For scenarios requiring existing data (GetById, Update, Delete, Query, file ops), the harness pre-inserts records before the agent prompt:

```bash
df records insert <entity-id> \
  --body '{"Title": "Pre-existing Record"}' \
  --tenant CodingAgentsEvals
# → returns record ID, passed into agent task prompt
```

## Cleanup

| Resource | Command |
|----------|---------|
| Records created by workflow or pre-inserted | `df records delete <entity-id> <record-id...>` |
| File attachments | `df files delete <entity-id> <record-id> <field-name>` |
| Entity schema | Separate cleanup mechanism (not via CLI) |

## Full Validation Flow (with Runtime)

```
1. [Harness] df entities create EvalEnt_<ts>    → entity-id, field-ids
2. [Harness] df records insert ...              (if pre-population needed)
3. [Agent]   Generate XAML using entity-id, field-ids, record-ids from prompt
4. [Harness] uip rpa get-errors --file-path <xaml> --project-dir <dir> --output json   ← BUILD-TIME
5. [Harness] Parse XAML + df entities get       ← OUTPUT SEMANTICS
6. [Harness] rpa-legacy debug <xaml>            ← RUNTIME EXECUTION
7. [Harness] df records get/query / df files download → assert data-side state
             AND verify OutputEntity values from debug output args
8. [Harness] Cleanup: df records delete / df files delete
```

## CLI Reference (Data Fabric)

| Operation | Command |
|-----------|---------|
| Create entity | `df entities create <name> --body <json>` |
| Get entity schema | `df entities get <entity-id>` |
| Insert record(s) | `df records insert <entity-id> --body <json>` |
| Get record | `df records get <entity-id> <record-id>` |
| Query records | `df records query <entity-id> --body <json>` |
| Delete records | `df records delete <entity-id> <key...>` |
| Upload file | `df files upload <entity-id> <record-id> <field-name> --file <path>` |
| Download file | `df files download <entity-id> <record-id> <field-name>` |
| Delete file | `df files delete <entity-id> <record-id> <field-name>` |

All commands accept `--tenant CodingAgentsEvals` and `--output json`.
