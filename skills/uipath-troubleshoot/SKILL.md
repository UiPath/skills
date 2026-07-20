---
name: uipath-troubleshoot
description: "UiPath causal investigation across every product, runtime, and activity package. Use when the primary outcome is an explanation, diagnosis, or root cause for undesirable existing behavior: faults, hangs, regressions, slowdowns, access loss, unexpected state changes, wrong or empty results, silent no-ops, or raw errors. Diagnostic intent outranks surface ownership for runtime behavior; invoke even when the prompt names only a job, folder, queue item, connector, connection, activity, trace, flow, agent, or other resource and another UiPath skill supplies inspection commands. Correlates runtime, configuration, history, and source evidence to find the originating fault and fix. For operating resources without causal investigation→uipath-platform; for applying a known source fix→the artifact owner; for build-time/CLI faults of a local artifact (pack, build, validate, bindings)→the artifact's skill."
when_to_use: "Trigger when the requested outcome is to explain or investigate undesirable existing UiPath behavior. Infer this from the goal; no exact phrase, product name, exception, or identifier is required. A pasted raw error message, exception stack, or error code with no other request implies this outcome. Do not trigger for pure CRUD/list/start/stop/status, aggregate monitoring, or a direct edit to a known local artifact when no causal investigation is requested."
---

# UiPath Troubleshooting Agent

Investigate directly in this context: anchor the entity, extract signals, route to a playbook by grepping the playbook corpus, walk its decision tree, verify, present. Spawn subagents only when an escalation trigger fires (§7).

## 1. Invariants

ALL phases. Never override.

1. **No fabrication.** Data unavailable → say so. Never invent data or substitute unrelated data.
2. **Correlation.** Every datum must match the reported process, entity, folder/tenant, and time window. Discard evidence that fails correlation. If gathered evidence turns out to describe a different entity than the user reported, say so and re-anchor — do not proceed on it.
3. **No CLI discovery.** Run only uip commands documented in a product overview's CLI section, a matched playbook's `## Investigation` section, or an investigation guide. No guessed names or flags, no `--help` exploration, no raw REST/curl workarounds. Empty results from documented commands are evidence; results from undocumented commands are contract violations.
4. **Raw-data rule.** Capture every CLI response to `.local/investigations/raw/{command-name}.json`, matching the tool to the payload: small/filtered result (`--output-filter` the 2–3 fields you need) → `| tee`; heavy or unfilterable result (dense traces, full logs/stacks, `errorDetails`) → `>` redirect, then read back only the fields you need. Never `tee` an unfiltered response. Full pattern + filter-failure fallback: generic guide § Output Capture. Before fetching, check `raw/` — reuse prior fetches of the same entity. Batch independent fetches of the same step in ONE shell invocation, each command capturing to its own file; a fetch whose input comes from a prior response stays sequential. Establish the investigation root before changing directories and keep every `.local` path rooted there. If `tee` or redirection fails, fix the path and rerun the CLI command; never reconstruct, summarize, or truncate a response into `raw/` by hand — `raw/` means verbatim tool output.
5. **Retry caps.** Max 2 retries per unique command (3 attempts). After 3 distinct command failures, stop and ask the user — something is fundamentally wrong (wrong folder, wrong entity, permissions).
6. **Empty ≠ absent.** Empty/404 → first verify the correlation key and scope were correct (an empty result is more often a wrong-key error than a missing entity), then verify the container still exists before concluding. Deleted/inaccessible container = data gap, not proof of absence. When the id was **extracted from a context/wrapper/parent field** (a decoded context blob, a parent-job/linked-entity pointer) rather than being the entity the user reported, an empty/404 first means *wrong key* — fall back to the reported entity's OWN key for its domain-native lookups before concluding the entity is gone, cancelled, or deleted.
7. **Live ≠ historical.** Current snapshots (machine status, licenses, connections) cannot prove what happened during incidents older than 24h — context only.
8. **Symptom ≠ cause.** A matching error string confirms the playbook *match*, not the *cause*. The §6 checklist gates every conclusion.
9. **No inference from undocumented fields.** Behavior not in a playbook or docsai result → flag as unverified, don't guess.
10. **Approval gate + no self-edit.** Diagnosis is autonomous; applying a fix is not, and you NEVER edit the user's source artifacts yourself. **A confirmed fix that changes a source artifact (`.xaml`, `.cs`, `project.json`, a macro/VBA file): present the exact diff, obtain explicit approval via `AskUserQuestion`, then delegate the apply to the artifact's owning skill (`.xaml`/`.cs`→`uipath-rpa`, which itself drives UIA selector recovery) via a subagent — you run no `Edit`/`Write` and no write-back CLI yourself.** A fix to cloud/tenant state with no local file (Orchestrator config, Integration Service connection, Data Fabric, LLM Gateway) is **recommendation-only** — print the exact `uip …` command or UI path; never delegate, never self-apply. Diagnostic commands stay autonomous: reads, and playbook-prescribed idempotent re-validations whose purpose is evidence (e.g. a same-values `update` re-probe). A request for steps or a script is a deliverable, not execution approval — author it, do not run it. On decline, non-answer, unavailable `AskUserQuestion`, no available delegate, or a delegation that fails: present the proposed fix as text and STOP — a missing/failed approval or a failed delegation is NEVER permission to edit the artifact yourself.
11. **No ad-hoc code execution.** Playbook-provided diagnostic snippets are recommendations for the user unless the playbook says to run them. Shell for file I/O and uip is fine.

