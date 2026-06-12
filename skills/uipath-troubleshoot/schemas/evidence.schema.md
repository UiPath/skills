# Evidence Schema

## Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `.local/investigations/evidence/` | Interpreted evidence summaries | JSON files with analysis and interpretation |
| `.local/investigations/raw/` | Raw data dumps | Unprocessed CLI responses, file contents |

Created by: Triage sub-agent, Hypothesis Tester sub-agent
Read by: All sub-agents, orchestrator

## File naming

### Evidence files (`.local/investigations/evidence/`)

- `triage-initial.json` — initial data from triage (job info, error, etc.)
- `{hypothesis-id}-{source}.json` — evidence for a specific hypothesis
  - e.g., `H1-cli-data.json`, `H1-docsai-results.json`, `H2a-source-analysis.json`

### Raw data files (`.local/investigations/raw/`)

- `triage-{command-name}.json` — raw triage CLI response
- `{hypothesis-id}-{command-name}.json` — raw CLI response for a hypothesis
  - e.g., `H1-Jobs_GetByKeyByIdentifier.json`, `H1-GetJobTraces.json`

## Structure

Each evidence file:

```json
{
  "id": "evidence-unique-id",
  "hypothesis_id": "H1",
  "source": "uip_cli | docsai | playbook | user | source_code",
  "collected_by": "triage | tester",
  "timestamp": "ISO8601",
  "query": "What was queried or asked (uip command, docsai query, file path read)",
  "raw_data_ref": "raw/H1-Jobs_GetByKeyByIdentifier.json",
  "raw_data_summary": "Condensed summary of what was found (keep under 100 lines)",
  "interpretation": "What this evidence means for the hypothesis",
  "elimination_checks": [
    {
      "criterion": "what elimination criterion from evidence_needed.to_eliminate was checked",
      "result": "what the query/check actually returned",
      "outcome": "passed (hypothesis survives) | failed (hypothesis eliminated) | not_testable (data unavailable)"
    }
  ],
  "execution_path_traced": [
    {
      "step": "description of this step in the expected execution path",
      "expected": "what the hypothesis predicts should have happened",
      "actual": "what the data actually shows",
      "verified_by": "which query or data source confirmed this"
    }
  ],
  "needs_user_input": false,
  "user_question": null
}
```

## Signals (triage-initial.json only)

`evidence/triage-initial.json` carries a top-level `signals` array. Signals are the structured inventory of discrete facts triage extracted from gathered data. They are the unified input to playbook matching, hypothesis generation, and hypothesis testing.

```json
{
  "signals": [
    {
      "name": "exception_class",
      "value": "System.NullReferenceException",
      "category": "exception",
      "source": "raw/triage-job-logs.json"
    },
    {
      "name": "package_version",
      "value": "UiPath.System.Activities 22.10.5",
      "category": "package_version",
      "source": "raw/triage-job-traces.json"
    },
    {
      "name": "asset_exists",
      "value": true,
      "category": "entity_state",
      "source": "raw/triage-resource-assets-list.json"
    }
  ]
}
```

### Fields

- `name` — short identifier for the signal (e.g., `exception_class`, `error_code`, `asset_exists`, `package_version`). Snake_case, descriptive.
- `value` — observed value. String, number, or boolean. For boolean signals like `asset_exists`, `true` means "asset is present"; `false` means "asset is absent".
- `category` — one of: `exception | error_code | http_status | activity_label | entity_state | package_version | runtime_type | error_fragment | cross_product_ref | folder_context`. Use the closest match; do not invent new categories without need.
- `source` — relative path to the raw file the signal was extracted from. The signal MUST be traceable back to actual observed data.

### Producers and consumers

- **Triage** produces signals while executing plan data-fetch steps. Each fetched response is scanned for signal-worthy facts and entries are appended to `signals`. Triage step E (match playbooks) iterates this array, not the raw files.
- **Hypothesis generator** reads `signals` to inform what hypotheses to draft. Each generated hypothesis records which signals supported it (see `schemas/hypotheses.schema.md` → `signals_supporting`).
- **Hypothesis tester** reads `signals` BEFORE its test plan. For each `to_confirm` / `to_eliminate` item, the tester checks whether a signal already resolves it. If yes, the corresponding plan step is `status: skipped` with the signal name in `purpose` — no re-fetch.

### Rules

- One signal per discrete fact. Do NOT combine multiple facts into one signal (`exception_class_and_message` is two signals, not one).
- Contradictory signals are not allowed. If two raw sources disagree, record both observations as separate signals with distinct `name`s and let the matcher / downstream agents resolve the conflict.
- Signals are immutable once written. New evidence appends new signals; existing signals don't get rewritten.

## Rules

- **Raw data MUST be written to `.local/investigations/raw/` immediately** — write the full response to a raw file BEFORE summarizing
- **Never keep raw data in context** — write it to a raw file, then read it back only if needed for analysis. Do not hold CLI responses or log dumps in the agent's working memory.
- Evidence files contain summaries and interpretation only; they reference raw files via `raw_data_ref`
- If a sub-agent needs user input, set `needs_user_input: true` and `user_question` to the question
- The orchestrator reads evidence files (not raw files) to make decisions
- Evidence files are immutable once written — new evidence gets a new file
- Raw files are immutable once written — they are the source of truth for what was actually returned
