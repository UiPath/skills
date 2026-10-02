# Reinstating PA — persistent index, agentic search

Agentic search is **not shipped as a file handling strategy** in this skill. It was removed so
`uipath-doc-strategy-select` could ship ahead of the agentic-search reference material it depends on
(`uipath-agents/references/agentic-search/*`, PR #3505).

This file is the reinstatement spec. It holds the **removed content verbatim** and says where each piece
goes back, so restoring PA is a mechanical change rather than an archaeology exercise. Work top to
bottom; the counts and cross-references at the end depend on the sections before them.

**Prerequisite.** `uipath-agents/references/agentic-search/{planning,impl-prompt,impl-python}.md` must
exist on the target branch first. Until they do, restoring the links below fails `skills:check-links`.

---

> **Links in this file are deliberately de-linked** — rendered as `text → target` rather than
> Markdown links. The quoted content points at a section and files that only exist once PA is
> reinstated, and `skills:check-links` validates every relative link in the repository. Restore
> normal link syntax as you paste each block back.

## 1. `SKILL.md`

### 1a. Frontmatter description

Currently reads `... vs batch transform vs persistent-index semantic search, and standard vs advanced ...`
and `For building the agent or its context resource→uipath-agents.`

Restore to:

```
UiPath file handling strategy selection — choose Extract vs Classify & Split vs Summarize vs Analyze files vs batch transform vs persistent-index search (semantic default, or an agentic multi-step search loop), and standard vs advanced autonomous-agent harness, before any node is authored. Matches a workload's output contract, corpus lifetime, evidence scope and review needs to the cheapest strategy that meets them, then hands off. For authoring or wiring the chosen node in a `.flow`→uipath-maestro-flow. For IXP project/taxonomy/model work→uipath-ixp. For building the agent, its context resource, or an agentic-search loop→uipath-agents. For which UiPath product to use at all, or PDD/SDD work→uipath-planner. For the context-grounding index CLI (`uip context-grounding`)→uipath-platform.
```

That is 795 characters against the 1024 cap; the shipped version is 722.

### 1b. Critical Rule 5 — reinsert between rules 4 and 5, renumbering 5–7 back to 6–8

```markdown
5. **Semantic search is the default.** Select an agentic search loop only when evidence from one lookup
   determines the next lookup. Then bound it — a stated numeric ceiling and a stop rule, per
   `/uipath:uipath-agents — references/agentic-search/planning.md`.
```

### 1c. Fast Routing — reinsert the PA row directly after the PS row

```markdown
| **PA** | Persistent index — agentic search | Reusable corpus; dependent questions, scattered evidence, or evidence-driven reformulation | One semantic search suffices; required metadata is absent; completeness cannot be verified |
```

And revert the PS row's reject condition. It currently reads:

> The answer needs evidence joined across dependent lookups — no strategy here covers that yet — or the
> user requires exhaustive coverage, which is SU

Restore to:

> Evidence must be joined across dependent searches, or the user requires exhaustive coverage

### 1d. Workflow — reinsert step 6, renumbering the current step 6 back to 7

```markdown
6. **Choose the search strategy.** Semantic by default; agentic only for dependent retrieval —
   `search-strategy-guide.md → references/search-strategy-guide.md`.
```

### 1e. Reference navigation — retarget the search-guide row

Currently `| What retrieval can and cannot establish, and the completeness boundary |`. Restore to:

```markdown
| Semantic vs agentic search, and the completeness boundary | `search-strategy-guide.md → references/search-strategy-guide.md` |
```

### 1f. Anti-patterns — put agentic search back in the list

Currently `Long documents, a persistent index, many Flow nodes, and a regulated industry ...`.
Restore to:

```markdown
- **Selecting advanced harness by association.** Long documents, a persistent index, agentic search, many
  Flow nodes, and a regulated industry are none of them harness requirements.
```

---

## 2. `references/case-library-guide.md`

### 2a. Reinsert the whole PA section between `## PS` and `## EX`

Insert this, followed by a `---` separator line, immediately before `## EX Extract`:

```markdown
## PA Persistent index — agentic search

Shared configuration: the same persistent index in the agent's context, read through a bounded search
loop. Define scope, an evidence checklist, a numeric budget, and stop conditions before invoking it —
`search-strategy-guide.md → search-strategy-guide.md`, and
`/uipath:uipath-agents — references/agentic-search/planning.md`
for the build.

### PA1 Resolve codes across several reference sources

**Problem description.** A line item has to be interpreted against an item master and two further
attribute sources before it means anything. The identifiers are noisy: aliases, placeholder substitution,
and seasonal variation all change which evidence is needed next, so one lookup identifies only part of
the answer. Working behaviour: an aliased base code and a placeholder are resolved using all the required
sources; where a match lacks the seasonal evidence to confirm it, the result comes back unresolved rather
than as a guessed final code.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop. Harness
chosen independently — the loop is not a harness feature.

**Decision reasoning.** The decisive signal is dependent retrieval: the identifier returned by the first
lookup is the input to the second. Scope to the relevant source and version. Resolve the base item, then
use the returned identifiers to search the dependent attribute sources, then validate the seasonal and
substitution evidence. Keep deterministic substitutions and row iteration in code. Return values with
source lineage and an explicit list of unresolved components.

**Negative example — observed boundary.** A single likely item match did not validate both dependent
attributes. Sheet-origin information was missing, so a constant-looking attribute could not be confirmed
valid for the current season. More searches and majority voting cannot restore provenance that was never
captured.

**Boundary.** An exact, complete keyed mapping belongs in a deterministic lookup, not a search loop. A
single-source question stays PS. If the reference data is small enough to travel with each row, that is
BT2, not a search loop. If the seasonal evidence is absent or contradictory, return needs-review; repair
the metadata or the source access rather than continuing to loop. Structure detection for the same file
is AF1, a separate step.

### PA2 Enrich a request with domain-specific evidence

**Problem description.** An incoming request must be normalized before the receiving office can act on
it. The terminology it should use, the artifacts it should carry, and the obligations that apply are
scattered across the domain corpus, and the mappings are not all predefined — so what to look up next
depends on what the last lookup returned. Working behaviour: a request whose canonical name and evidence
requirement live in different sources is resolved with both cited; an unresolved domain or obligation
becomes a reviewer question rather than a guess.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop after
domain selection. Human review where required.

**Decision reasoning.** The decisive signal is scattered evidence plus undefined mappings — reformulation
is doing real work, not padding recall. Select the domain first. Retrieve candidate obligations, inspect
canonical terms and document context, reformulate for whatever evidence is still missing, and return a
normalized request with citations and open questions. Preserve the retrieval trail and route the proposed
wording for review.

**Negative example — counterexample.** One global semantic hit can normalize the terminology while
missing a separate obligation entirely. Keyword rules alone cannot resolve contextual differences between
offices. Conversely, a simple definition request does not justify a loop at all.

**Boundary.** Bounded knowledge questions are PS3. If the requirement is *every* applicable obligation,
search cannot establish completeness — require a defined source manifest and a full review. Stop when each
required element has evidence or a recorded gap. Do not infer calibrated certainty from an
agent-generated confidence number.

### PA3 Investigate impacted documents, with an exhaustiveness boundary

**Problem description.** Several thousand controlled documents may be affected by a terminology or policy
change, and somebody has asked which ones. Iterative discovery genuinely helps — it finds candidates,
separates current text from revision history, and chases ambiguous references. What it cannot do is
prove it found them all, which matters because the deliverable is phrased as a complete list. Working
behaviour: a current-text hit, a history-only hit, an alias, a duplicate and an inaccessible document are
each handled correctly, and processed IDs are reconciled against the inventory before the list is allowed
to claim completeness; otherwise it is labelled partial.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop for
candidate discovery — **plus** a separate deterministic enumeration and coverage reconciliation whenever
the deliverable claims completeness.

**Decision reasoning.** The decisive signal is a collision: dependent discovery argues for the loop,
while an enumerative deliverable argues that the loop can never finish the job. Expand justified terms,
inspect current-content matches, deduplicate by stable document ID, and record scope and version
evidence. If the deliverable says "all impacted documents", add a deterministic corpus enumeration and
reconcile the processed IDs against the inventory.

**Negative example — observed workaround, unresolved guarantee.** A proof of concept raised the retrieval
result limit and added a review pass because relevance-only retrieval did not meet the enumeration
objective. That design is evidence of a completeness problem, not proof that every impacted document was
found. Reducing the per-run batch size did not help either — the ceiling was being consumed by a single
unbounded investigation, not by the number of items in a batch.

**Boundary.** A search loop is appropriate for investigation and **insufficient on its own for a
guaranteed exhaustive list**. A literal, well-defined keyword scan may be entirely deterministic —
prefer it. Reaching the result cap, lacking an inventory, or hitting unreadable files all prevent an
exhaustive claim.
```

### 2b. Restore the six cross-references

Each row: the shipped text on the left, what it was before on the right.

| Case | Currently reads | Restore to |
|---|---|---|
| AF1 boundary | "that is a grounded lookup and a separate step — not this one" | "that is PA1, separately" |
| PS1 boundary | "one retrieval cannot answer it — say so rather than returning a partial answer" | "that is PA" |
| PS2 boundary | "one scoped retrieval is not enough — flag it rather than answering from a partial read" | "use PA2" |
| PS3 boundary | "reaches past one scoped retrieval" | "is PA2" |
| BT1 boundary | "that is a grounded lookup outside BT — not a column on the row" | "that is PA1" |
| BT2 boundary | "when resolution depends on what an earlier lookup returned, no strategy here covers it yet" | "PA1 when resolution is dependent" |

### 2c. Restore the four Boundary Lookup rows

```markdown
| One semantic hit misses related rules or identifiers | PA1 or PA2 | PS3 for a one-passage question |
| "All impacted documents" or "nothing contradicts" | PA3 or SU1 | A result limit is not a coverage test |
| Search misses files or source metadata | PS1 or PA1 | Repair ingestion and metadata; do not loop blindly |
| Per-row work needs a reference table the row cannot see | BT2 | PA1 when the table cannot be condensed to fit |
```

### 2d. Counts

Header line 3 and the maintenance note at the end of the file:
`21 cases · 7 decision categories` → `24 cases · 8 decision categories`, and
`adding a twenty-second` → `adding a twenty-fifth`.

---

## 3. `references/search-strategy-guide.md`

This file was rewritten from a PS-vs-PA chooser into a PS-only guide. The **absence and completeness
content was deliberately kept** — Critical Rule 4 and the CS3, SU1, PS1, PS2 and PS3 boundaries all
depend on it, so do not overwrite the current file wholesale. Reinstate the removed sections into it.

The pre-removal file in full:

```markdown
# Search Strategy Guide — Semantic (PS) versus Agentic (PA)

Both strategies read the same persistent Context Grounding index through the agent's context. The difference
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

## Both strategies: retrieval never proves absence

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
| Wiring the index context resource itself | `/uipath:uipath-agents — context/index.md → ../../uipath-agents/references/lowcode/capabilities/context/index.md` |
| Creating, ingesting, and inspecting the index | `/uipath:uipath-platform — index-management.md → ../../uipath-platform/references/context-grounding/index-management.md` |
| Choosing among all four context-grounding strategies | `/uipath:uipath-agents — context-grounding-patterns.md → ../../uipath-agents/references/context-grounding-patterns.md` |

Enforcement differs by surface: low-code enforcement is prompt-level and best-effort, coded enforcement
is in a handler you own. If the budget must hold, that argues for the coded surface.

Cases: `PS1–PS3 → case-library-guide.md#ps-persistent-index--semantic-search`,
`PA1–PA3 → case-library-guide.md#pa-persistent-index--agentic-search`.
```

What to put back, specifically:

- The title, `# Search Strategy Guide — Semantic (PS) versus Agentic (PA)`.
- The `## Select agentic search when` section — the four triggers.
- The `## Stay with semantic when` section.
- The `## Before invoking the loop` section — scope, evidence checklist, numeric budget, stop conditions.
  Critical Rule 5 depends on this existing.
- The three `agentic-search/*` handoff rows and the enforcement-surface paragraph.
- `Cases:` gains ``PA1–PA3 → case-library-guide.md#pa-persistent-index--agentic-search``.

What to **drop** when you do: the current `## What one retrieval cannot reach` section. It exists only
to name the gap PA leaves, and becomes wrong once PA is back.

---

## 4. `references/strategy-routing-guide.md`

Reinsert the handoff row after the PS row:

```markdown
| Persistent index, agentic search (PA) | `uipath-agents` | `/uipath:uipath-agents — references/agentic-search/planning.md` |
```

And restore composition pattern 4, currently retitled "Enumeration with a completeness boundary":

```markdown
4. **Investigation with a completeness boundary.** Agentic search for candidate discovery → deterministic
   corpus enumeration and coverage reconciliation when the deliverable claims "all" → review → End. Search
   iteration alone never establishes completeness.
```

---

## 5. `references/agent-harness-guide.md`

Two lines. Currently `- a persistent index;` — restore to:

```markdown
- a persistent index, or an agentic search loop;
```

And currently "one retrieval cannot answer it — see search-strategy-guide.md; no strategy here covers
that shape yet." Restore to:

```markdown
State a numeric cap and a fallback per grounding tool. When the workload genuinely needs several
dependent lookups, that is agentic search — bound it deliberately per
```

---

## 6. `references/case-template.md`

```markdown
- **Keep exactly three cases per category** (AH, AF, CS, SU, PS, PA, EX, BT) unless the user changes
- For PS and PA: is semantic search the default, with the loop selected only for dependent retrieval and
```

Plus `21-case distribution` → `24-case distribution` and `twenty-second` → `twenty-fifth`.

---

## 7. Eval — `tests/tasks/uipath-doc-strategy-select/routing/`

### 7a. Restore the six PA rows to `strategy_selection.jsonl`

Takes the set from 42 rows back to 48, six per strategy across all eight.

```jsonl
{"id": "pa-two-step-vendor-match--a", "pair": "pa-two-step-vendor-match", "variant": "a", "expected_strategy": "PA", "provenance": "engagement", "workload": "Every inbound invoice has to end up matched to a company code and a vendor in our master data. The names printed on invoices are abbreviated, inconsistently punctuated and often not what we hold, so exact matching fails most of the time. There are thousands of locations and millions of vendor records. We would rather an invoice came back unmatched than matched to the wrong vendor."}\n{"id": "pa-two-step-vendor-match--b", "pair": "pa-two-step-vendor-match", "variant": "b", "expected_strategy": "PA", "provenance": "engagement", "workload": "Invoices land and we have to tie each one to a company code and a vendor in our master data before it can be posted. What is printed on the invoice is rarely what we hold — abbreviated, punctuated differently, sometimes a trading name. We have thousands of locations and several million vendor records to search. An unmatched invoice is annoying; one posted against the wrong vendor is a problem."}\n{"id": "pa-lost-participant-trace--a", "pair": "pa-lost-participant-trace", "variant": "a", "expected_strategy": "PA", "provenance": "engagement", "workload": "We have pension participants whose mail keeps bouncing. Tracing one means starting from the plan record, following whatever identifiers that turns up into other sources, and using what comes back to decide where to look next — an employer record leads to a payroll reference, which leads somewhere else again. Where the chain cannot be completed the participant stays flagged as untraced rather than being assigned a best-guess address."}\n{"id": "pa-lost-participant-trace--b", "pair": "pa-lost-participant-trace", "variant": "b", "expected_strategy": "PA", "provenance": "engagement", "workload": "We have pension members whose post keeps coming back. Tracing one starts from the plan record and goes wherever that leads — an old employer reference, then a payroll identifier, then something else again. Some of them we never close out, and those should stay marked untraced rather than get a best guess address."}\n{"id": "pa-obligation-chase--a", "pair": "pa-obligation-chase", "variant": "a", "expected_strategy": "PA", "provenance": "constructed", "workload": "When a new sanctions measure is published, an analyst has to work out which of our internal control standards it affects. The measure cites an authority and a legal instrument; the standards library uses its own numbering and rarely the same wording. Today that is an afternoon of following references from one document into another."}\n{"id": "pa-obligation-chase--b", "pair": "pa-obligation-chase", "variant": "b", "expected_strategy": "PA", "provenance": "constructed", "workload": "A new sanctions measure gets published and somebody has to say which of our control standards it touches. The measure names a legal instrument; our standards use their own numbering and different language. Working it out means following the references from one place to the next until you run out."}
```

These three workloads are drawn from real engagements and carry PA's decisive signals: two-step
dependent matching over large reference sets, a trace that follows identifiers from one source to the
next, and a sanctions-instrument chase. All three were correct at 6/6 in the last full run, so they are
known-good rows rather than speculative ones.

### 7b. `strategy_selection.yaml`

- Prompt: `one of AH, AF, CS, SU, PS, EX, BT` → `one of AH, AF, CS, SU, PS, PA, EX, BT`
- Description: `42 rows: 21 workloads` / `across all seven` → `48 rows: 24 workloads` / `across all eight`

### 7c. `check_strategy.py` and `analyze_consistency.py`

Both carry the same tuple. Put `"PA"` back between `"PS"` and `"EX"`:

```python
STRATEGIES = ("AH", "AF", "CS", "SU", "PS", "PA", "EX", "BT", "NONE")
```

### 7d. `routing_smoke.yaml` — restore the original task

This task asserted PA3 and was rewritten to assert SU1 instead. Its pre-removal form:

```yaml
task_id: skill-doc-strategy-select-routing-smoke
description: >
  Smoke test: a reusable-corpus workload with dependent lookups must route to
  agentic search rather than one-shot semantic search, and must carry the
  completeness boundary the skill teaches. Verifies the skill fires and that
  its routing contract — strategy, decisive signal, case ID, boundary — is applied,
  rather than a bare strategy label.
tags: [uipath-doc-strategy-select, smoke, mode:build, lifecycle:discover]

run_limits:
  expected_turns: 5

initial_prompt: |
  We keep several thousand controlled procedure documents in a knowledge index
  that is reused across runs. A reviewer asks: "which of these documents still
  reference the retired escalation terminology?" — the wording varies between
  documents, so one lookup never finds them all, and the reviewer needs the
  complete list.

  Load the applicable UiPath skill and route this workload. Write your routing
  decision to `route.txt` as a single line in the skill's reporting format,
  followed by two or three lines explaining what is required before the list
  can be called complete.

  Do NOT create a project, a flow, or an agent. Write only `route.txt`.

success_criteria:
  - type: skill_triggered
    description: "Agent invoked the uipath-doc-strategy-select skill"
    expected_skill: "uipath-doc-strategy-select"
    skill_name: "uipath-doc-strategy-select"
    weight: 1.5
    pass_threshold: 1.0

  - type: file_exists
    description: "Agent produced route.txt"
    path: "route.txt"
    weight: 1.0
    pass_threshold: 1.0

  - type: file_contains
    description: "Routed to agentic search on the dependent-lookup signal, citing the PA3 case"
    path: "route.txt"
    includes:
      - "PA3"
    weight: 3.0
    pass_threshold: 1.0

  - type: file_contains
    description: "Applied the completeness boundary rather than treating search as exhaustive"
    path: "route.txt"
    includes:
      - "enumerat"
    weight: 3.0
    pass_threshold: 1.0
```

When PA returns, the honest version of this workload asserts **both**: SU1 for the written review and
PA3 for the bounded discovery loop, with the deterministic enumeration as the boundary between them.

---

## Validation after reinstating

```bash
npm run skills:check-links                          # the agentic-search links must resolve
python3 scripts/check-skill-status.py --write-readme
python3 scripts/check-skills-sh.py
bash hooks/validate-skill-descriptions.sh           # description goes 722 -> 795 chars
python3 scripts/check-task-host-paths.py
python3 scripts/check-task-driver.py
```

Then confirm by hand, because no script checks these:

- Critical Rules run 1–8 with no gap, and the workflow runs 1–7.
- `case-library-guide.md` reports 24 cases across 8 categories, and `grep -c '^### '` agrees.
- Every Boundary Lookup row names a case that exists.
- `case-template.md`'s closing checklist still asks whether the links, the fast-routing table, the
  boundary lookup and the case distribution all agree — they are the four things this change desyncs.
