# Phase 0 — Interview Mode (sdd.md generation)

This file is a **thinking guide** for the agent: principles for how to listen, infer, ask, and resolve when no `sdd.md` is provided. Phase 0 produces an `sdd.md` that Phase 1 reads exactly as if a user wrote it.

> **Authoritative for the interview path only.** Trigger detection, mode behavior, hard stop, resumption, output contract. **Content rules** (authority hierarchy, task-type override priority, render-required fields, variable lineage, review items, source ledger) live in [sdd-generation-rules.md](sdd-generation-rules.md). Phase 1 logic lives in [planning.md](planning.md). Phases 2–6 live in [phased-execution.md](phased-execution.md).

## Goal

Produce a `sdd.md` shaped by [`assets/templates/sdd-template.md`](../assets/templates/sdd-template.md). After approval, Rule 2 applies: trust as written, no further gap-fill.

Phase 0 also writes:

- `tasks/registry-resolved.json` — one entry per task using Rule 9's required association and lookup keys, plus the resolved I/O contract when applicable.
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

When Phase 0 runs from scratch, first print the new-case roadmap from `SKILL.md § User-facing roadmap`, then AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Interview to generate sdd.md` | Begin interview (§Modes). |
| `I'll provide an sdd.md path` | Re-prompt for path. Re-check trigger. |
| `Abort` | Exit skill. No file changes. |

### Early tenant grounding and parallel discovery

After the user selects `Interview to generate sdd.md`, ask the Listen opener immediately. Do not make the user wait for tenant discovery before describing the case. Once the first description arrives, use dependency-safe waves:

1. **Wave 1 — overlap independent intake.** In one parallel tool batch, read every supplied document and run `uip login status --output json`. Extract named systems, resources, environments, likely tasks, and roles from the user's description and documents while login status resolves.
2. **Wave 2 — refresh before cache reads.** Only after login succeeds, run `uip maestro case registry pull`. Login → pull is sequential. If login or pull fails, continue the interview with `resource grounding unavailable` in working memory. Do not block Phase 0, do not treat missing cache files as empty results, and do not surface internal filenames. Phase 1 retries.
3. **Wave 3 — fan out candidates.** Once the pull succeeds and Sketch has stable likely task types/names or connector keys, search all independent candidates in parallel:
   - Runnable tasks (`process`, `agent`, `rpa`, `api-workflow`, `action`, `case-management`) → search the relevant caches by intended resource name and likely type.
   - Connector activities/triggers → search likely operations/triggers and inspect enabled Integration Service connections for each named connector/system.
   - Named systems with no stable task yet → record connector keys/connections as candidates only; do not invent connector tasks from the catalog.
   Keep only the top 1-3 plausible matches per described item, including folder/version/type.
4. **Wave 4 — resolve before confirmation.** Resolve trigger candidates before the case-shape packet and runnable/connector candidates before the work packet. Batch independent ambiguous resource/connection choices into one AskUserQuestion call when possible (up to 3 questions); keep each question scoped to one task, trigger, or connector.
5. **Wave 5 — fan out schemas.** After selections, run every independent `tasks describe` / `case spec` call concurrently across the selected live resources. A unique high-confidence candidate may start schema discovery immediately; its result must be available before the work or operational packet that depends on it. An ambiguous candidate must be selected first.
6. Use the resolved palette and schemas to make confirmation packets concrete. The later Resolve mode reconciles changed or stale items; it is not the first discovery pass.

**Grounding guardrails:**

- Registry and connection data are evidence, not requirements. Never create a stage/task because the tenant has a resource, and never rename domain work to match a resource.
- Do not dump catalogs or broad option lists. Candidate prompts are scoped to a task, trigger, connector, or system the user already described.
- A single high-confidence candidate can be carried silently into Resolve's auto-confirm bucket and schema fan-out; the user sees the resource in the work packet and the auto-confirm count at Approve.
- Multiple resources with the same name in different folders are ambiguous. Ask with the folder in the option label.
- A connector type with zero enabled connections is an unresolved connector identity, not proof the task should become `api-workflow` or Manual.
- If the sketch changes a task's type, intended resource name, connector, or operation, discard stale candidates and re-search.
- Parallelize reads and tenant I/O only after their prerequisites. Never run cache searches before a successful pull, schema discovery before an ambiguous selection, or final promotion before approval.
- Phase 1 remains authoritative: it refreshes the registry again and reuses Phase 0 results only when the current SDD still matches them.

## Modes

