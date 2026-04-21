# Deep RAG Pattern Node — Planning

The Deep RAG node runs comprehensive document synthesis over an attached file (PDF, Word, etc.): ingest, retrieve, reason, and return prose — optionally with per-sentence citations back to the source pages. It is one of two nodes in the **Patterns** category (alongside [Batch Transform](../batch-transform/planning.md)).

## Node Type

`uipath.pattern.deep-rag`

Fixed OOTB node type — no registry suffix, one version. It does not appear in `uip flow registry list` unless the tenant has the platform-side `canvas.nodes.patterns` feature flag enabled. The uip CLI unconditionally requests Patterns nodes in its manifest fetch, so they will appear once the server rolls the flag out to your tenant.

## When to Use

Use Deep RAG when the task is **"read this document and produce a thorough answer"** — summarization, Q&A, compliance checks, executive briefs — where depth matters and traceability back to the source is valuable.

### Selection Heuristics

| Situation | Use Deep RAG? |
| --- | --- |
| Summarize a long document (contract, policy, research paper) | Yes |
| Answer a free-form question grounded in one attached document | Yes |
| Produce a report where every claim must cite the source page | Yes — set `returnCitations: true` |
| Short, single-turn Q&A over small text in-memory | No — use [Agent](../agent/planning.md) or [Script](../script/planning.md) |
| Row-by-row enrichment of tabular data | No — use [Batch Transform](../batch-transform/planning.md) |
| Multi-document retrieval across a corpus | No — Deep RAG is scoped to one attachment per call. Chain multiple Deep RAG nodes (one per doc) and merge results, or use a published [Agent](../agent/planning.md) with a context-grounding resource |
| The user wants to chat with the document | No — Deep RAG is single-turn. Use an [Agent](../agent/planning.md) with a context resource for conversational behavior |

### Anti-Patterns

- **Do not use Deep RAG for small/simple text.** For a few paragraphs inline in `$vars`, a [Script](../script/planning.md) or [Agent](../agent/planning.md) is cheaper and faster.
- **Do not use Deep RAG as a general agent.** It cannot call tools, escalate, or loop — it is a single synthesis step. For multi-step reasoning with tool use, use an [Agent](../agent/planning.md).
- **Do not chain multiple Deep RAG nodes to emulate multi-document retrieval if the answer requires cross-document reasoning.** Per-document synthesis then merging loses cross-doc grounding. Use a published [Agent](../agent/planning.md) with a proper retrieval resource instead.

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `output` | right | source | Synthesis text (plus citations if enabled) |
| `error` | right | source | Error handler |

No artifact ports. Patterns nodes do not wire to resource files — the prompt lives on the node inputs.

## Output Variables

- `$vars.{nodeId}.output` — an object with:
  - `id` — the result identifier
  - `content.text` — the synthesized prose
  - `content.citations` — optional array (present only when `returnCitations: true`) of `{ ordinal, page, source }` pointing back to the attachment
- `$vars.{nodeId}.error` — populated on failure: `{ code, message, detail, category, status }`.

## Key Inputs

| Input | Required | Type | Description |
| --- | --- | --- | --- |
| `attachment` | Yes | string (file ref) | The document to synthesize. `$vars.*` reference to an upstream file handle, or a concrete UiPath file URI. |
| `prompt` | Yes | string | The task instruction — e.g., "Write a 3-paragraph executive summary", "List every SLA penalty clause", "Answer: what is the termination notice period?". |
| `returnCitations` | No | boolean | When `true`, the `content.citations` array is populated with per-claim page references. Default `false`. |

## Planning Annotation

In the architectural plan:

- `pattern: deep-rag — <one-line purpose>` with a placeholder for the attachment source (usually a `$vars.<upstream>.output.*` file handle) and a short summary of the prompt.
- If the downstream step needs to display or audit sources, call out `returnCitations: true` explicitly in the node table; otherwise leave it `false`.
