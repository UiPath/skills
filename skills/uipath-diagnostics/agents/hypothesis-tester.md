# Hypothesis Tester Sub-Agent

Gather evidence and evaluate ONE specific hypothesis.

**Follow `agents/shared.md` first.**

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
2. **Read the investigation guides** from `state.json.investigation_guides`. Follow the data correlation rules to verify evidence relates to the correct entity, and the testing prerequisites to know what to gather before drawing conclusions. If you cannot get data for the correct entity, set `inconclusive` and explain the gap — do NOT use unrelated data.
3. **Read the matched playbook** for this hypothesis (path in `state.json.matched_playbooks`). Always read `## Context` first for understanding. Then scope your work to the playbook's confidence level:
   - **High confidence** (has `## Investigation` with 1-2 verification steps) → follow those steps only. This should be quick verification, not deep investigation.
   - **Medium confidence** (has `## Investigation` with concrete diagnostic steps) → follow the steps. Each step produces evidence.
   - **Low confidence** (no `## Investigation` or general guidance only) → reason freely from context and evidence.
4. **Check existing evidence** — reuse data already in `evidence/`
5. **Gather new evidence** using available tools:
   - uip CLI commands, `uip docsai ask` for documentation, source code, user input
6. **For large result sets:** summarize yourself — group errors by type, count patterns, extract samples
7. **Before confirming, actively try to disprove:**
   - Check EVERY item in `evidence_needed.to_eliminate` — populate `elimination_checks` in the evidence file for each criterion with `outcome: "passed" | "failed" | "not_testable"`
   - Trace the full execution path — populate `execution_path_traced` with each step, expected vs. actual, and what verified it
   - For any downstream entity (child job, queue item, triggered process): query its actual state, don't infer from upstream
8. **Set status:**

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
