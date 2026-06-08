# Rule Catalog — Row Format

Schema for every row in the `agents-*-rules.md` judgment catalogs. The catalog is the contract — the agent applies each rule by reasoning and emits findings using its `rule_id`, `severity`, and `suggested_fix`.

The catalog is **judgment-only**: every rule requires the agent (itself an LLM) to read source and reason — prompt quality, tool-selection ambiguity, framework fit, semantic schema/eval mismatches. Deterministic checks (file presence, schema walks, counts, regex, run-artifact analysis) are **not** in the catalog; they run in the `uip agent review` / `uip codedagent review` CLI (SKILL.md Step 2.5a), which emits its findings in the same shape (`RuleId`, `Severity`, `Category`, `Description`, `File`, `SuggestedFix`).

## Row schema

Each catalog file uses one H2 section per logical checker (e.g., `## SchemaChecker`, `## ToolsChecker`). Inside each section, rules sit in one uniform table:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix |
```

| Column | Type | Source |
|---|---|---|
| `rule_id` | UPPER_SNAKE_CASE identifier in backticks | Stable contract. Never rename. |
| `severity` | One of `error` / `warning` / `info` / `judgment` (always a single value) | Mapped at report time (see below). |
| `category` | `evals` / `schema` / `tools` / `guardrails` / `general` / `code` / `security` / `runtime` | Drives report grouping. |
| `trigger` | Short condition phrase | What the rule fires on. |
| `detection_method` | The **judgment form** (see below) | The concrete evidence to read and how to reason about it. |
| `suggested_fix` | One imperative sentence | The remediation. |

## Severity mapping (catalog → report)

| Catalog `severity` | Report band (from SKILL.md Step 5) | Finding ID prefix |
|---|---|---|
| `error` | Critical | `C-D-` |
| `warning` | Warning | `W-D-` |
| `info` | Info | `I-D-` |
| `judgment` | Warning (default; agent picks Critical / Warning / Info based on contextual severity) | `W-D-` (or `C-D-` / `I-D-` when the agent escalates / de-escalates with reasoning logged in the finding's `description`) |

The `-D-` infix marks the finding as rule-driven (vs `-V-` for Step 2 validation output, or no infix for manual checklist findings). Review-CLI findings carry the `RuleId` the CLI emits and are reported in the same "Rule Findings" subsection.

## Detection method — the judgment form

Every catalog row's `detection_method` is the judgment form:

> **Judgment** — `Read <files>; assess whether <condition>; emit when <criteria>.` The agent reads the relevant source material (system prompt, tool descriptions, eval datapoints, schema, code) and applies the rule by reasoning. The `trigger` column states the rule; `detection_method` states the concrete evidence to inspect; the agent decides whether the rule fires and logs its reasoning in the finding's `description`.

Deterministic forms (Glob, Read+JSON walk, Grep, Bash, count/threshold, set-membership) do **not** appear in catalog rows — those checks live in the review CLI. If a check can be made a reliable single-file regex, count, or schema walk, it belongs in the CLI, not here.

## Status field (optional 7th column)

A rule MAY add a `status` column for deferred or experimental rules:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix | status |
```

Allowed `status` values:

- (omitted / blank) — active. Apply the rule.
- `deferred` — documented for traceability; do not apply. Record in the report's "Rules Skipped" section with reason "deferred (status: deferred)".

## The review CLI (deterministic findings)

The agent runs the review command once per agent, capturing JSON:

```bash
uip agent review --project-dir "<PROJECT_DIR>" --output json        # low-code
uip codedagent review --project-dir "<PROJECT_DIR>" --output json   # coded
```

It returns `Data.Issues[]` — deterministic findings keyed by `RuleId`, in the same severity/category/description/file/fix shape as a catalog row. The agent carries these into the report verbatim. The catalog does not list these `RuleId`s; the CLI's registry is their source of truth.

## Constants section

Judgment rows reference thresholds inline as soft cues (e.g. "a `<20-char` description is almost always too thin") rather than as hard constants — the agent reasons about sufficiency, not a fixed cutoff. A catalog file MAY still add a `## Constants` H2 if a kept rule genuinely needs a named threshold.

## Worked examples

**Judgment (prompt quality):**

```markdown
| `LC_PROMPT_ROLE_DEFINITION` | warning | general | System prompt does not open with a clear role / persona statement | Read the system prompt. Assess whether the opening paragraph states what the agent is and what it does. Emit when missing. file = system prompt source. | Add an opening sentence: `"You are an X that does Y."` |
```

**Judgment (tool sufficiency):**

```markdown
| `VAGUE_TOOL_DESCRIPTION` | judgment | tools | Tool description missing or too vague for the LLM to choose the tool correctly | Walk tools; read each `.description`. Assess: is it specific enough — purpose, side effects, when to use vs not — that the model can pick this tool over its siblings? Blank or boilerplate fires; a 2-3 sentence description does not. file = tool source, element = tool name. | Write a 2-3 sentence description covering purpose, side effects, and when to use vs not use the tool. |
```

## Reading order for the agent

1. Read this file once.
2. Read [`rule-catalog-workflow.md`](rule-catalog-workflow.md) for the Step 2.5 procedure (run the review CLI first, then the judgment catalog).
3. Run the review CLI; capture `Data.Issues[]`.
4. Read the catalog files indicated by the detection table for the current project type.
5. Apply rows; emit findings using the canonical line format from SKILL.md Step 5.
