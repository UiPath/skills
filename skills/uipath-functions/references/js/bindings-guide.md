# Bindings and Generated Descriptors

How `uip function pack`/`push` generate `entry-points.json` and `bindings_v2.json`, how hand-added resource bindings survive regeneration, and how bound resources reach the SDK at runtime via resource overwrites.

## Generated files

`uip function pack` and `uip function push` (and `uip solution pack`, which packs in-process) regenerate two descriptors at the project root; pack then copies them into `content/` inside the `.nupkg`:

| File | Contents |
|---|---|
| `entry-points.json` | One entry per function (the job surface) |
| `bindings_v2.json` | One `HttpTrigger` resource per HTTP-exposed function + any hand-added resource bindings |
| `package-descriptor.json` | Pack-time only; maps logical names to package paths — notably `"bindings.json"` → `"content/bindings_v2.json"` |

Regeneration reconciles against the existing files instead of rewriting them. Do not delete `entry-points.json` or `bindings_v2.json` between packs: they are the baseline that keeps IDs stable and preserves hand-added resources.

## entry-points.json

One entry per `defineFunction`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "content/functions/hello.ts",
      "uniqueId": "<STABLE_UUID>",
      "type": "function",
      "input":  { "type": "object", "properties": { "name": { "type": "string" } } },
      "output": { "type": "object", "properties": { "message": { "type": "string" } } }
    }
  ]
}
```

Reconciliation rules on regeneration:

- Function entries are matched by `filePath`: a match keeps its `uniqueId` (stable across re-packs, so Orchestrator updates triggers in place instead of duplicating) and keeps a manually-set `"isTransactionRoot": true`.
- `input`/`output` are always re-derived from the function's declared schemas.
- Entries whose function no longer exists are dropped.
- Entries with `type` other than `"function"` are preserved verbatim (Studio Web or other tooling may write these).

## bindings_v2.json — HttpTrigger resources

Each function that declares `method` + `path` gets one `HttpTrigger` resource; job-only functions get none.

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/bindings",
  "version": "2.0",
  "resources": [
    {
      "resource": "HttpTrigger",
      "key": "<STABLE_UUID>",
      "id": "<STABLE_UUID>",
      "value": {
        "EntryPointUniqueId": { "DefaultValue": "<ENTRY_POINT_UNIQUE_ID>", "IsExpression": false }
      },
      "metadata": {
        "BindingsVersion": "2.1",
        "Name": "hello",
        "Method": "POST",
        "Slug": "/hello",
        "CallingMode": "LongPolling",
        "Description": "Returns a greeting."
      }
    }
  ]
}
```

- Trigger identity is `Method` + `Slug`: an existing trigger matching both keeps its `key`/`id` across re-packs. The metadata `Slug` stores the `defineFunction` `path` verbatim — leading `/` included — unlike the invoke-URL segment, which drops it ([http-semantics-guide.md](http-semantics-guide.md)).
- `CallingMode` is always `LongPolling` — synchronous long-polling; there is no async/fire-and-forget mode. The trigger account is always "Run as HTTP Caller": the request runs with the caller's identity as `ctx.user` (the robot identity is separate — see [calling-uipath-apis-guide.md](calling-uipath-apis-guide.md)).
- `value.EntryPointUniqueId.DefaultValue` cross-references the function's `entry-points.json` `uniqueId`.

### Lifecycle on re-pack + publish

Orchestrator syncs triggers from these files after the Function Release is updated (manual step — see [deployment-guide.md](deployment-guide.md)):

| Change in code | Effect after release update |
|---|---|
| New `defineFunction` | New entry point + binding → new HTTP trigger |
| Renamed `name` or `path` | Old trigger deleted, new one created — **existing callers' URLs break** |
| Removed function | Trigger deleted |
| Changed `input`/`output` schema | Trigger schemas updated in place |

Sharp edge: a rename is a delete+create, never an update. Treat `method` + `path` as a published contract.

## Declaring resource bindings by hand

Any resource whose `resource` field is not `"HttpTrigger"` is preserved **verbatim** across every regeneration — the generator never reads, validates, or rewrites it. That is the mechanism for binding platform resources (storage buckets, queues, assets, processes) to the package: add the entry to `resources[]` in `bindings_v2.json` by hand and it survives all future packs.

Entry shape (`value` and `metadata` optional, passed through untouched):

```json
{
  "resource": "Storage",
  "key": "<UUID_YOU_MINT_ONCE>",
  "id": "<UUID_YOU_MINT_ONCE>",
  "metadata": { "Name": "blobs" }
}
```

The per-resource-type `value`/`metadata` schemas are defined by the platform's binding surface (solution/Orchestrator side), not by this project's tooling — mirror an entry created by the platform for the target resource type rather than inventing fields.

## Resource overwrites at runtime

Resource bindings pay off at runtime as **resource overwrites**: Orchestrator resolves the bindings for the release and the robot's user into a table `{"<RESOURCE_TYPE>.<RESOURCE_KEY>": { <PROPERTY>: <VALUE> }}` (keys case-sensitive, passed through verbatim — placeholder casing is illustrative) and delivers it per invocation:

- **HTTP mode**: request header `X-UiPath-ResourceOverwrites` (base64-encoded UTF-8 JSON), scoped to that one request. Never cached across requests — concurrent requests in one pooled process can belong to different releases/robot users.
- **Job mode**: the `resourceOverwrites` field of `runtime-context.json` (see [job-mode-guide.md](job-mode-guide.md)).

The runtime publishes an accessor at `globalThis[Symbol.for("uipath.resourceOverwrites.v1")]`; `@uipath/uipath-typescript` probes that slot and redirects its resource lookups (asset/queue/bucket/process names) to the bound targets. Nothing is surfaced on `ctx`, and function code needs no change.

Behavior to rely on:

- **Degrades, never fails**: an absent or corrupt header/table means SDK lookups fall back to the literal names written in code — a bindings problem never faults the invocation. The flip side: a broken binding manifests as "reads the wrong/original resource", not as an error.
- **Local serve has no overwrites** unless the caller sets the header itself; lookups use literal names.
- **When to care**: only when a function reads Assets/Buckets/Queues/Processes through `@uipath/uipath-typescript` and the deployment remaps them per environment or folder. Folder-correct redirection requires the whole chain: a hand-added resource entry in `bindings_v2.json` + the platform resolving it into the overwrite table for that release.
