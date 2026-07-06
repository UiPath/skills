---
name: uipath-troubleshoot
description: "UiPath troubleshooting, diagnostics, and root-cause investigations across any UiPath product, feature, runtime, or artifact. Investigates errors, failures, faults, exceptions, regressions, performance problems, unexpected behavior, and silent malfunctions — answers why something failed, broke, stopped, hung, slowed down, returned wrong results, lost access, or stopped working after a change. Also diagnoses failures and faults in Integration Service connectors/connections, Office 365 / Outlook, Google Workspace (GSuite), Excel / Word / PDF activities, Computer Vision, databases / SQL, and HTTP / web activities — route here (not uipath-platform) when the intent is why it failed rather than operating the surface. Walks the available evidence (logs, traces, incidents, status fields, configuration, history) to identify the originating fault and explain what changed. For operating or CRUD on these surfaces→uipath-platform."
when_to_use: "User asks why something failed, broke, stopped, hung, was stuck, returns wrong results, or behaves unexpectedly in any UiPath system. Triggers: 'why did X fail', 'find the cause', 'find why', 'what changed', 'investigate', 'diagnose', 'debug this', 'triage', 'help me figure out', 'what's wrong', 'root cause', 'fix this error', 'inspect this trace / incident / log / job / instance', 'X worked yesterday but now …'. Also fires on raw error messages, exception stacks, error codes, job / queue IDs, or 'stuck / orphan / zombie' state descriptions."
---

# UiPath Troubleshooting Agent

Run a hypothesis-driven root-cause investigation yourself, in this context, end to end: triage → generate hypotheses → test → evaluate → depth-check → resolution. No sub-agents — every phase below is a checklist you execute inline.

Legacy note — some playbooks predate this single-agent flow. Translate their phrasing: "the orchestrator" / "sub-agent" → you; "the orchestrator re-spawns you with the user's answer" → resume the current phase checklist with the answer; "write `.local/investigations/needs_input.json`" → ask via `AskUserQuestion` and wait (Critical Rule 11).

## Critical Rules

1. **No fabrication.** Data unavailable → STOP and say so. Never invent data or substitute unrelated data.
2. **Evidence-to-problem correlation.** Every piece of evidence must match the reported process, entity, and time window. Filter before fetching. Discard unrelated data.
3. **No inference from undocumented fields.** If a field's behavior isn't in a playbook or docsai result, don't guess — flag as unverified.
4. **No CLI discovery.** Before running ANY CLI command, verify it exists in (a) the product overview CLI section or (b) a matched playbook's `## Investigation` section. Never guess command names/flags. Never use `--help` to discover commands.
5. **Empty ≠ absent.** Empty/404 → verify the container exists before concluding. Deleted/inaccessible container = data gap, not proof of absence.
6. **Live state ≠ historical state.** Current infrastructure snapshots cannot prove what happened during past incidents (>24h old — context only).
7. **CLI retry cap.** Max 2 retries per unique command (3 attempts). After 3 distinct command failures in one phase, stop and ask the user via `AskUserQuestion` — something is fundamentally wrong (wrong folder, wrong entity, missing permissions).
8. **Symptom ≠ cause.** "Confirmed as root cause" requires the underlying cause from the playbook's cause list ("What can cause it", under `## Context`) named with cause-specific evidence. Symptom matches alone (right error string, expected non-zero exit code) confirm the *playbook match*, not the *cause*. The DEPTH CHECK phase enforces this gate — never skip it.
9. **Never skip the hypothesis loop.** Conclusive-looking triage evidence still goes through GENERATE → TEST → EVALUATE. TRIAGE classifies and gathers — it does not determine root cause; a non-obvious cause surfaces only in the test cycle.
10. **Test hypotheses one at a time**, highest rank first.
11. **When you need user input, call `AskUserQuestion` and wait.** Do not proceed until answered. If the tool is unavailable in this harness, ask in plain text and stop.
12. **Read-once.** Never re-read a reference or state file already read this session. State files are write-through audit records, not your memory. One exception: DEPTH CHECK re-reads the evidence files it cites.
13. **Batch independent calls.** A plan step marked `batch` executes all its independent calls in one round-trip: for CLI fetches, ONE shell invocation chaining the commands, each redirecting to its own `raw/` file; for file reads, ONE message containing all the Read calls. Never serialize independent fetches or reads one message at a time.
14. **Never `cd`.** Run commands from the working directory; redirect output to relative `.local/investigations/raw/` paths.
15. **Never generate or execute code** (no Python, no inline code). Shell commands for file I/O and `uip` are fine.

## Investigation State

All state lives in `.local/investigations/` (relative to working directory). Schemas in `schemas/`. You are the only writer — write each artifact when its phase completes; the files are the auditable record of the method.

| File | Purpose |
|------|---------|
| `state.json` | Scope, phase, plan, matched playbooks |
| `hypotheses.json` | All hypotheses + status + per-hypothesis `test_plan` |
| `evidence/*.json` | Interpreted summaries |
| `raw/*.json` | Full raw CLI/API responses |
| `scope-check.json` | Domain expansion verdict |
| `depth-check.json` | Depth-gate verdict on confirmed root causes |

Write raw responses to `raw/` immediately; don't keep them in context. Decisions read evidence summaries, not raw files.

**Startup:** create the state directories in one command — `mkdir -p .local/investigations/raw .local/investigations/evidence` (see Tools § File I/O for the shell/write rules).

**Resume:** if context was compacted or restarted mid-investigation, resume from `state.json.phase`.

## Phase Machine

Update `state.json.phase` at each transition:

| Phase | Entry condition | Next |
|-------|----------------|------|
| `triage` | User describes problem (or new data arrives) | `hypotheses` |
| `hypotheses` | Triage complete, playbooks matched | `test` |
| `test` | Hypotheses ready, testing next in rank order | `evaluate` |
| `evaluate` | Test verdict recorded | `deepen`, `test`, or `depth_check` |
| `deepen` | Confirmed symptom needs sub-hypotheses | `hypotheses` (re-enter GENERATE) |
| `depth_check` | Hypothesis confirmed as root cause | `resolution` (verified), `test` (one re-round), or ask the user |
| `resolution` | Depth check verified, or all hypotheses exhausted | `complete` |
| `complete` | Findings presented to user | — |

**New data from user at any point** (error messages, job IDs, logs, screenshots) → go back to TRIAGE with the new data. Do NOT patch new data into an in-progress investigation.

## Confidence-Level Behavior

Follow this table in every phase. Do not redefine confidence behavior locally.

| Confidence | GENERATE | TEST | Elimination | Exec-path required? |
|---|---|---|---|---|
| **High** | 1 hypothesis per matched playbook; skip docsai unless matched playbooks are empty | 1-2 verification steps only | Quick check only | No |
| **Medium** | 1-2 hypotheses per matched playbook; docsai for additional context | Follow all troubleshooting steps in playbook | All `to_eliminate` items | Yes |
| **Low** | 2-5 hypotheses per matched playbook + docsai | Free-form reasoning | All `to_eliminate` items | Yes |

