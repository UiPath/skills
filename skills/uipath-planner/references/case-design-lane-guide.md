# Case Design Lane — conversational case authoring

Product-specific conversational design lane for **Case Management**. This lane makes `uipath-planner` the **sole author of case SDDs**: it designs the case in the session's **in-memory model**, confirms it in ONE user checkpoint, resolves tenant resources at design time, and then writes the SDD. It replaces the interview the build skill (`uipath-maestro-case`) used to run itself; that skill hands design requests off to this lane at runtime — in the SAME conversation — and resumes the build on the Case Review's Build answer. The lane is product-agnostic in shape (Listen / Sketch / one confirmation) — BPMN and Flow can plug in later; today it is wired for Case Management.

> **Authoritative for the conversation path only.** Entry modes, Listen/Sketch flow, terminal step, resumption, output contract. Everything else lives in [references/case/](case/): the case model ([model.md](case/model.md), [variables.md](case/variables.md), [slas.md](case/slas.md)), authoring method ([authoring.md](case/authoring.md), [principles.md](case/principles.md)), render contracts ([render-case-definition.md](case/render-case-definition.md), [render-stages-tasks.md](case/render-stages-tasks.md)), tenant grounding ([grounding.md](case/grounding.md)), and the confirmation gate ([review.md](case/review.md)). The render shape is [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) with worked patterns in [`case-sdd-examples.md`](../assets/templates/case-sdd-examples.md). Everything after the SDD (tasks.md, caseplan.json, validate, publish) is owned by `uipath-maestro-case`.

## Read budget

Read this file, [case/model.md](case/model.md) (the case model the assumptions rely on), and [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) to begin — in parallel, each **at most once per session**. Open the other [case/](case/) files when their activity starts: shaping and typing → [authoring.md](case/authoring.md); data wiring → [variables.md](case/variables.md); SLAs → [slas.md](case/slas.md); rendering Section 1 / Section 2 → the two render contracts; the confirmation → [review.md](case/review.md). Do NOT read the generic Phase D references (pdd-analysis, product-selection levels beyond the Constraint Gate) for a conversational case request — scope is already decided. Reference paths resolve relative to this skill's base directory (given at invocation) — never hunt for them with `find` / global `ls`.

**Draft finalization budget (hard):** read this file's finalize sections (§Resumption, §Terminal step, §Template conformance gate) plus `sdd.draft.md` and the template — once each; work from those reads. Scripts are RUN, never read: invoke `audit_sdd.py` directly and act on its findings — opening the script source is a budget violation. The normalization contract (numeric `Task S{K}.{M}` headings, `**Task envelope**` markers, plain `<UNRESOLVED>` markers) lives in those sections — skipping them ships the draft's defects into the final SDD. Do NOT open the [case/](case/) content files or `case-sdd-examples.md`: finalization normalizes structure, it does not redesign. No subagents, no background tasks, no tenant discovery unless identities are needed and a session exists. Write via the §Terminal step write-early cadence.

## Entry modes — who called, who writes

| Mode | Trigger | Terminal step |
|---|---|---|
| **Build handoff** | The user asked `uipath-maestro-case` to build a case but no `sdd.md` exists — it hands the design to this lane in the SAME conversation, with the user | Run the normal flow to §Confirm, with the BUILD confirmation options (build-review preference folded in — see §Confirm). On a Build answer: write **`sdd.md`** at the working root — the build skill's filename contract (never overwrite an existing one) — `Status: ready`, then hand straight back: the build skill's phases continue immediately in this conversation, reusing the in-memory model and this session's resolution outcomes. NO stop, no re-invocation, no `## Next Steps` detour. |
| **Direct design** | User (or Delegate) asks to design / generate a case SDD, greenfield, no PDD | Write `<CASE_NAME_KEBAB>-sdd.md` (user-specified output path wins), Planner Handoff `Status: ready`, report the path, STOP. Task derivation / build continue on a later turn (Lane A or `uipath-maestro-case`). |
| **Draft request** | User explicitly asks for a reviewable draft and to stop there | Write `sdd.draft.md` (or `<name>-sdd.draft.md` when the request names the file), report, STOP. Never promote. |
| **Draft finalization** | A case `sdd.draft.md` exists and the user asks to finalize it | §Resumption: read the draft as the settled design, normalize to the template, run the conformance gate, write the final SDD, STOP. Final basename derives from the draft's: `sdd.draft.md` → `sdd.md`; `<name>-sdd.draft.md` → `<name>-sdd.md`; a user-specified output path wins. |
| **PDD-driven case** | A PDD routed to Phase D and scope selection picked Case Management | Standard Phase D flow ([sdd-generation-guide.md](sdd-generation-guide.md)) — but the case body obeys [references/case/](case/) and grounding runs per [case/grounding.md](case/grounding.md). |

