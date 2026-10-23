# Case Design Lane — conversational case authoring

Design a Case Management SDD conversationally, then write it. `uipath-planner` is the sole case-SDD author; every case-design path, including a `uipath-maestro-case` build handoff in the same conversation, uses this lane. Run **Listen**, **Sketch**, and **Confirm**; write on acceptance. Never interrogate: use best assumptions, disclose every decision, and spend at most ONE clarifying call. Read all three sources in parallel, at most once per session, with the Read tool (never `cat`): this file owns conversation, tenant grounding, authoring, confirmation, and writing; [case-design-layers-guide.md](case-design-layers-guide.md) owns the model and every design **Default**; [`case-sdd-template.md`](../../assets/templates/case/case-sdd-template.md) owns rendering, inline cell rules, and the validation footer. This is the COMPLETE design set. Do NOT read generic Phase D references (pdd-analysis or product-selection beyond the Constraint Gate). Resolve paths from this skill's invocation base; never use `find` or global `ls`. Everything after the SDD (`caseplan.json`, validation, publishing) belongs to `uipath-maestro-case`.

**Draft finalization read budget:** read exactly once each: `sdd.draft.md`; this file's §Resumption and §Terminal step; and the template's § Validation render contract. Do not read the layers guide or planning references. Do not read tenant resources unless an identity is needed and a session exists. Spawn nothing except the conformance-gate subagent (§Template conformance gate); it reads the checklist, not you. No background tasks.

## Entry

If the request describes any case stage, work, trigger, domain, or attached document, treat it as first Listen input and skip entry prompts. A bare “create a case” gets the Listen opener; there is no entry menu. Abort is always available by free text. Tenant work never blocks entry; §Tenant grounding controls pulling.

## Tenant grounding — full resolution at design time

Resolve identities at design time through registry pull, per-resource cache lookups, connection checks, and ONE batched gate. A confirmed design carries resolved identities; build verifies rather than rediscovers them.

