# Context Capability

Contexts are runtime-retrievable resources. Each uses `$resourceType: "context"` and one of these lowercase `contextType` values:

| `contextType` | Backing | `uip solution resources refresh` auto-generates solution resources? | Walkthrough |
|---|---|---|---|
| `"index"` | ECS Context Grounding index (StorageBucket-backed) | Yes — writes `index/<Name>.json`, `bucket/orchestratorBucket/<Bucket>.json`, and 2 debug entries | [index.md](index.md) |
| `"attachments"` | Runtime files passed by the caller | No solution resource needed | [attachments.md](attachments.md) |
| `"datafabricentityset"` | DataFabric entity sets | No — hand-author solution files | [datafabric.md](datafabric.md) |

## Decision

- Use `index` for RAG or semantic search across documents indexed in Context Grounding: [index.md](index.md)
- Use `attachments` for files uploaded by the caller at runtime: [attachments.md](attachments.md)
- Use `datafabricentityset` for queries against DataFabric entity sets: [datafabric.md](datafabric.md)

> **File-as-input ≠ attachments context.** For a plain file input read by a built-in tool without semantic retrieval, use `job-attachment` + `analyze-attachments`. See [../built-in-tools/built-in-tools.md](../built-in-tools/built-in-tools.md) and [../../agent-definition.md](../../agent-definition.md) § File Attachments.

## Casing Rule

`contextType` and `retrievalMode` values are lowercase. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § What NOT to Do — Anti-pattern 12.

## Sibling Files

- [index.md](index.md) — Context Grounding RAG index walkthrough
- [attachments.md](attachments.md) — Runtime file attachments
- [datafabric.md](datafabric.md) — DataFabric entity-set context

## References

- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics