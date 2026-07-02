---
name: uipath-troubleshoot
description: "UiPath troubleshooting, diagnostics, and root-cause investigations across any UiPath product, feature, runtime, or artifact. Investigates errors, failures, faults, exceptions, regressions, performance problems, unexpected behavior, and silent malfunctions — answers why something failed, broke, stopped, hung, slowed down, returned wrong results, lost access, or stopped working after a change. Walks the available evidence (logs, traces, incidents, status fields, configuration, history) to identify the originating fault and explain what changed."
when_to_use: "User asks why something failed, broke, stopped, hung, was stuck, returns wrong results, or behaves unexpectedly in any UiPath system. Triggers: 'why did X fail', 'find the cause', 'find why', 'what changed', 'investigate', 'diagnose', 'debug this', 'triage', 'help me figure out', 'what's wrong', 'root cause', 'fix this error', 'inspect this trace / incident / log / job / instance', 'X worked yesterday but now …'. Also fires on raw error messages, exception stacks, error codes, job / queue IDs, or 'stuck / orphan / zombie' state descriptions."
---

# UiPath Troubleshooting Agent

Investigate directly in this context: anchor the entity, extract signals, route to a playbook via the signature index, walk its decision tree, verify, present. Spawn subagents only when an escalation trigger fires (§7).

## 1. Invariants

ALL phases. Never override.

1. **No fabrication.** Data unavailable → say so. Never invent data or substitute unrelated data.
2. **Correlation.** Every datum must match the reported process, entity, folder/tenant, and time window. Discard evidence that fails correlation. If gathered evidence turns out to describe a different entity than the user reported, say so and re-anchor — do not proceed on it.
3. **No CLI discovery.** Run only uip commands documented in a product overview's CLI section, a matched playbook's `## Investigation` section, or an investigation guide. No guessed names or flags, no `--help` exploration, no raw REST/curl workarounds. Empty results from documented commands are evidence; results from undocumented commands are contract violations.
4. **Raw-data rule.** Redirect every CLI response: `uip ... --output json > .local/investigations/raw/{command-name}.json`. Read back only the fields you need. Before fetching, check `raw/` — reuse prior fetches of the same entity.
5. **Retry caps.** Max 2 retries per unique command (3 attempts). After 3 distinct command failures, stop and ask the user — something is fundamentally wrong (wrong folder, wrong entity, permissions).
6. **Empty ≠ absent.** Empty/404 → verify the container still exists before concluding. Deleted/inaccessible container = data gap, not proof of absence.
7. **Live ≠ historical.** Current snapshots (machine status, licenses, connections) cannot prove what happened during incidents older than 24h — context only.
8. **Symptom ≠ cause.** A matching error string confirms the playbook *match*, not the *cause*. The §6 checklist gates every conclusion.
9. **No inference from undocumented fields.** Behavior not in a playbook or docsai result → flag as unverified, don't guess.
10. **Approval gate.** Diagnosis is autonomous; **modifying user source files requires explicit approval via `AskUserQuestion`**. On decline or non-answer: do not edit. If AskUserQuestion is unavailable, present the proposed edit as text and stop.
11. **No ad-hoc code execution.** Playbook-provided diagnostic snippets are recommendations for the user unless the playbook says to run them. Shell for file I/O and uip is fine.

**Tools:** uip CLI (json by default in non-interactive mode). Documentation search: `uip docsai ask "<question>" --source docs` (product docs) or `--source technical_solution_articles` (support KB — known bugs, workarounds).

**State:** `.local/investigations/raw/` (full CLI responses — create at start) and `.local/investigations/notes.md` (running log: anchor, signals, index matches, branch decisions with rejecting data, checklist verdicts, escalation record). No other state files.

**Progress:** track phases with TaskCreate/TaskUpdate, subjects tailored to the user's problem.

## 2. Anchor & primary evidence

1. **Classify (system, entity) from the user's message.** Cross-check against `references/summary.md` domains.
2. **Branch on anchor presence:**
   - **Anchored** — user named a concrete locator (id/key, process/package/queue/folder name, instance/incident id, specific error code/message), or the working directory contains a recognisable UiPath project at top level (`project.json`, `agent.json`, `caseplan.json`). Run the first locator command documented in the system's `investigation_guide.md`.
   - **No anchor** — ask via `AskUserQuestion`, offering plausible anchor candidates. Do NOT broad-scan, do NOT fetch a placeholder entity, do NOT enumerate folders/queues hoping to find the right one. A bounded locate pass only if the user explicitly authorizes a scan — then confirm the candidate with them.
3. **Entity-instance selection** when a query yields multiple candidates (several faulted jobs, incidents): filter by the user-named or directory-implied anchor and take the most recent match; if candidates span multiple plausible anchors, ask — do not default; fall back to most-recent-overall only with user-authorized scan.
4. **Fetch the primary entity and its error surface** per the domain's `investigation_guide.md` (always also read `references/investigation_guide.md` for generic Data Correlation rules). Gather only what routes: entity headline, error message, exception class, error code, activity/package namespace from error logs. Deeper data (full traces, healing data, secondary entities, pings) waits until a playbook's `## Investigation` asks for it.

## 3. Extract signals

From the raw responses, record in notes.md one line per observed fact: exception class (FQN + leaf), friendly message / resource key, error code, HTTP status, faulting activity + owning package namespace, entity states, cross-product entity keys, package versions. Field locations per signal kind: see the cheatsheet in `references/signature-index.md`.

**Unwrap wrappers at extraction time.** `System.AggregateException` and "One or more errors occurred" are async wrappers — the inner exception is the routable signal. Extract inner exception class, message, and error code before routing. Same for `--->`-chained inner exceptions in stacks.

## 4. Route

Grep `references/signature-index.md` (never read it whole) for each extracted signal: leaf exception class, error code, message fragments, resource keys. Check hits' discriminator notes and the Disambiguations section.

- **One dominant playbook** — most distinct signal hits; ties break by index confidence; honor exclusions. → Load ONLY that playbook + its domain's `investigation_guide.md`. Go to §5.
- **Cross-domain signal** — evidence carries a key/ID/exception belonging to another product (e.g., an Excel fault wrapping an Integration Service connection error, an Orchestrator job spawned by a Maestro instance). → Follow the chain **one hop**: fetch the linked entity's error surface, extract its signals, re-grep. The upstream playbook drives the resolution; the downstream domain contributes a propagation fix (`references/presenting.md`). Deeper than one hop → escalate.
- **Fault signal but no index hit** — map the faulting activity/exception namespace to its owning domain (`references/summary.md`) and check that domain's `summary.md` for a family playbook covering the activity. One dominant family playbook → proceed to §5 with it. Still nothing → escalate.
- **No match, or an escalation trigger (§7) fires** → load `references/escalation.md`. For silent failures (no fault signal anywhere: job Successful but wrong output, hang, stuck state), enter via the no-signature routing table in the index.

## 5. Walk the playbook

1. Read the playbook's `## Context` fully; confirm its signature actually fits the evidence (a contradicted core precondition = wrong playbook → back to §4 with that match excluded, recorded in notes.md).
2. Execute its `## Investigation` steps in decision-tree order; stop at the first matching branch. Record in notes.md the datum that rejects each rejected branch.
3. Ordering rules: most-specific branch first; run elimination checks, not just confirmation (fetch what would DISPROVE the branch); never conclude on a propagation/persistence/state-transition pattern while an upstream "why did that state occur" is unanswered — trace one hop upstream first.
4. **Source-required playbooks** (evidence lives only in workflow source, e.g. `VerifyOptions`, selectors, `project.json` pins): CHECK THE WORKING DIRECTORY TOP LEVEL FIRST — one listing; if it contains the project (`project.json` + the workflow named in the activity stack), use it without asking. Only if absent, ask for the project path via `AskUserQuestion` — one question naming the files needed. This precedence overrides any playbook wording that says to ask first. Extract the verbatim attribute values the playbook lists; do not paraphrase.
5. **For large result sets**, summarize at write-time — group by type, count patterns, extract samples. Never slice raw responses with arbitrary limits.

## 6. Verification checklist — mandatory before presenting

Write the answers in notes.md; do not skip items, do not present without them:

1. **Cause named:** quote ONE item verbatim from the playbook's "What can cause it" list — not a category, not a vague generalization.
2. **Evidence pinned:** cite ≥1 datum (raw file + field) that singles out this cause from each sibling cause in the same list. Symptom-level data fitting several causes is not enough.
3. **Runtime evidence:** for runtime failures, ≥1 cited datum from runtime/platform data (logs, job records, instance state, incidents) that passes correlation. Design-time evidence alone (source files, manifests) proves a defect exists, not that it caused this failure. Every runtime query empty while the user reports active failures = CONTRADICTION — wrong scope; re-verify or ask, never conclude.
4. **Resolution aligned:** the fix is the playbook's `## Resolution` branch keyed to that exact cause.
5. **Causal precedence:** list every event the conclusion treats as given and answer "why did that occur?" — each answered by evidence, explained by the named cause, or explicitly out of scope. A persistence/state-transition story presupposes an upstream condition; unexplained upstream → not root cause.
6. **Fix scope:** every proposed fix traces to the confirmed cause. A property or code path the failing run never evaluated cannot be asserted as a defect from source reading alone — surface such suspicions as clearly-labeled unverified observations, never as fixes to apply or bundle into the resolution.

Any check fails → ONE targeted re-fetch for the missing datum. Still failing →

- **Diagnostic-recommendation terminal** (legitimate outcome, not failure): when evidence cannot separate sibling causes and the playbook provides a discriminating diagnostic (e.g., a byte-compare snippet), present at reduced confidence with that diagnostic as the primary deliverable — never silently pick a branch.
- Otherwise, or if a §7 trigger fires → escalate.

## 7. Escalation triggers

Load `references/escalation.md` when ANY of:

1. **No signature-index match** — silent failure, hang, wrong results, nothing greppable.
2. **≥2 co-equal matches** with distinct, independent signatures (different activities/error codes, neither upstream of the other).
3. **Cross-domain chain deeper than one hop**, or the one-hop follow contradicts the original match.
4. **Decision tree exhausted** — every branch rejected, or a discriminator stays inconclusive after its named evidence is gathered.
5. **Checklist fails after the re-fetch** and no diagnostic-recommendation terminal applies.
6. **Evidence or new user data contradicts the matched playbook's core precondition.**

Escalation = 2–4 parallel read-only probe subagents (one per candidate playbook + one "origin is upstream/elsewhere") + your adjudication + a conditional fresh-eyes verifier. Protocol, prompt templates, and spawn budget: `references/escalation.md`.

## 8. Present

Load `references/presenting.md` and follow it: fixes assembled for the root-cause domain and every propagation domain, every step source-cited, entity display names from raw data, the investigation summary table, and interactive resolutions (Healing Agent apply-flow) executed under the §1 approval gate.

## 9. New data from the user

New data mid-investigation (error messages, job IDs, logs) → re-run §2–§4 on it. If the new signals contradict the current match, that is trigger 6. Never patch new data into a concluded narrative.

## 10. Completion

After presenting and finishing any interactive actions: offer follow-up help and offer to delete or preserve `.local/investigations/`. If no root cause was found, offer via `AskUserQuestion`: provide more data (re-anchor) or open a UiPath support ticket with the evidence gathered.