Phase 0 moves through five modes of attention. Listen opens broad while tenant grounding starts; Sketch assembles the case model; Ask confirms it in three plain-language packets; Resolve reconciles only changed or unresolved tenant mappings; Approve validates the draft and promotes it after consent. Listen / Sketch / Ask loop freely as new context lands.

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
- **Named systems seed grounding.** When the user names a deployed resource, app, connector, external system, environment, or connection ("Salesforce Prod", "VendorRiskAgent", "Invoice Approval app"), add it to the candidate palette from §Early tenant grounding. Do not ask the user to browse all tenant resources; search only for what they named or what the sketch has inferred.

Listen does not ask shaping questions — those belong in Ask's confirmation packets (§Ask). The opening prompt is the *opener*, not the whole interview: capture what the user volunteers, then let the packets drive every dimension to depth. The single exception is technical: when a referenced doc is unreadable (see `.docx` / `.pptx` / scanned-PDF row above), request a paste so Listen can keep reading. Inferences are private to the sketch.

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
- **§1.5 declare-vs-xref (apply while sketching variables, every path).** Mint a §1.5 row ONLY for `In` / `Out` args, trigger-payload Variables, and case-level state read by a condition or in ≥ 2 places. An input that is just one upstream task's output is referenced directly (`<- "Stage"."Task".out` / `vars.$xref('Stage','Task','out')`), NEVER relayed through a new §1.5 variable. This holds on the **doc-derived path** (Listen reads a PDD/spec → Sketch) too, where the interactive Resolve back-solve does not run — so the steer must be applied here. See [sdd-generation-rules.md § 1.5 Case Variables](sdd-generation-rules.md) and § Variable lineage closure.
- **Resource grounding while sketching.** As soon as a task has a stable likely type + intended resource name, or a connector/system has a stable connector key, search the candidate palette. Use matches to propose the right task type/resource/connection in Ask, but keep the draft portable: type-specific intended names are concrete, identity/folder fields remain tentative until Resolve finalizes them. A miss means "ask or unresolved later," never "change the business process."

**Required fields (block until answered):**

| Field | Source |
|---|---|
| Case Name (PascalCase) | Listen / Ask |
| Case Identifier prefix (2-4 char UPPER) | Listen / inferred / Ask |
| ≥1 Trigger (Manual / Timer / Connector Event) | Listen / Ask |
| ≥1 Stage with name | Listen |
| ≥1 Task per stage with name + type | Listen / Ask per stage |
| ≥1 Case exit condition | Listen / Ask |

Do not render or rewrite the complete `sdd.draft.md` after every answer. Persist resumable partial SDD state only after each confirmation packet is accepted: seed/update Case Definition + stage skeleton after packet 1, stage/task blocks after packet 2, and variables/personas/integrations after packet 3. Use one section-batched Read → mutate → Write/Edit cycle per accepted packet (maximum three routine draft updates). Free-text corrections update only the affected section. After Resolve reconciliation, render/fill the complete template once before Finalization.

### Ask

Ask is a **three-packet confirmation walk**, not a gap-only afterthought or a field-by-field form. Listen seeds the sketch and early tenant grounding makes it concrete. Ask then presents the agent's reasoning in three short, plain-language summaries. Each packet asks the user to confirm, change, or add; the user validates the understandable case model rather than the SDD syntax.

Before a packet, ask any unresolved Always-Ask question whose answer would materially change that packet. Do not hide two plausible interpretations inside a summary. After a packet is accepted, checkpoint only its affected SDD sections. The final Approve summary is the second confirmation layer before `sdd.md` exists.

#### Confirmation packet 1 — case shape

Resolve any connector/event trigger candidate needed by this packet, then show:

- One-sentence objective.
- What starts the case.
- Primary stage flow from start to finish.
- Every interrupting secondary stage, stated as what pauses active work, how it starts, and whether it returns or closes the case.
- Successful completion and alternate outcomes.

Use a compact shape such as:

```text
Starts when: A request arrives from the customer portal
Main flow: Intake → Review → Fulfillment
Interrupting work:
- Escalation pauses Review and returns to Review
- Withdrawal pauses active work and closes the case
Done when: Fulfillment completes
```

Do not expose rule names, `Interrupting: Yes`, or stage-entry syntax. Ask one confirmation question. Corrections loop within this packet until the shape is accepted.

#### Confirmation packet 2 — work inside stages

Before this packet, fan out all stable resource/connection searches, resolve independent ambiguities in batched prompts, and fetch schemas for unique or selected live resources. For every stage, show each task in source order with:

- Task name and plain-language purpose.
- Task type (`Human action`, `Agent`, `Process`, `API workflow`, `Connector activity`, `Wait`, or `Child case` in user-visible text).
- Activation (`Sequential`, `Event-driven`, or `Manually triggered`).
- `Required` or `Optional`; manually triggered tasks are always shown as optional.
- Owner/persona when known.
- Selected tenant resource/connection, or `Not available yet` when unresolved.

