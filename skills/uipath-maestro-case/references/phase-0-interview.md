# Phase 0 — Interview Mode (sdd.md generation)

This file is a **thinking guide** for the agent: principles for how to listen, infer, ask, and resolve when no `sdd.md` is provided. Phase 0 produces an `sdd.md` that Phase 1 reads exactly as if a user wrote it.

> **Authoritative for the interview path only.** Trigger detection, mode behavior, threshold handling, hard stop, resumption, output contract. **Content rules** (authority hierarchy, task-type override priority, render-required fields, variable lineage, review items, source ledger) live in [sdd-generation-rules.md](sdd-generation-rules.md). Phase 1 logic lives in [planning.md](planning.md). Phases 2–6 live in [phased-execution.md](phased-execution.md).

## Goal

Produce a `sdd.md` shaped by [`assets/templates/sdd-template.md`](../assets/templates/sdd-template.md). After approval, Rule 2 applies: trust as written, no further gap-fill.

Phase 0 also writes:

- `tasks/registry-resolved.json` — one entry per task (search query, all matches, selected, rationale, resolved I/O contract).
- `sdd.draft.md` — intermediate; deleted atomically at approval.
- `sdd-viewer.html` — optional, written only if the user accepts the preview offer (§HTML preview).

## When Phase 0 runs

Strict binary trigger. Look for an `.md` file at the resolved path whose basename (case-insensitive) contains `sdd`. Examples that count: `sdd.md`, `loan-sdd.md`, `case_demo_sdd.md`, `./specs/onboarding-sdd.md`. Plain `.md` references without `sdd` in the name don't count.

| State | Action |
|---|---|
| File present, basename = `sdd.md` | Skip Phase 0. Hand to Phase 1. |
| File present, basename ≠ `sdd.md` | Copy contents to `./sdd.md` (preserve original at its path). Skip Phase 0. Hand to Phase 1. |
| File absent, `sdd.draft.md` present | Resume (§Resumption). |
| File absent, no draft | Run Phase 0 from scratch (§Entry). |

If the user prompt names no `.md` reference, default candidate is `./sdd.md`. Ask the user to confirm or supply a different path before assuming.

## Entry

When Phase 0 runs from scratch, AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Interview to generate sdd.md` | Begin interview (§Modes). |
| `I'll provide an sdd.md path` | Re-prompt for path. Re-check trigger. |
| `Abort` | Exit skill. No file changes. |

## Modes

Phase 0 moves through five modes of attention. Listen opens broad (one prompt + read everything shared); **Ask then runs a progressive walk through every SDD dimension** (§Ask → Progressive coverage walk) so coverage never depends on what Listen happened to catch. Listen / Sketch / Ask loop freely as new context lands. Resolve and Approve are gates.

### Listen

The opening move. One message, one prompt:

> Tell me about the case you want to build. What kicks it off, what stages does it move through, and how does it close out? Drop in any docs you have — paths, paste, or attach.

What the agent does as the user responds:

- **Reads everything mentioned.** If the user types a path, drags a file, or names a doc, read it immediately. Don't ask permission — the user shared it intentionally.
- **Reads in parallel** when the user names multiple docs (parallel Read tool calls in one message).
- **Globs work.** "Everything in `~/process-docs/`" → list with `ls`, read each with Read.
- **Narrates content, not filenames.** As each doc lands, post one short line about *what's in it*, not "Reading X…":
  > `vendor-onboarding.md — 4 stages (Intake → Compliance → Finance → Activation), 2 personas, 8-hour SLA on Compliance.`
- **Partial reads for huge docs.** Past ~2000 lines, read the first chunk, narrate the signal, decide if more is needed. Don't grind silently through 50 pages.
- **Unreadable formats** (`.docx`, `.pptx`, scanned image PDFs) → ask the user to paste the relevant section. PDFs up to 10 pages are read directly; larger PDFs need explicit page ranges.
- **Mid-flow docs are first-class.** If the user drops a new doc during Sketch or Ask, re-read, update inferences, narrate the delta:
  > `Got the SLA spec. The Compliance SLA is 8 hours, not the 4-hour default I was about to use.`
- **Verbal-only is fine.** A user who describes the process with no attachment is treated the same way — listen, narrate inferences.

Listen does not ask shaping questions — those belong in Ask's progressive walk (§Ask). The opening prompt is the *opener*, not the whole interview: capture what the user volunteers, then let the walk drive every dimension to depth. The single exception is technical: when a referenced doc is unreadable (see `.docx` / `.pptx` / scanned-PDF row above), request a paste so Listen can keep reading. Inferences are private to the sketch.

#### Domain-vocabulary capture (during Listen)

The user's first description is the corpus of verbatim domain terms. While listening, capture into the working sketch:

