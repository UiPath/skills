# Case Design Lane — conversational case authoring

Product-specific conversational design lane for **Case Management**. This lane makes `uipath-planner` the **sole author of case SDDs**: it designs the case in the session's **in-memory model**, confirms it in ONE user checkpoint, resolves tenant resources at design time, and then writes the SDD. It replaces the interview the build skill (`uipath-maestro-case`) used to run itself; that skill hands design requests off to this lane at runtime — in the SAME conversation — and resumes the build on the Case Review's Build answer. The lane is product-agnostic in shape (Listen / Sketch / one confirmation) — BPMN and Flow can plug in later; today it is wired for Case Management.

> **Authoritative for the interview: conversation path, tenant grounding, authoring policy, review items, and the confirmation.** Case knowledge lives in exactly three files: this one (interview flow); [case-design-layers-guide.md](case-design-layers-guide.md) (the case in design layers — skeleton, gates, data, SLAs, naming, the closure checklist); and [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) (the render contract — skeleton + cell rules inline + the validation footer; worked patterns in [`case-sdd-examples.md`](../assets/templates/case-sdd-examples.md)). Deterministic shape/contract checks are mechanized by `scripts/audit_sdd.py`. Everything after the SDD (tasks.md, caseplan.json, validate, publish) is owned by `uipath-maestro-case`.

## Read budget

Read this file, [case-design-layers-guide.md](case-design-layers-guide.md) (the case model the assumptions rely on), and [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) (the render contract — its cell rules and validation footer govern the write) to begin — in parallel, each **at most once per session**. These three are the COMPLETE design reading set: do NOT read `case-sdd-examples.md` unless stuck on a specific worked pattern mid-authoring, and NEVER read `scripts/audit_sdd.py` in any mode — scripts are RUN, and their findings are the interface. Do NOT read the generic Phase D references (pdd-analysis, product-selection levels beyond the Constraint Gate) for a conversational case request — scope is already decided. Reference paths resolve relative to this skill's base directory (given at invocation) — never hunt for them with `find` / global `ls`.

**Draft finalization budget (hard):** read this file's finalize sections (§Resumption, §Terminal step) plus `sdd.draft.md` and the template (its validation footer is the gate) — once each; work from those reads. Scripts are RUN, never read (§ Read budget above) — opening `audit_sdd.py` is a budget violation in this mode too. The normalization contract (numeric `Task S{K}.{M}` headings, `**Task envelope**` markers, plain `<UNRESOLVED>` markers) lives in those sections — skipping them ships the draft's defects into the final SDD. Do NOT open [case-design-layers-guide.md](case-design-layers-guide.md) or `case-sdd-examples.md`: finalization normalizes structure, it does not redesign. No subagents, no background tasks, no tenant discovery unless identities are needed and a session exists. Write via the §Terminal step write-early cadence.

## Entry modes — who called, who writes

| Mode | Trigger | Terminal step |
|---|---|---|
| **Build handoff** | The user asked `uipath-maestro-case` to build a case but no `sdd.md` exists — it hands the design to this lane in the SAME conversation, with the user | Run the normal flow to §Confirm, with the BUILD confirmation options (build-review preference folded in — see §Confirm). On a Build answer: write **`sdd.md`** at the working root — the build skill's filename contract (never overwrite an existing one) — `Status: ready`, then hand straight back: the build skill's phases continue immediately in this conversation, reusing the in-memory model and this session's resolution outcomes. NO stop, no re-invocation, no `## Next Steps` detour. |
| **Direct design** | User (or Delegate) asks to design / generate a case SDD, greenfield, no PDD | Write `<CASE_NAME_KEBAB>-sdd.md` (user-specified output path wins), Planner Handoff `Status: ready`, report the path, STOP. Task derivation / build continue on a later turn (Lane A or `uipath-maestro-case`). |
| **Draft request** | User explicitly asks for a reviewable draft and to stop there | Write `sdd.draft.md` (or `<name>-sdd.draft.md` when the request names the file), report, STOP. Never promote. |
| **Draft finalization** | A case `sdd.draft.md` exists and the user asks to finalize it | §Resumption: read the draft as the settled design, normalize to the template, run the conformance gate, write the final SDD, STOP. Final basename derives from the draft's: `sdd.draft.md` → `sdd.md`; `<name>-sdd.draft.md` → `<name>-sdd.md`; a user-specified output path wins. |
| **PDD-driven case** | A PDD routed to Phase D and scope selection picked Case Management | Standard Phase D flow ([sdd-generation-guide.md](sdd-generation-guide.md)) — but the case body obeys [case-design-layers-guide.md](case-design-layers-guide.md) + the template's inline render contract, and grounding runs per §Tenant grounding below. |

