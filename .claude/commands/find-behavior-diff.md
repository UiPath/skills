---
# Front-matter = metadata ABOUT the command (YAML). Every field is optional.
description: Behavior-diff + cost-attribution report between an optimized and a baseline run
# Usage hint shown inline as you type:  <required>  [optional]
argument-hint: "[optimized-run-path] [baseline-run-path] [output-dir] [classification-md-path]"
# Tool allowlist. Needs to read runs, write the report + chart image, and run matplotlib via uv.
allowed-tools: Read(*), Glob(*), Grep(*), Bash(*), Write(*), Edit(*)
# Optional: pin a model. Omit to use the session's current model.
# model: claude-sonnet-4-6
---

## Context

You are optimizing agent skills to reduce the cost of using coding agents. The cost model is in `/home/azureuser/projects/coder_eval/tmp/cost.md`. Cost is measured by **3 cost dimensions** — (1) thinking tokens, (2) tool-result tokens, (3) tool-calls/turns — targeted by **3 optimization techniques**:

- **Scripted skills**: turn deterministic procedures found in the skill files into scripts to cut tool-calls/turns; they also cut thinking (the agent doesn't re-derive an encoded procedure) and, for some scripts, tool-result tokens (output written to a file instead of into context).
- **Thinking budget prompt (RB1, RB2)**: softly curb reasoning to cut thinking tokens.
- **Working style prompt (WS1–WS7)**: 7 bullets, each targeting different cost dimensions.

The exact injected prompts are in `/home/azureuser/projects/coder_eval/tmp/skill-optimization/analysis-tools/docs/prompts/skill-md-injected-block.md`. Load it to get the current RB1/RB2 and WS1–WS7 wording before attributing.

**Inputs:** `$1` optimized run, `$2` baseline run, `$3` output dir, `$4` classification md (e.g. `.../classification/classification-details-<skill>.md`) whose "What the Skill Teaches" table lists which procedures are codifiable.

**Scope:** compare only tasks that **succeeded in both runs** ("both-solved"). Each run path may hold one or many tasks (`<run>/default/<task>/<rep>/task.json`); each task may have repeats. Report `n` (reps/task) and, if n=1, flag per-task numbers as point estimates.

**Aggregating repeats — use the recurring behavior, not a plain mean.** When a task has multiple repeats, a single aberrant rep (a timeout, a wrong-skill detour, a `format`/`validate` debug spiral, a lone giant thinking burst) can dominate a plain mean and manufacture a fake win/regression. So for each task+arm: (1) keep only successful reps; (2) identify the **recurring (modal) behavior** and **exclude the behaviorally-aberrant minority** — operationally, drop a rep if its four-lever behavior vector (tool-calls, turns, tool-result tokens, thinking tokens) deviates from the reps' median by more than `max(floor, 3·MAD)` on ANY lever (suggested floors: 6 calls, 6 turns, 20k tool-result, 6k thinking), requiring at least half the reps to survive (else fall back to all successful reps); (3) take the per-task value as the **mean over the surviving recurring reps**. Report how many reps were excluded. Rationale: "if 4 of 5 reps behave the same way, the comparison should be against that recurring behavior, not against the 1 outlier." For the per-task **narrative** (Step 3) describe a rep drawn from the recurring set, not an excluded outlier; if you narrate rep `00` and it was excluded, say so and describe the recurring behavior instead.

---

## Step 1 — Collect the data from `task.json` (do this exactly; it makes the report reproducible)

For every both-solved task, per successful rep, read `task.json` and compute:

- **thinking tokens** = Σ `output_tokens` of *thinking-only* assistant messages under `iterations[].messages[]` (a message whose `content_blocks` block-types are exactly `{"thinking"}`).
- **tool-result tokens** = Σ `result_tokens` over `iterations[].commands[]`.
- **tool-calls** = `len(iterations[].commands[])`. A **script invocation** = a `commands[]` entry with `tool_name=="Bash"` whose `parameters.command` matches `python3 …/<script>.py` (a `Read`/`grep`/`cat` of the script source does NOT count). Count per script (e.g. scaffold/drift/diagram).
- **cost** = `total_token_usage.total_cost_usd`.
- **cache-read** = `total_token_usage.cache_read_input_tokens`; **cache-create** = `total_token_usage.cache_creation_input_tokens`; **output** = `total_token_usage.output_tokens`; **uncached** = `total_token_usage.uncached_input_tokens`.
- **time** = `duration_seconds`. **turns T** = cost-model agentic-step count (think→call-tools→observe cycles).
- **task instruction** = `task_description`.
- **ordered action trace** = walk `iterations[].commands[]` in order (Skill / Read / Write / Edit / Bash / TaskCreate·Update / Glob·Grep), plus thinking bursts ≥1.5k tok, to describe how the agent solved it.
- **the four targeted-lever deltas** — `Δtool-calls`, `Δturns`, `Δtool-result tokens`, `Δthinking tokens` (OPT − BASE). These four are exactly what the optimization can move, and they drive the real-vs-noise test in Step 2, so store them on every row.

Aggregate: per task take the **recurring-rep mean** (the mean over surviving reps after excluding behavioral outliers — see Scope); `Δ = OPT − BASE`; task-averaged and summed across the both-solved set.

**Tokens are read directly; per-bucket dollars are derived.** `task.json` stores each bucket as a **token count** and stores only ONE dollar field — `total_token_usage.total_cost_usd` (the authoritative whole-task total). So prefer **token counts** when describing where cost sits or moves; they come straight from the file. Any per-bucket dollar split is a derivation: bucket tokens × Sonnet rate (output/thinking **$15/M**, cache-read **$0.30/M**, cache-create **$3.75/M**, uncached **$3/M** — the `g≈5× / r≈0.1× / w≈1.25×` tiers). **Verify the rates by reconciliation**: `output×$15/M + cache_read×$0.30/M + cache_create×$3.75/M + uncached×$3/M` must equal `total_cost_usd` to ~$0 on every `task.json`; if it does, the split is a faithful decomposition of the real total (not a guess) and can be quoted — otherwise fix the rates before dollarizing. `total_cost_usd` deltas are always exact; the only interpretive cut is splitting output into thinking vs non-thinking.

Prefer writing one small Python script under `$3/` (or the scratchpad) that emits a JSON of per-task rows (all metrics + the four lever deltas), so the tables, chart, and noise test all draw from the same numbers.

## Step 2 — Attribute each task's difference (ranked by dominance)

Assign the cost change to **scripted skill / thinking-budget (RB1,RB2) / working style (name the WS# bullet) / noise** — for working style, cite the specific bullet(s). Rules:
- **Scripts** get credit only when a bundled script replaced *multiple* manual tool calls or a derivation burst — verify by reading the BASE trajectory (e.g. BASE hand-writes 6 metadata files / reverse-engineers a schema; OPT does it in one `scaffold_metadata.py` call). Isolate bundled scripts from the agent's own inline-python (that's working style WS5).
- **Thinking budget** when BASE has large abstract reasoning bursts that OPT trims (check the burst tokens shrink).
- **Working style** when OPT drops to-do ceremony (WS2/WS7), fishing (WS4/WS7), re-reads (WS4), heavy references (WS3), pipes bulk output to files/redirects (WS6), or chains CLI calls into one turn (WS2).
- Be honest: many small tasks are **n=1 noise** or an **environment confound** (e.g. the validator npm-install "dance"); call these out rather than crediting the optimization. Note real **backfires** (e.g. reading script source re-triggering re-planning).
Explain, per task, why the behavior change raised/lowered cost via the cost-model term (`g` thinking, `r·(T−t)` re-read, `w` write).

**The real-vs-noise test (apply to EVERY task, wins and regressions alike).** Because runs are single-rep (n=1), a cost difference is only a real optimization effect when the agent **measurably did something different** — otherwise it is noise, regardless of how large the dollar swing is. "Different" is judged across the **four levers the prompts target: tool-calls, turns, tool-result tokens, and thinking tokens.** Thinking counts because RB1/RB2 target reasoning directly, so a materially different amount of thinking (even with calls/turns/tool-result flat) is a genuine prompt effect — the RB2-burst regressions and the thinking-shrink wins are real, not noise. Operational threshold: a task is a **real** effect if any lever moved non-trivially — **≥3 tool-calls, ≥3 turns, ≥5k tool-result tokens, or ≥1.5k thinking tokens**; if all four are ~flat and only the dollars moved, label it **noise** and do NOT credit/blame the optimization. Compute this from the four lever deltas on each row. Report, for both wins and regressions: how many are real vs noise, the $ each group carries, and — the key honesty check — that the noise should roughly **cancel across the set** (symmetric ± swings), so the net saving is attributable to the real behavior changes rather than to n=1 luck. Thresholds are heuristics: state them, treat borderline (especially single-burst thinking) cases as gray-zone needing replication.

## Step 3 — Write `$3/report.md` in EXACTLY this structure

Reproduce these sections, headings, and formats verbatim (this is the required output shape):

**Title + intro** — `# <skill> skill optimization — cost-reduction report`, then the "Cost reduction is measured by 3 cost dimensions … targeted by 3 optimization techniques" paragraph and the three bullets (Scripted skills / Thinking budget prompt / Working style prompt), as in the Context above.

**`## Script Generation of <skill>`** — from the classification md at `$4`:
1. Para 1: the skill's work-area overview (copy the classification md's lead-in).
2. Para 2: "**M out of N areas** can be turned into scripts, and the corresponding scripts are: …" (count the Codifiable=Yes rows; list the script filenames).
3. **Para 3 (required): specify the source** — name the classification md used, e.g. "Codifiability is taken from `<path to $4>`." 
4. Then a note that many remaining areas are CLI calls the working-style prompt chains into one tool call by planning ahead.
5. Then copy the classification md's numbered "What the Skill Teaches" table (`| # | Area | Codifiable? | Notes |`) verbatim.

