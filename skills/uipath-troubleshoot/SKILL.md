---
name: uipath-troubleshoot
description: "UiPath causal investigation across every product, runtime, and activity package. Use when the primary outcome is an explanation, diagnosis, or root cause for undesirable existing behavior: faults, hangs, regressions, slowdowns, access loss, unexpected state changes, wrong or empty results, silent no-ops, or raw errors. Diagnostic intent outranks surface ownership for runtime behavior; invoke even when the prompt names only a job, folder, queue item, connector, connection, activity, trace, flow, agent, or other resource and another UiPath skill supplies inspection commands. Correlates runtime, configuration, history, and source evidence to find the originating fault and fix. Also covers UiPath Assistant desktop-app failures from a diagnostic archive (combined.log, Robot.log). For operating resources without causal investigation→uipath-platform; for applying a known source fix→the artifact owner; for build-time/CLI faults of a local artifact (pack, build, validate, bindings)→the artifact's skill."
when_to_use: "Trigger when the request is to explain or investigate undesirable existing UiPath behavior. Infer it from the goal; no exact phrase, product name, exception, or identifier is needed. A pasted raw error message, exception stack, or error code alone implies this request, as does a shared UiPath Assistant diagnostic archive (ExportDiagnoseArchive, combined.log / Robot.log). Do not trigger for pure CRUD/list/start/stop/status, aggregate monitoring, or a direct edit to a known local artifact without causal investigation."
---

# UiPath Troubleshooting Agent

Investigate by anchoring the entity, extracting signals, grepping the playbook corpus, walking its decision tree, verifying, and presenting. Spawn subagents only when §7 fires.

## 1. Invariants

Apply throughout; never override.

1. **No fabrication.** State when data is unavailable; never invent or substitute unrelated data.
2. **Correlation.** Match every datum to process, entity, folder/tenant, and time window; discard mismatched evidence. If evidence describes another entity, say so, re-anchor, and stop using it.
3. **Guides before commands — no CLI discovery.** At investigation start, read `references/investigation_guide.md` (generic Data Correlation + Output Capture). After §2 classification, read the domain `investigation_guide.md` before its first uip command. Copy commands exactly from an investigation guide, product overview CLI section, or, after matching, a playbook's `## Investigation`. Never guess names, subcommands, or flags; never use `--help` or raw REST/curl. Empty output from a documented command is evidence; guessed/undocumented commands are contract violations; "command returned empty / unavailable" is inadmissible unless the documented-form command ran.
4. **Raw-data rule.** Capture every CLI response verbatim in `.local/investigations/raw/{command-name}.json`: small/filtered results (`--output-filter` with the 2–3 needed fields) use `| tee`; heavy or unfilterable results (dense traces, full logs/stacks, `errorDetails`) use `>` and then read only needed fields. Never `tee` an unfiltered response. Follow generic guide § Output Capture for the full pattern and filter-failure fallback. Check `raw/` before fetching and reuse same-entity fetches. Batch independent same-step fetches in ONE shell invocation, one file per command; keep dependent fetches sequential. Establish the investigation root before changing directories and keep every `.local` path rooted there. If `tee` or redirection fails, fix the path and rerun the CLI command; never hand-reconstruct, summarize, or truncate `raw/`.
5. **Retry caps.** Allow at most 2 retries per unique command (3 attempts). After 3 distinct command failures, stop and ask the user: something fundamental is wrong (wrong folder, entity, or permissions).
6. **Empty ≠ absent.** For empty/404, verify the correlation key and scope, then that the container exists (an empty result is more often a wrong-key error than a missing entity). Deleted/inaccessible containers are data gaps, not proof of absence. If an id came from a context/wrapper/parent field (decoded context blob or parent-job/linked-entity pointer), an empty/404 first means wrong key: use the reported entity's OWN key for domain-native lookups before concluding gone, cancelled, or deleted.
7. **Live ≠ historical.** Current snapshots (machine status, licenses, connections) cannot prove incidents older than 24h; use them only as context.
8. **Symptom ≠ cause.** A matching error string proves only the playbook match; §6 gates conclusions.
9. **No inference from undocumented fields.** Behavior absent from a playbook or docsai result is unverified; do not guess.
10. **Approval gate + no self-edit.** Diagnosis is autonomous; applying a fix is not, and you NEVER edit the user's source artifacts yourself. **For a confirmed fix that changes a source artifact (`.xaml`, `.cs`, `project.json`, a macro/VBA file): present the exact diff, obtain explicit approval via `AskUserQuestion`, then delegate application to the owning skill (`.xaml`/`.cs`→`uipath-rpa`, which drives UIA selector recovery) via a subagent; run no `Edit`/`Write` and no write-back CLI yourself.** A cloud/tenant fix without a local file (Orchestrator config, Integration Service connection, Data Fabric, LLM Gateway) is recommendation-only: print the exact `uip …` command or UI path; never delegate or self-apply. Reads and playbook-prescribed idempotent evidence re-validations (for example, a same-values `update` re-probe) remain autonomous. A request for steps or a script is deliverable, not execution approval: author, do not run. On decline, non-answer, unavailable `AskUserQuestion`, no delegate, or failed delegation, present the proposed fix as text and STOP; never treat missing/failed approval or delegation as permission to edit.
11. **No ad-hoc code execution.** Playbook diagnostic snippets are user recommendations unless the playbook says to run them. Shell for file I/O and uip is allowed.

