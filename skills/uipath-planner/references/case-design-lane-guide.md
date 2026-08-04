# Case Design Lane — conversational case authoring

Product-specific conversational design lane for **Case Management**. This lane makes `uipath-planner` the **sole author of case SDDs**: it designs the case in the session's **in-memory model**, confirms it in ONE user checkpoint, resolves tenant resources at design time, and then either writes the SDD or hands the confirmed model back to the caller. It replaces the interview the build skill (`uipath-maestro-case`) used to run itself. The lane is product-agnostic in shape (Listen / Sketch / one confirmation) — BPMN and Flow can plug in later; today it is wired for Case Management.

> **Authoritative for the conversation path only.** Entry modes, grounding, confirmation, resumption, output contract. **Content rules** (authority hierarchy, task-type override priority, render-required fields, variable lineage, review items, source ledger, finalization checks) live in [case-authoring-rules-guide.md](case-authoring-rules-guide.md). The render shape is [`assets/templates/case-sdd-template.md`](../assets/templates/case-sdd-template.md) with worked patterns in [`case-sdd-examples.md`](../assets/templates/case-sdd-examples.md). Everything after the SDD (tasks.md, caseplan.json, validate, publish) is owned by `uipath-maestro-case`.

## Read budget

Read this file, [case-authoring-rules-guide.md](case-authoring-rules-guide.md) (the mental model + task-type reasoning the assumptions rely on), and [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) to begin — in parallel, each **at most once per session**. Do NOT read the generic Phase D references (pdd-analysis, product-selection levels beyond the Constraint Gate) for a conversational case request — scope is already decided. Reference paths resolve relative to this skill's base directory (given at invocation) — never hunt for them with `find` / global `ls`.

**Draft finalization budget (hard):** read this file's finalize sections (§Resumption, §Terminal step, §Template conformance gate) plus `sdd.draft.md` and the template — once each; work from those reads. The normalization contract (numeric `Task S{K}.{M}` headings, `**Task envelope**` markers, plain `<UNRESOLVED>` markers) lives in those sections — skipping them ships the draft's defects into the final SDD. Do NOT open `case-authoring-rules-guide.md` or `case-sdd-examples.md`: finalization normalizes structure, it does not redesign. No subagents, no background tasks, no tenant discovery unless identities are needed and a session exists. Write via the §Terminal step write-early cadence.

## Entry modes — who called, who writes

| Mode | Trigger | Terminal step |
|---|---|---|
| **Delegated — subagent SDD author** | `uipath-maestro-case` spawns this lane as a **subagent** because no `sdd.md` exists for a case build request (or a case draft needs finalizing) | **Write `sdd.md`** at the caller's working root (never overwrite an existing one), template-conformant and gate-passed, `Status: ready`. AskUserQuestion is unavailable in a subagent — run best-assumption throughout (§Failure modes fallback). **Return in the final report:** the full Case Review packet + `Decisions I made` + the resolution ledger as a JSON block (§Resolution ledger). The caller presents the review to the user and owns the build. |
| **Direct design** | User (or Delegate) asks to design / generate a case SDD, greenfield, no PDD | Write `<CASE_NAME_KEBAB>-sdd.md` (user-specified output path wins), Planner Handoff `Status: ready`, report the path, STOP. Task derivation / build continue on a later turn (Lane A or `uipath-maestro-case`). |
| **Draft request** | User explicitly asks for a reviewable draft and to stop there | Write `sdd.draft.md` (or `<name>-sdd.draft.md` when the request names the file), report, STOP. Never promote. |
| **Draft finalization** | A case `sdd.draft.md` exists and the user asks to finalize it | §Resumption: read the draft as the settled design, normalize to the template, run the conformance gate, write the final SDD, STOP. Final basename derives from the draft's: `sdd.draft.md` → `sdd.md`; `<name>-sdd.draft.md` → `<name>-sdd.md`; a user-specified output path wins. |
| **PDD-driven case** | A PDD routed to Phase D and scope selection picked Case Management | Standard Phase D flow ([sdd-generation-guide.md](sdd-generation-guide.md)) — but the case body obeys [case-authoring-rules-guide.md](case-authoring-rules-guide.md) and grounding runs per this guide. |

