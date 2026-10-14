# Shared cloud resource across projects

Two (or more) projects in the solution declare a binding to the **same cloud resource** — typically a shared queue, asset, or storage bucket that multiple agents/processes read from.

## Setup

`ProjectA/bindings_v2.json` and `ProjectB/bindings_v2.json` both contain:

```json
{ "resource": "queue", "key": "OrdersQueue",
  "value": { "name": { "defaultValue": "OrdersQueue" },
             "folderPath": { "defaultValue": "Shared/Production" } },
  "metadata": { "subType": "queue", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
```

Same name, same folder, same cloud GUID.

## What happens at refresh

```
Synced 1 resources (0 already in solution)
```

(Or `Imported: 1, Skipped: 1` depending on iteration order.) The first project's binding triggers `addOrUpdateResourceToSolutionAsync`, which imports `OrdersQueue` into the solution with its cloud GUID as the solution-resource key. The second project's binding hits the same cloud GUID — already in `knownResourceKeys` from the first import — and **skips silently**. No suffix, no duplicate, no error.

## Gotchas

- **The skip is idempotent across refreshes** for cloud-imported resources. If you ever see two `OrdersQueue.json` entries (without distinct cloud keys), something else is wrong — most likely a binding's `folderPath` placeholder differs (`solution_folder` vs `Shared/Production`) and the second binding falls through the [virtual-creation path](virtual-resource.md) instead of the import path.
- **Refresh does NOT update the resource's local config** if the cloud-side definition changed (e.g. queue retry count edited in OR after import, or a field added to an entity in Data Fabric). Refresh is import-only by design — that is what keeps your local edits from being wiped on every re-scan — and it reports the resource under `Skipped`. To pull the new cloud definition, run `uip solution resources edit <resource-key> --source remote --force`; without `--force` it lists what would change and writes nothing. See [develop-solution.md Step 11a](../develop-solution.md#step-11a-pull-a-changed-cloud-definition-source-remote).
- **At deploy, both projects' runtime dependencies point at the same `resourceKey`.** This is correct — they share the cloud resource. The deploy folder gets one queue (or one link to an existing one if you've used `deploy config link`).
- **At publish/upload time you cannot have two solution-level entries with the same cloud key.** If you accidentally produce that state by hand-editing files, `pack` rejects with a duplicate-key error.

## Verify

```bash
uip solution resources list --source local --kind Queue --output json | jq '.Data[] | select(.Name == "OrdersQueue")'
```

Exactly one entry, with a key that matches the cloud GUID (the `Key` field) returned by `uip or queues list --folder-path "Shared/Production" --name OrdersQueue`.

> See: [develop-solution.md — Step 7: Refresh Resources](../develop-solution.md#step-7-refresh-resources).
