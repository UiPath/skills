# bindings_v2.json Sync

Sync `bindings_v2.json` after plugins write top-level `bindings[]` in `caseplan.case`. Output shape is independent of the source.

## When to Run

**Batch, not per task.** Only `uip solution resources refresh` consumes this file, once before upload/debug. Run sync only at:

1. **End of Phase 2 Step 9** (after all non-connector tasks): covers process/agent/rpa/action/api-workflow/function/business-rule/case-management bindings.
2. **End of Phase 3 Step 9.7** (after connector tasks): adds Connection bindings and populates the IS cache for tasks.
3. **End of Phase 3 Step 10.5** (after Phase 2 connector-rule stubs are upgraded across stage-entry, stage-exit, case-exit, and task-entry): adds Connection bindings and IS-cache entries for resolved rules. Phase 2 stubs add none; without this sync, rule-introduced Connection/Folder bindings and cache entries are absent when `resource refresh` runs.

Individual task/rule plugins write per-target bindings to top-level `bindings[]`; batch regeneration reads that complete array once.

## § Regenerate bindings_v2.json

After writing top-level `bindings[]`, run:

```bash
uip maestro case bindings sync "<SolutionDir>/<ProjectName>/caseplan.case" --output json
```

It reads root `bindings[]`, groups entries by `resourceKey`, and fully overwrites `bindings_v2.json` beside the plan. Response `Data`: `BindingsPath`, `ResourceCount`, `ConnectionCount`. **Never author or edit `bindings_v2.json` by hand**: incorrect field names are invisible to `solution resources refresh` and fail silently at deploy. If the installed CLI lacks `bindings sync`, derive the file from the shapes below as a last resort and say so in the completion report.

### What the command emits

`caseplan.case` stores two entries per resource (one per property); `bindings_v2.json` stores one entry per resource with properties under `value`. These shapes explain Check 7; do not type them manually.

### Non-connector resource entry

```json
{
  "resource": "<resource>",
  "key": "<resourceKey>",
  "value": {
    "name": { "defaultValue": "<name binding default>" },
    "folderPath": { "defaultValue": "<folderPath binding default>" }
  },
  "metadata": { "BindingsVersion": "2.2", "subType": "<resourceSubType — omit if none>" }
}
```

**Inline-built sibling exception (agent / api-workflow / business-rule):** `value.folderPath.defaultValue` is always `"solution_folder"` (resource identity), not the caseplan `folderPath` binding `default` (`""` for an inline sibling). The sidecar retains this sentinel while runtime `folderPath` remains `""`; they are intentionally decoupled. `value.name.defaultValue` and `metadata.subType` (`"Agent"` / `"Api"` per kind; omitted for a business rule) follow the caseplan binding. Full rationale: the inline-built-sibling decoupling blockquote later in this file.

### Connector resource entry

```json
{
  "resource": "Connection",
  "key": "<connectionId>",
  "value": {
    "ConnectionId": { "defaultValue": "<connectionId>" },
    "folderKey": { "defaultValue": "<folderKey>" }
  },
  "metadata": { "connector": "<connectorKey>" }
}
```

Use casing `ConnectionId` (capital C). `@uipath/solution-sdk` reader `sync-resources-from-bindings.ts` looks up `value.ConnectionId.defaultValue` and falls back to the entry `key`; the api-workflow bindings writer emits the same form. The earlier lowercase-reader note about `syncConnectionResources` was wrong: no such CLI function exists.

File envelope: `{ "version": "2.0", "resources": [ /* one entry per resource */ ] }`.

## § Populate IS connection cache

After `get-connection` succeeds (Step 1), connector plugins must populate the local cache used by `uip solution resources refresh`. This applies to connector **tasks** (Step 9.7), connector **triggers** (Step 6.1), and **condition-rule upgrades** in all four scopes (Step 10.5).

**Path:** `~/.uipath/cache/integrationservice/<connectorKey>/connections.json`

**Shape — bare JSON array:**

```json
[
    {
        "id": "<connectionId>",
        "name": "<connectionName>",
        "connectorKey": "<connectorKey>",
        "connectorName": "<connectorName>",
        "folderKey": "<folderKey>",
        "folderName": "<folderName>"
    }
]
```

Populate fields from: `id` = `connection-id` from `registry-resolved.json` (Planning); `name` = `.Data.Connections[selected].Name`; `connectorKey` = `connector-key` from `registry-resolved.json` (Planning); `connectorName` = `.Data.Connections[selected].Connector.Name`; `folderKey` = `.Data.Connections[selected].Folder.Key`; `folderName` = `.Data.Connections[selected].Folder.Name` (the latter four from `get-connection`, Step 1).

