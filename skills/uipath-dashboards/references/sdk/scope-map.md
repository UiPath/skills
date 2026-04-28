# scope-map

SDK class → OAuth scope mapping. In secret-mode these are **informational** (the token already carries the user's permissions), but we write them to `state.json.scopes` and `SECURITY.md` so downstream consumers know what the dashboard exercises.

## Mapping

| SDK class (import path) | Scope |
|---|---|
| `Jobs` (`@uipath/uipath-typescript/jobs`) | `OR.Jobs.Read`, `OR.Folders.Read` |
| `Processes` (`@uipath/uipath-typescript/processes`) | `OR.Execution.Read`, `OR.Folders.Read` |
| `Assets` (`@uipath/uipath-typescript/assets`) | `OR.Assets.Read`, `OR.Folders.Read` |
| `Queues` (`@uipath/uipath-typescript/queues`) | `OR.Queues.Read`, `OR.Folders.Read` |
| `Tasks` (`@uipath/uipath-typescript/tasks`) | `OR.Tasks.Read`, `OR.Folders.Read` |
| `Buckets` (`@uipath/uipath-typescript/buckets`) | `OR.Administration.Read`, `OR.Folders.Read` |
| `Cases`, `CaseInstances` (`@uipath/uipath-typescript/cases`) | `OR.Cases.Read`, `OR.Folders.Read` |
| `Entities`, `ChoiceSets` (`@uipath/uipath-typescript/entities`) | `DataService.Schema.Read`, `DataService.Data.Read` |
| `MaestroProcesses`, `ProcessInstances`, `ProcessIncidents` (`@uipath/uipath-typescript/maestro-processes`) | `OR.Execution.Read`, `OR.Folders.Read` |
| `ConversationalAgent`, `Exchanges`, `Messages` (`@uipath/uipath-typescript/conversational-agent`) | `ConversationalAgents.Traces.Api`, `OR.Folders.Read` |
| `Folders` (`@uipath/uipath-typescript`) | `OR.Folders.Read` |

**Verify exact scope strings** against UiPath Orchestrator External App scope catalog at deploy time — scope names occasionally change with Orchestrator releases.

## Derivation from generated code

To compute a dashboard's scope set:
1. Grep generated code for `new <ClassName>(sdk)` patterns.
2. Map each class to its scope set per the table.
3. Deduplicate + sort.
4. Write to `state.json.scopes`.
5. Mirror into `SECURITY.md` as "Scopes exercised by this dashboard".

## Example

For the agent-health dashboard (Jobs queries + folder list):
```
scopes: ["OR.Folders.Read", "OR.Jobs.Read"]
```

## Why this matters (even in secret-mode)

- **Auditability.** Reviewers can see what a dashboard touches without reading code.
- **Downgrade path.** If v2 introduces scoped tokens, the scope list is the minimum viable scope set.
- **Documentation.** Generated `SECURITY.md` cites the scopes so operators know the dashboard's surface.
