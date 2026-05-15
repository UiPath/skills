# Summarize Pattern Node — Planning

The Summarize node runs comprehensive document synthesis over an attached file (PDF, Word, etc.): ingest, retrieve, reason, and return prose — optionally with per-sentence citations back to the source pages. It sits in the **Document Processing** category of the add-node panel.

## Node Type

`uipath.pattern.deep-rag`

(The wire type still reads `deep-rag` even though the canvas display name is "Summarize" — the node type is contractual with the runtime serializer and was not renamed.)

Fixed OOTB node type — no registry suffix, one version. It does not appear in `uip maestro flow registry list` unless the tenant has the platform-side `canvas.nodes.summarize` feature flag enabled. The uip CLI unconditionally requests this flag in its manifest fetch, so the node will appear once the server rolls it out to your tenant.

## When to Use

Use Summarize when the task is **"read this document and produce a thorough answer"** — summarization, Q&A, compliance checks, executive briefs — where depth matters and traceability back to the source is valuable.

### Selection Heuristics

| Situation | Use Summarize? |
| --- | --- |
| Summarize a long document (contract, policy, research paper) | Yes |
| Answer a free-form question grounded in one attached document | Yes |
| Produce a report where every claim must cite the source page | Yes — set `returnCitations: true` |
| Short, single-turn Q&A over small text in-memory | No — use [Agent](../agent/planning.md) or [Script](../script/planning.md) |
| Row-by-row enrichment of tabular data | No — use [Batch Transform](../batch-transform/planning.md) |
| Multi-document retrieval across a corpus | No — Summarize is scoped to one attachment per call. Chain multiple Summarize nodes (one per doc) and merge results, or use a published [Agent](../agent/planning.md) with a context-grounding resource |
| The user wants to chat with the document | No — Summarize is single-turn. Use an [Agent](../agent/planning.md) with a context resource for conversational behavior |

### Anti-Patterns

- **Do not use Summarize for small/simple text.** For a few paragraphs inline in `$vars`, a [Script](../script/planning.md) or [Agent](../agent/planning.md) is cheaper and faster.
- **Do not use Summarize as a general agent.** It cannot call tools, escalate, or loop — it is a single synthesis step. For multi-step reasoning with tool use, use an [Agent](../agent/planning.md).
- **Do not chain multiple Summarize nodes to emulate multi-document retrieval if the answer requires cross-document reasoning.** Per-document synthesis then merging loses cross-doc grounding. Use a published [Agent](../agent/planning.md) with a proper retrieval resource instead.

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `output` | right | source | Synthesis text (plus citations if enabled) |
| `error` | right | source | Error handler |

No artifact ports. Pattern-style nodes do not wire to resource files — the prompt lives on the node inputs.

## Output Variables

`$vars.{nodeId}.output` is an object whose schema is published on the OOTB definition (also mirrored on the node instance's `outputs.output.schema`):

- `id` — string, the result identifier
- `content` — `object | null`
  - `content.Text` — string, the synthesized prose
  - `content.Citations` — `array | null`, present only when `returnCitations: true`. Each entry: `{ Ordinal: integer, PageNumber: integer, Source: string, Reference: string }`

Note the **PascalCase** field names (`Text`, `Citations`, `Ordinal`, `PageNumber`, `Source`, `Reference`) — the runtime emits them this way to match the engine response shape; lowercase variants (`text`, `citations`, `page`) are wrong.

`$vars.{nodeId}.error` — populated on failure: `{ code, message, detail, category, status }`.

## Key Inputs

| Input | Required | Type | Description |
| --- | --- | --- | --- |
| `attachment` | Yes | full Flow Attachment | The runtime engine wants the **full Flow Attachment object** (`{ FullName, Id, Metadata, MimeType }`). Source it as a flow-level `in` variable of `type: "file"` bound to the trigger via `triggerNodeId: "<triggerId>"`. The variable's payload is populated by `uip maestro flow debug --attachment <fileVarId>=<path>` (repeatable; `<fileVarId>=` is required). **Invariant:** the LHS `<fileVarId>` MUST equal a `variables.globals[]` entry's `id` where `direction:"in"` AND `type:"file"`. Verify with `jq '.variables.globals[] | select(.direction=="in" and .type=="file") | .id' <flow>.flow` before invoking — the CLI does not yet enforce this and a mismatch faults silently at runtime. Reference it on the Summarize node as `=js:$vars.<triggerId>.output.<fileVarId>` — that path resolves to the whole Attachment object at runtime. The OOTB `inputDefinition.attachment` declares `type: "string"` because Studio Web's file-picker form serializes the object into that string slot at save time; the engine deserializes it back. **Never** wire a bare GUID, URL, byte stream, file path, or `.Id`/`.FullName` subfield. |
| `prompt` | Yes | string | The task instruction — e.g., "Write a 3-paragraph executive summary", "List every SLA penalty clause", "Answer: what is the termination notice period?". |
| `returnCitations` | No | boolean | When `true`, the `content.Citations` array is populated with per-claim page references. Default `false`. |

## Planning Annotation

In the architectural plan:

- `pattern: summarize — <one-line purpose>` with a placeholder for the attachment source (a `=js:$vars.<triggerId>.output.<fileVarId>` reference to a trigger-bound `in` variable of `type: "file"`) and a short summary of the prompt.
- If the downstream step needs to display or audit sources, call out `returnCitations: true` explicitly in the node table; otherwise leave it `false`.
