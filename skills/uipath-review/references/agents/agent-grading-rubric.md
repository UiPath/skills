# Agent Review — Letter Grade (A–F)

How the review computes the letter grade for **agent projects** (low-code `agent.json` and coded `main.py`). Run this in **Step 4.5**, after agent validation (Step 2), the review CLI + judgment catalog (Step 2.5), manual review (Step 3), and optimization + architecture scoring (Step 4) — the grade is a function of those outputs, never a fresh judgment.

> Scope: agents only, matching the skill's phase-1 model (the Step 2.5 judgment catalog is agent-only today; RPA, flows, and coded apps are future phases). Do **not** grade non-agent projects with this rubric. When a solution mixes agents with other types, grade the agent projects and leave the others ungraded (note "grading: agents only, phase 1").

The grade has two sub-grades, computed independently, then gated:

```
Final grade = min(G_det, G_jud)
```

- **G_det** — deterministic sub-grade. **Read it directly from the review CLI** — do not recompute it. `uip agent review` / `uip codedagent review` returns `Data.Grade`, the grade it assigns to its own deterministic checks. That letter **is** G_det.
- **G_jud** — non-deterministic sub-grade. Driven by judgment: the agent judgment catalog ([agents-common-rules.md](agents-common-rules.md) + the format file) read in Step 2.5b, the manual agent checklist ([agent-review-checklist.md](agent-review-checklist.md)) in Step 3, and the architecture-principle scores (1–5) from [architecture-assessment-guide.md §4](../architecture-assessment-guide.md).

`min()` means an agent cannot earn an A from a clean CLI grade if its prompt, tools, and error handling are weak (G_jud gates it down), and cannot earn an A from strong design if the CLI's deterministic grade is poor (G_det gates it down). The grade is bounded by the weaker dimension. Because `min` only ever lowers the CLI grade, the **skill grade is always ≤ `Data.Grade`**.

## G_det — read it from the review CLI, never recompute

`uip agent review` / `uip codedagent review` already runs every deterministic check (structural/schema, placeholder cross-refs, eval counts/diversity, secret & import regex, framework symbol existence, packaging/git hygiene) and grades them. Read the grade from the JSON response and use it verbatim:

```
G_det = <response>.Data.Grade        # e.g. "B"
```

The response also carries `Data.Verdict` (PASS/FAIL) and `Data.Score`; `Data.Grade` is the letter to use.

**Do not tally `Data.Issues[]` and re-derive a grade.** Recomputing duplicates work the CLI already did and risks drifting from the CLI's own grade — the exact inconsistency this design avoids. The deterministic findings (`Data.Issues[]`) are still carried into the report verbatim (Step 2.5a), but the *grade* comes from `Data.Grade`, not from counting them.

