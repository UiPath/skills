# Findings — uipath-maestro-flow

One codifiable procedure identified. All CLI commands (`flow validate`, `flow format`, `eval run *`, etc.) and generative authoring steps are excluded.

---

## 1. Evaluator JSON structure validation — VALIDATE

**Source:** `references/evaluate/references/evaluators-guide.md` — type table, JSON shape examples, anti-patterns

**Procedure:** Given one or more evaluator JSON files, validate each against the rules in `evaluators-guide.md`:

1. File parses as valid JSON
2. Required top-level fields present: `id`, `name`, `version`, `evaluatorTypeId`, `evaluatorConfig`
3. `evaluatorTypeId` is one of the 7 valid internal values:

| `--type` CLI flag | Valid `evaluatorTypeId` | LLM? |
|---|---|---|
| `exact-match` | `uipath-exact-match` | No |
| `json-similarity` | `uipath-json-similarity` | No |
| `contains` | `uipath-contains` | No |
| `llm-judge-output` | `uipath-llm-judge-output-semantic-similarity` | Yes |
| `llm-judge-strict-json` | `uipath-llm-judge-output-strict-json-similarity` | Yes |
| `llm-judge-trajectory` | `uipath-llm-judge-trajectory-similarity` | Yes |
| `llm-judge-trajectory-simulation` | `uipath-llm-judge-trajectory-simulation` | Yes |

4. LLM-judge types must have `evaluatorConfig.model` as a non-empty string (omitting it causes a 500 from the LLM gateway — anti-pattern in `evaluators-guide.md`)
5. Deterministic types (`exact-match`, `json-similarity`, `contains`) must NOT carry `evaluatorConfig.model`
6. No duplicate `id` values across the checked set (copy-paste guard — anti-pattern in `evaluators-guide.md`)

**Why it's mechanical:** Every rule is stated explicitly in the guide. No judgment on content — only type and field presence.

**Script:** `scripts/validate_evaluators.py`

```bash
# Single file
python3 scripts/validate_evaluators.py path/to/my-evaluator.json

# Multiple files
python3 scripts/validate_evaluators.py eval-a.json eval-b.json eval-c.json

# All *.json files in a directory
python3 scripts/validate_evaluators.py --dir MySolution/MyFlow/evaluators/
```

Key args:
- `files`   One or more evaluator JSON file paths (positional)
- `--dir`   Directory to scan for all `*.json` files instead

Example output:
```
# Pass
OK: 2 file(s) passed

# Fail
FAIL [greeting-quality.json]: evaluatorTypeId='uipath-llm-judge-output-semantic-similarity' is an llm-judge type — evaluatorConfig.model must be a non-empty string (omitting model causes a 500 from the LLM gateway)

1 file(s) failed, 1 passed
```

**Turn savings:** Without the script, the agent writes evaluator JSON, submits via CLI, receives an opaque API 500, reads the error, diagnoses the missing field, corrects the JSON, and resubmits — typically 2 extra turns per malformed file. The script surfaces the problem before any API call.

**Tests:** `script-tests/validate_evaluators/`