Example:

```text
Review
1. Extract application details — Agent — Sequential — Required — ApplicationTriageAgent
2. Review application — Human action — Sequential — Required — Underwriter
3. Request specialist review — Human action — Manually triggered — Optional — Underwriter
```

Do not expose `adhoc`, resource IDs, folder IDs, or cache terminology. If the case has more than 5 stages or 10 tasks, split this packet into consecutive stage groups while retaining one conceptual work confirmation; do not produce one prompt per task.

#### Confirmation packet 3 — operational contract

Run all selected-resource schema discovery before this packet. Show only business-relevant facts:

- Decision outcomes and their destination stages/outcomes.
- Information entering and leaving each task/stage, including every required live-resource input.
- Resource and enabled-connection mappings.
- Personas/ownership not already obvious from packet 2.
- Case/stage/action timing the user mentioned.
- Unavailable resources, connections, or required inputs that will remain unresolved.

Use a compact summary grouped under `Decisions`, `Data`, `Resources`, `Timing`, and `Not available yet`. Ask one confirmation question. If tenant schema discovery introduces a requirement that contradicts packet 2, return to the affected packet and show only the delta before continuing.

#### Packet rules

- A packet is mandatory even when Listen was detailed; high-confidence content is presented for confirmation rather than skipped.
- Preserve the user's vocabulary and stage/task order.
- User corrections invalidate only affected downstream reasoning. Re-search/re-describe only resources whose type, intended name, connector, operation, or binding changed.
- Do not re-confirm unchanged packets. Show a delta confirmation when later tenant evidence materially changes an accepted packet; otherwise continue silently.
- The three packets replace the old one-prompt-per-dimension walk. Always-Ask questions and genuine resource ambiguities remain focused questions because they prevent shape-changing mistakes.

#### Buildability musts (capture across the packets)

Eight things decide whether the SDD builds in one pass. Capture each in the named packet before it is accepted — they are where SDDs silently become unbuildable:

1. **Exception trigger source** (packet 1) — per lane, ask *how it fires*: a gate decision → `selected-stage-completed`/`selected-stage-exited` (+ `IF` on the decision var); a person launches it → `user-selected-stage`; an external event → `wait-for-connector`. Secondary stages are interrupting lanes: set `Interrupting: Yes` on the stage and on every secondary-stage entry row. Terminal lanes end (`exit-only` + §1.4a case-exit); return lanes use `return-to-origin`. Keep each lane's entry **distinct** — identical entries fail `validate`. See [sdd-generation-rules.md § Logical integrity](sdd-generation-rules.md#logical-integrity--stage-graph).
2. **Decision outcome → route** (packet 3) — per button, capture its outcome variable AND destination (advance / which exception / loop). No outcome may dead-end: a status string with nowhere to go is a broken branch. When the destination is an exception lane, that lane's entry MUST key off this variable's value (§Logical integrity step 5) — a button that "routes to the X lane" while X is entered only by an external event is a dead branch, blocked at Finalization step 15.
3. **Task output capture** (packet 3) — per configure/decide/capture task, name the §1.5 variable that stores its result. A form that collects values (rate, terms) but binds no output silently loses them.
4. **Required-input back-solve** (packet 3) — per send/connector/agent, map every required input to a variable: an email needs a recipient *address* var (not a name); an agent needs its source data.
5. **Conditional gates** (packets 2–3) — ask if any role or step is conditional on a value (loan size, risk, region). Model a guarded rule + persona, never a prose footnote (e.g. `>$5M → Credit Analyst review`).
6. **Connector failure cover** (packets 1–3) — when an `execute-connector-activity` / `wait-for-connector` sits in a primary (non-exception) stage on the critical path, ask whether a failure needs handling. Model the handler as an exception lane entered on the failure / error event; with ≥ 2 such connector tasks and no cover, Finalization raises a `high` review item (`rev_no_failure_path`). Record provenance if the user declines.
7. **Manual activation classifier** (packets 1–2) — decide which "manual" surface the user means before rendering: a user/API starts a new case → Manual trigger; a case worker launches one optional task inside the current stage → task `adhoc` + `Required: No`; a case worker chooses an interrupting exception/rework lane → secondary stage with `user-selected-stage`, not task `adhoc`.
8. **Resource/connection grounding** (packets 1–3) — for each runnable or connector-bound task, capture the intended resource/connector name early and check the candidate palette. A resolved-looking type with no live instance still needs a portable intended name plus unresolved identity. A connector operation with 0 or >1 enabled connections needs an Ask before the packet that displays it; do not let the SDD reach Approve with a silent connection guess.

#### Single-question (default for shape-changing gaps)

