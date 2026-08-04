# DataFabric Entity Set Context

Walkthrough for adding a context resource backed by one or more DataFabric entity sets.

For other context variants, see [context.md](context.md).

## When to Use

- Agent needs to query against UiPath DataFabric entity sets
- The entity sets already exist in DataFabric

## Agent-Level Resource Shape

**Path:** `<AgentName>/resources/<ContextName>/resource.json`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "datafabricentityset",
  "entitySet": [
    {
      "id": "<uuid>",
      "referenceKey": "<entity-key>",
      "name": "<EntityName>",
      "folderId": "<folder-uuid>",
      "folderDisplayName": "Shared",
      "description": null
    }
    // ...more entities
  ]
}
```

No `indexName` and no `settings` for DataFabric contexts. The shape is entirely different from index/attachments.

## Solution-Level Files

**Not auto-generated.** Solution-level resource generation for DataFabric contexts is not yet supported by `uip solution resources refresh` — the agent-level `resource.json` is written, but you must hand-author any solution manifests needed.

## Gotchas

1. `contextType` value MUST be `"datafabricentityset"` (all lowercase) — see [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.
2. **Every `entitySet` entry requires a non-null `referenceKey` (string) and a UUID-string `folderId`.** Schema validation rejects `null` or missing values for either — `uip agent refresh` / `validate` fails with only `resources/<Name>/resource.json: Invalid input`, no field path. When authoring offline without the live DataFabric folder GUID, use a placeholder UUID for `folderId` and the entity name as `referenceKey` — refresh does not resolve them against the cloud (solution-level generation is unsupported, see above). Do NOT leave `entitySet` empty to silence the error: an empty list passes refresh but the context retrieves nothing.

## References

- [context.md](context.md) — capability overview
- [index.md](index.md) — Context Grounding RAG
- [attachments.md](attachments.md) — runtime file attachments
