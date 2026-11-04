# Agentic Search — Planning

Agentic search answers **one question with N adaptive queries** over a stable, pre-built Context
Grounding index. Each query is chosen from what the previous ones returned.

It is not a new `contextType` and not a new `retrievalMode`. It is a composition:

```
index search (retrievalMode: "semantic")
  + an agentic-search guidance block in the agent's system prompt
  + the autonomous agent harness's multi-step tool loop
  + an enforced call budget
```

The harness already runs a multi-step tool loop. Left alone it re-queries until the runtime kills it
(`AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS`, in a flow: node Failed, incident `170002`). Agentic search
is that same loop made deliberate and bounded.

## When the loop is warranted

An agentic loop costs 3–10x the latency and tokens of a single retrieval call, and on end-to-end judged
correctness it frequently does not beat one-shot. Recall improves almost mechanically — more queries
means a larger union of retrieved pages — so recall alone is not a reason to ship it.

Use the loop when at least one holds:

- the answer requires **multi-hop** composition across pages or documents;
- the question is **enumerative** ("list all X", "which of the N sites…") and top-k from one query
  structurally cannot cover the answer set;
- the user's vocabulary is unlikely to match the corpus vocabulary, so **query reformulation** is the
  bottleneck;
- the corpus is heterogeneous and the right sub-corpus must be discovered first.

Otherwise route to one-shot index search. Say so explicitly rather than building the loop by default —
the routing decision is part of the deliverable.

## Mode boundaries

| Need | Mode |
|---|---|
| One question, one answer, over runtime **attachments** | DeepRAG — [../lowcode/capabilities/built-in-tools/deeprag/planning.md](../lowcode/capabilities/built-in-tools/deeprag/planning.md) |
| One question, ranked snippets, from a **pre-built** index | Index search — [../lowcode/capabilities/context/index.md](../lowcode/capabilities/context/index.md) |
| One question, **N adaptive queries**, from a pre-built index | **Agentic search** — this guide |
| One row in, one row out, over a CSV | BatchTransform — [../lowcode/capabilities/built-in-tools/batch-transform/planning.md](../lowcode/capabilities/built-in-tools/batch-transform/planning.md) |

Agentic search is a distinct mode from DeepRAG: a stable reusable corpus rather than an ephemeral
attachment index, and N adaptive queries rather than one server-side synthesis pass. DeepRAG's own
iteration is internal and unparameterized — you cannot budget it, inspect its queries, or stop it early.

> `deep-rag`, `deeprag`, `ECS.DeepRag` and `uipath.pattern.deep-rag` are fixed identifiers — node type,
> BPMN `serviceType`, and a `retrievalMode` enum value. Never rename them in code, JSON, or node types.
> Product-name changes apply to display names only; see
> [../../../uipath-maestro-flow/references/author/plugins/summarize/planning.md](../../../uipath-maestro-flow/references/author/plugins/summarize/planning.md),
> which keeps the `deep-rag` wire type under the canvas name "Summarize".

## Shape

Two shapes, and the surface decides which you get.

### Single agent (low-code, and the default)

One autonomous agent with an `index` context resource and a guidance block in its system prompt. The
agent issues a query, reads the snippets, decides whether anything is still missing, and queries again
with different terms. The call cap lives in the prompt.

### Two-tier coordinator / researcher (coded only)

A coordinator that owns the question and the answer, and a researcher sub-agent that owns the searches.
**The coordinator gets no retrieval tool.** That single constraint buys three things:

- query formulation becomes an explicit, inspectable artifact (the task description) instead of an
  implicit step inside one prompt;
- the answer is written in a context holding the researcher's *quoted* findings rather than raw page
  dumps, which reduces drift into tangential content;
- budget accounting has exactly one chokepoint.

Use the two-tier shape when the question is genuinely multi-hop and you need the query trail as an
artifact. For a bounded enumerative question, one agent with a budget is simpler and cheaper.

## Surface selection

| Surface signal | Read |
|---|---|
| `agent.json` with `"type": "lowCode"`, or building in Studio Web Agent Builder | [impl-prompt.md](impl-prompt.md) |
| `pyproject.toml` + `langgraph.json`, or the user wants Python | [impl-python.md](impl-python.md) |

The difference is not cosmetic. It decides whether the budget is **enforced** or merely **requested**:

| Surface | Budget, de-duplication, minimum-search floor |
|---|---|
| Low-code | No handler you own — the index tool is platform-provided. Enforcement degrades to prompt text plus `resultCount` / `threshold`. Best-effort. |
| Coded | You own the tool. Wrap the retriever and enforce all three in code. Deterministic. |

If the question is high-stakes and the budget must hold, that is an argument for the coded surface.

## Did it beat one-shot?

Before shipping the loop, compare it against plain index search on the same questions and the same
index. Score **both**:

- **recall** — did the retrieved set contain the answer;
- **judged correctness / faithfulness** — did the final answer get it right, grounded in quoted text.

Recall rises mechanically with query count, so a recall-only comparison always flatters agentic search
and tells you nothing. Record latency and realized search count alongside; realized count is a measured
output, never an assumption. If judged correctness does not improve, ship one-shot.

## References

- [impl-prompt.md](impl-prompt.md) — low-code: the guidance block, resource settings, and the limits of
  prompt-only enforcement
- [impl-python.md](impl-python.md) — coded: the retriever wrapper that enforces budget, de-duplication,
  and the minimum-search floor
- [../context-grounding-patterns.md](../context-grounding-patterns.md) — mode selection across all four
  context-grounding modes
- [../../../uipath-platform/references/context-grounding/index-management.md](../../../uipath-platform/references/context-grounding/index-management.md)
  — create, ingest, and inspect the index from the CLI
