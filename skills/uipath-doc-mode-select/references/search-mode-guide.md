# Search Mode Guide — Semantic (PS) versus Agentic (PA)

Both modes read the same persistent Context Grounding index through the agent's context. The difference
is how many queries answer one question.

This guide selects. `/uipath:uipath-agents — references/agentic-search/planning.md`
owns building the loop.

## Semantic search is the default

One query, ranked snippets, the agent answers from them. `retrievalMode: "semantic"` on an `index`
context resource. Choose it whenever a bounded question is answerable from a few passages — which is most
questions.

An agentic loop costs several times the latency and tokens of one call, and on judged correctness it
often does not beat one-shot. Recall rises mechanically with query count, so a recall improvement alone
never justifies the loop.

## Select agentic search when

At least one must hold:

- **Dependent retrieval** — evidence returned by one lookup determines what to look up next. An
  identifier, code, or cross-reference found in the first result is the input to the second query.
- **Enumerative deliverable** — "list all X", "which of the N documents reference Y". Top-k from a single
  query structurally cannot cover the answer set.
- **Vocabulary mismatch** — the user's wording is unlikely to match the corpus wording, so reformulation
  is the actual bottleneck.
- **Heterogeneous corpus** — the right sub-corpus must be discovered before the real question can be asked.

## Stay with semantic when

- one lookup answers the question;
- the needed metadata is simply absent — more queries cannot recover provenance that was never ingested;
- the question is a single well-defined term or definition;
- completeness cannot be verified anyway, and the deliverable claims it.

## Both modes: retrieval never proves absence

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

## Before invoking the loop

Define four things, or the loop has no shape:

1. **Source scope** — index, version, folder, and access boundary.
2. **Evidence checklist** — what must be found for the question to be answered.
3. **Budget** — a numeric ceiling on searches, and a wall-clock bound if latency matters.
4. **Stop conditions** — sufficient evidence, budget exhausted, or repeated searches returning nothing new.

Return unresolved items rather than guessing. Stopping with a named gap is a result; a fabricated value is not.

## Handing off

| Need | Read |
|---|---|
| Whether the loop is warranted, and how to build it | `/uipath:uipath-agents — references/agentic-search/planning.md` |
| Low-code: guidance prompt, resource settings, enforcement limits | `/uipath:uipath-agents — references/agentic-search/impl-prompt.md` |
| Coded: a retriever wrapper that enforces budget and de-duplication | `/uipath:uipath-agents — references/agentic-search/impl-python.md` |
| Wiring the index context resource itself | [/uipath:uipath-agents — context/index.md](../../uipath-agents/references/lowcode/capabilities/context/index.md) |
| Creating, ingesting, and inspecting the index | [/uipath:uipath-platform — index-management.md](../../uipath-platform/references/context-grounding/index-management.md) |
| Choosing among all four context-grounding modes | [/uipath:uipath-agents — context-grounding-patterns.md](../../uipath-agents/references/context-grounding-patterns.md) |

Enforcement differs by surface: low-code enforcement is prompt-level and best-effort, coded enforcement
is in a handler you own. If the budget must hold, that argues for the coded surface.

Cases: [PS1–PS3](case-library-guide.md#ps-persistent-index--semantic-search),
[PA1–PA3](case-library-guide.md#pa-persistent-index--agentic-search).
