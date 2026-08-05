# external-workflow task — Planning

Integration Service **external automation**: a workflow that runs in an external system, invoked from the case through an IS connection. Schema type `external-workflow`; packages to `bpmn:ServiceTask`.

Use for an sdd.md task whose `Type:` is `external-workflow`. For a UiPath API workflow → [api-workflow](../api-workflow/planning.md). For a single connector operation → [connector-activity](../connector-activity/planning.md). For an inbound event the case waits on → [connector-trigger](../connector-trigger/planning.md).

## Registry Resolution — there is none

**Do not search the cache. There is no cache file to search.**

External automations are catalogued in TypeCache under project type `IntsvcExternalAutomation`. `uip maestro case registry pull` fetches a different TypeCache slice, so no `IntsvcExternalAutomation` entry exists in `typecache-packages-index.json` or `typecache-activities-index.json` — verified against a `--force`-refreshed cache. `external-workflow` is also absent from `uip maestro case tasks describe --type` and from `uip maestro case registry search --type`.

This is a **CLI coverage gap, not an empty tenant**. Consequences for planning:

1. **Skip the cache lookup entirely.** Do not run a search that will return 0 and then report "0 resources on this tenant" — that statement would be false and sends the user hunting for a resource that is already published.
2. **Do not route this through the Rule 17 empty-lookup gate.** That gate distinguishes creatable from non-creatable types after a genuine 0-match. This is not a 0-match; it is an unreachable index. Go straight to placeholder.
3. **Record the entry in `registry-resolved.json` anyway** (Rule 9 — one object per task), with:
   - `cacheFile: null`
   - `matches: []`
   - `selected: null`
   - `rationale` naming the gap explicitly, e.g. `"external-workflow resources live in the IntsvcExternalAutomation TypeCache slice, which registry pull does not fetch. Not searched — no cache file exists. CLI coverage gap, not a missing tenant resource."`
4. **Report it in the completion output** under external resources, phrased as *attach in Studio Web* rather than *register the resource* — the resource may well already exist.

## When the SDD supplies identity

An sdd.md may carry concrete connector identity for the automation (connection, operation, execution mode). When **all** of the following are present and concrete, plan a resolved task instead of a placeholder:

| Field | sdd.md source |
|---|---|
| `Resolved Resource` | the automation's name |
| `Folder Path` | its folder |
| `Operation` | the external-automation operation (e.g. `RunWorkflow`) |
| `Connection ID` | the IS connection UUID |

Any one of these `<UNRESOLVED>` → placeholder. Partial identity is not bindable; do not half-emit.

## Execution mode — capture it explicitly

The automation runs either synchronously (case waits for the result) or asynchronously (case fires and continues). Read the mode from the SDD's description of whether the case waits.

| SDD says | `execution-mode:` | Emitted `serviceType` |
|---|---|---|
| case waits for the workflow's result | `sync` | `Intsvc.SyncWorkflowExecution` |
| case continues without waiting (default) | `async` | `Intsvc.AsyncWorkflowExecution` |

Record `execution-mode:` on the T-entry **even when it is the default** (Rule 6 — never omit a value that looks like a default). It drives both `data.serviceType` and the `executionType` / `eventMode` context fields, and nothing downstream can re-derive it.

> **Why this matters more than it looks.** If `data.serviceType` is omitted at emission the packager falls back to `Intsvc.SyncWorkflowExecution`, while the Studio Web designer's default is `Intsvc.AsyncWorkflowExecution`. An unrecorded mode therefore silently produces the *opposite* of the designed behavior, and `uip maestro case validate` does not flag it.

## `tasks.md` T-entry shape

Placeholder (the normal outcome):

````markdown
## T14: Add external-workflow task "Sync order to fulfilment system" to "Fulfilment"
```text
<UNRESOLVED: external-workflow "OrderSyncFlow">
Not searched — external automations live in the IntsvcExternalAutomation TypeCache slice,
which `uip maestro case registry pull` does not fetch. No cache file exists to search.
Attach in Studio Web (the automation may already be published).
Wiring notes for upgrade — inputs:
  orderId    = "=vars.orderId"
  customerId = "=vars.customerId"
outputs expected: fulfilmentRef
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

Resolved (SDD supplied full identity):

```markdown
## T14: Add external-workflow task "Sync order to fulfilment system" to "Fulfilment"
- type: external-workflow
- name: "OrderSyncFlow"
- folder-path: "Shared/Fulfilment"
- operation: RunWorkflow
- connection-id: 3f2a91c4-8b17-4d5e-9a02-77c1e4b8d310
- execution-mode: async
- isRequired: true
- runOnlyOnce: false
- activation-mode: sequential
- entry-rule: runs-sequentially
- lane: 2
- inputs:
  - orderId = "=vars.orderId"
  - customerId = "=vars.customerId"
- rationale: "..."
```

Keep `- type: external-workflow` on both shapes — Rule 16's enum value, not the folder name.

## Handoff

Implementation shape → [impl-json.md](impl-json.md).
