# Local virtual asset / queue without cloud counterpart

You're shipping a **brand-new** asset (or queue, or bucket) as part of the solution — it doesn't exist in the target tenant yet. You want it provisioned at deploy time, with a value you'll set per environment.

There are two paths to create a virtual resource:

- **From a binding** — write the resource into `bindings_v2.json` (typically via the owning product: Maestro Flow / Case, Studio Web, agent scaffold), then `solution resource refresh` reconciles it into a virtual stub. The flow this page covers.
- **Atomically, no binding** — `uip solution resource add --source local --kind <kind> --name <name>` (see [develop-solution.md Step 9](../develop-solution.md#step-9-add-a-resource-atomically)). Useful when no project consumes the resource yet (CI provisioning ahead of code), or when an agent is mutating one resource at a time and doesn't want to touch any binding file. Same end state on disk; same deploy behavior. Offline-friendly (no auth round-trip).

## Setup

A binding to a resource that **isn't** in cloud:

```json
{ "resource": "asset", "key": "ApiBaseUrl",
  "value": { "name": { "defaultValue": "ApiBaseUrl" },
             "folderPath": { "defaultValue": "solution_folder" } },
  "metadata": { "subType": "StringAsset", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
```

The `folderPath: "solution_folder"` placeholder signals "this resource lives inside the solution, not in a specific cloud folder." Use a real cloud FQN (`"Shared/Production"`) only if you want the asset deployed to that exact folder during `deploy run`.

## What happens at refresh

```
Synced 1 resources (0 already in solution)
```

RCS lookup fails (resource doesn't exist), the sync falls through to `createVirtualResourceAsync`, and the asset is created **as a virtual stub** with a local UUID:

```
resources/solution_folder/asset/stringAsset/ApiBaseUrl.json
```

The stub has `value: ""` (or the type's placeholder default — `false` for boolean, `0` for number).

## Idempotency on re-refresh

Re-running `solution resource refresh` is a no-op for virtuals at the same `(kind, folder, name)` — the second pass detects the existing stub and skips:

```
Synced 0 resources (1 already in solution)
```

If two bindings point at the same name in **different non-`solution_folder` cloud folders**, both create stubs and the second is suffixed `_1` (same SDK uniqueness algorithm as [same-name-across-folders](same-name-across-folders.md)).

## What happens at deploy

`solution deploy run --config-file <path>` validates the deployment config server-side. A virtual asset with no value fails fast:

```
[1009] asset ApiBaseUrl: Invalid argument 'Value'
```

This is **expected** — you must either set a value or link the asset to an existing cloud one before deploy. Two options:

```bash
# Option A: set a value (e.g. environment-specific)
uip solution deploy config set deploy-config.json ApiBaseUrl value "https://api.production.example.com"

# Option B: link to an existing cloud asset
uip solution deploy config link deploy-config.json ApiBaseUrl \
  --name ProductionApiUrl --folder-path "Shared/Production"

# Then deploy
uip solution deploy run -n MyDeployment --package-name MySolution --package-version 1.0.0 \
  --folder-name MySolution --parent-folder-path Shared --config-file deploy-config.json
```

## Gotchas

- **`folderPath: "solution_folder"` vs `"."` vs a real cloud FQN** — all three normalize to "no specific cloud folder" *for the binding*, but the resulting virtual has different `folders[0].fullyQualifiedName` on disk. Stick with `"solution_folder"` (Studio Web's convention) unless you have a reason.
- **Don't set the asset value in `bindings_v2.json` thinking it'll flow through.** Bindings carry name + folder. The value lives in the deploy config (per-environment) or, for virtuals, comes from `deploy config set`.
- **Type-specific required fields** beyond `value`: bucket needs `storageContainer`, others have their own. Refresh fills these with type-appropriate placeholders (empty string / 0 / false). Same `[1009] Invalid argument` deploy error if left at placeholder.
- **A virtual asset has no `referenceKey` in any tool resource file** — bindings reference virtuals by name + folder, not by key. Don't try to copy a stub's UUID into a tool's `referenceKey`.
- **Virtuals are not pushed to RCS by `solution upload`.** Upload writes the solution to Studio Web; the virtual remains local until deploy turns it into a real cloud resource (or you link it to an existing one).

## Verify

```bash
# Virtual exists locally
uip solution resource list --source local --kind Asset --output json

# Deploy config has the resource and its `configuration.value`
uip solution deploy config get MySolution -d deploy-config.json --output json
jq '.resources[] | select(.name == "ApiBaseUrl")' deploy-config.json
```

> See: [pack-and-deploy.md — Configuration Workflow](../pack-and-deploy.md#configuration-workflow).