1. Read the cache; if absent, use `[]`.
2. If an entry with the same `id` exists, skip it; otherwise append it.
3. Write a bare JSON array, **not** `{ cachedAt, data }`.

Run:

```bash
mkdir -p ~/.uipath/cache/integrationservice/<connectorKey>
```

This direct write avoids CLI bugs involving a tenant-ID prefix in the path and wrapped `{ cachedAt, data }` format.

## What `resource refresh` produces

With `bindings_v2.json` and the IS cache present, `uip solution resources refresh` creates:

| Input | Output | Purpose |
|---|---|---|
| Non-connector bindings in `bindings_v2.json` | `resources/solution_folder/process/<subType>/<name>.json` **and** `package/<packageName>.json` | Orchestrator resource declarations: **two** files per binding (process/app and package); `resources remove` on the process/app deletes both. |
| Connection binding plus IS cache | `resources/solution_folder/connection/<connectorKey>/<name>.json` | Connection declaration |
| Both | `userProfile/<userId>/debug_overwrites.json` | Maps abstract resources to Orchestrator instances for debug |

All three are required for `uip solution upload` and `uip maestro case debug` without `Resource is not configured` warnings.

> `refresh` never removes. See [§ Prune orphaned solution resources](#prune-orphaned-solution-resources).

> **Inline-built siblings (agent / api-workflow / business-rule):** `bindings_v2` identity and caseplan runtime `folderPath` are **DECOUPLED**. Keep resource identity at the `solution_folder` sentinel in `bindings_v2.json` `key` (`"solution_folder.<name>"`), `value.folderPath.defaultValue` (`"solution_folder"`), caseplan `resourceKey`, and `resources/solution_folder/…` path. However, the caseplan task's `folderPath` binding `default` MUST be `""` (co-located runtime folder), not the sentinel; `"solution_folder"` causes invocation failure with `folder not exist`. The sibling must be registered in the `.uipx`. Full rationale (deploy provisioning, runtime invocation): [create-inline-common.md § Step 3](plugins/tasks/create-inline-common.md#step-3--binding-invariants); per-type debug behavior in each type's § Step 3.

## Cleanup on task or rule removal

When removing a task or connector condition rule and pruning its root bindings per [case-editing-operations.md](case-editing-operations.md) § Delete a node / § Delete a condition rule / § Delete a task:

1. Regenerate `bindings_v2.json` from the updated array.
2. Prune the orphaned solution resource — [§ Prune orphaned solution resources](#prune-orphaned-solution-resources).

## Prune orphaned solution resources

A repoint (changed `resourceKey`) or removal leaves the old registry resource. `refresh` is additive-only, never prunes, and still reports `Warnings: []`.

Symptom: Studio Web `prepareForCustomDebug` fails with `Sequence contains no matching element` (`errorCode 2106`); FE shows *"Resource provisioning failed"*. `uip maestro case validate` remains `Valid` because it never reads the registry.

After regenerating `bindings_v2.json` and running `resources refresh`:

1. Run `uip solution resources list --solution-folder <SolutionDir> --source local --output json`.
2. Match each entry to `bindings_v2.json` `resources[]`:
   - `connection`: match `Key` (connection UUID) to the Connection entry's `key`.
   - `process` / `app`: match **`Name`** to `value.name.defaultValue`; **`Key` does NOT match** because the registry uses the Orchestrator entity UUID while `bindings_v2.json` uses `<folderPath>.<name>`.
   - **Skip `package` entries**; never target one directly. Removing its owning `process` / `app` cascades to that resource's own package declaration (the one named by its `dependencies[]`); sibling resources and packages are untouched.
   - **Never prune the case project's own `process` + `package` pair** (`Name` == the case project): `solution projects add` creates it, not a binding, so it is intentionally absent from `bindings_v2.json`.
3. Remove every unmatched entry using that entry's step-1 `Key` (the registry GUID, never the sidecar `key`). Run `uip solution resources remove <ResourceKey> --solution-folder <SolutionDir> --output json`. This is offline, requires no auth, and does not modify `bindings_v2.json`.
4. Re-run `resources refresh`, then re-publish via Phase 5 (`uip solution upload` — [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish)) so Studio Web drops its copy. Local removal alone does not clear an uploaded orphan. Re-upload overwrites the Studio Web solution in place and discards edits since the last upload; the replaced contents are recorded as a restorable version. Keep it behind the Phase 5 consent gate.

<!-- END: bindings-v2-sync.md -->