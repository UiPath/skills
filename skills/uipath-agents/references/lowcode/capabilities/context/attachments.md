# Attachments Context

Walkthrough for adding a context resource that takes runtime files passed to the agent. No backing index — files are uploaded with each agent invocation.

For other context variants, see [context.md](context.md).

## When to Use

- Caller uploads files (PDFs, images, documents) at runtime
- No persistent index needed — files are processed per-invocation
- No solution-level resource binding (attachments are runtime-only)

## Agent-Level Resource Shape

**Path:** `<AgentName>/resources/<ContextName>/resource.json`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "attachments",
  "indexName": "<ContextName>",          // same as name for attachments
  "attachments": {
    "description": "Array of files, documents, images to process."
  },
  "settings": {
    "retrievalMode": "semantic",
    "query": { "variant": "dynamic" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },
    "threshold": 0,
    "resultCount": 3
  }
}
```

## Solution-Level Files

None. No solution-level file is produced — attachments are runtime-only.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Anti-pattern 12 (lowercase `contextType`).

## References

- [context.md](context.md) — capability overview
- [index.md](index.md) — Context Grounding RAG
- [datafabric.md](datafabric.md) — DataFabric entity-set context
