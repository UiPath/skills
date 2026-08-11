# bindings_v2.json Sync

Shared procedure for keeping `bindings_v2.json` in sync after any plugin writes to the bindings array in `caseplan.json`.

Bindings live at top-level `bindings[]` in `caseplan.json`. Output `bindings_v2.json` shape is independent of the source.

## When to Run

**Sync-as-you-write — one group at a time, never deferred.** Immediately after a plugin writes a binding pair to top-level `bindings[]` in `caseplan.json` (non-connector `name`+`folderPath`, or connector `ConnectionId`+`folderKey`), append that group's ONE converted entry to `bindings_v2.json` per § Append one resource entry (below). The caseplan pair and its sidecar entry are one unit of work; the plugin's Post-Write Verification checks both.

Never defer the append to an end-of-phase batch. The sidecar has no execution-time feedback — `validate` never reads it; only `resources refresh` consumes it, and in eval/CI that often runs harness-side after the agent finishes. A deferred batch is a checkpoint that one-pass agent runs demonstrably skip (observed artifacts: an untouched scaffold `resources: []`, and a partial raw-format copy — both alongside a complete `bindings[]`). A one-group append with the shape in front of you is mechanical; a 16-entry batch recalled later is not.

**Full regeneration (§ Regenerate, below) is the repair path, not the primary path.** Run it only on:

