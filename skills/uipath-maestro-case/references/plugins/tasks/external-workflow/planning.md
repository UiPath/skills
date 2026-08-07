# external-workflow task — Planning

Integration Service **external automation**: a workflow that runs in an external system, invoked from the case through an IS connection. Schema type `external-workflow`; packages to `bpmn:ServiceTask`.

Use for an sdd.md task whose `Type:` is `external-workflow`. For a UiPath API workflow → [api-workflow](../api-workflow/planning.md). For a single connector operation → [connector-activity](../connector-activity/planning.md). For an inbound event the case waits on → [connector-trigger](../connector-trigger/planning.md).

> **CLI dependency.** Resolution below requires a `uip` build that indexes the external-automation connector catalog. Where it does not, the index file is absent and every external-workflow task falls back to a placeholder — see [§ Unindexed CLI](#unindexed-cli--placeholder-fallback).

## Registry Resolution

External automations are connector activities served from a separate TypeCache slice (`projectType=IntsvcExternalAutomation`). They resolve through the **standard connector pipeline**, just against their own index.

**Primary cache file:** `~/.uip/case-resources/typecache-external-automation-activities-index.json`

Sibling indexes exist for triggers and packages (`…-external-automation-triggers-index.json`, `…-external-automation-packages-index.json`). The three external-automation indexes are disjoint from the regular `typecache-*` ones — an `uiPathActivityTypeId` in one never appears in another — so **do not cross-type fallback** into `typecache-activities-index.json`.

### Step 1 — find the activity

Search the external-automation index by the SDD's automation name:

```bash
uip maestro case registry search "<name>" --type typecache-external-automation-activities --output json
```

Capture `Resource.UiPathActivityTypeId` and `Resource.Configuration` (a JSON **string** — parse it) which carries `connectorKey`, `objectName`, and `subType`.

### Step 2 — pick a connection

```bash
uip maestro case registry get-connection --type typecache-external-automation-activities --activity-type-id <uiPathActivityTypeId> --output json
```

`Data.Connections[]` lists candidates. **Check `State`** — a connection in `State: "Failed"` still resolves metadata but cannot execute. Record the state in `registry-resolved.json`; if every candidate is `Failed`, resolve the task but flag it in `build-issues.md` rather than silently binding a broken connection. If more than one connection is healthy and the SDD does not name one, use AskUserQuestion.

### Step 3 — fetch the contract

```bash
uip maestro case tasks describe --type external-workflow --id <uiPathActivityTypeId> --connection-id <connectionId> --output json
```

`--connection-id` is **required** — omitting it fails with `--connection-id is required for external-workflow type`. The response carries `Inputs[]` and `Outputs[]` in the same shape as any connector activity. Typical Power Automate contract:

- `pathParameters` (`json`) and `queryParameters` (`json`) — the latter carries `FieldDefinitions` naming the real user-facing fields (e.g. `WorkflowId` → wire name `workflow_id`, display `Flow`, required)
- `response` (`jsonSchema`) — the flow's return payload

**Never fabricate this contract.** The field names are connector-specific; read them from `describe`.

### Step 4 — persist

Record in `registry-resolved.json` (Rule 9) with `cacheFile: "typecache-external-automation-activities-index.json"`, the full exact-name match set, and `selected` carrying the `uiPathActivityTypeId`, `connectionId`, and connection `State`.

## Unindexed CLI — placeholder fallback

When `typecache-external-automation-activities-index.json` does not exist **after a successful `registry pull`**, this CLI does not index the external-automation catalog. This is a **CLI coverage gap, not an empty tenant** — the automation may well be published.

1. Skip the lookup; do not report "0 resources on this tenant."
2. Do not route through the Rule 17 empty-lookup gate — that gate is for genuine 0-match results, not an unreachable index.
3. Emit the placeholder per [impl-json.md § Placeholder shape](impl-json.md#placeholder-shape-fallback).
4. Record the entry in `registry-resolved.json` with `cacheFile: null`, `matches: []`, `selected: null`, and a rationale naming the missing index and the CLI dependency.
5. In the completion report, phrase it as *upgrade the CLI, or attach in Studio Web* — not *register the resource*.

## Execution mode — capture it explicitly

The automation runs either synchronously (case waits for the result) or asynchronously (case fires and continues). Read the mode from the SDD's description of whether the case waits.

| SDD says | `execution-mode:` | Emitted `serviceType` |
|---|---|---|
| case waits for the workflow's result | `sync` | `Intsvc.SyncWorkflowExecution` |
| case continues without waiting (default) | `async` | `Intsvc.AsyncWorkflowExecution` |

Record `execution-mode:` on the T-entry **even when it is the default** (Rule 6 — never omit a value that looks like a default). It drives both `data.serviceType` and the `executionType` / `eventMode` context fields, and nothing downstream can re-derive it.

> **Why record it even when defaulted.** If `data.serviceType` is omitted at emission the packager falls back to `Intsvc.SyncWorkflowExecution`, while the Studio Web designer's default is `Intsvc.AsyncWorkflowExecution`. An unrecorded mode therefore produces an artifact that differs from what the designer would have written for the same case, and `uip maestro case validate` does not flag the difference.
>
> **Scope of the consequence.** For the Power Automate connector the runtime waits for a response either way — vendor behavior, per the connector's user guide — so the practical impact today is artifact fidelity and round-trip stability, not a changed execution outcome. Treat the mismatch as a correctness issue in what we emit, not as evidence of a runtime defect, and do not report it to users as one.

## `tasks.md` T-entry shape

Resolved (the normal outcome on a current CLI):

```markdown
## T14: Add external-workflow task "Sync order to fulfilment system" to "Fulfilment"
- type: external-workflow
- activity-type-id: 5286269b-e305-3e83-9ac9-342bbdc4274d
- connector-key: uipath-microsoft-powerautomate
- object-name: triggerFlow
- connection-id: b7d7d2bf-02a8-4651-b82b-9c3f84b2c13d
- name: "OrderSyncFlow"
- folder-path: "Shared/Fulfilment"
- execution-mode: async
- isRequired: true
- runOnlyOnce: false
- activation-mode: sequential
- entry-rule: runs-sequentially
- lane: 2
- inputs:
  - queryParameters.WorkflowId = "<flow id>"
- rationale: "..."
```

Placeholder (older CLI, or automation genuinely absent):

````markdown
## T14: Add external-workflow task "Sync order to fulfilment system" to "Fulfilment"
```text
<UNRESOLVED: external-workflow "OrderSyncFlow">
typecache-external-automation-activities-index.json not present after registry pull —
this CLI does not index the external-automation catalog.
Upgrade the CLI and re-run planning, or attach in Studio Web.
Wiring notes for upgrade — inputs:
  orderId    = "=vars.orderId"
  customerId = "=vars.customerId"
outputs expected: response
```
- type: external-workflow
- isRequired: true
- runOnlyOnce: false
- activation-mode: sequential
- entry-rule: runs-sequentially
- execution-mode: async
- lane: 2
- rationale: "..."
````

Keep `- type: external-workflow` on both shapes — Rule 16's enum value, not the folder name.

## Handoff

Implementation shape → [impl-json.md](impl-json.md).