**One question at a time**, ranked by information value. Use plain AskUserQuestion before the affected packet, stage the answer in working memory, and checkpoint it with that packet rather than rewriting the draft immediately. Apply to:

- Trigger type (when external system / portal / form / schedule / signup / event is mentioned)
- Task type on ambiguous verbs or compliance-override conflicts
- Case exit condition
- Stage exit `Marks Stage Complete: Yes` ↔ WHEN pairing
- SLA value when user mentioned timing
- Variable Type when file / attachment / document is in scope (see §Listen file detection)

These fields change the generated case shape; bundling them obscures the decision and survives the Approve scan.

#### Batched independent choices

Batching is allowed in two places only: (a) up to 3 independent ambiguous resource/connection selections before packets 1–2, and (b) one low-impact AskUserQuestion for fields whose defaults do not change case shape. Never batch dependent questions.

Low-impact fields:

| Field | Default if not picked |
|---|---|
| Case-level description (Section 1.1) | `—` (Phase 1 leaves blank) |
| Persona descriptions (Section 3) | `—` |
| Secondary-stage descriptions | `—` |
| Optional `conditionExpression` cells in Entry / Exit rows | `—` (no IF filter) |
| Optional `Business Calendar` cell on timers | `—` (use 24×7) |
| Optional task SLA on `action` tasks | `—` (inherits case SLA) |
| App-view detail (Section 3) | "Case list" + "Case detail" baseline view names |

Use the low-impact batch at most once in the whole interview. Each row defaulted records `inferred-default:<reason>` in the source ledger. Resource/connection batches do not consume this allowance because they replace independent per-item prompts with the same choices.

#### When to Ask vs Default

**Default to Ask when in doubt.** Ask is cheap (~30s). A wrong default is expensive: the user scans the Approve summary fast, the default may survive, Rule 2 locks the file, and a Phase 1 re-run is forced.

**Default with narration** ONLY when ALL three high-confidence criteria hold for the field:

1. **Verbatim or one-step mechanical.** The value is either (a) written verbatim by the user, (b) lifted from a doc the user shared and currently in your context, or (c) a one-step mechanical derivation. Allowed derivations: `PascalCase → 2–4 letter prefix`; `no roles mentioned → persona=Process Owner`; user said `"I kick it off"` / `"we start the case manually"` → `trigger=Manual`. If the user says `"manual"` / `"ad-hoc"` about in-case work, ask whether they mean an `adhoc` task or a user-selected secondary stage.
2. **No interpretation step.** If you have to choose between two plausible meanings, it's interpretation — Ask.
3. **Field is not on the Always-Ask list below.**

**Always-Ask** (never default — these change case shape, wrong defaults force Phase 1 rework):

| Field | Why never default |
|---|---|
| Trigger type when ANY external system, portal, form, schedule, signup, or inbound event is mentioned | `Timer` / `Connector Event` change generation path. "Vendor signs up" → portal/event, NOT Manual. |
| Trigger type when a tenant case-entity / data-object record-created start is mentioned | This is an event trigger with the named object as Source. Missing tenant provisioning is handled later as an unresolved placeholder, not by downgrading to Manual. |
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
| "The named data object might not exist in this tenant, so Manual is safer." | Preserve the object as an event trigger. Unresolved resources become placeholders during planning/build. |
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

### Resolve

Resolve is incremental and starts during Sketch. It must finish each tenant-dependent decision **before** the confirmation packet that displays that decision. The late Resolve mode is reconciliation only: confirm that accepted task types, intended resource names, connectors, operations, folders, identities, and schemas still match the current draft. Do not restart from a blank search set when §Early tenant grounding already found candidates. If any matching field changed during Ask, discard only that stale candidate and re-search/re-describe it.

Before final registry selection, establish the concrete intended resource name for every `process`, `agent`, `rpa`, `api-workflow`, `action`, and `case-management` task. Write it to the task type's portable-name field: `Resolved Resource` for process/agent/rpa/api-workflow, the `Action App: <deploymentTitle>` value in `HITL Implementation` for action, and `Child Case` for case-management. Preserve a name the user supplied; if it is absent, ask rather than silently substituting the task's display name. These portable-name fields are NEVER `<UNRESOLVED>`.

Find each matching registry resource using that intended name. Search the cache file under `~/.uip/case-resources/` by name keywords. Filename varies by component type — common cases:

- `process-index.json`, `agent-index.json`, `api-index.json`, `processOrchestration-index.json`, `caseManagement-index.json` — `<type>-index.json` shape
- `action-apps-index.json` — kebab + plural for HITL action apps
- `typecache-activities-index.json` — for `execute-connector-activity` (`CONNECTOR_ACTIVITY`)
- `typecache-triggers-index.json` — for `wait-for-connector` (`CONNECTOR_TRIGGER`)

