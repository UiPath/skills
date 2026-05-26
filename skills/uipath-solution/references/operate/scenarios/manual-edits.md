# Manual edits when the CLI doesn't cover the case

The CLI now covers atomic **create** ([Step 9: `solution resource add`](../develop-solution.md#step-9-add-a-resource-atomically)) and **delete** ([Step 10: `solution resource remove`](../develop-solution.md#step-10-remove-a-resource)). What's still missing is `solution resource update` for field-level edits on resources already in the solution. `solution resource refresh` is import-only (it reconciles binding additions, not field edits on existing entries).

For an in-place field edit, you have three options ordered by preference:

1. **Edit in Studio Web** — `solution upload`, edit in the SW UI, re-export. The proper way; SDK does all the validation and back-references.
2. **`solution deploy config set` / `link` / `unlink`** — for changes that only need to apply at deploy time (per-environment values, link state). Touches only the deploy config file, not the solution-level resources.
3. **Hand-edit the JSON directly** — the escape hatch when neither of the above fits and you don't want a full SW round-trip. Works, but **not ideal** — there's no validation, the SDK can silently undo your change on the next refresh if your edit conflicts with what bindings would re-derive, and structural mistakes corrupt the solution. Use only when you understand which fields the SDK leaves alone.

This page covers (3) — what's safe to hand-edit and what's not. For creating or deleting a whole resource (not editing fields on an existing one), prefer `solution resource add` / `remove`.

## What the SDK actually compares

`addOrUpdateResourceToSolutionAsync` calls `compareResourceSpecs` to decide if a resource is `Unchanged` / `Updated`. That comparison **looks at `resource.spec` only** (with reference and secret properties excluded). Top-level fields on `resource` (`name`, `key`, `kind`, `description`, `folders`, etc.) are not part of the spec compare — but most of them carry identity or relationship semantics that other parts of the system rely on.

## Solution-level resource files (`resources/solution_folder/<kind>/<name>.json`)

Open the file. The shape is roughly:

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "key": "11de87d3-...",                // identity — never edit
    "name": "MyResource",                 // identity — never edit
    "kind": "asset",                      // identity — never edit
    "type": "stringAsset",                // identity — never edit
    "apiVersion": "orchestrator.uipath.com/v1",  // managed — never edit
    "description": "...",                 // free text — safe to edit
    "isOverridable": true,                // SW link UI toggle — safe but stays `true` in practice
    "dependencies": [...],                // SDK-managed cross-refs — never edit
    "runtimeDependencies": [...],         // computed at pack — never edit
    "files": [...],                       // SDK-managed — never edit
    "folders": [{ "fullyQualifiedName": "solution_folder" }],  // edit moves the resource — risky (see below)
    "spec": {
      "name": "MyResource",               // duplicate of top-level — must stay in sync if you ever edit name
      "type": "Text",                     // identity — never edit
      "value": "",                        // safe to edit (asset value, queue config, bucket retention, etc.)
      "scope": "global",                  // safe but rarely needs editing
      ...                                 // see kind-specific guidance below
    },
    "locks": []                           // SDK-managed — never edit
  }
}
```

| Editable | Why | Caveats |
|---|---|---|
| `resource.description` | Free-text, not referenced by anything | None |
| `resource.spec.<runtime-config>` | The reason most edits exist (asset `value`, queue retry/auto-retry, bucket `tags`/`retentionPeriod`/`retentionAction`, process `tags`/`retentionPeriod`/`hiddenForAttendedUser`/`alwaysRunning`/`autoStartProcess`) | These DO trigger `Updated` on next refresh. That's fine — the next refresh just re-saves with your edited spec. Don't edit reference fields (anything ending in `Reference`, `Ref`, `Key`) by hand. |
| `resource.spec.tags` | List of strings, no relationships | None |
| `resource.isOverridable` | Toggle for whether SW lets bindings link this | Setting to `false` blocks SW link UI — usually leave `true` |

| **Don't edit** | Why |
|---|---|
| `resource.key` | Cross-references everywhere; rename breaks bindings and dependent resources |
| `resource.name` | Bindings find resources by name; rename without updating bindings → bindings unresolved at deploy. SW or `solution upload` round-trip is the only safe way to rename |
| `resource.kind` / `resource.type` / `apiVersion` | Identity — switching kind is "delete + create new", do that explicitly |
| `resource.spec.name` / `resource.spec.type` | Must match top-level; SDK's `compareResourceSpecs` flags any drift |
| `resource.dependencies` | SDK rebuilds these at refresh from `bindings_v2.json`; manual edits get overwritten |
| `resource.runtimeDependencies` | Recomputed at every pack — manual edits lost on next pack |
| `resource.files`, `resource.locks` | Managed; never appear in user-edit scenarios |
| `resource.folders` | Moves the resource. For a *cloud-imported* resource the folder is `solution_folder` (placeholder) — editing it doesn't change cloud location, only confuses sync. For a *virtual* resource that you authored at a non-`solution_folder` folder, edit at the binding (`bindings_v2.json`) and let refresh re-create — don't edit the resource file directly |
| `resource.spec.<reference-fields>` | E.g. `storageBucketReference`, `retentionBucketRef`. The SDK rewrites these when the target's link state changes; hand-edits get clobbered. (Also see [SOL-7051](https://uipath.atlassian.net/browse/SOL-7051) — the rewrite isn't always applied automatically; that's a known bug, not a license to hand-edit dependents arbitrarily) |

### Examples — safe edits

```jsonc
// asset/stringAsset/MyAsset.json — set a default value
"spec": { "name": "MyAsset", "type": "Text", "scope": "global",
          "value": "https://api.production.example.com" }   // ← edit this

