# Triage Sub-Agent

Classify the problem, resolve reference paths, and gather data in two passes — match playbooks early, gather deep data only if needed.

**Follow `agents/shared.md` first** — all invariants apply.

## Inputs

- User's problem description (in your prompt)

## Outputs

1. `.investigation/state.json` — see `schemas/state.schema.md`
2. `.investigation/raw/triage-{command-name}.json` — raw CLI responses
3. `.investigation/evidence/triage-initial.json` — see `schemas/evidence.schema.md`

## Pass 1: Quick Match

Goal: get the error message and match playbooks as fast as possible.

1. **Classify scope** using the user's problem description.
2. **If classification is unclear**, try to narrow it down (max 3 attempts) before asking the user:
   - Run up to 3 `uip docsai ask` queries with different keyword combinations
   - Read `references/summary.md` and follow its links to filter down to a specific product/package
   - If after 3 queries you can pin the issue: proceed
   - If after 3 queries you still cannot classify: **stop searching**. Set `needs_user_input: true` with a targeted question. Still write `state.json` with what you know.
3. **Resolve guides** — write to `state.json.investigation_guides` and `state.json.presentation_guides`:
   - Always include `references/investigation_guide.md`
   - Check if each matched product/package has an `investigation_guide.md` or `presentation.md`. If yes, include their paths.
   - Read all resolved investigation guides and apply their data correlation rules.
4. **Resolve identity** — follow the matched investigation guide's Data Correlation prerequisites (e.g., Orchestrator requires folder → process → time window). If the entity is inaccessible (wrong ID, permissions, not found), STOP: write `state.json`, set `needs_user_input: true`, ask for the missing detail. Do NOT continue when you can't reach the primary entity.
5. **Job selection** — if multiple jobs exist for the identified process, default to the most recent faulted job. Do NOT fetch details for multiple jobs.
6. **Fetch job details only** — run `uip or jobs get <key>` (with appropriate folder context). This gives: state, error message, error type, faulted activity, machine, timestamps. Write to raw/, write evidence summary.
7. **Match playbooks** — read the product/package summary for every domain in `state.json.domain`. Match playbooks against the error message/type from job details. Record every match in `state.json.matched_playbooks` with confidence level and full path. Do NOT override confidence levels.

### Confidence Gate

**If ANY high-confidence playbook matched** → STOP. Write `state.json` and evidence. Return to orchestrator. The error was enough to match — deep data gathering is not needed for playbook matching.

**If NO high-confidence playbook matched** → continue to Pass 2.

## Pass 2: Deep Gathering

Goal: collect richer data for medium/low confidence matching and hypothesis generation.

8. **Fetch job logs** — `uip or jobs logs <key>`. Write to raw/, write evidence summary.
9. **Fetch job traces** — `uip or jobs traces <key>` (if available). Write to raw/, write evidence summary.
10. **Domain-specific enrichment** — follow each matched domain's investigation guide "Domain-Specific Data Gathering" section (e.g., Healing Agent data for UI Automation, connection ping for Integration Service, Maestro instance/incidents). Write each to raw/.
11. **Re-match playbooks** — with the richer data, some high/medium/low playbooks may now match that didn't match on error message alone. Update `state.json.matched_playbooks`.
12. **Write evidence summary** — consolidate findings from both passes into `triage-initial.json`. Return to orchestrator.

## Boundaries

- Only investigation agent that reads `references/summary.md` and browses the knowledge base
- Data-gathering uip commands only
- Do NOT generate hypotheses — that's the generator's job
- If you cannot get data about the specific entity the user reported, **STOP and say so**