If §Early tenant grounding did not complete a successful pull, run `uip login status --output json` and then `uip maestro case registry pull` before treating any cache as searchable. If the pull fails, follow §Failure modes: keep portable intended names, mark only identity/folder fields unresolved, and let Phase 1 retry. See [registry-discovery.md § Cache File Index](registry-discovery.md#cache-file-index) for the authoritative file list, identifier fields, and cross-type fallback rules.

**Resource reality — resolve EVERY runnable across all registry types, and confirm a LIVE instance, not just a type match.** Resolving the real identity here is what lets Phase 1–3 build in one pass; defer it and the build halts on first use.

| Task type | Resolve to | Buildable only when a live instance exists |
|---|---|---|
| `execute-connector-activity` | connector `typeId` + operation (`typecache-activities-index.json`) | a registered IS **connection** (`connectionId`) for that connector |
| `wait-for-connector` | connector-trigger `typeId` (`typecache-triggers-index.json`) | an IS connection for the inbound event |
| `agent` | `agentId` (`agent-index.json`) | the agent is **deployed** — or built inline at the Phase 1 Rule 17 Create gate (in-solution sibling) |
| `action` (human task / HITL) | `actionAppId` (`action-apps-index.json`) when a deployed Action App matches | else `<UNRESOLVED>` + Rule-8 placeholder — inline JSON-schema authoring is NOT supported by the action plugin |
| `process` / `rpa` | `processOrchestrationId` (`process-index.json` / `processOrchestration-index.json`) | the process is **published** |
| `api-workflow` | `apiWorkflowId` (`api-index.json`) | the API workflow is **deployed** — or built inline at the Phase 1 Rule 17 Create gate (in-solution sibling) |
| `case-management` | child case (`caseManagement-index.json`) | the child case is **published** |

A *type* match with **no live instance** still ships an unresolved identity + a `high` review item — never fabricate IDs (SKILL.md Rule 8). Preserve the type-specific portable name: `Resolved Resource` for process/agent/rpa/api-workflow, the Action App title for action, and `Child Case` for case-management. Write `<UNRESOLVED>` only to that type's resolution fields: `Resource Identity` + `Folder Path`, or `Action App ID` + `Deployment Folder`. (A connector type can exist in the catalog while the tenant has zero connections — its identity is still unresolved.)

**Narrate the search before presenting matches.** Don't drop the AskUserQuestion cold:

> `Searching registry for "InvoiceValidation"… 2 matches.`

#### Resolution cadence — parallel fan-out and packet confirmation

As soon as stable intended names/types are available, run or reuse all independent task, trigger, operation, and connection searches in parallel, then bucket results:

| Bucket | Definition |
|---|---|
| **A — single high-confidence** | Exactly 1 match **across all folders**, AND the match's name shares ≥ 1 token (case-insensitive, ≥ 3 chars) with the task's intended resource name |
| **B — ambiguous** | Multiple matches (**including the same resource name present in ≥2 folders** — a cross-folder name never auto-confirms), OR single match with no token overlap |
| **C — empty** | 0 matches across cache files |

Provisionally select bucket A without a separate gate, record `tenant-registry:<resource-name>` provenance with `auto_confirmed: true` and `grounded_early: true`, and show the concrete selection in confirmation packet 2. Packet 2 is the user's confirmation of those picks; the Approve summary also surfaces `Auto-confirmed: N registry matches (single-match high-confidence).`

#### Batched ambiguity prompts (bucket B + bucket C remainder)

Use one AskUserQuestion call with up to 3 independent questions; each question represents one ambiguous task/trigger/connector and has 4 options max. Continue in additional batches when needed. **When candidate matches differ by folder, each option label MUST carry the match's folder `fullyQualifiedName`** — the user is choosing a folder, not just a name. Tasks resolve independently, so the resulting case may bind different tasks to resources in different folders/solutions (mixing is valid — there is no single-solution constraint):

| Option | Effect |
|---|---|
| `<top match — name · folder · version · type>` | Record selection (incl. chosen folder). |
| `<second match — name · folder · version · type>` (if available) | Record selection (incl. chosen folder). |
| `Placeholder — resolve later` | Keep `<UNRESOLVED>` on `taskTypeId` / `typeId` / `connectionId`. Retain the task type's concrete portable name and leave only its identity/folder fields unresolved. Phase 1 emits a placeholder task per Rule 8. **For an `agent` or `api-workflow`,** Phase 1's Rule 17 gate additionally offers to build it inline as an in-solution sibling ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)) — a no-match resource of these kinds need not stay manual. Action Apps and child cases remain placeholder-only. |
| `Something else` | Free-text re-search keyword, retry. |