**Tools:** uip CLI (json by default in non-interactive mode). Documentation search: `uip docsai ask "<question>" --source docs` (product docs) or `--source technical_solution_articles` (support KB — known bugs, workarounds).

**State:** `.local/investigations/raw/` (full CLI responses — create at start) and `.local/investigations/notes.md` (running log: anchor, signals, playbook matches, branch decisions with rejecting data, checklist verdicts, escalation record). No other state files.

**Progress:** track phases with TaskCreate/TaskUpdate, subjects tailored to the user's problem.

## 2. Anchor & primary evidence

1. **Classify (system, entity) from the user's message.** Cross-check against `references/summary.md` domains.
2. **Branch on anchor presence:**
   - **Anchored** — user named a concrete locator (id/key, process/package/queue/folder name, instance/incident id, specific error code/message), or the working directory contains a recognisable UiPath project at top level (`project.json`, `agent.json`, `caseplan.json`). Run the first locator command documented in the system's `investigation_guide.md`; if the system has no guide, proceed with the user-supplied signals to §3–§4 — the matched playbook's `## Investigation` supplies the commands.
   - **No anchor** — ask via `AskUserQuestion`, offering plausible anchor candidates. Do NOT broad-scan, do NOT fetch a placeholder entity, do NOT enumerate folders/queues hoping to find the right one. A bounded locate pass only if the user explicitly authorizes a scan — then confirm the candidate with them.
3. **Entity-instance selection** when a query yields multiple candidates (several faulted jobs, incidents): filter by the user-named or directory-implied anchor and take the most recent match; if candidates span multiple plausible anchors, ask — do not default; fall back to most-recent-overall only with user-authorized scan.
4. **Fetch the primary entity and its error surface** per the domain's `investigation_guide.md` when the domain has one (always also read `references/investigation_guide.md` for generic Data Correlation and Output Capture rules). Gather only what routes: entity headline, error message, exception class, error code, activity/package namespace from error logs. Deeper data (full traces, healing data, secondary entities, pings) waits until a playbook's `## Investigation` asks for it.

## 3. Extract signals

From the raw responses, record in notes.md one line per observed fact: exception class (FQN + leaf), friendly message / resource key, error code, HTTP status, faulting activity + owning package namespace, entity states, cross-product entity keys, package versions. Field locations per signal kind: see the cheatsheet in `references/investigation_guide.md` § Signal-Extraction Cheatsheet.