If `Data.Grade` is missing or the CLI is unavailable, see [Edge cases](#edge-cases).

## G_jud — the judgment sub-grade you compute

This is the only sub-grade the agent computes, because no CLI can grade it reliably.

**Step 1 — Architecture-average base.** Average the applicable principle scores (1–5) from [architecture-assessment-guide.md §4](../architecture-assessment-guide.md): Modularity, Resilience, Maintainability, Security, Governance. **Scalability is usually N/A for a single agent** — exclude it (and any other principle that does not apply) and average the rest; **state which were excluded** in the report. Score against agent-appropriate evidence: Modularity = prompt/tool decomposition, Resilience = error handling around LLM/tool calls, Maintainability = prompt and tool clarity + eval coverage, Security = secret handling + guardrails, Governance = tracing + eval sets + versioning.

| Architecture average | base G_jud |
|---|---|
| 4.5 – 5.0 | **A** |
| 3.5 – 4.49 | **B** |
| 2.5 – 3.49 | **C** |
| 1.5 – 2.49 | **D** |
| 1.0 – 1.49 | **F** |

**Step 2 — Judgment-finding cap.** The principle scores already absorb most judgment findings (a "no error handling around `llm.ainvoke`" finding is why Resilience scored 2). Apply only one additional cap, to catch a blocking design flaw the averaged scores understate:

- Any **unmitigated judgment Critical** caps G_jud at **D**.
- A judgment Critical with **security or data-integrity** impact (prompt-injection exposure, secret leak into tool args, no guardrail on a destructive tool) caps G_jud at **F**.

Do not apply further per-Warning deductions — that double-counts against the principle scores.

> Findings from the review CLI (`Data.Issues[]`) already shaped `Data.Grade` = G_det — do **not** also let them cap G_jud. Only **judgment** findings (Step 2.5b catalog + Step 3 manual) feed G_jud. This keeps each finding in exactly one sub-grade.

## Final grade and rationale

`Final = min(G_det, G_jud)` where `G_det = Data.Grade`. Always report the **binding constraint** in one line so the grade is auditable:

```
Agent Grade: B — gated by G_det (CLI Data.Grade B). Design is strong (G_jud A, arch avg 4.5).
```

Map the letter to the verdict word (this is the only place the letter→word mapping lives; the bands that produce each letter live above / in the CLI):

| Grade | Verdict label |
|---|---|
| **A** / **B** | Good |
| **C** / **D** | Needs Improvement |
| **F** | Critical Issues |

## Per-agent vs overall

- **Per-agent grade:** read `Data.Grade` (G_det) and compute G_jud for the agent; grade = `min`. Report in the Per-Project Summary table (Step 5) for each agent row; leave non-agent rows ungraded (`—`).
- **Single-agent review:** the overall Agent Grade IS the agent's grade.
- **Solution with multiple agents:** the overall Agent Grade = the **worst** per-agent grade. A solution is only as deployable as its weakest agent — do not average grades. Non-agent projects do not contribute a grade (phase 1).

## Edge cases

| Situation | Handling |
|---|---|
| **`Data.Grade` absent** (older CLI returns only `Data.Verdict` / `Data.Score`) | Map what the CLI gives you: `Data.Verdict = FAIL` → G_det = F; otherwise translate `Data.Score` to the nearest A–F using the same band widths the CLI documents. Note the substitution in "Rules Skipped". |
| **Review CLI unavailable** (no `agent review` / `codedagent review`) | No `Data.Grade` to read. Report the grade as **G_jud alone**, explicitly flagged: "G_det unavailable — review CLI not installed; grade reflects judgment only." Do not fabricate a deterministic grade by counting `agent validate` output. |
| **`uip agent validate` (Step 2) reports a blocking Error** not reflected in `Data.Grade` | A project that fails validation is not deployable — floor the final grade at **F** regardless of `Data.Grade`, and cite the validate Error as the binding constraint. |
| **No PDD available** | Business-logic alignment is ungraded. Compute the grade from technical quality only and add: "Grade reflects technical quality; business-logic alignment unverified (no PDD)." |
| **No eval set present** | Governance/Maintainability scores lose their eval-coverage signal — score the remaining evidence and note the eval gap rather than forcing a low score. |

## Alignment with the review CLI's `Data.Grade`

Because **G_det = `Data.Grade`** and the final grade is `min(G_det, G_jud)`:

- The skill grade **equals** `Data.Grade` when G_jud ≥ `Data.Grade` (judgment/design does not drag it down).
- The skill grade is **lower** than `Data.Grade` when G_jud is worse (weak prompt/tool design, a judgment Critical) — the skill adds the judgment dimension the CLI does not assess.
- The skill grade is **never higher** than `Data.Grade` (min only lowers).
- Report both, and state the gap in one line when they differ: "CLI Data.Grade A (deterministic checks); skill grade C — G_jud gated by thin prompt/tool design (arch avg 3.2)."

## Determinism contract

- **G_det is reproducible because it is the CLI's deterministic grade** — same agent, same `Data.Grade`, every run. The skill does not recompute it.
- **G_jud is reproducible given the principle scores** — reason from the same evidence (architecture-assessment-guide.md §4 criteria + the judgment catalog) in the same order so the scores, and therefore the grade, are stable run-to-run.
- The grade is **derived, never asserted.** Every grade must trace to `Data.Grade` (G_det), the G_jud average, and the `min()` binding constraint. A grade with no shown derivation is invalid.
- Do not introduce grade values outside `A` / `B` / `C` / `D` / `F`. No `+`/`-` modifiers, no `A*`, no numeric-only grade.

## Worked examples

**Example 1 — clean CLI grade, average design.**
- G_det = `Data.Grade` = **B** (read from `uip codedagent review`).
- G_jud: arch avg = (Modularity 4 + Resilience 4 + Maintainability 4 + Security 4 + Governance 3) / 5 = 3.8 (Scalability N/A) → **B**. No judgment Critical.
- Final = min(B, B) = **B — Good.** Binding: both.

**Example 2 — strong CLI grade, but thin prompt and no error handling.**
- G_det = `Data.Grade` = **A**.
- G_jud: arch avg = (Modularity 2 + Resilience 2 + Maintainability 2 + Security 3 + Governance 2) / 5 = 2.2 → **D**.
- Final = min(A, D) = **D.** Binding: G_jud — prompt/tool/error-handling quality (arch avg 2.2). A clean CLI grade does not rescue a weak design.

**Example 3 — strong design, but a tool description leaks a secret into args.**
- G_det = `Data.Grade` = **A** (the CLI's regex did not catch this semantic leak).
- G_jud: arch avg 4.3 → **B**, but a judgment Critical with secret-leak (data-integrity) impact → cap at **F**.
- Final = min(A, F) = **F.** Binding: G_jud security cap — a secret-leak Critical blocks deployment regardless of design.

**Example 4 — CLI grade diverges from skill grade.**
- G_det = `Data.Grade` = **A** (deterministic checks pass).
- G_jud: arch avg over applicable principles (Scalability excluded) = (Modularity 3 + Resilience 3 + Maintainability 3 + Security 4 + Governance 3) / 5 = 3.2 → **C**. One judgment Warning on prompt quality (no cap).
- Final = min(A, C) = **C.** Report: "CLI Data.Grade A (deterministic); skill grade C — G_jud gated by thin prompt/tool design (arch avg 3.2). Scalability excluded (N/A for low-code agent)."

## Anti-patterns

1. **Do not recompute G_det from finding counts.** Read `Data.Grade` from the review CLI. Recomputing risks disagreeing with the CLI's own grade.
2. **Do not grade non-agent projects with this rubric.** It is agent-scoped (phase 1). RPA, flows, and coded apps get a grade when their rubric is authored.
3. **Do not let a deterministic blocker average away.** This is a hard gate (`min`), not a weighted blend — a security/data-integrity judgment Critical forces F regardless of `Data.Grade`.
4. **Do not double-count a finding.** CLI findings already shaped `Data.Grade` (G_det); only judgment findings feed G_jud.
5. **Do not invent `+`/`-` or numeric grades.** Five letters only: A / B / C / D / F.
6. **Do not average per-agent grades** for the overall solution grade — take the worst.
7. **Do not restate the CLI's `Data.Grade` as the skill grade.** They differ whenever G_jud is lower; report both.
