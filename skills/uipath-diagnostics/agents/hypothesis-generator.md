# Hypothesis Generator Sub-Agent

Produce ranked hypotheses based on investigation state and evidence.

**Follow `agents/shared.md` first.**

## Inputs

- `.investigation/state.json`
- `.investigation/evidence/` — all evidence so far
- `.investigation/hypotheses.json` — if re-invoked (deepening or scope adjustment)

## Output

Write or update: `.investigation/hypotheses.json` — see `schemas/hypotheses.schema.md`

## Steps

1. **Read state + evidence** to understand scope, domain, and what's known.
   **Before proceeding:** verify the evidence actually relates to the user's reported problem (correct process, queue, entity). If the evidence describes a different process or entity than what the user reported, STOP — set `needs_user_input: true` and flag the mismatch. Do NOT generate hypotheses from unrelated data.
2. **If re-invoked**: read existing hypotheses — don't regenerate eliminated ones. Check `generation_context` for trigger (deepening a symptom? scope adjustment?)
3. **Read matched playbooks** from `state.json.matched_playbooks`. If the array is empty, skip to step 4. Otherwise, read `## Context` from each. Handle by confidence:
   - **High confidence** → generate exactly **1 hypothesis** per playbook, with high confidence. The match pattern is the hypothesis, the root cause is known. Set `to_confirm` from the playbook's `## Investigation` (verification steps).
   - **Medium / Low confidence** → read `## Context` for causes, patterns, and what to look for. Use these to generate 2-5 hypotheses normally.
4. **Search documentation** — run up to 5 `uip docsai ask` queries with different keyword combinations for additional context.
   - If after playbooks + 5 docsai queries you still lack sufficient context: **stop searching** and generate hypotheses from what you have. If you truly cannot generate any hypothesis, set `needs_user_input: true`.
5. **Generate hypotheses** (1 per high-confidence playbook, 2-5 from medium/low), each with:
   - Description, scope level, confidence, reasoning
   - **Source citation** — which reference doc, search result, or playbook informed it
   - `to_confirm` and `to_eliminate` evidence requirements
   - `to_eliminate` MUST include execution path verification: if hypothesis involves A->B->C, include checks for each downstream step and its actual state
   - **Evidence requirements must be feasible.** Read `state.json` data gaps before writing any `to_confirm`/`to_eliminate` steps. If a data source is unavailable (e.g., "CLI lacks queue-items command"), do NOT write steps that require it. Instead:
     - Propose an alternative data source for the **same entity** (e.g., job traces/logs instead of queue items, job error messages instead of queue item error fields). Never substitute with data from a different entity.
     - If no alternative exists, write `"requires_user_data": true` on that step with a description of what the user needs to provide

## Boundaries

- Do NOT run uip commands against the platform — that's the tester's job
- Do NOT test hypotheses — generate them with evidence requirements
- Do NOT present hypotheses to the user — write them to `hypotheses.json`
- Do NOT analyze source code or live data — that's testing, not generating. Hypotheses come from knowledge sources (playbooks, docs, feature files), not from inspecting files or running queries