**Empty registry match** across bucket C → AskUserQuestion `Force pull and re-resolve` / `Use placeholders for all` — plus, when ≥1 still-empty is an `agent` or `api-workflow` AND the CLI supports `registry --local`, `Create missing resources inline` (build as in-solution siblings; see [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery)) — per Rule 17, applied per batch, not per task. When the user picks `Use placeholders for all`, every unresolved task emits a high-severity review item per [sdd-generation-rules.md § Review items](sdd-generation-rules.md#review-items).

#### Schema discovery — pull each resolved task's I/O contract

Identity is not the whole contract. The SDD's task Inputs / Outputs `Field` cells MUST match the resource's real argument / field names verbatim (see [sdd-generation-rules.md § Task content rules](sdd-generation-rules.md#task-content-rules)), and a connector's *required* inputs stay invisible until its schema is read. For every task resolved to a **live instance** (skip tasks whose identity is `<UNRESOLVED>` — no identity, no schema), pull its contract and use it to fill the `Field` cells from the real names and to back-solve required inputs against the *actual* list, not the user's recollection.

Run in parallel after the picks land — `--output json`, connectors via `spec`, runnables via `tasks describe`. Start a bucket-A candidate immediately so its contract is ready before packet 2 or 3; wait for the user's selection before describing a bucket-B candidate:

| Resolved task type | Discovery command | Yields |
|---|---|---|
| `process` / `agent` / `rpa` / `api-workflow` / `action` / `case-management` | `uip maestro case tasks describe --type <type> --id <resolved-id> --output json` | In / Out argument names + types |
| `execute-connector-activity` | `uip maestro case spec --type activity --activity-type-id <typeId> --connection-id <connId> --skip-case-shape --output json` | required body / query / path fields, output fields, filterable fields |
| `wait-for-connector` + connector **event trigger** | `uip maestro case spec --type trigger --activity-type-id <typeId> --connection-id <connId> --skip-case-shape --output json` | required event params, output payload fields |
| `wait-for-timer` | — | no contract — skip |

For each task with required inputs the sketch has not mapped, one AskUserQuestion in business terms — name the inputs, never the schema mechanics (§Forbidden vocabulary):

> `Send Slack message needs a channel and a message body — what feeds each?`

Map each answer to a variable, a literal, or an upstream task's output (§Ask → Buildability musts). **When the answer is an upstream task's output, reference it directly** — whole-value `<- "Stage"."Task".out` or, inside a larger `=js:` expression, `vars.$xref('Stage','Task','out')` — and do NOT mint a §1.5 Case Variable for it (the emitting task is its own producer; see [sdd-generation-rules.md § Resolved-resource I/O completeness](sdd-generation-rules.md#resolved-resource-io-completeness)). For an event trigger, surface required event params the same way (e.g., which mailbox folder) and fill each payload-extraction Variable's `sourceFields` path from the discovered output shape. A filter clause the connector can't support → narrate and Ask for a substitute. A required input the user skips → `<UNRESOLVED>` + a `high` review item (optional input skipped → `medium`). Coverage closes against the resource's **own required-input list**, not the user's recollection — every required input ends Resolve either bound or `<UNRESOLVED>`+review-item; the Approve gate re-checks this (§Finalization step 19).

**Connection selection (connector tasks).** For each `execute-connector-activity`, `wait-for-connector`, and connector event trigger, resolve the IS **connection**, not just the activity `typeId`. When the cache holds **0 or > 1** connections for the connector, include that connector in the next batched ambiguity prompt — in business terms (the account / environment name, never the `connectionId`). Never auto-pick among multiple, never leave `connectionId` silently `<UNRESOLVED>`; a missing connection is a `high` review item per §Resource reality.

**Action-app field fidelity.** For each `action` task resolved to a deployed app, author the Input / Output Schema **only** from the app's `tasks describe` fields. If the user described context the app does not expose, AskUserQuestion: `Deploy a task-specific app` / `Limit inputs to the app's fields` / `Placeholder — resolve later`. Never author a field the app lacks — it cannot bind ([sdd-generation-rules.md § Finalization step 16](sdd-generation-rules.md#finalization)). If ONE app is the best match for ≥ 2 tasks that each need different fields, that is the generic-substitute smell — surface it (`rev_substitute_app`) rather than authoring divergent schemas onto the same app.

**Cost.** One CLI call per resolved task, run in parallel and resolved-only. This discovery happens before confirmation rather than as a late serial Resolve, so it reduces wall-clock time while preventing wrong `Field` names and unmapped required inputs from surviving into Phase 3 / 4.

After all picks and schema discovery, freeze the shared resolution state. Then persist `tasks/registry-resolved.json` and the affected `sdd.draft.md` sections concurrently because they are distinct files. The JSON uses Rule 9 shape and MUST record, per resolved task, each declared **input name + `required` flag** and the full **declared output-field list** — Phase 3 io-binding Check 5 re-verifies required-input coverage and output-field fidelity against this without re-fetching ([io-binding/impl-json.md § Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness)). In the draft, a resolved task uses the selected entry's canonical type-specific name, exact folder, and identity; an unresolved task retains its requested portable name and uses `<UNRESOLVED>` only for its identity/folder fields. Also update the matching Section 4 roll-up row when that resource family has one. Any unresolved task carries a paired `review_items[]` entry in the same JSON.

At late reconciliation, compare every accepted mapping to the frozen state. If nothing material changed, continue without another prompt. If a resource disappeared, a connection changed, a schema added a required input, or an accepted task changed type/name/operation, show one plain-language delta confirmation and update only the affected packet. Re-read `sdd.draft.md` and `tasks/registry-resolved.json` in parallel before Finalization.

> **Phase 1 handoff.** `sdd.md` is the authoritative handoff; `tasks/registry-resolved.json` is an optional cache/audit artifact. Phase 1 reuses an entry only after its type, searched cache, canonical name, exact folder, and identity match the current SDD per [planning.md § Phase 0 carryover](planning.md#step-2--locate-and-parse-the-design-document). A missing, unresolved, or mismatched field makes the entry stale and triggers discovery from the SDD's type-specific portable name (`Resolved Resource`, Action App title, or `Child Case`).

### Approve

Complete `sdd.draft.md`, then run all 19 **Finalization checks** in [sdd-generation-rules.md § Finalization](sdd-generation-rules.md#finalization) against the draft. Do not create `sdd.md` yet. Any blocking failure routes back to `Re-edit` / `Restart` / `Abort`. Advisory pass (step 14) emits `medium` review items but does not block; `high` review items gate through an explicit opt-in.

On pass:

1. Print a concise commit summary (not the full document). This is the second confirmation layer over the three accepted packets:

```
Ready to create sdd.md.

Case: <name>
Starts when: <plain-language trigger>
Main flow: <Primary A> → <Primary B> → <Primary C>
Interrupting work:
  - <Secondary>: pauses <origin>; <returns to origin | closes case>
Outcomes: <successful completion>; <alternate exits>

Tasks: N  sequential=N  event-driven=N  manually-triggered=N
Resources: resolved=N  not-available-yet=N
Integrations: N  Personas: N  Child cases: N
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

The summary MUST include the plain-language start, main flow, interrupting secondary stages, outcomes, task activation counts, and resolved/unavailable resource counts. It must be sufficient to approve without opening the SDD. The **`Inferred / defaulted` block is mandatory** whenever Sketch defaulted ANY field. List every defaulted value with source attribution. Omit the block only if zero fields were defaulted. This is the user's last chance to catch wrong defaults before Rule 2 locks the file — never collapse to counts alone when defaults exist.

The **`Caller obligation` block** is mandatory when any §1.5 row has `Category: In` + `Type: file`. Omit otherwise. The text is fixed; do not paraphrase.

The **`Architect advisories` block** lists each `medium` review item emitted by the architect's-lens pass ([sdd-generation-rules.md § Architect's lens](sdd-generation-rules.md#architects-lens)). Omit when count is 0. These do not block Approve but should be visible.

Source-attribution examples: `(PascalCase derivation)`, `(no roles mentioned → Process Owner)`, `(no SLA stated → 3-day default)`, `(verb "review" — defaulted to action)`, `(user said "start the case manually" → trigger=Manual)`, `(user said "manual follow-up task" → task entry=adhoc)`.

2. AskUserQuestion (4 options — base set; if any `high` review items exist, replace `Create SDD and continue` with `Create SDD despite N high-severity items` populated with the count):

| Option | Next |
|---|---|
| `Create SDD and continue` | Atomically rename `sdd.draft.md` → `sdd.md`, then exit Phase 0 and begin [planning.md](planning.md) Step 1. |
| `Generate HTML preview` | Write `./sdd-viewer.html` from the validated draft (§HTML preview). Re-show this prompt. |
| `Change something` | Free-text correction → update only the affected section of `sdd.draft.md` → re-run affected Finalization checks → re-show summary. |
| `Restart or abort` | Follow-up AskUserQuestion (`Restart interview` / `Abort`). Restart wipes `sdd.draft.md` and `tasks/registry-resolved.json`, then returns to §Entry. Abort exits and leaves draft artifacts in place. |

3. Only after the user approves, atomically rename `sdd.draft.md` → `sdd.md`, report its path, and proceed. If `sdd.md` appeared since Phase 0 started, abort instead of overwriting it.

**Free-text corrections are first-class refines.** A message like "actually the SLA on Compliance is 8 hours not 4" is treated as an edit — update the affected section in `sdd.draft.md`, narrate the change, return to Approve. The user does not need to pick the `Change something` option to make corrections.

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

If the user edits `sdd.draft.md` after a preview is generated, the existing `sdd-viewer.html` is stale. Either regenerate it (re-pick `Generate HTML preview` at Approve) or leave it — Phase 1 ignores the file either way.

## Resumption

When `sdd.draft.md` is present at trigger time, AskUserQuestion (4 options):

| Option | Effect |
|---|---|
| `Resume from where I left off` | Re-read `sdd.draft.md`. Infer the last complete packet from populated sections; when `tasks/registry-resolved.json` is present, reconcile it against the draft before resuming. Continue from the next incomplete packet. |
| `Discard draft, restart` | Delete `sdd.draft.md` + `tasks/registry-resolved.json`. Return to §Entry. |
| `Use draft as-is, finalize` | Run Approve gate on the draft as-is. Edit validation may flag missing required fields. |
| `Abort` | Exit. No file changes. |

Raw Listen output is never persisted. Resumption picks up from the last confirmed packet recorded in the partial draft.

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
| Registry pull fails (CLI error, no auth) | Skip live resolution. For process/agent/rpa/api-workflow, keep a concrete intended `Resolved Resource`; for action, keep the Action App title; for case-management, keep `Child Case`. Mark only the type-specific identity/folder fields `<UNRESOLVED>` and pair the unresolved identity with a `high` review item. Phase 1 retries discovery and emits placeholders only for identities that remain unresolved. Inform user. |
| `sdd.md` already exists at path when interview begins | Should not happen — trigger detection exits Phase 0 first. If race, abort with error. Never overwrite. |
| HTML preview generation fails (template missing, write error) | Inform user, fall back to text summary only. Approve gate is unaffected. |

## Output contract — what Phase 1 sees

After Approve:

- `sdd.md` — always present. May include `<UNRESOLVED>` markers or `—` placeholders, but every process/agent/rpa/api-workflow task has a concrete `Resolved Resource`, every action has a concrete Action App title, and every case-management task has a concrete `Child Case` name.
- `tasks/registry-resolved.json` — **present only if Resolve ran successfully.** Absent when Resolve was skipped (registry pull failed, no auth, or the cache was unreachable — see Failure modes). Phase 1 ([planning.md § Step 2](planning.md#step-2--locate-and-parse-the-design-document)) validates every carry-over entry against the current SDD before reuse; stale or mismatched entries are re-resolved from the type-specific portable name and replaced. If the file is absent, Phase 1 runs full discovery and writes a fresh file. Either way, format matches Rule 9 when written.
- `sdd-viewer.html` — present only if user generated the preview. Phase 1 ignores it.
- `sdd.draft.md` — deleted (atomic rename at Approve).

Phase 1 ([planning.md](planning.md) Step 2) reads `sdd.md` exactly as a user-provided file. Rule 2 applies from this point: trust as written, no further gap-fill.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Strict binary trigger; presence = trust-as-written.
- **Do NOT suggest or invoke any other skill automatically during the interview.** Keep the interview self-contained; the user may explicitly invoke another skill when needed.
- **Do NOT persist Listen output as a transcript.** Inferences live in the working sketch and the packet-checkpointed draft, not in a separate transcript file.
- **Do NOT use `sed`/`awk`/`python`/`node` to mutate `sdd.draft.md`, `sdd.md`, `tasks/registry-resolved.json`, or `sdd-viewer.html`.** Read + Write/Edit only (Rule 13).
- **Do NOT bundle dependent or shape-changing questions.** Ask those one at a time before the affected packet. Independent resource/connection ambiguities may share one call (up to 3 questions), and each confirmation packet intentionally summarizes several already-reasoned facts.
- **Do NOT silently auto-pick ambiguous registry matches.** Single-match high-confidence resources may be provisionally selected only through the §Resolve cadence, must be shown in confirmation packet 2, and must surface as a count at Approve. Ambiguous matches, cross-folder name matches, missing connections, and empty matches always ask or become explicit unresolved identities with review items.
- **Do NOT treat the HTML preview as approval.** It is a review aid; the final create-SDD approval is still required after the three packet confirmations.
- **Do NOT narrate filenames or schema mechanics in user-visible output.** See §Forbidden vocabulary.
- **Do NOT ask for permission to read user-provided docs.** If the user named them, read them.
