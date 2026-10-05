# Case Design Lane — conversational case authoring

Design a Case Management SDD in conversation, then write it. `uipath-planner` is the sole author of case SDDs; every case design path runs through this lane, including a build handoff from `uipath-maestro-case` (same conversation, same user). Run three moves — **Listen**, **Sketch**, **Confirm** — and write on the accept answer. Never interrogate: decide by best assumption, disclose every decision, spend at most ONE clarifying call.

Case knowledge is split three ways. Read all three to begin, in parallel, **at most once per session**:

| File | Owns |
|---|---|
| this file | the conversation: entry, tenant grounding, authoring policy, the one confirmation, the write |
| [case-design-layers-guide.md](case-design-layers-guide.md) | the case model and every design **Default** — skeleton, gates, data, SLAs, naming, the closure checklist |
| [`case-sdd-template.md`](../../assets/templates/case/case-sdd-template.md) | the render contract — skeleton, cell rules inline, validation footer |

That is the COMPLETE design reading set. Do NOT read the generic Phase D references (pdd-analysis, product-selection beyond the Constraint Gate): scope is already decided. Reference paths resolve against this skill's base directory, given at invocation — never hunt with `find` / global `ls`. Open all three with the Read tool, never `cat`. Everything after the SDD (caseplan.json, validate, publish) belongs to `uipath-maestro-case`.

**Draft finalization — read budget (hard).** Read exactly these, once each:

| Read | Not |
|---|---|
| `sdd.draft.md` | the layers guide — finalization normalizes structure, it does not redesign |
| this file's §Resumption and §Terminal step | any planning reference |
| the template, for its § Validation render contract | tenant resources, unless an identity is needed and a session exists |

Spawn nothing, except the checklist subagent in the §Template conformance gate fallback when the CLI has no `sdd` command. No background tasks.

## Entry

Request already describes the case (any stages, work, trigger, domain, or attached docs) → skip every entry prompt, go straight to work; the request IS the first Listen input. Bare request ("create a case", nothing else) → the Listen opener. No entry menu. Abort is always a free-text away. Tenant work never blocks entry (§Tenant grounding owns when the pull starts).

## Tenant grounding — full resolution at design time

Resolve identities at design time — registry pull, per-resource cache lookups, connection checks, ONE batched gate — so a confirmed design carries resolved identities and the build verifies instead of re-discovering.

**Resolve identities only.** Schema discovery is build work (`tasks describe` / `case spec`). A design that needs a field name it was not given writes `<UNRESOLVED>` + a review item; it never runs a spec call to find out, and never takes field names from a `--output json` envelope's keys — those are PascalCased, so they are the wrong names ([layers § External names](case-design-layers-guide.md#external-names--schema-fields-are-lookup-keys)).

**Registry data is evidence, not requirements.** Never add or rename business work to match tenant inventory. Never dump catalogs into chat.

1. **Seeds.** The systems, resources, apps, and connectors §Listen captured are the lookup set.
2. **Chain kickoff — background.** One background command: `uip login status --output json && uip maestro case registry pull`. Kickoff TIMING is mode-bound: Build handoff starts the chain AT LANE ENTRY, batched with the first document reads; every other mode starts it at the first tenant-bound signal (a named system/resource/connector, or an inferred runnable/connector/action task); a case with no tenant-bound items never pulls. ONE pull per session — a pull that succeeded this session is reused by the build. Best-effort: never block on it, never delay the confirmation for it, never surface its output unprompted.
3. **Resolution pass — join, never wait.** When the sketch is complete and the pull succeeded, resolve every named or inferred resource in ONE parallel batch of cache lookups; for each connector also check enabled connections.

   | Bucket | Definition | Action |
   |---|---|---|
   | Single confident match | 1 exact-name match across all folders, ≥ 1 shared name token; connectors: exactly 1 enabled connection | Adopt: identity + exact folder into SDD cells + a resolution record; disclose as a decision line. The only silent pick |
   | Ambiguous | Multiple matches; cross-folder same name; no token overlap; > 1 enabled connection | Queue for the gate. A name deployed in ≥ 2 folders is always ambiguous — never pick a folder silently |
   | Empty | 0 matches / 0 enabled connections AFTER a successful pull | Queue for the gate |

   Cache files (`~/.uip/case-resources/`): agents `agent-index.json` · API workflows `api-index.json` · Coded Functions `function-index.json` · RPA processes `process-index.json` · orchestration processes `processOrchestration-index.json` · child cases `caseManagement-index.json` · Action Apps `action-apps-index.json` · connector activities/triggers `typecache-activities-index.json` / `typecache-triggers-index.json`.

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

