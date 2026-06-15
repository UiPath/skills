# Grading Rubric — Letter Grade (A–F)

How the review computes the single letter grade reported in Step 5. Run this in **Step 4.5**, after validation (Step 2), rule findings (Step 2.5), manual review (Step 3), and optimization + architecture scoring (Step 4) are complete — the grade is a function of those outputs, never a fresh judgment.

The grade has two sub-grades, computed independently, then gated:

```
Final grade = min(G_det, G_jud)
```

- **G_det** — deterministic sub-grade. Driven only by objective, byte-reproducible findings: `uip ... validate` / `build` / `analyze` (Step 2) and `uip agent review` / `uip codedagent review` (Step 2.5a). Two runs over the same project produce the same G_det.
- **G_jud** — non-deterministic sub-grade. Driven by judgment: the six architecture-principle scores (1–5) from [architecture-assessment-guide.md §4](architecture-assessment-guide.md) plus judgment-catalog (Step 2.5b) and manual-checklist (Step 3) findings.

`min()` means a project cannot earn an A on clean validation if its design is monolithic and insecure (G_jud gates it down), and cannot earn an A on elegant design if it fails to build (G_det gates it down). The grade is bounded by the weaker dimension.

## Classify every finding by source first

Each Critical / Warning / Info finding feeds exactly one sub-grade — never both. This prevents double-counting.

| Finding source | Feeds |
|---|---|
| Step 2 validation / build / Workflow Analyzer (`V-E` / `V-W` / `V-I`) | **G_det** |
| Step 2.5a review CLI (`uip agent review` / `uip codedagent review` `Data.Issues[]`) | **G_det** |
| Step 2.5b judgment catalog (`*-D-*` findings whose `rule_id` is a `judgment`-form catalog row) | **G_jud** |
| Step 3 manual checklist findings (no `rule_id`, or PDD-alignment findings) | **G_jud** |
| Architecture principle scores (1–5) | **G_jud** |

> A Critical the CLI caught (e.g. `ST-SEC-007` SecureString) is deterministic → G_det. A Critical only manual reasoning caught (e.g. "credentials read from a plaintext config file the analyzer didn't flag") is judgment → G_jud. Both still appear in the report's Critical Findings section; they differ only in which sub-grade they bind.

## G_det — deterministic sub-grade

Count only deterministic findings (the two G_det rows above).

| Condition | G_det |
|---|---|
| 0 Critical AND project builds + validates clean AND 0–1 deterministic Warnings | **A** |
| 0 Critical AND 2–3 deterministic Warnings | **B** |
| 0 Critical AND 4–7 deterministic Warnings | **C** |
| Exactly 1 deterministic Critical with a clear non-security fix, OR 8+ deterministic Warnings | **D** |
| ≥2 deterministic Criticals, OR any security / data-integrity Critical, OR the project fails to build or validate | **F** |

Deterministic Info-level findings do not move the band.

**What counts as a deterministic Critical:** a `validate` Error, a failed `build`, a Workflow Analyzer Error-level violation (e.g. `ST-SEC-007`), a review-CLI issue with `Severity: error`, a missing required file the CLI reports, a circular dependency, or a hardcoded-secret the analyzer/CLI flags.

## G_jud — non-deterministic sub-grade

**Step 1 — Architecture-average base.** Average the six principle scores (1–5) from [architecture-assessment-guide.md §4](architecture-assessment-guide.md): Modularity, Scalability, Resilience, Maintainability, Security, Governance. If a principle genuinely does not apply to the project type (e.g. queue-style Scalability for a one-shot utility, or RPA-only resilience for a low-code agent), exclude it and average the applicable ones — **state which were excluded** in the report.

| Architecture average | base G_jud |
|---|---|
| 4.5 – 5.0 | **A** |
| 3.5 – 4.49 | **B** |
| 2.5 – 3.49 | **C** |
| 1.5 – 2.49 | **D** |
| 1.0 – 1.49 | **F** |

**Step 2 — Judgment-finding cap.** The principle scores already absorb most judgment findings (a "no error handling" finding is why Resilience scored 2). Apply only one additional cap, to catch a blocking design flaw the averaged scores understate:

- Any **unmitigated judgment Critical** caps G_jud at **D**.
- A judgment Critical with **security or data-integrity** impact caps G_jud at **F**.

Do not apply further per-Warning deductions — that double-counts against the principle scores.

## Final grade and rationale

`Final = min(G_det, G_jud)`. Always report the **binding constraint** in one line so the grade is auditable:

```
Overall Grade: B — gated by G_det (3 deterministic Warnings). Design is strong (G_jud A, arch avg 4.5).
```

Map the letter to the existing quality verdict so the headline reads naturally and never contradicts the count-based verdict:

| Grade | Verdict label | Meaning |
|---|---|---|
| **A** | Good | Excellent — production-ready, ship it |
| **B** | Good | Good — minor fixes before production |
| **C** | Needs Improvement | Acceptable — needs work before production |
| **D** | Needs Improvement | Significant issues — not production-ready |
| **F** | Critical Issues | Failing — not deployable |

## Per-project vs overall grade

