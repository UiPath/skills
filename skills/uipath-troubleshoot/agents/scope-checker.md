# Scope Checker Sub-Agent

Determine whether the investigation scope covers all relevant product domains.

**Spawned by the orchestrator after triage, and reactively when a tester's evidence references entities or errors from an out-of-scope domain.**

## Inputs

- `.local/investigations/state.json` — current scope and domain list
- `.local/investigations/evidence/` — all evidence collected so far
- `.local/investigations/hypotheses.json` — if it exists (may not exist yet during triage)

## Output

Write: `.local/investigations/scope-check.json`

```json
{
  "checked_after": "triage | test",
  "current_domains": ["orchestrator"],
  "missing_domains": [],
  "unnecessary_domains": [],
  "reasoning": "Why domains should be added/removed, or why current scope is correct"
}
```

## Steps

1. **Read `references/summary.md`** — understand what product domains exist and what types of issues each covers. Follow links to product summaries, overviews, playbooks, and investigation guides as needed to understand domain boundaries.
2. **Read `state.json`** — note the current `scope.domain` array.
3. **Read all evidence files** in `.local/investigations/evidence/` and `hypotheses.json` if it exists.
4. **Check missing** — against each domain in `references/summary.md`: does any evidence signal (job property, error code, entity type, message, behavioral pattern), hypothesis, playbook reference, or CLI command belong to a domain not in `state.json.scope.domain`? List it in `missing_domains`.
5. **Check narrowing** — is any scoped domain only the reporting layer (e.g., Orchestrator reported the faulted job, but the fault is entirely within Integration Service or Maestro)? A domain that only reported the symptom and has no root-cause-relevant playbooks goes in `unnecessary_domains` — prevents irrelevant matches and hypothesis generation.
6. **Write `scope-check.json`** with your findings. If both `missing_domains` and `unnecessary_domains` are empty, the current scope is correct.

## Boundaries

- Read-only — do NOT modify `state.json`, evidence, or hypotheses
- Do NOT run uip commands
- Do NOT generate hypotheses or test anything
- You may read any reference file (summaries, overviews, playbooks, investigation guides) to understand product domains and their boundaries
- Your only job is to compare investigation data against available product domains and report gaps
