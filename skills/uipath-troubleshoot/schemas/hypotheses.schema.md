# Hypotheses Schema

File: `.local/investigations/hypotheses.json`

Created by: Hypothesis Generator sub-agent
Read by: Hypothesis Tester sub-agent, orchestrator
Updated by: Hypothesis Tester (status, evidence, is_root_cause, open_gaps), Orchestrator (may override root-cause flag; writes resolution)

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
      "source": "playbook | docsai | evidence",
      "evidence_needed": {
        "to_confirm": ["what evidence would prove this"],
        "to_eliminate": ["what evidence would disprove this"]
      },
      "signals_supporting": ["names of signals from triage-initial.json that support this hypothesis"],
      "signals_contradicting": ["names of signals that would contradict — populated by tester if any fire"],
      "test_plan": [
        {
          "n": 1,
          "action": "uip <subcommand> --output json | tee raw/H1-<file>.json",
          "purpose": "fetches a to_confirm or to_eliminate item",
          "feeds": "evidence/H1-<source>.json",
          "revise_if": "observed-field condition (empty if unconditional)",
          "status": "pending"
        }
      ],
      "evidence_refs": ["evidence/H1-cli-data.json"],
      "evidence_summary": "What was actually discovered during testing",
      "open_gaps": ["what is still missing — unmet testable prerequisites, undocumented-command gaps, out-of-band prerequisites, or a runtime-evidence contradiction"],
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

- Hypothesis Generator creates/appends hypotheses, populates `signals_supporting` from the triage `signals` inventory (each hypothesis cites the signals that drove it), leaves `test_plan: []` and `signals_contradicting: []` — the tester writes those.
- Hypothesis Tester reads triage's `signals` array BEFORE writing `test_plan`. Any `to_confirm` / `to_eliminate` item already resolved by an existing signal becomes a `status: skipped` plan step with the signal name in `purpose`. After execution, the tester updates: `status`, `evidence_refs`, `evidence_summary`, and appends any new contradicting signals to `signals_contradicting`. See `schemas/state.schema.md` § Plan for plan-step structure.
- Hypothesis Tester writes `open_gaps` on `inconclusive`/`confirmed` (unmet testable prerequisites, undocumented-command gaps, out-of-band prerequisites, runtime-evidence contradictions). `status: confirmed` may carry `open_gaps` only for out-of-band items that do not block confirmation.
- Hypothesis Tester sets `is_root_cause` on confirm (`true` = evidence explains WHY, `false` = shows only WHAT). Orchestrator may override per its upstream-cause gate.
- Orchestrator updates: `resolution` field for confirmed root causes, after the depth-check verdict (the depth-verifier reads the playbook's `## Resolution`, not this field)
- Never remove eliminated hypotheses — they prevent retesting
- `parent` links sub-hypotheses to the confirmed symptom they're deepening
- `generation_context` tells the generator what happened before (for re-invocation)
- When deepening: orchestrator sets `generation_context.trigger: "deepening"` and `generation_context.parent_hypothesis` to the ID of the confirmed symptom before re-invoking the generator
- `source`: `playbook` for playbook-derived, `docsai` for documentation-derived, `evidence` for evidence-derived. This is the hypothesis-origin tag — distinct from the evidence-file `source` enum (`uip_cli | docsai | playbook | user | source_code`) in `evidence.schema.md`.
- `test_plan` step `status` enum is `pending | done | skipped` (see `state.schema.md` § Plan)
- The generator drafts hypotheses for every matched playbook — all confidence levels — in a single round (see `shared.md` § Single-round coverage rule), ranked by `signal_match_count`. `trigger: "scope_adjustment"` re-invocation is reserved for producing additional hypotheses from docsai once every playbook-derived hypothesis is eliminated. When a high-confidence hypothesis is confirmed, the orchestrator skips the lower-ranked remainder (subject to the co-equal-roots guard).
