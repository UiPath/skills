# Context Capability

Contexts feed retrievable information into an agent at runtime. Three variants exist, discriminated by `contextType`. All use `$resourceType: "context"`.

## When to Use

- Agent needs to retrieve from a knowledge base (RAG / Context Grounding)
- Agent needs runtime file attachments (uploaded by the caller)
- Agent needs to query DataFabric entity sets

## Variants

| `contextType` | Backing | Solution-level auto-gen by `uip solution resource refresh`? | Walkthrough |
|---|---|---|---|
| `"index"` | ECS Context Grounding index (StorageBucket-backed) | Yes — auto-writes `index/<Name>.json` + `bucket/orchestratorBucket/<Bucket>.json` + 2 debug entries | [index.md](index.md) |
| `"attachments"` | Runtime files passed to the agent | No (no solution resource needed) | [attachments.md](attachments.md) |
| `"datafabricentityset"` | DataFabric entity sets | No (not yet auto-generated; hand-author solution files) | [datafabric.md](datafabric.md) |

## Decision

- **RAG / semantic search across documents indexed in Context Grounding** → `index` ([index.md](index.md))
- **Files attached at runtime by the caller (uploaded with each request)** → `attachments` ([attachments.md](attachments.md))
- **Queries against DataFabric entity sets** → `datafabricentityset` ([datafabric.md](datafabric.md))

## Casing Rule

`contextType` and `retrievalMode` values are lowercase. See [../../critical-rules.md](../../critical-rules.md) § What NOT to Do — Anti-pattern 12.

## Sibling Files

- [index.md](index.md) — Context Grounding RAG index walkthrough (most common variant)
- [attachments.md](attachments.md) — Runtime file attachments
- [datafabric.md](datafabric.md) — DataFabric entity-set context

## References

- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
