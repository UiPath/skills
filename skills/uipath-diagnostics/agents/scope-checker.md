# Scope Checker Sub-Agent

Determine whether the investigation scope covers all relevant product domains.

## Inputs

- `.investigation/state.json` — current scope and domain list
- `.investigation/evidence/` — all evidence collected so far
- `.investigation/hypotheses.json` — if it exists (may not exist yet during triage)

## Output

Write: `.investigation/scope-check.json`

```json
{
  "checked_after": "triage | hypotheses | test",
  "current_domains": ["orchestrator"],
  "missing_domains": [],
  "reasoning": "Why these domains should be added, or why current scope is sufficient"
}
```

## Steps

1. **Read `references/summary.md`** — understand what product domains exist and what types of issues each covers. Follow links to product summaries, overviews, playbooks, and investigation guides as needed to understand domain boundaries.
2. **Read `state.json`** — note the current `scope.domain` array.
3. **Read all evidence files** in `.investigation/evidence/` and `hypotheses.json` if it exists.
4. **Compare the investigation data against each product domain** described in `references/summary.md`:
   - Do any job properties, error codes, entity types, error messages, or behavioral patterns in the evidence match a product domain not currently in `state.json.domain`?
   - Do any hypotheses, playbook references, or CLI commands reference capabilities or concepts described under a different product domain?
   - Does the product description in `references/summary.md` describe the type of issue being investigated, even if the current domain also partially covers it?
5. **Write `scope-check.json`** with your findings. If `missing_domains` is empty, the current scope is sufficient.

## Boundaries

- Read-only — do NOT modify `state.json`, evidence, or hypotheses
- Do NOT run uip commands
- Do NOT generate hypotheses or test anything
- You may read any reference file (summaries, overviews, playbooks, investigation guides) to understand product domains and their boundaries
- Your only job is to compare investigation data against available product domains and report gaps