- **Roles** (exact casing): `CFO`, `Senior Underwriter`, `Triage Nurse`, `Onboarding Specialist`. Quote verbatim.
- **Domain nouns**: `Vendor` vs `Supplier` vs `Partner`; `Loan File` vs `Application`; `PO` vs `Purchase Request`. Pick the one the user used; never homogenize.
- **Stage labels**: `Triage`, `Underwriting`, `Adverse Action Notice`, `Funding`. Preserve casing and spelling.
- **Decision outcomes**: `Approve` / `Decline` / `Needs Info` (NOT `Approve` / `Reject` / `Pending` unless those were the user's words).
- **Integration shortnames**: if the user says `Workday`, never write `the HR system`.

Every captured term lands in the source ledger with provenance `verbatim:"<quoted exact phrase>"` (truncated at 40 chars in the ledger; full quote stays in working memory). The Sketch and Approve renderings MUST use the verbatim phrase. Synonym drift is a fidelity defect — see [sdd-generation-rules.md § Domain fidelity](sdd-generation-rules.md#domain-fidelity).

#### File / attachment / document detection (during Listen)

When the user mentions any of: `file`, `attachment`, `document`, `PDF`, `image`, `scan`, `upload`, `evidence`, `receipt`, `invoice` (as an artifact, not as a domain noun) — flag the conversation for a file-type Ask in §Ask, do not silently default. Three patterns to distinguish:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads a file at case start | "caller submits a PDF", "uploaded with the request", "comes in as an attachment" | `Category: In`, `Type: file` — see Use Case 9 in `sdd-template-examples.md`. Caller-obligation surfaces in Approve summary (§Approve summary). |
| Connector activity downloads / produces a file mid-case | "fetch the attachment from email", "download from Drive / S3", "pull the receipt from the vendor portal" | `Category: Variable`, `Type: file` populated by a task's Outputs `-> ` row — Use Case 10. |
| User stores a URL or metadata, not the bytes | "we just store the link", "we keep the document ID", "we reference the file in their system" | `Type: string` (URL) or `Type: jsonSchema` (metadata blob). NOT `file`. |

In Ask, present the three options when the indicator is detected. Default is forbidden — the wrong type breaks downstream binding (file → JobAttachment record, string → opaque URL, jsonSchema → arbitrary object).

### Sketch

The agent privately fills out the SDD shape against [`sdd-template.md`](../assets/templates/sdd-template.md). When picking a value for any field, follow the priority order in [sdd-generation-rules.md § Content authority hierarchy](sdd-generation-rules.md#content-authority-hierarchy) — platform schema and compliance constraints override user preference.

- Fields from Listen → recorded.
- Inferrable fields → recorded with a one-line narration AND a source-ledger entry per [sdd-generation-rules.md § Source ledger](sdd-generation-rules.md#source-ledger-provenance):
  > `Inferring case prefix: VNDR (source: mechanical:PascalCase→prefix).`
  > `Defaulting to single "Process Owner" persona (source: inferred-default:no roles mentioned).`
- Required fields still missing → marked as gaps to Ask.
- Optional fields still missing → marked `—` in the draft. No question.

**Required fields (block until answered):**

| Field | Source |
|---|---|
| Case Name (PascalCase) | Listen / Ask |
| Case Identifier prefix (2-4 char UPPER) | Listen / inferred / Ask |
| ≥1 Trigger (Manual / Timer / Connector Event) | Listen / Ask |
| ≥1 Stage with name | Listen |
| ≥1 Task per stage with name + type | Listen / Ask per stage |
| ≥1 Case exit condition | Listen / Ask |

Write `sdd.draft.md` as the sketch firms up. Update in place each time a gap closes — one Read → mutate → Write/Edit cycle per change (Rule 13).

### Ask

Ask is a **progressive walk** through the SDD dimensions, not a gap-only afterthought. Listen seeds the sketch; Ask then walks every core dimension in order (§Progressive coverage walk), confirming or extending each so the SDD reaches full depth on task detail, personas, and decisions — not just what Listen happened to surface. Two cadences carry the prompts: **single-question** (default — shape-changing gaps) and **batched** (independent low-impact follow-ups only, so a 14-task case doesn't burn 14 prompts).

#### Progressive coverage walk (interview backbone)

After Listen seeds the sketch, walk these dimensions **in order** — one prompt per dimension, each anchored to what the sketch already holds (`Here's what I have for <X> — confirm, change, or add`). This is the confirm-or-modify pattern, never a cold form. The walk guarantees coverage even when Listen was thin; it is what makes Phase 0 progressive rather than a single open question.

Skip a dimension's prompt only when Listen already captured it verbatim at high confidence AND it is not on the §Always-Ask list. Rows 2, 3, 7, 8 are never skipped — they define the case shape.

| # | Dimension | Prompt (anchored to the sketch) | Feeds |
|---|---|---|---|
| 1 | Process & objective | `This case handles <X> to achieve <Y> — right?` | §1.1 |
| 2 | Stage flow (E2E) | Show inferred stages in order; `Does this match start → finish?` Loop until confirmed — the only looping prompt. | §2 stages |
| 3 | Tasks per stage + type | Per stage: list inferred tasks + proposed type; `What work happens in <Stage>, and who or what does each step?` Pick each type via [sdd-generation-rules.md § Choosing the task type](sdd-generation-rules.md#choosing-the-task-type). | §2 task summary, task blocks |
| 4 | Personas / owners | Show inferred roles; `Who works these tasks, and which stages do they own?` | §3 personas, task Owner |
| 5 | Decisions / gates | `Where does someone approve / decline / escalate?` Each gate → an `action` task with buttons, or a routing exit. | task buttons, exits |
| 6 | Data per stage | `What information is collected or produced at each step?` | §1.5 variables |
| 7 | Trigger & exit | `What kicks this off, and what does 'done' look like?` Trigger type is Always-Ask the moment a portal / form / schedule / event is named. | §1.3, §1.4 |
| 8 | Exceptions / escalations | `What goes wrong, and how is it handled?` Each handler → a secondary (exception) stage — see [sdd-generation-rules.md § Mental model](sdd-generation-rules.md#mental-model-stages-secondary-stages-tasks). | exception stages |
| 9 | SLA / timing | Only when the user mentioned timing. `How long should <stage / case> take?` | §1.2, stage SLA |

Each row is a single-question prompt by default. Collapse only the safe-to-default rows (4 persona descriptions, 9 SLA when timing was never raised) into the one allowed §Batched prompt. Trigger type (7), task type on ambiguous verbs (3), and case exit (7) stay single-question — they are Always-Ask.

#### Buildability musts (capture during the walk)

Five things decide whether the SDD builds in one pass. Capture each *during* the walk above — they are where SDDs silently become unbuildable:

1. **Exception trigger source** (row 8) — per lane, ask *how it fires*: a gate decision → `selected-stage-completed`/`selected-stage-exited` (+ `IF` on the decision var); a person launches it → `user-selected-stage`; an external event → `wait-for-connector`. `Interrupting: Yes` for mid-stage lanes; terminal lanes end (`exit-only` + §1.4a case-exit), return lanes use `return-to-origin`. Keep each lane's entry **distinct** — identical entries fail `validate`. See [sdd-generation-rules.md § Logical integrity](sdd-generation-rules.md#logical-integrity--stage-graph).
2. **Decision outcome → route** (row 5) — per button, capture its outcome variable AND destination (advance / which exception / loop). No outcome may dead-end: a status string with nowhere to go is a broken branch.
3. **Task output capture** (row 6) — per configure/decide/capture task, name the §1.5 variable that stores its result. A form that collects values (rate, terms) but binds no output silently loses them.
4. **Required-input back-solve** (row 6) — per send/connector/agent, map every required input to a variable: an email needs a recipient *address* var (not a name); an agent needs its source data.
5. **Conditional gates** (rows 4–5) — ask if any role or step is conditional on a value (loan size, risk, region). Model a guarded rule + persona, never a prose footnote (e.g. `>$5M → Credit Analyst review`).

#### Single-question (default for shape-changing gaps)

**One question at a time**, ranked by information value. Use plain AskUserQuestion. Update `sdd.draft.md` after each answer. Apply to:

- Trigger type (when external system / portal / form / schedule / signup / event is mentioned)
- Task type on ambiguous verbs or compliance-override conflicts
- Case exit condition
- Stage exit `Marks Stage Complete: Yes` ↔ WHEN pairing
- SLA value when user mentioned timing
- Variable Type when file / attachment / document is in scope (see §Listen file detection)

These fields change the generated case shape; bundling them obscures the decision and survives the Approve scan.

#### Batched (low-impact follow-ups only)

One AskUserQuestion with up to 4 `multiSelect: true` rows for fields whose value can be defaulted safely AND whose default does NOT change case shape:

| Field | Default if not picked |
|---|---|
| Case-level description (Section 1.1) | `—` (Phase 1 leaves blank) |
| Persona descriptions (Section 3) | `—` |
| Exception-stage descriptions | `—` |
| Optional `conditionExpression` cells in Entry / Exit rows | `—` (no IF filter) |
| Optional `Business Calendar` cell on timers | `—` (use 24×7) |
| Optional task SLA on `action` tasks | `—` (inherits case SLA) |
| App-view detail (Section 3) | "Case list" + "Case detail" baseline view names |

Use sparingly — at most one batched prompt in the whole interview. Each row defaulted records `inferred-default:<reason>` in the source ledger.

#### When to Ask vs Default

**Default to Ask when in doubt.** Ask is cheap (~30s). A wrong default is expensive: the user scans the Approve summary fast, the default may survive, Rule 2 locks the file, and a Phase 1 re-run is forced.

**Default with narration** ONLY when ALL three high-confidence criteria hold for the field:

1. **Verbatim or one-step mechanical.** The value is either (a) written verbatim by the user, (b) lifted from a doc the user shared and currently in your context, or (c) a one-step mechanical derivation. Allowed derivations: `PascalCase → 2–4 letter prefix`; `no roles mentioned → persona=Process Owner`; user said `"I kick it off"` / `"we run it manually"` / `"ad-hoc"` → `trigger=Manual`.
2. **No interpretation step.** If you have to choose between two plausible meanings, it's interpretation — Ask.
3. **Field is not on the Always-Ask list below.**

**Always-Ask** (never default — these change case shape, wrong defaults force Phase 1 rework):

| Field | Why never default |
|---|---|
| Trigger type when ANY external system, portal, form, schedule, signup, or inbound event is mentioned | `Timer` / `Connector Event` change generation path. "Vendor signs up" → portal/event, NOT Manual. |
| Task type on ambiguous verbs (`review`, `approve`, `check`, `validate`, `process`, `assess`, `sign off`, `decide`) | `action` (HITL) vs `agent` (LLM) generate different shapes. The verb alone is not enough. |
| Task type when a **compliance trigger phrase** is in the transcript (ECOA, NCQA, HIPAA, SOC 2, FCRA, FINRA, "licensed X", "fiduciary review", etc.) AND user proposed non-`action` | Tier 2 of the authority hierarchy forces `action`; do not silently accept user's stated type. See [sdd-generation-rules.md § Task-type override priority](sdd-generation-rules.md#task-type-override-priority). |
| Case exit condition | Wrong exit traps the case open or closes prematurely. |
| Stage exit `Marks Stage Complete` ↔ WHEN pairing | Mismatched pairing fails Phase 4 validate per [sdd-template.md](../assets/templates/sdd-template.md) Key Rule 4. |
| SLA value (if user mentioned timing at all) | Mishearing "about a day" as 3 days creates an SLA breach on every run. |

**Mark `—`** for optional fields the user didn't touch. No question.

> **Never silent.** Every defaulted value gets (a) a one-line narration when recorded in Sketch *and* (b) an entry in the Approve summary's `Inferred / defaulted` block. "Default with narration" is not "default silently."

#### Red flags — STOP and Ask

These thoughts mean STOP and use AskUserQuestion before continuing:

| Thought | Reality |
|---|---|
| "I'm confident enough about the trigger." | Trigger ≠ Manual the moment a portal, form, schedule, or external system is mentioned. Always-Ask. |
| "The user said 'review' — probably an `action` task." | `review` is on the Always-Ask list. Ask. |
| "User said 'I'll fix it later' — defaulting is sanctioned." | User-permission to default ≠ permission to skip Ask. Rule 2 locks the file post-Approve. Wrong defaults survive. |
| "User is in a hurry, don't burn turns." | One Ask costs 30s. One wrong default costs a Phase 4 retry loop. Ask. |
| "Edit at Approve is a first-class escape hatch — defaults are cheap to fix." | Only if the user notices. Plan for the case where they don't. Ask now. |
| "Five of six required fields are confident; only one is shaky." | Skip Ask requires ALL fields confident. One shaky field = Ask. |
| "The file lists this exact default as an example, so I'm allowed." | The example only applies when ALL three high-confidence criteria above are met. Re-check before defaulting. |

#### Stuck detector

If 3 stuck replies accumulate within a single Ask, trigger §Soft redirect. Counter is per-field; a new Ask resets it. An **answered** reply resets the counter to 0, even if prior replies tripped it — a late genuine answer cancels the strike (do not trigger Soft redirect if reply N is `answered`, regardless of N−1, N−2, N−3 classifications).

Classification of each reply:

| Class | Definition | Counts toward stuck? |
|---|---|---|
| **answered** | Reply proposes ONE concrete value for the field asked, AS the answer. A value named in passing inside a different question (e.g., capability / integration / scope question) is NOT `answered` — the user must offer it as their decision. | No — resets counter to 0 |
| **unanswerable** | User explicitly says they don't know, can't decide, or "you pick" / "whichever" / "you decide". (Punting the choice to the agent → `unanswerable`, not `answered`.) | Yes |
| **contradictory** | Reply offers two or more candidate values without resolution. Trigger phrases: "either A or B", "either of those", "either one", "A or maybe B", "A — actually no, B". A user who lists candidates and does not pick is `contradictory`. | Yes |
| **off-topic** | Reply does not address the field asked. Includes: history, context, questions back at the agent, integration / scope / capability questions, unrelated tangents. "Related to the case" is NOT enough — must address the specific field as the user's chosen answer. A capability question that *incidentally mentions* the asked field's domain (e.g., "do you support X when the case closes?") is still off-topic — the mention is context, not a proposal. | Yes |

**Worked examples** (Ask: "How should this case close out?"):

| User reply | Class | Why |
|---|---|---|
| "When funding is disbursed." | `answered` | One concrete value, proposed as the answer. |
| "I guess when funding is disbursed — or after LOS confirms. Either of those." | `contradictory` | Two values, "either of those" = explicit non-choice. |
| "You pick whichever is standard." | `unanswerable` | Explicit punt. |
| "Do you support webhook callbacks to our LOS when origination closes?" | `off-topic` | Capability question; the closing event is mentioned as context, not proposed as the answer. |
| "Historically we had files stay open for weeks. The 2023 audit was rough." | `off-topic` | History, no value proposed. |

#### Threshold check

After Sketch + Ask close out, count from `sdd.draft.md`:

- Stages, Tasks total, Distinct integrations, Distinct personas, `case-management` tasks (child cases).
- Exception stages — counted but never triggers redirect.

Breach any quantitative cap → §Soft redirect.

### Resolve

For each task in `sdd.draft.md`, find the matching registry resource. Search the cache file under `~/.uip/case-resources/` by name keywords. Filename varies by component type — common cases:

- `process-index.json`, `agent-index.json`, `api-index.json`, `processOrchestration-index.json`, `caseManagement-index.json` — `<type>-index.json` shape
- `action-apps-index.json` — kebab + plural for HITL action apps
- `typecache-activities-index.json` — for `execute-connector-activity` (`CONNECTOR_ACTIVITY`)
- `typecache-triggers-index.json` — for `wait-for-connector` (`CONNECTOR_TRIGGER`)

Run `uip maestro case registry pull` first if cache absent. See [registry-discovery.md § Cache File Index](registry-discovery.md#cache-file-index) for the authoritative file list, identifier fields, and cross-type fallback rules.

**Resource reality — resolve EVERY runnable across all registry types, and confirm a LIVE instance, not just a type match.** Resolving the real identity here is what lets Phase 1–3 build in one pass; defer it and the build halts on first use.

| Task type | Resolve to | Buildable only when a live instance exists |
|---|---|---|
| `execute-connector-activity` | connector `typeId` + operation (`typecache-activities-index.json`) | a registered IS **connection** (`connectionId`) for that connector |
| `wait-for-connector` | connector-trigger `typeId` (`typecache-triggers-index.json`) | an IS connection for the inbound event |
| `agent` | `agentId` (`agent-index.json`) | the agent is **deployed** |
| `action` (human task / HITL) | `actionAppId` (`action-apps-index.json`) when a deployed Action App matches | else fall back to a v2 JSON-schema form — no app needed |
| `process` / `rpa` | `processOrchestrationId` (`process-index.json` / `processOrchestration-index.json`) | the process is **published** |
| `api-workflow` | `apiWorkflowId` (`api-index.json`) | the API workflow is **deployed** |
| `case-management` | child case (`caseManagement-index.json`) | the child case is **published** |

A *type* match with **no live instance** still ships `<UNRESOLVED>` + a `high` review item — never fabricate IDs (SKILL.md Rule 8). (A connector type can exist in the catalog while the tenant has zero connections — that is still `<UNRESOLVED>`.)

**Narrate the search before presenting matches.** Don't drop the AskUserQuestion cold:

> `Searching registry for "InvoiceValidation"… 2 matches.`

#### Resolve cadence — auto-confirm gate (one upfront prompt, then auto-pick single-match)

Before per-task prompts, run all task searches in parallel, then bucket results:

| Bucket | Definition |
|---|---|
| **A — single high-confidence** | Exactly 1 match, AND the match's name shares ≥ 1 token (case-insensitive, ≥ 3 chars) with the task's `Task Name` |
| **B — ambiguous** | Multiple matches, OR single match with no token overlap |
| **C — empty** | 0 matches across cache files |

Present a single upfront AskUserQuestion **only when bucket A is non-empty**:

| Option | Effect |
|---|---|
| `Auto-confirm <N> single-match high-confidence resolutions; ask me about the rest` | Record bucket A picks silently; proceed to per-task prompts only for bucket B + C |
| `Ask me about every task` | Skip auto-confirm; present per-task prompt for every task |

For each bucket A auto-confirm, record `tenant-registry:<resource-name>` provenance in `tasks/registry-resolved.json` with an additional `auto_confirmed: true` flag. The Approve summary's `Inferred / defaulted` block surfaces the count: `Auto-confirmed: N registry matches (single-match high-confidence).` The user re-validates at Approve.

#### Per-task prompts (bucket B + bucket C remainder)

Per-task AskUserQuestion (4 options max):

| Option | Effect |
|---|---|
| `<top match — name + version + type>` | Record selection. |
| `<second match>` (if available) | Record selection. |
| `Placeholder — resolve later` | Keep `<UNRESOLVED>` on `taskTypeId` / `typeId` / `connectionId`. Phase 1 emits placeholder task per Rule 8. |
| `Something else` | Free-text re-search keyword, retry. |

**Empty registry match** across bucket C → AskUserQuestion `Force pull and re-resolve` / `Skip and use placeholders` (Rule 17), applied per batch, not per task. When the user picks `Skip and use placeholders`, every unresolved task emits a high-severity review item per [sdd-generation-rules.md § Review items](sdd-generation-rules.md#review-items).

#### Schema discovery — pull each resolved task's I/O contract

Identity is not the whole contract. The SDD's task Inputs / Outputs `Field` cells MUST match the resource's real argument / field names verbatim (see [sdd-generation-rules.md § Task content rules](sdd-generation-rules.md#task-content-rules)), and a connector's *required* inputs stay invisible until its schema is read. For every task resolved to a **live instance** (skip `<UNRESOLVED>` — no identity, no schema), pull its contract and use it to fill the `Field` cells from the real names and to back-solve required inputs against the *actual* list, not the user's recollection.

Run in parallel after the picks land — `--output json`, connectors via `spec`, runnables via `tasks describe`:

| Resolved task type | Discovery command | Yields |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` / `action` / `case-management` | `uip maestro case tasks describe --type <type> --id <resolved-id> --output json` | In / Out argument names + types |
| `execute-connector-activity` | `uip maestro case spec --type activity --activity-type-id <typeId> --connection-id <connId> --skip-case-shape --output json` | required body / query / path fields, output fields, filterable fields |
| `wait-for-connector` + connector **event trigger** | `uip maestro case spec --type trigger --activity-type-id <typeId> --connection-id <connId> --skip-case-shape --output json` | required event params, output payload fields |
| `wait-for-timer` | — | no contract — skip |

For each task with required inputs the sketch has not mapped, one AskUserQuestion in business terms — name the inputs, never the schema mechanics (§Forbidden vocabulary):

> `Send Slack message needs a channel and a message body — what feeds each?`

Map each answer to a variable, a literal, or an upstream task's output (§Ask → Buildability musts). For an event trigger, surface required event params the same way (e.g., which mailbox folder) and fill each payload-extraction Variable's `sourceFields` path from the discovered output shape. A filter clause the connector can't support → narrate and Ask for a substitute.

**Cost.** One CLI call per resolved task, run in parallel and resolved-only. The trade is a longer Resolve for far fewer Phase 3 / 4 binding failures — wrong `Field` names and unmapped required inputs that otherwise surface only after Rule 2 locks the file.

After all picks and schema discovery, write `tasks/registry-resolved.json` (Rule 9 shape — including each resolved task's fetched I/O contract). Update `sdd.draft.md` with concrete resource names and the real Inputs / Outputs `Field` names. Any unresolved task carries a paired `review_items[]` entry in the same JSON.

> **Phase 1 handoff.** Phase 1 reads `tasks/registry-resolved.json` and skips re-search for resolved entries. It still extends the file with any resolutions Phase 0 deferred. No artifact replay; sdd.md is the contract.

### Approve

Before renaming, run the **Finalization checks** in [sdd-generation-rules.md § Finalization](sdd-generation-rules.md#finalization) — the full 14-step list including stage-graph connectivity (step 12), domain-fidelity scan (step 13), and architect's-lens advisory pass (step 14). Any blocking failure (steps 1–10, 12, 13) routes back to `Re-edit` / `Restart` / `Abort`. Advisory passes (step 14) emit `medium` review items but do not block.

On pass:

1. Atomic rename `sdd.draft.md` → `sdd.md`.
2. Print concise summary (not the full document):

```
Phase 0 complete.

Path:    ./sdd.md
Stages:  N
Tasks:   N
  - process: N
  - agent: N
  - ...
Integrations: N
Personas:     N
Child cases:  N
Threshold status: WITHIN | EXCEEDED (<which>)
Review items:    high=N  medium=N  low=N
Auto-confirmed:  N registry matches (single-match high-confidence)

Inferred / defaulted (please confirm — these were NOT stated verbatim):
  - <field>: <value>  (<source>)
  - <field>: <value>  (<source>)
  ...

Caller obligation (file In-arg detected — omit block when no file In-arg present):
  File In-args:  evidenceDoc, signedAgreement
  Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
  PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
  In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
  Maestro Studio Web's "Start case" dialog does this automatically.

Architect advisories (medium review items — non-blocking):
  - <id>: <one-line>  (target: <stage/task>)
  ...
```

The **`Inferred / defaulted` block is mandatory** whenever Sketch defaulted ANY field. List every defaulted value with source attribution. Omit the block only if zero fields were defaulted. This is the user's last chance to catch wrong defaults before Rule 2 locks the file — never collapse to counts alone when defaults exist.

The **`Caller obligation` block** is mandatory when any §1.5 row has `Category: In` + `Type: file`. Omit otherwise. The text is fixed; do not paraphrase.

The **`Architect advisories` block** lists each `medium` review item emitted by the architect's-lens pass ([sdd-generation-rules.md § Architect's lens](sdd-generation-rules.md#architects-lens)). Omit when count is 0. These do not block Approve but should be visible.

Source-attribution examples: `(PascalCase derivation)`, `(no roles mentioned → Process Owner)`, `(no SLA stated → 3-day default)`, `(verb "review" — defaulted to action)`, `(user said "ad-hoc" → trigger=Manual)`.

3. AskUserQuestion (4 options — base set; if any `high` review items exist, replace `Approve and proceed to Phase 1` with `Approve despite N high-severity items` populated with the count):

| Option | Next |
|---|---|
| `Approve and proceed to Phase 1` | Exit Phase 0. Begin [planning.md](planning.md) Step 1. |
| `Generate HTML preview` | Write `./sdd-viewer.html` (§HTML preview). Re-show this prompt. |
| `Edit and re-validate` | Free-text correction → update affected section of `sdd.md` → re-run Finalization checks → re-show summary. |
| `Restart or abort` | Follow-up AskUserQuestion (`Restart interview` / `Abort`). Restart wipes `sdd.md`, `sdd.draft.md`, `tasks/registry-resolved.json` and returns to §Entry. Abort exits skill, leaves artifacts in place. |

**Free-text corrections are first-class refines.** A message like "actually the SLA on Compliance is 8 hours not 4" is treated as an edit — update the section in `sdd.md`, narrate the change, return to Approve. The user does not need to pick the `Edit` option to make corrections.

#### Edit validation

Structural checks before re-approve:

- All required fields present (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit).
- Every stage has ≥1 task entry.
- Every task has `Type:` from the closed 9-value enum (Rule 16): `process` | `agent` | `rpa` | `action` | `api-workflow` | `case-management` | `execute-connector-activity` | `wait-for-connector` | `wait-for-timer`. Reject `external-agent`, `connector-activity`, `connector-trigger`, or any other value.
- Every task has at minimum a `Description:` line.
- **Exit Condition WHEN ↔ Marks Complete pairing** ([sdd-template.md](../assets/templates/sdd-template.md) Key Rule 4 — applies to both stage exit and case exit):
  - **Stage exit:** `Marks Stage Complete: Yes` → must use `required-tasks-completed` / `required-stages-completed`; `No` → may use `selected-tasks-completed(...)`. Flag any `Yes + selected-tasks-completed` pair as error.
  - **Case exit:** `Marks Case Complete: Yes` → must use `required-stages-completed` / `wait-for-connector`; `No` → may use `selected-stage-completed(...)` / `selected-stage-exited(...)` / `wait-for-connector`. Flag any `Yes + selected-stage-*` pair as error.

Validation fail → list specific issues, AskUserQuestion `Re-edit` / `Restart` / `Abort`.

Threshold breach on edit → §Soft redirect (user can override or switch).

## HTML preview

Optional. Offered at Approve. The viewer is a self-contained HTML file the user opens locally — no server, no internet.

### What it shows

Reads the same case structure used to render `sdd.md` and renders four sections matching `sdd-template.md`:

1. **Case Definition** — name, prefix, SLA, triggers, exit conditions, variables.
2. **Stages & Tasks** — each stage as a collapsible card; tasks listed inside with type badges; click for full detail panel.
3. **Personas & App Views** — personas with stage scope + permissions; process app views.
4. **Integrations** — connectors with operations; external agents.

### Interactive elements

- Sticky sidebar TOC; click to jump; active section highlights on scroll.
- Stage cards expand/collapse; "Collapse all" toggle for skim review.
- Click any task → side panel with full detail (entry condition, I/O bindings, action buttons, connector config, timer value, child-case data flow — whatever fits the type).
- Filter task lists by persona (multi-select pills) and by task type.
- "Unresolved only" toggle — hides everything without `<UNRESOLVED>` markers.
- "Schema view" toggle — surfaces schema field names alongside human labels (e.g., `Marks Stage Complete (markStageComplete)`).
- Free-text search across stage / task / variable names.
- Print / save-as-PDF button (uses a print stylesheet that hides controls and forces all stages expanded).

### Generation

Read [`assets/templates/sdd-viewer.html`](../assets/templates/sdd-viewer.html). It contains a `<script id="sdd-data" type="application/json">__SDD_DATA__</script>` block. Replace the `__SDD_DATA__` token with a JSON object matching the schema documented inline in the template's header comment. The agent has this structured data in working memory from Sketch — serialize it directly. Do NOT re-parse `sdd.md`.

Write the populated file to `./sdd-viewer.html` (Read + Write only, Rule 13). Tell the user:

> `Generated ./sdd-viewer.html — open it in a browser to review.`

Re-show the Approve prompt. The viewer is a review aid, not a checkpoint — it does not replace the Approve gate.

If the user edits `sdd.md` after a preview is generated, the existing `sdd-viewer.html` is stale. Either regenerate it (re-pick `Generate HTML preview` at Approve) or leave it — Phase 1 ignores the file either way.

## Thresholds

Hard quantitative caps. Breach triggers §Soft redirect (not hard refuse).

| Threshold | Cap |
|---|---|
| Stages | > 7 |
| Tasks total | > 14 |
| Distinct integrations | > 3 |
| Distinct personas | > 3 |
| Child cases (`case-management` tasks) | ≥ 1 |

**Exception stages are NOT a threshold.** They may appear freely.

## Soft redirect

AskUserQuestion (2 options):

| Option | Effect |
|---|---|
| `Continue with warning header` | Proceed. Set warning header in generated `sdd.md` (§Warning header). |
| `Abort` | Exit. No file changes beyond what already exists. Preserve `sdd.draft.md` so the user can resume after manually trimming scope. |

### Warning header

When user overrode, prepend immediately under the H1 in `sdd.md`:

```markdown
> **⚠️ Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: <stages> stages, <tasks> tasks, <integrations> integrations,
> <personas> personas, <child-cases> child cases.
> Review carefully before approving. Consider splitting into smaller cases or trimming scope.
```

Phase 1 ignores it (blockquote, not a structural field). The HTML viewer surfaces it as a banner.

## Resumption

When `sdd.draft.md` is present at trigger time, AskUserQuestion (4 options):

| Option | Effect |
|---|---|
| `Resume from where I left off` | Re-read `sdd.draft.md`. Infer position (all required fields present = Sketch + Ask done; `tasks/registry-resolved.json` present = Resolve done). Continue from the next mode. |
| `Discard draft, restart` | Delete `sdd.draft.md` + `tasks/registry-resolved.json`. Return to §Entry. |
| `Use draft as-is, finalize` | Run Approve gate on the draft as-is. Edit validation may flag missing required fields. |
| `Abort` | Exit. No file changes. |

Listen output is never persisted. Resumption picks up from Sketch onward.

## Forbidden vocabulary (user-visible output)

The user sees a conversation that produces a document. They don't see the machinery. Never surface in chat or in `sdd.md`:

- `sdd.draft.md`, `tasks/registry-resolved.json`, internal filenames. (**Exception:** `sdd-viewer.html` is intentionally user-visible — the user opens it in a browser, so the filename must be named at generation time. Do not surface it anywhere else.)
- `<UNRESOLVED>` markers in narration (they may appear in the file; never in chat lines).
- `Listen`, `Sketch`, `Ask`, `Resolve`, `Approve`, `Round 1`, `Round 2`, `Round 3`, `Round 4` — these are agent-facing mode names, not user-facing.
- `the validator`, `the schema check`, `structural validation`, `edit-loop validation`.
- `the cache`, `the registry index`, `~/.uip/`, `~/.uipath/`.
- `interview answers`, `from cache`, `from the registry`, `from state.*`, `REVIEW:`, `wiki/`, `PDD`, `pdd.md`, or any chain-of-thought explanation of how a value was derived (echoes [`sdd-template.md`](../assets/templates/sdd-template.md) Output Rules).

If the user asks how something works, explain in their language (cases, stages, tasks, triggers, SLAs, personas, connectors, exceptions) — never file names or internal mechanisms.

## Failure modes

| Symptom | Action |
|---|---|
| User says "skip" / "I don't know" on optional field | Write `—` in the draft. |
| User says "skip" on required field | Write `<UNRESOLVED: <agent's question>>` in the draft. Phase 1 + post-build loop will revisit. |
| 3 stuck replies in single Ask (per-field counter, reset on `answered` — see §Ask Stuck detector for classification) | Trigger §Soft redirect. |
| Registry pull fails (CLI error, no auth) | Skip Resolve. All tasks marked `<UNRESOLVED>`. Phase 1 emits placeholders. Inform user. |
| User edits `sdd.md` to add stages exceeding threshold | Edit validation fires §Soft redirect. |
| `sdd.md` already exists at path when interview begins | Should not happen — trigger detection exits Phase 0 first. If race, abort with error. Never overwrite. |
| HTML preview generation fails (template missing, write error) | Inform user, fall back to text summary only. Approve gate is unaffected. |

## Output contract — what Phase 1 sees

After Approve:

- `sdd.md` — always present. May include warning header, `<UNRESOLVED>` markers, or `—` placeholders.
- `tasks/registry-resolved.json` — **present only if Resolve ran successfully.** Absent when Resolve was skipped (registry pull failed, no auth, or the cache was unreachable — see Failure modes). Phase 1 ([planning.md § Step 3](planning.md)) handles both cases: if the file exists, it reads carry-over picks and skips re-search for resolved entries; if absent, it runs full discovery from scratch. Either way, format matches Phase 1's artifact shape (Rule 9) when written.
- `sdd-viewer.html` — present only if user generated the preview. Phase 1 ignores it.
- `sdd.draft.md` — deleted (atomic rename at Approve).

Phase 1 ([planning.md](planning.md) Step 2) reads `sdd.md` exactly as a user-provided file. Rule 2 applies from this point: trust as written, no further gap-fill.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Strict binary trigger; presence = trust-as-written.
- **Do NOT suggest or invoke any other skill on threshold breach or stuck detection.** Phase 0 stays self-contained — surface the warning header, give the user `Continue` / `Abort`, never push a redirect.
- **Do NOT persist Listen output as a transcript.** Inferences live in the draft (the sketch), not in a separate file.
- **Do NOT use `sed`/`awk`/`python`/`node` to mutate `sdd.draft.md`, `sdd.md`, `tasks/registry-resolved.json`, or `sdd-viewer.html`.** Read + Write/Edit only (Rule 13).
- **Do NOT bundle questions in Ask.** One per message. Bundles re-introduce the form-feel Phase 0 is reframed to avoid.
- **Do NOT silently auto-pick a registry match in Resolve.** AskUserQuestion every task; never infer (Rule 2 spirit).
- **Do NOT proceed past the threshold check when counts already exceed thresholds.** Force soft-redirect prompt before continuing.
- **Do NOT skip the warning header when user overrode threshold.** Future agents reading the file must see the override flag.
- **Do NOT treat the HTML preview as a checkpoint.** It's a review aid. Approve is the only gate.
- **Do NOT narrate filenames or schema mechanics in user-visible output.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
