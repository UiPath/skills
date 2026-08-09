# Phase 0 — Interview Mode (case design)

This file is a **thinking guide** for the agent: how to listen, assume, confirm once, and hand off fast when no `sdd.md` is provided. Phase 0 designs the case in the session's **in-memory model**; `sdd.md` is rendered from that model in parallel with the first build actions — a reference artifact, never a review gate.

> **Authoritative for the interview path only.** Trigger detection, mode behavior, confirmation, resumption, output contract. **Content rules** (authority hierarchy, task-type override priority, render-required fields, variable lineage, review items, source ledger) live in [sdd-generation-rules.md](sdd-generation-rules.md). Phase 1 logic lives in [planning.md](planning.md). Phases 2–6 live in [phased-execution.md](phased-execution.md).

## Goal

Design the case as an in-memory model shaped by [`assets/templates/sdd-template.md`](../assets/templates/sdd-template.md), confirm it in ONE user prompt, then start the build. Phase 0 is **best-assumption by default**: it decides everything it can from the user's words and documents, and *informs* the user of every decision — it does not interrogate. `sdd.md` renders from the confirmed model concurrently with the first build actions. For later sessions and re-runs the file is the contract (Rule 2: trust as written); within this session, the in-memory model that produced it drives the build.

**The Phase 0 confirmation IS the plan-first approval surface.** If workspace or project rules require "show a plan before editing," satisfy that requirement by showing the structured §Confirm case-design summary below. Do not insert a separate generic implementation plan, "Build Plan," or "Approve this plan" checkpoint before §Confirm. A user "Yes" to a generic implementation plan is not a Build answer and must not create files.

Phase 0 writes:

- `sdd.md` — rendered once from the confirmed model, batched with the first build actions (or written and reported when the request was design-only).
- `sdd-viewer.html` — optional, generated only on explicit request (§HTML preview).
- `sdd.draft.md` — ONLY when the user explicitly asks for a draft to review; normal runs never create it. If the request explicitly says to get/save the draft and stop, show the Case Review and write the draft in the same response instead of asking for another approval. `tasks/registry-resolved.json` is a Phase 1 artifact — Phase 0 does not write it.

**Fast path — no-build design + plan.** If the opening request explicitly asks to produce `sdd.md` plus `tasks/tasks.md` and stop before `caseplan.json`, follow §Build start's **No-build design + plan request** path immediately after sketching the case. This path is self-contained: do not read `planning.md`, plugin planning references, tenant registry/cache files, or the full `sdd-generation-rules.md` checklist. Read this file plus `assets/templates/sdd-template.md` only as needed, compose a concise full-template SDD, write `sdd.md`, create `tasks/`, write the compact plan, and stop. Keep the artifacts bounded: one short rationale paragraph per stage/task/SLA/exception choice is enough; do not expand optional examples, source-ledger prose, registry audit detail, or build-phase validation notes.

## When Phase 0 runs

Strict binary trigger. Look for an `.md` file at the resolved path whose basename (case-insensitive) contains `sdd`. Examples that count: `sdd.md`, `loan-sdd.md`, `case_demo_sdd.md`, `./specs/onboarding-sdd.md`. Plain `.md` references without `sdd` in the name don't count.

| State | Action |
|---|---|
| File present, basename = `sdd.md` | Skip Phase 0. Hand to Phase 1. |
| File present, basename ≠ `sdd.md` | Copy contents to `./sdd.md` (preserve original at its path). Skip Phase 0. Hand to Phase 1. |
| File absent, `sdd.draft.md` present | Resume (§Resumption). |
| File absent, no draft | Run Phase 0 from scratch (§Entry). |

If the user prompt names no `.md` reference, default candidate is `./sdd.md` — proceed on that assumption and record it as a decision; do not ask.

## Entry

**If the user's request already describes the case** (any stages, work, trigger, domain, or attached docs), skip every entry prompt: print the roadmap from `SKILL.md § User-facing roadmap` and go straight to work — the request IS the first Listen input. **Only a bare request** ("create a case" with nothing else) gets the Listen opener after the roadmap. There is no entry menu; a user who has an `sdd.md` will say so, and abort is always a free-text away. If the same request also asks for `tasks.md`, do not read planning/plugin references yet; first show the Phase 0 Case Review and get the Build / Save approval.

**No tenant work at Entry.** Nothing about the tenant is a prerequisite for designing the case — do not run login or `registry pull` up front. Grounding starts only when the case shows it needs it (§Tenant grounding).

## Tenant grounding — requirement-driven, one light pass, no questions

Phase 0 grounds resources lazily, in parallel with the design, with a **single name-match pass** at most. Schema discovery (`tasks describe`, `case spec`) belongs to the build phases — never run it in Phase 0.

