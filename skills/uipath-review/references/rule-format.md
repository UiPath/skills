# Rule Catalog — Row Format

Schema for every row in `agents-*-rules.md` catalog files. The catalog is the contract — the agent applies it verbatim and emits findings using its `rule_id`, `severity`, and `suggested_fix` values.

The agent applying rules is itself an LLM, so the catalog mixes two row kinds in one table: rules that resolve mechanically (file presence, schema walks, CLI output) and rules that require the agent's own reasoning (prompt quality, tool overlap, failure-mode risk). Both use the same row schema; only the `detection_method` column differs.

## Row schema

Every catalog file uses a single H2 section per logical checker (e.g., `## EvalsChecker`, `## SchemaChecker`). Inside each section, rules sit in one uniform table:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix |
```

| Column | Type | Source |
|---|---|---|
| `rule_id` | UPPER_SNAKE_CASE identifier in backticks | Verbatim from POC. Stable contract. Never rename. |
| `severity` | One of `error` / `warning` / `info` / `judgment` (always a single value — rules with observation-dependent severity are split into distinct `rule_id`s, e.g., `TOO_MANY_TOOLS` / `EXCESSIVE_TOOL_COUNT`). | Verbatim from POC. Mapped at report time (see below). |
| `category` | `evals` / `schema` / `tools` / `guardrails` / `general` / `lowcode` / `code` / `security` / `runtime` / `eval-results` | Matches the `uip agent review --checks <name>` argument vocabulary. Drives report grouping. Not every catalog uses every value — the low-code catalog uses `evals` / `schema` / `tools` / `guardrails` / `general` / `lowcode`; the coded catalog additionally uses `code` / `security` / `runtime` / `eval-results`. |
| `trigger` | Short condition phrase | Verbatim from POC. |
| `detection_method` | One of the forms below | Concrete instruction the agent executes (mechanical) or reasons through (judgment). |
| `suggested_fix` | One imperative sentence | Verbatim from POC `_fix_suggestion()` / rule body. |

## Severity mapping (catalog → report)

| Catalog `severity` | Report band (from SKILL.md Step 5) | Finding ID prefix |
|---|---|---|
| `error` | Critical | `C-D-` |
| `warning` | Warning | `W-D-` |
| `info` | Info | `I-D-` |
| `judgment` | Warning (default; agent picks Critical / Warning / Info based on contextual severity) | `W-D-` (or `C-D-` / `I-D-` when the agent escalates / de-escalates with reasoning logged in the finding's `description`) |

The `-D-` infix marks the finding as catalog-driven (vs `-V-` for validation CLI output or no infix for manual checklist findings).

## Detection method forms

`detection_method` cells must be one of these forms. Pick the simplest that works.

### Mechanical forms (resolve to a yes/no on file content)

1. **Glob** — `Glob '<pattern>' relative to project root; emit when <count condition>.`
2. **Read + JSON walk** — `Read <file>; parse JSON; check <jsonpath>; emit when <condition>.`
3. **Grep** — `Grep -n '<regex>' <file-or-glob>; emit one finding per match.`
4. **Bash one-liner** — `Bash: <command>; emit if <stdout condition>.` (e.g., `git ls-files .env` → non-empty)
5. **CLI** — `Run \`uip agent review --project-dir "<PROJECT_DIR>" --checks <name> --output json\` and pick out findings where \`rule_id == "<RULE_ID>"\`.` Use when the rule requires code execution the agent cannot perform inline (AST parsing, embedding-based diversity, complex flow analysis).

### Judgment form (agent applies via reasoning)

6. **Judgment** — `Read <files>; assess whether <condition>; emit when <criteria>.` The agent reads the relevant source material (system prompt, tool descriptions, eval datapoints, schema, etc.) and applies the rule by reasoning. The `trigger` column states the rule; the `detection_method` states the concrete evidence to inspect; the agent decides whether the rule fires.

Mix freely within one section — a row's `detection_method` can be inline-mechanical, CLI-mechanical, or judgment, depending on the rule.

## Status field (optional 7th column)

A rule MAY add a `status` column for deferred or experimental rules:

```markdown
| rule_id | severity | category | trigger | detection_method | suggested_fix | status |
| `EVAL_LOW_DIVERSITY` | error | evals | … | Run `uip agent review --checks evals --output json` and pick `rule_id == "EVAL_LOW_DIVERSITY"`. | … | |
```

Allowed `status` values:

- (omitted / blank) — active. Apply the rule.
- `deferred` — documented for traceability; do not apply. Record in the report's "Rules Skipped" section with reason "deferred (status: deferred)".

🔲 proposed and 🚫 retired POC rows do not migrate to the catalog at all.

## CLI invocation pattern

When a row's `detection_method` is the CLI form, the agent runs:

```bash
uip agent review --project-dir "<PROJECT_DIR>" --checks <name>[,<name>...] --output json
```

`--checks` accepts a comma-separated list of checker names matching the H2 sections of the catalog. Low-code catalog: `evals`, `schema`, `tools`, `guardrails`, `general`, `lowcode`. Coded catalog adds: `code`, `security`, `runtime`, `eval-results`. The CLI returns JSON containing findings keyed by `rule_id` — the agent picks out the ones it needs.

> Batching multiple checks in one invocation is preferred when several CLI-form rules belong to the same checker (e.g., all eval rules in one `--checks evals` call).

## Constants section

Each catalog file MAY end with a `## Constants` H2 listing thresholds the rows reference by name:

```markdown
## Constants

| Constant | Value | Used by |
|---|---|---|
| `MAX_TOOLS_WARNING` | 20 | `TOO_MANY_TOOLS` |
| `MAX_TOOLS_ERROR` | 30 | `TOO_MANY_TOOLS` |
```

Rows then reference the constant by name in `trigger` / `detection_method` instead of inlining the literal — keeps thresholds in one place.

## Worked examples

**Mechanical (inline):**

```markdown
| `LOWCODE_MESSAGES_NO_USER` | error | lowcode | `messages[]` has no `role: "user"` entry | Read `agent.json` → `.messages[]`. Emit when no element has `.role == "user"`. file = `agent.json`. | Add a `{"role": "user", "content": "..."}` message — input templating only reaches the model through the user message. |
```

**Mechanical (CLI):**

```markdown
| `EVAL_LOW_DIVERSITY` | error | evals | Input embedding entropy < `DIVERSITY_ERROR_THRESHOLD` | Run `uip agent review --project-dir "<PROJECT_DIR>" --checks evals --output json`; pick findings where `rule_id == "EVAL_LOW_DIVERSITY"`. | Diversify eval inputs — current inputs cluster too tightly in semantic space. |
```

**Judgment:**

```markdown
| `LC_PROMPT_ROLE_DEFINITION` | warning | general | System prompt does not open with a clear role / persona statement | Read the system prompt. Assess whether the opening paragraph states what the agent is and what it does. Emit when missing. file = system prompt source. | Add an opening sentence: `"You are an X that does Y."` |
```

## Reading order for the agent

1. Read this file once.
2. Read [`rule-catalog-workflow.md`](rule-catalog-workflow.md) for the Step 2.5 procedure.
3. Read the catalog files indicated by the detection table for the current project type.
4. Apply rows; emit findings using the canonical line format from SKILL.md Step 5.