**One output contract.** The design engine exists once; this skill ALWAYS executes the Write. The filename follows the consumer: delegated mode writes the caller's contract (`sdd.md` at the provided working root); direct mode writes this skill's (`<CASE_NAME_KEBAB>-sdd.md`). Never write `sdd.md` AND `<case>-sdd.md` for the same design, and NEVER overwrite an existing `sdd.md` at the caller's resolved path — if one appears mid-run, abort the write and surface it.

**Delegation prompt contract (subagent mode).** The caller spawns one subagent whose prompt carries: the user's request + document paths verbatim, the resolved working directory, and the instruction to follow this lane end-to-end. Inside the subagent there is no user: skip the one clarifying call, decide everything best-assumption (every would-have-asked value gets a decision line), run grounding + the resolution gate non-interactively (`resolve at build` for every gate item — never `create during build`), pass the conformance gate, and write `sdd.md` via the §Terminal step cadence. The subagent's **final report** is the approval payload: the complete 10-section Case Review, the `Decisions I made` block, ⚠ flags, and the resolution ledger as one fenced JSON block. The caller shows that review to the real user for the Build answer — the SDD file on disk is the durable artifact at the boundary; corrections re-enter as a targeted re-delegation ("edit `sdd.md`: <change>").

## Goal

Design the case as an in-memory model shaped by the template, confirm it in ONE user prompt, then execute the mode's terminal step. The lane is **best-assumption by default**: it decides everything it can from the user's words and documents, and *informs* the user of every decision — it does not interrogate. For later sessions and re-runs the written SDD is the contract (the build skill trusts it as written); within this session, the in-memory model that produced it drives whatever comes next.

**The confirmation IS the plan-first approval surface.** If workspace or project rules require "show a plan before editing," satisfy that with the structured §Confirm Case Review below. Do not insert a separate generic "Build Plan" / "Approve this plan" checkpoint. A user "Yes" to a generic implementation plan is not a Build answer and must not create files.

## Entry

**If the request already describes the case** (any stages, work, trigger, domain, or attached docs), skip every entry prompt and go straight to work — the request IS the first Listen input. **Only a bare request** ("create a case" with nothing else) gets the Listen opener. There is no entry menu; abort is always a free-text away.

**No tenant work at Entry.** Nothing about the tenant is a prerequisite for designing the case — grounding starts only when the case shows it needs it (§Tenant grounding).

## Tenant grounding — full resolution at design time

This lane does **full identity resolution** — registry pull, per-resource cache lookups, connection checks, and the ambiguity/empty gate — so a confirmed design carries resolved identities and the build's planning pass becomes verify-only. Schema discovery (`tasks describe`, `case spec`) is NOT design work — it stays in the build phases.

1. **Intake batch.** Read every supplied document in parallel. Extract named systems, resources, likely tasks, and roles.
2. **Chain kickoff — requirement-driven, background.** The FIRST moment the sketch identifies tenant-bound work (a named system/resource/connector, or an inferred runnable/connector/action task), start ONE background command in the same batch as whatever is already running: `uip login status --output json && uip maestro case registry pull`. It resolves while sketching continues; a case with no tenant-bound items never pulls. Best-effort: never block on it, never surface its output unprompted. **No session** (not logged in, CLI absent, pull fails — e.g. Delegate offline): one plain-language line (§What to say while working), keep concrete intended names, mark every identity `resolve at build`, continue — the design stays complete and safe.
3. **Resolution pass — join, never wait.** When the sketch is complete and the pull succeeded, resolve every named or inferred resource in ONE parallel batch of cache lookups — `~/.uip/case-resources/<type>-index.json` per type (`agent-index`, `api-index`, `process-index`, `processOrchestration-index`, `caseManagement-index`, `action-apps-index` for HITL apps, `typecache-activities-index` / `typecache-triggers-index` for connectors). For each connector also check enabled connections. Bucket each result:
   - **Single confident match** (1 exact-name match across all folders, ≥ 1 shared name token; for connectors: exactly 1 enabled connection) → **adopt**: write identity + exact folder into the model's SDD cells and a ledger entry; disclose as a decision line.
   - **Ambiguous** (multiple matches, cross-folder same-name, no token overlap; > 1 enabled connection) → queue for the resolution gate. Do NOT auto-pick.
   - **Empty** (0 matches after a successful pull; 0 enabled connections) → queue for the resolution gate. A missing cache file *before* a successful pull is a failed precondition, never a zero-match result.
