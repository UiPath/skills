# Investigation State Schema

File: `.investigation/state.json`

Created by: Triage sub-agent
Read by: All sub-agents, orchestrator
Updated by: Orchestrator (phase transitions, requirements)

## Structure

```json
{
  "id": "inv-YYYY-MM-DD-NNN",
  "created_at": "ISO8601 timestamp",
  "phase": "triage | hypotheses | test | evaluate | deepen | resolution | complete",
  "scope": {
    "level": "platform | product | feature | process | activity",
    "domain": ["maestro", "orchestrator"],
    "confidence": "high | medium | low"
  },
  "entry_point": {
    "type": "job_id | error_message | queue_name | natural_language",
    "value": "the raw identifier or description the user provided"
  },
  "triage_summary": "One-paragraph classification of the problem",
  "user_context": "Original problem description from the user",
  "requirements": {
    "folder_id": 2157426,
    "source_code_path": null
  }
}
```

## Requirements

The `requirements` object is a flat key-value map. Keys correspond to requirement `id`s declared in the matched playbook's frontmatter. Values are:
- A resolved value (string, number) if auto-resolved by triage or provided by user
- `null` if unresolved
- `"unavailable"` if user explicitly declined to provide

The orchestrator reads the playbook's requirement definitions to know which keys are required, deferrable, etc. The state file only stores the resolved values.

## Rules

- Triage sub-agent creates this file
- Orchestrator updates `phase` as the investigation progresses
- Orchestrator updates `requirements` when the user provides values
- The `scope` may be updated by the orchestrator when scope adjustment occurs
