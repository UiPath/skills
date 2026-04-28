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

**Not auto-generated.** Solution-level resource generation for DataFabric contexts is not yet supported by `uip solution resource refresh` — the agent-level `resource.json` is written, but you must hand-author any solution manifests needed.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Anti-pattern 12 — `contextType` value MUST be `"datafabricentityset"` (all lowercase). camelCase like `"dataFabricEntitySet"` passes `uip agent validate` but Studio Web silently drops the resource.

## References

- [context.md](context.md) — capability overview
- [index.md](index.md) — Context Grounding RAG
- [attachments.md](attachments.md) — runtime file attachments
