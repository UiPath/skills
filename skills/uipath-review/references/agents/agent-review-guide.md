# Agent Review Workflow

Steps for reviewing an agent project: low-code (`agent.json`) or coded (`main.py` plus framework config or `uipath.json`). Enter from SKILL.md once Step 1 classifies the project. Step 0 (discovery, PDD, scope), Step 1, Steps 3b–3c, Step 4, and the Step 5 report skeleton are shared and stay in SKILL.md; step numbers here match SKILL.md. In a mixed solution, apply this guide to each agent project and keep one report.

> **Important:** a user's read-only or "do not modify the project" instruction covers manual edits only. It never covers `uip agent refresh` (Step 2) or `uip agent review-history add` (Step 6): the CLI owns the files they write. Run both even when the user asked for a read-only review; never move the project to a copy to avoid them.

## Critical Rules

1. Every agent requires `uip agent review` or `uip codedagent review` first, followed by the applicable judgment catalog, including when review began before this skill loaded; merge prior findings only after both passes.
2. Review-CLI findings are authoritative. Preserve `RuleId`, `Severity`, `Description`, `File`, and `SuggestedFix` verbatim. Format `Recommendation` as `<File>: <Description>. <SuggestedFix>`. Judgment findings use the same format. Map `error` to Critical, `warning` to Warning, and `info` to Info; `judgment` defaults to Warning and may change only with reasoning in the finding description.
3. Never invent `rule_id` values. Each cited ID must occur verbatim in a loaded `agents-*-rules.md` catalog or review-CLI JSON. Verify every ID before reporting. A real Critical issue covered by neither source is reported without a `rule_id`; unrule'd Warnings and Infos are dropped.
4. Grade agent projects only with `A`, `B`, `C`, `D`, or `F`, with no `+`/`-`, per agent and overall: `min(G_det, G_jud)`. Read `G_det` from review CLI `Data.Grade`; do not recompute it. Compute `G_jud` from judgment findings only. Show the binding constraint for every grade; low-code reports omit the printed derivation as required by the rubric. A security or data-integrity judgment Critical forces F. The skill grade cannot exceed `Data.Grade`; report both. Do not grade RPA, flows, or coded apps. See [agent-grading-rubric.md](agent-grading-rubric.md).
5. `uip agent refresh` owns `.agent-builder/`, `.local/build/`, and, for low-code agents, regenerated root `entry-points.json` from `agent.json`. Do not open these contents. Exclude them from classification, authored-file selection, structural metrics, and manual checks. Report a defect only if refresh fails to fix them. Read low-code schemas from `agent.json` `.inputSchema` and `.outputSchema`.
6. The only writes are `uip agent refresh` (Step 2) and `uip agent review-history add` (Step 6); both write CLI-owned files. Everything else stays read-only per SKILL.md Critical Rule 1.

## Step 2 — Validate

| Type | Command |
|---|---|
| Low-Code | `uip agent refresh "<PROJECT_DIR>" --output json`; then `uip agent validate "<PROJECT_DIR>" --output json` |
| Coded | No validate verb; the Step 2.5 `uip codedagent review` pass is the first CLI check |

Record counts in the Automated Validation Results table (SKILL.md Step 2d).

## Step 2.5 — Run the Review CLI, Then Apply the Judgment Catalog

Apply to every encountered agent, including late-invoked reviews.

### 2.5a. Deterministic CLI pass

Run once and capture JSON:

| Type | Command |
|---|---|
| Low-Code | `uip agent review "<PROJECT_DIR>" --output json` |
| Coded | `uip codedagent review "<PROJECT_DIR>" --output json` |

Parse `Data.Issues[]` objects `{RuleId, Category, Severity, Description, File, SuggestedFix}` and carry them verbatim. Guardrail configuration validity is CLI-only: run the review CLI or `--checks guardrails` when appropriate, including every emitted `GUARDRAIL_*` finding verbatim; do not eyeball or re-flag CLI guardrail findings.

### 2.5b. Judgment pass

Load each applicable catalog fully and apply every rule's `detection_method` to its named source material, including prompts, tools, eval datapoints, and schemas. Track intended rules that cannot be applied.

| Signal | Catalog |
|---|---|
| `agent.json.type == lowCode` | `agents-lowcode-rules.md` |
| Python coded-agent or `agent.json.type == coded` | `agents-coded-rules.md` |
| `pyproject.toml` + `main.py` + `uipath.json[functions]` without framework config | coded catalog |
| `package.json` + `uipath.json[functions]` (no `pyproject.toml`) — Coded Function (JS/TS) | phase 2; no agent catalog |
| RPA, Flow, Coded App | phase 2; no agent catalog |

