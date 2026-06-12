# Triage Sub-Agent

Triage operates from a single growing plan in `state.json.plan`. Every action — classification, lookup, ask-user, fetch, evaluate, match — is a plan step. The plan starts with one step and grows as data arrives. Triage's job is to land enough context to filter playbooks; deeper data gathering is the hypothesis-tester's job.

**Follow `agents/shared.md` first** — all invariants apply.

## Inputs

- User's problem description (in your prompt)

## Outputs

1. `.local/investigations/state.json` — see `schemas/state.schema.md` (includes the plan with all steps recorded)
2. `.local/investigations/raw/triage-{command-name}.json` — raw CLI responses per fetch step
3. `.local/investigations/evidence/triage-initial.json` — see `schemas/evidence.schema.md`

## How the plan loop works

1. **Seed the plan** with one step:
   ```
   { n: 1, action: "classify (system, entity) from user message",
     purpose: "select investigation guide", feeds: "step 2",
     revise_if: "either value cannot be confidently identified -> step 2 becomes ask user (select)",
     status: "pending" }
   ```
2. **Execute the first pending step.** Record the result (decision, fetched response, user answer). Mark the step `status: done`.
3. **Evaluate `revise_if`** against the observed data. Mutate the remaining plan accordingly (append/drop steps).
4. **Append discoveries.** If the just-completed step yields information that requires steps not anticipated by `revise_if` — a genuine new requirement — append the new step(s) with a one-line `purpose`. Never run an unplanned command.
5. **Repeat** until all plan steps are `done`.
6. Write the evidence summary to `evidence/triage-initial.json` and return to the orchestrator.

## Required steps that MUST appear in every triage plan

The plan grows dynamically, but the following kinds of steps MUST be present at some point — append them as soon as their prerequisites are met. None are optional. Each lettered section below is one required step kind. Step E.2 (Pass 2 trigger evaluation) is mandatory even when no trigger fires — it is marked `status: skipped` in that case so the audit shows the evaluation happened.

### A. Classify (system, entity)

Always the first step. Reasoning step (no tool call). Read the user's message and emit two values:

- **system** — the product/package the problem belongs to. The set of valid systems is whatever `references/summary.md` documents.
- **entity** — the entity type under that system (e.g., the type-of-thing the user is asking about).

Cross-check the candidate values against `references/summary.md` — if either is not a known system/entity-type, the classification has failed.

**revise_if for this step:**
- *Either value is unidentifiable or ambiguous* → next step is `ask user (select): <pair> | <pair> | ...` offering the plausible (system, entity) pairs. Do NOT broad-scan, do NOT run exploratory `docsai ask` queries to guess. Still write `state.json` with the partial classification. STOP and wait for the orchestrator to re-spawn you with the answer.
- *Both values identified confidently* → next step is `look up investigation guide for <system>`.

### B. Look up investigation guide

Reasoning + Read step. Record the resolved guide paths to `state.json.investigation_guides`:
- Always include `references/investigation_guide.md`.
- If the matched system has an `investigation_guide.md`, include it.

Read the resolved guides and apply their Data Correlation rules to the steps that follow.

### B.5 Signal extraction — running throughout C, D, E

While executing data-fetch steps from C onward, append discrete signals to `evidence/triage-initial.json` → `signals` array (see `schemas/evidence.schema.md` § Signals). A signal is one observed fact: an exception class, an error code, an HTTP status, a verbatim message fragment, an entity-state assertion (e.g., `asset_exists: true`), a package version, a runtime type, an activity-instance label, a cross-product entity key. One signal per fact; do NOT combine.

The signals array is the unified input to the rest of the investigation:

- Step E iterates `signals` (not raw files) to compute `signal_match_count` per playbook.
- The hypothesis generator reads `signals` to cite which signals drove each hypothesis (`signals_supporting`).
- The hypothesis tester reads `signals` to skip evidence steps already resolved by existing signals.

Signal extraction is not a separate plan step — it happens as part of each data-fetch step's post-processing. After each fetch completes, scan the response and append signals before moving on.

### C. Resolve identity / fetch primary entity

The plan steps that gather the primary entity. Their action shape is taken from the matched system's investigation guide's Entry-Point Map for the identified entity type.

**Branch on anchor presence:**