**Domain fidelity.** Transcribe business terms, never paraphrase — the categories captured verbatim are listed at §Domain-vocabulary capture. A synonym is a fidelity defect, not polish. Only these mechanical normalizations are allowed (`mechanical:<derivation>`): PascalCase case name, 2–4 char UPPER prefix, camelCase variables. A term the user wrote once carries `verbatim:"<quote>"` and the confirmation renders it exactly — that display is the spelling check.

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

- **Reads everything mentioned — never asks permission.** Path, dragged file, named doc → read immediately, in parallel when multiple. "Everything in `~/process-docs/`" → `ls` + parallel Reads.
- **Narrates content, not filenames.** One short line per doc about *what's in it*: `vendor-onboarding.md — 4 stages (Intake → Compliance → Finance → Activation), 2 personas, 8-hour SLA on Compliance.`
- **Partial reads for huge docs.** Past ~2000 lines, read the first chunk, narrate the signal, decide if more is needed. Unreadable formats (`.docx`, `.pptx`, scanned PDFs) → one paste request; PDFs ≤ 10 pages read directly.
- **Mid-flow docs are first-class.** New doc after the sketch exists → re-read, update the model, narrate the delta.
- **Named systems seed grounding.** Deployed resources, apps, connectors, systems named by the user feed §Tenant grounding.

Listen asks nothing beyond the opener. Gaps are filled by assumption in Sketch, not by questions.

#### Domain-vocabulary capture (during Listen)