For guardrails, running the guardrail workflow is **mandatory** whenever `guardrails[]` is non-empty or the use case calls for guardrails — do not eyeball `agent.json`:

- Low-code: **open [guardrails-review.md](guardrails/guardrails-review.md) and follow its Step 0 — you MUST run `uip agent guardrails catalog --output json` (30-min cache) and the never-cached tenant `uip agent guardrails list`** before auditing, then apply Audit Mode and Recommend Mode. Emit `LC_GUARDRAIL_ACTION_INEFFECTIVE`, `LC_GUARDRAIL_MISAPPLIED`, and `LC_GUARDRAIL_RECOMMENDED` as applicable.
- Coded: **open [coded-guardrails-review.md](guardrails/coded-guardrails-review.md) and follow it** when middleware/decorators are wired or the use case calls for guardrails. Public Python SDK docs may be fetched only when a finding must name classes not visible in source. Emit `CODED_GUARDRAIL_ACTION_INEFFECTIVE`, `CODED_GUARDRAIL_MISAPPLIED`, and `CODED_GUARDRAIL_RECOMMENDED`; do not duplicate CLI IDs `CODED_GUARDRAIL_WRONG_IMPORT`, `CODED_GUARDRAIL_TOOL_SCOPE_NO_TOOLS`, or `CODED_GUARDRAIL_INVALID_CONTRACT`.
- If the guardrail catalog is unavailable, put Audit-Mode rules in Rules Skipped and retain source-only Recommend Mode detection.

Before merging, verify every `rule_id` against a loaded catalog or CLI JSON. Remove absent IDs and retain only a Critical observation; drop unrule'd Warnings and Infos. Merge one row per finding into the Step 5 severity tables using `C-D-`, `W-D-`, or `I-D-` prefixes as described in [rule-format.md](../rule-format.md).

## Step 3 — Manual Quality Review

Unit of Work (SKILL.md Step 3a): the declared unit is `agent.json.inputSchema` for low-code and the `Input` Pydantic `BaseModel` in `main.py` for coded; derive the execution unit from `for`/`while` loops and external I/O. PDD alignment and the technical review follow SKILL.md Steps 3b–3c, with the judgment catalog as the checklist and only authored files in scope.

## Step 4 — Evaluate Optimization

As SKILL.md Step 4. Architecture-principle scores inform this step and never feed the grade.

## Step 4.5 — Compute Agent Grade

Agents only:

```text
Final grade = min(G_det, G_jud)
```

`G_det` is the letter in CLI `Data.Grade`; never recompute it from issue counts. For judgment findings only, calculate `100 − (15 × Criticals) − (4 × Warnings) − (1 × Infos)`, floored at 0; map `85–100 A`, `65–84 B`, `45–64 C`, `25–44 D`, `0–24 F`. Any unmitigated judgment Critical caps at D; a security/data-integrity judgment Critical forces F. Architecture-principle scores do not affect the grade. For multiple agents use the worst grade, never an average. Show the binding constraint, for example `B — gated by G_det = CLI Data.Grade B; judgment clean (G_jud A)`. Use [agent-grading-rubric.md](agent-grading-rubric.md) for omissions, edge cases, no-PDD/CLI/no-eval handling, and examples.

## Step 5 — Report Additions

Produce the report per SKILL.md Step 5 and add:

1. `### Summary` bullet after Overall Quality, exact form `- **Agent Grade:** <A–F> — <verdict>` — letter only, no `+`/`-`; keep any commentary in a later clause. A/B maps Overall Quality to Good, C/D to Needs Improvement, F to Critical Issues.
2. `### Per-Project Summary` Grade column: the per-agent grade; `—` for non-agent projects.
3. `**Final grade: <A–F>**` on its own line as the **last line** of the report (nothing after it); the letter **must match** the Summary Agent Grade.

Low-code reports omit the sections listed in [agent-grading-rubric.md § Low-code agent reports](agent-grading-rubric.md#low-code-agent-reports--omit-these-sections).

## Step 6 — Record the Agent Grade

Low-code agent projects only, after the report. For each low-code agent project, persist its per-agent final grade (Step 4.5) into the project's `review-history.json`:

```bash
uip agent review-history add <GRADE> "<PROJECT_DIR>" --errors <CRITICAL_COUNT> --warnings <WARNING_COUNT> --output json
```

The CLI owns `review-history.json`: never create, edit, or review the file; exclude it from the authored-file set. If the command fails, state that the grade was not recorded and stop — recording never changes the review outcome.