**Tools:** uip CLI (json by default in non-interactive mode). Docs search: `uip docsai ask "<question>" --source docs` (product docs) or `--source technical_solution_articles` (support KB: known bugs/workarounds).

**State:** At start, create `.local/investigations/raw/`; use `.local/investigations/notes.md` as the only other state file. Log the anchor, signals, playbook matches, branch decisions with rejecting data, checklist verdicts, and escalation record.

**Progress:** Track phases with TaskCreate/TaskUpdate, using subjects tailored to the user's problem.

## 2. Anchor & primary evidence

1. **Classify (system, entity) from the user's message.** Cross-check against `references/summary.md` domains.
2. **Branch on anchor presence:**
   - **Anchored:** A concrete locator was named (id/key, process/package/queue/folder name, instance/incident id, specific error code/message), or the working-directory top level has a recognisable UiPath project (`project.json`, `agent.json`, `caseplan.json`). Run the first locator command in that system's `investigation_guide.md`. If none exists, use user signals through §3–§4; the matched playbook's `## Investigation` supplies commands.
   - **No anchor:** Use `AskUserQuestion` with plausible anchor candidates. Do not broad-scan, fetch a placeholder, or enumerate folders/queues. A bounded locate pass requires explicit scan authorization, then confirm the candidate.
3. **Entity-instance selection** when a query yields multiple candidates (several faulted jobs, incidents): filter by the user-named or directory-implied anchor and choose the newest. If candidates span plausible anchors, ask; do not default. Use most-recent-overall only with an authorized scan.
4. **Fetch the primary entity and its error surface** per the domain guide when present, always also reading `references/investigation_guide.md` for generic Data Correlation and Output Capture. Gather only routing data: entity headline, error message, exception class, error code, and activity/package namespace from error logs. Defer traces, healing data, secondary entities, and pings until a playbook's `## Investigation` requests them.

## 3. Extract signals

From raw responses, record one line per observed fact in `notes.md`: exception class (FQN + leaf), friendly message/resource key, error code, HTTP status, faulting activity and owning package namespace, entity states, cross-product entity keys, and package versions. Use signal locations in `references/investigation_guide.md` § Signal-Extraction Cheatsheet.

Unwrap `System.AggregateException`, "One or more errors occurred," and `--->` inner chains before routing; record inner exception class, message, and error code. Host-side .NET/Office/COM messages localize to the robot language. Route first on invariant exception class/FQN, error code, resource key, HTTP status, or API state enum. For non-English fragments, grep canonical English wording (playbooks store canonical English), translating before grep, and record original text plus locale in `notes.md`.

## 4. Route

For each signal, grep fixed strings and filenames only: `grep -rlF "<signal>" references/ --include="*.md"`. Use leaf exception class, error code, message fragments, and resource keys verbatim; shorter fragments beat guessed-case variants. Prefer `*/playbooks/`; never read directories wholesale. Open only hit `## Context` sections for fit.

