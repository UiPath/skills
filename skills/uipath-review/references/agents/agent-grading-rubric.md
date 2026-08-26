# Agent Review — Letter Grade (A–F)

How the review computes the letter grade for **agent projects** (low-code `agent.json` and coded `main.py`). Run this in **Step 4.5**, after agent validation (Step 2), the review CLI + judgment catalog (Step 2.5), and manual review (Step 3) — the grade is a function of those outputs, never a fresh judgment.

> Scope: agents only, matching the skill's phase-1 model (the Step 2.5 judgment catalog is agent-only today; RPA, flows, and coded apps are future phases). Do **not** grade non-agent projects with this rubric. When a solution mixes agents with other types, grade the agent projects and leave the others ungraded (note "grading: agents only, phase 1").

The grade has two sub-grades, computed independently, then gated:

```
Final grade = min(G_det, G_jud)
```

- **G_det** — deterministic sub-grade. **Read it directly from the review CLI** — do not recompute it. `uip agent review` / `uip codedagent review` returns `Data.Grade`, the grade it assigns to its own deterministic checks. That letter **is** G_det.
- **G_jud** — non-deterministic sub-grade. Driven by the judgment findings: the format-specific agent judgment catalog read in Step 2.5b and the manual review in Step 3.

`min()` means an agent cannot earn an A from a clean CLI grade if the judgment findings are heavy (G_jud gates it down), and cannot earn an A from clean judgment if the CLI's deterministic grade is poor (G_det gates it down). The grade is bounded by the weaker dimension. Because `min` only ever lowers the CLI grade, the **skill grade is always ≤ `Data.Grade`**.

## G_det — read it from the review CLI, never recompute

`uip agent review` / `uip codedagent review` runs the deterministic checks its registry ships (structural/schema gates, placeholder cross-refs, eval-set structure, guardrail configuration validity) and grades them. Read the grade from the JSON response and use it verbatim:

```
G_det = <response>.Data.Grade        # e.g. "B"
```

The response also carries `Data.Verdict` (PASS/FAIL) and `Data.Score`; `Data.Grade` is the letter to use. It ships `+`/`-` modifiers (`A+` … `F`) — collapse to the base letter (`C+` → `C`) so both sub-grades share the five-letter scale.

**Do not tally `Data.Issues[]` and re-derive a grade.** Recomputing duplicates work the CLI already did and risks drifting from the CLI's own grade — the exact inconsistency this design avoids. The deterministic findings (`Data.Issues[]`) are still carried into the report verbatim (Step 2.5a), but the *grade* comes from `Data.Grade`, not from counting them.

