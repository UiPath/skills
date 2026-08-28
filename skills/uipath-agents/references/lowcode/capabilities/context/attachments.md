# Attachments Context

Use a context resource with `$resourceType: "context"` and `contextType: "attachments"` to process files supplied at runtime. No backing index or solution-level resource binding is used; files are uploaded for each invocation. For other context variants, see [context.md](context.md).

> **Not what you want?** To accept a file as a plain agent input field and read its contents via a built-in tool, see [../built-in-tools/built-in-tools.md](../built-in-tools/built-in-tools.md) and [../../agent-definition.md](../../agent-definition.md) § File Attachments. That pattern uses `$resourceType: "tool"` (not context) and pairs a `job-attachment` input with `analyze-attachments`.

## When to Use

Use attachments when callers upload PDFs, images, or documents at runtime and files should be processed per invocation without a persistent index or solution-level files.

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
  "folderPath": "solution_folder",
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

None. Attachments are runtime-only.

## Gotchas

`contextType` MUST be `"attachments"` (all lowercase). See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.

## References

- [context.md](context.md) — capability overview
- [index.md](index.md) — Context Grounding RAG
- [datafabric.md](datafabric.md) — DataFabric entity-set context