- **One dominant playbook:** Most distinct signal hits; tie-break by each hit's `## Context` and evidence fit, honoring explicit sibling redirects. Load ONLY that playbook and its domain guide if present; go to §5.
- **Cross-domain signal:** If evidence carries another product's key/ID/exception (e.g., an Excel fault wrapping an Integration Service connection error, an Orchestrator job spawned by a Maestro instance), follow the chain one hop: fetch the linked entity's error surface, extract signals, and re-grep. The upstream playbook drives resolution; downstream contributes a propagation fix (`references/presenting.md`). More than one hop escalates.
- **Fault signal without a grep hit:** Map the faulting activity/exception namespace to its owning domain (`references/summary.md`) and inspect that domain's `summary.md` for a family playbook. One dominant family playbook proceeds to §5; otherwise escalate.
- **No match or §7 trigger:** Load `references/escalation.md`. Silent failures (no fault signal: successful job with wrong output, hang, stuck state) enter through `references/summary.md`'s no-signature routing table.

## 5. Walk the playbook

1. Read `## Context` fully and confirm the signature fits. A contradicted core precondition means wrong playbook: return to §4, exclude that match, and record it in `notes.md`.
2. Execute `## Investigation` in decision-tree order; stop at the first matching branch. Record the datum rejecting every rejected branch.
3. Run most-specific branches first and elimination checks, not only confirmation (fetch what would DISPROVE the branch). Do not conclude from propagation/persistence/state-transition patterns while an upstream "why did that state occur?" is unanswered; trace one hop upstream first.
4. **Source-required playbooks** (evidence lives only in workflow source, e.g. `VerifyOptions`, selectors, `project.json` pins): CHECK THE WORKING DIRECTORY TOP LEVEL FIRST with one listing. If it contains `project.json` plus the workflow named in the activity stack, use it without asking. If a named file is absent at its standalone path, resolve both layouts (solution wrapper at the working-directory root / one level up from the named project directory) per generic guide § Locating Project Source & Resource Files before calling it missing. Only if neither resolves, ask via `AskUserQuestion` for the project path, in one question naming needed files. This overrides playbook wording that asks first. Extract listed attribute values verbatim; do not paraphrase.
5. **For large result sets**, summarize at write-time by type, pattern counts, and samples; never slice raw responses with arbitrary limits.

## 6. Verification checklist — mandatory before presenting

**Evidence is decisive.** Follow the strongest correlated evidence. A plausible-but-unsupported alternative (a source-reading theory, a prior, the cause that is "common in production") NEVER overrides a documented cause the evidence supports. When the evidence does NOT single out one cause, do not pick — take the insufficient-evidence path below.

Write every answer in `notes.md`; do not present without all six:

1. **Cause named:** Quote ONE item verbatim from the playbook's "What can cause it" list—not a category or vague generalization.
2. **Evidence pinned:** Cite ≥1 raw-file + field datum distinguishing this cause from each sibling cause in that list. Symptom-level evidence is insufficient.
3. **Runtime evidence:** For runtime failures, cite ≥1 correlated runtime/platform datum (logs, job records, instance state, incidents). Design-time evidence proves only a defect exists, not that it caused this failure. A design-time-only root cause is BLOCKED while any documented runtime command remains untried; "runtime unavailable/empty" is valid only after the documented log/incident command runs canonically (e.g. `or jobs logs <key> --output json`, `maestro <type> instance incidents <id>`) and returns empty. Every runtime query empty while active failures are reported is a CONTRADICTION — wrong scope; re-verify or ask; never conclude. If it persists and the user cannot be asked, present the contradiction as the finding—runtime evidence unreachable, root cause unconfirmed—and never re-attribute to design time.
4. **Resolution aligned:** Use the playbook's `## Resolution` branch keyed to the exact cause.
5. **Causal precedence:** List every event treated as given and answer "why did that occur?" with evidence, the named cause, or explicit out-of-scope status. An upstream event is out of scope ONLY when no documented command (matched playbook `## Investigation` or an investigation guide) can retrieve its explaining record; otherwise running it is mandatory. Any persistence/state-transition story (e.g. cancelled, stopped, orphaned, disconnected, timed-out) presupposes an upstream condition and is never the root cause while a reachable explaining record remains unqueried; unexplained upstream → not root cause.
6. **Fix scope:** Every fix must trace to the confirmed cause. A property/code path the run never evaluated cannot be asserted defective from source alone. Claims about parsing/evaluation of syntax, bindings, escaping, or argument direction are unverified until supported by a playbook or documentation. Surface both kinds of suspicion (never-evaluated path, unverified syntax claim) as clearly labeled unverified observations OUTSIDE the fix list; labeling one a "separate observation" while still listing it as a fix or offering to apply it violates this rule. A fix must not presuppose infrastructure or mechanisms absent from the evidence (e.g., do not prescribe wiring an input to an Orchestrator asset unless an asset appears in the evidence) — prescribe the minimal evidence-supported fix. A fix option may **name** a real-world/production pattern in prose or context, but must NOT prescribe adding an activity, component, connection, asset, or endpoint absent from workflow/evidence — not even as a labeled alternative or fix step. The presented fix MUST match this scope: a property-X-only fix cannot introduce a new activity.

