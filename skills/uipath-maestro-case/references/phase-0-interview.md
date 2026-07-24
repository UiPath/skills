# Phase 0 — Interview Mode (case design)

This file is a **thinking guide** for the agent: how to listen, assume, confirm once, and hand off fast when no `sdd.md` is provided. Phase 0 designs the case in the session's **in-memory model**; `sdd.md` is rendered from that model in parallel with the first build actions — a reference artifact, never a review gate.

> **Authoritative for the interview path only.** Trigger detection, mode behavior, confirmation, resumption, output contract. **Content rules** (authority hierarchy, task-type override priority, render-required fields, variable lineage, review items, source ledger) live in [sdd-generation-rules.md](sdd-generation-rules.md). Phase 1 logic lives in [planning.md](planning.md). Phases 2–6 live in [phased-execution.md](phased-execution.md).

## Goal

Design the case as an in-memory model shaped by [`assets/templates/sdd-template.md`](../assets/templates/sdd-template.md), confirm it in ONE user prompt, then start the build. Phase 0 is **best-assumption by default**: it decides everything it can from the user's words and documents, and *informs* the user of every decision — it does not interrogate. `sdd.md` renders from the confirmed model concurrently with the first build actions. For later sessions and re-runs the file is the contract (Rule 2: trust as written); within this session, the in-memory model that produced it drives the build.

Phase 0 writes:

- `sdd.md` — rendered once from the confirmed model, batched with the first build actions (or written and reported when the request was design-only).
- `case-board.html` + `case-board-data.js` — the dual-render visual board (§Case board): app byte-copied from `assets/templates/case-board.html`, data write-only. Phase 1 ignores both.
- `sdd-viewer.html` — optional, generated only on explicit request (§HTML preview).
- `sdd.draft.md` — ONLY when the user explicitly asks for a draft to review; normal runs never create it. `tasks/registry-resolved.json` is a Phase 1 artifact — Phase 0 does not write it.

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

**If the user's request already describes the case** (any stages, work, trigger, domain, or attached docs), skip every entry prompt: print the roadmap from `SKILL.md § User-facing roadmap` and go straight to work — the request IS the first Listen input. **Only a bare request** ("create a case" with nothing else) gets the Listen opener after the roadmap. There is no entry menu; a user who has an `sdd.md` will say so, and abort is always a free-text away.

**No tenant work at Entry.** Nothing about the tenant is a prerequisite for designing the case — do not run login or `registry pull` up front. Grounding starts only when the case shows it needs it (§Tenant grounding).

## Tenant grounding — requirement-driven, one light pass, no questions

Phase 0 grounds resources lazily, in parallel with the design, with a **single name-match pass** at most. Schema discovery (`tasks describe`, `case spec`) belongs to the build phases — never run it in Phase 0.

1. **Intake batch.** Read every supplied document in parallel. Extract named systems, resources, likely tasks, and roles.
2. **Requirement-driven kickoff.** The FIRST moment the sketch identifies tenant-bound work — a named system/resource/connector, or an inferred runnable/connector/action task — start the grounding chain as ONE background command, in the same batch as whatever is already running: `uip login status --output json && uip maestro case registry pull`. It resolves while sketching continues; a case with no tenant-bound items never pulls in Phase 0. Best-effort: never block on it, never surface its output unprompted; on failure, one plain-language line (§What to say while working), keep intended names, mark identities `resolve at build`, continue. If the harness cannot run background commands, run login → pull in the batch that composes the confirmation.
3. **Light match pass — join, never wait.** When composing the confirmation, check the chain. If the pull succeeded, run ONE cache lookup per named or inferred resource (`~/.uip/case-resources/<type>-index.json`; `action-apps-index.json` for HITL apps; `typecache-activities-index.json` / `typecache-triggers-index.json` for connectors) — all lookups in one parallel batch. With ≥ 4 lookups, fan them out to parallel read-only subagents (one per item or type family; cache Reads only — never writes, never prompts, never login/pull; parent spot-verifies adopted identities). Bucket each result:
   - **Single confident match** (1 match across all folders, ≥ 1 shared name token) → adopt silently; shows as the task's resource in the confirmation with a decision line.
   - **Anything else** (multiple matches, cross-folder same-name, no token overlap, zero matches, 0 or > 1 enabled connections for a connector) → mark `resolve at build`. Do NOT ask, do NOT auto-pick among candidates, do NOT fetch schemas. Phase 1's discovery and its Rule 17 gate handle the choice with full authority.

   If the pull has NOT finished when the confirmation is ready, do not wait: present with `resolve at build` on the tenant-bound items and let the build reconcile — the confirmation is never delayed by the tenant.