If `Data.Grade` is missing or the CLI is unavailable, see [Edge cases](#edge-cases).

## G_jud — the judgment sub-grade you compute

This is the only sub-grade the agent computes, because no CLI can grade it reliably.

**Step 1 — Penalty score.** Count the judgment findings by severity and deduct from 100, then look the score up in the [grade chart](#grade-chart):

```
G_jud score = 100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos)      # floor 0
```

**Step 2 — Judgment-finding cap.** Two caps catch a blocking flaw the score understates:

- Any **unmitigated judgment Critical** caps G_jud at **D**.
- A judgment Critical with **security or data-integrity** impact (prompt-injection exposure, secret leak into tool args, no guardrail on a destructive tool) caps G_jud at **F**.

> Findings from the review CLI (`Data.Issues[]`) already shaped `Data.Grade` = G_det — do **not** also count them in G_jud. Only **judgment** findings (Step 2.5b catalog + Step 3 manual) feed G_jud. This keeps each finding in exactly one sub-grade.

The architecture-principle scores in [architecture-assessment-guide.md §4](../architecture-assessment-guide.md) inform the optimization review; they do **not** feed the grade.

## Grade chart

Score → letter, collapsed from the review CLI's own chart (`A+`/`A`/`A-` → `A`, and so on). Used for the G_jud lookup and for the `Data.Grade`-absent fallback below.

| Score | Grade |
|------:|-------|
| 85–100 | **A** |
| 65–84 | **B** |
| 45–64 | **C** |
| 25–44 | **D** |
| 0–24 | **F** |

## Final grade and rationale

`Final = min(G_det, G_jud)` where `G_det = Data.Grade`. Always report the **binding constraint** in one line so the grade is auditable (low-code omits it — see below):

```
Agent Grade: B — gated by G_det (CLI Data.Grade B). Judgment is clean (G_jud A, 91).
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

## Low-code agent reports — omit these sections

Low-code agent review (`agent.json`): omit entirely — no placeholder, no "not applicable" note.

| Section | Omit when |
|---|---|
| PDD Alignment | No PDD available |
| Per-Project Summary | Review scope is a single project, including a single project inside a solution |
| Grade derivation | Always — the `Agent Grade` line carries the letter and verdict label only: no binding constraint, sub-grades, or `Data.Grade` comparison |
| Optimization Notes | Always |

The `**Final grade: <A–F>**` last line still prints.

## Edge cases

| Situation | Handling |
|---|---|
| **`Data.Grade` absent** (older CLI returns only `Data.Verdict` / `Data.Score`) | Map what the CLI gives you: `Data.Verdict = FAIL` → G_det = F; otherwise look `Data.Score` up in the [grade chart](#grade-chart). Note the substitution in "Rules Skipped". |
| **Review CLI unavailable** (no `agent review` / `codedagent review`) | No `Data.Grade` to read. Report the grade as **G_jud alone**, explicitly flagged: "G_det unavailable — review CLI not installed; grade reflects judgment only." Do not fabricate a deterministic grade by counting `agent validate` output. |
| **`uip agent validate` (Step 2) reports a blocking Error** not reflected in `Data.Grade` | A project that fails validation is not deployable — floor the final grade at **F** regardless of `Data.Grade`, and cite the validate Error as the binding constraint. |
| **No PDD available** | Business-logic alignment is ungraded. Compute the grade from technical quality only and add: "Grade reflects technical quality; business-logic alignment unverified (no PDD)." |
| **No eval set present** | Raise the eval-coverage gap as one judgment finding — do not restate it as several findings to force the score down. |

## Alignment with the review CLI's `Data.Grade`

Because **G_det = `Data.Grade`** and the final grade is `min(G_det, G_jud)`:

- The skill grade **equals** `Data.Grade` when G_jud ≥ `Data.Grade` (judgment findings do not drag it down).
- The skill grade is **lower** than `Data.Grade` when G_jud is worse (heavy judgment findings, a judgment Critical) — the skill adds the judgment dimension the CLI does not assess.
- The skill grade is **never higher** than `Data.Grade` (min only lowers).
- Report both, and state the gap in one line when they differ: "CLI Data.Grade A (deterministic checks); skill grade C — G_jud 62 over 9 judgment Warnings, 2 Infos."

## Determinism contract

- **G_det is reproducible because it is the CLI's deterministic grade** — same agent, same `Data.Grade`, every run. The skill does not recompute it.
- **G_jud is reproducible given the judgment findings** — same findings at the same severities, same score, same letter.
- The grade is **derived, never asserted.** Every grade must trace to `Data.Grade` (G_det), the G_jud score, and the `min()` binding constraint. A grade with no shown derivation is invalid, except where the report omits derivation (low-code).
- Do not introduce skill grade values outside `A` / `B` / `C` / `D` / `F`. No `+`/`-` modifiers, no `A*`, no numeric-only grade.

## Worked examples

**Example 1 — clean CLI grade, few judgment findings.**
- G_det = `Data.Grade` = **B** (read from `uip codedagent review`).
- G_jud: 0 Criticals, 2 Warnings, 1 Info → 100 − 8 − 1 = 91 → **A**. No cap.
- Final = min(B, A) = **B — Good.** Binding: G_det.

**Example 2 — strong CLI grade, but many judgment findings.**
- G_det = `Data.Grade` = **A**.
- G_jud: 0 Criticals, 12 Warnings, 4 Infos → 100 − 48 − 4 = 48 → **C**.
- Final = min(A, C) = **C.** Binding: G_jud — 12 Warnings on prompt, tool, and error-handling quality. A clean CLI grade does not rescue them.

**Example 3 — few findings, but a tool description leaks a secret into args.**
- G_det = `Data.Grade` = **A** (the CLI's regex did not catch this semantic leak).
- G_jud: 1 Critical, 1 Warning → 100 − 15 − 4 = 81 → **B**, but the Critical carries secret-leak (data-integrity) impact → cap at **F**.
- Final = min(A, F) = **F.** Binding: G_jud security cap — a secret-leak Critical blocks deployment regardless of the score.

**Example 4 — CLI grade diverges from skill grade, `+` collapsed.**
- `Data.Grade` = `A-` → collapse → G_det = **A**.
- G_jud: 0 Criticals, 9 Warnings, 2 Infos → 100 − 36 − 2 = 62 → **C**.
- Final = min(A, C) = **C.** Report: "CLI Data.Grade A- (deterministic); skill grade C — G_jud 62 over 9 Warnings, 2 Infos."

## Anti-patterns

1. **Do not recompute G_det from finding counts.** Read `Data.Grade` from the review CLI. Recomputing risks disagreeing with the CLI's own grade.
2. **Do not grade non-agent projects with this rubric.** It is agent-scoped (phase 1). RPA, flows, and coded apps get a grade when their rubric is authored.
3. **Do not let a deterministic blocker average away.** This is a hard gate (`min`), not a weighted blend — a security/data-integrity judgment Critical forces F regardless of `Data.Grade`.
4. **Do not double-count a finding.** CLI findings already shaped `Data.Grade` (G_det); only judgment findings feed G_jud.
5. **Do not invent `+`/`-` or numeric grades.** Five letters only: A / B / C / D / F. Quoting the CLI's raw `Data.Grade` (`A-`) alongside it is fine.
6. **Do not average per-agent grades** for the overall solution grade — take the worst.
7. **Do not restate the CLI's `Data.Grade` as the skill grade.** They differ whenever G_jud is lower; report both.
8. **Do not feed architecture-principle scores into the grade.** They inform the optimization review only; G_jud is a judgment-finding count.
