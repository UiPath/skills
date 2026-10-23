# Agentic Search — Coded Implementation (Python / LangGraph)

Build a budgeted search loop over a Context Grounding index in a coded agent. Read
[planning.md](planning.md) first and confirm the loop is warranted.

This is the surface where the budget is **enforced** rather than requested. Everything
[impl-prompt.md](impl-prompt.md) can only ask for, you own here.

## The invariant that makes this work

**Enforcement lives in the tool handler, not in the prompt.** A system prompt saying "run at most 3
searches" constrains nothing. Budget, de-duplication, and the minimum-search floor belong in the
function the model calls. The agent's only real freedom should be *what* to search for.

Corollary: **the budget is generated, never typed.** One constant feeds both the prompt text and the
handler that refuses search N+1. Hardcoding `3` in the prompt while the handler enforces `5` is drift
that is invisible in logs.

## Retriever construction is not free-form

Use `ContextGroundingRetriever` from `uipath_langchain.retrievers` — never `sdk.context_grounding.search()`.
Both framework guides require this, and bindings derivation depends on it:
`uip codedagent init` scans code for SDK resource call sites to emit the `index` binding.

**Construct the retriever at one fixed call site with literal `index_name` and `folder_path`.** A
retriever built inside a loop from a variable index name produces no binding, and the agent fails at
runtime with an unresolved resource. Build it once, reuse it across iterations.

See [../coded/capabilities/context-grounding.md](../coded/capabilities/context-grounding.md) for the
retriever's full surface and [../coded/lifecycle/bindings-reference.md](../coded/lifecycle/bindings-reference.md)
for the binding sync workflow.

## Run context

One mutable object per question, created before the agent starts:

```python
from dataclasses import dataclass, field

@dataclass
class SearchBudget:
    limit: int                                    # also interpolated into the prompt
    used: int = 0
    min_searches: int = 1
    seen: set[str] = field(default_factory=set)   # normalized queries
```

`limit` is passed to both the prompt builder and the handler, so moving it moves prompt and enforcement
together.

## The search tool

Order matters. Each step exists because of a specific failure:

```python
import re
from langchain_core.tools import tool
from uipath_langchain.retrievers import ContextGroundingRetriever

RETRIEVER = ContextGroundingRetriever(index_name="company_docs", folder_path="Shared")
MAX_SNIPPET_CHARS = 1200

def _normalize(q: str) -> str:
    return re.sub(r"[^\w\s]", "", q.lower()).strip()

@tool
async def search_knowledge_base(query: str) -> str:
    """Search the knowledge base. Use distinctive terms from the question."""
    if BUDGET.used >= BUDGET.limit:
        return (
            f"Search budget exhausted ({BUDGET.limit} searches used). "
            "Answer now with the evidence you already have, and state what is still missing."
        )

    normalized = _normalize(query)
    if normalized in BUDGET.seen:
        return (
            f"You already searched for '{query}' and it returned the results above. "
            "Search with different terms, or answer with what you have."
        )

    documents = await RETRIEVER.ainvoke(query)
    BUDGET.used += 1
    BUDGET.seen.add(normalized)

    if not documents:
        return f"No results for '{query}'. Try different terms, or report that this evidence is unavailable."

    return "\n\n".join(
        f"[Source: {d.metadata.get('source', 'Unknown')}, "
        f"Page: {d.metadata.get('page_number', 'n/a')}]\n"
        f"{d.page_content[:MAX_SNIPPET_CHARS]}"
        for d in documents
    )
```

| Step | Why |
|---|---|
| Budget check **returns a string, does not raise** | A raised exception tends to end the run rather than produce an answer from partial findings |
| De-duplication **does not increment `used`** | A rejected duplicate returned no new pages. Charging for it silently shrinks the effective budget and makes runs incomparable |
| Normalize before comparing | Lowercase, strip punctuation, collapse whitespace. Without it, `"Return policy?"` and `"return policy"` are two searches |
| Empty result still charges the budget | It consumed a retrieval call, and the agent needs to learn that this phrasing is a dead end |
| Per-snippet truncation | One wide table otherwise crowds out every later result in the context window |
| `[Source, Page]` inline | Citations must exist at the lowest layer or they cannot be required at the top |