**`## Summary`** (four subsections, in this order)
- `### Overall Results` — generate a normalized BASE-vs-OPT bar chart with matplotlib (run via `uv run --with matplotlib python <script>`), save to `$3/images/overall-results.png`, and embed it with a relative `![…](images/overall-results.png)` link + a one-line caption. Chart spec: horizontal grouped bars, each metric **normalized to BASE=100%** (so different scales share one axis), rows = Total cost, Total time, Cost/task, Thinking tokens, Tool-result tokens, Tool-calls, Cost-model turns (unit + scope in each row label), BASE = neutral gray, OPT = a CVD-safe blue (#0072B2), direct value labels + a `−X%` reduction callout per row, legend below, x-axis "Value relative to BASE (BASE=100%)". Then a **"Where the $X saving comes from"** table: `| bucket | Δ tokens (sum) | share | cost-model term |` with rows thinking (`g·thk`), cache-read (`r·(TR+G)·(T−t)`), non-thinking output = output−thinking (`g·(cl+tc)`), cache-create + uncached (`w·TR`); share = each bucket's % of the total $ saving (this share column is the one derived split — the `Δ tokens` column is direct). **Add a one-line note under the table** stating that its `Δ tokens` values are **exact sums over tasks**, while the chart's per-task figures are **rounded for display**, so multiplying a rounded chart delta by the task count won't exactly reproduce these sums (a small rounding gap); the exact sums (and the $ total from `total_cost_usd`) are authoritative.
- `### Where the cost comes from before optimization — and how OPT cuts it` — the causal story, in **prose leaning on token counts** (direct from `task.json`), not derived dollar percentages. Para 1 (BASE origin): what dominates the BASE bill — state the raw token magnitudes (e.g. "~XM cache-read + ~XM cache-create context tokens vs only ~Xk thinking") to show whether cost is context-driven or reasoning-driven, and name the BASE pathologies that run it up (big refs/CLI dumps parked in context and re-read every turn, to-do ceremony, fishing, full-file rewrites). Para 2 (how OPT cuts it): the behavior changes that shrink those sources and the resulting token reductions (which lever falls most). Then a **wins mechanism table** `| Mechanism (what OPT changed) | Term | Examples (Δcost) |` (3–5 rows: keep-output-out-of-context WS3/WS6, skip-unneeded-refs WS3/WS7, collapse-over-reasoning RB1/RB2, cut-turns/chain-CLI WS2/WS7, edit-don't-rewrite WS5 — each with 2–4 real task examples and their Δcost). Close with a **`Real vs. noise`** paragraph that DEFINES the four-lever behavioral test once (it is reused by the next subsection) and reports the **wins** split: N real / M noise, the $ each carries, and the noise task names.
- `### Why cost increases in some tasks` — only if there are regressions. State the count that cost more **and** how many are attributable vs noise by the same test (e.g. "43 cost more, ~36 attributable, ~7 noise"). A **regression mechanism table** (same columns) — typically: hand-assembly/turn-sprawl (inline-python-heredoc loop breaking `format`/`validate` into debug spirals; WS2/WS4/WS5/WS7 backfire), RB2-firing-when-it-should-reserve (large unprompted thinking bursts; `g·G`), read-first-over-applied (big refs/full-file-rewrites into context; `w·TR`). Then a **`Real vs. noise` (regressions)** paragraph applying the test defined above, plus a **netting** paragraph: across all tasks, X real / Y noise, noise is roughly symmetric (±) so it nearly cancels, therefore the headline saving is ~entirely attributable to real behavior changes, not n=1 luck. End with the concrete remediation targets the regressions imply.
- `### How Are results Collected` — the methodology: for thinking / tool-result / tool-calls (with script-invocation rule) and the four `total_token_usage` cache/output buckets, give the exact `task.json` field path and a tiny real JSON example (as in Step 1). Note that bucket **token counts are read directly** and `total_cost_usd` is the only stored dollar (per-bucket dollars are derived and reconcile to it exactly). State the both-solved / success-only scope and the n per task.

**`## Case Analysis`** — output the heading only, **leave the body empty** (the user fills this in manually). Do not write anything under it.

**`## Reference`**
- `### Per Task Table` — first a **"Script usage & benefit:"** line: how many tasks invoked a bundled script, how many of those got cheaper / flat / more expensive, and in how many the script was the *dominant* driver. Then the table, one row per both-solved task, sorted by cost delta (best→worst):
  `| # | task | Δcost | Δthinking tok ($) | Δtool-result tok | Δtool-calls | Δtime | scripts sc/dr/gd | attribution (ranked) |`
  where Δcost = `$BASE→$OPT (−%)`, Δthinking shows tokens and the $ (Δthinking × $15/M), Δtime = `BASEs→OPTs (−%)`, scripts = per-script invocation counts, attribution = the ranked drivers from Step 2.
- `### Per Task Behavior` — one block per both-solved task (same order), each:
  ```
  **<task>** (<Δcost%>, <short attribution>)
  - Task: <task_description>
  - Before (BASE): <how the agent solved it pre-optimization, from the trajectory>
  - After (OPT): <how it solved it post-optimization, from the trajectory>
  - **Why cheaper:** <or **Why MORE expensive:** for regressions — tie the behavior change to the cost-model term and the measured deltas. If the four levers are all flat and only the dollars moved, say so explicitly and label the delta **n=1 noise** rather than attributing it to the optimization>
  ```

All numbers must come from the Step-1 extraction (cite `task.json` fields, not guesses). Keep prose factual; where a figure is interpretation (e.g. attribution) say so. The per-task noise calls here must be consistent with the real-vs-noise counts reported in `## Summary`.