- **Per-project grade:** compute G_det and G_jud for the project; grade = `min`. Report in the Per-Project Summary table (Step 5).
- **Single-project review:** the overall grade IS the project grade.
- **Solution / multi-project review:** the overall grade = `min(` worst per-project grade, a solution-level G_det `)`. Solution-level G_det folds in cross-project deterministic findings (circular dependency, version mismatch, missing `.uipx`/config). A solution is only as deployable as its weakest executable — do not average project grades.

## Edge cases

| Situation | Handling |
|---|---|
| **Windows-Legacy project** — `uip rpa validate`/`build` target Modern projects | G_det cannot be computed from the Modern CLI. Compute the grade from G_jud (architecture scores + manual findings) only; note "G_det not computed — Legacy validation routes to `uipath-rpa` (Legacy mode)". Do **not** grade F merely because the Modern CLI did not run. |
| **No PDD available** | Business-logic alignment is ungraded. Compute the grade from technical quality only and add: "Grade reflects technical quality; business-logic alignment unverified (no PDD)." |
| **Review CLI unavailable** (no `agent review` / `codedagent review`) | The CLI's deterministic findings are missing. Compute G_det from Step 2 validation/build only; note the gap in "Rules Skipped". Do not invent findings to fill it. |
| **Project type with no architecture scoring yet** | If you cannot responsibly score the six principles, report G_det only and state that G_jud was not computed; the grade is then G_det with that caveat. |

## Alignment with the review CLI's `Data.Grade`

`uip agent review` / `uip codedagent review` return `Data.Verdict`, `Data.Score`, and `Data.Grade` for **agent** projects. These grade the CLI's deterministic checks only.

- Report the CLI's `Data.Grade` alongside the skill grade when present.
- The skill grade may be **lower** than `Data.Grade` (the skill adds G_jud — architecture + judgment — which the CLI does not assess). It should rarely be higher; if it is, re-check G_det classification.
- If they diverge, state why in one line: "CLI grade A (deterministic checks); skill grade C — G_jud gated by Resilience 2 / Maintainability 2."
- Never overwrite or restate the CLI's `Data.Grade` as the skill grade. Present both.

## Determinism contract

- **G_det is fully reproducible** — same project, same G_det, every run.
- **G_jud is reproducible given the six principle scores** — reason from the same evidence (architecture-assessment-guide.md §4 criteria) in the same order so the scores, and therefore the grade, are stable run-to-run.
- The grade is **derived, never asserted.** Every grade in a report must trace to its G_det band, its G_jud average, and the `min()` binding constraint. A grade with no shown derivation is invalid.
- Do not introduce grade values outside `A` / `B` / `C` / `D` / `F`. No `+`/`-` modifiers, no `A*`, no numeric-only grade.

## Worked examples

**Example 1 — clean RPA project, average design.**
- G_det: 0 Critical, builds clean, 3 deterministic Warnings → **B**.
- G_jud: arch avg = (Modularity 4 + Scalability 3 + Resilience 4 + Maintainability 4 + Security 4 + Governance 3) / 6 = 3.67 → **B**. No judgment Critical.
- Final = min(B, B) = **B — Good (minor fixes).** Binding: both.

**Example 2 — validates clean, but monolithic and insecure design.**
- G_det: 0 Critical, 1 deterministic Warning → **A**.
- G_jud: arch avg = (Modularity 2 + Scalability 2 + Resilience 2 + Maintainability 2 + Security 2 + Governance 2) / 6 = 2.0 → **D**.
- Final = min(A, D) = **D.** Binding: G_jud — design quality (arch avg 2.0). The clean validation does not rescue a poor design.

**Example 3 — strong design, one hardcoded credential the analyzer flagged.**
- G_det: 1 deterministic security Critical (`ST-SEC-007`) → **F** (security Critical).
- G_jud: arch avg 4.3 → **B**.
- Final = min(F, B) = **F.** Binding: G_det — security Critical blocks deployment regardless of design.

**Example 4 — low-code agent, CLI grade present.**
- CLI `Data.Grade` = A (deterministic checks pass).
- G_det: 0 Critical, 2 deterministic Warnings from the review CLI → **A**.
- G_jud: arch avg over applicable principles (Scalability excluded as N/A) = (Modularity 3 + Resilience 3 + Maintainability 3 + Security 4 + Governance 3) / 5 = 3.2 → **C**. One judgment Warning on prompt quality (no cap).
- Final = min(A, C) = **C.** Report: "CLI grade A (deterministic); skill grade C — G_jud gated by thin prompt/tool design (arch avg 3.2). Scalability excluded (N/A for low-code agent)."

## Anti-patterns

1. **Do not assign a grade by feel.** Compute G_det and G_jud from the rubric tables, then `min()`. Show the derivation.
2. **Do not let a deterministic blocker average away.** This is a hard gate (`min`), not a weighted blend — a security/data-integrity Critical forces F regardless of design.
3. **Do not double-count a finding** in both sub-grades. Classify by source (table above) — it feeds exactly one.
4. **Do not invent `+`/`-` or numeric grades.** Five letters only: A / B / C / D / F.
5. **Do not average per-project grades** for the overall solution grade — take the worst, gated by solution-level G_det.
6. **Do not grade F for a Legacy project just because the Modern CLI did not run.** Compute from G_jud and note the routing.
7. **Do not restate the CLI's `Data.Grade` as the skill grade.** They measure different things; report both.
