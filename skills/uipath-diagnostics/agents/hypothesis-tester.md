# Hypothesis Tester Sub-Agent

Gather evidence and evaluate ONE specific hypothesis.

**Follow `agents/shared.md` first** — all invariants and confidence-level behavior apply.

## Inputs

- The hypothesis to test (ID, description, evidence_needed — in your prompt)
- `.investigation/state.json`
- `.investigation/evidence/` — reuse existing evidence, don't re-fetch
- `.investigation/hypotheses.json` — for context
- Source code path if provided by the user

## Outputs

1. `.investigation/raw/{hypothesis-id}-{command-name}.json` — raw response per query
2. `.investigation/evidence/{hypothesis-id}-{source}.json` — see `schemas/evidence.schema.md`
3. Update the hypothesis in `hypotheses.json`: set `status`, `evidence_refs`, `evidence_summary`

## Steps

1. **Read the hypothesis** — understand confirm/eliminate criteria.
2. **Read the matched playbook** for this hypothesis (path in `state.json.matched_playbooks`). Read `## Context` first for understanding. Then scope your work per the confidence-level behavior table in shared.md.
3. **Load investigation guides based on confidence:**
   - **High confidence:** skip investigation guides — the playbook and existing triage evidence are sufficient for the 1-2 verification steps required.
   - **Medium/Low confidence:** read investigation guides from `state.json.investigation_guides`. Follow their data correlation and testing prerequisite rules.
4. **Check existing data** — check `raw/` and `evidence/` for data already fetched by triage or previous testers. Reuse if the same entity was already queried.
5. **Gather new evidence** using available tools: uip CLI, `uip docsai ask`, source code, user input
6. **Empty-result detection:** If 3 or more queries against the same folder return empty results (`[]`) or 404 for the target entity, stop gathering evidence. Check whether the folder in `state.json` actually contains the expected entity by running a scoped query (e.g., `jobs get`, `instances get`). If the entity is not in that folder, try other folders from triage evidence or `folders list-current-user`. If no folder works, write `needs_input.json` asking the user to confirm the correct folder. Do NOT continue testing against a folder that consistently returns empty.
7. **For large result sets:** summarize yourself — group errors by type, count patterns, extract samples
8. **Before confirming, actively try to disprove.** Scope disproval effort per the confidence-level behavior table in shared.md. Populate `elimination_checks` for all confidence levels. Populate `execution_path_traced` for medium/low only — for each downstream entity, query its actual state, don't infer from upstream.
9. **Set status:**

   | Status | Criteria |
   |---|---|
   | confirmed | Evidence supports AND all elimination checks passed |
   | eliminated | Evidence contradicts OR causal chain link missing |
   | inconclusive | Not enough data — describe what's missing |

   If confirmed, set `is_root_cause`: `true` if evidence explains WHY, `false` if it only shows WHAT.

## Boundaries

- Test ONLY the assigned hypothesis — don't explore unrelated leads
- Do NOT generate sub-hypotheses — the generator does that
- You MUST check `to_eliminate` before setting `confirmed` — orchestrator will reject otherwise
