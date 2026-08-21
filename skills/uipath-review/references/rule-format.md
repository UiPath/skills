# Rule Catalog — Row Format

Schema for every row in `agents-*-rules.md` judgment catalogs. The catalog is the contract: reason about each rule and emit findings with its `rule_id`, `severity`, and `suggested_fix`.

The catalog is **judgment-only**. Read source and reason about prompt quality, tool-selection ambiguity, framework fit, and semantic schema/eval mismatches. Put deterministic checks (file presence, schema walks, counts, regex, and run-artifact analysis) in the `uip agent review` / `uip codedagent review` CLI (SKILL.md Step 2.5a), which emits `RuleId`, `Severity`, `Category`, `Description`, `File`, and `SuggestedFix`.

## Row schema

Each catalog file has one H2 section per logical checker (for example, `## SchemaChecker` and `## ToolsChecker`) containing one table:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix |
```

| Column | Type | Source |
|---|---|---|
| `rule_id` | UPPER_SNAKE_CASE identifier in backticks | Stable contract; never rename. |
| `severity` | One of `error` / `warning` / `info` / `judgment` | Mapped at report time below. |
| `category` | `evals` / `schema` / `tools` / `guardrails` / `general` / `code` / `security` / `runtime` | Drives report grouping. |
| `trigger` | Short condition phrase | States what fires the rule. |
| `detection_method` | Judgment form below | States what evidence to read and how to reason. |
| `suggested_fix` | One imperative sentence | States the remediation. |

## Severity mapping (catalog → report)

| Catalog `severity` | Report band (from SKILL.md Step 5) | Finding ID prefix |
|---|---|---|
| `error` | Critical | `C-D-` |
| `warning` | Warning | `W-D-` |
| `info` | Info | `I-D-` |
| `judgment` | Warning by default; choose Critical / Warning / Info according to contextual severity and log the reasoning in the finding's `description` | `W-D-` (or `C-D-` / `I-D-` when escalated or de-escalated) |

The `-D-` infix marks rule-driven findings, versus `-V-` for Step 2 validation output and no infix for manual checklist findings. Review-CLI findings carry the CLI-emitted `RuleId` and use the same severity table.

## Detection method — the judgment form

Every catalog row's `detection_method` must use this form:

> **Judgment** — `Read <files>; assess whether <condition>; emit when <criteria>.` Read the relevant source material (system prompt, tool descriptions, eval datapoints, schema, or code), reason whether the rule fires, and log that reasoning in the finding's `description`.

Do not put deterministic forms (`Glob`, `Read+JSON walk`, `Grep`, `Bash`, count/threshold, or set-membership) in catalog rows. Put checks reliably performed by a single-file regex, count, or schema walk in the review CLI instead.

## Status field (optional 7th column)

A rule MAY add:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix | status |
```

Allowed `status` values:

- omitted / blank — active; apply the rule.
- `deferred` — document for traceability but do not apply. Record it in the report's "Rules Skipped" section with reason `deferred (status: deferred)`.

## The review CLI (deterministic findings)

Run the review command once per agent and capture JSON:

```bash
uip agent review "<PROJECT_DIR>" --output json        # low-code
uip codedagent review "<PROJECT_DIR>" --output json   # coded
```

Use `Data.Issues[]`. Carry its deterministic findings into the report verbatim; each has the same severity/category/description/file/fix shape as a catalog row. The catalog does not list these `RuleId`s; the CLI registry is their source of truth.

## Constants section

Judgment rows may reference thresholds inline as soft cues (for example, "a `<20-char` description is almost always too thin"), but reason about sufficiency rather than applying a fixed cutoff. A catalog file MAY add a `## Constants` H2 when a kept rule genuinely needs a named threshold.

## Worked examples

**Judgment (prompt quality):**

```markdown
| `LC_PROMPT_ROLE_DEFINITION` | warning | general | System prompt does not open with a clear role / persona statement | Read the system prompt. Assess whether the opening paragraph states what the agent is and what it does. Emit when missing. file = system prompt source. | Add an opening sentence: `"You are an X that does Y."` |
```

**Judgment (tool sufficiency):**

```markdown
| `VAGUE_TOOL_DESCRIPTION` | judgment | tools | Tool description missing or too vague for the LLM to choose the tool correctly | Walk tools; read each `.description`. Assess whether it is specific enough—purpose, side effects, and when to use versus not use it—for the model to choose it over siblings. Blank or boilerplate fires; a 2-3 sentence description does not. file = tool source, element = tool name. | Write a 2-3 sentence description covering purpose, side effects, and when to use vs not use the tool. |
```

## Reading order for the agent

1. Read this file once.
2. Read [`rule-catalog-workflow.md`](rule-catalog-workflow.md) for the Step 2.5 procedure (run the review CLI first, then the judgment catalog).
3. Run the review CLI; capture `Data.Issues[]`.
4. Read the catalog files indicated by the detection table for the current project type.
5. Apply the rows and emit findings using the canonical line format from SKILL.md Step 5.