1. **Intake batch.** Read every supplied document in parallel. Extract named systems, resources, likely tasks, and roles.
2. **Requirement-driven kickoff.** For build runs only, the FIRST moment the sketch identifies tenant-bound work — a named system/resource/connector, or an inferred runnable/connector/action task — start the grounding chain as ONE background command, in the same batch as whatever is already running: `uip login status --output json && uip maestro case registry pull`. It resolves while sketching continues; a case with no tenant-bound items never pulls in Phase 0. Best-effort: never block on it, never surface its output unprompted; on failure, one plain-language line (§What to say while working), keep intended names, mark identities `resolve at build`, continue. If the harness cannot run background commands, run login → pull in the batch that composes the confirmation. **No-build runs skip grounding:** when the user explicitly asks to stop at a draft, final SDD, or implementation plan and not create `caseplan.json`, do not run login, registry, connection, schema, or user-discovery commands in Phase 0; preserve concrete intended names and mark identities `resolve at build`.
3. **Light match pass — join, never wait.** When composing the confirmation, check the chain. If the pull succeeded, run ONE cache lookup per named or inferred resource (`~/.uip/case-resources/<type>-index.json`; `action-apps-index.json` for HITL apps; `typecache-activities-index.json` / `typecache-triggers-index.json` for connectors) — all lookups in one parallel batch. With ≥ 4 lookups, use parallel read-only workers where supported (one per item or type family; cache reads only — never writes, never prompts, never login/pull; parent spot-verifies adopted identities). Bucket each result:
   - **Single confident match** (1 match across all folders, ≥ 1 shared name token) → adopt silently; shows as the task's resource in the confirmation with a decision line.
   - **Anything else** (multiple matches, cross-folder same-name, no token overlap, zero matches, 0 or > 1 enabled connections for a connector) → mark `resolve at build`. Do NOT ask, do NOT auto-pick among candidates, do NOT fetch schemas. Phase 1's discovery and its Rule 17 gate handle the choice with full authority.

   If the pull has NOT finished when the confirmation is ready, do not wait: present with `resolve at build` on the tenant-bound items and let the build reconcile — the confirmation is never delayed by the tenant.

**Guardrails:** registry data is evidence, not requirements — never add/rename business work to match tenant inventory; never dump catalogs; keep type-specific portable names concrete (`Resolved Resource`, Action App title, `Child Case`) even when identity defers; a connector with zero connections is `resolve at build`, not a reason to change the task type. A no-build run does not need tenant evidence to be useful; the later build run owns authoritative identity resolution.

## Modes

Three moves. **Listen** takes in everything offered; **Sketch** builds the complete case model by best assumption, recording every decision; **Confirm** shows the whole case once with the decisions taken and asks a single question — on a Build answer, the build starts and `sdd.md` is written alongside it (§Build start). Listen and Sketch loop freely as new context lands; there is no separate Resolve or Approve pass.

### Listen

The opening move for a bare request. One message, one prompt:

> Tell me about the case you want to build. What kicks it off, what stages does it move through, and how does it close out? Drop in any docs you have — paths, paste, or attach.

What the agent does as input arrives:

- **Reads everything mentioned.** Path, dragged file, named doc → read immediately, in parallel when multiple. "Everything in `~/process-docs/`" → `ls` + parallel Reads.
- **Narrates content, not filenames.** One short line per doc about *what's in it*: `vendor-onboarding.md — 4 stages (Intake → Compliance → Finance → Activation), 2 personas, 8-hour SLA on Compliance.`
- **Partial reads for huge docs.** Past ~2000 lines, read the first chunk, narrate the signal, decide if more is needed. Unreadable formats (`.docx`, `.pptx`, scanned PDFs) → one paste request; PDFs ≤ 10 pages read directly.
- **Mid-flow docs are first-class.** New doc after the sketch exists → re-read, update the model, narrate the delta.
- **Named systems seed grounding.** Deployed resources, apps, connectors, systems named by the user feed the §Tenant grounding light pass.

Listen asks nothing beyond the opener. Gaps are filled by assumption in Sketch, not by questions.

#### Domain-vocabulary capture (during Listen)

