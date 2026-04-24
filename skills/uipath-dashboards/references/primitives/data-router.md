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
2. **Reason before you lookup.** The agent is a **dashboard expert**, not a phrase-book. For every metric the user asks about, classify it on the four axes in [../sdk/metric-derivation.md](../sdk/metric-derivation.md) — **shape, time framing, aggregation, service** — and derive the SDK call from first principles. Only then consult `intent-map.md` for an illustrative example that might match.
3. **v1: always route to SDK (`source: 'sdk'`).** Insights / AOPS branches are reserved in the type but never returned in v1.
4. **[../sdk/intent-map.md](../sdk/intent-map.md) is illustrative, not exhaustive.** If the requested metric isn't in the catalog, derive it per `metric-derivation.md`'s framework. Novel metrics are the default case, not the edge case.
5. **[../sdk/service-semantics.md](../sdk/service-semantics.md)** is the SDK's mental model — what each service's canonical row is, its filterable dimensions, its time axis, its idiomatic column set for detail views. Read this when deriving any metric, especially for choosing which service owns the data.
6. **Consult `sdk/invariants.md`** BEFORE writing any filter — server-side field names, pagination rule, zero-fill rule. Mixing client/server names yields silent no-ops.
7. **Stamp scopes from `sdk/scope-map.md`** — the router output's `scope` array merges into `state.json.scopes` (informational in secret-mode).
8. **Folder-scoped by default.** Include `state.json.folderKey` unless the intent is explicitly cross-folder (user phrase contains "across all folders" / "tenant-wide").
9. **Compose from primitives, don't reinvent.** `fetchAllWithFilter`, `zeroFill`, `isoDaysAgo`, `hourBucket`, `groupBy`, `dedupById`, `percentile`, `delta` are all in `src/lib/queries/_shared.ts` and `src/lib/utils.ts`. The generator uses them; it does NOT write a new `.reduce()` for every metric.

## Details

The resolution procedure for ANY metric:

1. **Classify on the four axes** ([metric-derivation.md](../sdk/metric-derivation.md) § "The four-axis decomposition"):
   - Shape: scalar | scalar-with-delta | time-series | categorical | ranked | parts-of-whole | distribution | flow
   - Time framing: snapshot | point-in-time count | bucketed series | trend vs prior period | rolling window
   - Aggregation: count | distinct | sum | mean | percentile | ratio | rate-of-change | top-N | group-by
   - Service: which SDK class owns the canonical row (per [service-semantics.md](../sdk/service-semantics.md))
2. **Synthesize the SDK call** from the axes. Pagination, filters, field names come from the service's semantics. Aggregation is composed from primitives.
3. **Validate against invariants** — server-side OData names (not client-side renames), cursor-object pagination, dedup-by-id, zero-fill time buckets, drop-epoch-fallbacks.
4. **Check [intent-map.md](../sdk/intent-map.md)** as a sanity check — if there's a worked example for this or a similar metric, does your derivation match? If not, step back and verify your axes.
5. **If the metric can't be derived** (service not in SDK, data genuinely unavailable), halt and tell the user what you CAN query that's adjacent — never fabricate.

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
