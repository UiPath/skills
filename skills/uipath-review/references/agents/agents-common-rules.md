# Agents — Common Rules (both formats)

Judgment rules that apply to **both** coded and low-code agents. Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

> **This catalog is judgment-only.** Deterministic agent checks (eval counts, tool counts, schema-property presence, set-membership, regex, run-artifact analysis) run in the `uip agent review` / `uip codedagent review` CLI, which the reviewer invokes **first** (SKILL.md Step 2.5). The CLI returns those findings in the same rule format. This file holds only rules that require an LLM to read source and reason — what a regex or count cannot decide reliably.

Companion files:

- [`agents-lowcode-rules.md`](agents-lowcode-rules.md) — low-code judgment rules
- [`agents-coded-rules.md`](agents-coded-rules.md) — coded judgment rules

---

## SchemaChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `SCHEMA_NO_DESCRIPTIONS` | judgment | schema | Input/output schema properties lack **informative** descriptions | Locate the schema (see [Schema location](#schema-location)). Read each property's `description`. Assess — not mere presence: is each description informative enough for the LLM to populate / consume the field correctly and for Studio Web to render a useful hint? A field named `id` described as `"the id"` adds no signal; a missing description on a non-obvious field is worse. Emit when a meaningful share of properties are undescribed or described with content that restates the field name. file = schema source. (The deterministic `>50%-missing` count runs in the review CLI; this rule judges informativeness.) | Add a `description` to each property that states what it holds, valid values, and format — Studio Web shows these as field hints and the LLM uses them as semantic signals. |

### Schema location

- **Coded** — Read `entry-points.json` if present; else `uipath.json` → `.entryPoints[0].input` / `.entryPoints[0].output`. The finding's `file` points to whichever source was read.
- **Low-code normalized** — Read the normalized JSON. Use `.input_schema` and `.output_schema`.
- **Low-code agent-builder** — Read `entry-points.json`. Use `.entryPoints[0].input` and `.entryPoints[0].output`.

Assess input and output schema independently — emit a separate finding per schema when each is weak.

---

## What this catalog cannot do

The agent applies these rules from the project source as it is *checked into the repo*. It cannot verify runtime behaviour (whether the LLM follows the prompt, whether tool selection is correct, whether guardrails fire) or validate live IDs (connection IDs, index names, recipients) — those require running the agent or calling APIs.