Capture verbatim into the model: **roles** (exact casing — `CFO`, `Triage Nurse`), **domain nouns** (`Vendor` vs `Supplier` — never homogenize), **stage labels**, **decision outcomes** (`Approve` / `Decline` / `Needs Info`, not synonyms), **integration shortnames** (`Workday`, never "the HR system"). Provenance `verbatim:"<quote>"` per [sdd-generation-rules.md § Source ledger](sdd-generation-rules.md#source-ledger-provenance). Synonym drift is a fidelity defect ([§ Domain fidelity](sdd-generation-rules.md#domain-fidelity)).

#### File / attachment / document detection (during Listen)

When the user mentions `file`, `attachment`, `PDF`, `upload`, `evidence`, `receipt` (as artifact, not domain noun), pick the best-matching pattern from the indicators and record the decision — ask only if the user's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file` — Use Case 9; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row — Use Case 10. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

### Sketch — best assumption, every field

Fill the complete SDD shape against [`sdd-template.md`](../assets/templates/sdd-template.md) from what Listen captured, deciding every open field by best assumption. Authority order per [sdd-generation-rules.md § Content authority hierarchy](sdd-generation-rules.md#content-authority-hierarchy) — platform schema and compliance constraints override user phrasing (apply the override silently; it becomes a decision line). Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. Every stage, task, and configured SLA also gets a durable `Design Rationale` in the model explaining the kind/type, activation/sequencing, and routing/threshold choice; the confirmation summarizes it but does not replace it. The model lives in memory — **no draft file, no checkpoint writes**; `sdd.md` is written later at build start.

**Assumption playbook** (former ask-list, now decided and disclosed):

| Field | Best assumption |
|---|---|
| Trigger type | External system / portal / form / inbound event / record-created mentioned → **Connector Event** with that source (unprovisioned tenant object stays an event trigger — never downgrade to Manual); schedule/recurring → **Timer**; otherwise → **Manual**. |
| Task type on ambiguous verbs (`review`, `approve`, `validate`, `decide`, …) | Named human role or judgment implied → `action`; framed as automated/AI → `agent`; truly even → `action` (keeps a human in the loop; the user can flip it in one correction). Compliance trigger phrase (HIPAA, ECOA, FINRA, "licensed X", …) → `action`, always ([§ Task-type override priority](sdd-generation-rules.md#task-type-override-priority)). |
| "Manual" in-case work | Starts a new case → Manual trigger; optional worker-launched task → `adhoc` + `Required: No`; worker-chosen exception/rework lane → secondary stage with `user-selected-stage`. Pick by context; disclose. |
| Case exit | Last primary stage completes (`required-stages-completed`, `Marks Case Complete: Yes`) unless the user described another close-out; alternate outcomes → non-completing case-exit rules. |
| Stage exit ↔ Marks Complete pairing | Derive mechanically per sdd-template Key Rule 4 — never author an illegal pair. |
| SLA | Only when the user mentioned timing; take their words literally ("about a day" → 1 day). No timing mentioned → `—`. For every SLA, decide scope, status, and response separately (§ SLA response model). No stated response → `notify-only` for both statuses; never invent a stage or task for a notification. |
| Case name / prefix | PascalCase from the domain noun; prefix = 2–4 letter mechanical derivation. |
| Personas | Named roles verbatim; none mentioned → single `Process Owner`. |
| Optional fields untouched by the user | `—`. Never a question. |
| Resources / connections | §Tenant grounding light pass: single confident match adopted, everything else `resolve at build`. |

**Structure rules while sketching:** §1.5 declare-vs-xref — mint a §1.5 row ONLY for `In`/`Out` args, trigger-payload Variables, and state read by a condition or ≥ 2 consumers; a single upstream output feeding one consumer is referenced directly (`<- "Stage"."Task".out` / `vars.$xref(...)`), never relayed. Required fields (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit) must all be settled — by user input or by playbook assumption.

**Conditional role / step gates must be inspectable.** When the source states a thresholded actor or step (for example, "Credit Analyst only over $5M; otherwise Underwriter"), model it as a guarded rule, task, recipient, or computed owner field AND preserve the business phrase close to the threshold in the draft/SDD text. A reviewer and a mechanical grep should be able to see both the actor name and threshold in one rule/task/rationale line, e.g. `Credit Analyst route when loanAmount > 5000000` or `Credit Analyst for loans >$5M; Underwriter otherwise`. Do not leave the gate only in a persona table or detached prose.

**Other-path sweep — mandatory before confirmation.** Do not design only the primary flow and wait for the user to ask about alternatives later. Check the source for: rework / needs-info loops; rejection, withdrawal, and cancellation; SLA escalation; external-system failure; manual override or worker-selected side work; optional side work; and terminal outcomes that differ from successful completion. For each scenario, choose the correct model: interrupting secondary stage, terminal case-exit, non-completing case-exit, task-level branch, `adhoc` task, SLA notification only, or "not modeled" when the source explicitly rules it out. If the source names or strongly implies a scenario, model it by best assumption and disclose it in **Other Paths Considered**. If the source has no signal at all, spend the one clarifying call on a single bounded question before confirmation: "I don't see any other paths beyond the primary flow. Should I add standard paths for rework, cancellation/withdrawal, SLA escalation, or keep only the primary flow?"

**Buildability musts** — settle all ten by assumption and surface each in the confirmation; they are where designs silently become unbuildable: (1) other-path trigger source (gate decision → `selected-stage-completed/-exited` + IF; person → `user-selected-stage` only with an upstream `wait-for-user` exit; external/global event → one `wait-for-connector` entry on the secondary stage; SLA at-risk/breach that requires case work → one `sla-status-change` entry whose target and SLA title — plus an at-risk escalation title for an at-risk row only — are declared in the SDD, while warning-only escalation stays a notification; interrupting flags on stage + entry rows; terminal `exit-only` vs `return-to-origin`; never duplicate global-event exits/tasks across primary stages); (2) every decision outcome routes somewhere — no dead-end status values, and an outcome that targets a lane keys that lane's entry; (3) every configure/decide task's output lands in a variable or direct reference; (4) every send/connector/agent's required inputs map to variables/literals/upstream outputs as far as knowable without schemas — the rest resolves at build; (5) conditional roles/steps become guarded rules + personas, not prose, with the actor and threshold visible together in the draft/SDD; (6) a critical-path connector failure gets a modeled other path when the user described failure handling — otherwise note it as an architect advisory; (7) manual-surface classification per the playbook: human-performed required work is `action`, optional user-launched work is `adhoc`; (8) intended resource names concrete, identities per the light pass; (9) every stage/task/SLA has durable rationale in the model, including why an ordered run is sequential, independent work is parallel, or parallel-after-predecessor siblings share one task set; (10) every non-start entry rule has a concrete producer/reference.

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, (c) the user asked to be asked, or (d) the mandatory other-path sweep found no source signal at all. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" / "this resource has two matches" — STOP: the playbook decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in Phase 0 are the one clarifying call (when earned), the confirmation itself, and the explicit-sign-off path.

### Confirm — the single checkpoint

One structured **Case Review**, one question. Run the [sdd-generation-rules.md § Finalization](sdd-generation-rules.md#finalization) checks against the in-memory model FIRST — fix failures silently (they are the agent's defects, not the user's decisions); anything unfixable becomes a Review Flags row. This is the business approval surface and must be complete enough to approve the case behavior without opening `sdd.md`. It is a decision-first review, not a generic build plan or a compressed copy of the SDD.

**Coverage map:** SDD Section 1 (case definition) → Case Snapshot + SLA and Escalations + Rules and Outcomes; SDD Section 2 (stages/tasks) → Primary Journey + Other Paths Considered + SLA and Escalations + Rules and Outcomes; SDD Section 3 (personas/views) → Case Snapshot + Human action labels in the journey/path tables + action apps in Resources and Integrations; SDD Section 4 (integrations) → Resources and Integrations. The Case Review intentionally omits the data contract, variables, and task inputs/outputs; those technical details remain complete in `sdd.md`. Anything with a High review item in the SDD model also appears in Review Flags.

Start with `## Case Review: <Case name>`, then use this exact section order:

1. **Case Snapshot** — table `Item | Proposed design`. Include `Objective`, `Starts when`, `Primary personas`, `Successful completion`, `Other terminal outcomes`, and `SLA coverage`. Mark assumed values with `(assumed)`. Do not show the case ID prefix unless it affects a user decision.
2. **Primary Journey** — table `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? | SLA`. Include every primary stage once, in flow order. The `Tasks` cell names every task in execution order and shows task type, required/optional status, and activation/grouping. Preserve sequence and joins, for example: `Sequential: Capture request (Human action, required) → Validate request (RPA workflow, required)`; `Parallel: Risk review (Agent, required) + Compliance review (Human action, required)`; `After both: Make decision (Human action, required)`. Show event-triggered and manually triggered tasks explicitly.
3. **Other Paths Considered** — table `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active work? | Return or case outcome | Rationale`. Include every modeled exception, secondary stage, optional path, and alternate terminal route. Also include standard paths intentionally left unmodeled when that omission is a design decision. Name each path task with its type, required/optional status, and activation/grouping.
4. **SLA and Escalations** — table `Scope | SLA | Time target or condition | Status or threshold | Response | Response target | Interrupts active work? | Rationale`. Include one row per meaningful `(scope, SLA, status)` combination, including separate at-risk and breached rows when both exist. Use only `notify-only`, `start-task`, `enter-stage`, `exit-stage`, or `exit-case` as the response. Name the notification, task, stage, or outcome in `Response target`; use `N/A` for interrupting behavior when the response is `notify-only`, and `No` for `start-task`. Do not assume every breach creates an escalation stage. Show `None` when the case has no SLA.
5. **Rules and Outcomes** — table `Scope | Element | Rule | When | If | Then`. Include only business-significant routing, completion, and terminal rules. Omit generated sequencing already visible in `Tasks`, and do not repeat SLA rows unless the rule is needed to understand routing. Business conditions belong in `If`; do not add a data or variable column.
6. **Resources and Integrations** — table `Task | Intended resource or system | Resolution`. Include action apps, agents, RPA/processes, API workflows, child cases, connectors, and named external systems. `resolve at build` is acceptable; a missing row is not.
7. **Decisions I Made** — table `Decision | Why | Provenance`. Include every assumption, override, resource decision, task-type decision, activation/sequence decision, and intentionally omitted path. Use plain-language provenance (`you said "then"`; `compliance wording`; `no SLA mentioned`). Group decisions only when they share the same rationale and provenance. Do not repeat facts already clear in another section unless the choice itself needs approval.
8. **Review Flags** — table `Item to review | Why it matters | Default if accepted`. Show `None` when empty. Include unfixable Finalization findings, missing connections, unresolved high-impact choices, and any item the user should inspect before approving.

After Review Flags, show the **Caller obligation** fixed text when any §1.5 row is `Category: In` + `Type: file` (JobAttachment pre-create contract; Studio Web's "Start case" dialog handles it automatically). Omit it otherwise. It is a conditional build obligation, not a ninth review section.

**Product vocabulary.** Use these user-visible activation labels consistently: `Sequential`, `Parallel`, `Parallel after predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, and `Conditional gate`. Map SDD/tasks.md `event-triggered` to `Event-triggered`, `adhoc` to `Manually triggered`, and `parallel-after-predecessor` to `Parallel after predecessor`. Prefer product-facing task labels such as `Human action`, `Agent`, `RPA workflow`, `API workflow`, and `Child case` over schema enum names in the review.

**No duplicated review surfaces.** Each business decision appears once. Do not add a Data Contract section, variable rows, task input/output rows, a second stages list, or per-stage/per-task detail cards. Keep the full technical contract and per-stage/per-task detail in `sdd.md`.

**Completeness gate.** The confirmation is incomplete unless it contains all eight sections, names every stage and task, covers every modeled and intentionally omitted path, shows every meaningful SLA response/status row, and includes Caller obligation when relevant. Do not ask `Build it...`, `Save...`, or any approval question until every section has been shown, even when a section says `None` or `Not used`. Do not replace this confirmation with a generic list of build steps, artifact names, output folder, validation commands, resource-placeholder caveats, or a summary that points to `sdd.md` for a missing business decision.

Confirmation question (AskUserQuestion): `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. The build choice records the Rule 11 preference — never re-asked mid-build. When ⚠ flagged items exist, relabel the first option `Build despite N flagged items — straight through`. For a **design-only** request swap the build options for `Save the design`; for a **draft** request, `Save as draft`. If the user's initial prompt already says to get/save a draft and stop, treat that as the `Save as draft` answer after the Case Review: write `sdd.draft.md` immediately and stop. The draft still uses SDD section/stage/task headings so a reviewer can inspect it directly.

Corrections (`Change something` or any free text) update the model, re-run affected Finalization checks, and re-show ONLY the changed Case Review sections or rows: snapshot, journey, other paths, SLA responses, rules, resources, decisions, and review flags. A correction never restarts the walk. After showing the changed sections, include a short `Suggested next steps` line before the next confirmation prompt, e.g. `Suggested next steps: approve the updated design, choose preview pause if you want a visual checkpoint, or change another part of the case.`

**Explicit sign-off requests** ("only after I approve", "I'll review before you build") suppress nothing about the flow but add one explicit approval prompt after the confirmation is accepted and before any file is created — honor it exactly.

### Template conformance gate — before `sdd.md` is written

The exact rendered text for `sdd.md` must pass this gate before Write. This is a render check, not a second design review: run it against the in-memory text you are about to write; if the harness makes that impossible, do one shallow post-write structural Read before Phase 1. Do not use the read to redesign the case.

Required shape:

- First heading: `# SDD — {Case Name}`.
- `## Table of Contents`.
- Exact section headings: `## Section 1: Case Definition`, `## Section 2: Stages & Tasks`, `## Section 3: Personas & App Views`, `## Section 4: Integrations`.
- Section 1 contains `### Case Metadata`, `### Case Triggers`, `### Case Exit Conditions`, and `### Case Variables`.
- Every modeled primary stage has `### Stage {N}: {Stage Name}`; every modeled secondary stage has `### Secondary Stage: {Stage Name}`.
- Every stage block contains `**Type:**`, `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, and `#### Tasks`.
- Every modeled primary-stage task has `##### Task {N}.{M}: {Task Name}`; every modeled secondary-stage task has numeric secondary numbering `##### Task S{K}.{M}: {Task Name}` where `K` is the secondary-stage order. Do not preserve letter prefixes such as `R.1`, `W.1`, `CC.1`, or `ESC.1`. Each task block contains `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, `**Entry Condition:**`, exact marker `**Task envelope**` (no colon), and the matching type-specific detail block.
- Section 3 contains `### Personas` and `### Process App Views`.
- Section 4 contains the integration/resource family headings needed by the modeled task types, or an explicit `> None.` for empty families.

Forbidden summary-only replacement sections at top level: `## Source`, `## Case Objective`, `## Actors And Systems`, `## Case Trigger`, `## Stages`, `## Business Rules`, `## Task Plan`, `## Resource Resolution`, `## Acceptance Scenarios`. Their presence as the main document structure means the SDD is a summary, not a template render. Also forbid source/build-mode/path narration such as `Source: /...`, `Build mode`, `output folder`, validation-command checklists, or "generated from requirements file" prose in the SDD body.

If the gate fails, rewrite from the model and template before Phase 1. Do not proceed to planning on a summary SDD, even if a later `caseplan.json` would validate.

### Build start — SDD written alongside the build

On a Build answer:

1. **Transition line** (§What to say while working): `Starting the build — the design doc will be saved alongside as a reference. Say stop anytime.`
2. **Render gate first:** compose the full SDD text from `assets/templates/sdd-template.md` and pass §Template conformance gate. This is the only allowed pre-write SDD check.
3. **One parallel batch:** Write `sdd.md` (full render from the confirmed in-memory model — direct Write, no draft, no rename) + `uip solution init <SolutionName>` (derived exactly as Phase 2 Step 6.0 does; its idempotent skip then applies) + Phase 1's Rule 3 `uip login status` → `registry pull` chain **only if Phase 0's pull did not already succeed this session** — a same-session successful pull is reused, never repeated (SKILL.md Rule 3 fast path). The SDD write is NEVER a standalone blocking turn — it always shares the batch with build actions.
4. **One artifact line** after the write lands: `Design doc saved to ./sdd.md — reference it anytime.`
5. Proceed into [planning.md](planning.md) Step 1 **from the in-memory model** — do not re-read the just-written `sdd.md` in this session except for the shallow template-conformance check described above. Re-read it only when working memory may be stale (context compaction, resumed session); then the file is authoritative (Rule 2). For later sessions and re-runs, `sdd.md` is the contract exactly as if the user wrote it.
6. If `sdd.md` appeared at the path since Phase 0 started, abort instead of overwriting.

**Design-only request:** write `sdd.md`, report the path in one line, stop before Phase 1. **Draft request:** write `sdd.draft.md`, report, stop — never promote. **Free-text corrections stay first-class after the build starts:** treat one as a targeted edit to the affected artifact (model + `sdd.md` + downstream), narrate it in one line, continue.

**No-build design + plan request:** when the prompt explicitly asks for `sdd.md` plus `tasks/tasks.md` and says to stop before creating `caseplan.json`, do not enter full Phase 1 and do not read `planning.md` or plugin planning references. If the same prompt already says to produce those artifacts and stop, treat it as the save instruction: show the Case Review, then write the full `sdd.md`, create `tasks/`, write compact `tasks/tasks.md`, and stop in the same response without asking for another approval. If the user only asked to review the plan first, wait for approval before writing. The compact plan is a review handoff for a later build run, so it omits registry-derived files and tenant evidence.

For this no-build path, prefer progress over exhaustive internal auditing: once the case model covers the stated stages, tasks, global interrupts, SLAs, variables, resources, and rationales, write the artifacts. Do not run the full Finalization checklist, do not inspect schema/planning references, and do not spend a separate turn refining optional SDD prose. The artifact contract below plus the template conformance shape are the gate.

The full-template requirement still applies in no-build mode: every task's `**Entry Condition:**` is followed by the template's `| WHEN | IF | Display Name |` table. Do not collapse an executable task gate into inline prose on the heading line; doing so drops the condition from the later planning handoff. A source rule that depends on a business attribute or threshold (for example, department- or seniority-gated eligibility) must be represented in an executable condition, output mapping, or guarded recipient/assignment expression, not only in a Design Rationale.

Compact `tasks/tasks.md` contract for this no-build path:

- Use T-numbered entries for the case root, triggers, variables/arguments, stages, tasks, entry/exit/condition rules, and SLA/escalation rules that matter to the design.
- Use machine-scannable task headings in the plan: `## T{N}: task "{Task Name}"`. Do not hide task T-entries under dotted subheadings such as `### T12.1`; nested prose is allowed under the H2, but the task entry itself uses a plain integer T-number and quotes the task name.
- Stage entries include `stage-kind`, `entry-rule`, `exit-rule`, `interrupting`, `required`, `sla`, and `rationale`.
- Task entries include `stage`, `type`, `activation-mode`, `entry-rule`, `lane`, `required`, `run-only-once`, `resource-intent`, `identity: resolve at build`, and `rationale`.
- Preserve each task's confirmed SDD activation semantics exactly. A singleton task that starts with its stage remains `activation-mode: parallel` + `entry-rule: current-stage-entered`; a single-task stage or list position does not make it sequential. Use `sequential` + `runs-sequentially` only when the source explicitly requires an ordered run or dependency.
- Sequential runs use consecutive single-task lane numbers; every task in the run has `activation-mode: sequential` and `entry-rule: runs-sequentially`.
- When the prompt says every primary phase/stage has an SLA target, every named primary stage renders its own `#### Stage SLA` block with a concrete `**SLA Title:**` (prefer `<Stage Name> SLA`) and concrete at-risk/breach display names. Every `sla-status-change` reference uses those exact titles. Keep per-stage SLA tables consistent with the SLA Response Map: a breach row routes to its declared interrupting response (the `sla-status-change`-entered secondary stage), never to a notify-only action; notify-only rows are at-risk warnings.
- Global event/exception entries name exactly one interrupting secondary stage and the rule type (`wait-for-connector` or `sla-status-change`); do not duplicate those events across every primary stage. A `sla-status-change` entry names target + SLA title, plus an at-risk escalation title only for an at-risk row (a breach names the SLA alone) — all declared in the SDD and repeated verbatim in `tasks/tasks.md`.
- Do not add `taskTypeId`, `activityTypeId`, `connectionId`, resolved schemas, `inputs`, `outputs`, `registry-resolved.json`, or `recipients-resolved.json`.
- MANDATORY final gate: the plan is not deliverable until the skill's deterministic audit prints `AUDIT OK` (read-only; not a Rule-13 violation): `python3 "<this skill's folder>/scripts/audit_plan.py" tasks/tasks.md --sdd sdd.md`. On `AUDIT FAIL`, fix each finding with Edit and re-run; max 3 rounds, then surface the remaining findings. Quote the final `AUDIT OK` line in the reply as evidence. If `python3` is unavailable, re-check headings and per-task fields against this contract manually.
- End the response with suggested next steps: review the SDD/plan, then run a later build to resolve tenant resources and create `caseplan.json`.

## HTML preview

Optional, **on-request only** — never offered proactively. Available any time after the confirmation exists, including mid-build. Self-contained local HTML: Case Definition, collapsible Stages & Tasks with detail panels, Personas & App Views, Integrations; persona/type filters, unresolved-only and schema-view toggles, search, print stylesheet.

Generation: Read [`assets/templates/sdd-viewer.html`](../assets/templates/sdd-viewer.html), replace the `__SDD_DATA__` token in its `<script id="sdd-data">` block with JSON serialized from the in-memory model (schema in the template's header comment — do NOT re-parse `sdd.md`), Write `./sdd-viewer.html` (Rule 13), tell the user: `Generated ./sdd-viewer.html — open it in a browser to review.` Failure → one-line notice, continue.

## Resumption

`sdd.draft.md` at trigger time is a leftover from an on-request draft or an older run. AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Use the draft — finalize and continue` | Read it as the design input, run Finalization, show the §Confirm summary built from it, proceed normally. |
| `Discard draft, start fresh` | Delete `sdd.draft.md`. Return to §Entry. |
| `Abort` | Exit. No file changes. |

If the user explicitly asks to finalize the existing draft, choose `Use the draft — finalize and continue` by assumption and do not ask a redundant resumption question. If AskUserQuestion is unavailable, make the same assumption unless the user asked to discard or abort. Finalization stays inside this skill: render the final `sdd.md` from the Case Management template and run the template conformance gate; never route `sdd.draft.md` finalization to `uipath-planner`.

**Direct finalize fast path:** for a request that says the draft design is settled and asks for final `sdd.md` only:

1. Read exactly three inputs: `sdd.draft.md`, this resumption/gate section, and `assets/templates/sdd-template.md`. Do not read planning/plugin references, inspect tenant resources, or spawn subagents.
2. The draft is the design source: its stages, tasks, variables, conditions, SLAs, personas, and integration intent are settled. Normalize structure and repair mechanically required rule pairings only — a schema-required companion rule is not a redesign. Never add, drop, or rename a business element; preserve exact stage and task display names (including punctuation), task types, variables, conditions, connector placeholders, and domain rules.
3. `user-selected-stage` repair: retain the authored lane and give every eligible upstream primary stage a completing `required-tasks-completed` / `wait-for-user` / `Marks Stage Complete: Yes` exit; wording such as "any active case" means every primary stage. **This repair replaces that stage's existing `required-tasks-completed | exit-only | Yes` row; it never adds a second completion row or a `Marks Stage Complete: No` row.** `wait-for-user` is picker exposure, not automatic event/SLA/decision routing — add no such trigger.
4. Inventory the draft's ordered stage and task headings in memory; render one complete output block per entry. Never use `cp`, `mv`, `install`, `rsync`, or any other shell copy/rename to produce the final artifact.
5. Every stage block carries `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, and `#### Tasks`.
6. Every task block carries `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, `**Entry Condition:**`, exact marker `**Task envelope**` (no colon) followed by its Required / Run Only Once / Skip Condition table, and the matching type-specific detail block.
7. Copy each type-specific detail block's heading and bold field labels verbatim from sdd-template.md — never rename, merge, or restyle them (`**Timer:**` stays `**Timer:**`, not `**Timer Mode:**`). When the draft has only task summaries, fill concise default detail tables. Every `process` / `agent` / `rpa` / `api-workflow` task ends with:

   ```markdown
   ###### Process / Agent / RPA / API Workflow Task Detail

   **Resolved Resource:** {draft's intended resource name; when the draft names none, the task display name — never `<UNRESOLVED>`}
   **Folder Path:** <UNRESOLVED>
   **Resource Identity:** <UNRESOLVED>
   ```

   Keep concrete folder/identity values the draft already supplies.
8. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block. Dropping or simplifying one loses a business rule.
9. A thresholded actor or policy condition stated only in draft prose/personas must also become executable inside an existing task or stage: a guarded owner/recipient/assignment expression or an `IF =js:` entry/exit condition that names the source attribute and threshold on one line (for example, `=js:vars.requestAmount > 100000 ? "Role:SeniorApprover" : "Role:Approver"`). Persona prose and Design Rationale alone are not final. This conversion never adds or renames a task.
10. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
11. Section 3/4 tables keep the template's exact column headers (Section 4 Agents: `Agent | Folder | Resource ID (+version) | Inputs → Outputs (or shared contract) | Used By Tasks`); never substitute a compact layout — dropped columns lose the folder/identity/IO contract.
12. For a large draft that needs batched writes, first Write the complete ordered document skeleton — Sections 1–4 with every primary/secondary stage heading in source order inside Section 2 — then Edit each stage/task block in place. Never append a deferred or omitted stage after `## Section 3`; insert it at its existing Section 2 heading before continuing.
13. Write `sdd.md` with Write/Edit. Never delete or rename `sdd.draft.md` — it stays beside the finalized document.
14. Audit loop — MANDATORY, not optional: the finalized `sdd.md` is unpresentable until this prints `AUDIT OK`. Run the skill's deterministic auditor on the written file (read-only; running it does not violate Rule 13):

    ```bash
    python3 "<this skill's folder>/scripts/audit_sdd.py" sdd.md --draft sdd.draft.md
    ```

    On `AUDIT FAIL`, repair each finding with Edit and re-run; repeat until it prints `AUDIT OK` (max 3 rounds — then stop and present the remaining findings). If `python3` is unavailable, verify manually instead; all of these must hold:
    - Same ordered stage/task inventory as the draft; every inventoried stage and task appears before `## Section 3`.
    - Per task type, task count equals type-detail-block count (N `process`/`agent`/`rpa`/`api-workflow` tasks ⇒ N `Process / Agent / RPA / API Workflow Task Detail` headings; likewise action / connector / timer / child-case blocks).
    - Every draft `=js:` expression is present in the output.
    - Literal seven-column Case Variables header (`Name | Category | Type | sourceTriggers | sourceFields | Default | Description`).
    - Explicit `**Interrupting:** Yes` or `No` line on every secondary stage.
    - Every stage/task block carries the literal markers from steps 5–6.
15. Stop. The finalized `sdd.md` beside the untouched `sdd.draft.md` is the deliverable; quote the audit's final `AUDIT OK` line in the reply as evidence.

## What to say while working

Silence and machinery-talk are both experience defects. Business-language lines only (§Forbidden vocabulary):

- **Decisions narrate as they land** — the doc-read lines and inference one-liners during Listen/Sketch are the running commentary; the `Decisions I Made` table is the complete record.
- **Before any stretch longer than ~a minute without a question**, one expectation-setter: `Design confirmed — building now. Nothing needed from you for a few minutes.`
- **At milestones**, one line each, business terms only. Never per-tool-call narration.
- **The moment tenant grounding fails**, one line: `I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.` Never let `resolve at build` rows be the first signal.
- **When continuing past a point without a prompt** (build start, Rule 11 straight-through), name what happens next and how to interrupt.

## Forbidden vocabulary (user-visible output)

The user sees a conversation that produces a case. Never surface in chat or in `sdd.md`:

- `sdd.draft.md`, `tasks/registry-resolved.json`, internal filenames. (**Exceptions:** `sdd.md` (the artifact line) and `sdd-viewer.html` (at generation) are intentionally user-visible.)
- `<UNRESOLVED>` markers in narration (file-only; chat says `resolve at build`).
- `Listen`, `Sketch`, `Confirm`, mode names, `the validator`, `structural validation`, `the cache`, `the registry index`, `~/.uip/`.
- `interview answers`, `from cache`, `REVIEW:`, `PDD`, or any chain-of-thought mechanics (echoes [`sdd-template.md`](../assets/templates/sdd-template.md) Output Rules).

If the user asks how something works, explain in their language (cases, stages, tasks, triggers, SLAs, personas, connectors, exceptions).

## Failure modes

| Symptom | Action |
|---|---|
| User says "skip" / "I don't know" during the one clarifying call | Best assumption + decision line. Optional field with no basis → `—`. |
| Required field with no basis even for assumption | `<UNRESOLVED: <question>>` in the model + ⚠ flagged line in the confirmation. Phase 1 + post-build loop revisit. |
| AskUserQuestion unavailable / unresponsive | One-line notice, continue best-assumption: every would-have-asked value gets a decision line; promotion scoped to the request — draft request → `sdd.draft.md` only; design-only → `sdd.md` on a clean Finalization pass, stop; build request → proceed, decisions carried in the confirmation text. |
| Registry pull fails (CLI error, no auth) | One plain-language line immediately. Keep concrete portable names (`Resolved Resource`, Action App title, `Child Case`); mark identities/folders `resolve at build` (`<UNRESOLVED>` in the file) with paired review items. Phase 1 retries discovery. |
| `sdd.md` already exists at path when interview begins | Should not happen — trigger detection exits Phase 0 first. If race, abort. Never overwrite. |
| Viewer write fails | One-line notice, continue — chat is the approval surface. |

## Output contract — what the build sees

- **In-session:** the confirmed in-memory model drives Phase 1 directly. `sdd.md` — written at build start (batched with build actions) — matches it exactly. A Phase 0 pull that succeeded this session is reused by Phase 1 (no re-pull — Rule 3 fast path). `tasks/registry-resolved.json` is produced by Phase 1, not Phase 0; light-pass matches are hints Phase 1 re-verifies against the session cache.
- **Cross-session / re-run:** `sdd.md` is the sole contract, read per Rule 2 exactly as a user-provided file — including after context compaction. It may carry `<UNRESOLVED>` identities and `—` placeholders, but every process/agent/rpa/api-workflow task has a concrete `Resolved Resource`, every action a concrete Action App title, every case-management task a concrete `Child Case`.
- `sdd-viewer.html` — on request only; ignored by Phase 1.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Strict binary trigger; presence = trust-as-written.
- **Do NOT interrogate.** No entry menu when the request has content, no per-dimension question walk, no confirming what the playbook decides. The budget is ONE clarifying call (when earned) + ONE confirmation. Uncertainty is resolved by assumption + disclosure, not by a question.
- **Do NOT hide a decision.** Every assumption, override, and resource pick appears in the `Decisions I Made` table, grouped when that keeps the Case Review scannable. Best-assumption without disclosure is guessing.
- **Do NOT substitute a generic build plan for the confirmation.** A "Build Plan" / "Approve this plan" list that names folders, artifacts, validation commands, primary stages, or resource caveats is not the Phase 0 confirmation. Show the required case-design sections first; only then may `Build it...` be asked.
- **Do NOT plan only the happy path.** Run the other-path sweep before confirmation and show **Other Paths Considered** even when the outcome is "primary flow only by user choice."
- **Do NOT write a summary `sdd.md`.** `sdd.md` must be the full template render, not the Case Review and not a build note. Missing Section 1/2/3/4 headings, missing per-stage/per-task detail blocks, or top-level summary sections are blocking render failures.
- **Do NOT run schema discovery (`tasks describe` / `case spec`) or ambiguity prompts in Phase 0.** One light name-match pass only; everything unclear is `resolve at build` — Phase 1 owns authoritative resolution and its Rule 17 gate.
- **Do NOT pull the tenant registry as a prerequisite, and never twice in one session.** The login/pull chain starts only when the case first shows tenant-bound work; a pull that succeeded this session is reused by Phase 1 (Rule 3 fast path). Equally, never delay the confirmation waiting for the pull.
- **Do NOT auto-pick among multiple resource matches.** Cross-folder or multi-match = `resolve at build`, disclosed. (Single confident match adopts silently — that is the only silent pick.)
- **Do NOT write `sdd.draft.md` or checkpoint files in a normal run.** The model lives in memory; drafts exist on explicit request only.
- **Do NOT block the build on the SDD write, and do NOT re-read the just-written `sdd.md` in-session.** The write shares a batch with the first build actions; memory drives the build. Re-read only on staleness (compaction/resume).
- **Do NOT ask the user to review or approve the `sdd.md` document.** The confirmation is the approval; the file is its artifact. An explicit sign-off request adds one prompt — nothing else does.
- **Do NOT let discovery workers write skill artifacts, prompt the user, or run the registry pull.** Fan-out is read-only; the parent owns every write.
- **Do NOT go silent during assembly and build start.** Post the expectation-setter and milestone lines from §What to say while working.
- **Do NOT use `sed`/`awk`/`python`/`node` to mutate `sdd.md`, `sdd.draft.md`, or `sdd-viewer.html`.** Read + Write/Edit only (Rule 13).
- **Do NOT invent gates or thresholds.** No size limit, no approval-before-creating-files, no complexity stop. The complete Phase 0 stop list: the one clarifying call (when earned), the confirmation, the explicit-sign-off prompt (when requested) — then the build's own gates (Phase 4 retry cap, debug, publish).
- **Do NOT narrate filenames or schema mechanics.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
