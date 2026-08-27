# Summarize Pattern Node — Planning

The Summarize node comprehensively synthesizes one attached document (PDF, Word, etc.) through ingestion, retrieval, reasoning, and prose output, optionally with per-sentence source-page citations. It is in the **Document Processing** add-node category.

## Node Type

`uip.pattern.deep-rag`

The wire type remains `deep-rag` although the canvas name is "Summarize"; this is contractual with the runtime serializer. This fixed OOTB type has no registry suffix and one version. It appears only when the platform-side `canvas.nodes.summarize` feature flag is enabled. The uip CLI requests this flag unconditionally in its manifest fetch, so the node appears after server rollout to the tenant. It does not appear in `uip maestro flow registry list` before then.

## When to Use

Use Summarize for **"read this document and produce a thorough answer"** tasks, including summarization, document-grounded Q&A, compliance checks, and executive briefs where depth or source traceability matters.

| Situation | Use Summarize? |
| --- | --- |
| Long-document summarization, such as a contract, policy, or research paper | Yes |
| Free-form question grounded in one attached document | Yes |
| Reports requiring every claim to cite a source page | Yes — set `returnCitations: true` |
| Short, single-turn Q&A over small in-memory text | No — use [Agent](../agent/planning.md) or [Script](../script/planning.md) |
| Row-by-row tabular enrichment | No — use [Batch Transform](../batch-transform/planning.md) |
| Retrieval across multiple documents | No — Summarize supports one attachment per call. Chain one node per document and merge results, or use a published [Agent](../agent/planning.md) with a context-grounding resource. Do not chain nodes when the answer requires cross-document reasoning; per-document synthesis followed by merging loses cross-document grounding. |
| Conversational document chat | No — Summarize is single-turn. Use an [Agent](../agent/planning.md) with a context resource. |

### Anti-Patterns

- Do not use Summarize for small or simple text. For a few paragraphs inline in `$vars`, use a [Script](../script/planning.md) or [Agent](../agent/planning.md), which is cheaper and faster.
- Do not use Summarize as a general agent. It cannot call tools, escalate, or loop; use an [Agent](../agent/planning.md) for multi-step reasoning with tool use.

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `output` | right | source | Synthesis text, plus citations when enabled |
| `error` | right | source | Error handler |

There are no artifact ports. Pattern nodes do not wire to resource files; supply the prompt through node inputs.

## Output Variables

`$vars.{nodeId}.output` is an object whose schema is published on the OOTB definition and mirrored in `outputs.output.schema`:

- `id` — string, result identifier
- `content` — `object | null`
  - `content.Text` — string, synthesized prose
  - `content.Citations` — `array | null`, present only when `returnCitations: true`; entries are `{ Ordinal: integer, PageNumber: integer, Source: string, Reference: string }`

Use the exact **PascalCase** names `Text`, `Citations`, `Ordinal`, `PageNumber`, `Source`, and `Reference`. Lowercase variants such as `text`, `citations`, and `page` are incorrect.

`$vars.{nodeId}.error` is populated on failure with `{ code, message, detail, category, status }`.

## Key Inputs

| Input | Required | Type | Description |
| --- | --- | --- | --- |
| `attachment` | Yes | full Flow Attachment | Supply the full case-sensitive Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; `ID` is uppercase, not `Id`. Define it as a flow-level `in` variable with `type: "file"`, bound to the trigger using `triggerNodeId: "<triggerId>"`. Populate it with `uip maestro flow debug --attachment <fileVarId>=<path>`; the flag is repeatable and `<fileVarId>=` must match the variable's `id` (see [cli-commands.md — Pre-flight](../../../../shared/cli-commands.md#pre-flight---attachment-binding)). Reference it on the node as `=js:$vars.<triggerId>.output.<fileVarId>`, which resolves to the whole Attachment object. Although the OOTB `inputDefinition.attachment` declares `type: "string"` because Studio Web serializes the object into that slot when saving, the engine deserializes it back. Never wire a bare GUID, URL, byte stream, file path, or `.ID`/`.FullName` subfield. |
| `prompt` | Yes | string | Task instruction, such as an executive summary, a list of SLA penalty clauses, or an answer about a termination notice period. |
| `returnCitations` | No | boolean | Set to `true` to populate `content.Citations` with per-claim page references; default is `false`. |

## Planning Annotation

In the architectural plan:

- Write `pattern: summarize — <one-line purpose>` with a placeholder for the attachment source: `=js:$vars.<triggerId>.output.<fileVarId>`, referencing a trigger-bound `in` variable of `type: "file"`, plus a short prompt summary.
- Explicitly call out `returnCitations: true` in the node table when downstream steps display or audit sources; otherwise leave it `false`.