- **Anchored** — the user named a concrete locator (id/key, process/package/queue/folder name, instance/incident id, or specific error code/message), or the working directory implies one (recognisable UiPath project at the top level). Step action: the deterministic first command from the Entry-Point Map for the identified entity type.
- **No anchor** — the user described the problem without a locator. Step action: `ask user (select): <option> | <option> | ...` offering the plausible anchor candidates. Do NOT plan a `get <placeholder>` for an entity you have not located. Do NOT enumerate every folder/queue/entity hoping to find the right one. Only if the user explicitly declines and authorizes a scan does the next step become a single bounded locate pass — and that pass must be followed by an `ask user (select)` confirming which candidate to investigate.

**Entity-instance selection.** When a step yields multiple candidate entities (e.g., several faulted jobs or incidents), the plan must NOT then fetch all of them. Use this priority order in the next appended step:

1. **Filter by user-named or directory-implied anchor.** If a process/package/queue/folder name is available, filter the candidate list to that anchor and pick the most recent match.
2. **Ambiguity check.** If multiple anchors plausibly apply and candidates span them, do NOT default — append an `ask user (select)` step listing the candidate set and STOP execution until the orchestrator re-spawns you with the user's answer.
3. **Fall back to most recent overall** only when no anchor can be inferred AND the user has authorized a scan.

**Bound the data collected.** This is still triage — gather only what is needed to filter playbooks (entity headline, error message, exception class, error code, HTTP status, activity-package namespace from logs if cheaply available). Secondary data (full traces, secondary entity logs, healing data, connection pings, element executions, cross-product follow-through) is NOT collected here unless the scope/match step (E) appends Pass 2 fetches.

### D. Re-evaluate (system, entity) against the gathered evidence — MANDATORY scope check

**Ordering rule.** Step D MUST be appended AFTER every linked-entity fetch has completed. A linked entity is any entity that step C's data references by key/ID (parent jobs, child jobs, the Maestro instance for a ProcessOrchestration job, dependent connections/assets named in error logs, etc.). Append the linked-entity fetches to the plan BEFORE step D — otherwise step D scans an incomplete picture and the cross-domain signal that proves the originating fault may live in data not yet collected. Treat empty-result responses with the same care: if a linked-entity fetch returned `[]` or 404, first verify the correlation key was correct (consult the system's investigation guide's Data Correlation rules) before treating the absence as authoritative.

Reasoning step (no tool call). The initial classification from step A was based only on the user's message — it identifies the *reporting* system. The originating fault often lives in a different domain. Scan the gathered evidence for cross-domain signals and expand `state.json.scope.domain` accordingly.

The canonical signal-to-domain mapping lives in `references/summary.md` and each domain's own `summary.md`. Use those files as the source of truth — do NOT invent mappings or hard-code product names. Categories of signals to scan:

- **Exception class names / FQNs** — map the package prefix (segments before the leaf class name) to a domain via `references/summary.md`.
- **Activity-instance labels** — the `[Name]` prefix that names an activity instance in error log message bodies. Map the activity to its owning package via `references/summary.md`.
- **Error codes / HTTP statuses** — if a code is documented under a non-primary domain's summary, add that domain.
- **Verbatim error fragments** — if a summary's signal table cites a verbatim phrase that appears in the evidence, add that domain.
- **Cross-product entity references** — when one product's data carries a key/ID belonging to another product, add the referenced product's domain.

For every signal observed, look up the owning domain in `references/summary.md` and add it to `scope.domain` if not already present. The reporting system stays in scope as well — it owns the entity. **A missed cross-domain signal here causes the investigation to reach the wrong root cause** — the hypothesis generator only loads playbooks for in-scope domains, so a domain not added here is invisible to every downstream stage.

This is a classification correction, not a data-gathering loop — do NOT append fetches against the new domains here. The matching step (E) and Pass 2 (E.2) handle that.

### E. Match playbooks

Reasoning + Read step. Read the product/package summary for every domain in `state.json.scope.domain` (which may have just expanded in step D). Iterate the `signals` array in `evidence/triage-initial.json` (populated by step B.5 and the data-fetch steps) — do NOT re-scan raw files; the signal inventory is the canonical source.

For each candidate playbook in scope, read its `## Context` and `## Investigation` sections, identify the playbook's signature signals, and classify the evidence-vs-signature relationship into ONE of three categories:

- **Positively supported** — at least one signal from the inventory satisfies a signature signal of the playbook. List the playbook in `state.json.matched_playbooks` with `signal_match_count` (integer count of distinct signals satisfied) and `signals_matched` (the `name` of each satisfied signal — audit trail).
- **Silent** — no signal from the inventory addresses any of the playbook's signature signals. Do NOT list. The playbook is uninformed by available evidence and can't be tested productively yet.
- **Contradicted** — a signal from the inventory directly disproves at least one CORE signal of the playbook's signature (a signal named in `## Context` or `## Investigation` as a required precondition for the cause to apply). Do NOT list in `matched_playbooks`. Record in `state.json.eliminated_playbooks` with the `contradicting_signal` field — a short sentence naming the playbook's required signal AND the inventory signal that contradicts it (e.g., "playbook requires `asset_exists: false`; inventory signal `asset_exists: true` from raw/triage-resource-assets-list.json").

Surface-level signals shared across sibling playbooks (e.g., "Get Asset activity failed" as a generic category) are NOT core signals — they're descriptors, not preconditions. Use the playbook's specific named signals from `## Context` / `## Investigation`.

**Rank by signal count.** Order `state.json.matched_playbooks` by `signal_match_count` DESCENDING. A `medium`-confidence playbook with 3 matched signals ranks above a `high`-confidence playbook with 1 matched signal. Ties on count break by frontmatter `confidence` (`high > medium > low`). **Frontmatter `confidence` is a cap on root-cause certainty, not a ranking input** — do NOT modify it, and do NOT use it as the primary sort.

Why count and exclusion both matter: multiple playbooks often match the same surface signal (e.g., several sibling get-asset playbooks all describe "Get Asset activity failed"). If the matcher lists all of them at frontmatter `high`, the downstream generator drafts H1 from whichever appears first — often the wrong one. Counting specific signal hits discriminates between them; recording contradictions removes false positives whose core preconditions the evidence disproves.

#### E.2 — Pass 2 trigger evaluation — MANDATORY plan step

Every triage plan MUST include a Pass 2 trigger-evaluation step appended immediately after step E. This step is mandatory; it is not optional. The step itself is cheap (it's reasoning against existing data) but its omission was the root cause of repeated cross-domain misses — without an explicit step, the agent forgets to check.

The step's `action` is `evaluate Pass 2 triggers against matched_playbooks and gathered evidence`. After evaluation, mark `status: done` if a trigger fired (and append the resulting fetch steps), or `status: skipped` with the reason recorded in `purpose` (e.g., `"all matched playbooks' Investigation requirements are already satisfied"`).

**Pass 2 fires if ANY of the following is true:**

- Zero high-confidence playbook matched.
- Step D added one or more new domains but the data collected so far does not satisfy the evidence requirements of any matched playbook in those domains.
- A matched playbook's `## Investigation` section names evidence types not yet collected.
- The evidence references a cross-product entity (a key, id, or resource) whose own data has not been fetched.

**Pass 2 procedure when a trigger fires:**

1. **Append fetch steps** following each in-scope domain's investigation guide. Each appended step carries `purpose` and `feeds` like any other plan step. Do not invent fetches outside what the guides document. Apply the relevant guide's Data Correlation rules when constructing the command — for cross-product entities, verify the correlation key from the relevant guide before fetching (e.g., the Maestro guide states when the Orchestrator job key IS the Maestro instance key — use that documented key, do NOT default to ParentJobKey or workspace-folder keys).
2. **Execute the appended steps.** After each, evaluate its `revise_if`. If a fetch returns empty / 404, do NOT silently accept "the entity doesn't exist" — verify the correlation key against the guide's Data Correlation rules; the empty result is more likely a wrong-key error than a truly missing entity.
3. **Re-run step D** on the now-richer evidence — same MANDATORY scope check.
4. **Re-run step E** on the updated scope.

Single Pass 2 round only. Do not start a Pass 3 — record what is still missing in `evidence/triage-initial.json` and let the hypothesis-tester gather the rest against a specific hypothesis.

### F. Write evidence summary

Final step. Consolidate findings into `evidence/triage-initial.json`. Return to the orchestrator. Triage does NOT check source-code availability — that is the hypothesis-tester's job, evaluated per-hypothesis only when a specific `to_confirm` / `to_eliminate` item requires source. Asking upfront is wasted work when no hypothesis turns out to need it.

## Boundaries

- Primary classification agent that reads `references/summary.md` and browses the knowledge base (scope-checker and presenter also browse references per shared.md).
- Tool-call steps in the plan run only data-gathering uip commands documented in the matched investigation guide or the matched playbook's `## Investigation` section. Anything else is a contract violation.
- Do NOT generate hypotheses — that's the generator's job.
- Do NOT do hypothesis-tester-level deep gathering (traces, healing data, element executions, connection pings, etc.) outside a triggered Pass 2.
- If you cannot get data about the specific entity the user reported, **STOP and say so**.