// queue/Queue/OrdersQueue.json — change retry count
"spec": { ..., "maxNumberOfRetries": 5, ... }                // ← edit this

// process/api/MyApi.json — change retention
"spec": { ..., "retentionPeriod": 14, ... }                  // ← edit this

// bucket/Bucket/Storage.json — adjust tags
"spec": { ..., "tags": [{ "name": "Env", "value": "prod" }], ... }
```

After any solution-level edit, run a sanity check:

```bash
uip solution resource list --kind <kind> --solution-folder . --source local --output json
```

The list should show your resource with the new spec. If `resource refresh` reverts the change on the next run, you edited a field the bindings re-derive — back out and use the deploy-config path or SW UI instead.

## Deploy config files (`deploy-config.json`)

Same principle, looser rules. The deploy config is **per-deployment**, not per-solution — editing it doesn't mutate the solution itself, only what `solution deploy run` provisions. Three editing paths:

1. **`uip solution deploy config set <file> <resource> <prop> <value>`** — preferred. Validated, scoped, idempotent.
2. **`uip solution deploy config link/unlink <file> <resource> ...`** — for binding to existing cloud resources or removing the binding.
3. **Manual JSON edits** — fall back to this when the CLI doesn't cover what you need (e.g. nested cross-reference fields like `configuration.storageBucketReference.key`, or adding a fresh `linkToResource` block from scratch). Same shape as the SDK writes:

```jsonc
{
  "resources": [
    {
      "kind": "asset",
      "name": "MyAsset",
      "resourceKey": "11de87d3-...",
      "folderPaths": ["solution_folder"],
      "configuration": {
        "value": "manually-edited-value",   // ← safe to edit by hand
        "description": "...",                // ← safe
        "tags": [...]                        // ← safe
      },
      "linkToResource": {                    // ← safe to add/remove/edit by hand
        "name": "ProductionAsset",
        "folderPath": "Shared/Production"
      }
    }
  ]
}
```

**Manual editing of the deploy config is not ideal** — there's no schema validation in the CLI, and a bad edit fails server-side at `deploy run` (often with a generic `ValidationFailed`). But it's the pragmatic escape hatch when:

- You need to set a nested property `config set` doesn't expose (e.g. `configuration.storageBucketReference.key` to work around [SOL-7051](https://uipath.atlassian.net/browse/SOL-7051)).
- You're scripting a config transform (CI step injecting per-environment secrets, etc.) and want a single JSON-patch step instead of N CLI calls.
- The CLI surface is missing a flag for the field you need.

In those cases: edit the file, run `uip solution deploy run --config-file <path>`, and let the deploy validation catch any structural mistakes. Deploy errors come back fast and verbose enough to localize the bad field.

> See: [pack-and-deploy.md — Configuration Workflow](../pack-and-deploy.md#configuration-workflow) for the standard `set`/`link`/`unlink` flow.