Log per call: raw query, normalized query, accepted or rejected, returned document ids, latency.
Realized search count is a reported metric, never an assumption.

## The minimum-search floor, and its gap

To stop the agent answering from parametric knowledge without searching at all, gate the answer:

```python
if BUDGET.used < BUDGET.min_searches:
    return "You have not searched yet. Search the knowledge base before answering."
```

**This floor is bypassable, and you must plan for it.** It only fires when the agent terminates through
a tool you control. An agent that finishes by emitting plain text walks straight past it. Mitigate one
of two ways:

- treat plain-text termination as a run failure in your harness and retry, or
- re-inject a user turn ("You have not searched — answer through the tool") for a bounded number of retries.

Relevant whenever `min_searches >= 1`, which is the normal setting.

## Two-tier shape (optional)

For genuinely multi-hop questions, split the graph: a coordinator node that owns the question and the
answer, and a researcher node that owns the searches. **Give the search tool to the researcher only.**

Pass the researcher a task description that carries the full original question, two or three candidate
search terms, and an instruction to quote exact text with `[Source, Page]`. The coordinator then answers
from quoted findings rather than raw page dumps.

Cap concurrent researchers at one unless you are deliberately measuring a parallel variant — parallel
researchers race on `BUDGET.used` and make the budget nondeterministic.

For graph construction, state shape, and `Command`-driven node transitions see
[../coded/frameworks/langgraph-integration.md](../coded/frameworks/langgraph-integration.md).

## Prompt, generated from the budget

```python
def build_prompt(budget: int) -> str:
    return f"""Answer questions from the knowledge base using the search tool.

You have a maximum of {budget} searches for this question. Use the fewest that answer it.

1. Search with the most distinctive words from the question.
2. If the result answers the question, stop and answer. Do NOT search again to fill the budget.
3. Search again only when something specific is still missing, and only with different terms.
4. Quote exact text with its [Source, Page] citation for every fact you report.

Use only text the search tool returned. Never add your own knowledge. If a list was requested, verify
you captured every item. If you cannot find the information, say so and name what is missing."""
```

Note step 2. Without an explicit early exit the agent delegates and searches until the budget is empty
regardless of whether the first result was sufficient.

## Failure handling

| Condition | Handler response |
|---|---|
| Index returns zero hits | Explicit "no results for this query" string; still charge the search |
| Index or network error | Retry once, then return an error string and flag the run degraded — do not let it look like a genuinely empty corpus |
| Malformed arguments | Return a usage message; do not charge the budget |
| Turn cap reached with no answer | Record as no-answer. Never synthesize an answer in the harness |
| `403 User is missing required index permissions` | Folder permission, not a code bug — see [../coded/capabilities/context-grounding.md](../coded/capabilities/context-grounding.md) § Folder Targeting |

## Before you ship

Run the comparison in [planning.md](planning.md) § Did it beat one-shot. If judged correctness does not
improve over plain index search on the same questions, ship one-shot — the recall gain alone is not a result.

## References

- [planning.md](planning.md) — whether the loop is warranted, mode boundaries, the one-shot comparison
- [impl-prompt.md](impl-prompt.md) — the low-code surface and what prompt-only enforcement cannot do
- [../coded/capabilities/context-grounding.md](../coded/capabilities/context-grounding.md) — retriever
  and vector-store surface, folder targeting, troubleshooting
- [../coded/frameworks/langgraph-integration.md](../coded/frameworks/langgraph-integration.md) — graph
  construction, LLM classes, `uip codedagent init`
- [../coded/lifecycle/bindings-reference.md](../coded/lifecycle/bindings-reference.md) — deriving the
  `index` binding from retriever call sites
