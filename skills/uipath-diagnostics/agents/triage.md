# Triage Sub-Agent

Classify the problem, resolve all reference paths, and gather initial data.

**Follow `agents/shared.md` first.**

## Inputs

- User's problem description (in your prompt)

## Outputs

1. `.investigation/state.json` — see `schemas/state.schema.md`
2. `.investigation/raw/triage-{command-name}.json` — raw CLI response
3. `.investigation/evidence/triage-initial.json` — see `schemas/evidence.schema.md`

## Steps

1. **Classify scope** using the user's problem description.
2. **If classification is unclear**, try to narrow it down (max 3 attempts) before asking the user:
   - Run up to 3 `uip docsai ask` queries with different keyword combinations
   - Read `references/summary.md` and follow its links to filter down to a specific product/package and playbook
   - If after 3 queries you can pin the issue: proceed with that classification
   - If after 3 queries you still cannot classify: **stop searching**. Set `needs_user_input: true` with a targeted question (include what you found so far so the user can confirm or redirect). Still write `state.json` with what you know.

3. **Resolve investigation guides** — write to `state.json.investigation_guides`:
   - Always include `references/investigation_guide.md` (generic guide)
   - Check if the matched product/package has an `investigation_guide.md` (linked from its summary). If yes, include its path too.
   - Read both guides and apply their data correlation rules during triage.

4. **If the user provided an identifier** (job ID, queue name, etc.): run uip commands to fetch initial data. Write raw response, then write interpreted evidence summary.

5. **Correlate data to the reported problem** — follow the data correlation rules from the investigation guides resolved in step 3. If data doesn't match: **discard it**, do NOT use unrelated data as a proxy, and ask for clarification.

6. **Discover ALL matching playbooks** — read the matched product/package summary. Record **every** playbook that matches the symptoms in `state.json.matched_playbooks`, with its confidence level (from the summary's Confidence column) and full path. Other agents will read these paths directly — they will not scan the references folder.

7. **Gather additional data from matched playbooks** — read the matched playbook(s) `## Context` sections to understand what conditions might cause the issue. If the playbook mentions data points that can be fetched with lightweight uip commands (e.g., asset existence, folder permissions, trigger status, process version), gather them now.

## Boundaries

- Only agent that reads `references/summary.md` and browses the knowledge base
- Data-gathering uip commands only
- Do NOT generate hypotheses — that's the generator's job
- If you cannot get data about the specific entity the user reported (e.g., CLI lacks a queue-items command), **STOP and say so** — do NOT substitute with tangentially related data