**Resolve identities only.** Schema discovery is build work (`tasks describe` / `case spec`). If a needed field name was not supplied, write `<UNRESOLVED>` plus a review item; never call a spec to discover it and never take field names from `--output json` envelope keys (they are PascalCased and wrong): [layers § External names](case-design-layers-guide.md#external-names--schema-fields-are-lookup-keys).

Registry data is evidence, not requirements. Never dump catalogs into chat.

1. **Seeds:** use systems, resources, apps, and connectors captured by §Listen.
2. **Kickoff:** run one background command: `uip login status --output json && uip maestro case registry pull`. In Build handoff mode start it AT LANE ENTRY, batched with the first reads; otherwise start at the first tenant-bound signal (named system/resource/connector or inferred runnable/connector/action task). A case with no tenant-bound items never pulls. Pull once per session; reuse a successful pull for the build. Best effort: do not block, delay confirmation, or surface output unprompted.
3. **Resolution pass:** after the sketch is complete and the pull succeeded, resolve every named/inferred resource in ONE parallel cache-lookup batch; check enabled connections for each connector.

| Bucket | Definition | Action |
|---|---|---|
| Single confident match | 1 exact-name match across all folders, ≥ 1 shared name token; connector has exactly 1 enabled connection | Adopt identity and exact folder into SDD cells and a resolution record; disclose as a decision. This is the only silent pick. |
| Ambiguous | Multiple matches; cross-folder same name; no token overlap; > 1 enabled connection | Queue for the gate. A name in ≥ 2 folders is always ambiguous; never silently choose a folder. |
| Empty | 0 matches / 0 enabled connections AFTER a successful pull | Queue for the gate. |

Cache files (`~/.uip/case-resources/`): agents `agent-index.json` · API workflows `api-index.json` · Coded Functions `function-index.json` · RPA processes `process-index.json` · orchestration processes `processOrchestration-index.json` · child cases `caseManagement-index.json` · business rules `businessRule-index.json` · Action Apps `action-apps-index.json` · connector activities/triggers `typecache-activities-index.json` / `typecache-triggers-index.json` · external agents `typecache-external-agent-activities-index.json` · external automations `typecache-external-automation-activities-index.json`. IXP deployments are not cached: run `uip solution resources list --kind IxpDeployment --source remote --output json` (name, key, folder) and `uip ixp deployments list <ixp-project-name> --output json` (Model Name), both read-only, in the same batch.

4. **ONE batched gate at review time:** put queued items in the §Confirm turn as one AskUserQuestion (≤ 4 questions; overflow goes into the confirmation follow-up), grouped by `(name, type)` with usages. Offer **Pick a match** (candidates with folder FQNs), **Resolve at build** (identity remains `<UNRESOLVED>` plus paired review item; build emits a placeholder), or **Create during build** only for empty `agent`, `api-workflow`, or `business-rule` lookups (record the decision; build executes it; lane never scaffolds). Never pre-judge names. If the pull is unfinished when review is ready, present pending items with resolve-at-build; never wait.
5. Show every adopted identity, connection, gate decision, and deferral in Case Review (Resources and Integrations and Decisions I Made), SDD Section 2 cells, and Section 4 roll-up. The resolution record (§Resolution ledger) is machine-only.

| Situation | Action |
|---|---|
| Not logged in, CLI absent, or pull fails | Immediately say: “I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.” Keep concrete intended names; mark identities resolve-at-build (`<UNRESOLVED>` in file) with paired review items; continue. |
| Design-only, draft, or plan-only | Skip grounding; keep intended names concrete, identities resolve-at-build, and report that wiring defers to the build. |
| Connector has zero enabled connections | Make it a gate item, never a reason to change task type. |

## Authoring policy

### Content authority hierarchy

Apply the highest applicable tier: (1) platform schema constraints—invalid task `type` values or illegal WHEN ↔ Marks-Complete pairs never ship; (2) stated or implied regulatory/compliance constraints (ECOA, NCQA, GDPR, HIPAA, SOC 2, FCRA, FINRA, …), using [case-design-layers-guide.md § Task-type override priority](case-design-layers-guide.md#task-type-override-priority); (3) matching tenant evidence—prefer type and identity, but never add/rename business work; (4) user preference; (5) user-document values; (6) layer **Defaults** ([case-design-layers-guide.md](case-design-layers-guide.md)); (7) general-practice fallback. Apply higher-tier overrides and surface them in `Decisions I Made` with `(source: <tier>-override)`.

### Domain fidelity

Transcribe business terms exactly; synonyms are defects. Preserve roles with exact casing (`CFO`, `Triage Nurse`, never `Approver`/`Manager`), domain nouns (`Vendor`, `Claim`, never `Supplier`/`Record`), stage labels, outcomes (`Approve` / `Decline` / `Needs Info`), and integration shortnames (`Workday`, not “the HR system”). Mechanical changes only: `mechanical:<derivation>` for PascalCase case name, 2–4 character UPPER prefix, and camelCase variables. A term written once gets `verbatim:"<quote>"`; confirmation renders it exactly.

### Source ledger

Use inline italic attribution in `sdd.md` (`Manual _(source: user-stated)_`; omit attribution for `user-stated`) and `Decisions I Made`. Persist rationale in every stage/task `Design Rationale` and SLA rationale; build copies it into plan entries.

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

Any non-`user-stated`, non-`verbatim` field without provenance blocks confirmation.

## Modes

Three moves only: **Listen** takes all offered input; **Sketch** completes the model by best assumption and records decisions; **Confirm** shows the complete case once and asks one question. Listen and Sketch may loop as context arrives. There is no Resolve or Approve pass; resolution runs in the background and surfaces at Confirm.

### Listen

For a bare request, send exactly:

> Tell me about the case you want to build. What kicks it off, what stages does it move through, and how does it close out? Drop in any docs you have — paths, paste, or attach.

Read every mentioned path, dragged file, or named document immediately, in parallel when possible; never ask permission. “Everything in `~/process-docs/`” means `ls` plus parallel Reads. Narrate content, not filenames, with one short line per document. For documents past ~2000 lines, read an initial chunk, narrate its signal, and decide whether more is needed. For unreadable `.docx`, `.pptx`, or scanned PDFs request one paste; read PDFs ≤ 10 pages directly. Documents added after a sketch are first-class: reread, update the model, and narrate the delta. Use named systems, deployed resources, apps, and connectors to seed grounding. Listen asks nothing beyond the opener. Gaps are filled by assumption in Sketch, not by questions.

#### Domain-vocabulary capture (during Listen)

Capture roles, domain nouns, stage labels, decision outcomes, and integration shortnames verbatim with provenance `verbatim:"<quote>"`.

#### File / attachment / document detection (during Listen)

When `file`, `attachment`, `PDF`, `upload`, `evidence`, or `receipt` denotes an artifact rather than a domain noun, choose the best pattern and record the decision. Ask only if words indicate two patterns simultaneously.

| Pattern | Indicator | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | “caller submits a PDF”, “uploaded with the request” | `Category: In`, `Type: file`; caller obligation in confirmation. |
| Connector downloads mid-case | “fetch the attachment from email”, “pull from Drive / S3” | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | “store the link”, “keep the document ID” | `Type: string` (URL) or `Type: jsonSchema` (metadata), never `file`. |

### Sketch — best assumption, every field

Complete [`case-sdd-template.md`](../../assets/templates/case/case-sdd-template.md), using each layer's **Default** ([case-design-layers-guide.md](case-design-layers-guide.md)) for every open field — decided and disclosed, never asked. Apply platform/compliance overrides and disclose them. Before Confirm, settle case name, prefix, ≥ 1 trigger, ≥ 1 stage, ≥ 1 typed task per stage, and ≥ 1 case exit. Every non-verbatim value gets a source-ledger entry and confirmation `Decisions` line. Every stage, task, and SLA gets durable rationale covering kind/type, activation/sequencing, and routing/threshold. On interactive paths keep the model in memory: no `sdd.draft.md` or partial artifact unless requested. **Bounded no-build design is the exception.**

#### Bounded no-build design — plan-only requests

For design plus implementation plan only, with no tenant work:
**Concise CONTENT, exact SHAPE.** Shape never relaxes: the template's heading skeleton holds. A freeform outline (`## 1. Case Metadata…`, `## Decisions I Made` as a body section) is a blocking render failure in this mode too.

0. **Write first, then design into the file. The seed is the FIRST tool call after the reading set — before any design reasoning, not after it:** title, `## Document History`, Planner Handoff header with `Status: draft` / `Template validation: pending`, and `## Table of Contents`. Then Edit-append one section at a time using §Terminal step cadence from the first section. Holding the whole case in memory and writing at the end is this mode's failure: it spends the turn budget on one unbounded generation pass and produces no `sdd.md` at all. On-disk bytes are recovery state. Confirmation gates only the `Status: ready` flip, not the seed. **If you have read the three files and have not yet written the seed, you are already in the failure mode.**
1. Preserve template headings, per-stage Entry/Exit Conditions TABLES and rule syntax, per-task blocks with `**Task envelope**`, and Planner Handoff. A freeform outline or body `## Decisions I Made` is blocking.
2. Keep prose concise: one rationale sentence per stage/task/SLA/exception; omit expanded examples, provenance prose, and registry audit detail.
3. Run [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md) on the written file plus a reachability spot-check, not the full closure checklist or polish iterations; build later revalidates.
4. In PROSE write bare `sla-status-change`, never a partial call with placeholder arguments.

Before confirmation, run [layers § Other-path sweep](case-design-layers-guide.md#other-path-sweep--mandatory-before-confirmation) and disclose every outcome under **Other Paths Considered**. If there is no source signal, spend the one clarifying call. Settle every blocking item in [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) by assumption and disclose each at confirmation.

#### The one clarifying call

Ask before confirmation only when: (a) no case is inferable (empty/contentless request), (b) user inputs contradict on a shape-changing field, (c) the user requested questions, or (d) the mandatory other-path sweep found no source signal. Batch into ONE AskUserQuestion call (≤ 4 questions). Unclear answers receive a best assumption and decision line; never re-press. Uncertainty alone is not a reason to ask: layer Defaults decide trigger type, task type, SLA wording, and similar gaps. There is no size gate, approval-before-file gate, or lightweight mode; only this call, confirmation, and explicit-sign-off path stop the lane.

### Confirm — the single checkpoint

First walk [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) against the in-memory model and silently fix authoring defects. Unfixable issues become Review Flags. Mechanical checks run later on the written file ([case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md)). Present Case Review with the tenant gate. The confirmation IS the plan-first approval surface — never substitute a generic build plan, and never create files on a "Yes" to one.

Coverage: SDD §1 → sections 1/4/5; §2 → sections 2/3/4/5; §3 → sections 1/6; §4 → section 6. Each business decision appears ONCE. The review omits the data contract, variables, task inputs/outputs, a second stages list, and per-stage detail cards. Anything carrying a high review item also appears in Review Flags.

Start with `## Case Review: <Case name>` and show exactly these eight sections in order:

1. **Case Snapshot** — `Item | Proposed design`; rows `Objective`, `Starts when`, `Primary personas`, `Successful completion`, `Other terminal outcomes`, `SLA coverage`; mark assumptions `(assumed)` and omit case ID prefix unless decision-relevant.
2. **Primary Journey** — `# | Stage | Purpose | Tasks | Starts when | Completes or exits when | Required? | SLA`; every primary stage once in flow order. Tasks show execution order, type, required/optional, activation/grouping — e.g. `Sequential: Capture request (Human action, required) → Validate request (RPA workflow, required)`; `After both: Make decision (Human action, required)` — including explicit event/manual triggers.
3. **Other Paths Considered** — `Scenario | Trigger or condition | Modeled as | Tasks | Interrupts active work? | Return or case outcome | Rationale`; include every modeled exception, secondary stage, optional path, alternate terminal, and standard path intentionally omitted. Include task type/required/activation.
4. **SLA and Escalations** — `Scope | SLA | Time target or condition | Status or threshold | Response | Response target | Interrupts active work? | Rationale`; one row per meaningful `(scope, SLA, status)`, separate at-risk and breached rows, only responses from [layers § Choosing the response](case-design-layers-guide.md#choosing-the-response), and `None` when no SLA. Legal interruption values come only from that table; never assume every breach creates an escalation stage.
5. **Rules and Outcomes** — `Scope | Element | Rule | When | If | Then`; business-significant routing/completion/terminal rules only, no generated sequencing or repeated SLA unless needed for routing; conditions belong in `If`, not a data column.
6. **Resources and Integrations** — `Task | Intended resource or system | Resolution`; include action apps, agents, RPA/processes, API workflows, business rules, child cases, connectors, and named external systems. Every such row is required. Resolution is `resolved (<folder>)`, `create during build`, `resolve at build`, or a candidate pick.
7. **Decisions I Made** — `Decision | Why | Provenance`; include every assumption, override, resource/task-type/activation decision, and intentionally omitted path. Use plain-language rationale; group only shared rationale and provenance. Flagged items carry ⚠.
8. **Review Flags** — `Item to review | Why it matters | Default if accepted`; use `None` if empty; include unfixable findings, missing connections, and unresolved high-impact choices.

If any §1.5 row is `Category: In` + `Type: file`, show this block after Review Flags; otherwise omit it:

    Caller obligation (file In-arg detected):
      File In-args:  <comma-separated names>
      Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
      PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
      In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
      Maestro Studio Web's "Start case" dialog does this automatically.

User-visible activation labels are `Sequential`, `Parallel`, `Parallel after predecessor`, `Event-triggered`, `Manually triggered`, `Fan-in`, and `Conditional gate`; map `adhoc` to `Manually triggered`. Prefer `Human action`, `Agent`, `RPA workflow`, `API workflow`, and `Child case` over schema enum names.

The review is incomplete unless all eight sections appear (including `None`), every stage/task is named, every modeled and intentionally omitted path is covered, every meaningful SLA response/status row appears, and the caller block appears when relevant. Never ask approval before all sections, and never substitute build steps, artifacts, folders, validation commands, or a summary pointing to the SDD.

Ask one AskUserQuestion:

| Mode | Options |
|---|---|
| Build handoff | `Build it — straight through` / `Build it — pause at the build preview` / `Change something`; with ⚠ use `Build despite N flagged items — straight through`. The build answer captures consent and build-review preference once, never re-asked mid-build. |
| Direct design-only | `Save the design` / `Change something`; with ⚠ use `Save despite N flagged items`. |
| Draft request | `Save as draft` / `Change something`. A request already saying save-and-stop is the answer; write without another prompt. |

Corrections update the model, rerun affected finalization checks, and show only changed sections/rows followed by one `Suggested next steps` line. Never restart the walk. An explicit request for sign-off adds exactly one approval prompt after acceptance and before file creation.

### Review items

Keep structured unresolved gaps in memory and show them only as confirmation `Review Flags`, never in `sdd.md`; build stores them under matching task `review_items[]` in its resolution-audit file.

```jsonc
{
  "id": "rev_<short-slug>",
  "target": "<sdd.md section path or task name>",
  "issue": "<one-sentence problem>",
  "severity": "high" | "medium" | "low",
  "next_step": "<what the user must do to resolve>"
}
```

| Level | Meaning | Examples |
|---|---|---|
| **high** | Blocks build | Missing `connectionId` / `actionAppId` / deployed runnable; unbound required input (`rev_unbound_input_<task>_<field>`); phantom extract field (`rev_phantom_output_<task>_<field>`); open variable lineage; missing trigger config; unreconciled compliance override |
| **medium** | Build defaults with a prompt | Missing escalation recipient (default = owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | Missing case / secondary-stage description; stylistic placeholder |

Any open `high` changes Build to `Build despite N flagged items`; user must choose it. Never build silently past high. Medium/low remain advisory. Never lower severity to pass the gate; severity moves only when resolved.

### Template conformance gate — before `sdd.md` is written

The template § Validation footer and the 37-item [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md) are the contract: skeleton, block markers, closed enums and gate pairings, data closure, liveness, and forbidden summary-only sections. Skeleton: `## Document History`, then `## Planner Handoff` plus `<!-- planner-handoff:v1 -->`, then `## Table of Contents`; case body follows. Run the checklist against the written file before `Status: ready` in every mode: one structural Read, then answer every item PASS or FAIL in the transcript with a verbatim file quote, judging block role/position rather than wording. No script/interpreter. This is rendering, not redesign; on failure rewrite from model and template, never create a summary SDD.

When `Agent` is available, run the checklist in ONE read-only subagent. Give it the written SDD path and [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md), not the template; require only the PASS/FAIL table with one verbatim quote per item. Do not read the checklist yourself to "check first". It must not edit or design and is never spawned per item or per family. The parent repairs and flips ready. This is the only permitted spawn. Without `Agent`, walk the same 35 items inline with identical evidence requirements; budget it as dominant cost, make targeted repairs, and do not re-answer passed items.

### Terminal step — write the SDD

Write in batches, gate, then flip. Interactive mode starts on acceptance; bounded no-build and draft finalization start at work and settle sections into an existing file. Confirmation gates only the ready flip.

1. **Seed Write, then Edit-append per section—three separate calls, never one.** Seed title, `## Document History`, Planner Handoff header with `Status: draft` and `Template validation: pending` as table rows (never HTML comment/bold line), and `## Table of Contents`. Then Edit-append in template order: Section 1; Section 2 one stage block at a time, every primary/secondary stage in source order; Section 3; Section 4; `## Next Steps`. Compose each section immediately before appending; do not re-Read between sibling appends. Partial file is recovery state. Never `cp`, `mv`, or `rsync` an artifact into place.
2. **Gate the written file:** run [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md), items 1–29 and 34–37 (also 30–33 when finalizing a draft). Answer every item with a quote, repair each FAIL with targeted Edit, and re-answer failed items only; maximum 3 rounds, then stop and report remaining failures. One structural Read is allowed.
3. Make the LAST Edit `Status: ready`, `Template validation: passed`. Drafts retain `Status: draft`; interruption leaves a resumable draft.
4. Use the user's output path when specified; otherwise:

| Mode | File | After writing |
|---|---|---|
<!--skill-flavor:build-handoff-row:start-->
| Build handoff (`uipath-maestro-case` asked for a build, no `sdd.md`) | `sdd.md` at working root; NEVER overwrite existing; abort and surface it | Do NOT stop. Build answer already consented; begin build phases immediately in this conversation (`uip solution init` plus Phase 1), verifying resolved identities rather than rediscovering them. |
<!--skill-flavor:build-handoff-row:end-->
| Direct design (design/generate a case SDD, greenfield, no PDD) | `<CASE_NAME_KEBAB>-sdd.md` | STOP — the write is a turn boundary; `## Next Steps` points to Lane A or `uipath-maestro-case` for a later opt-in turn. |
| Draft request (user asked for a reviewable draft and to stop) | `sdd.draft.md`, or `<name>-sdd.draft.md` when named | STOP; never promote a draft. |
| Draft finalization (a `sdd.draft.md` exists, user asks to finalize) | Draft basename minus `.draft` | STOP; §Resumption applies and draft remains beside final. |
| PDD-driven case (a PDD routed to Phase D, scope picked Case Management) | Standard Phase D output path ([sdd-generation-guide.md](../sdd-generation-guide.md)) | Standard Phase D flow; body still follows layers guide/template. |

Never write both `sdd.md` and `<case>-sdd.md` for one design. Report the path once. Free-text corrections after this step remain targeted edits to model, file, and downstream; narrate one line and continue.

## Resolution ledger

Keep one in-memory record per attempted/resolved registry lookup. SDD cells carry identities for cross-session use; if build runs later in the SAME session, its planning pass persists records verbatim as `tasks/registry-resolved.json` and verifies instead of re-resolving. Machine-only; user-facing outcomes belong in Resources and Integrations.

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

A `gateDecision` means the user answered and build must execute it without re-asking. A default deferral (no session, failed/pending pull, or non-interactive run) has NO `gateDecision`; build re-asks. Before a successful pull in this session, a missing cache file is failed precondition, never zero matches. Only a successful pull permits empty-lookup flow. Keep deep runtime metadata (agent prompts, package versions, endpoints, release tags) out of the SDD — SDD cells carry name, folder, identity, and sub-type only; everything else rides this record.

## HTML preview

Optional and on-request only; never offer proactively. Read [`assets/templates/case/sdd-viewer.html`](../../assets/templates/case/sdd-viewer.html), replace the `__SDD_DATA__` token inside the element with `id="sdd-data"` using JSON serialized from the live in-memory model (schema is in the template header; do not reparse SDD). Leave the second token in the later error string unchanged. Write `./sdd-viewer.html` and say: `Generated ./sdd-viewer.html — open it in a browser to review.` On failure, give one-line notice and continue. Downstream build ignores this file.

## Resumption

A `sdd.draft.md` at lane entry is leftover from an on-request draft or older run. AskUserQuestion:

| Option | Effect |
|---|---|
| `Use the draft — finalize and continue` | Read as design input, run Finalization, show §Confirm from it, continue normally. |
| `Discard draft, start fresh` | Delete draft and return to §Entry. |
| `Abort` | Exit with no file changes. |

If explicitly asked to finalize, choose Use by assumption; if AskUserQuestion is unavailable, do the same unless user asked to discard/abort.

**Direct finalize fast path:** when the user says the draft is settled and requests only the final SDD:

1. Read once each: the draft; this section plus §Terminal step and §Template conformance gate; and the template. Do not read layers/planning references, inspect tenant resources, or spawn background work. The conformance-gate subagent is the only permitted spawn.
2. Treat draft stages, tasks, variables, conditions, SLAs, personas, and integration intent as settled. Normalize structure and mechanically required pairings only; never add, drop, or rename business elements. Preserve exact stage/task display names, punctuation, task types, variables, conditions, connector placeholders, and domain rules.
3. For `user-selected-stage`, retain authored lane and give every eligible upstream primary stage a completing `required-tasks-completed` / `wait-for-user` / `Marks Stage Complete: Yes` exit. “Any active case” means every primary stage. Replace that stage's existing `required-tasks-completed | exit-only | Yes` row; never add a second completion row or `Marks Stage Complete: No`. `wait-for-user` is picker exposure, not automatic event/SLA/decision routing; add none.
4. Inventory ordered stage/task headings in memory and render one full block per entry. The template § Validation footer and [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md) define shape, including draft-parity items 30–33. Never `cp`, `mv`, `install`, or `rsync`; never delete/rename draft.
5. Expand any summary-only task into a full detail block under the same footer.
5a. A task the draft left as a summary still gets its full detail block, per that same footer — Section 2 is appended one stage block at a time (every primary and secondary stage in source order), each with its task detail blocks.
6. Preserve every draft `=js:` expression verbatim in the same owning task/stage with fields, variables, and output mapping intact.
7. **Mandatory threshold-policy scan:** scan descriptions, personas, and rationale for comparator-plus-amount phrases `>`, `<`, `≥`, `≤`, `over`, `above`, `under`, `below`, `at least`, `more/less than` next to `$5M`, `100000`, `L4`, or another amount. Every policy must also be executable in its owning task/stage. A persona scope `StageX (amount > $N only)` becomes Stages `StageX` and Notes `amount > $N only`, plus a matching HIGH-side guarded expression in a StageX table cell (Inputs/owner/recipient/WHEN/IF), such as `=js:vars.amount > N000000 ? "Role:SomeRole" : "Role:DefaultRole"`, with numeral written out (`5000000`, not `$5M`) and role/attribute on one line. An `=js:` fragment in rationale/description is not encoding. Reuse existing attribute variables; do not add/rename tasks or variables.
8. Normalize secondary headings to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; remove draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
9. Move draft SLA `At-Risk Action` / `Breach Action` values into the § SLA Response Map row for their `(scope, SLA, status)`; final SDD has no such columns and values must not be dropped.
10. Seed, append, gate, and flip per §Terminal step; never one Write. Use full checklist items 1–37, including 30–33 with draft open beside final: inventory parity, verbatim `=js:` preservation, executable threshold encoding, draft retained. Ready requires every item PASS. Repair FAILs with Edit and re-answer failed items only, maximum 3 rounds; then stop and report remainder. Quote final tally (`35/35 PASS`) as evidence, then stop.

## What to say while working

Use business-language commentary, never silence or machinery talk. Narrate decisions as they land; document-read lines and inference one-liners are the running commentary, while `Decisions I Made` is complete. Before any stretch of ~a minute without a question say: `Design confirmed — handing to the build now. Nothing needed from you for a few minutes.` At milestones give one business-language line, not per-tool-call narration. When grounding fails immediately say: `I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.` Never let `resolve at build` rows be the first signal. When continuing without a prompt, say what happens next and how to interrupt.

## Forbidden vocabulary (user-visible output)

Never surface in chat or in the SDD: internal filenames (except `sdd.draft.md` on an explicit draft request and the intentionally reported written SDD path), `<UNRESOLVED>` in narration (file-only; chat says `resolve at build`), `Listen`, `Sketch`, `Confirm`, mode names, `the validator`, `structural validation`, `the cache`, `the registry index`, `~/.uip/`, `resolution ledger`, `delegation`, `subagent mode`, `interview answers`, `from cache`, `REVIEW:`, or chain-of-thought mechanics. Explain behavior as cases, stages, tasks, triggers, SLAs, personas, connectors, and exceptions.

## Failure modes

| Symptom | Action |
|---|---|
| “skip” / “I don't know” during clarifying call | Best assumption plus decision line; optional field without basis → `—`. |
| Required field lacks basis even for assumption | Use `<UNRESOLVED: <question>>` in model and ⚠ confirmation line; build revisits. |
| AskUserQuestion unavailable/unresponsive | One-line notice; continue by assumption; every would-have-asked value gets decision line; gate items default to `resolve at build` with NO `gateDecision`; promotion is request-scoped: draft → draft only, design-only → final SDD after clean Finalization then stop, build handoff → final SDD after clean Finalization then build continues with default straight-through. |
| Registry pull fails | Immediately give plain-language tenant-failure line; keep concrete portable names; mark identity/folder resolve-at-build (`<UNRESOLVED>` in file) with review items; build planning retries. |
| Build handoff finds existing `sdd.md` at root | Surface it; handoff should not have happened; build consumes that file trust-as-written (§Terminal step). |
| Context compaction mid-render | Re-render from on-disk partial, `sdd.draft.md`, or Case Review model summary. Do not re-invoke skills, reread applied references, search filesystem, or spawn; source plus template suffice. |

## Anti-patterns

- Do NOT scaffold projects, spawn build subagents, or execute create-on-missing. `Create during build` is a recorded decision executed by build; design never writes a project.
- Do NOT ask the user to review/approve the SDD document. Confirmation is approval; the file is its artifact. Explicit sign-off adds exactly one prompt.
- Do NOT invent gates: no size, complexity, approval-before-files, or lightweight mode. Only the earned clarifying call, confirmation, and explicit-sign-off path stop the lane.