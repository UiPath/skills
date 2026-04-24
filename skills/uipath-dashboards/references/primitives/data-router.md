# data-router

## Purpose
Translate a user-intent phrase ("top agents by invocation", "error rate over 7 days") into a concrete SDK call spec that the generator turns into a React query hook.

## Inputs
- User-intent phrase (string).
- Current state.json (for `folderKey` scoping).

## Outputs
```ts
{
  source: 'sdk' | 'insights' | 'aops',  // v1: always 'sdk'
  service: string,                       // e.g., 'Jobs', 'Processes'
  method: string,                        // e.g., 'getAll'
  filter?: string,                       // OData filter (server-side field names!)
  fieldsProjected?: string[],            // client-side field names for display
  scope: string[],                       // e.g., ['OR.Jobs.Read', 'OR.Folders.Read']
  aggregation?: 'count' | 'avg' | 'topN' | 'timeBuckets' | ...
}
```

## Rules
1. **Step 0 — Load SDK context if not already present.** Fetch https://uipath.github.io/uipath-typescript/llms-full-content.txt OR drag `node_modules/@uipath/uipath-typescript/` into context. Don't reinvent method signatures from memory.
2. **v1: always route to SDK (`source: 'sdk'`).** Insights / AOPS branches are reserved in the type but never returned in v1.
3. **Consult `sdk/intent-map.md`** for the user-phrase → SDK call translation — it's the dashboard-specific opinion layer.
4. **Consult `sdk/invariants.md`** BEFORE writing any filter — server-side field names, pagination rule, zero-fill rule. Mixing client/server names yields silent no-ops.
5. **Stamp scopes from `sdk/scope-map.md`** — the router output's `scope` array merges into `state.json.scopes` (informational in secret-mode).
6. **Folder-scoped by default.** Include `state.json.folderKey` unless the intent is explicitly cross-folder (user phrase contains "across all folders" / "tenant-wide").

## Details

See [../sdk/intent-map.md](../sdk/intent-map.md) for the complete user-phrase → SDK call table.

### v2+ reserved branches

```ts
// Not implemented in v1 — documented for forward-compat
type InsightsRoute = { source: 'insights', endpoint: string, query: object, scope: string[] };
type AopsRoute = { source: 'aops', command: string, args: object };
```

The router's return type is the **union** of the three. v1 implementations only ever emit the SDK branch. Adding a new source later is a one-file change.

### Error paths
| Condition | Action |
|---|---|
| No intent-map entry matches the phrase | Surface "I can map X, Y, Z kinds of questions. Rephrase or ask about: …" — don't guess. |
| Phrase implies data not available in SDK | Point at `sdk/intent-map.md` "data not in SDK" section; say what IS available. |
| Phrase requires auth scope the user's token can't grant | Secret-mode: no-op at router (tokens are full-scope); document scope need in generated `SECURITY.md`. |