1. **Step 12 Check 7 drift** — parity mismatch at the Phase 3 exit gate ([implementation.md](implementation.md)): regenerate once, re-check, halt if still divergent
2. **Task / rule removal** — [§ Cleanup](#cleanup-on-task-or-rule-removal)
3. **Edit-mode flows** that re-point resource bindings ([case-editing-operations.md](case-editing-operations.md))

---

## § Append one resource entry (primary)

Run immediately after writing a group's binding pair to `caseplan.json`:

1. Take the pair just written — both entries share one `resourceKey`.
2. Convert to ONE entry per the shapes in § Regenerate below (non-connector vs connector; the inline-built-sibling exception applies here too).
3. Edit `bindings_v2.json`: if it is still the empty scaffold (`"resources": []`), replace the empty array with `[ <entry> ]`; otherwise insert the entry before the closing `]` of `resources`. If an entry with the same `key` already exists, update it in place — never duplicate.

Example — the caseplan pair and its ONE sidecar entry:

```jsonc
// caseplan.json bindings[] — two entries, one per property
{ "id": "bRpaName1", "name": "name",       "type": "string", "resource": "process", "resourceKey": "Shared/FinOps.RPA Workflow", "default": "RPA Workflow",  "propertyAttribute": "name" },
{ "id": "bRpaFold1", "name": "folderPath", "type": "string", "resource": "process", "resourceKey": "Shared/FinOps.RPA Workflow", "default": "Shared/FinOps", "propertyAttribute": "folderPath" }
```

```jsonc
// bindings_v2.json resources[] — ONE entry, properties nested under value
{
  "resource": "process",
  "key": "Shared/FinOps.RPA Workflow",
  "value": {
    "name":       { "defaultValue": "RPA Workflow" },
    "folderPath": { "defaultValue": "Shared/FinOps" }
  }
}
```

> **Format sentinel (hard rule).** A `resources[]` entry has exactly `resource` / `key` / `value` (+ `metadata` when applicable). If an entry contains `id`, `propertyAttribute`, or a per-property `default`, caseplan bindings were copied RAW into the sidecar — wrong file format; rebuild that entry via the conversion above. Empty `resources: []` alongside a non-empty `bindings[]` means the sync never ran. Step 12 Check 7 halts on both.

---

## § Regenerate bindings_v2.json

**Repair / edit-mode path** — primary sync is § Append one resource entry (above); run this full pass only per the triggers in § When to Run. The sidecar uses a **different format**: `caseplan.json` stores two entries per resource (one per property), `bindings_v2.json` stores one entry per resource with properties nested under `value`.

### Procedure

1. Read top-level `bindings[]` from `caseplan.json`
2. Group bindings by `resourceKey` — entries sharing the same key belong to one resource
3. For each group, produce one resource entry using the shapes below
4. Write the full file (always overwrite, never append) to `<SolutionDir>/<ProjectName>/bindings_v2.json`

### Non-connector resource entry

```json
{
  "resource": "<resource>",
  "key": "<resourceKey>",
  "value": {
    "name": { "defaultValue": "<name binding default>" },
    "folderPath": { "defaultValue": "<folderPath binding default>" }
  },
  "metadata": { "subType": "<resourceSubType — omit metadata key if none>" }
}
```

> **Inline-built sibling exception (agent / api-workflow) — the one case where the shape's `<folderPath binding default>` placeholder does NOT take the caseplan default.** `value.folderPath.defaultValue` is **`"solution_folder"`** (resource identity), NOT the caseplan `folderPath` binding `default` (which is `""` for an inline sibling). `bindings_v2.json` keeps the `solution_folder` sentinel while the caseplan runtime `folderPath` stays `""` — they are intentionally decoupled. `value.name.defaultValue` and `metadata.subType` (`"Agent"` / `"Api"` per kind) follow the caseplan binding as usual. Full rationale: the inline-built-sibling decoupling blockquote later in this file.

### Connector resource entry

```json
{
  "resource": "Connection",
  "key": "<connectionId>",
  "value": {
    "connectionId": { "defaultValue": "<connectionId>" },
    "folderKey": { "defaultValue": "<folderKey>" }
  },
  "metadata": { "connector": "<connectorKey>" }
}
```

> **Known CLI bug:** `syncConnectionResources` reads `value.connectionId` (lowercase c) but `flow-schema` writes `value.ConnectionId` (uppercase C). Use **lowercase `connectionId`** until fixed.

File envelope: `{ "version": "2.0", "resources": [ /* one entry per resource */ ] }`

---

## § Populate IS connection cache

`uip solution resources refresh` reads a local IS cache that connector plugins must populate after `get-connection`. Applies to all three connector-resolving paths: connector **tasks** (Step 9.7), connector **triggers** (Step 6.1), and connector **condition-rule upgrades** in any of the 4 scopes (Step 10.5).

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

### Field sources

| Field | Source | Plugin step |
|---|---|---|
| `id` | `connection-id` from `tasks.md` | Planning |
| `name` | `.Data.Connections[selected].name` from `get-connection` | Step 1 |
| `connectorKey` | `connector-key` from `tasks.md` | Planning |
| `connectorName` | `.Data.Connections[selected].connector.name` from `get-connection` | Step 1 |
| `folderKey` | `.Data.Connections[selected].folder.key` from `get-connection` | Step 1 |
| `folderName` | `.Data.Connections[selected].folder.name` from `get-connection` | Step 1 |

### Procedure

After `get-connection` succeeds (Step 1), write or merge the cache:

1. Read existing cache at the path above (may not exist — start with `[]`)
2. If an entry with the same `id` already exists, skip
3. Otherwise append the new entry
4. Write the file as a bare JSON array (NOT wrapped in `{ cachedAt, data }`)

```bash
mkdir -p ~/.uipath/cache/integrationservice/<connectorKey>
```

> Workaround for CLI bugs: (1) tenant-ID prefix in cache path, (2) wrapped `{ cachedAt, data }` format. Direct write bypasses both.

---

## What `resource refresh` produces

With `bindings_v2.json` and IS cache in place, `uip solution resources refresh` creates:

| Input | Output | Purpose |
|---|---|---|
| Non-connector bindings in `bindings_v2.json` | `resources/solution_folder/process/` files | Resource declarations imported from Orchestrator |
| Connection binding in `bindings_v2.json` + IS cache | `resources/solution_folder/connection/<connectorKey>/<name>.json` | Connection resource declaration |
| Both | `userProfile/<userId>/debug_overwrites.json` | Maps abstract resources to Orchestrator instances for debug |

All three required for `uip solution upload` and `uip maestro case debug` to work without "Resource is not configured" warnings.

> **Inline-built siblings (agent / api-workflow) — `bindings_v2` identity and the caseplan runtime `folderPath` are DECOUPLED.** This is the one case where `bindings_v2.json` does NOT mirror the caseplan binding's `folderPath`. Keep the **resource identity** at the `solution_folder` sentinel everywhere it belongs — `bindings_v2.json` `key` (`"solution_folder.<name>"`) and `value.folderPath.defaultValue` (`"solution_folder"`), plus the caseplan `resourceKey` and the `resources/solution_folder/…` path. **BUT the caseplan task's `folderPath` binding `default` MUST be `""`** (co-located runtime folder), NOT the sentinel — `"solution_folder"` there fails at invocation with `folder not exist`. Prerequisite for deploy/debug: the sibling registered in the `.uipx`. Full rationale (deploy provisioning, runtime invocation): [create-inline-common.md § Step 3](plugins/tasks/create-inline-common.md#step-3--binding-invariants); per-type debug behavior in each type's § Step 3.

---

## Cleanup on task or rule removal

When any task or connector condition rule is removed and its root bindings are pruned (per [case-editing-operations.md](case-editing-operations.md) § Delete a node / § Delete a condition rule / § Delete a task):

1. After pruning root bindings, regenerate `bindings_v2.json` from the updated array.

<!-- END: bindings-v2-sync.md -->
