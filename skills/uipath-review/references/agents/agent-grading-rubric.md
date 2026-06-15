# Agent Review — Letter Grade (A–F)

How the review computes the letter grade for **agent projects** (low-code `agent.json` and coded `main.py`). Run this in **Step 4.5**, after agent validation (Step 2), the review CLI + judgment catalog (Step 2.5), manual review (Step 3), and optimization + architecture scoring (Step 4) — the grade is a function of those outputs, never a fresh judgment.

> Scope: agents only, matching the skill's phase-1 model (the Step 2.5 judgment catalog is agent-only today; RPA, flows, and coded apps are future phases). Do **not** grade non-agent projects with this rubric. When a solution mixes agents with other types, grade the agent projects and leave the others ungraded (note "grading: agents only, phase 1").

The grade has two sub-grades, computed independently, then gated:

```
Final grade = min(G_det, G_jud)
```

- **G_det** — deterministic sub-grade. Driven only by objective, byte-reproducible findings: `uip agent validate` (Step 2) and `uip agent review` / `uip codedagent review` (Step 2.5a). Two runs over the same agent produce the same G_det.
- **G_jud** — non-deterministic sub-grade. Driven by judgment: the agent judgment catalog ([agents-common-rules.md](agents-common-rules.md) + the format file) read in Step 2.5b, the manual agent checklist ([agent-review-checklist.md](agent-review-checklist.md)) in Step 3, and the architecture-principle scores (1–5) from [architecture-assessment-guide.md §4](../architecture-assessment-guide.md).

`min()` means an agent cannot earn an A on a clean `agent validate` if its prompt, tools, and error handling are weak (G_jud gates it down), and cannot earn an A on strong design if the review CLI reports an error (G_det gates it down). The grade is bounded by the weaker dimension.

## Classify every finding by source first

Each Critical / Warning / Info finding feeds exactly one sub-grade — never both. This prevents double-counting.

| Finding source | Feeds |
|---|---|
| Step 2 `uip agent validate` (`V-E` / `V-W` / `V-I`) | **G_det** |
| Step 2.5a review CLI (`uip agent review` / `uip codedagent review` `Data.Issues[]`) | **G_det** |
| Step 2.5b judgment catalog (`*-D-*` findings — `judgment`-form catalog rows) | **G_jud** |
| Step 3 manual agent-checklist findings (no `rule_id`, or PDD-alignment findings) | **G_jud** |
| Architecture principle scores (1–5) | **G_jud** |

> A Critical the review CLI caught (e.g. a missing entry point) is deterministic → G_det. A Critical only reasoning caught (e.g. a system prompt that leaks credentials into tool calls) is judgment → G_jud. Both still appear in the report's findings; they differ only in which sub-grade they bind.

## G_det — deterministic sub-grade

Count only deterministic findings (the two G_det rows above).

| Condition | G_det |
|---|---|
| 0 Critical AND `agent validate` clean AND 0–1 deterministic Warnings | **A** |
| 0 Critical AND 2–3 deterministic Warnings | **B** |
| 0 Critical AND 4–7 deterministic Warnings | **C** |
| Exactly 1 deterministic Critical with a clear non-security fix, OR 8+ deterministic Warnings | **D** |
| ≥2 deterministic Criticals, OR any security / data-integrity Critical, OR `agent validate` fails | **F** |

Deterministic Info-level findings do not move the band.

**What counts as a deterministic Critical:** an `agent validate` Error, a review-CLI issue with `Severity: error`, a missing required file the CLI reports (e.g. `agent.json`, framework config, `pyproject.toml`), a missing framework dependency, or a hardcoded-secret the CLI's regex flags.

## G_jud — non-deterministic sub-grade

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

## Final grade and rationale

`Final = min(G_det, G_jud)`. Always report the **binding constraint** in one line so the grade is auditable:

```
Agent Grade: B — gated by G_det (3 deterministic Warnings). Design is strong (G_jud A, arch avg 4.5).
```

Map the letter to the existing quality verdict so the headline reads naturally and never contradicts the count-based verdict:

| Grade | Verdict label | Meaning |
|---|---|---|
| **A** | Good | Excellent — production-ready, ship it |
| **B** | Good | Good — minor fixes before production |
| **C** | Needs Improvement | Acceptable — needs work before production |
| **D** | Needs Improvement | Significant issues — not production-ready |
| **F** | Critical Issues | Failing — not deployable |

## Per-agent vs overall

- **Per-agent grade:** compute G_det and G_jud for the agent; grade = `min`. Report in the Per-Project Summary table (Step 5) for each agent row; leave non-agent rows ungraded (`—`).
- **Single-agent review:** the overall Agent Grade IS the agent's grade.
- **Solution with multiple agents:** the overall Agent Grade = the **worst** per-agent grade. A solution is only as deployable as its weakest agent — do not average grades. Non-agent projects do not contribute a grade (phase 1).

