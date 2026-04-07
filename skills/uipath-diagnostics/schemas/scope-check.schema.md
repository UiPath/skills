# Scope Check Schema

File: `.investigation/scope-check.json`

Created by: Scope Checker sub-agent
Read by: Orchestrator

## Structure

```json
{
  "checked_after": "triage | hypotheses | test",
  "current_domains": ["orchestrator"],
  "missing_domains": [],
  "unnecessary_domains": [],
  "reasoning": "Why domains should be added/removed, or why current scope is correct"
}
```

## Rules

- Scope Checker writes this file after analyzing evidence against known product domains
- Orchestrator reads it to decide whether to expand or narrow scope
- `checked_after` records which phase triggered the scope check
- `missing_domains` lists domains that should be added based on evidence
- `unnecessary_domains` lists domains that are only reporting layers with no relevant playbooks
- If both `missing_domains` and `unnecessary_domains` are empty, the current scope is correct
