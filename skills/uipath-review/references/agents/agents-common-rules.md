# Agents — Common Rules (both formats)

Rules that apply to **both** coded and low-code agents. Read [`../rule-format.md`](../rule-format.md) and [`../rule-catalog-workflow.md`](../rule-catalog-workflow.md) first.

Companion files:

- [`agents-lowcode-rules.md`](agents-lowcode-rules.md) — low-code agent rules (mechanical + judgment)
- [`agents-coded-rules.md`](agents-coded-rules.md) — coded agent rules (mechanical + judgment)


---

## EvalsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `NO_EVALS` | error | evals | `eval_count == 0` | Compute `eval_count` per [Eval count](#eval-count) below. Emit when `eval_count == 0`, file = project root. | Add at least one eval set with ≥1 datapoint before deploying. Target `TARGET_EVAL_COUNT` datapoints. |
| `TOO_FEW_EVALS` | error | evals | `0 < eval_count < MIN_EVAL_COUNT` | Compute `eval_count`. Emit when `0 < eval_count < MIN_EVAL_COUNT`, file = project root. | Add datapoints to reach at least `MIN_EVAL_COUNT`; target `TARGET_EVAL_COUNT`. |
| `FEW_EVALS` | warning | evals | `MIN_EVAL_COUNT <= eval_count < TARGET_EVAL_COUNT` | Compute `eval_count`. Emit when `MIN_EVAL_COUNT <= eval_count < TARGET_EVAL_COUNT`, file = project root. | Grow the eval set toward `TARGET_EVAL_COUNT` for stronger regression coverage. |

### Eval count

Source of `eval_count` depends on layout:

- **Coded** — `Glob 'eval-sets/*.json'` (and `'evaluations/eval-sets/*.json'`, `'evals/eval-sets/*.json'`) at project root. For each file, Read JSON; if the file has an `evaluations` or `datapoints` array, sum the array lengths; else count `1` per file. `eval_count` is the total.
- **Low-code normalized** — Read the normalized JSON. `eval_count` = `len(.datasets)` if present, else `0`.
- **Low-code agent-builder** — `Glob 'evals/eval-sets/*.json'`. For each file, Read JSON; sum `len(.evaluations)` or `len(.datapoints)`. `eval_count` is the total. (Falls back to `0` if neither field exists — agent-builder ships eval *count* only; quality checks are low-code-only and live in the low-code catalog.)

---

## SchemaChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `SCHEMA_NO_DESCRIPTIONS` | warning | schema | >50% of schema properties lack `description` | Locate the input/output schema (see [Schema location](#schema-location) below). Walk `.properties.*`. Count properties with no `description` field (or empty string). Emit when `(missing / total) > 0.5` and `total >= 2`. file = schema source file. | Add a `description` to each schema property — Studio Web shows these as field hints, and the LLM uses them as semantic signals. |

### Schema location

- **Coded** — Read `entry-points.json` if present; else fall back to `uipath.json` → `.entryPoints[0].input` / `.entryPoints[0].output`. The emitted finding's `file` points to whichever source was read.
- **Low-code normalized** — Read the normalized JSON. Use `.input_schema` and `.output_schema`.
- **Low-code agent-builder** — Read `entry-points.json`. Use `.entryPoints[0].input` and `.entryPoints[0].output`. Cross-check against `agent.json` → `.inputSchema` / `.outputSchema` (drift is caught by `LOWCODE_SCHEMA_DRIFT` in the low-code catalog).

Emit one finding per schema (input vs output) when each independently exceeds the 50% threshold.

---

## ToolsChecker

| rule_id | severity | category | trigger | detection_method | suggested_fix |
|---|---|---|---|---|---|
| `TOO_MANY_TOOLS` | warning\|error | tools | `tool_count > MAX_TOOLS_WARNING` (warning); `tool_count > MAX_TOOLS_ERROR` (error) | Compute `tool_count` per [Tool count](#tool-count) below. Emit with `severity=error` if `tool_count > MAX_TOOLS_ERROR`; else `severity=warning` if `tool_count > MAX_TOOLS_WARNING`; else do not emit. file = project root. | Split into multiple specialized agents (each ≤ `MAX_TOOLS_WARNING` tools) or remove tools the agent does not exercise in any eval. |

### Tool count

- **Coded** — Walk every `.py` file under project root with `ast`. Count top-level function definitions decorated with `@tool`, `@function_tool`, `@langchain_tool`, or any decorator whose name ends in `_tool` / `Tool`. Skip files under `tests/`, `evals/`, `evaluations/`. *(For projects without decorator-style tools, fall back to counting `tools=[...]` literal entries in `Agent(...)` constructor calls.)*
- **Low-code normalized** — `len(.tools)` from the normalized JSON.
- **Low-code agent-builder** — `Glob 'resources/*/resource.json'`; count files whose JSON has `.type == "tool"` (or matches the tool type vocabulary in [`agents-lowcode-rules.md`](agents-lowcode-rules.md) → ToolsChecker section).

---

## Constants

| Constant | Value | Used by |
|---|---|---|
| `MIN_EVAL_COUNT` | 5 | `TOO_FEW_EVALS` |
| `TARGET_EVAL_COUNT` | 30 | `FEW_EVALS`, `TOO_FEW_EVALS` (suggested fix) |
| `MAX_TOOLS_WARNING` | 20 | `TOO_MANY_TOOLS` |
| `MAX_TOOLS_ERROR` | 30 | `TOO_MANY_TOOLS` |