## Edge cases

| Situation | Handling |
|---|---|
| **No PDD available** | Business-logic alignment is ungraded. Compute the grade from technical quality only and add: "Grade reflects technical quality; business-logic alignment unverified (no PDD)." |
| **Review CLI unavailable** (no `agent review` / `codedagent review`) | The CLI's deterministic findings are missing. Compute G_det from `uip agent validate` only; note the gap in "Rules Skipped". Do not invent findings to fill it. |
| **No eval set present** | Governance/Maintainability scores lose their eval-coverage signal — score the remaining evidence and note the eval gap rather than forcing a low score. |

## Alignment with the review CLI's `Data.Grade`

`uip agent review` / `uip codedagent review` return `Data.Verdict`, `Data.Score`, and `Data.Grade`. These grade the CLI's deterministic checks only.

- Report the CLI's `Data.Grade` alongside the skill grade when present.
- The skill grade may be **lower** than `Data.Grade` (the skill adds G_jud — architecture + judgment — which the CLI does not assess). It should rarely be higher; if it is, re-check G_det classification.
- If they diverge, state why in one line: "CLI grade A (deterministic checks); skill grade C — G_jud gated by thin prompt/tool design (arch avg 3.2)."
- Never overwrite or restate the CLI's `Data.Grade` as the skill grade. Present both.

## Determinism contract

- **G_det is fully reproducible** — same agent, same G_det, every run.
- **G_jud is reproducible given the principle scores** — reason from the same evidence (architecture-assessment-guide.md §4 criteria + the judgment catalog) in the same order so the scores, and therefore the grade, are stable run-to-run.
- The grade is **derived, never asserted.** Every grade must trace to its G_det band, its G_jud average, and the `min()` binding constraint. A grade with no shown derivation is invalid.
- Do not introduce grade values outside `A` / `B` / `C` / `D` / `F`. No `+`/`-` modifiers, no `A*`, no numeric-only grade.

## Worked examples

**Example 1 — coded agent, clean CLI, average design.**
- G_det: `agent validate` clean, `codedagent review` reports 0 errors + 3 Warnings → **B**.
- G_jud: arch avg = (Modularity 4 + Resilience 4 + Maintainability 4 + Security 4 + Governance 3) / 5 = 3.8 (Scalability N/A) → **B**. No judgment Critical.
- Final = min(B, B) = **B — Good (minor fixes).** Binding: both.

**Example 2 — validates clean, but thin prompt and no error handling.**
- G_det: 0 Critical, 1 Warning from the review CLI → **A**.
- G_jud: arch avg = (Modularity 2 + Resilience 2 + Maintainability 2 + Security 3 + Governance 2) / 5 = 2.2 → **D**.
- Final = min(A, D) = **D.** Binding: G_jud — prompt/tool/error-handling quality (arch avg 2.2). The clean validation does not rescue a weak design.

**Example 3 — strong design, but a tool description leaks a secret into args.**
- G_det: 0 Critical from the CLI → **A**.
- G_jud: arch avg 4.3 → **B**, but a judgment Critical with secret-leak (data-integrity) impact → cap at **F**.
- Final = min(A, F) = **F.** Binding: G_jud security cap — a secret-leak Critical blocks deployment regardless of design.

**Example 4 — low-code agent, CLI grade present, diverges from skill grade.**
- CLI `Data.Grade` = A (deterministic checks pass).
- G_det: 0 Critical, 2 deterministic Warnings from `uip agent review` → **A**.
- G_jud: arch avg over applicable principles (Scalability excluded) = (Modularity 3 + Resilience 3 + Maintainability 3 + Security 4 + Governance 3) / 5 = 3.2 → **C**. One judgment Warning on prompt quality (no cap).
- Final = min(A, C) = **C.** Report: "CLI grade A (deterministic); skill grade C — G_jud gated by thin prompt/tool design (arch avg 3.2). Scalability excluded (N/A for low-code agent)."

## Anti-patterns

1. **Do not grade non-agent projects with this rubric.** It is agent-scoped (phase 1). RPA, flows, and coded apps get a grade when their rubric is authored.
2. **Do not assign a grade by feel.** Compute G_det and G_jud from the rubric tables, then `min()`. Show the derivation.
3. **Do not let a deterministic blocker average away.** This is a hard gate (`min`), not a weighted blend — a security/data-integrity Critical forces F regardless of design.
4. **Do not double-count a finding** in both sub-grades. Classify by source (table above) — it feeds exactly one.
5. **Do not invent `+`/`-` or numeric grades.** Five letters only: A / B / C / D / F.
6. **Do not average per-agent grades** for the overall solution grade — take the worst.
7. **Do not restate the CLI's `Data.Grade` as the skill grade.** They measure different things; report both.