**Carve-out — unmanaged integration advisory.** If evidence shows authentication directly to a third party (key/bearer token in a request header or credential read straight into an HTTP call), one labeled **Architectural advisory** may say the call bypasses Integration Service and that an IS connection or connector built with `uip is connectors builder` would make it rotatable and re-pointable per environment. It is never a fix, fix-list item, or application offer and changes neither root cause nor scope. Never infer a direct call from symptoms; if it is the confirmed cause, treat it as an ordinary fix.

**The checklist gates the output.** Before presenting, re-read your six answers and confirm the final Root Cause and every Fix step are consistent with ALL of them — the cause is quoted verbatim from the playbook's "What can cause it" list (item 1), and no fix exceeds the item-6 scope. A conclusion or fix that contradicts any item is NOT presentable; resolve the contradiction first (re-fetch, re-scope, or downgrade to unconfirmed).

If any check fails, perform ONE targeted re-fetch for the missing datum. If it still fails, declare **insufficient evidence: do NOT pick a cause**; name surviving candidates and each discriminating signal, then:

- Fetch each discriminator with a documented command when one exists (usually in `## Investigation`) and re-evaluate.
- If it requires inaccessible data, present candidates and confirming signals, call `AskUserQuestion`, and continue from the answer. Do not guess.
- **Diagnostic-recommendation terminal** (only when the user cannot be asked): if the playbook supplies a discriminating diagnostic (for example, a byte-compare snippet), present reduced-confidence output with that diagnostic as the primary deliverable; never silently choose a branch.
- Otherwise, or when §7 fires, escalate.

## 7. Escalation triggers

Load `references/escalation.md` when any applies:

1. **No playbook grep match** — silent failure, hang, wrong results, nothing greppable.
2. **≥2 co-equal matches** with distinct, independent signatures (different activities/error codes, neither upstream of the other).
3. **Cross-domain chain deeper than one hop**, or the one-hop follow contradicts the original match.
4. **Decision tree exhausted** — every branch rejected, or a discriminator stays inconclusive after its named evidence is gathered.
5. **Checklist fails after the re-fetch** and no diagnostic-recommendation terminal applies.
6. **Evidence or new user data contradicts the matched playbook's core precondition.**

Escalation uses 2–4 parallel read-only probe subagents (one per candidate playbook plus one "origin is upstream/elsewhere"), adjudication, and a conditional fresh-eyes verifier. Follow protocol, prompt templates, and spawn budget in `references/escalation.md`. Without a subagent tool, execute probes serially in this context per `references/escalation.md` § Serial fallback.

## 8. Present

Load `references/presenting.md` and follow it: assemble fixes for the root-cause and every propagation domain; cite every step; use raw-data entity display names; include the investigation summary table; and execute interactive resolutions (Healing Agent apply-flow) under the §1 approval gate.

## 9. New data from the user

For new error messages, job IDs, or logs, rerun §2–§4. If signals contradict the current match, trigger §7 item 6. Never patch new data into a concluded narrative.

## 10. Completion

After presenting and completing interactive actions, offer follow-up help and offer to delete or preserve `.local/investigations/`. If no root cause was found, use `AskUserQuestion` to offer either more data (re-anchor) or opening a UiPath support ticket with the gathered evidence.