**Unwrap wrappers at extraction time.** `System.AggregateException` and "One or more errors occurred" are async wrappers — the inner exception is the routable signal. Extract inner exception class, message, and error code before routing. Same for `--->`-chained inner exceptions in stacks.

**Localized error text.** Host-side messages (.NET framework, Office/COM) localize with the robot's system language; playbooks store canonical English. Route on language-invariant signals first — exception class/FQN, error codes, resource keys, HTTP status, API state enum values (these never localize). If a message fragment is non-English, grep the playbooks with its canonical English wording (translate before grepping) and record the original text plus locale in notes.md.

## 4. Route

Grep the playbook corpus for each extracted signal — fixed-string, filenames only (`grep -rlF "<signal>" references/ --include="*.md"`): leaf exception class, error code, message fragments, resource keys. Signals are verbatim — a shorter fragment beats a guessed-case variant. Prefer hits under `*/playbooks/`; never read directories wholesale — open only the hits' `## Context` sections to check fit.

- **One dominant playbook** — most distinct signal hits; ties break by reading each hit's `## Context` and keeping the one whose preconditions fit the evidence; honor a playbook's explicit redirects to sibling playbooks. → Load ONLY that playbook + its domain's `investigation_guide.md` (if the domain has one). Go to §5.
- **Cross-domain signal** — evidence carries a key/ID/exception belonging to another product (e.g., an Excel fault wrapping an Integration Service connection error, an Orchestrator job spawned by a Maestro instance). → Follow the chain **one hop**: fetch the linked entity's error surface, extract its signals, re-grep. The upstream playbook drives the resolution; the downstream domain contributes a propagation fix (`references/presenting.md`). Deeper than one hop → escalate.
- **Fault signal but no grep hit** — map the faulting activity/exception namespace to its owning domain (`references/summary.md`) and check that domain's `summary.md` for a family playbook covering the activity. One dominant family playbook → proceed to §5 with it. Still nothing → escalate.
- **No match, or an escalation trigger (§7) fires** → load `references/escalation.md`. For silent failures (no fault signal anywhere: job Successful but wrong output, hang, stuck state), enter via the no-signature routing table in `references/summary.md`.

## 5. Walk the playbook

1. Read the playbook's `## Context` fully; confirm its signature actually fits the evidence (a contradicted core precondition = wrong playbook → back to §4 with that match excluded, recorded in notes.md).
2. Execute its `## Investigation` steps in decision-tree order; stop at the first matching branch. Record in notes.md the datum that rejects each rejected branch.
3. Ordering rules: most-specific branch first; run elimination checks, not just confirmation (fetch what would DISPROVE the branch); never conclude on a propagation/persistence/state-transition pattern while an upstream "why did that state occur" is unanswered — trace one hop upstream first.
4. **Source-required playbooks** (evidence lives only in workflow source, e.g. `VerifyOptions`, selectors, `project.json` pins): CHECK THE WORKING DIRECTORY TOP LEVEL FIRST — one listing; if it contains the project (`project.json` + the workflow named in the activity stack), use it without asking. A playbook-named file not at its standalone path may sit in the other layout — resolve both (solution wrapper at the working-directory root / one level up from the named project dir) per generic guide § Locating Project Source & Resource Files before treating it as missing; absence from one layout is not absence. Only if neither layout resolves, ask for the project path via `AskUserQuestion` — one question naming the files needed. This precedence overrides any playbook wording that says to ask first. Extract the verbatim attribute values the playbook lists; do not paraphrase.
5. **For large result sets**, summarize at write-time — group by type, count patterns, extract samples. Never slice raw responses with arbitrary limits.

## 6. Verification checklist — mandatory before presenting

Write the answers in notes.md; do not skip items, do not present without them:

1. **Cause named:** quote ONE item verbatim from the playbook's "What can cause it" list — not a category, not a vague generalization.
2. **Evidence pinned:** cite ≥1 datum (raw file + field) that singles out this cause from each sibling cause in the same list. Symptom-level data fitting several causes is not enough.
3. **Runtime evidence:** for runtime failures, ≥1 cited datum from runtime/platform data (logs, job records, instance state, incidents) that passes correlation. Design-time evidence alone (source files, manifests) proves a defect exists, not that it caused this failure. Every runtime query empty while the user reports active failures = CONTRADICTION — wrong scope; re-verify or ask, never conclude. If the contradiction persists and the user cannot be asked, present the contradiction itself as the finding (runtime evidence unreachable — root cause unconfirmed) — never re-attribute the failure to a design-time observation.
4. **Resolution aligned:** the fix is the playbook's `## Resolution` branch keyed to that exact cause.
5. **Causal precedence:** list every event the conclusion treats as given and answer "why did that occur?" — each answered by evidence, explained by the named cause, or explicitly out of scope. An upstream event may be ruled **out of scope ONLY if no documented command** (a matched playbook's `## Investigation` or an investigation guide) can retrieve the record that explains it; if such a command exists, running it is mandatory before concluding. A persistence/state-transition story (cancelled, stopped, orphaned, disconnected, timed-out) presupposes an upstream condition and is **never** the root cause while the record explaining it is reachable and unqueried; unexplained upstream → not root cause.
6. **Fix scope:** every proposed fix traces to the confirmed cause. A property or code path the failing run never evaluated cannot be asserted as a defect from source reading alone — and a defect claim that rests on how the platform parses or evaluates source syntax (expression bindings, escaping, argument direction) is unverified until confirmed against a playbook or documentation. Surface such suspicions as clearly-labeled unverified observations OUTSIDE the fix list — labeling one a "separate observation" while still listing it as a fix or offering to apply it violates this rule. The same gate applies to solutions: a fix must not presuppose infrastructure or mechanisms absent from the evidence (e.g., do not prescribe wiring an input to an Orchestrator asset unless an asset appears in the evidence) — prescribe the minimal evidence-supported fix; alternatives go as labeled options.

Any check fails → ONE targeted re-fetch for the missing datum. Still failing →

- **Diagnostic-recommendation terminal** (legitimate outcome, not failure): when evidence cannot separate sibling causes and the playbook provides a discriminating diagnostic (e.g., a byte-compare snippet), present at reduced confidence with that diagnostic as the primary deliverable — never silently pick a branch.
- Otherwise, or if a §7 trigger fires → escalate.

## 7. Escalation triggers

Load `references/escalation.md` when ANY of:

1. **No playbook grep match** — silent failure, hang, wrong results, nothing greppable.
2. **≥2 co-equal matches** with distinct, independent signatures (different activities/error codes, neither upstream of the other).
3. **Cross-domain chain deeper than one hop**, or the one-hop follow contradicts the original match.
4. **Decision tree exhausted** — every branch rejected, or a discriminator stays inconclusive after its named evidence is gathered.
5. **Checklist fails after the re-fetch** and no diagnostic-recommendation terminal applies.
6. **Evidence or new user data contradicts the matched playbook's core precondition.**

Escalation = 2–4 parallel read-only probe subagents (one per candidate playbook + one "origin is upstream/elsewhere") + your adjudication + a conditional fresh-eyes verifier. Protocol, prompt templates, and spawn budget: `references/escalation.md`. No subagent-spawning tool in this harness → same protocol, probes executed serially in this context (`references/escalation.md` § Serial fallback).

## 8. Present

Load `references/presenting.md` and follow it: fixes assembled for the root-cause domain and every propagation domain, every step source-cited, entity display names from raw data, the investigation summary table, and interactive resolutions (Healing Agent apply-flow) executed under the §1 approval gate.

## 9. New data from the user

New data mid-investigation (error messages, job IDs, logs) → re-run §2–§4 on it. If the new signals contradict the current match, that is trigger 6. Never patch new data into a concluded narrative.

## 10. Completion

After presenting and finishing any interactive actions: offer follow-up help and offer to delete or preserve `.local/investigations/`. If no root cause was found, offer via `AskUserQuestion`: provide more data (re-anchor) or open a UiPath support ticket with the evidence gathered.
