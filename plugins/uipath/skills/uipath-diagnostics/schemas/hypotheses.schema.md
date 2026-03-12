# Hypotheses Schema

File: `.investigation/hypotheses.json`

Created by: Hypothesis Generator sub-agent
Read by: Hypothesis Tester sub-agent, orchestrator
Updated by: Hypothesis Tester (status, evidence), Orchestrator (root cause flag)

## Structure

```json
{
  "hypotheses": [
    {
      "id": "H1",
      "description": "Human-readable description of what could be wrong",
      "scope_level": "platform | product | feature | process | activity",
      "confidence": "high | medium | low",
      "status": "pending | confirmed | eliminated | inconclusive",
      "is_root_cause": null,
      "parent": null,
      "reasoning": "Why this hypothesis was generated — what data or pattern led to it",
      "source": "knowledge_graph | rag | playbook | playbook_shortcut",
      "evidence_needed": {
        "to_confirm": ["what evidence would prove this"],
        "to_eliminate": ["what evidence would disprove this"]
      },
      "evidence_refs": ["evidence/H1-mcp-data.json"],
      "evidence_summary": "What was actually discovered during testing",
      "resolution": null
    }
  ],
  "generation_context": {
    "round": 1,
    "trigger": "initial | scope_adjustment | deepening",
    "parent_hypothesis": null,
    "eliminated_ids": [],
    "scope_at_generation": "process",
    "needs_user_input": false,
    "user_question": null
  }
}
```

## Rules

- Hypothesis Generator creates/appends hypotheses
- Hypothesis Tester updates: `status`, `evidence_refs`, `evidence_summary`
- Orchestrator updates: `is_root_cause` (true/false) after tester confirms
- Orchestrator updates: `resolution` field for confirmed root causes
- Never remove eliminated hypotheses — they prevent retesting
- `parent` links sub-hypotheses to the confirmed symptom they're deepening
- `generation_context` tells the generator what happened before (for re-invocation)
- `source` indicates where the hypothesis came from. Set to `playbook_shortcut` for shortcut-originated hypotheses — the orchestrator uses this to decide if it can skip testing remaining hypotheses after confirmation