**Guardrails:** registry data is evidence, not requirements — never add/rename business work to match tenant inventory; never dump catalogs; keep type-specific portable names concrete (`Resolved Resource`, Action App title, `Child Case`) even when identity defers; a connector with zero connections is `resolve at build`, not a reason to change the task type.

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

Fill the complete SDD shape against [`sdd-template.md`](../assets/templates/sdd-template.md) from what Listen captured, deciding every open field by best assumption. Authority order per [sdd-generation-rules.md § Content authority hierarchy](sdd-generation-rules.md#content-authority-hierarchy) — platform schema and compliance constraints override user phrasing (apply the override silently; it becomes a decision line). Every non-verbatim value gets a source-ledger entry AND a line in the confirmation's `Decisions` block. The model lives in memory — **no draft file, no checkpoint writes**; the only Phase 0 writes are the board files (§Case board) and, later, `sdd.md`.

**Assumption playbook** (former ask-list, now decided and disclosed):

| Field | Best assumption |
|---|---|
| Trigger type | External system / portal / form / inbound event / record-created mentioned → **Connector Event** with that source (unprovisioned tenant object stays an event trigger — never downgrade to Manual); schedule/recurring → **Timer**; otherwise → **Manual**. |
| Task type on ambiguous verbs (`review`, `approve`, `validate`, `decide`, …) | Named human role or judgment implied → `action`; framed as automated/AI → `agent`; truly even → `action` (keeps a human in the loop; the user can flip it in one correction). Compliance trigger phrase (HIPAA, ECOA, FINRA, "licensed X", …) → `action`, always ([§ Task-type override priority](sdd-generation-rules.md#task-type-override-priority)). |
| "Manual" in-case work | Starts a new case → Manual trigger; optional worker-launched task → `adhoc` + `Required: No`; worker-chosen exception/rework lane → secondary stage with `user-selected-stage`. Pick by context; disclose. |
| Case exit | Last primary stage completes (`required-stages-completed`, `Marks Case Complete: Yes`) unless the user described another close-out; alternate outcomes → non-completing case-exit rules. |
| Stage exit ↔ Marks Complete pairing | Derive mechanically per sdd-template Key Rule 4 — never author an illegal pair. |
| SLA | Only when the user mentioned timing; take their words literally ("about a day" → 1 day). No timing mentioned → `—`. |
| Case name / prefix | PascalCase from the domain noun; prefix = 2–4 letter mechanical derivation. |
| Personas | Named roles verbatim; none mentioned → single `Process Owner`. |
| Optional fields untouched by the user | `—`. Never a question. |
| Resources / connections | §Tenant grounding light pass: single confident match adopted, everything else `resolve at build`. |

**Structure rules while sketching:** §1.5 declare-vs-xref — mint a §1.5 row ONLY for `In`/`Out` args, trigger-payload Variables, and state read by a condition or ≥ 2 consumers; a single upstream output feeding one consumer is referenced directly (`<- "Stage"."Task".out` / `vars.$xref(...)`), never relayed. Required fields (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit) must all be settled — by user input or by playbook assumption.

**Buildability musts** — settle all eight by assumption and surface each in the confirmation; they are where designs silently become unbuildable: (1) exception-lane trigger source (gate decision → `selected-stage-completed/-exited` + IF; person → `user-selected-stage`; event → `wait-for-connector`; interrupting flags on stage + entry rows; terminal `exit-only` vs `return-to-origin`; distinct entries per lane); (2) every decision outcome routes somewhere — no dead-end status values, and an outcome that targets a lane keys that lane's entry; (3) every configure/decide task's output lands in a variable or direct reference; (4) every send/connector/agent's required inputs map to variables/literals/upstream outputs as far as knowable without schemas — the rest resolves at build; (5) conditional roles/steps become guarded rules + personas, not prose; (6) a critical-path connector failure gets an exception lane when the user described failure handling — otherwise note it as an architect advisory, don't ask; (7) manual-surface classification per the playbook; (8) intended resource names concrete, identities per the light pass.

**The one clarifying call (rare).** Ask before the confirmation ONLY when: (a) no case is inferable at all (empty or contentless request), (b) the user's own inputs contradict each other on a shape-changing field, or (c) the user asked to be asked. Batch everything into ONE AskUserQuestion call (≤ 4 questions). An unclear answer → take the best assumption, disclose it, move on — never re-press. Everything else: assume and inform.

**Red flags — you're about to over-ask.** "I should confirm the trigger type" / "review could be action or agent, better ask" / "the SLA wording is vague" / "this resource has two matches" — STOP: the playbook decides all of these; the decision line in the confirmation is the user's chance to correct. The bar for a question is *contradiction or emptiness*, not uncertainty. Equally, there is NO size gate, no "approval before creating files", no lightweight mode — the only stops in Phase 0 are the one clarifying call (when earned), the confirmation itself, and the explicit-sign-off path.

### Case board — dual-render at the confirmation

The confirmation (and every correction re-show) renders from the SAME in-memory model, in the same turn:

1. **Chat structure — canonical.** The confirmation tables below. The question always anchors here; approval never depends on a browser.
2. **Case board file — enhancement.** At the first render, copy the static app byte-identical — `cp "<skill>/assets/templates/case-board.html" ./case-board.html` (sanctioned verbatim copy — SKILL.md Rule 13 carve-out) — then Write `./case-board-data.js` (`window.SDD_DATA = {...}` per the schema in the template's header comment). On corrections, patch only changed sections via Edit. Never Read either file back — the model lives in memory; the board is write-only output.
3. **One pointer line, first render only:** `Visual board: ./case-board.html — it updates as we refine.` Open it on request (`open` / `xdg-open`). Do not re-mention it.

Board failure → one-line notice, continue. The board never blocks, never gates, never substitutes for the chat confirmation.

### Confirm — the single checkpoint

One structured presentation of the whole case, one question. Run the [sdd-generation-rules.md § Finalization](sdd-generation-rules.md#finalization) checks against the in-memory model FIRST — fix failures silently (they are the agent's defects, not the user's decisions); anything unfixable becomes a flagged line. Then show, in chat (canonical) with the board refreshed in the same turn:

- **Happy path table** — one row per primary stage: `# | Stage | Target | Work | Who / what` (work = task names in order; who/what = user-visible type names, resolved resource names, or `resolve at build`).
- **Exception lanes** — one line each: name · what fires it · pauses/returns/closes.
- **Anytime actions** — optional worker-launched items, `resolve at build` marked.
- **Rules / tiers** — each conditional gate in one line.
- **Decisions I made** — EVERY assumption, override, and resource decision, one line each with its plain-language source (`Trigger: portal event (you said "submitted through the portal")` · `Review application: human task (compliance wording)` · `SlackNotify: resolve at build (two workspaces match)`). This block is mandatory and complete — it is how the user audits the design without being interrogated. Flagged items (unfixable Finalization findings, missing connections) appear here with a ⚠ marker.
- **Caller obligation** — mandatory fixed text when any §1.5 row is `Category: In` + `Type: file` (JobAttachment pre-create contract; Studio Web's "Start case" dialog handles it automatically). Omit otherwise.

Confirmation question (AskUserQuestion): `Build it — straight through` / `Build it — pause at the build preview` / `Change something`. The build choice records the Rule 11 preference — never re-asked mid-build. When ⚠ flagged items exist, relabel the first option `Build despite N flagged items — straight through`. For a **design-only** request swap the build options for `Save the design`; for a **draft** request, `Save as draft`.

Corrections (`Change something` or any free text) update the model, re-run affected Finalization checks, and re-show ONLY the changed rows plus their decision lines. A correction never restarts the walk.

**Explicit sign-off requests** ("only after I approve", "I'll review before you build") suppress nothing about the flow but add one explicit approval prompt after the confirmation is accepted and before any file is created — honor it exactly.

### Build start — SDD written alongside the build

On a Build answer:

1. **Transition line** (§What to say while working): `Starting the build — the design doc will be saved alongside as a reference. Say stop anytime.`
2. **One parallel batch:** Write `sdd.md` (full render from the confirmed in-memory model — direct Write, no draft, no rename) + `uip solution init <SolutionName>` (derived exactly as Phase 2 Step 6.0 does; its idempotent skip then applies) + Phase 1's Rule 3 `uip login status` → `registry pull` chain **only if Phase 0's pull did not already succeed this session** — a same-session successful pull is reused, never repeated (SKILL.md Rule 3 fast path). The SDD write is NEVER a standalone blocking turn — it always shares the batch with build actions.
3. **One artifact line** after the write lands: `Design doc saved to ./sdd.md — reference it anytime.`
4. Proceed into [planning.md](planning.md) Step 1 **from the in-memory model** — do not re-read the just-written `sdd.md` in this session. Re-read it only when working memory may be stale (context compaction, resumed session); then the file is authoritative (Rule 2). For later sessions and re-runs, `sdd.md` is the contract exactly as if the user wrote it.
5. If `sdd.md` appeared at the path since Phase 0 started, abort instead of overwriting.

**Design-only request:** write `sdd.md`, report the path in one line, stop before Phase 1. **Draft request:** write `sdd.draft.md`, report, stop — never promote. **Free-text corrections stay first-class after the build starts:** treat one as a targeted edit to the affected artifact (model + `sdd.md` + downstream), narrate it in one line, continue.

## HTML preview

Optional, **on-request only** — never offered proactively; the case board covers the visual need. Available any time after the confirmation exists, including mid-build. Self-contained local HTML: Case Definition, collapsible Stages & Tasks with detail panels, Personas & App Views, Integrations; persona/type filters, unresolved-only and schema-view toggles, search, print stylesheet.

Generation: Read [`assets/templates/sdd-viewer.html`](../assets/templates/sdd-viewer.html), replace the `__SDD_DATA__` token in its `<script id="sdd-data">` block with JSON serialized from the in-memory model (schema in the template's header comment — do NOT re-parse `sdd.md`), Write `./sdd-viewer.html` (Rule 13), tell the user: `Generated ./sdd-viewer.html — open it in a browser to review.` Failure → one-line notice, continue.

## Resumption

`sdd.draft.md` at trigger time is a leftover from an on-request draft or an older run. AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Use the draft — finalize and continue` | Read it as the design input, run Finalization, show the §Confirm summary built from it, proceed normally. |
| `Discard draft, start fresh` | Delete `sdd.draft.md`. Return to §Entry. |
| `Abort` | Exit. No file changes. |

## What to say while working

Silence and machinery-talk are both experience defects. Business-language lines only (§Forbidden vocabulary):

- **Decisions narrate as they land** — the doc-read lines and inference one-liners during Listen/Sketch are the running commentary; the `Decisions I made` block is the complete record.
- **Before any stretch longer than ~a minute without a question**, one expectation-setter: `Design confirmed — building now. Nothing needed from you for a few minutes.`
- **At milestones**, one line each, business terms only. Never per-tool-call narration.
- **The moment tenant grounding fails**, one line: `I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.` Never let `resolve at build` rows be the first signal.
- **When continuing past a point without a prompt** (build start, Rule 11 straight-through), name what happens next and how to interrupt.

## Forbidden vocabulary (user-visible output)

The user sees a conversation that produces a case. Never surface in chat or in `sdd.md`:

- `sdd.draft.md`, `tasks/registry-resolved.json`, internal filenames. (**Exceptions:** `sdd.md` (the artifact line), `case-board.html` (pointer line — once), `sdd-viewer.html` (at generation) are intentionally user-visible. `case-board-data.js` is never mentioned.)
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
| Board or viewer write fails | One-line notice, continue — chat is the approval surface. |

## Output contract — what the build sees

- **In-session:** the confirmed in-memory model drives Phase 1 directly. `sdd.md` — written at build start (batched with build actions) — matches it exactly. A Phase 0 pull that succeeded this session is reused by Phase 1 (no re-pull — Rule 3 fast path). `tasks/registry-resolved.json` is produced by Phase 1, not Phase 0; light-pass matches are hints Phase 1 re-verifies against the session cache.
- **Cross-session / re-run:** `sdd.md` is the sole contract, read per Rule 2 exactly as a user-provided file — including after context compaction. It may carry `<UNRESOLVED>` identities and `—` placeholders, but every process/agent/rpa/api-workflow task has a concrete `Resolved Resource`, every action a concrete Action App title, every case-management task a concrete `Child Case`.
- `case-board.html` + `case-board-data.js` — present when the confirmation rendered; ignored by Phase 1. `sdd-viewer.html` — on request only.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Strict binary trigger; presence = trust-as-written.
- **Do NOT interrogate.** No entry menu when the request has content, no per-dimension question walk, no confirming what the playbook decides. The budget is ONE clarifying call (when earned) + ONE confirmation. Uncertainty is resolved by assumption + disclosure, not by a question.
- **Do NOT hide a decision.** Every assumption, override, and resource pick appears in the `Decisions I made` block. Best-assumption without disclosure is guessing.
- **Do NOT run schema discovery (`tasks describe` / `case spec`) or ambiguity prompts in Phase 0.** One light name-match pass only; everything unclear is `resolve at build` — Phase 1 owns authoritative resolution and its Rule 17 gate.
- **Do NOT pull the tenant registry as a prerequisite, and never twice in one session.** The login/pull chain starts only when the case first shows tenant-bound work; a pull that succeeded this session is reused by Phase 1 (Rule 3 fast path). Equally, never delay the confirmation waiting for the pull.
- **Do NOT auto-pick among multiple resource matches.** Cross-folder or multi-match = `resolve at build`, disclosed. (Single confident match adopts silently — that is the only silent pick.)
- **Do NOT write `sdd.draft.md` or checkpoint files in a normal run.** The model lives in memory; the only pre-build writes are the board files. Drafts exist on explicit request only.
- **Do NOT block the build on the SDD write, and do NOT re-read the just-written `sdd.md` in-session.** The write shares a batch with the first build actions; memory drives the build. Re-read only on staleness (compaction/resume).
- **Do NOT ask the user to review or approve the `sdd.md` document.** The confirmation is the approval; the file is its artifact. An explicit sign-off request adds one prompt — nothing else does.
- **Do NOT let discovery subagents write skill artifacts, prompt the user, or run the registry pull.** Fan-out is read-only; the parent owns every write.
- **Do NOT go silent during assembly and build start.** Post the expectation-setter and milestone lines from §What to say while working.
- **Do NOT Read `case-board.html` or `case-board-data.js` back, and do NOT generate the board app inline.** Byte-copy + write-only data.
- **Do NOT use `sed`/`awk`/`python`/`node` to mutate `sdd.md`, `sdd.draft.md`, `case-board-data.js`, or `sdd-viewer.html`.** Read + Write/Edit only (Rule 13).
- **Do NOT invent gates or thresholds.** No size limit, no approval-before-creating-files, no complexity stop. The complete Phase 0 stop list: the one clarifying call (when earned), the confirmation, the explicit-sign-off prompt (when requested) — then the build's own gates (Phase 4 retry cap, debug, publish).
- **Do NOT narrate filenames or schema mechanics.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
