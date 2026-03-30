# Investigation State Schema

File: `.investigation/state.json`

Created by: Triage sub-agent
Read by: All sub-agents, orchestrator
Updated by: Orchestrator (phase transitions)

## Structure

```json
{
  "id": "inv-YYYY-MM-DD-NNN",
  "created_at": "ISO8601 timestamp",
  "phase": "triage | hypotheses | test | evaluate | deepen | resolution | complete",
  "scope": {
    "level": "platform | product | feature | process | activity",
    "domain": ["orchestrator", "ui-automation"],
    "confidence": "high | medium | low"
  },
  "entry_point": {
    "type": "job_id | error_message | queue_name | natural_language",
    "value": "the raw identifier or description the user provided"
  },
  "triage_summary": "One-paragraph classification of the problem",
  "user_context": "Original problem description from the user",
  "investigation_guides": [
    "references/investigation_guide.md",
    "references/products/orchestrator/investigation_guide.md"
  ],
  "matched_playbooks": [
    {
      "confidence": "high | medium | low",
      "path": "references/products/orchestrator/playbooks/job-stuck.md"
    }
  ],
  "requirements": {
    "folder_id": 2157426,
    "source_code_path": "/path/to/project"
  }
}
```

## Investigation Guides

Resolved by triage. Always includes the generic guide (`references/investigation_guide.md`). Includes the product-specific guide if one exists. Other agents read these paths directly — they do NOT scan the references folder themselves.

## Matched Playbooks

Resolved by triage. Full paths to every playbook that matches the symptoms, with confidence level (high/medium/low). High-confidence playbooks have a specific error match and known cause. Medium have concrete diagnostic steps. Low provide general context. The generator uses confidence to decide how many hypotheses to produce per playbook.

## Requirements

Generic key-value store for data gathered during the investigation. Any agent can read it; triage and orchestrator write to it.

- Keys are freeform — use descriptive names (e.g., `folder_id`, `source_code_path`, `queue_name`)
- Values are whatever was collected (string, number, etc.)

## Rules

- Triage sub-agent creates this file and resolves all reference paths
- Other agents read paths from `state.json` — they do NOT browse `references/` themselves
- Orchestrator updates `phase` as the investigation progresses
- Any agent can read `requirements`; triage and orchestrator write to it
- The `scope` may be updated by the orchestrator when scope adjustment occurs
