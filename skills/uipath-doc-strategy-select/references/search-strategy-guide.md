# Search Guide — what a retrieval can and cannot establish

Semantic search reads a persistent Context Grounding index through the agent's context:
`retrievalMode: "semantic"` on an `index` context resource. One query, ranked snippets, the agent answers
from them. Choose it whenever a bounded question is answerable from a few passages — which is most
questions.

This guide selects. `uipath-agents` owns wiring the context resource, and `uipath-platform` owns the
index itself.

## Retrieval never proves absence

A search result supports a positive finding. It cannot establish that something does not exist, and it
cannot establish that everything was found.

| Claim | What it actually requires |
|---|---|
| "No contrary clause exists" | Complete review of the defined document set, with coverage tracked |
| "All impacted documents" | Deterministic corpus enumeration plus reconciliation of processed IDs against the inventory |
| "This policy does not cover X" | Confirmed ingestion and freshness first — otherwise the answer is *unresolved*, not *absent* |

A larger result limit is not a coverage test. Reaching the result cap, lacking an inventory, or hitting
unreadable files all prevent an exhaustive claim — label the list partial.

Verify ingestion and freshness before interpreting an empty result. A silently skipped file format
produces "no relevant hit" that reads exactly like "no such policy".

Return unresolved items rather than guessing. Stopping with a named gap is a result; a fabricated value
is not.

## What one retrieval cannot reach

Three shapes need more than a single scoped lookup. Recognise each one and route it, rather than
answering from a partial read:

- **Dependent retrieval** — evidence returned by one lookup determines what to look up next. An
  identifier, code, or cross-reference found in the first result is the input to the second query.
  Widening the query does not help: the second query is not known until the first has returned. When the
  chain is open-ended — the agent decides how many hops it needs and when it has enough — **this is
  AH**. The advanced harness plans its own next step, and the per-run file workspace carries each hop's
  evidence into the next, which is the two-signal bar in
  [agent-harness-guide.md](agent-harness-guide.md) met by a long run plus persisted intermediate work.
  Bound it even so: a stated numeric ceiling on lookups and a stop rule naming what the agent reports
  when it hits that ceiling. A chain of fixed, known length — look up the code, then look up that
  code's record — is not AH; that is a deterministic sequence of two scoped lookups.
- **Enumerative deliverable** — "list all X", "which of the N documents reference Y". Top-k from a single
  query structurally cannot cover the answer set; that needs deterministic enumeration, and where the
  deliverable is a written review of a defined set, SU1 is the route.
- **Heterogeneous corpus** — the right sub-corpus must be discovered before the real question can be
  asked. Resolve the domain first, as PS3 does, or the question is unanswerable as posed.

Where the needed metadata was never ingested, no amount of querying recovers it — repair the corpus.

## Handing off

| Need | Read |
|---|---|
| Wiring the index context resource itself | [/uipath:uipath-agents — context/index.md](../../uipath-agents/references/lowcode/capabilities/context/index.md) |
| Creating, ingesting, and inspecting the index | [/uipath:uipath-platform — index-management.md](../../uipath-platform/references/context-grounding/index-management.md) |
| Choosing among the context-grounding patterns | [/uipath:uipath-agents — context-grounding-patterns.md](../../uipath-agents/references/context-grounding-patterns.md) |

Cases: [PS1–PS3](case-library-guide.md#ps-persistent-index--semantic-search). For a dependent chain,
[AH1–AH3](case-library-guide.md#ah-advanced-harness).