**One output contract.** The design engine exists once; this skill ALWAYS executes the Write. The filename follows the consumer: a build handoff writes `sdd.md` at the working root (the build skill's contract); standalone direct design writes `<CASE_NAME_KEBAB>-sdd.md`. Never write `sdd.md` AND `<case>-sdd.md` for the same design, and NEVER overwrite an existing `sdd.md` at the working root — if one appears mid-run, abort the write and surface it.

## Goal

Design the case as an in-memory model shaped by the template, confirm it in ONE user prompt, then execute the mode's terminal step. The lane is **best-assumption by default**: it decides everything it can from the user's words and documents, and *informs* the user of every decision — it does not interrogate. For later sessions and re-runs the written SDD is the contract (the build skill trusts it as written); within this session, the in-memory model that produced it drives whatever comes next.

**The confirmation IS the plan-first approval surface.** If workspace or project rules require "show a plan before editing," satisfy that with the structured §Confirm Case Review below. Do not insert a separate generic "Build Plan" / "Approve this plan" checkpoint. A user "Yes" to a generic implementation plan is not a Build answer and must not create files.

## Entry

**If the request already describes the case** (any stages, work, trigger, domain, or attached docs), skip every entry prompt and go straight to work — the request IS the first Listen input. **Only a bare request** ("create a case" with nothing else) gets the Listen opener. There is no entry menu; abort is always a free-text away.

**Tenant work never blocks Entry.** Nothing about the tenant is a prerequisite for designing the case. **Build handoff mode:** fire the §Tenant grounding login+pull chain in the background AT ENTRY, in the same batch as the first document reads — the build's Phase 1 needs a fresh registry unconditionally, so starting it here costs nothing and lets resolution land before the Case Review. All other modes start grounding only when the case shows it needs it (§Tenant grounding).

## Tenant grounding — full resolution at design time

Full identity resolution at design time — registry pull, per-resource cache lookups, connection checks, one batched gate — so a confirmed design carries resolved identities and the build's planning pass verifies instead of re-discovering.

**Principles:** (1) Tenant work never blocks entry — nothing about the tenant is a prerequisite for designing. (2) Schema discovery is build work (`tasks describe` / `case spec`) — design resolves identities only. A design that needs a field name it was not given writes `<UNRESOLVED>` + a review item; it does NOT run a spec call to find out, and never takes field names from a `--output json` envelope's keys (they are PascalCased, so they are the wrong names — [layers § External names](case-design-layers-guide.md#external-names--schema-fields-are-lookup-keys)). (3) One pull per session; a pull that succeeded this session is reused by the build. Never delay the confirmation waiting for a pull. (4) Registry data is evidence, not requirements — never add or rename business work to match tenant inventory; never dump catalogs into chat.

**The contract:**

1. **Intake batch.** Read every supplied document in parallel; extract named systems, resources, likely tasks, roles. Named systems seed grounding.
2. **Chain kickoff — background.** One background command: `uip login status --output json && uip maestro case registry pull`. Kickoff TIMING is mode-bound: Build handoff starts the chain AT LANE ENTRY, batched with the first document reads; every other mode starts it at the first tenant-bound signal (a named system/resource/connector, or an inferred runnable/connector/action task); a case with no tenant-bound items never pulls. Best-effort — never block on it, never surface its output unprompted.
3. **Resolution pass — join, never wait.** When the sketch is complete and the pull succeeded, resolve every named or inferred resource in ONE parallel batch of cache lookups; for each connector also check enabled connections.

   | Bucket | Definition | Action |
   |---|---|---|
   | Single confident match | 1 exact-name match across all folders, ≥ 1 shared name token; connectors: exactly 1 enabled connection | Adopt: identity + exact folder into SDD cells + a resolution record; disclose as a decision line. The only silent pick |
   | Ambiguous | Multiple matches; cross-folder same name; no token overlap; > 1 enabled connection | Queue for the gate. A name deployed in ≥ 2 folders is always ambiguous — never pick a folder silently |
   | Empty | 0 matches / 0 enabled connections AFTER a successful pull | Queue for the gate |

   Cache files (`~/.uip/case-resources/`): agents `agent-index.json` · API workflows `api-index.json` · RPA processes `process-index.json` · orchestration processes `processOrchestration-index.json` · child cases `caseManagement-index.json` · Action Apps `action-apps-index.json` · connector activities/triggers `typecache-activities-index.json` / `typecache-triggers-index.json`.

4. **The ONE batched gate — at review time.** Queued items ride the §Confirm turn as one AskUserQuestion (≤ 4 questions; overflow carries into the confirmation's follow-up), grouped by `(name, type)` with usages listed. Options per group: **Pick a match** (candidates with folder FQNs); **Resolve at build** (identity stays `<UNRESOLVED>` + a paired review item; the build emits a placeholder); **Create during build** (ONLY for empty `agent` / `api-workflow` lookups — records the decision, the build executes it; the lane never scaffolds). Never pre-judge by name heuristics — the user's call. Pull unfinished when the review is ready → present with resolve-at-build on pending items; never wait.
5. **Visibility.** Every adopted identity, connection, gate decision, and deferral appears in the Case Review (Resources and Integrations + Decisions I Made) and lands in SDD Section 2 cells and the Section 4 roll-up. The per-lookup resolution record (§Resolution ledger below) is machine-only — never user-facing.

**No session / failures:**

| Situation | Action |
|---|---|
| Not logged in, CLI absent, pull fails | One plain-language line the moment it happens: "I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build." Keep concrete intended names; mark identities resolve-at-build (`<UNRESOLVED>` in the file) with paired review items; continue |
| Design-only / draft / plan-only runs | Skip grounding entirely — intended names stay concrete, identities resolve-at-build, report that resource wiring defers to the build run |
| Connector with zero enabled connections | A gate item — never a reason to change the task type |

## Authoring policy

**Content authority hierarchy.** When signals conflict, the highest tier wins: (1) **Platform schema constraints** — schema-invalid values never ship, regardless of source (a task `type` outside the closed enum, an illegal WHEN ↔ Marks-Complete pair). (2) **Regulatory / compliance constraint** stated or implied (ECOA, NCQA, GDPR, HIPAA, SOC 2, FCRA, FINRA, …) — forces task types ([case-design-layers-guide.md § Task-type override priority](case-design-layers-guide.md#task-type-override-priority)). (3) **Tenant evidence** — a deployed resource in the registry cache matching described work; prefer its type and identity; never add stages/tasks or rename business work to match tenant inventory. (4) **User-stated preference** in chat. (5) **Doc-extracted values** from user-shared documents. (6) **Inferred defaults** — each layer's stated **Default** ([case-design-layers-guide.md](case-design-layers-guide.md)). (7) **General-practice fallback.** Apply a higher-tier override AND surface it in the confirmation's `Decisions I Made` table with provenance `(source: <tier>-override)`.

**Domain fidelity.** Transcribe business terms; never paraphrase. Verbatim: roles (`CFO`, `Triage Nurse` — never `Approver`/`Manager`), domain nouns (`Vendor`, `Claim` — never `Record`/`Item`), stage labels (user's casing), decision outcomes (`Approve`/`Decline`/`Needs Info` — not synonyms), integration shortnames (`Workday`, never "the HR system"). Allowed mechanical normalization (`mechanical:<derivation>`): PascalCase Case Name, 2–4 char UPPER prefix, camelCase variables. Synonyms are a fidelity defect, not polish. A term the user wrote once carries `verbatim:"<quote>"`; the confirmation renders it exactly — that display is the spelling check.

**Source ledger (provenance).** Two surfaces: inline italic attribution in `sdd.md` (`Manual _(source: user-stated)_`; omit for `user-stated`) and `Decisions I Made`. Rationale is durable, not chat-only — persist it in each stage/task `Design Rationale` and SLA rationale field (the build copies it into its plan entries).

| Kind | When |
|---|---|
| `user-stated` | User wrote the value in chat (no annotation needed). Paraphrase acceptable. |
| `verbatim:"<quote>"` | Rendered cell is exactly the user's phrase — strongest signal; preferred for customer-named entities. Truncate the quote at 40 chars in the ledger. |
| `user-doc:<filename>` | Lifted from a user-shared document |
| `mechanical:<derivation>` | One-step derivation (`mechanical:PascalCase→prefix`) |
| `compliance-override:<rule>` | Regulatory constraint forced the value (`compliance-override:ECOA→action`) |
| `tenant-registry:<resource-name>` | Resolved from the registry cache |
| `connector-priority:<connector>` | Tier 3/tenant evidence selected `execute-connector-activity` over `api-workflow` |
| `inferred-default:<reason>` | Defaulted with no matching source (use sparingly) |

A non-`user-stated`, non-`verbatim` field without provenance blocks the confirmation until annotated.

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

Capture verbatim into the model: **roles** (exact casing — `CFO`, `Triage Nurse`), **domain nouns** (`Vendor` vs `Supplier` — never homogenize), **stage labels**, **decision outcomes** (`Approve` / `Decline` / `Needs Info`, not synonyms), **integration shortnames** (`Workday`, never "the HR system"). Provenance `verbatim:"<quote>"` per §Authoring policy. Synonym drift is a fidelity defect (§Authoring policy — Domain fidelity).

#### File / attachment / document detection (during Listen)

When the user mentions `file`, `attachment`, `PDF`, `upload`, `evidence`, `receipt` (as artifact, not domain noun), pick the best-matching pattern from the indicators and record the decision — ask only if the user's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file`; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

### Sketch — best assumption, every field

Fill the complete SDD shape against [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) from what Listen captured. Every open field takes the **Default** stated in its layer ([case-design-layers-guide.md](case-design-layers-guide.md)) — decided and disclosed, never asked. Platform schema and compliance constraints override user phrasing (§Authoring policy): apply silently, then surface as a decision line.

Settle before Confirm: case name, prefix, ≥ 1 trigger, ≥ 1 stage, ≥ 1 typed task per stage, ≥ 1 case exit — by user input or by layer default.

Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. Every stage, task, and configured SLA gets a durable `Design Rationale` covering kind/type, activation/sequencing, and the routing/threshold choice. Resources resolve per §Tenant grounding. The model lives in memory — **no draft file, no checkpoint writes**.

**Bounded no-build design — plan-only requests.** When the request explicitly stops before `caseplan.json` (design + implementation plan only, tenant work forbidden), prefer progress over exhaustive internal auditing: once the model covers the stated stages, tasks, global interrupts, SLAs, variables, resources, and rationales — write. **Bounded means concise CONTENT, exact SHAPE.**

1. **Shape is never relaxed.** The template's heading skeleton (`# SDD — {Case Name}`, `## Table of Contents`, `## Section 1: Case Definition` … `## Section 4: Integrations`), the per-stage Entry/Exit Conditions TABLES (rule syntax included — e.g. named-args `sla-status-change(...)` rows), the per-task detail blocks with `**Task envelope**`, and the Planner Handoff header all hold. A freeform outline (`## 1. Case Metadata…`, `## Decisions I Made` as a body section) is a blocking render failure in this mode too.
2. **Conciseness lives ONLY in prose depth.** One short rationale sentence per stage/task/SLA/exception choice; do not expand optional examples, provenance prose, or registry audit detail.
3. **The gate is the script, not the checklist.** Do NOT run the full Finalization checklist. Run `audit_sdd.py` on the written file (enforcement families: template § Validation) plus a reachability spot-check.
4. **In PROSE, reference the rule as bare `sla-status-change`** — never a partial call form with placeholder args; build-side checkers reject wrong arity anywhere.
5. **Thresholded policy is executable, not narrative** — [layers § Expressions](case-design-layers-guide.md#expressions).
6. **Do not iterate for polish.** The later build run re-validates everything.
7. **Write cadence.** This bound applies on top of the seed-first cadence (§Terminal step): AFTER the accept answer a fresh design writes early and per-section; before it the model stays in memory (no draft file, no checkpoint writes).

*Prompt-shaped clauses — these exist because specific eval prompts require them, and they are not part of the durable contract. Keep them separable; if one stops earning its place, delete it rather than generalizing it.*

- When the prompt says **every primary phase/stage has an SLA target**, render each per the template's Stage SLA block (deterministic default titles are in its SLA Title cell) with concrete titles and at-risk/breach display names; every `sla-status-change` reference uses those exact titles, and the § SLA Response Map carries the responses (breach into a lane reads `enter-stage: <Secondary Stage Name>`, never `Notify: <role>`).

**Conditional role / step gates must be inspectable.** Encoding rule: [layers § Expressions](case-design-layers-guide.md#expressions) (thresholded policy lands in an executable cell, numeral written out). Lane-specific addition: keep the business phrase on the same line as the numeral so a reviewer and a mechanical grep both see actor and threshold together — `Credit Analyst route when loanAmount > 5000000`. Never leave the gate only in a persona table or detached prose.

**Other-path sweep — mandatory before confirmation.** Owned by [case-design-layers-guide.md § Other-path sweep](case-design-layers-guide.md#other-path-sweep--mandatory-before-confirmation):
sweep the standard scenarios, pick the smallest faithful model per path, disclose everything in **Other
Paths Considered**; when the source has no signal at all, spend the one bounded question.

**Closure.** Settle every blocking item of [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) by assumption and surface each in the confirmation — they are where designs silently become unbuildable. (The same list is re-walked at §Confirm.)

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, (c) the user asked to be asked, or (d) the mandatory other-path sweep found no source signal at all. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" — STOP: the playbook decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in this lane are the one clarifying call (when earned), the confirmation itself (with its folded resolution gate), and the explicit-sign-off path.

### Confirm — the single checkpoint

Walk [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) against the in-memory model FIRST — fix failures silently (they are authoring defects, not user decisions); anything unfixable becomes a Review Flags row (§Review items). The mechanical shape/contract checks run later, on the written file (`audit_sdd.py` — template § Validation). Then present the Case Review. The §Tenant grounding resolution gate (when it has items) rides this same turn. The confirmation IS the plan-first approval surface — never substitute a generic build plan, and never create files on a "Yes" to one.

**The Case Review — eight sections, one question.** A decision-first business approval surface, complete enough to approve the case behavior without opening any SDD file — never a generic build plan and never a compressed SDD copy. Coverage: SDD §1 → sections 1/4/5; §2 → sections 2/3/4/5; §3 → sections 1/6; §4 → section 6. The review intentionally omits the data contract, variables, and task inputs/outputs — those stay complete in the SDD. Anything carrying a high review item also appears in Review Flags.

Start with `## Case Review: <Case name>`, then exactly this order:

1. **Case Snapshot** — `Item | Proposed design`. Rows: `Objective`, `Starts when`, `Primary personas`, `Successful completion`, `Other terminal outcomes`, `SLA coverage`. Assumed values marked `(assumed)`. No case ID prefix unless it affects a decision.
2. **Primary Journey** — `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? | SLA`. Every primary stage once, flow order. `Tasks` cell: every task in execution order with type, required/optional, activation/grouping — e.g. `Sequential: Capture request (Human action, required) → Validate request (RPA workflow, required)`; `After both: Make decision (Human action, required)`. Event-triggered and manually triggered shown explicitly.
3. **Other Paths Considered** — `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active work? | Return or case outcome | Rationale`. Every modeled exception, secondary stage, optional path, alternate terminal — AND standard paths intentionally unmodeled when that omission is a decision. Path tasks carry type/required/activation.
4. **SLA and Escalations** — `Scope | SLA | Time target or condition | Status or threshold | Response | Response target | Interrupts active work? | Rationale`. One row per meaningful `(scope, SLA, status)`; separate at-risk and breached rows when both exist; responses from the closed set ([layers § Choosing the response](case-design-layers-guide.md#choosing-the-response)). Interrupting cell: per the Response column's row in [layers § Choosing the response](case-design-layers-guide.md#choosing-the-response) — that table is the only home for which values are legal. `None` when no SLA. Never assume every breach creates an escalation stage.
5. **Rules and Outcomes** — `Scope | Element | Rule | When | If | Then`. Business-significant routing/completion/terminal rules only; omit generated sequencing visible in `Tasks`; no SLA repeats unless needed for routing; business conditions in `If`, no data column.
6. **Resources and Integrations** — `Task | Intended resource or system | Resolution`. Action apps, agents, RPA/processes, API workflows, child cases, connectors, named external systems. `Resolution` = design-time outcome: `resolved (<folder>)`, `create during build`, `resolve at build`, or a candidate pick. A missing row is not acceptable.
7. **Decisions I Made** — `Decision | Why | Provenance`. Every assumption, override, resource/task-type/activation decision, and intentionally omitted path, plain language (`you said "then"`, `compliance wording`, `no SLA mentioned`). Group only decisions sharing rationale AND provenance. Flagged items carry ⚠.
8. **Review Flags** — `Item to review | Why it matters | Default if accepted`. `None` when empty. Unfixable findings, missing connections, unresolved high-impact choices.

After Review Flags, when any §1.5 row is `Category: In` + `Type: file`, show this fixed block (omit otherwise — a conditional build obligation, not a ninth section):

```
Caller obligation (file In-arg detected):
  File In-args:  <comma-separated names>
  Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
  PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
  In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
  Maestro Studio Web's "Start case" dialog does this automatically.
```

**Product vocabulary.** User-visible activation labels: `Sequential`, `Parallel`, `Parallel after predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, `Conditional gate` (`adhoc` → `Manually triggered`). Prefer product task labels — `Human action`, `Agent`, `RPA workflow`, `API workflow`, `Child case` — over schema enum names.

**No duplicated review surfaces.** Each business decision appears once. No Data Contract section, variable rows, task I/O rows, second stages list, or per-stage detail cards — technical detail stays in the SDD.

**Completeness gate.** Incomplete unless: all eight sections shown, every stage and task named, every modeled and intentionally omitted path covered, every meaningful SLA response/status row present, Caller obligation when relevant. No approval question before every section has been shown — even sections reading `None`. Never substitute a list of build steps, artifacts, folders, or validation commands, or a summary that points at the SDD for a missing business decision.

**Confirmation question (one AskUserQuestion)** — options by mode:

| Mode | Options |
|---|---|
| Build handoff | `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. The Build answer is the consent AND the build-review preference, captured once, never re-asked mid-build. With ⚠ flags: first option reads `Build despite N flagged items — straight through` |
| Direct design-only | `Save the design` / `Change something` (⚠ → `Save despite N flagged items`) |
| Draft request | `Save as draft` / `Change something`. A prompt that already says save-a-draft-and-stop counts as the answer: write immediately, no extra prompt |

Corrections (`Change something` or free text) update the model, re-run the affected Finalization checks, and re-show ONLY the changed sections or rows, then one `Suggested next steps` line before the next prompt. A correction never restarts the walk. **Explicit sign-off requests** ("only after I approve") add exactly one approval prompt after acceptance, before any file is created — nothing else changes.

### Review items

Structured gap escalations — a field could not be fully resolved but the build needs the context. Live in the in-memory model; surface ONLY as `Review Flags` rows in the confirmation — never in the `sdd.md` body. The build persists them under the matching task's `review_items[]` in its resolution audit file.

```jsonc
{
  "id": "rev_<short-slug>",
  "target": "<sdd.md section path or task name>",
  "issue": "<one-sentence problem>",
  "severity": "high" | "medium" | "low",
  "next_step": "<what the user must do to resolve>"
}
```

| Level | Definition | Examples |
|---|---|---|
| **high** | Blocks the build until resolved | Missing `connectionId` / `actionAppId` / deployed runnable; unbound required input (`rev_unbound_input_<task>_<field>`); phantom extract field (`rev_phantom_output_<task>_<field>`); open variable lineage; missing trigger config; unreconciled compliance override |
| **medium** | Build defaults with a prompt | Missing escalation recipient (default = owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | Missing case / secondary-stage description; stylistic placeholder |

**Gate behavior:** any open `high` item relabels the confirmation's Build option `Build despite N flagged items` — the user must pick it; silently building past `high` is forbidden. `medium`/`low` are advisory rows. Never downgrade a severity to pass the gate — it moves only when the underlying issue resolves.

### Template conformance gate — before `sdd.md` is written

Mechanized by `audit_sdd.py` — the template's § Validation footer is the contract (document skeleton, per-block markers, forbidden summary-only sections). Run it against the **on-disk file assembled by the write-early cadence, before the `Status: ready` flip** — in every mode; one structural Read is allowed to repair findings. This is a render check, not a second design review; on failure, rewrite from the model and template — never a summary SDD, even if a later `caseplan.json` would validate.

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

One record per resolved or attempted registry lookup, kept in-memory; the SDD cells carry identities for
cross-session use; when the build runs later in the SAME session, its planning pass persists these records
verbatim as `tasks/registry-resolved.json` and verifies instead of re-resolving. **Machine data — never
user-facing** (Resources and Integrations carries every user-relevant outcome).

```jsonc
{
  "stage": "<SDD stage name>",
  "task": "<SDD task name>",
  "taskType": "<task type>",
  "cacheFile": "<index basename actually searched>",
  "searchQuery": "<lookup string>",
  "matches": [ /* FULL exact-name match set from the refreshed cache — never a summary */ ],
  "selected": { /* adopted entry */ },        // null after a genuine empty lookup
  "rationale": "<why>",
  "gateDecision": "pick:<name>" | "resolve-at-build" | "create-during-build"  // only when the user answered
}
```

1. `gateDecision` present = the user answered the gate; the build executes it without re-asking. A defaulted deferral (no session, failed/pending pull, non-interactive run) carries NO `gateDecision` — the build's own gate re-asks.
2. Before a successful pull this session, a missing cache file is a failed precondition — never a zero-match result. Only after a successful pull may an empty match set enter the empty-lookup flow.
3. Deep runtime metadata (agent prompts, package versions, endpoints, release tags) stays out of the SDD — name + folder + identity + sub-type only; everything else rides this record.

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
5. Render every block to the template's shape contract — per-stage and per-task markers, the exact type-specific detail headings and bold field labels (`**Timer:**` stays `**Timer:**`), `**Type:** Stage` on every stage block, Section 3/4 column headers verbatim, real newlines. That contract lives in [`case-sdd-template.md`](../assets/templates/case-sdd-template.md) § Validation and is enforced by `audit_sdd.py` (step 12) — it is not restated here, and a compact or renamed layout drops the folder/identity/IO contract.
6. When the draft has only task summaries, fill concise default detail tables. Every `process` / `agent` / `rpa` / `api-workflow` task ends with:

   ```markdown
   ###### Process / Agent / RPA / API Workflow Task Detail

   **Resolved Resource:** {draft's intended resource name; when the draft names none, the task display name — never <UNRESOLVED>}
   **Folder Path:** <UNRESOLVED>
   **Resource Identity:** <UNRESOLVED>
   ```

   Keep concrete folder/identity values the draft already supplies.
7. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block, with its field names, variable references, and output mapping intact — an equivalent-looking shorthand that drops an input, predicate, or intermediate field is a failure, not a simplification.
8. Threshold-policy conversion — MANDATORY scan, not optional polish. Scan the draft (descriptions, personas table, rationale) for comparator + amount phrases: `>`, `<`, `≥`, `≤`, `over`, `above`, `under`, `below`, `at least`, `more/less than` next to an amount (`$5M`, `100000`, `L4`). EVERY such policy must also appear in an executable cell of the owning task or stage in the final — prose-only is a render failure:
    - A personas row like `SomeRole | StageX (amount > $N only)` REQUIRES a matching guarded expression inside a StageX task block, phrased on the HIGH side and assigning the exception role: an owner/recipient cell or entry-condition IF cell containing `=js:vars.amount > N000000 ? "Role:SomeRole" : "Role:DefaultRole"` — the numeral written out (`5000000`, not `$5M`), the role and attribute on the same line. The expression lives in a table cell (Inputs/owner/recipient/WHEN/IF); an `=js:` fragment inside `**Design Rationale:**` or `**Description:**` prose is NOT an encoding and fails the gate.
    - Reuse an existing variable that carries the attribute; the conversion never adds or renames a task or variable.
    - Persona prose and Design Rationale alone are not final.
9. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
10. A draft's per-stage SLA table may carry `At-Risk Action` / `Breach Action` columns; the final SDD does not. Move each response into the § SLA Response Map row for that `(scope, SLA, status)` — never drop it, never keep the column.
11. Compose the complete finalized document from the draft and write it in ONE Write — Sections 1–4 with every primary/secondary stage in source order inside Section 2 (the draft is the recovery point; on interruption, re-finalize from it). After the Write, repair audit findings with targeted Edits only. Never append a deferred or omitted stage after `## Section 3`; place it at its Section 2 position.
12. Audit loop — MANDATORY, not optional: the finalized SDD is unpresentable and the `ready` flip is forbidden until this prints `AUDIT OK`. Run the skill's deterministic auditor on the written file (read-only):

    ```bash
    python3 "<this skill's folder>/scripts/audit_sdd.py" <final SDD path> --draft <draft path>
    # python3 absent (common on Windows) → retry the same line with `python`, then `py`
    ```

    On `AUDIT FAIL`, repair each finding with Edit and re-run; repeat until it prints `AUDIT OK` (max 3 rounds — then stop and present the remaining findings). Only if `python3`, `python`, and `py` are all unavailable, verify manually against the enforcement list in the template's § Validation footer — every item must hold.
13. Then flip `ready` (§Terminal step), write the final SDD basename per §Entry modes, and stop; quote the audit's final `AUDIT OK` line in the reply as evidence.

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
- **Do NOT run schema discovery (`tasks describe` / `case spec`) at design time.** Identity resolution only; schemas belong to the build phases. An unknown field name is `<UNRESOLVED>` + a review item — not a spec call, and not a name invented to look plausible.
- **Do NOT block on the tenant registry, and never pull twice in one session.** The login/pull chain runs in the background — entry-time in Build handoff mode, first-tenant-bound-work otherwise (§Tenant grounding); a pull that succeeded this session is reused by the build (its same-session fast path). Never delay the confirmation waiting for the pull.
- **Do NOT auto-pick among multiple resource matches, and do NOT re-ask at build what the gate already answered.** Ambiguity is the gate's job, once, at review time. (Single confident match adopts silently — that is the only silent pick.)
- **Do NOT scaffold projects, spawn build subagents, or execute create-on-missing here.** `Create during build` is a recorded decision the build skill executes.
- **Do NOT write `sdd.draft.md` or checkpoint files in a normal run.** The model lives in memory; drafts exist on explicit request only.
- **Do NOT ask the user to review or approve the SDD document.** The confirmation is the approval; the file is its artifact. An explicit sign-off request adds one prompt — nothing else does.
- **Do NOT go silent during assembly.** Post the expectation-setter and milestone lines from §What to say while working.
- **Do NOT invent gates or thresholds.** No size limit, no approval-before-creating-files, no complexity stop.
- **Do NOT narrate filenames or schema mechanics.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