4. **Resolution gate — the ONE batched ask, at review time.** Present the queued items together with the Case Review — one `AskUserQuestion` call (≤ 4 questions; overflow groups carry into the confirmation's follow-up), grouped by `(name, type)` with usages listed. Options per group:
   - **Pick a match** — ambiguous lookups list the candidates with folder FQNs; the user picks one (or `resolve at build`). A resource name deployed in ≥ 2 folders is ALWAYS ambiguous — never "pick one folder" silently.
   - **Resolve at build** — identity stays `<UNRESOLVED>` in the SDD with a paired review item; the build emits a placeholder task the user upgrades later.
   - **Create during build** — offered ONLY for empty `agent` / `api-workflow` lookups. Records the decision in the ledger; the **build skill** executes its inline-create flow from it (this lane never scaffolds projects or spawns build subagents). Non-creatable kinds (regular RPA process, action, case-management, connectors, agentic process) show `resolve at build` only.
   Do NOT pre-judge by resource-name heuristics — the user's call. If the pull has NOT finished when the review is ready, do not wait: present with `resolve at build` on the pending items. The gate runs ONCE, here — the build must not re-ask.
5. **Visibility.** Every adopted identity, connection, gate decision, and `resolve at build` deferral is visible in the Case Review (Resources & integrations + Decisions I made) and lands in SDD Section 2 task cells and the Section 4 roll-up.

**Guardrails:** registry data is evidence, not requirements — never add/rename business work to match tenant inventory; never dump catalogs; keep type-specific portable names concrete (`Resolved Resource`, Action App title, `Child Case`) even when identity defers; a connector with zero connections is a gate item, not a reason to change the task type. **Design-only, draft, and no-session runs skip grounding entirely** — preserve concrete intended names, mark identities `resolve at build`, and report that resource wiring is deferred to the build run.

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

Capture verbatim into the model: **roles** (exact casing — `CFO`, `Triage Nurse`), **domain nouns** (`Vendor` vs `Supplier` — never homogenize), **stage labels**, **decision outcomes** (`Approve` / `Decline` / `Needs Info`, not synonyms), **integration shortnames** (`Workday`, never "the HR system"). Provenance `verbatim:"<quote>"` per [case-authoring-rules-guide.md § Source ledger](case-authoring-rules-guide.md#source-ledger-provenance). Synonym drift is a fidelity defect ([§ Domain fidelity](case-authoring-rules-guide.md#domain-fidelity)).

#### File / attachment / document detection (during Listen)

When the user mentions `file`, `attachment`, `PDF`, `upload`, `evidence`, `receipt` (as artifact, not domain noun), pick the best-matching pattern from the indicators and record the decision — ask only if the user's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file`; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

### Sketch — best assumption, every field

Fill the complete SDD shape against [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) from what Listen captured, deciding every open field by best assumption. Authority order per [case-authoring-rules-guide.md § Content authority hierarchy](case-authoring-rules-guide.md#content-authority-hierarchy) — platform schema and compliance constraints override user phrasing (apply the override silently; it becomes a decision line). Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. Every stage, task, and configured SLA also gets a durable `Design Rationale` in the model explaining the kind/type, activation/sequencing, and routing/threshold choice. The model lives in memory — **no draft file, no checkpoint writes**.

**Assumption playbook** (decided and disclosed, never asked):

| Field | Best assumption |
|---|---|
| Trigger type | External system / portal / form / inbound event / record-created mentioned → **Connector Event** with that source (unprovisioned tenant object stays an event trigger — never downgrade to Manual); schedule/recurring → **Timer**; otherwise → **Manual**. |
| Task type on ambiguous verbs (`review`, `approve`, `validate`, `decide`, …) | Named human role or judgment implied → `action`; framed as automated/AI → `agent`; truly even → `action` (keeps a human in the loop; the user can flip it in one correction). Compliance trigger phrase (HIPAA, ECOA, FINRA, "licensed X", …) → `action`, always ([§ Task-type override priority](case-authoring-rules-guide.md#task-type-override-priority)). |
| "Manual" in-case work | Starts a new case → Manual trigger; optional worker-launched task → `adhoc` + `Required: No`; worker-chosen exception/rework lane → secondary stage with `user-selected-stage`. Pick by context; disclose. |
| Case exit | Last primary stage completes (`required-stages-completed`, `Marks Case Complete: Yes`) unless the user described another close-out; alternate outcomes → non-completing case-exit rules. |
| Stage exit ↔ Marks Complete pairing | Derive mechanically per the WHEN ↔ Marks-Complete pairing rule — never author an illegal pair. |
| SLA | Only when the user mentioned timing; take their words literally ("about a day" → 1 day). No timing mentioned → `—`. For every SLA, decide scope, status, and response separately ([§ SLA response model](case-authoring-rules-guide.md#mental-model-stages-secondary-stages-tasks)). No stated response → `notify-only` for both statuses; never invent a stage or task for a notification. |
| Case name / prefix | PascalCase from the domain noun; prefix = 2–4 letter mechanical derivation. |
| Personas | Named roles verbatim; none mentioned → single `Process Owner`. |
| Optional fields untouched by the user | `—`. Never a question. |
| Resources / connections | §Tenant grounding: single confident match adopted; ambiguous/empty → resolution gate at review time; no session → `resolve at build`. |

**Structure rules while sketching:** §1.5 declare-vs-xref — mint a §1.5 row ONLY for `In`/`Out` args, trigger-payload Variables, and state read by a condition or ≥ 2 consumers; a single upstream output feeding one consumer is referenced directly (`<- "Stage"."Task".out` / `vars.$xref(...)`), never relayed. Required fields (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit) must all be settled — by user input or by playbook assumption.

**Bounded no-build design — plan-only requests and delegations.** When the request explicitly stops before `caseplan.json` (design + implementation plan only, tenant work forbidden), prefer progress over exhaustive internal auditing: once the model covers the stated stages, tasks, global interrupts, SLAs, variables, resources, and rationales — write. Compose a CONCISE full-template SDD: one short rationale sentence per stage/task/SLA/exception choice; do not expand optional examples, provenance prose, or registry audit detail. Do NOT run the full Finalization checklist — the template conformance gate, the schema-pairing check, and a reachability spot-check are the whole gate for this mode. Do not iterate for polish; the later build run re-validates everything. This bound applies on top of the seed-first cadence (§Terminal step) — write while designing, not after.

**Other-path sweep — mandatory before confirmation.** Do not design only the primary flow and wait for the user to ask about alternatives later. Check the source for: rework / needs-info loops; rejection, withdrawal, and cancellation; SLA escalation; external-system failure; manual override or worker-selected side work; optional side work; and terminal outcomes that differ from successful completion. For each scenario, choose the correct model: interrupting secondary stage, terminal case-exit, non-completing case-exit, task-level branch, `adhoc` task, SLA notification only, or "not modeled" when the source explicitly rules it out. If the source names or strongly implies a scenario, model it by best assumption and disclose it in **Other Paths Considered**. If the source has no signal at all, spend the one clarifying call on a single bounded question before confirmation: "I don't see any other paths beyond the primary flow. Should I add standard paths for rework, cancellation/withdrawal, SLA escalation, or keep only the primary flow?"

**Buildability musts** — settle all nine by assumption and surface each in the confirmation; they are where designs silently become unbuildable: (1) other-path trigger source (gate decision → `selected-stage-completed/-exited` + IF; person → `user-selected-stage`; external/global event → one `wait-for-connector` entry on the secondary stage; SLA at-risk/breach that requires case work → one `sla-status-change` entry whose target and SLA title — plus an at-risk escalation title for an at-risk row only — are declared in the SDD, while warning-only escalation stays a notification; interrupting flags on stage + entry rows; terminal `exit-only` vs `return-to-origin`; never duplicate global-event exits/tasks across primary stages); (2) every decision outcome routes somewhere — no dead-end status values, and an outcome that targets a lane keys that lane's entry; (3) every configure/decide task's output lands in a variable or direct reference; (4) every send/connector/agent's required inputs map to variables/literals/upstream outputs as far as knowable without schemas — the rest resolves at build; (5) conditional roles/steps become guarded rules + personas, not prose; (6) a critical-path connector failure gets a modeled other path when the user described failure handling — otherwise note it as an architect advisory; (7) manual-surface classification per the playbook; (8) intended resource names concrete, identities per §Tenant grounding; (9) every stage/task/SLA has durable rationale in the model, including why an ordered run is sequential or independent work is parallel.

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, (c) the user asked to be asked, or (d) the mandatory other-path sweep found no source signal at all. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" — STOP: the playbook decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in this lane are the one clarifying call (when earned), the confirmation itself (with its folded resolution gate), and the explicit-sign-off path.

### Confirm — the single checkpoint

One structured **Case Review**, one question. Run the [case-authoring-rules-guide.md § Finalization](case-authoring-rules-guide.md#finalization) checks against the in-memory model FIRST — fix failures silently (they are the agent's defects, not the user's decisions); anything unfixable becomes a flagged line. This is the user approval surface and must be complete enough to review without opening any SDD file. It is not a generic build plan and not the full SDD prose: it mirrors the SDD sections in scan-friendly tables and grouped bullets. The §Tenant grounding resolution gate (when it has items) rides this same turn.

**Coverage map:** SDD Section 1 (case definition) → Case snapshot + Data contract + Rules / tiers; SDD Section 2 (stages/tasks) → Stages list + Stage/task detail cards + Other Paths Considered; SDD Section 3 (personas/views) → Case snapshot + stage/task cards; SDD Section 4 (integrations) → Resources & integrations. Anything with a High review item in the SDD model also appears in Review flags.

Use this exact section order:

1. **Case snapshot** — table `Item | Review value`. Include case name/prefix, objective, trigger(s), primary personas, completion/terminal outcomes, SLA summary, and build-review preference if already implied. If a value was assumed, mark it with `(assumed)`.
2. **Data contract** — table `Kind | Name | Type | Source | Used for`. Include every user-facing `In` and `Out` argument, every trigger-payload variable, and every state variable that drives routing, SLAs, task inputs, or downstream outputs. Group only purely task-local one-consumer values as `task-local outputs`; do not omit case-level data by saying it appears in the SDD.
3. **Stages list** — table `Kind | # | Stage | Why it exists | Tasks to review | Entry / trigger | Completes / exits | SLA`. Include every primary and secondary stage. List primary stages first in flow order (`Kind: primary`, numbered), then secondary stages (`Kind: secondary`, `# = —`). For secondary rows, `Entry / trigger` names the interrupting signal or decision route, and `Completes / exits` says `return-to-origin`, `exit-only`, or case-close behavior. The `Tasks to review` cell lists every task in that stage as `mode: Task Name (type, persona/resource, required/optional)`, preserving sequence and fan-in: `sequential: Verify identity → Set supplier record`; `parallel: Risk review + Tax validation`; `fan-in: Onboarding decision after both`.
4. **Stage/task detail cards** — grouped bullets, one review card per stage. Each card shows: stage kind and why it is primary or secondary, entry trigger/condition, task type choices with classification rationale, activation rationale, key inputs/outputs, and any resource identity (`resolved`, concrete intended name, or `resolve at build`). For every task, name why its type fits the work and why its activation mode fits the timing (`sequential`, `parallel`, `event-driven`, `adhoc`, `fan-in`, `conditional-gate`). Every stage must have a card and every task must be named at least once across Stages list or the card.
5. **Other Paths Considered** — table `Scenario | Trigger / condition | Modeled as | Return / close behavior | Review note`. Include modeled exception/secondary paths and any intentionally unmodeled standard path when the user explicitly chose primary-flow-only. User-facing heading is exactly **Other Paths Considered**.
6. **Rules / tiers** — table `Rule | Where it applies | Data used | Outcome`. Include every conditional gate, amount/risk tier, SLA escalation rule, withdrawal/cancellation rule, rejection/needs-info route, and terminal outcome rule.
7. **Resources & integrations** — table `Family | Intended resource/system | Used by | Resolution`. Include action apps, agents, RPA/processes, API workflows, case-management children, connectors, and named external systems. `Resolution` shows the design-time outcome: `resolved (<folder>)`, the gate decision (`create during build`, `resolve at build`), or a candidate pick. A missing row is not acceptable.
8. **Decisions I made** — grouped bullets for every assumption, override, resource decision, task-type decision, activation/sequence decision, and intentionally omitted path. Use plain-language source notes (`you said "then"`; `compliance wording`; `no SLA mentioned`). Flagged items (unfixable Finalization findings, missing connections) appear here with a ⚠ marker.
9. **Review flags** — explicit `None` when empty; otherwise list the exact items the user should inspect before approving.
10. **Caller obligation** — mandatory fixed text when any §1.5 row is `Category: In` + `Type: file` (JobAttachment pre-create contract; Studio Web's "Start case" dialog handles it automatically). Omit otherwise.

**Activation mode vocabulary.** Use these user-visible labels consistently in the review: `sequential`, `parallel`, `event-driven`, `adhoc`, `fan-in`, `conditional-gate`. Use `event-driven` in chat even when the SDD field is `event-triggered`.

**Completeness gate.** The confirmation is incomplete unless it contains Case snapshot, Data contract, Stages list, Stage/task detail cards, Other Paths Considered, Rules / tiers, Resources & integrations, Decisions I made, Review flags, and Caller obligation when relevant. Do not ask `Build it...`, `Save...`, or any approval question until every section has been shown, even when a section says `None` or `Not used`. Do not replace this confirmation with a generic list of build steps, artifact names, output folder, validation commands, resource-placeholder caveats, or a summary that points to the SDD for the missing detail.

**Confirmation question (AskUserQuestion)** — options by mode:

- **Delegated build (subagent):** no question is asked — the caller presents the returned Case Review and captures the build choice itself. The report's review packet must therefore be complete enough to approve from. The caller's build-review preference — never re-asked mid-build. When ⚠ flagged items exist, relabel the first option `Build despite N flagged items — straight through`.
- **Direct design-only:** `Save the design` / `Change something`.
- **Draft request:** `Save as draft` / `Change something`. If the user's initial prompt already says to get/save a draft and stop, treat that as the `Save as draft` answer after the Case Review: write the draft immediately and stop without another approval prompt.

Corrections (`Change something` or any free text) update the model, re-run affected Finalization checks, and re-show ONLY the changed Case Review sections or rows. A correction never restarts the walk. After showing the changed sections, include a short `Suggested next steps` line before the next confirmation prompt.

**Explicit sign-off requests** ("only after I approve", "I'll review before you build") suppress nothing about the flow but add one explicit approval prompt after the confirmation is accepted and before any file is created — honor it exactly.

### Template conformance gate — before `sdd.md` is written

The exact rendered SDD text must pass this gate before it leaves the lane — in every mode against the **on-disk file assembled by the write-early cadence, before the `Status: ready` flip** (one structural Read is the check). This is a render check, not a second design review. Do not use the read to redesign the case.

Required shape:

- First heading: `# SDD — {Case Name}`.
- `## Table of Contents`, then the `## Planner Handoff` header + `<!-- planner-handoff:v1 -->` marker per the template (the blueprint TOC stays first; the handoff follows it).
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

On the confirmation's accept answer, execute the mode's terminal step (§Entry modes). **Subagent mode does NOT wait:** there is no user and no accept answer — start writing as soon as the case model's Section 1 fields settle, and run the Finalization checks against the growing on-disk file, section by section, instead of in-head first. A composition stretch longer than a few minutes with no Write is a defect in subagent mode — the seed write is the FIRST act after Sketch, not the last after checks.

**Delegated (subagent) — write earliest, then report:**

1. Seed `sdd.md` at the caller's working root the moment Sketch settles Section 1 (`Status: draft`), then append each Section 2 stage block as it is decided, then Sections 3/4 — running the relevant Finalization checks per section against the on-disk text and fixing findings by editing the file. Gate, then `ready` flip last. If an `sdd.md` appeared at that path since the lane started, abort and surface it — never overwrite.
2. Compose the final report: the complete Case Review packet (all 10 sections), `Decisions I made`, ⚠ flags, and the resolution ledger as one fenced JSON block (§Resolution ledger). The report IS the caller's approval payload — a bare "done, wrote sdd.md" return defeats the design; the caller must be able to show the review without re-reading the file.
3. Return. The caller owns the user-facing Build answer, the build preference, and every later phase.

**Direct design / draft / finalization — write early, section-batched (mandatory):**

Never compose the whole SDD in-head and Write once at the end: a long silent composition turn risks context compaction that destroys unwritten work, and the on-disk partial file is the only cheap recovery point. Cadence:

1. **Seed Write immediately** after the accept answer: title + Table of Contents + Planner Handoff header with `Status: draft`, `Template validation: pending`.
2. **Per-section Edit-appends**, in template order: Section 1 → Section 2 one stage block at a time → Section 3 → Section 4 → Next Steps. No re-Read between sibling appends. Compose each section just before its append — not the whole document up front.
3. **Gate on the on-disk file:** run the §Template conformance gate against the assembled file (one structural Read is allowed here).
4. **Ready flip is the LAST Edit:** `Status: ready`, `Template validation: passed` (drafts keep `Status: draft`). An interrupted run leaves a resumable `draft` on disk.
5. Report the path in one line. STOP — the SDD write is a turn boundary; task derivation (Lane A) or the build (`uipath-maestro-case`) continues on a later turn, opt-in. `## Next Steps` in the written SDD points at the build: load `uipath-maestro-case` with this file as `sdd.md` (its planning pass verifies the resolved identities instead of re-discovering them), or load `uipath-planner` Lane A for cross-product task derivation.

**Free-text corrections stay first-class after the terminal step:** treat one as a targeted edit to the affected artifact (model + file + downstream), narrate it in one line, continue.

## Resolution ledger

The machine-shaped record of §Tenant grounding, returned as a fenced JSON block in the delegated subagent's final report (and kept in-memory in direct mode — the SDD cells carry the identities for cross-session use). One entry per resolved/attempted lookup, exact keys: `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches` (the full exact-name match set from the refreshed cache, not a summary), `selected` (the adopted entry, or `null` after a genuine empty lookup), and `rationale` — plus a `gateDecision` field (`pick:<name>` / `resolve-at-build` / `create-during-build`) when the item went through the resolution gate. This is exactly the build skill's `tasks/registry-resolved.json` entry shape, so the caller persists it verbatim and its planning pass verifies instead of re-resolving. Connection resolutions ride the matching connector task's entry.

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

**Direct finalize fast path:** for a request that says the draft design is settled and asks for the final SDD only, read this section + §Terminal step + §Template conformance gate, the draft, and the template — once each, nothing else (§Read budget: not the authoring rules guide, not the examples file); do not read planning references, do not inspect tenant resources, do not spawn subagents or background tasks. Start the seed Write as soon as the draft is read (§Terminal step cadence), then append section by section. Treat the draft's stages, tasks, variables, conditions, SLAs, personas, and integration intent as the design source. Normalize structure only: every existing task gets a full detail block, exact `**Task envelope**` marker followed by its Required/Run Only Once/Skip Condition table, and the matching type-specific detail block. Secondary-stage task headings must be normalized to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never preserve draft letter prefixes like `R.1`, `W.1`, `CC.1`, or `ESC.1`. Preserve concrete intended resource names; leave intentionally unresolved identities `<UNRESOLVED>`. Then write the final SDD (basename per §Entry modes) and stop.

## What to say while working

Silence and machinery-talk are both experience defects. Business-language lines only (§Forbidden vocabulary):

- **Decisions narrate as they land** — the doc-read lines and inference one-liners during Listen/Sketch are the running commentary; the `Decisions I made` block is the complete record.
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
| AskUserQuestion unavailable / unresponsive (Delegate needs this) | One-line notice, continue best-assumption: every would-have-asked value gets a decision line; gate items default to `resolve at build`; promotion scoped to the request — draft request → draft file only; design-only → the final SDD on a clean Finalization pass, stop; delegated build (subagent) is already the AskUserQuestion-unavailable case — write `sdd.md` and return the review with decisions carried in it. |
| Registry pull fails (CLI error, no auth) | One plain-language line immediately. Keep concrete portable names; mark identities/folders `resolve at build` (`<UNRESOLVED>` in the file) with paired review items. The build's planning pass retries discovery. |
| `sdd.md` already exists at the caller's resolved path | Delegated mode should never have been entered — return an error report; never overwrite. |
| Caller context lost mid-delegation (compaction) | The rendered SDD text + Case Review live in the conversation; re-render from them on request. |
| Context compaction mid-render (direct/finalize) | Resume from the on-disk partial SDD: re-read it + the design source (`sdd.draft.md` or the model summary in the Case Review), append the next missing section, continue the cadence. Do NOT re-invoke skills, do NOT re-read reference guides already applied, do NOT search the filesystem, do NOT spawn background tasks — the partial file + template are sufficient. |

## Output contract — what the consumer sees

- **Delegated (subagent):** `sdd.md` on disk is the contract — the caller reads it per its trust-as-written rule; the returned Case Review powers the caller's approval gate, and the returned ledger JSON seeds its verify-only planning directly. No file from this lane.
- **Direct, cross-session:** the written SDD is the sole contract, read by any consumer exactly as if the user wrote it — Planner Handoff `Status: ready`, resolved identities in Section 2/Section 4 cells, `<UNRESOLVED>` only where deferred with review items, every process/agent/rpa/api-workflow task carrying a concrete `Resolved Resource`, every action a concrete Action App title, every case-management task a concrete `Child Case`.

## Anti-patterns

- **Do NOT return without the full Case Review + ledger in the report.** The file alone is not the deliverable — the caller's approval gate runs on the returned review, and its verify-only planning runs on the returned ledger.
- **Do NOT overwrite an existing `sdd.md`.** Presence = trust-as-written; abort and surface.
- **Do NOT interrogate.** No entry menu when the request has content, no per-dimension question walk, no confirming what the playbook decides. The budget is ONE clarifying call (when earned) + ONE confirmation (with the folded resolution gate). Uncertainty is resolved by assumption + disclosure, not by a question.
- **Do NOT hide a decision.** Every assumption, override, and resource pick appears in the `Decisions I made` block. Best-assumption without disclosure is guessing.
- **Do NOT substitute a generic build plan for the confirmation.** A "Build Plan" / "Approve this plan" list that names folders, artifacts, validation commands, primary stages, or resource caveats is not the confirmation. Show the required case-design sections first; only then may the approval question be asked.
- **Do NOT plan only the happy path.** Run the other-path sweep before confirmation and show **Other Paths Considered** even when the outcome is "primary flow only by user choice."
- **Do NOT ship a summary SDD.** The rendered text must be the full template render, not the Case Review and not a build note. Missing Section 1/2/3/4 headings, missing per-stage/per-task detail blocks, or top-level summary sections are blocking render failures.
- **Do NOT run schema discovery (`tasks describe` / `case spec`) at design time.** Identity resolution only; schemas belong to the build phases.
- **Do NOT pull the tenant registry as a prerequisite, and never twice in one session.** The login/pull chain starts only when the case first shows tenant-bound work; a pull that succeeded this session is reused by the build (its same-session fast path). Never delay the confirmation waiting for the pull.
- **Do NOT auto-pick among multiple resource matches, and do NOT re-ask at build what the gate already answered.** Ambiguity is the gate's job, once, at review time. (Single confident match adopts silently — that is the only silent pick.)
- **Do NOT scaffold projects, spawn build subagents, or execute create-on-missing here.** `Create during build` is a recorded decision the build skill executes.
- **Do NOT write `sdd.draft.md` or checkpoint files in a normal run.** The model lives in memory; drafts exist on explicit request only.
- **Do NOT ask the user to review or approve the SDD document.** The confirmation is the approval; the file is its artifact. (Subagent mode: the caller runs the approval on the returned review.) An explicit sign-off request adds one prompt — nothing else does.
- **Do NOT go silent during assembly.** Post the expectation-setter and milestone lines from §What to say while working.
- **Do NOT invent gates or thresholds.** No size limit, no approval-before-creating-files, no complexity stop.
- **Do NOT narrate filenames or schema mechanics.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