**One output contract.** The design engine exists once; this skill ALWAYS executes the Write. The filename follows the consumer: a build handoff writes `sdd.md` at the working root (the build skill's contract); standalone direct design writes `<CASE_NAME_KEBAB>-sdd.md`. Never write `sdd.md` AND `<case>-sdd.md` for the same design, and NEVER overwrite an existing `sdd.md` at the working root — if one appears mid-run, abort the write and surface it.

## Goal

Design the case as an in-memory model shaped by the template, confirm it in ONE user prompt, then execute the mode's terminal step. The lane is **best-assumption by default**: it decides everything it can from the user's words and documents, and *informs* the user of every decision — it does not interrogate. For later sessions and re-runs the written SDD is the contract (the build skill trusts it as written); within this session, the in-memory model that produced it drives whatever comes next.

**The confirmation IS the plan-first approval surface.** If workspace or project rules require "show a plan before editing," satisfy that with the structured §Confirm Case Review below. Do not insert a separate generic "Build Plan" / "Approve this plan" checkpoint. A user "Yes" to a generic implementation plan is not a Build answer and must not create files.

## Entry

**If the request already describes the case** (any stages, work, trigger, domain, or attached docs), skip every entry prompt and go straight to work — the request IS the first Listen input. **Only a bare request** ("create a case" with nothing else) gets the Listen opener. There is no entry menu; abort is always a free-text away.

**Tenant work never blocks Entry.** Nothing about the tenant is a prerequisite for designing the case. **Build handoff mode:** fire the §Tenant grounding login+pull chain in the background AT ENTRY, in the same batch as the first document reads — the build's Phase 1 needs a fresh registry unconditionally, so starting it here costs nothing and lets resolution land before the Case Review. All other modes start grounding only when the case shows it needs it (§Tenant grounding).

## Tenant grounding — full resolution at design time

Owned by [case/grounding.md](case/grounding.md) — principles, the 5-step contract, result bucketing,
the cache-file map, the ONE batched resolution gate, the per-lookup resolution record, and the no-session
behavior. What stays here: kickoff TIMING is mode-bound — Build handoff starts the login+pull chain AT LANE
ENTRY, batched with the first document reads; every other mode starts it at the first tenant-bound signal.

## Modes

Three moves. **Listen** takes in everything offered; **Sketch** builds the complete case model by best assumption, recording every decision; **Confirm** shows the whole case once with the decisions taken and asks a single question. Listen and Sketch loop freely as new context lands; there is no separate Resolve or Approve pass — resolution rides the background chain and surfaces at Confirm.

### Listen

The opening move for a bare request. One message, one prompt:

> Tell me about the case you want to build. What kicks it off, what stages does it move through, and how does it close out? Drop in any docs you have — paths, paste, or attach.

What the agent does as input arrives:

- **Reads everything mentioned.** Path, dragged file, named doc → read immediately, in parallel when multiple. "Everything in `~/process-docs/`" → `ls` + parallel Reads.
- **Narrates content, not filenames.** One short line per doc about *what's in it*: `vendor-onboarding.md — 4 stages (Intake → Compliance → Finance → Activation), 2 personas, 8-hour SLA on Compliance.`
- **Partial reads for huge docs.** Past ~2000 lines, read the first chunk, narrate the signal, decide if more is needed. Unreadable formats (`.docx`, `.pptx`, scanned PDFs) → one paste request; PDFs ≤ 10 pages read directly.
- **Mid-flow docs are first-class.** New doc after the sketch exists → re-read, update the model, narrate the delta.
- **Named systems seed grounding.** Deployed resources, apps, connectors, systems named by the user feed §Tenant grounding.

Listen asks nothing beyond the opener. Gaps are filled by assumption in Sketch, not by questions.

#### Domain-vocabulary capture (during Listen)

Capture verbatim into the model: **roles** (exact casing — `CFO`, `Triage Nurse`), **domain nouns** (`Vendor` vs `Supplier` — never homogenize), **stage labels**, **decision outcomes** (`Approve` / `Decline` / `Needs Info`, not synonyms), **integration shortnames** (`Workday`, never "the HR system"). Provenance `verbatim:"<quote>"` per [case/principles.md § Source ledger](case/principles.md#source-ledger-provenance). Synonym drift is a fidelity defect ([case/principles.md § Domain fidelity](case/principles.md#domain-fidelity)).

#### File / attachment / document detection (during Listen)

When the user mentions `file`, `attachment`, `PDF`, `upload`, `evidence`, `receipt` (as artifact, not domain noun), pick the best-matching pattern from the indicators and record the decision — ask only if the user's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file`; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

### Sketch — best assumption, every field

Fill the complete SDD shape against [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) from what Listen captured, deciding every open field by best assumption. Authority order per [case/principles.md § Content authority hierarchy](case/principles.md#content-authority-hierarchy) — platform schema and compliance constraints override user phrasing (apply the override silently; it becomes a decision line). Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. Every stage, task, and configured SLA also gets a durable `Design Rationale` in the model explaining the kind/type, activation/sequencing, and routing/threshold choice. The model lives in memory — **no draft file, no checkpoint writes**.

**Assumption playbook** (decided and disclosed, never asked):

| Field | Best assumption |
|---|---|
| Trigger type | External system / portal / form / inbound event / record-created mentioned → **Connector Event** with that source (unprovisioned tenant object stays an event trigger — never downgrade to Manual); schedule/recurring → **Timer**; otherwise → **Manual**. |
| Task type on ambiguous verbs (`review`, `approve`, `validate`, `decide`, …) | Named human role or judgment implied → `action`; framed as automated/AI → `agent`; truly even → `action` (keeps a human in the loop; the user can flip it in one correction). Compliance trigger phrase (HIPAA, ECOA, FINRA, "licensed X", …) → `action`, always ([case/authoring.md § Override priority](case/authoring.md#task-type-override-priority)). |
| "Manual" in-case work | Starts a new case → Manual trigger; optional worker-launched task → `adhoc` + `Required: No`; worker-chosen exception/rework lane → secondary stage with `user-selected-stage`. Pick by context; disclose. |
| Case exit | Last primary stage completes (`required-stages-completed`, `Marks Case Complete: Yes`) unless the user described another close-out; alternate outcomes → non-completing case-exit rules. |
| Stage exit ↔ Marks Complete pairing | Derive mechanically per the WHEN ↔ Marks-Complete pairing rule — never author an illegal pair. |
| SLA | Only when the user mentioned timing; take their words literally ("about a day" → 1 day). No timing mentioned → `—`. For every SLA, decide scope, status, and response separately ([case/slas.md § Response model](case/slas.md#choosing-the-response)). No stated response → `notify-only` for both statuses; never invent a stage or task for a notification. |
| Case name / prefix | PascalCase from the domain noun; prefix = 2–4 letter mechanical derivation. |
| Personas | Named roles verbatim; none mentioned → single `Process Owner`. |
| Optional fields untouched by the user | `—`. Never a question. |
| Resources / connections | §Tenant grounding: single confident match adopted; ambiguous/empty → resolution gate at review time; no session → `resolve at build`. |

**Structure rules while sketching:** reference upstream task outputs directly; declare Case Variables only for arguments, trigger payloads, and multi-consumer or condition-read state ([case/variables.md](case/variables.md)). Required fields (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit) must all be settled — by user input or by playbook assumption.

**Bounded no-build design — plan-only requests.** When the request explicitly stops before `caseplan.json` (design + implementation plan only, tenant work forbidden), prefer progress over exhaustive internal auditing: once the model covers the stated stages, tasks, global interrupts, SLAs, variables, resources, and rationales — write. **Bounded means concise CONTENT, exact SHAPE.** The template's heading skeleton (`# SDD — {Case Name}`, `## Table of Contents`, `## Section 1: Case Definition` … `## Section 4: Integrations`), the per-stage Entry/Exit Conditions TABLES (rule syntax included — e.g. named-args `sla-status-change(...)` rows), the per-task detail blocks with `**Task envelope**`, and the Planner Handoff header are NEVER relaxed — a freeform outline (`## 1. Case Metadata…`, `## Decisions I Made` as body sections) is a blocking render failure even in this mode. Conciseness lives ONLY in prose depth: one short rationale sentence per stage/task/SLA/exception choice; do not expand optional examples, provenance prose, or registry audit detail. Do NOT run the full Finalization checklist — the gate for this mode is exactly four checks: the template conformance gate; the schema-pairing check; a reachability spot-check; and **SLA reference closure** — every `sla-status-change` entry row appears in its stage's Entry Conditions TABLE (never only in prose) using the named-args form `sla-status-change("<target>","<SLA Title>")` (at-risk rows add the escalation title), each title matching an SLA declared on that exact target; the case-level target is the literal `root` — never `Case` or the case name — and stage-level targets use the exact stage display name. A bare `sla-status-change` row cannot resolve to a `slaId` at build time and leaves the lane unreachable. In PROSE (rationales, descriptions), reference the rule as bare `sla-status-change` — NEVER a partial call form with placeholder args like `sla-status-change("root", ...)`; build-side checkers scan every call-form occurrence in the document and reject wrong arity wherever it appears. The full-template requirement still applies in this mode: every task's `**Entry Condition:**` is followed by the template's `| WHEN | IF | Display Name |` table — do not collapse an executable task gate into inline prose on the heading line; doing so drops the condition from the later planning handoff. A source rule that depends on a business attribute or threshold (for example, department- or seniority-gated eligibility) must be represented in an executable condition, output mapping, or guarded recipient/assignment expression, not only in a Design Rationale. When the prompt says every primary phase/stage has an SLA target, every named primary stage renders its own `#### Stage SLA` block with a concrete line-start `**SLA Title:**` (prefer `<Stage Name> SLA`; render `**SLA Type:**` and `**SLA Title:**` as two separate lines — a collapsed single line hides the title from line-start tooling) and concrete at-risk/breach display names; every `sla-status-change` reference uses those exact titles. Keep per-stage SLA tables consistent with the SLA Response Map: the breach cell reads `enter-stage: <Secondary Stage Name>` (the `sla-status-change`-entered interrupting stage), never `Notify: <role>`; notify-only cells are for at-risk warnings. Do not iterate for polish; the later build run re-validates everything. This bound applies on top of the seed-first cadence (§Terminal step): AFTER the accept answer, a fresh design writes early and per-section. Before the accept answer the model stays in memory (no draft file, no checkpoint writes).

**Conditional role / step gates must be inspectable.** When the source states a thresholded actor or step (for example, "Credit Analyst only over $5M; otherwise Underwriter"), model it as a guarded rule, task, recipient, or computed owner field AND preserve the business phrase close to the threshold in the draft/SDD text. A reviewer and a mechanical grep should be able to see both the actor name and threshold in one rule/task/rationale line, e.g. `Credit Analyst route when loanAmount > 5000000` or `Credit Analyst for loans >$5M; Underwriter otherwise`. Do not leave the gate only in a persona table or detached prose.

**Other-path sweep — mandatory before confirmation.** Owned by [case/authoring.md § Other-path sweep](case/authoring.md#other-path-sweep--mandatory-before-confirmation):
sweep the standard scenarios, pick the smallest faithful model per path, disclose everything in **Other
Paths Considered**; when the source has no signal at all, spend the one bounded question.

**Buildability musts** — settle all ten by assumption and surface each in the confirmation; they are where designs silently become unbuildable: (1) other-path trigger source (gate decision → `selected-stage-completed/-exited` + IF; person → `user-selected-stage` only with an upstream `wait-for-user` exit; external/global event → one `wait-for-connector` entry on the secondary stage; SLA at-risk/breach that requires case work → one `sla-status-change` entry whose target and SLA title — plus an at-risk escalation title for an at-risk row only — are declared in the SDD, while warning-only escalation stays a notification; interrupting flags on stage + entry rows; terminal `exit-only` vs `return-to-origin`; never duplicate global-event exits/tasks across primary stages); (2) every decision outcome routes somewhere — no dead-end status values, and an outcome that targets a lane keys that lane's entry; (3) every configure/decide task's output lands in a variable or direct reference; (4) every send/connector/agent's required inputs map to variables/literals/upstream outputs as far as knowable without schemas — the rest resolves at build; (5) conditional roles/steps become guarded rules + personas, not prose, with the actor and threshold visible together in the draft/SDD; (6) a critical-path connector failure gets a modeled other path when the user described failure handling — otherwise note it as an architect advisory; (7) manual-surface classification per the playbook: human-performed required work is `action`, optional user-launched work is `adhoc`; (8) intended resource names concrete, identities per §Tenant grounding; (9) every stage/task/SLA has durable rationale in the model, including why an ordered run is sequential, independent work is parallel, or parallel-after-predecessor siblings share one task set; (10) every non-start entry rule has a concrete producer/reference.

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, (c) the user asked to be asked, or (d) the mandatory other-path sweep found no source signal at all. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" — STOP: the playbook decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in this lane are the one clarifying call (when earned), the confirmation itself (with its folded resolution gate), and the explicit-sign-off path.

### Confirm — the single checkpoint

The whole checkpoint contract — the eight exact sections and their column shapes, the Caller-obligation
block, product vocabulary, completeness gate, the mode-specific confirmation options (including
`Build despite N flagged items`), corrections re-showing only changed sections, and explicit-sign-off
handling — is owned by [case/review.md](case/review.md). Run its finalization checklist against the
in-memory model FIRST (fix failures silently; unfixable items become Review Flags rows), then present the
review. The §Tenant grounding resolution gate (when it has items) rides this same turn. The confirmation IS
the plan-first approval surface — never substitute a generic build plan, and never create files on a "Yes"
to one.

### Template conformance gate — before `sdd.md` is written

The exact rendered SDD text must pass this gate before it leaves the lane — in every mode against the **on-disk file assembled by the write-early cadence, before the `Status: ready` flip** (one structural Read is the check). This is a render check, not a second design review. Do not use the read to redesign the case.

Required shape:

- First heading: `# SDD — {Case Name}`.
- `## Document History`, then the `## Planner Handoff` header + `<!-- planner-handoff:v1 -->` marker, then `## Table of Contents` — the universal planner scaffold (Rule 5); the case body follows.
- Exact section headings: `## Section 1: Case Definition`, `## Section 2: Stages & Tasks`, `## Section 3: Personas & App Views`, `## Section 4: Integrations`.
- Section 1 contains `### Case Metadata`, `### Case Triggers`, `### Case Exit Conditions`, and `### Case Variables`.
- Every modeled primary stage has `### Stage {N}: {Stage Name}`; every modeled secondary stage has `### Secondary Stage: {Stage Name}`.
- Every stage block contains `**Type:**`, `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, and `#### Tasks`.
- Every modeled primary-stage task has `##### Task {N}.{M}: {Task Name}`; every modeled secondary-stage task has numeric secondary numbering `##### Task S{K}.{M}: {Task Name}` where `K` is the secondary-stage order. Do not preserve letter prefixes such as `R.1`, `W.1`, `CC.1`, or `ESC.1`. Each task block contains `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, `**Entry Condition:**`, exact marker `**Task envelope**` (no colon), and the matching type-specific detail block.
- Every `<UNRESOLVED>` marker renders as plain text, exactly `<UNRESOLVED>` — never backtick-wrapped, never annotated inside the cell (build-phase checkers and Phase 1 discovery match the plain marker).
- Section 3 contains `### Personas` and `### Process App Views`.
- Section 4 contains the integration/resource family headings needed by the modeled task types, or an explicit `> None.` for empty families.

Forbidden summary-only replacement sections at top level: `## Source`, `## Case Objective`, `## Actors And Systems`, `## Case Trigger`, `## Stages`, `## Business Rules`, `## Task Plan`, `## Resource Resolution`, `## Acceptance Scenarios`. Their presence as the main document structure means the SDD is a summary, not a template render. Also forbid source/build-mode/path narration such as `Source: /...`, `Build mode`, `output folder`, validation-command checklists, or "generated from requirements file" prose in the SDD body.

If the gate fails, rewrite from the model and template before shipping. Do not write a summary SDD, even if a later `caseplan.json` would validate.

### Terminal step — who writes what

On the confirmation's accept answer, execute the mode's terminal step (§Entry modes).

**Fresh designs (build handoff / direct design / draft request) — write early, section-batched (mandatory):**
Draft finalization is different: the draft on disk is already the recovery point, so compose the complete
finalized document from it and write ONE `sdd.md` in a single Write, then run the audit and repair findings
with targeted Edits (§Resumption step 12) — the per-section cadence below is a fresh-design contract, and
following it during finalization costs ~25 extra turns for zero recovery value.

Never compose the whole SDD in-head and Write once at the end: a long silent composition turn risks context compaction that destroys unwritten work, and the on-disk partial file is the only cheap recovery point. Cadence:

1. **Seed Write immediately** after the accept answer: title + Document History + Planner Handoff header (`Status: draft`, `Template validation: pending`) + Table of Contents.
2. **Per-section Edit-appends**, in template order: Section 1 → Section 2 one stage block at a time → Section 3 → Section 4 → Next Steps. No re-Read between sibling appends. Compose each section just before its append — not the whole document up front.
3. **Gate on the on-disk file:** run the §Template conformance gate against the assembled file (one structural Read is allowed here).
4. **Ready flip is the LAST Edit:** `Status: ready`, `Template validation: passed` (drafts keep `Status: draft`). An interrupted run leaves a resumable `draft` on disk.
5. Report the path in one line, then fork by mode. **Build handoff:** do NOT stop — the Build answer already carried consent, so the build skill's phases start immediately in this conversation (`uip solution init` + its Phase 1, which verifies the resolved identities instead of re-discovering them). **Direct design / draft / finalization:** STOP — the SDD write is a turn boundary; task derivation (Lane A) or the build (`uipath-maestro-case`) continues on a later turn, opt-in, and `## Next Steps` in the written SDD points there.

**Free-text corrections stay first-class after the terminal step:** treat one as a targeted edit to the affected artifact (model + file + downstream), narrate it in one line, continue.

## Resolution ledger

The per-lookup record shape, `gateDecision` semantics, and cache-state rules are owned by
[case/grounding.md § Resolution record](case/grounding.md#the-resolution-record). Kept in-memory; the SDD cells
carry identities for cross-session use; when the build runs later in the SAME session, its planning pass
persists these records verbatim as `tasks/registry-resolved.json` and verifies instead of re-resolving.
**Machine data — never user-facing** (Resources and Integrations carries every user-relevant outcome).

## HTML preview

Optional, **on-request only** — never offered proactively. Self-contained local HTML review of the case design (Case Definition, collapsible Stages & Tasks, Personas, Integrations; filters and search). Generation: Read [`assets/templates/sdd-viewer.html`](../assets/templates/sdd-viewer.html), replace the `__SDD_DATA__` token in its `<script id="sdd-data">` block with JSON serialized from the in-memory model (schema in the template's header comment — do NOT re-parse the SDD when the model is live), Write `./sdd-viewer.html`, tell the user: `Generated ./sdd-viewer.html — open it in a browser to review.` Failure → one-line notice, continue. Downstream build phases ignore this file.

## Resumption

A case `sdd.draft.md` at lane entry is a leftover from an on-request draft or an older run. AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Use the draft — finalize and continue` | Read it as the design input, run Finalization, show the §Confirm summary built from it, proceed normally. |
| `Discard draft, start fresh` | Delete the draft. Return to §Entry. |
| `Abort` | Exit. No file changes. |

If the user explicitly asks to finalize the existing draft, choose `Use the draft — finalize and continue` by assumption and do not ask a redundant resumption question. If AskUserQuestion is unavailable, make the same assumption unless the user asked to discard or abort.

**Direct finalize fast path:** for a request that says the draft design is settled and asks for the final SDD only:

1. Read exactly these inputs, once each: the draft, this section + §Terminal step + §Template conformance gate, and the template (§Read budget: not the authoring rules guide, not the examples file). Do not read planning references, inspect tenant resources, or spawn subagents or background tasks.
2. The draft is the design source: its stages, tasks, variables, conditions, SLAs, personas, and integration intent are settled. Normalize structure and repair mechanically required rule pairings only — a schema-required companion rule is not a redesign. Never add, drop, or rename a business element; preserve exact stage and task display names (including punctuation), task types, variables, conditions, connector placeholders, and domain rules.
3. `user-selected-stage` repair: retain the authored lane and give every eligible upstream primary stage a completing `required-tasks-completed` / `wait-for-user` / `Marks Stage Complete: Yes` exit; wording such as "any active case" means every primary stage. **This repair replaces that stage's existing `required-tasks-completed | exit-only | Yes` row; it never adds a second completion row or a `Marks Stage Complete: No` row.** `wait-for-user` is picker exposure, not automatic event/SLA/decision routing — add no such trigger.
4. Inventory the draft's ordered stage and task headings in memory; render one complete output block per entry — preserve exactly one `##### Task …: {Task Name}` detail block per inventoried task, never replacing them with only a stage-level `#### Tasks` table or a shared `### Task Definitions` table. Never use `cp`, `mv`, `install`, `rsync`, or any other shell copy/rename to produce the final artifact, and never delete or rename the draft — it stays beside the finalized document. Render with Write/Edit; if a copy seed is ever used, it counts only once every block is normalized in place and the audit passes — `mv`/`rm` on the draft are never acceptable.
5. Every stage block carries `**Type:** Stage` (that literal — never `Secondary Stage` or a stage-kind word; secondary-ness lives in the `### Secondary Stage:` heading, `**Stage Kind:** secondary`, and `**Interrupting:**`), `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, and `#### Tasks`.
6. Every task block carries `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, `**Entry Condition:**`, exact marker `**Task envelope**` (no colon) followed by its Required / Run Only Once / Skip Condition table, and the matching type-specific detail block.
7. Copy each type-specific detail block's heading and bold field labels verbatim from the template — never rename, merge, or restyle them (`**Timer:**` stays `**Timer:**`, not `**Timer Mode:**`). When the draft has only task summaries, fill concise default detail tables. Every `process` / `agent` / `rpa` / `api-workflow` task ends with:

   ```markdown
   ###### Process / Agent / RPA / API Workflow Task Detail

   **Resolved Resource:** {draft's intended resource name; when the draft names none, the task display name — never <UNRESOLVED>}
   **Folder Path:** <UNRESOLVED>
   **Resource Identity:** <UNRESOLVED>
   ```

   Keep concrete folder/identity values the draft already supplies.
8. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block, with its field names, variable references, and output mapping intact — an equivalent-looking shorthand that drops an input, predicate, or intermediate field is a failure, not a simplification.
9. Threshold-policy conversion — MANDATORY scan, not optional polish. Scan the draft (descriptions, personas table, rationale) for comparator + amount phrases: `>`, `<`, `≥`, `≤`, `over`, `above`, `under`, `below`, `at least`, `more/less than` next to an amount (`$5M`, `100000`, `L4`). EVERY such policy must also appear in an executable cell of the owning task or stage in the final — prose-only is a render failure:
    - A personas row like `SomeRole | StageX (amount > $N only)` REQUIRES a matching guarded expression inside a StageX task block, phrased on the HIGH side and assigning the exception role: an owner/recipient cell or entry-condition IF cell containing `=js:vars.amount > N000000 ? "Role:SomeRole" : "Role:DefaultRole"` — the numeral written out (`5000000`, not `$5M`), the role and attribute on the same line. The expression lives in a table cell (Inputs/owner/recipient/WHEN/IF); an `=js:` fragment inside `**Design Rationale:**` or `**Description:**` prose is NOT an encoding and fails the gate.
    - Reuse an existing variable that carries the attribute; the conversion never adds or renames a task or variable.
    - Persona prose and Design Rationale alone are not final.
10. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
11. Section 3/4 tables keep the template's exact column headers (Section 4 Agents: `Agent | Folder | Resource ID (+version) | Inputs → Outputs (or shared contract) | Used By Tasks`); never substitute a compact layout — dropped columns lose the folder/identity/IO contract.
12. Emit real newlines: the literal two-character sequence `\n` anywhere in the written document is a render failure — if one appears, rewrite that block with actual line breaks. Compose the complete finalized document from the draft and write it in ONE Write — Sections 1–4 with every primary/secondary stage in source order inside Section 2 (the draft is the recovery point; on interruption, re-finalize from it). After the Write, repair audit findings with targeted Edits only. Never append a deferred or omitted stage after `## Section 3`; place it at its Section 2 position in the composed document.
13. Audit loop — MANDATORY, not optional: the finalized SDD is unpresentable and the `ready` flip is forbidden until this prints `AUDIT OK`. Run the skill's deterministic auditor on the written file (read-only):

    ```bash
    python3 "<this skill's folder>/scripts/audit_sdd.py" <final SDD path> --draft <draft path>
    ```

    On `AUDIT FAIL`, repair each finding with Edit and re-run; repeat until it prints `AUDIT OK` (max 3 rounds — then stop and present the remaining findings). If `python3` is unavailable, verify manually instead; all of these must hold:
    - Same ordered stage/task inventory as the draft; every inventoried stage and task appears before `## Section 3`.
    - Per task type, task count equals type-detail-block count (N `process`/`agent`/`rpa`/`api-workflow` tasks ⇒ N `Process / Agent / RPA / API Workflow Task Detail` headings; likewise action / connector / timer / child-case blocks).
    - Every draft `=js:` expression is present in the output.
    - Every consumed `=vars.X` is declared in Case Variables and keeps a producer — a `-> X` output row, an assignment, a Default, or a trigger source; a consumer without a producer is a lineage failure.
    - No comparator threshold from the draft (`>$5M`, `≤ $N`, `over $X`) remains prose-only — each appears in an executable table cell (owner/recipient/WHEN/IF), high-side guard assigning the exception role; `=js:` inside Rationale/Description prose does not count (step 9).
    - Literal seven-column Case Variables header (`Name | Category | Type | sourceTriggers | sourceFields | Default | Description`).
    - Explicit `**Interrupting:** Yes` or `No` line on every secondary stage.
    - Every secondary stage that exits `return-to-origin` declares `**Interrupting:** Yes`, and each of its Stage Entry Conditions rows says `Interrupting: Yes`.
    - Every stage/task block carries the literal markers from steps 5–6.
14. Then flip `ready` (§Terminal step), write the final SDD basename per §Entry modes, and stop; quote the audit's final `AUDIT OK` line in the reply as evidence.

## What to say while working

Silence and machinery-talk are both experience defects. Business-language lines only (§Forbidden vocabulary):

- **Decisions narrate as they land** — the doc-read lines and inference one-liners during Listen/Sketch are the running commentary; the `Decisions I Made` block is the complete record.
- **Before any stretch longer than ~a minute without a question**, one expectation-setter: `Design confirmed — handing to the build now. Nothing needed from you for a few minutes.`
- **At milestones**, one line each, business terms only. Never per-tool-call narration.
- **The moment tenant grounding fails**, one line: `I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.` Never let `resolve at build` rows be the first signal.
- **When continuing past a point without a prompt**, name what happens next and how to interrupt.

## Forbidden vocabulary (user-visible output)

The user sees a conversation that produces a case design. Never surface in chat or in the SDD:

- Internal filenames (`sdd.draft.md` is user-visible only on explicit draft requests; the written SDD path is intentionally user-visible in the artifact line).
- `<UNRESOLVED>` markers in narration (file-only; chat says `resolve at build`).
- `Listen`, `Sketch`, `Confirm`, mode names, `the validator`, `structural validation`, `the cache`, `the registry index`, `~/.uip/`, `resolution ledger`, `delegation`, `subagent mode`.
- `interview answers`, `from cache`, `REVIEW:`, or any chain-of-thought mechanics.

If the user asks how something works, explain in their language (cases, stages, tasks, triggers, SLAs, personas, connectors, exceptions).

## Failure modes

| Symptom | Action |
|---|---|
| User says "skip" / "I don't know" during the one clarifying call | Best assumption + decision line. Optional field with no basis → `—`. |
| Required field with no basis even for assumption | `<UNRESOLVED: <question>>` in the model + ⚠ flagged line in the confirmation. The build's phases revisit. |
| AskUserQuestion unavailable / unresponsive (Delegate needs this) | One-line notice, continue best-assumption: every would-have-asked value gets a decision line; gate items default to `resolve at build` with NO `gateDecision` recorded (the build's gate re-asks them); promotion scoped to the request — draft request → draft file only; design-only → the final SDD on a clean Finalization pass, stop; build handoff → the final SDD on a clean Finalization pass, then the build continues with its default straight-through preference. |
| Registry pull fails (CLI error, no auth) | One plain-language line immediately. Keep concrete portable names; mark identities/folders `resolve at build` (`<UNRESOLVED>` in the file) with paired review items. The build's planning pass retries discovery. |
| `sdd.md` already exists at the working root (build handoff) | The handoff should not have happened — surface it; the build skill consumes the existing file trust-as-written. Never overwrite. |
| Context compaction mid-render (direct/finalize) | Resume from the on-disk partial SDD: re-read it + the design source (`sdd.draft.md` or the model summary in the Case Review), append the next missing section, continue the cadence. Do NOT re-invoke skills, do NOT re-read reference guides already applied, do NOT search the filesystem, do NOT spawn background tasks — the partial file + template are sufficient. |

## Output contract — what the consumer sees

- **Build handoff, same session:** the Build answer is the consent; `sdd.md` on disk plus the in-memory model drive the build directly, and the in-context resolution outcomes (§Resolution ledger) seed its verify-only planning.
- **Direct, cross-session:** the written SDD is the sole contract, read by any consumer exactly as if the user wrote it — Planner Handoff `Status: ready`, resolved identities in Section 2/Section 4 cells, `<UNRESOLVED>` only where deferred with review items, every process/agent/rpa/api-workflow task carrying a concrete `Resolved Resource`, every action a concrete Action App title, every case-management task a concrete `Child Case`.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Presence = trust-as-written; abort and surface.
- **Do NOT interrogate.** No entry menu when the request has content, no per-dimension question walk, no confirming what the playbook decides. The budget is ONE clarifying call (when earned) + ONE confirmation (with the folded resolution gate). Uncertainty is resolved by assumption + disclosure, not by a question.
- **Do NOT hide a decision.** Every assumption, override, and resource pick appears in the `Decisions I Made` block. Best-assumption without disclosure is guessing.
- **Do NOT substitute a generic build plan for the confirmation.** A "Build Plan" / "Approve this plan" list that names folders, artifacts, validation commands, primary stages, or resource caveats is not the confirmation. Show the required case-design sections first; only then may the approval question be asked.
- **Do NOT plan only the happy path.** Run the other-path sweep before confirmation and show **Other Paths Considered** even when the outcome is "primary flow only by user choice."
- **Do NOT ship a summary SDD.** The rendered text must be the full template render, not the Case Review and not a build note. Missing Section 1/2/3/4 headings, missing per-stage/per-task detail blocks, or top-level summary sections are blocking render failures.
- **Do NOT run schema discovery (`tasks describe` / `case spec`) at design time.** Identity resolution only; schemas belong to the build phases.
- **Do NOT block on the tenant registry, and never pull twice in one session.** The login/pull chain runs in the background — entry-time in Build handoff mode, first-tenant-bound-work otherwise (§Tenant grounding); a pull that succeeded this session is reused by the build (its same-session fast path). Never delay the confirmation waiting for the pull.
- **Do NOT auto-pick among multiple resource matches, and do NOT re-ask at build what the gate already answered.** Ambiguity is the gate's job, once, at review time. (Single confident match adopts silently — that is the only silent pick.)
- **Do NOT scaffold projects, spawn build subagents, or execute create-on-missing here.** `Create during build` is a recorded decision the build skill executes.
- **Do NOT write `sdd.draft.md` or checkpoint files in a normal run.** The model lives in memory; drafts exist on explicit request only.
- **Do NOT ask the user to review or approve the SDD document.** The confirmation is the approval; the file is its artifact. An explicit sign-off request adds one prompt — nothing else does.
- **Do NOT go silent during assembly.** Post the expectation-setter and milestone lines from §What to say while working.
- **Do NOT invent gates or thresholds.** No size limit, no approval-before-creating-files, no complexity stop.
- **Do NOT narrate filenames or schema mechanics.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
