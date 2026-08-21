# Agent Review — Letter Grade (A–F)

Compute the letter grade for agent projects (low-code `agent.json` and coded `main.py`) in **Step 4.5**, after agent validation (Step 2), the review CLI + judgment catalog (Step 2.5), and manual review (Step 3). Derive the grade from those outputs; never create a fresh judgment.

> Scope: agents only, matching the skill's phase-1 model (the Step 2.5 judgment catalog is agent-only today; RPA, flows, and coded apps are future phases). Do **not** grade non-agent projects with this rubric. For mixed solutions, grade agent projects and leave others ungraded (note "grading: agents only, phase 1").

## Grade model

Compute two independent sub-grades and use the weaker:

```text
Final grade = min(G_det, G_jud)
```

- **G_det:** Run `uip agent review` or `uip codedagent review`; read `<response>.Data.Grade`. Do not recompute it. Carry `Data.Issues[]` into the report verbatim in Step 2.5a, but do not count those findings in G_jud. The CLI covers its deterministic registry, including structural/schema gates, placeholder cross-refs, eval-set structure, and guardrail configuration validity.
- **G_jud:** Count only judgment findings from the format-specific agent judgment catalog in Step 2.5b and manual review in Step 3. Use the formula and caps below.

Collapse CLI `+`/`-` modifiers to the base letter (`C+` → `C`); use only `A` / `B` / `C` / `D` / `F` for both sub-grades. If `Data.Grade` is missing or the CLI is unavailable, apply [Edge cases](#edge-cases).

### G_jud

```text
G_jud score = 100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos)  # floor 0
```

Map the score using the [grade chart](#grade-chart), then apply these caps:

- Any **unmitigated judgment Critical** caps G_jud at **D**.
- A judgment Critical with **security or data-integrity** impact—such as prompt-injection exposure, a secret leak into tool args, or no guardrail on a destructive tool—caps G_jud at **F**.

Architecture-principle scores in [architecture-assessment-guide.md §4](../architecture-assessment-guide.md) inform optimization review only; they do not feed the grade.

## Grade chart

Collapse the review CLI's `A+`/`A`/`A-` and equivalent modifiers to the base letter:

| Score | Grade |
|------:|-------|
| 85–100 | **A** |
| 65–84 | **B** |
| 45–64 | **C** |
| 25–44 | **D** |
| 0–24 | **F** |

## Final grade and rationale

Compute `Final = min(G_det, G_jud)`. Report the binding constraint:

```text
Agent Grade: B — gated by G_det (CLI Data.Grade B). Judgment is clean (G_jud A, 91).
```

When G_jud is lower, report both and state the gap, for example: `CLI Data.Grade A (deterministic checks); skill grade C — G_jud 62 over 9 judgment Warnings, 2 Infos.`

Use this verdict mapping:

| Grade | Verdict label |
|---|---|
| **A** / **B** | Good |
| **C** / **D** | Needs Improvement |
| **F** | Critical Issues |

## Per-agent and overall grades

- **Per-agent:** Read `Data.Grade` as G_det, compute G_jud, and use `min`. Put the result in the Per-Project Summary table (Step 5) for each agent; use `—` for non-agent rows.
- **Single agent:** The overall Agent Grade is that agent's grade.
- **Multiple agents:** The overall Agent Grade is the worst per-agent grade; do not average. Non-agent projects do not contribute in phase 1.

## Low-code agent reports

For low-code `agent.json`, omit these sections entirely:

| Section | Omit when |
|---|---|
| PDD Alignment | No PDD available |
| Per-Project Summary | Review scope is a single project, including a single project inside a solution |
| Grade derivation | Always; the `Agent Grade` line carries only the letter and verdict label, with no binding constraint, sub-grades, or `Data.Grade` comparison |
| Optimization Notes | Always |

Still print: `**Final grade: <A–F>**`.

## Edge cases

| Situation | Handling |
|---|---|
| **`Data.Grade` absent** (older CLI returns only `Data.Verdict` / `Data.Score`) | Map `Data.Verdict = FAIL` to G_det = F; otherwise map `Data.Score` using the [grade chart](#grade-chart). Note the substitution in "Rules Skipped". |
| **Review CLI unavailable** (no `agent review` / `codedagent review`) | Report G_jud alone and explicitly state: "G_det unavailable — review CLI not installed; grade reflects judgment only." Do not fabricate G_det by counting `agent validate` output. |
| **`uip agent validate` (Step 2) reports a blocking Error** not reflected in `Data.Grade` | Run `uip agent validate` as required by Step 2. A validation failure is not deployable: floor the final grade at **F**, regardless of `Data.Grade`, and cite the validate Error as the binding constraint. |
| **No PDD available** | Do not grade business-logic alignment. Grade technical quality only and add: "Grade reflects technical quality; business-logic alignment unverified (no PDD)." |
| **No eval set present** | Raise the eval-coverage gap as one judgment finding; do not restate it as multiple findings to lower the score. |

## Determinism contract

- G_det is reproducible because it is the CLI's deterministic grade: the same agent yields the same `Data.Grade`.
- G_jud is reproducible from the judgment findings, severities, formula, and caps.
- Trace every grade to `Data.Grade` (G_det), the G_jud score, and the `min()` binding constraint, except where low-code reporting omits derivation.
- Use only `A` / `B` / `C` / `D` / `F`; never introduce `+`/`-`, `A*`, or numeric-only grades. Quoting the CLI's raw `Data.Grade` such as `A-` alongside the collapsed grade is permitted.

## Anti-patterns

1. Do not recompute G_det from finding counts; read `Data.Grade` from the review CLI.
2. Do not grade non-agent projects with this phase-1 rubric; RPA, flows, and coded apps require their own rubric.
3. Do not average away a deterministic blocker; `min` is a hard gate, and a security/data-integrity judgment Critical forces F regardless of `Data.Grade`.
4. Do not double-count findings: CLI findings shape G_det; judgment findings alone feed G_jud.
5. Do not invent `+`/`-` or numeric grades.
6. Do not average per-agent grades; use the worst.
7. Do not restate the CLI's `Data.Grade` as the skill grade when G_jud is lower; report both.
8. Do not feed architecture-principle scores into the grade; they inform optimization only.