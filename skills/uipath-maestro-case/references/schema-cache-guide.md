# Run-Scoped Schema Cache Guide

Build each distinct task or connector contract once, persist the complete CLI response, and reuse it for every consumer in the same greenfield run. The cache is a run artifact, not a cross-run cache: create it after the mandatory registry pull and replace it when planning regenerates from scratch.

Path: `tasks/schema-cache.json`, adjacent to `tasks.md`.

## Invariants

1. **One fetch per exact request.** Before any `tasks describe`, `case spec`, or `get-connection` call, compare the proposed request with the cache. An exact hit is a Read, never another CLI call.
2. **Share schemas, not generated IDs.** Two task declarations that point to the same action app or process share one schema response, but each task still mints its own task, input, output, and binding IDs.
3. **Persist the complete `Data` payload.** Do not summarize inputs/outputs or copy selected fields into reasoning. The plugin recipe reads the cached response and consumes the same paths it would consume from live CLI output.
4. **Request identity includes every shape-affecting argument.** Never reuse a connector response merely because its connection is the same. Activity/trigger type, activity type ID, object name, connection ID, and configured input details must match.
5. **No ad-hoc implementation fetch.** Phase 2 and Phase 3 consume a named cache entry. A missing or mismatched entry returns to the gather pass, performs one fetch, persists it, then resumes.
6. **No stale cross-run reuse.** Regenerate-from-scratch replaces this file. Continue-without-regenerate may reuse it only when the current `tasks.md` entry carries the same key and the stored request still exactly matches.
7. **Artifact I/O follows Rule 13.** Create and update the cache via Read + Write/Edit only. Do not use redirection, `jq`, Python, Node, or a helper script.

## Artifact Shape

Use short stable keys (`N01`, `D01`, `C01`, `K01`) so `tasks.md` can reference entries without copying request bodies.

```jsonc
{
  "version": 1,
  "nonConnector": {
    "N01": {
      "request": {
        "type": "action",
        "id": "<action-app-id>",
        "elementId": null
      },
      "consumers": ["T14", "T27"],
      "response": { "Data": "<complete tasks describe Data payload>" }
    }
  },
  "connectorDiscovery": {
    "D01": {
      "request": {
        "type": "activity",
        "activityTypeId": "<type-id>",
        "connectionId": "<connection-id>",
        "objectName": null,
        "skipCaseShape": true
      },
      "consumers": ["T19"],
      "response": { "Data": "<complete lean case spec Data payload>" }
    }
  },
  "connectorShapes": {
    "C01": {
      "request": {
        "type": "activity",
        "activityTypeId": "<type-id>",
        "connectionId": "<connection-id>",
        "objectName": null,
        "inputDetails": { "bodyParameters": {}, "queryParameters": {} }
      },
      "consumers": ["T19"],
      "response": { "Data": "<complete populated case spec Data payload>" }
    }
  },
  "connections": {
    "K01": {
      "request": {
        "cacheType": "typecache-activities",
        "activityTypeId": "<type-id>"
      },
      "selections": { "T19": "<connection-id>" },
      "response": { "Data": "<complete get-connection Data payload>" }
    }
  }
}
```

`response` may contain the command envelope in addition to `Data`; the complete `Data` payload is mandatory. Preserve the live PascalCase keys. Connector plugin normalization to camelCase happens only when the cached subtree is spliced into `caseplan.json`.

## Request Equality

### Non-connector task schema

The equality tuple is:

```text
(type, entityKey, elementId-or-null)
```

One `uip maestro case tasks describe` call serves every task with the same tuple. Multi-element agents differ by `elementId` and therefore use different entries. Inline-built agents and API workflows use the sibling `entry-points.json` schema under the same cache contract; record `source: "entry-points"` in the request instead of calling the tenant CLI.

### Connection resolution

The equality tuple is:

```text
(cacheType, activityTypeId)
```

Run `get-connection` once for that tuple and reuse its full connection list. Selection remains per consumer: record `selections[T-number]`, because two tasks may intentionally choose different connections from the same response. Consumers with the same selected ID can share downstream connector requests when their other request fields also match. A different activity type gets a separate lookup even if it belongs to the same connector.

### Connector discovery

The equality tuple is:

```text
(type, activityTypeId, connectionId, objectName-or-null, skipCaseShape=true)
```

This lean request discovers required fields, references, outputs, filters, and operation metadata. Reuse it during planning for every exact-match consumer.

### Populated connector shape

The equality tuple is:

```text
(type, activityTypeId, connectionId, objectName-or-null, exact inputDetails object)
```

Object-key order is irrelevant; key names, array order, scalar values, expressions, and filter trees must match. Two consumers with different literals or filters need separate entries even if the operation and connection are identical.

The lean discovery and populated shape are different exact requests. Normally each is fetched at most once. When planning already has unambiguous exact field keys and complete input details, it may issue the populated request immediately, use that one response for discovery and implementation, and omit the separate lean entry. Do not attempt this optimization when SDD names must be mapped against live fields, reference choices must be discovered, required fields are unknown, or filter support is unknown.

## Gather Pass — Phase 1

After registry resolution and before emitting the affected `tasks.md` entries:

1. Inventory all schema consumers by T-number.
2. Group non-connector consumers by the non-connector equality tuple.
3. Group connection lookups and connector discovery requests by their equality tuples.
4. Execute each cache miss exactly once with `--output json`.
5. Persist each complete response immediately, then add every consumer T-number to its entry.
6. Record the relevant key on each `tasks.md` entry:
   - `schema-cache-key: N01` for non-connector tasks.
   - `connection-cache-key: K01` for connector targets.
   - `connector-discovery-key: D01` when a separate lean request was needed.
   - `connector-shape-key: C01` when the populated response is already available.
7. When connector input details become complete only after discovery/reference resolution, run the populated request once at the end of Phase 1 and persist `Cxx` before the planning approval hard stop.

If a connector task/rule needs a generated Phase 2 ID, gather its missing populated request once at Phase 3 re-entry, persist it, and then start stage mutations. A resolved **case-level event trigger must already have `Cxx` before Phase 2**, because its configured trigger node participates in the Phase 2 publish-for-review artifact. Do not interleave schema CLI calls with stage Edits.

## Consumption

- Phase 2 task-shape construction reads `Nxx.response.Data` for non-connector inputs and outputs.
- Phase 3 connector construction reads `Cxx.response.Data.CaseShape` and `Connection`.
- Connector plugins still perform placeholder substitution, ID minting, output-name deduplication, and PascalCase-to-camelCase key normalization per their recipes. These operations are consumer-specific and do not mutate the shared cache entry.
- A connector-bound condition rule, connector task, and event trigger may share a `Cxx` only when their exact populated request matches. Their target envelopes and generated IDs remain separate.

## Recovery and Verification

On compaction or interruption, Read `tasks.md` and `schema-cache.json`, then resume from the first T-entry whose referenced cache key is absent or whose stored request does not match. Never repeat a successful cached request merely because reasoning context was compacted.

Before Phase 2, verify:

- every resolved non-connector task has a valid `Nxx` key;
- every resolved event trigger has `Kxx` + ready `Cxx`; every resolved connector task/rule has `Kxx` plus either ready `Cxx` or the information needed to gather it once at Phase 3 re-entry;
- identical non-connector tuples point to the same key;
- different connector input details do not point to the same `Cxx`;
- no cache entry contains generated task/input/output/binding IDs.
