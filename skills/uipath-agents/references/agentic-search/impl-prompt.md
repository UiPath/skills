# Agentic Search — Low-Code Implementation

Turn a low-code autonomous agent's index context into a bounded search loop. Read
[planning.md](planning.md) first and confirm the loop is warranted; most questions should stay one-shot.

## What you can and cannot enforce here

The index tool is platform-provided. There is no handler you own, so **every constraint below is a
request to the model, not a guarantee**. Prompt-only enforcement is exactly the regime that
[../lowcode/capabilities/context/index.md](../lowcode/capabilities/context/index.md) § Gotchas documents
failing when it is left implicit — an uncapped agent re-queries until the runtime kills it, and raising
`settings.maxIterations` only moves the failure.

| Constraint | Low-code mechanism | Holds? |
|---|---|---|
| Maximum searches | A hard number in the system prompt | Usually, if stated as a number and paired with a stop rule |
| Never repeat a query | A prompt instruction | Weakly — the model cannot see its own normalized history |
| Minimum one search before answering | A prompt instruction | Weakly |
| Result breadth per call | `settings.resultCount` | Yes — platform-enforced |
| Score floor | `settings.threshold` | Yes — platform-enforced |
| Absolute loop ceiling | `settings.maxIterations` | Yes, but it is a kill switch: the run fails, it does not answer |

If the budget must hold deterministically, build on the coded surface instead — [impl-python.md](impl-python.md).

## Step 1 — Wire the index context resource

Add an `index` context resource with `retrievalMode: "semantic"`. Full walkthrough, resource shape,
solution files and refresh mechanics: [../lowcode/capabilities/context/index.md](../lowcode/capabilities/context/index.md).

Two settings carry the loop:

```jsonc
"settings": {
  "retrievalMode": "semantic",
  "query": { "variant": "dynamic", "description": "Search query for this step of the investigation" },
  "resultCount": 5,
  "threshold": 0
}
```

- `query.variant` MUST be `"dynamic"`. The agent supplies each query at runtime; `"static"` and
  `"argument"` both pin the query and make a loop impossible.
- `resultCount` is breadth per call, not depth. Raising it is not a substitute for a second query with
  better terms — it returns more of the same neighbourhood.
- Leave `threshold` at `0` while tuning. A non-zero floor silently empties later, narrower queries and
  the agent reads that as "no such evidence".

`contextType` and `retrievalMode` values are lowercase — see
[../lowcode/critical-rules/critical-rules.md](../lowcode/critical-rules/critical-rules.md) Anti-pattern 12.

## Step 2 — Add the guidance block to the system prompt

Append this to the agent's system prompt, after its role and output contract. Replace `<N>`,
`<toolName>` and the corpus description; keep the structure.

```text
## Searching the knowledge base

Answer from <toolName> results only. Never add facts from your own knowledge.

Run up to <N> searches for this question. Spend them only as needed — a single well-targeted search
is often enough.

1. Search with the most distinctive words from the question.
2. Read what came back and decide: does it already answer the question? If yes, stop searching and
   answer now. Do not search again to fill the budget.
3. Search again ONLY when something specific is still missing, and only with different terms —
   synonyms, related concepts, or a name, code, or number that appeared in the previous results.
   Never re-run a search you have already run.
4. After <N> searches, stop and answer with what you have.

Before answering, re-read the question and check:
- Have I found the specific fact, number, or list that was asked for?
- If a list was requested, have I found ALL items, not just the first few?
- Am I quoting the right section, not an adjacent table?

If you cannot find the information, say so plainly and name what is missing. Never invent a value to
fill a required output field.
```

### Why each clause is there

| Clause | Failure it prevents |
|---|---|
| "stop searching and answer now" | Without an explicit early exit the agent searches until the budget is empty regardless of whether the first result was sufficient |
| "only with different terms" | A re-issued query returns identical snippets and buys nothing; repeated searches are the dominant budget leak |
| "after `<N>` searches, stop and answer" | Separates a spent budget from a failed run. Without it the loop ends at `maxIterations` with no answer at all |
| "if a list was requested, have I found ALL items" | Truncated lists — the first match reported as the whole set |
| "never add facts from your own knowledge" | Parametric leakage — plausible facts absent from the corpus |
| "say so plainly and name what is missing" | An unresolved question returned as a confident wrong answer |

## Step 3 — Discipline the answer, not just the search

Four failure modes recur. Each needs a line in the output contract, not just in the search block:

| Failure | Rule to state |
|---|---|
| Over-answering — a multi-section essay in reply to "how many?" | Match answer scope to question scope |
| Bare values — `42.8 million` with no scenario attached | Never emit a value without its qualifying context |
| Parametric leakage — plausible facts that are not in the corpus | Use only retrieved text |
| Truncated lists — the first match reported as the whole set | Re-read the question; verify every item is captured |

## Step 4 — Set the ceiling, and know what it is

Keep `settings.maxIterations` at its default 25. It is a kill switch, not a loop control: the run fails
at the ceiling, it does not answer. Your `<N>` from step 2 is what actually ends the loop; `maxIterations`
only stops a runaway from burning tokens indefinitely. Setting it to `<N>` is a mistake — the agent needs
iterations for reasoning and output shaping beyond its searches.

See [../lowcode/prompting/autonomous-agent-prompting-guide.md](../lowcode/prompting/autonomous-agent-prompting-guide.md)
for the surrounding system-prompt skeleton this block slots into.

## Gotchas

- **The early-exit clause is load-bearing.** Removing "stop searching and answer now" reliably turns a
  3-search budget into 3 searches on every question, including the ones the first result answered.
- **State the budget as a number, not an adjective.** "Search a few times" and "search as needed" both
  read as "no limit".
- **Do not describe the budget in two places with two numbers.** One number, one sentence. A prompt that
  says "up to 3" in one paragraph and "up to 5" in another gets the larger of the two, or neither.
- **A larger `resultCount` is not proof of coverage.** For "all impacted documents", retrieval cannot
  establish completeness at any breadth — pair it with a deterministic enumeration of the corpus and
  reconcile, or label the list partial.
- **Debug with the query trail.** Run `uip agent debug` and read which queries the agent actually issued.
  Repeated near-identical queries mean the "different terms" clause is not landing; queries unrelated to
  the question mean the distinctive-terms instruction needs the corpus register named explicitly.

## References

- [planning.md](planning.md) — whether the loop is warranted at all, and the one-shot comparison
- [impl-python.md](impl-python.md) — the coded surface, where the budget is actually enforced
- [../lowcode/capabilities/context/index.md](../lowcode/capabilities/context/index.md) — the index
  context resource: shape, solution files, refresh, ingestion
- [../lowcode/prompting/autonomous-agent-prompting-guide.md](../lowcode/prompting/autonomous-agent-prompting-guide.md)
  — system-prompt skeleton and production checklist
