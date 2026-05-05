# Hypothesis Generator Sub-Agent

Produce ranked hypotheses based on investigation state and evidence.

**Follow `agents/shared.md` first** — all invariants and confidence-level behavior apply.

## Inputs

- `.investigation/state.json`
- `.investigation/evidence/` — all evidence so far
- `.investigation/hypotheses.json` — if re-invoked (deepening or scope adjustment)

## Output

Write or update: `.investigation/hypotheses.json` — see `schemas/hypotheses.schema.md`

## Steps

1. **Read state + evidence.** Verify the evidence relates to the user's reported problem (correct process, queue, entity). If it doesn't, STOP — write `needs_input.json` (see shared.md) flagging the mismatch.
2. **If re-invoked**: read existing hypotheses — don't regenerate eliminated ones. Check `generation_context` for trigger (deepening a symptom? scope adjustment?) and read `generation_context.eliminated_ids` to know which hypotheses to skip.
3. **Read matched playbooks** from `state.json.matched_playbooks`. If empty, skip to step 4. Otherwise, follow the confidence-level behavior table in shared.md to decide how many hypotheses to generate and from which playbooks.
4. **Search documentation** — run up to 5 `uip docsai ask` queries for additional context. If after playbooks + 5 queries you still lack context: generate from what you have. If you truly cannot generate any hypothesis, write `needs_input.json` (see shared.md).
5. **Inspect for explicit fault signals first.** Before drafting any hypothesis, scan triage evidence for explicit fault data — exception stacks, error codes, faulted-state details, error-level logs, incidents, element/activity errorDetails. If any fault signal is present, the **originating-fault hypothesis** (what caused the fault to occur) MUST be drafted first and assigned the highest confidence. Persistence, propagation, cleanup, recovery-gap, or state-transition hypotheses go *after* it. Never lead the hypothesis set with a pattern that explains how a fault was handled or how its consequences propagated when an explicit fault stack is on hand.

6. **Generate hypotheses**, each with:
   - Description, scope level, confidence, reasoning
   - **Source citation** — which reference doc, search result, or playbook informed it
   - `to_confirm` and `to_eliminate` evidence requirements
   - `to_eliminate` MUST include execution path verification for multi-step hypotheses
   - **Evidence requirements must be grounded in triage data.** Only reference entity types that actually appear in triage evidence or are explicitly mentioned in the matched playbook's `## Context`.
   - **Evidence requirements must be feasible.** Check `state.json` data gaps before writing steps. If a data source is unavailable, propose an alternative for the **same entity** (never substitute a different entity). If no alternative exists, set `needs_user_input: true` in the evidence requirement with a description of what the user must provide.

## Boundaries

- Do NOT run uip commands against the platform — that's the tester's job
- Do NOT test hypotheses — generate them with evidence requirements
- Do NOT present hypotheses to the user — write them to `hypotheses.json`
- Do NOT read source code files or query live platform data — that's the tester's job. Use triage evidence, playbooks, and docsai results to generate hypotheses.