Capture verbatim into the model, provenance `verbatim:"<quote>"`: **roles** (exact casing — `CFO`, `Triage Nurse`, never `Approver`/`Manager`), **domain nouns** (`Vendor`, `Claim` — never homogenized to `Supplier`/`Record`), **stage labels** (user's casing), **decision outcomes** (`Approve` / `Decline` / `Needs Info`, not synonyms), **integration shortnames** (`Workday`, never "the HR system").

#### File / attachment / document detection (during Listen)

When the user mentions `file`, `attachment`, `PDF`, `upload`, `evidence`, `receipt` (as artifact, not domain noun), pick the best-matching pattern from the indicators and record the decision — ask only if the user's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file`; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

### Sketch — best assumption, every field

Fill the complete SDD shape against [`case-sdd-template.md`](../../assets/templates/case/case-sdd-template.md) from what Listen captured. Every open field takes the **Default** stated in its layer ([case-design-layers-guide.md](case-design-layers-guide.md)) — decided and disclosed, never asked. Platform schema and compliance constraints override user phrasing (§Authoring policy): apply silently, then surface as a decision line.

Settle before Confirm: case name, prefix, ≥ 1 trigger, ≥ 1 stage, ≥ 1 typed task per stage, ≥ 1 case exit — by user input or by layer default.

Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. Every stage, task, and configured SLA gets a durable `Design Rationale` covering kind/type, activation/sequencing, and the routing/threshold choice. Resources resolve per §Tenant grounding. On the interactive path the model lives in memory until the confirmation — no `sdd.draft.md`, no partial artifact the user did not ask for. **Bounded no-build design is the exception: it writes first. See the block below.**

**Bounded no-build design — plan-only requests.** Request stops before `caseplan.json` (design + implementation plan only, tenant work forbidden). **Concise CONTENT, exact SHAPE.**

0. **Write first, then design into the file. The seed is the FIRST tool call after the reading set — before any design reasoning, not after it.** Its content is fixed and depends on nothing you have yet decided, so nothing about the design may precede it: title, `## Document History`, the Planner Handoff header at `Status: draft` / `Template validation: pending`, `## Table of Contents`. Then Edit-append one section at a time as each settles — §Terminal step owns the exact cadence, and it applies here from the first section, not after the confirmation. Holding the whole case in memory and writing at the end is this mode's failure, not a stylistic preference: it spends the turn budget on one unbounded generation pass and produces no `sdd.md` at all. Bytes on disk are the recovery point and each append bounds the turn. The confirmation still gates the `Status: ready` flip; it never gated the seed. **If you have read the three files and have not yet written the seed, you are already in the failure mode.**

1. **Shape never relaxes.** The template's heading skeleton, the per-stage Entry/Exit Conditions TABLES (rule syntax included), the per-task detail blocks with `**Task envelope**`, and the Planner Handoff header all hold. A freeform outline (`## 1. Case Metadata…`, `## Decisions I Made` as a body section) is a blocking render failure in this mode too.
2. **Concision lives only in prose depth.** One rationale sentence per stage/task/SLA/exception choice; no expanded examples, provenance prose, or registry audit detail.
3. **The gate is the CLI.** Run `uip maestro case sdd validate` on the written file (§Terminal step 3) plus a reachability spot-check — no checklist walk unless its fallback applies, and no polish iterations; the later build run re-validates everything.
4. **In PROSE reference the rule as bare `sla-status-change`** — never a partial call form with placeholder args; build-side checkers reject wrong arity anywhere.

**Other-path sweep — mandatory before confirmation.** Run [layers § Other-path sweep](case-design-layers-guide.md#other-path-sweep--mandatory-before-confirmation) and disclose every outcome in the confirmation's **Other Paths Considered**. No source signal at all → spend the one clarifying call.

**Closure.** Settle every blocking item of [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) by assumption and surface each in the confirmation — they are where designs silently become unbuildable. (The same list is re-walked at §Confirm.)

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, (c) the user asked to be asked, or (d) the mandatory other-path sweep found no source signal at all. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" — STOP: each layer's stated **Default** decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in this lane are the one clarifying call (when earned), the confirmation itself (with its folded resolution gate), and the explicit-sign-off path.

### Confirm — the single checkpoint

Walk [case-design-layers-guide.md § Layer closure](case-design-layers-guide.md#layer-closure--the-design-checklist) against the in-memory model FIRST — fix failures silently (they are authoring defects, not user decisions); anything unfixable becomes a Review Flags row (§Review items). The mechanical shape/contract checks run later, on the written file (`uip maestro case sdd validate`, §Terminal step 3). Then present the Case Review. The §Tenant grounding resolution gate (when it has items) rides this same turn. The confirmation IS the plan-first approval surface — never substitute a generic build plan, and never create files on a "Yes" to one.

**The Case Review — eight sections, one question.** A decision-first business approval surface, complete enough to approve the case behavior without opening any SDD file — never a generic build plan and never a compressed SDD copy. Coverage: SDD §1 → sections 1/4/5; §2 → sections 2/3/4/5; §3 → sections 1/6; §4 → section 6. Each business decision appears ONCE. The review omits the data contract, variables, task inputs/outputs, a second stages list, and per-stage detail cards — that detail stays complete in the SDD. Anything carrying a high review item also appears in Review Flags.

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

The template's § Validation footer is the shape contract, and `uip maestro case sdd validate` (§Terminal step 3) is the gate. Skeleton head: `## Document History`, then the `## Planner Handoff` header + `<!-- planner-handoff:v1 -->` marker, then `## Table of Contents` — the universal planner scaffold (Rule 5); the case body follows. The CLI owns the render check for every checklist item except four draft-parity items, which only apply when finalizing a draft and which you check yourself on the written file, inline — no subagent and no read of `case-sdd-conformance-checklist.md`; each item is stated here in full:

| # | Check |
|---|---|
| 30 | The ordered stage and task inventory equals the draft's — names verbatim, only letter prefixes renumbered. |
| 31 | Every `=js:` expression in the draft appears verbatim in the final, inside the same owning block, except a character-level repair `sdd validate` required (listed to the user). |
| 32 | Every comparator + amount policy in the draft (`>`, `<`, `≥`, `≤`, or words for over / under / at least / more than / less than, next to an amount) is encoded in an executable cell (owner / recipient / WHEN / IF / Inputs) of the owning task or stage, on the same side of the threshold. |
| 33 | The draft file still exists beside the final, unrenamed. |

Answer each item PASS or FAIL in the transcript with one verbatim quote from the file, repair each FAIL with a targeted Edit, and re-answer only the failed items — max 3 rounds. No CLI command reads the draft, so these four are yours (measured: `checklist_coverage.json` reads them `needs-draft`); everything else, including data closure (items 17–19), is `sdd validate`'s. This is a render check, not a second design review; on failure, rewrite from the model and template — never a summary SDD, even if a later `caseplan.json` would validate.

**Fallback — only when the CLI has no `sdd` command.** If `uip maestro case sdd validate` answers with an unknown-command error (`unknown command 'sdd'`, `invalid_argument`), the installed CLI predates the gate. Say so in one line, then walk [case-sdd-conformance-checklist.md](case-sdd-conformance-checklist.md) against the written file in ONE subagent when the `Agent` tool is available — hand it the SDD path and that file, require the PASS/FAIL table with one verbatim quote per item and nothing else; the parent applies every repair Edit and owns the ready flip — or inline in the transcript when it is not. Items 1–29 and 34–35, plus 30–33 when finalizing a draft; repair each FAIL with a targeted Edit and re-answer only the failed items, max 3 rounds. Any other `sdd validate` failure is a real finding, never a reason to walk the checklist.

### Terminal step — write the SDD

Write the SDD to disk in batches, gate it, validate it, flip it, format it. The mode decides only the filename and whether the turn ends, and WHEN this step starts: on the accept answer for the interactive path, but at the start of the work for bounded no-build design and draft finalization, which settle the body section by section into a file already on disk (§Sketch, bounded no-build item 0). The `Status: ready` flip in step 4 is what the confirmation gates in every mode — never the seed.

1. **Seed Write, then Edit-append per section — three separate calls, never one.** Seed Write: title + `## Document History` + the Planner Handoff header stamped `Status: draft`, `Template validation: pending` (as ROWS of its table — never an HTML comment or a bold line) + `## Table of Contents`. A document that reaches disk in a single Write has skipped the gate by construction. Then Edit-append in template order — Section 1 → Section 2 one stage block at a time (every primary and secondary stage in source order) → Section 3 → Section 4 → `## Next Steps` — composing each section just before its append, not the whole document up front; no re-Read between sibling appends. The partial file on disk is the recovery point for a mid-turn failure or compaction (§Failure modes). Never `cp`/`mv`/`rsync` an artifact into place.
2. **When finalizing a draft, check the four draft-parity items** (30–33) in §Template conformance gate inline on the written file; in every other mode there is no checklist step. No other checklist walk unless the §Template conformance gate fallback applies. One structural Read is allowed here.
3. **Validate the written file with the CLI:** `uip maestro case sdd validate "<SDD_PATH>" --output json`. Exit 0 is the precondition for the ready flip. `Data.Issues[]` entries with `Severity: warning` neither block it nor call for a hand Edit: a warning describes a form the parser accepts (a row written without outer pipes, an indented table), and step 5 normalizes table form mechanically. On a non-zero exit, repair each error `Issue` (its `Code`, `Line` and `Message` name the defect) with a targeted Edit and run it again — max 3 rounds, then stop at `Status: draft` and present what remains. Never flip `ready` while this command fails. Every Edit this step makes is a change to a design the user has seen, so list each one in the final message in one business-language line (what changed, where, why the build needs it); never repair silently. If the response names `sdd` as an unknown command, the installed CLI predates the gate: run the §Template conformance gate fallback instead, and say so in one line.
4. **Ready flip is the LAST Edit:** `Status: ready`, `Template validation: passed` — `passed` means step 3's CLI validation passed (and, when finalizing a draft, step 2's four draft-parity items) (or, under the fallback, the full checklist walk). Drafts keep `Status: draft`. An interrupted run leaves a resumable `draft` on disk.
5. **Format the file with the CLI, on every handoff — the last write:** `uip maestro case sdd format "<SDD_PATH>" --output json`, after the flip. It rewrites the file in place: it normalizes tables (outer pipes, one separator row, cell padding) and never changes a heading, a prose line, a cell's content, or row or column order. This is the only step that changes table form — never normalize a table by hand. When `Data.Changed` is true, tell the user in one line that the tables were tidied and nothing else changed. If the response names `sdd format` as an unknown command, the installed CLI predates it: skip this step and say so in one line.
6. **Filename by mode** — a user-specified output path always wins:

| Mode | File | After the write |
|---|---|---|
<!--skill-flavor:build-handoff-row:start-->
| Build handoff (`uipath-maestro-case` asked for a build, no `sdd.md`) | `sdd.md` at the working root — NEVER overwrite an existing one; abort and surface it | Do NOT stop. The Build answer already carried consent: the build's phases start immediately in this conversation (`uip solution init` + its Phase 1, verifying the resolved identities instead of re-discovering them) |
<!--skill-flavor:build-handoff-row:end-->
| Normalization (`uipath-maestro-case` handed over a free-form `sdd.md` that `sdd parse` could not read) | `sdd.md`, after the original is written to `sdd.original.md` (§Normalize a free-form SDD) | Do NOT stop: hand back to the build in this conversation |
| Direct design (design/generate a case SDD, greenfield, no PDD) | `<CASE_NAME_KEBAB>-sdd.md` | STOP — the write is a turn boundary; `## Next Steps` points at Lane A or `uipath-maestro-case` for a later, opt-in turn |
| Draft request (user asked for a reviewable draft and to stop) | `sdd.draft.md`, or `<name>-sdd.draft.md` when the request names the file | STOP. Never promote a draft |
| Draft finalization (a `sdd.draft.md` exists, user asks to finalize) | the draft's basename minus `.draft` | STOP. §Resumption owns the procedure; the draft stays on disk beside the final |
| PDD-driven case (a PDD routed to Phase D, scope picked Case Management) | the standard Phase D output path ([sdd-generation-guide.md](../sdd-generation-guide.md)) | Standard Phase D flow — the case body still obeys the layers guide and the template |

Never write `sdd.md` AND `<case>-sdd.md` for the same design. Report the path in one line.

**Free-text corrections stay first-class after the terminal step:** a correction to a case SDD written earlier, or in another session, runs §SDD correction. Within this session, treat one as a targeted edit to the affected artifact (model + file + downstream), narrate it in one line, continue. Edit only the lines the correction names — never reformat untouched rows by hand, even ones `sdd validate` warns about — then run §Terminal steps 3 and 5 on the file.

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

Optional, **on-request only** — never offered proactively. Self-contained local HTML review of the case design (Case Definition, collapsible Stages & Tasks, Personas, Integrations; filters and search). Generation: Read [`assets/templates/case/sdd-viewer.html`](../../assets/templates/case/sdd-viewer.html), replace the `__SDD_DATA__` token inside the element with `id="sdd-data"` — the file carries a second copy of that token in an error string further down, which stays as it is — with JSON serialized from the in-memory model (schema in the template's header comment — do NOT re-parse the SDD when the model is live), Write `./sdd-viewer.html`, tell the user: `Generated ./sdd-viewer.html — open it in a browser to review.` Failure → one-line notice, continue. Downstream build phases ignore this file.

## Resumption

A case `sdd.draft.md` at lane entry is a leftover from an on-request draft or an older run. AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Use the draft — finalize and continue` | Read it as the design input, run Finalization, show the §Confirm summary built from it, proceed normally. |
| `Discard draft, start fresh` | Delete the draft. Return to §Entry. |
| `Abort` | Exit. No file changes. |

If the user explicitly asks to finalize the existing draft, choose `Use the draft — finalize and continue` by assumption and do not ask a redundant resumption question. If AskUserQuestion is unavailable, make the same assumption unless the user asked to discard or abort.

**Direct finalize fast path:** for a request that says the draft design is settled and asks for the final SDD only:

1. Read exactly these inputs, once each: the draft, this section + §Terminal step + §Template conformance gate, and the template (the finalization read budget at the top of this file: not the layers guide). Do not read planning references, inspect tenant resources, or spawn background tasks. The conformance-gate subagent (§Template conformance gate) is the one permitted spawn.
2. The draft is the design source: its stages, tasks, variables, conditions, SLAs, personas, and integration intent are settled. Normalize structure and repair mechanically required rule pairings only — a schema-required companion rule is not a redesign. Never add, drop, or rename a business element; preserve exact stage and task display names (including punctuation), task types, variables, conditions, connector placeholders, and domain rules.
3. `user-selected-stage` repair: retain the authored lane and give every eligible upstream primary stage a completing `required-tasks-completed` / `wait-for-user` / `Marks Stage Complete: Yes` exit; wording such as "any active case" means every primary stage. **This repair replaces that stage's existing `required-tasks-completed | exit-only | Yes` row; it never adds a second completion row or a `Marks Stage Complete: No` row.** `wait-for-user` is picker exposure, not automatic event/SLA/decision routing — add no such trigger.
4. Inventory the draft's ordered stage and task headings in memory and render one complete block per entry — **the shape contract is the template's § Validation footer** (draft-parity items 30–33 included), checked by `uip maestro case sdd validate`; it is not restated here. Never `cp`, `mv`, `install`, or `rsync` an artifact into place, and never delete or rename the draft — it stays beside the finalized document.
5. A task the draft left as a summary still gets its full detail block, per that same footer.
6. Every `=js:` expression in the draft appears verbatim in the output, inside the same owning task or stage block, with its field names, variable references, and output mapping intact — an equivalent-looking shorthand that drops an input, predicate, or intermediate field is a failure, not a simplification. The one exception is a repair §Terminal step 3 requires because the expression does not compile (for example curly quotes `“…”` used as string delimiters, restored to straight quotes): change only the characters the CLI names, keep every field, variable and predicate, and list the change to the user.
7. Threshold-policy conversion — MANDATORY scan, not optional polish. Scan the draft (descriptions, personas table, rationale) for comparator + amount phrases: `>`, `<`, `≥`, `≤`, `over`, `above`, `under`, `below`, `at least`, `more/less than` next to an amount (`$5M`, `100000`, `L4`). EVERY such policy must also appear in an executable cell of the owning task or stage in the final — prose-only is a render failure:
    - A personas row like `SomeRole | StageX (amount > $N only)` REQUIRES a matching guarded expression inside a StageX task block, phrased on the HIGH side and assigning the exception role: an owner/recipient cell or entry-condition IF cell containing `=js:vars.amount > N000000 ? "Role:SomeRole" : "Role:DefaultRole"` — the numeral written out (`5000000`, not `$5M`), the role and attribute on the same line. The expression lives in a table cell (Inputs/owner/recipient/WHEN/IF); an `=js:` fragment inside `**Design Rationale:**` or `**Description:**` prose is NOT an encoding and fails the gate.
    - Reuse an existing variable that carries the attribute; the conversion never adds or renames a task or variable.
    - Persona prose and Design Rationale alone are not final.
8. Secondary-stage task headings normalize to `##### Task S{secondaryStageIndex}.{taskIndex}: {Task Name}`; never keep draft letter prefixes (`R.1`, `W.1`, `CC.1`, `ESC.1`).
9. A draft's per-stage SLA table may carry `At-Risk Action` / `Breach Action` columns; the final SDD does not. Move each response into the § SLA Response Map row for that `(scope, SLA, status)` — never drop it, never keep the column.
10. Write, gate, validate, flip, format per §Terminal step — seed, append, validate, flip, format, never one Write. Finalizing a draft does not collapse them: a settled draft makes the sections faster to compose, not the skeleton optional (the draft on disk is also a recovery point, so a compaction means re-finalizing from it). The gate here is the full checklist, items 1–35: items 30–33 are the draft comparison — inventory parity, verbatim `=js:` preservation, executable threshold encoding, draft still on disk — answered with `sdd.draft.md` open beside the final. The `ready` flip is forbidden until every item reads PASS and §Terminal step 3's CLI validation exits 0; repair each FAIL with Edit and re-answer the failed items, max 3 rounds, then stop and present what remains. Quote the final tally (`35/35 PASS`) as evidence, then stop.

## Normalize a free-form SDD

The build skill hands over an existing `sdd.md` that has no planner receipt and that `uip maestro case sdd parse` cannot read whole — a pasted outline or a summary — and asks for a build. (An SDD that parses whole builds directly, receipt or not.) Treat it as a draft: the design it states is settled, the template shape is not.

1. Read exactly these, once each: the document, this section, §Resumption's direct finalize fast path, §Terminal step, and the template. Do not read the layers guide unless the document leaves a required field with no basis.
2. Preserve the original before anything else: Write its content, byte for byte, to `sdd.original.md` beside it. This is the one case in which the lane replaces an existing `sdd.md`, and only once `sdd.original.md` holds what was there.
3. Render the design into the template exactly as the direct finalize fast path does (its rules 2–9): keep every stage, task, trigger, variable and rule the document states, by its exact name; fill only what the template requires and the document leaves out, by the design Defaults, each one recorded as a decision.
4. Write `sdd.md` per §Terminal step — seed, append, gate, validate, flip, format. The build skill reads the result, so `Template validation: passed` must mean what it means for any other SDD.
5. Tell the user in one short block: the original is kept as `sdd.original.md`, the design was rewritten into the template, and each default filled in. Then hand back to the build in this conversation (Rule 16 build handoff) — no Case Review: the user already stated the design.

## SDD correction

An existing case SDD plus a request to change the design — "change the case SLA to 4 days", "rename this task" — not to build from it or derive tasks. The request is the change; it needs no Listen, Sketch or Case Review.

1. Read exactly these, once each: the SDD, this section, §Terminal step. Read the template only when the change adds a block whose shape you need. Do not read the layers guide, inspect tenant resources, or spawn subagents.
2. Make only the Edits the request names. Never hand-edit any other line — no rewording, renumbering or reformatting, including rows `sdd validate` warns about. Table form is normalized only by §Terminal step 5, which never touches prose.
3. Append one `## Document History` row naming the change.
4. Run §Terminal step 3 on the file. Exit 0 → keep `Status: ready` and `Template validation: passed`, then run §Terminal step 5 (format). An error on a line you changed → repair it and list the repair. An error on a line the request did not touch → do not repair it; set `Template validation: pending`, report the error with its line, and ask whether to fix it.
5. Tell the user each change in one business-language line, whether the tables were tidied, and whether the document still validates. Then stop: a correction never starts a build.

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
| `sdd.md` already exists at the working root (build handoff) | The handoff should not have happened — surface it; the build skill consumes that file trust-as-written (§Terminal step). The exception is a free-form `sdd.md` the build skill handed over for normalization: §Normalize a free-form SDD. |
| Context compaction mid-render | Re-render from the design source — the on-disk partial (split path), `sdd.draft.md`, or the model summary in the Case Review. Do NOT re-invoke skills, re-read applied references, search the filesystem, or spawn background tasks: the source plus the template are sufficient. |

## Anti-patterns

Every other rule in this file is stated where it is applied. These three have no other home:

- **Do NOT scaffold projects, spawn build subagents, or execute create-on-missing.** `Create during build` is a recorded decision the build skill executes; design never writes a project.
- **Do NOT ask the user to review or approve the SDD document.** The confirmation is the approval; the file is its artifact. An explicit sign-off request adds exactly one prompt — nothing else does.
- **Do NOT invent gates.** No size limit, no complexity stop, no approval-before-creating-files, no lightweight mode. The only stops are the one clarifying call (when earned), the confirmation, and the explicit-sign-off path.