**Single-round coverage rule.** Across all confidence levels, GENERATE drafts hypotheses for *every* matched playbook in one round. Deferring medium/low playbooks to a later round wastes a full generate cycle when the first-tier hypothesis is inconclusive. The originating-fault hypothesis (GENERATE step 5) is still drafted *first* and ranked highest — the others sit beneath it in the same round.

**Playbook-signature granularity rule.** One hypothesis = one playbook match at its signature level. Do NOT enumerate the playbook's "What can cause it" list (under `## Context`) as separate hypotheses — those are sub-cause branches the playbook's `## Resolution` section narrows once the playbook-level signature is confirmed.

## Plan Loop

TRIAGE and TEST operate from a single growing plan. Plan location is per-phase: TRIAGE → `state.json.plan`; TEST → per-hypothesis `test_plan`.

The plan is an array of objects with the keys in `schemas/state.schema.md` § Plan: `{n, action, purpose, feeds, revise_if, status}`. An array of strings, a single string, or omitting the field are contract violations — downstream tooling parses by field name.

1. **Seed** the plan with the steps you can already foresee (see the phase's Required steps).
2. **Execute** the first pending step. Record the result. Mark `status: done`. Steps marked `batch` fire all their tool calls in ONE message (Critical Rule 13).
3. **Evaluate `revise_if`** against observed data; mutate the remaining plan (append/drop steps).
4. **Append discoveries.** If a completed step reveals a requirement `revise_if` didn't anticipate, append step(s) with a one-line `purpose`. Never run an unplanned command.
5. **Repeat** until all steps are `done`.
6. **Write outputs** (see the phase's final step) and move to the next phase.

## Tools

### uip CLI

Primary tool for the UiPath platform. Output defaults to json in non-interactive mode; use `--output json` to force it explicitly. Commands are documented in each product's overview CLI section and in playbook `## Investigation` sections — see Critical Rule 4.

### Documentation Search

`uip docsai ask "<question>" --source <source>`
- `--source docs` (default) — official product docs: feature behavior, configuration, API reference.
- `--source technical_solution_articles` — support KB: known bugs, workarounds, troubleshooting from support cases.

### Reading Playbooks and Guides

Read files from paths in `state.json`:
- `state.json.investigation_guides` — data correlation rules and testing prerequisites
- `state.json.matched_playbooks` — playbooks matched to the issue, with confidence level

**Confidence is a cap on root-cause certainty, not a ranking input** — rank by `signal_match_count` (see `state.schema.md` § Matched Playbooks). Do NOT modify a playbook's frontmatter confidence.

### Raw Data Rule

- **Redirect CLI output to file:** `uip ... --output json > .local/investigations/raw/{filename}.json` (or `-o .local/investigations/raw/`). Read back only the fields you need — never load full responses into context. The raw file is the record.
- Evidence files reference raw files via `raw_data_ref`.
- Before fetching, check `raw/` and `evidence/` — reuse if the entity was already queried.

### File I/O

The shell is POSIX `bash` — even on Windows. Never use PowerShell cmdlets (`New-Item`, `Out-Null`): they fail with `command not found`.

- **Directories:** `mkdir -p .local/investigations/raw .local/investigations/evidence` — one command, idempotent.
- **State/evidence files:** write with the `Write` tool. Do not fall back to `cat > … << 'EOF'` heredocs — JSON bodies break heredoc quoting.
- Never write files via inline code (Critical Rule 15).

## Investigation Flow

### TRIAGE

This phase operates from a single growing plan in `state.json.plan`. Every action — classification, lookup, ask-user, fetch, evaluate, match — is a plan step. The plan starts with one step and grows as data arrives. TRIAGE's job is to land enough context to filter playbooks; deeper data gathering belongs to TEST.

Seed the plan with the classify step:
```
{ n: 1, action: "classify (system, entity) from user message",
  purpose: "select investigation guide", feeds: "step 2",
  revise_if: "either value cannot be confidently identified -> step 2 becomes ask user (select)",
  status: "pending" }
```

The following step kinds MUST appear in every triage plan — append each as soon as its prerequisites are met. None are optional. Step E.2 is mandatory even when no trigger fires — mark it `status: skipped` in that case so the audit shows the evaluation happened.

#### A. Classify (system, entity)

Always the first step. Reasoning step (no tool call). Read the user's message and emit two values:

- **system** — the product/package the problem belongs to. The set of valid systems is whatever `references/summary.md` documents.
- **entity** — the entity type under that system (e.g., the type-of-thing the user is asking about).

Cross-check the candidate values against `references/summary.md` — if either is not a known system/entity-type, the classification has failed.

**revise_if for this step:**
- *Either value unidentifiable or ambiguous* → next step is `ask user (select)` with the plausible (system, entity) pairs via `AskUserQuestion`. Do NOT broad-scan or run exploratory `docsai ask` to guess. Write the partial classification to `state.json`, ask, and continue the plan with the answer.
- *Both values identified confidently* → next step is `look up investigation guide for <system>`.

#### B. Look up investigation guide

Reasoning + Read step. Record the resolved guide paths to `state.json.investigation_guides`:
- Always include `references/investigation_guide.md`.
- If the matched system has an `investigation_guide.md`, include it.

Read the resolved guides and apply their Data Correlation rules to the steps that follow.

#### B.5 Signal extraction — running throughout C, D, E

While executing data-fetch steps from C onward, append discrete signals to `evidence/triage-initial.json` → `signals` array (see `schemas/evidence.schema.md` § Signals). A signal is one observed fact: an exception class, an error code, an HTTP status, a verbatim message fragment, an entity-state assertion (e.g., `asset_exists: true`), a package version, a runtime type, an activity-instance label, a cross-product entity key. One signal per fact; do NOT combine. Tag each with the closest `category` from the enum in `schemas/evidence.schema.md` § Signals.

The signals array is the unified input to the rest of the investigation:

- Step E iterates `signals` (not raw files) to compute `signal_match_count` per playbook.
- GENERATE reads `signals` to cite which signals drove each hypothesis (`signals_supporting`).
- TEST reads `signals` to skip evidence steps already resolved by existing signals.

Signal extraction is not a separate plan step — after each fetch completes, scan the response and append signals before moving on.

#### C. Resolve identity / fetch primary entity

The plan steps that gather the primary entity. Their action shape is taken from the matched system's investigation guide — the documented first locator command for the identified entity type.

**Branch on anchor presence:**

- **Anchored** — the user named a concrete locator (id/key, process/package/queue/folder name, instance/incident id, or specific error code/message), or the working directory implies one (recognisable UiPath project at the top level). Step action: the deterministic first locator command the matched system's investigation guide documents for the identified entity type.
- **No anchor** — the user described the problem without a locator. Step action: `ask user (select): <option> | <option> | ...` offering the plausible anchor candidates. Do NOT plan a `get <placeholder>` for an entity you have not located. Do NOT enumerate every folder/queue/entity hoping to find the right one. Only if the user explicitly declines and authorizes a scan does the next step become a single bounded locate pass — followed by an `ask user (select)` confirming which candidate to investigate.

**Entity-instance selection.** When a step yields multiple candidate entities (e.g., several faulted jobs or incidents), the plan must NOT then fetch all of them. Priority order for the next appended step:

1. **Filter by user-named or directory-implied anchor.** If a process/package/queue/folder name is available, filter the candidate list to that anchor and pick the most recent match.
2. **Ambiguity check.** If multiple anchors plausibly apply and candidates span them, do NOT default — `ask user (select)` listing the candidate set, wait for the answer.
3. **Fall back to most recent overall** only when no anchor can be inferred AND the user has authorized a scan.

**Bound to triage level.** Gather only what filters playbooks: entity headline, error message, exception class, error code, HTTP status, activity-package namespace (from logs, if cheap). Secondary data — linked-entity data, recovery/diagnostic payloads, connection pings, element executions, cross-product follow-through — is collected only if step E appends Pass 2 fetches. Whatever the matched guide includes in the entity's opening batch (below) is gathered up-front, not deferred.

**Batch the opening fetches — do NOT serialize.** The matched guide documents an opening evidence batch for the identified entity — a set of independent data-gathering commands. Once the entity is resolved to a concrete locator, plan them as **one** `batch` step and fire the whole set in one round-trip (Critical Rule 13): one shell invocation chaining every fetch, each redirected to its own `raw/` capture file. The batch's membership, commands, filters, and `raw/` capture pattern are defined by the guide for that entity type — do NOT enumerate, name, or invent them here. This batch is the primary latency lever — serial fetching is the largest avoidable cost in triage.

#### D. Re-evaluate (system, entity) against the gathered evidence — MANDATORY scope check

**Ordering rule.** Step D MUST be appended AFTER every linked-entity fetch has completed. A linked entity is any entity that step C's data references by key/ID (parent jobs, child jobs, dependent connections/assets named in error logs, etc.). Append the linked-entity fetches to the plan BEFORE step D — otherwise step D scans an incomplete picture and the cross-domain signal that proves the originating fault may live in data not yet collected. Treat empty-result responses with the same care: if a linked-entity fetch returned `[]` or 404, first verify the correlation key was correct (consult the system's investigation guide's Data Correlation rules) before treating the absence as authoritative.

Reasoning step (no tool call). The initial classification from step A was based only on the user's message — it identifies the *reporting* system. The originating fault often lives in a different domain. Scan the gathered evidence for cross-domain signals and expand `state.json.scope.domain` accordingly.

The canonical signal-to-domain mapping lives in `references/summary.md` and each domain's own `summary.md`. Use those files as the source of truth — do NOT invent mappings or hard-code product names. Categories of signals to scan:

- **Exception class names / FQNs** — map the package prefix (segments before the leaf class name) to a domain via `references/summary.md`.
- **Activity-instance labels** — the `[Name]` prefix that names an activity instance in error log message bodies. Map the activity to its owning package via `references/summary.md`.
- **Error codes / HTTP statuses** — if a code is documented under a non-primary domain's summary, add that domain.
- **Verbatim error fragments** — if a summary's signal table cites a verbatim phrase that appears in the evidence, add that domain.
- **Cross-product entity references** — when one product's data carries a key/ID belonging to another product, add the referenced product's domain.

For every signal observed, look up the owning domain in `references/summary.md` and add it to `scope.domain` if not already present. The reporting system stays in scope as well — it owns the entity. **A missed cross-domain signal here causes the investigation to reach the wrong root cause** — GENERATE only loads playbooks for in-scope domains, so a domain not added here is invisible to every downstream phase.

This is a classification correction, not a data-gathering loop — do NOT append fetches against the new domains here. Steps E and E.2 handle that.

#### E. Match playbooks

Reasoning + Read step. Read the product/package summary for every domain in `state.json.scope.domain` (which may have just expanded in step D) — independent summaries are a `batch` read. Iterate the `signals` array in `evidence/triage-initial.json` — do NOT re-scan raw files; the signal inventory is the canonical source.

For each candidate playbook in scope, read its `## Context` and `## Investigation` sections (batch independent playbook reads), identify the playbook's signature signals, and classify the evidence-vs-signature relationship into ONE of three categories:

- **Positively supported** — at least one signal from the inventory satisfies a signature signal of the playbook. List the playbook in `state.json.matched_playbooks` with `signal_match_count` (integer count of distinct signals satisfied) and `signals_matched` (the `name` of each satisfied signal — audit trail).
- **Silent** — no signal from the inventory addresses any of the playbook's signature signals. Do NOT list. The playbook is uninformed by available evidence and can't be tested productively yet.
- **Contradicted** — a signal from the inventory directly disproves at least one CORE signal of the playbook's signature (a signal named in `## Context` or `## Investigation` as a required precondition for the cause to apply). Do NOT list in `matched_playbooks`. Record in `state.json.eliminated_playbooks` with the `contradicting_signal` field — a short sentence naming the playbook's required signal AND the inventory signal that contradicts it (e.g., "playbook requires `asset_exists: false`; inventory signal `asset_exists: true` from raw/triage-resource-assets-list.json").

Surface-level signals shared across sibling playbooks (e.g., a generic "activity failed" category) are NOT core signals — they're descriptors, not preconditions. Use the playbook's specific named signals from `## Context` / `## Investigation`.

**Rank by signal count.** Order `state.json.matched_playbooks` by `signal_match_count` DESCENDING. A `medium`-confidence playbook with 3 matched signals ranks above a `high`-confidence playbook with 1 matched signal. Ties on count break by frontmatter `confidence` (`high > medium > low`). **Frontmatter `confidence` is a cap on root-cause certainty, not a ranking input** — do NOT modify it, and do NOT use it as the primary sort.

Why count and exclusion both matter: multiple playbooks often match the same surface signal. If the matcher lists all of them at frontmatter `high`, GENERATE drafts H1 from whichever appears first — often the wrong one. Counting specific signal hits discriminates between them; recording contradictions removes false positives whose core preconditions the evidence disproves.

##### E.2 — Pass 2 trigger evaluation — MANDATORY plan step

Every triage plan MUST include a Pass 2 trigger-evaluation step appended immediately after step E. The step is cheap (reasoning against existing data) but its omission was the root cause of repeated cross-domain misses — without an explicit step, the check gets skipped.

The step's `action` is `evaluate Pass 2 triggers against matched_playbooks and gathered evidence`. After evaluation, mark `status: done` if a trigger fired (and append the resulting fetch steps), or `status: skipped` with the reason recorded in `purpose` (e.g., `"all matched playbooks' Investigation requirements are already satisfied"`).

**Pass 2 fires if ANY of the following is true:**

- Zero high-confidence playbook matched.
- Step D added one or more new domains but the data collected so far does not satisfy the evidence requirements of any matched playbook in those domains.
- A matched playbook's `## Investigation` section names evidence types not yet collected.
- The evidence references a cross-product entity (a key, id, or resource) whose own data has not been fetched.

**Pass 2 procedure when a trigger fires:**

1. **Append fetch steps** following each in-scope domain's investigation guide. Each appended step carries `purpose` and `feeds` like any other plan step; independent fetches form a `batch` step. Do not invent fetches outside what the guides document. Apply the relevant guide's Data Correlation rules when constructing the command — for cross-product entities, verify the correlation key from the relevant guide before fetching; use that documented key, do NOT default to a guessed key.
2. **Execute the appended steps.** After each, evaluate its `revise_if`. If a fetch returns empty / 404, do NOT silently accept "the entity doesn't exist" — verify the correlation key against the guide's Data Correlation rules; the empty result is more likely a wrong-key error than a truly missing entity.
3. **Re-run step D** on the now-richer evidence — same MANDATORY scope check.
4. **Re-run step E** on the updated scope.

Single Pass 2 round only. Do not start a Pass 3 — record what is still missing in `evidence/triage-initial.json` and let TEST gather the rest against a specific hypothesis.

#### F. Write evidence summary

Final step. Consolidate findings into `evidence/triage-initial.json`. Populate BOTH:

- **`signals`** — the atomic fact index (step B.5), used for matching.
- **`core_evidence`** — the curated verbatim payload TEST consumes instead of re-fetching. Populate it per `schemas/evidence.schema.md` § Core evidence: the generic core from the opening batch, and `additional` from the load-bearing fields the matched guide's `## Data Correlation` section names for this system. The schema defines the fields — do NOT enumerate them here. Every populated field traces to a `raw/` file. Leave unsupported fields null — do NOT fabricate.

TRIAGE does NOT check source-code availability — that is TEST's job (step D), evaluated per-hypothesis only when a specific `to_confirm` / `to_eliminate` item requires source. Asking upfront is wasted work when no hypothesis turns out to need it.

**Sanity gate (on completing TRIAGE):** verify the triage evidence relates to the reported problem (process/entity/time window). If it's about a different entity: discard it, inform the user, and re-run TRIAGE or ask for clarification.

**Phase rules:**
- Tool-call steps run only data-gathering uip commands documented in the matched investigation guide or a matched playbook's `## Investigation` section. Anything else is a contract violation.
- Do NOT generate hypotheses here.
- Do NOT do TEST-level deep gathering (traces, recovery/diagnostic payloads, element executions, connection pings, etc.) outside a triggered Pass 2.
- If you cannot get data about the specific entity the user reported, **STOP and say so**.

### SCOPE CHECK

Run this checklist (a) mandatorily after TRIAGE completes, (b) reactively during EVALUATE when test evidence references entities or errors from an out-of-scope domain.

1. **Recall `references/summary.md`** (already read during triage — read-once) — what product domains exist and what types of issues each covers. Follow links to product summaries, overviews, playbooks, and investigation guides as needed to understand domain boundaries (only files not yet read).
2. **Note the current `scope.domain` array** in `state.json`.
3. **Review all evidence gathered so far** and `hypotheses.json` if it exists.
4. **Check missing** — against each domain in `references/summary.md`: does any evidence signal (job property, error code, entity type, message, behavioral pattern), hypothesis, playbook reference, or CLI command belong to a domain not in `state.json.scope.domain`? List it in `missing_domains`.
5. **Check narrowing** — is any scoped domain only the reporting layer (it reported the symptom but has no root-cause-relevant playbooks)? List it in `unnecessary_domains` — prevents irrelevant matches and hypothesis generation.
6. **Write `scope-check.json`** (see `schemas/scope-check.schema.md`). Both lists empty = current scope is correct.

**Act on the verdict:**
- `missing_domains` → ask the user via `AskUserQuestion` whether to expand; if approved, run Pass-2-style fetches for the new domains per their investigation guides and re-run TRIAGE steps D + E on the expanded scope.
- `unnecessary_domains` → remove from `state.json.scope.domain`.

### GENERATE

Produce ranked hypotheses from investigation state and evidence. Write or update `hypotheses.json` — see `schemas/hypotheses.schema.md`. Behavior varies by confidence level per the Confidence-Level Behavior table.

1. **Review state + evidence + signals** (from context — read-once). Verify the evidence relates to the user's reported problem (correct process, queue, entity). If it doesn't, STOP — surface the mismatch to the user via `AskUserQuestion`.
2. **If re-entering** (deepening or scope adjustment): skip hypotheses in `generation_context.eliminated_ids` (never regenerate eliminated ones). On `trigger: deepening`, each new sub-hypothesis MUST name a *distinct upstream cause* for the parent's confirmed state — not a reworded paraphrase. If you cannot name a distinct upstream cause, ask the user instead of restating.
3. **Use `state.json.matched_playbooks`** — pre-ranked by `signal_match_count` (highest specificity first). Honor that ordering: H1 is drafted from the top-ranked playbook, H2 from the second-ranked, etc. **Never draft hypotheses from playbooks in `eliminated_playbooks`** — those are disproved by signals already.

   Generate hypotheses for **every** matched playbook in a **single round** (Single-round coverage rule). Hypotheses per playbook follow the Confidence-Level Behavior table ("GENERATE" column).

   **Cite signals.** Each hypothesis records `signals_supporting` — the names of signals from `evidence/triage-initial.json.signals` that drove it. A hypothesis with zero supporting signals is a contract violation: every drafted hypothesis must trace to at least one observed signal, otherwise it is unfounded speculation.
4. **Search documentation** — up to 5 `uip docsai ask` queries for additional context (batch independent queries). If after playbooks + 5 queries you still lack context: generate from what you have. If you truly cannot generate any hypothesis, ask the user.
5. **Inspect for explicit fault signals first.** Before drafting any hypothesis, scan triage evidence for explicit fault data — exception stacks, error codes, faulted-state details, error-level logs, incidents, element/activity errorDetails. If any fault signal is present, the **originating-fault hypothesis** (what caused the fault to occur) MUST be drafted first and assigned the highest confidence. Persistence, propagation, cleanup, recovery-gap, or state-transition hypotheses go *after* it. Never lead the hypothesis set with a pattern that explains how a fault was handled or how its consequences propagated when an explicit fault stack is on hand.
6. **Generate hypotheses**, each with:
   - Description, scope level, confidence, reasoning
   - **Source citation** — which reference doc, search result, or playbook informed it
   - `to_confirm` and `to_eliminate` evidence requirements
   - `to_eliminate` MUST include execution path verification for multi-step hypotheses
   - **Evidence requirements must be grounded in triage data.** Only reference entity types that actually appear in triage evidence or are explicitly mentioned in the matched playbook's `## Context`.
   - **Evidence requirements must be feasible.** Check `state.json` data gaps before writing steps. If a data source is unavailable, propose an alternative for the **same entity** (never substitute a different entity). If no alternative exists, set `needs_user_input: true` on the evidence requirement with what the user must provide.

**Phase rules:**
- No platform fetches in this phase — docsai only. Live data gathering is TEST's job.
- Do NOT read source code files here.
- Hypotheses go to `hypotheses.json`, not to the user.

### TEST

Test ONE hypothesis — the highest-ranked `pending` one. The test operates from a per-hypothesis `test_plan` in `hypotheses.json`. You have a clear initial picture — the hypothesis, the matched playbook's `## Investigation` section, and the `evidence_needed.to_confirm` / `to_eliminate` items — so most of the plan is knowable upfront. Revise as data arrives.

Outputs: `raw/{hypothesis-id}-{command-name}.json` per fetch; `evidence/{hypothesis-id}-{source}.json` (see `schemas/evidence.schema.md`); update the hypothesis in `hypotheses.json` — `test_plan` (all steps recorded), then `status`, `evidence_refs`, `evidence_summary`, `is_root_cause`.

Required steps in every test plan:

#### A. Review hypothesis + matched playbook

Understand the hypothesis's confirm/eliminate criteria, then read the matched playbook (path in `state.json.matched_playbooks`; skip if already read — read-once). Read `## Context` first to understand the cause being investigated. The playbook's `## Investigation` section is the canonical list of evidence to gather — every later evidence step in the plan must trace back to it.

Scope the work per the Confidence-Level Behavior table.

#### B. Investigation guides — Data Correlation always; Testing Prerequisites by confidence

Apply every guide in `state.json.investigation_guides` (read during triage — read-once) BEFORE any evidence step. Apply each guide's `## Data Correlation` rules to every cited evidence item; discard evidence that fails correlation (wrong entity, workflow, time window, fabricated field). Never confirm on evidence that fails correlation.

- **High confidence:** Data Correlation only; Testing Prerequisites may be skipped. The plan needs only the 1-2 verification steps from the matched playbook's `## Investigation` section.
- **Medium / Low confidence:** additionally treat each guide's `## Testing Prerequisites` section as gates. Two categories:
  - A prerequisite is **testable** when the data it requires is reachable with the available toolset (uip CLI commands documented in the matched playbook or product overview, source code when `source_code_path` is set, `uip docsai ask`, or user input). Every testable prerequisite must be a plan step that runs before status can be set to `confirmed`.
  - A prerequisite is **out-of-band** when it requires anything outside that toolset (host shell access on the affected server, host filesystem inspection, network connectivity probes from a specific machine, third-party service configuration not exposed via uip, etc.). Record these in `open_gaps`; they do NOT block confirmation, provided no alternative hypothesis is supported by the available evidence.

If a testable prerequisite is unmet and no plan step can satisfy it, the final status decision must be `inconclusive` with the unmet prerequisite listed in `open_gaps`.

#### C. Reuse TRIAGE evidence before refetching (delta-only)

Reasoning step. TRIAGE already gathered the opening evidence and distilled it into `evidence/triage-initial.json` — the delta-baseline. **Fetch ONLY the delta** — the hypothesis-specific evidence absent from that baseline. Do NOT re-run the guide's opening batch; TRIAGE already ran it. Resolve each `to_confirm` / `to_eliminate` item against these sources in order; only genuinely unresolved items survive into step E as fetches:

1. **Check `core_evidence`** — the curated verbatim payload TRIAGE produced (`evidence/triage-initial.json.core_evidence`, already in context; see `schemas/evidence.schema.md` § Core evidence). If an item's evidence is already present in a populated `core_evidence` field, add the plan step as `status: skipped` with the resolving field path in `purpose` (e.g., `"resolved by core_evidence.<field>"`). Do NOT re-fetch — the underlying raw file is already on disk (`source`); read it back only if you need more than the summary.
2. **Query the signal inventory** — `evidence/triage-initial.json.signals`. For items not covered by `core_evidence`, check whether a signal resolves it. If yes:
   - Add a plan step with `status: skipped`, the matching signal's `name` in `purpose` (e.g., `"resolved by signal asset_exists=true"`).
   - Append the signal name to the hypothesis's `signals_supporting` (positively supports) or `signals_contradicting` (disproves).
3. **Check raw / evidence files for non-signaled data.** For items still unresolved, check `raw/` and `evidence/` filenames for prior fetches of the same entity. If a prior TEST round or TRIAGE already fetched it, add the plan step as `status: skipped` with the existing file path in `purpose`. Do NOT re-run the same command.

Only items unresolved after 1–3 become live fetches in step E. If `core_evidence` and signals already resolve every `to_confirm` / `to_eliminate` item, step E adds **no** new fetches.

If a `to_eliminate` item is disproved by the TRIAGE baseline — a signal or a populated `core_evidence` field contradicts the hypothesis — record it (signal name in `signals_contradicting`, or the field path in the evidence summary) and set the hypothesis `status: eliminated` immediately — no further test plan needed. Move to step F.

#### D. Source-code availability check (conditional)

Triggered when any `to_confirm` / `to_eliminate` item names a project source file (workflow file, code file, project manifest). TEST resolves source availability — TRIAGE does not pre-ask. In order, no shortcuts:

a. **Check `state.json.requirements.source_code_path`** — if already set (recorded by a prior test round), use it. Add the source-file reads as plan steps directly.

b. **Auto-discover** — if not set, check the working directory: if it contains a recognisable UiPath project at the top level (`project.json`, `agent.json`, `caseplan.json`), record `source_code_path = "."` in `state.json.requirements` and proceed to (d). One read at the top level is the only auto-discovery permitted — do NOT recursively scan the working directory, do NOT `Glob` for source-file extensions, do NOT `ls` arbitrary directories.

c. **If still unknown after (a) and (b)** → ask the user for the project path via `AskUserQuestion`, naming the specific file(s) the playbook requires. The user is the only source of truth here — do NOT guess. Persist the answer to `state.json.requirements.source_code_path` BEFORE continuing — do not re-ask.

d. Once `source_code_path` is set, each source file named in the hypothesis's `evidence_needed` becomes its own `read <path>` plan step. Extract the verbatim attribute values the playbook lists. Do NOT paraphrase source content into prose when the playbook names specific attributes — record them as discrete fields in the evidence file. If a `read` step fails because the resource does not exist or cannot be read as a file, do NOT retry the same or similarly-shaped path — record the gap in `open_gaps`, set the hypothesis `status: inconclusive`, and ask the user if a corrected path would let you proceed.

#### E. Evidence-gather steps — one per UNRESOLVED `to_confirm` / `to_eliminate` item

Derived from the matched playbook's `## Investigation` section — but **only for items step C left unresolved** (the delta). Items already resolved by `core_evidence`, signals, or existing raw files are `status: skipped` and generate no fetch. Do NOT re-run the guide's opening batch — TRIAGE already ran it and its output is in `core_evidence`; re-fetching it is a contract violation. One plan step per remaining piece of evidence the playbook names; independent fetches form a `batch` step. Rules:

- **Every tool-call step must run a command documented in the matched playbook's `## Investigation` section or the product overview's CLI section.** If you need an undocumented command, do NOT add it to the plan — record the gap in `open_gaps` and let the status fall to `inconclusive`.
- **Elimination checks are first-class plan steps.** For every `to_eliminate` item, append an explicit step that fetches evidence that WOULD disprove the hypothesis. Never let elimination be an afterthought.
- **For large result sets**, summarize at evidence-write time — group errors by type, count patterns, extract samples. Do NOT slice the response with arbitrary character/byte limits.
- **Preserve user-facing data verbatim when the playbook's `## Resolution` is interactive.** If the matched playbook's resolution requires showing concrete values to the user and/or calling `AskUserQuestion` (e.g., apply a recovered value, dismiss a detected condition, replay a specific request), the corresponding evidence step MUST extract those exact values into the evidence file. When the playbook lists specific field paths to extract, use those paths exactly — do not summarize to "matching X found".

**`revise_if` on evidence steps** encodes what observed-field condition would mutate the remaining plan. Most common patterns:

- *Empty result against the expected scope* → the next step's filter must change (re-target the right scope), OR if 3 or more queries against the same scope return empty for the target entity → ask the user to confirm the correct scope. Do NOT keep querying a scope that consistently returns empty.
- *Result reveals a field that drives the next playbook branch* → append the branch-specific follow-up step.

#### F. Status decision

Final reasoning step. Set status:

| Status | Criteria |
|---|---|
| confirmed | Evidence supports AND every `to_eliminate` step ran AND none disproved AND Data Correlation rules hold for every cited evidence item AND the runtime-evidence gate below passes AND (medium/low only) every **testable** Testing Prerequisite is satisfied — out-of-band prerequisites recorded in `open_gaps` do NOT block confirmation |
| eliminated | Evidence contradicts OR causal chain link missing |
| inconclusive | Not enough data — describe what's missing in `open_gaps`, including any unmet investigation-guide prerequisites or undocumented-command gaps |

**Runtime-evidence gate.** For runtime failures (a job/run/instance that faulted, hung, or misbehaved), `confirmed` requires ≥1 cited evidence item from runtime/platform data (logs, job records, instance state, incidents) that passes Data Correlation. Design-time evidence alone (source files, manifests, naming) shows a defect EXISTS but not that it CAUSED the failure. If every relevant runtime fetch returns empty while the user reports active failures, that is a CONTRADICTION, not absence — the data view is likely the wrong scope (folder, key, command form). Do NOT confirm: set `inconclusive`, record the contradiction in `open_gaps`, ask the user to verify scope.

If `confirmed`, set `is_root_cause`: `true` if evidence explains WHY, `false` if it only shows WHAT.

**Hard exit checklist — validate before leaving this phase:** `confirmed` is unreachable until every `to_eliminate` step ran and `test_plan` records it. If the checklist fails, the test is incomplete — finish it; do not carry an unvalidated verdict into EVALUATE. For medium/low, also verify `execution_path_traced` has no unverified downstream entities.

**Phase rules:**
- Test ONLY the assigned hypothesis — don't explore unrelated leads.
- Do NOT generate sub-hypotheses — that's GENERATE (deepening).
- Empty results from documented commands DO count as evidence (the entity legitimately doesn't exist / has no logs) — UNLESS the emptiness contradicts the user's report (runtime-evidence gate: a tenant with no trace of failures the user says are active means the data view is wrong, not the user). Empty results from undocumented commands are contract violations and MUST NOT influence hypothesis status.

### EVALUATE (after each test)

**Reactive scope check:** if the test evidence references entities/errors from an out-of-scope domain, run SCOPE CHECK and act on its verdict. Otherwise skip.

**Classify and act:**

Before classifying as **explains-WHY**, apply the upstream-cause gate. The mechanism (explicit-event check + implicit-presupposition check) is defined in DEPTH CHECK § Causal precedence. Decision rule: if the gate identifies any upstream condition that has a `pending` or `supported` sibling hypothesis answering it, classify the current hypothesis as **describes-WHAT** regardless of evidence strength.

**Sibling-precedence backstop:** if the candidate root cause is a persistence, propagation, cleanup, or state-transition pattern AND any sibling hypothesis is `pending` AND that sibling questions whether the underlying state has its own originating fault, the sibling MUST be tested before the candidate can be classified as **explains-WHY**. Stopping at the first confirmed hypothesis is incorrect when that hypothesis is downstream.

- **Eliminated / Inconclusive** → record, test next hypothesis.
- **Confirmed — explains WHY** (and passes upstream-cause gate) → root cause. Go to DEPTH CHECK (do **not** jump straight to RESOLUTION). Multiple confirmed root causes: depth-check each before skipping the rest.
- **Confirmed — describes WHAT only** → symptom. Re-enter GENERATE with `trigger: "deepening"` and `parent_hypothesis`.
- **All playbook hypotheses eliminated** → re-enter GENERATE with `trigger: "scope_adjustment"` and eliminated IDs to produce from docsai (every matched playbook — all confidence levels — was already drafted in the single round).

**Co-equal-roots guard.** Before applying any "skip remaining" exit after a confirmed+verified root cause, check `state.json.matched_playbooks`. If two or more playbooks are present at the same highest confidence level AND they correspond to **distinct, independent** error signatures (different activities, different error codes, neither upstream of the other), every pending hypothesis sourced from those playbooks MUST be tested before stopping. Do not exit on the first confirmed root cause when TRIAGE found multiple co-equal roots — you will under-report and miss fixes the user has to make. Only after each co-equal hypothesis is tested (confirmed, eliminated, or inconclusive) and depth-checked when confirmed do you proceed to RESOLUTION.

**Root cause vs. symptom:** a finding that explains WHY the failure occurs is a root cause. A finding that describes WHAT happened (but not why) is a symptom — deepen it.

**When to stop testing:**
- High-confidence root cause confirmed → DEPTH CHECK; if verified AND no other co-equal-confidence playbook is still pending (co-equal-roots guard), skip remaining hypotheses and go to RESOLUTION. If co-equal playbooks remain pending, continue testing them first.
- Medium/low root cause confirmed → DEPTH CHECK; if verified, ask the user if they want to continue.
- All hypotheses exhausted (eliminated or inconclusive) → RESOLUTION with "no root cause" outcome (no depth check needed when there is nothing to gate).

### DEPTH CHECK (after a hypothesis is confirmed as root cause)

Gate every confirmed root-cause hypothesis for depth before RESOLUTION. Output: `depth-check.json` with a `verdict` (`verified` | `shallow`) + gap list that decides — present the resolution, or run one more TEST round.

**Fresh-eyes rule:** before the verdict, re-read the cited evidence files from disk (the read-once exception) and quote the datum pinning the cause. A verdict from memory or from the confirming narrative is a contract violation — judge the files, not your recollection of them. Read the matched playbook's `## Context` cause list ("What can cause it") and `## Resolution` section (from context if already read).

The three depth checks (per confirmed hypothesis):

1. **Specific cause named.** The hypothesis's `evidence_summary` (or description) names *one* item from the playbook's cause list verbatim or as a tight paraphrase — specific, not a vague generalization (e.g. "the connection is invalid" when the playbook lists four distinct sub-causes).

2. **Evidence pinned to the cause.** Evidence files contain a datum that distinguishes the chosen cause from its siblings in the same cause list. Symptom-level data (e.g. "ping returned 404") fits multiple causes — not enough. Require evidence that singles out *this* cause: file contents, ownership, folder bindings, configuration flags, trace attributes.

3. **Resolution alignment.** The playbook's `## Resolution` must contain a branch keyed on the named cause. If it offers multiple branches under "If X, then …", confirm one corresponds to the cause named in check 1.

#### Causal precedence

A root cause is an *originating fault*: an event that, had it not occurred, would mean the failure never happened. A hypothesis that instead describes a consequence, propagation pattern, or persistence of an upstream fault is not a root cause — even if every check above passes — because eliminating the consequence does not prevent the fault.

Two precedence checks:

1. **Explicit-event check.** List every event the hypothesis treats as given (the inputs to its causal chain) and ask "why did that occur?". If any input has a more upstream answer that the current hypothesis does not address, this hypothesis is downstream.

2. **Implicit-presupposition check.** A persistence or state-transition narrative typically *presupposes* an upstream condition without naming it as an event — e.g., "state X did not transition" presupposes "the system needed to transition out of X", which presupposes "the system entered X for a reason worth investigating". Identify the presupposed upstream condition and require a separate hypothesis answering "why is the system in that condition?". If `hypotheses.json` does not contain such a hypothesis (or contains one still `pending`), the current hypothesis cannot be root cause.

If either check finds a missing upstream, reject the verdict — emit `shallow` with a `gaps` entry of `kind: "textual"` and `check: "causal_precedence"` (a string identifier distinct from the numbered checks 1–3; routing is on `kind`, not `check`), detail `"hypothesis describes consequence/persistence; upstream of <X> not investigated"`. Test the upstream condition before any downstream hypothesis can be accepted as root cause.

#### Output

Write `.local/investigations/depth-check.json`:

```json
{
  "schema_version": "1.1",
  "verdict": "verified",
  "hypothesis_id": "H1",
  "playbook_path": "<path from state.json.matched_playbooks>",
  "named_cause": "<verbatim or quoted paraphrase from the playbook's 'What can cause it' list>",
  "evidence_for_cause": [
    "<file path under .local/investigations/evidence/ or .local/investigations/raw/>"
  ],
  "resolution_alignment": "matches",
  "gaps": [
    {
      "kind": "factual",
      "check": 2,
      "detail": "<one-line description of the gap>"
    }
  ]
}
```

(`verdict`: `verified` | `shallow`; `resolution_alignment`: `matches` | `mismatch` | `missing`; `gaps[].kind`: `factual` | `textual`; `gaps[].check`: 1, 2, 3, or `"causal_precedence"`.)

Multiple hypotheses flagged `is_root_cause: true` → one entry per hypothesis as an array under a top-level `"checks"` key instead.

If `verdict` is `shallow`, list every missing dimension in `gaps` and route by gap `kind`.

#### Gap classification and routing

- **`kind: "factual"`** — applies to **check 2 only** (Evidence pinned). The evidence files lack a datum that singles out the named cause from neighboring causes. One more TEST round on the same hypothesis *can* fix this by gathering more CLI output, reading additional project-source files, or inspecting trace span attributes.
  **Routing: if ANY gap is factual** — run ONE additional TEST round on the same hypothesis to gather the missing evidence, then re-run DEPTH CHECK. Stop after one re-round. After that, either declare medium-confidence and proceed to RESOLUTION with the gaps surfaced to the user, or — if the gap is a genuine data limitation — ask the user and stop.

- **`kind: "textual"`** — applies to **checks 1 and 3** (Specific cause named, Resolution alignment). The cause is named imprecisely (paraphrase too loose, wrong sub-cause picked from a list of similar causes) or the resolution branch listed is the wrong one for the named cause. Re-testing will NOT fix this — the cause/resolution narrative is GENERATE's output, not TEST's.
  **Routing: if ALL gaps are textual** — do NOT re-test. Accept the confirmed hypothesis at `confidence: medium` and proceed to RESOLUTION. Surface the textual gaps in the resolution output so the user sees them.

  **A textual gap on check 1 (cause naming) does NOT invalidate the matched playbook's `## Resolution` procedure.** Cause label and remediation path are separable. When the matched playbook's resolution is interactive (show the user a recovered value and ask whether to apply), that procedure remains the authoritative resolution even if the cause description has been refined or partially refuted. Do NOT switch to another playbook's resolution just because that other playbook better names the cause — the original playbook's remediation must still run. Note the cause refinement in the gap `detail` and surface it alongside the unchanged resolution. The only situation in which the resolution branch itself should change is a check 3 gap (Resolution alignment) — flag that separately.

If a single check produces a gap with both factual and textual character (evidence missing AND cause paraphrased), emit two separate gap entries — one of each kind.

**Exhaustive-list exception:** if a playbook's cause list is truly exhaustive but a specific cause cannot be distinguished from the available data (genuine data gap, not laziness), declare `verdict: shallow` with `gaps: ["cannot disambiguate causes X vs Y from available evidence"]` and ask the user rather than re-test.

**Phase rules:**
- Do NOT alter `hypotheses.json` or `state.json` here.
- Do NOT run uip commands here.
- Symptom ≠ cause (Critical Rule 8): a symptom-level match alone does not satisfy check 1 or check 2.

### RESOLUTION

Produce the final user-facing resolution — formatting, entity naming, cross-domain fix completeness, evidence gating. Include **all domains from `state.json.scope.domain`** — do NOT pre-filter domains by judged relevance to the causal chain; classify each as root-cause or propagation domain and search docsai for each. Excluding a domain prevents finding the error handling patterns this phase is designed to surface.

1. **Gather context** — confirmed hypothesis details, evidence files for confirmed hypotheses; follow `raw_data_ref` to raw files for authoritative field values (read-once: only files/fields not already in context).

2. **Load presentation rules** — for each domain in `state.json.scope.domain`, check if `references/products/{domain}/presentation.md` or `references/activity-packages/{domain}/presentation.md` exists. Read all that exist (batch).

3. **Assemble fixes across all domains.** For each domain in the causal chain, classify: **root cause domain** (where the failure originated) or **propagation domain** (where the failure surfaced or was relayed).

   Root cause domain:
   1. Matched playbook's `## Resolution` present → use it as the fix for that domain.
   2. No `## Resolution` → `uip docsai ask` targeted at the domain's fix (e.g., "how to prevent [specific issue] in [domain]"). Use the result if it provides a concrete, actionable fix.
   3. Nothing useful → write: "No documented fix found for the {domain} layer — check UiPath documentation or consult UiPath support."

   Propagation domains (each one):
   1. Matched playbook's `## Resolution` present → use it as the fix for that domain.
   2. Search for error handling and propagation patterns — `uip docsai ask` focused on how that domain handles failures from downstream systems. Frame the query around the domain's role, not the specific root cause.
   3. Concrete pattern found (boundary events, retry policies, alert rules) → include as a preventive fix for that domain layer, citing the docsai result.
   4. Nothing useful → write: "No documented error handling pattern found for the {domain} layer — check UiPath documentation for resilience options."

   **Do NOT write "No configuration change needed" for a propagation domain.** Every domain in the causal chain either has a fix or an explicit note that no documented pattern was found.

   **Ground fixes in gathered evidence.** Before writing any fix step that creates or provisions something new, check the evidence files for an existing artifact that already satisfies the step (an existing valid resource, an already-provisioned equivalent). If one exists, the fix MUST name it verbatim and use it — proposing to create a new equivalent when a working one is already in evidence is a wrong fix. Likewise, when the playbook's `## Resolution` names a structural precondition for the fix to hold, check the evidence for that precondition's state and report it.

   Source gating: every fix step cites its source (playbook section, docsai result, or evidence file).
   - **Preserve docsai URLs** — full URL, not just a title.
   - **Unverified steps** — no documented source → drop, or mark `[Unverified]` visibly.
   - **Undocumented field/setting behavior** → do NOT include. Write: "Check UiPath documentation for [{field/setting}] behavior before proceeding."

4. **Format the resolution:**

```
Root Cause: {description}

What went wrong: {one sentence}

Why: {root cause explanation — trace the full causal chain across all domains}

Evidence:

### {Domain} (Root Cause)
- {bullet list — quote specific field values, error messages, IDs, timestamps, and state using this domain's presentation rules}

### {Domain} (Propagation)
- {bullet list — same}

Immediate fix:

### {Domain} (Root Cause)
1. {What to do — concrete action with exact navigation path or command}
  - Why: {cite evidence that makes this step necessary}
  - Where: {exact file, UI path, setting, or command}
  - Who: {RPA developer | admin | platform team | process owner}
  - Source: {playbook path or docsai URL}

### {Domain} (Propagation)
1. {same structure}

Preventive fix:

1. {Domain} -- {What to change — concrete action}
  - Why: {cite specific evidence showing the gap this fix addresses}
  - Where: {exact file, UI path, setting}
  - Who: {RPA developer | admin | platform team}
  - Source: {playbook path or docsai URL}
2. {next domain, same structure}
```

   **No root cause found** — present what was investigated and ruled out; recommend providing more data or opening a UiPath support ticket. Then use `AskUserQuestion` to offer: provide more data (re-enter TRIAGE), or open a UiPath support ticket with the evidence gathered.

5. **Apply presentation rules** — check every entity name in the formatted text against the presentation guides and raw evidence data: display names from raw data (not API property names or paraphrases); IDs only where needed for commands; UI labels, not API field names.

6. **Investigation summary table:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|

7. **Interactive resolutions — execute after presenting.** If a matched playbook's `## Resolution` (or a doc it links to) is interactive — it prescribes printing user-facing data and asking approval to apply, replay, or dismiss something — run this procedure for each such action, in order, before any generic follow-up:

   1. Print the user-facing values as plain text, separate from the question (raw XML/selectors render poorly inside `AskUserQuestion` options/previews). Pull every value from the confirmed hypotheses' evidence files. If a required value is missing, do NOT fabricate — surface the action as blocked, naming the missing evidence field, and move on.
   2. Print any warning the playbook documents for the current mode verbatim (e.g., a recommendation-only / unproven-recovery mode).
   3. Call `AskUserQuestion` with the action's question and options; ask for the project path (or other missing input) in the same call if not already known.
   4. On accept: follow the playbook's linked procedure exactly — do not improvise. If it references a sub-skill, follow that skill's USAGE.md; otherwise apply the documented direct-edit path and run any validation command the procedure lists.
   5. On decline: stop the action; do not modify files. Move to the next action.

   Do NOT skip an interactive resolution when: the playbook was downgraded `high`→`medium` by DEPTH CHECK (the resolution procedure is preserved across confidence downgrades — see DEPTH CHECK on textual gaps); DEPTH CHECK flagged a cause-name mismatch (a reclassified cause does NOT invalidate the playbook's interactive resolution — report both together); or the recovered/recommended data was produced in a recommendation-only or unproven mode (print the documented warning and let the user decide).

8. **Follow-up.** Root cause found → offer to help implement further changes or clean up `.local/investigations/`. After the investigation completes, offer to delete or preserve `.local/investigations/`.

**Phase rules:**
- Do NOT change hypothesis status, evidence, or investigation state here.
- `uip docsai ask` is the only uip command allowed in this phase.
- Do NOT fabricate fix steps from undocumented field behavior — cite sources or flag as unverified.
- Report unretrieved or empty runtime data as a data gap ("not retrievable from the current data view"), NEVER as proof the record does not exist. Assert absence only when the container was verified (Critical Rule 5).

## Progress

Where available, use `TaskCreate`/`TaskUpdate` for each phase. Tailor subjects to the user's problem.

## Anti-patterns

- Re-reading a file already read this session (state files included — you wrote them).
- Serializing independent fetches/reads that a `batch` step should fire in one round-trip.
- Running `--help` to discover CLI commands (Critical Rule 4) — commands come only from guides and playbooks.
- `cd` before commands — use relative paths.
- Skipping DEPTH CHECK because the evidence "looks conclusive" — over-committing on root cause is the known failure mode.
- Confirming a hypothesis whose `to_eliminate` steps didn't run.
- Enumerating a playbook's cause list as separate hypotheses (one hypothesis = one playbook signature).
- Fetching all candidate entities when one anchor filters them.
- Patching new user data into an in-progress investigation — new data → re-enter TRIAGE.
