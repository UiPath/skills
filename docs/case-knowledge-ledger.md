# Case Knowledge Ledger — conflict rulings & consolidation map

Phase 0 deliverable of the case-knowledge restructure (stacked-PR series). Every conflict found by the
2026-08-17 duplication audit is ruled here **once, with evidence**; every later PR in the series cites this
ledger instead of re-arguing. Nothing is deleted from either skill until its content is mapped here.

**Evidence environment:** `uip 1.198.0-preview.102` (validate = `@uipath/case-schema` SDK path), probed
2026-08-17. FE baseline: PO.Frontend `develop` @ `e8c176e4d`, case schema `27.0.0`. Probe method: minimal
v27 `caseplan.json` variants run through `uip maestro case validate --output json`; FE claims verified in
source (`src/types/case-mgmt-zod/`, `src/services/validation/case-mgmt/`).

Provenance convention: every ruling carries an `(as of …)` anchor. An expired anchor means re-verify, not
false.

---

## 1. Conflict rulings (C1–C13)

### C1 — Is `isRequired` written into the stage node? **YES.**
- Conflict: `implementation.md:123` ("planning-only metadata, not written into the stage node") vs
  `plugins/stages/impl-json.md:43,72,94` (emits it + post-write-checks it).
- Ruling: **write `data.isRequired` explicitly on every stage node.** It is schema-invisible but
  compiler-read (drives `required-stages-completed`), and validate resolves absent as not-required (see C2).
- Evidence: probe `p00` (valid with the field); FE `Node.d.ts:364` — field read by compilation, absent from
  zod schema (unvalidated-but-load-bearing class).
- Fix: correct `implementation.md:123`.

### C2 — Stage `isRequired` default. **No silent defaults anywhere; explicit end-to-end.**
- Conflict: `plugins/stages/planning.md:48` (default `true` for regular) vs same file `:79,:91` +
  `impl-json.md:17` (fall back to `false`) vs planner rules guide `:449` (`Yes` default).
- Ruling: **the SDD must state Required per stage (design guidance: primary = Yes unless argued);
  `tasks.md` carries it explicitly; emission writes it verbatim. Absent in JSON = NOT required.**
- Evidence: probes `p09`/`p10` — with `isRequired: false` *or absent*, `required-stages-completed` fails
  validate identically: `Case rule '…' has no required stage(s) selected` (as of uip 1.198.0-preview.102).
  Absent ≡ false at the validator; a build-side "default false" silently breaks case completion.

### C3 — Stage position. **Never compute positions; layout-strip wins.**
- Conflict: `plugins/stages/planning.md:66` ("auto-computed by the impl-json recipe: x = 100 + count*500")
  vs SKILL.md Rule 18 + `impl-json.md:30` (do NOT emit node-level position; emit `layout: {}`).
- Ruling: Rule 18 is correct. FE lifts `position/style/measured/width/height/zIndex` into the `layout`
  side-car on every write (`transformCaseInMemoryJsonToDiskJson.ts`) — authored positions are dead weight
  that only creates diff noise.
- Fix: delete the stale sentence at `planning.md:66` (points at a recipe that no longer exists).

### C4 — Interrupting cell for an SLA `start-task` response. **Render `—`.**
- Conflict: rules guide `:307` (`—`, "never Yes or No") vs lane guide `:134` (`No`) vs
  `sla-response-shapes.md:48` (`—`, "no interrupting cell at all").
- Ruling: `—`. A `start-task` response is a task-entry rule; interrupting semantics do not exist at task
  entry. 2-of-3 sources agree and the third gives no reason.
- Fix: lane guide `:134`.

### C5 — `wait-for-user` on a `Marks Stage Complete: Yes` row. **LEGAL.**
- Conflict: rules guide `:92` (allows) vs same file `:475` (omits from the Yes table) vs
  `stage-exit-conditions/impl-json.md:77` (canonical recipe IS `wait-for-user` + `marksStageComplete: true`)
  vs template `:173` (mandates the row in the `user-selected-stage` repair).
- Ruling: legal and canonical. Probes `p01` (`marksStageComplete: true`) and `p02` (`false`) both pass
  validate (as of 1.198.0-preview.102). FE compiles `wait-for-user` to a synthetic wait task; the flag
  independently controls whether that exit counts as completion — orthogonal knobs.
- Fix: rules guide `:475` table adds `wait-for-user` to the Yes row.

### C6 — `SlaRuleEntry` `id` / `displayName`. **Both required, always.**
- Conflict: `case-schema.md:435` ("id required *when referenced*") + `sla/impl-json.md:94` ("displayName
  optional") vs `case-schema.md:436` + `sla/planning.md:198` + rules guide `:265` (required).
- Ruling: both required on every entry. Probe `p03` (no displayName) → `[error] SLA name is missing`;
  probe `p04` (no id) → schema error `expected string, received undefined` (as of 1.198.0-preview.102;
  matches FE v26/v27 migrations that back-fill exactly these fields).
- Fix: `sla/impl-json.md:94`, `case-schema.md:435`.

### C7 — SLA units. **`min | h | d | w | m`, with `min` bounded 15–1000.**
- Conflict: template `:105` drops `min` from the case-level SLA cell (its own stage rows list it).
- Ruling: `min` is legal everywhere; bounds enforced. Probe `p05` (`count: 10, unit: "min"`) → stage SLA
  validation error (as of 1.198.0-preview.102).
- Fix: template `:105`.

### C8 — Variable `Type: jsonSchema`. **LEGAL; one coherent rule.**
- Conflict: rules guide `:393` ("never emit `json` or `jsonSchema`") vs same file `:126,:405` +
  `global-vars/*` + `case-sdd-examples.md:314` (documented, recommended, exemplified).
- Ruling: `jsonSchema` is valid — probe `p06` passes with a typed `body` (as of 1.198.0-preview.102).
  Single rule going forward: **`jsonSchema` (with `body`) for structured payloads whose fields are
  referenced downstream; `string` for opaque JSON blobs nothing dereferences.** `json` is not a type.
- Fix: rules guide `:393` (the blanket ban dies; the two-case rule lives once, in the shared variables
  semantics).

### C9 — Task display-name uniqueness on the design side. **Global across the case; design-time critical.**
- Conflict: build side (SKILL Rule 25, `case-schema.md:456`: whole-case pool, critical) vs planner parity
  table `:263` (no uniqueness at all) and `:262` (stage-label scope narrower than build's).
- Ruling: uniqueness is a whole-case constraint (FE `CASE_MGMT_STAGE_TASK_NAME_DUPLICATE`, critical). The
  planner authors every name, so the constraint binds at design time — the parity table was masking it.
- Fix: shared naming facts carry both scopes; planner finalization checks them.

### C10 — Tasks-file path. **`tasks/tasks.md`, adjacent to `sdd.md`.**
- Conflict: template Planner Handoff row `:32` (`<CASE_NAME_KEBAB>-tasks.md`) vs build behavior
  (SKILL.md:113 — always `tasks/tasks.md`).
- Ruling: the build side defines reality; the template row was aspirational. Standardize on
  `tasks/tasks.md`.
- Fix: template `:32`.

### C11 — END-marker contract. **Keep the contract; fix the two violations; lint it.**
- `brownfield.md` has no END marker (making Rule 24's hard-stop unsatisfiable for brownfield);
  rules guide `:1040` marker names a renamed file (`sdd-generation-rules.md`).
- Fix: add/correct markers; `lint-case-knowledge.py` enforces marker-matches-filename repo-wide.

### C12 — CLI error-code claims on the design side. **Codes don't surface; one check is real, one is not.**
- Probed (as of 1.198.0-preview.102, SDK validate path):
  - `required-tasks-completed` with no required task → **real error**, message
    `Stage exit rule '…' has no task(s) marked as required` (probe `p08`). No `CASE_MGMT_*` code in output.
  - `required-stages-completed` with no required stage → **real error**, message
    `Case rule '…' has no required stage(s) selected` (probes `p09`/`p10`).
  - Two secondary stages with **identical entry rules** → **passes validate** (probe `p07b`). The
    `CASE_MGMT_SECONDARY_STAGE_ENTRY_RULES_DUPLICATE` claim (rules guide `:898`) is not enforced on this
    path — it exists only in the CLI's legacy non-wired rule engine.
- Ruling: planner keeps the *design rationale* (identical interrupting entries are ambiguous routing) as a
  design-review flag, without the false "fails validate" teeth. Validate-behavior claims live only in the
  shared errors reference, message-quoted with version anchors, never bare `CASE_MGMT_*` codes.

### C13 — SDD write cadence. **In-memory until the Build/save answer; then write-early.**
- Conflict: lane guide `:92`/rules guide `:1011` (no file before consent) vs lane guide `:111` ("write
  while designing, not after").
- Ruling: both are right about different windows; the wording at `:111` is the bug. Single rule: the model
  lives in memory until the Case Review's Build (or save) answer; from that answer onward, write early and
  update incrementally. Reword `:111`.

---

## 2. Variables doctrine (new content ruling — probe-verified)

Directive: prefer task/trigger cross-references; avoid declared case variables.

| Producer | Reference form | Declaration needed | Evidence |
|---|---|---|---|
| Task output | `=vars.<outputId>` from any downstream input or condition (incl. interrupting secondary stage entries) | **None** — the full bare-mint output entry (`name, type, id, var, value, source, target, elementId`) self-declares | probes `p11b`, `p07c` pass; `p11` (partial entry: no `source`/`target`/`elementId`) fails `Variable 'vars.X' does not exist` |
| Trigger output | `=vars.<name>` | **One root `inputOutputs[]` companion** (`id`, `elementId: "root"`) — trigger-node outputs are never scanned by validation | probe `p12` (self-declared with `id`) fails; `p12b` (companion) passes; FE `ValidateCaseManagementFlowVariableUtils.ts` collects task/rule/root arrays only |
| Nobody (external/manual state) | `=vars.<name>` | Root `inputOutputs[]` declaration (the only remaining legitimate "case variable") | by construction |

Consequences for the restructure:
1. Shared variables semantics teach **direct task xref as the default wiring**; declared case variables are
   the exception (trigger companions + producerless state), not the norm.
2. The partial-entry failure mode (`p11`) becomes a build-side check: every emitted output entry carries
   the full bare-mint shape.
3. SDD minimal enhancement (see §3): task Inputs cells may reference an upstream output directly.

## 3. SDD template — minimal downstream-enhancing change

One change, scoped to §Task detail blocks: Inputs cells accept a **direct upstream reference**
`<Stage>.<Task>.<output-field>` (build resolves to `=vars.<outputId>`), and the Case Variables table is
re-scoped to trigger companions + producerless state only. No new sections, no new columns; existing SDDs
remain conformant (the old case-variable relay form still parses, it is just no longer taught).

---

## 4. Duplication → single home (D1–D16)

Homes: `KN` = `skills/uipath-planner/references/case-knowledge/` (shared, symlinked into maestro-case);
`PL` = planner-private `case-design/`; `MC` = maestro-case (existing paths, deduped in place).

| # | Rule (short) | Restatements | Single home |
|---|---|---|---|
| D1 | Secondary-stage semantics (interrupting lane, isRequired: false, exit types, excluded from required set) | 20 / 10 files | `KN/semantics/stages.md` |
| D2 | Global event modeled once on destination secondary stage | 10 | `KN/semantics/stages.md` |
| D3 | SLA response model (5 values; start-task placement; notify-only default) | 13 / 9 files | `KN/facts/sla.yaml` |
| D4 | Breach = `slaId` alone; at-risk = `slaId`+`escalationId`; never `any` | 12 | `KN/facts/sla.yaml` |
| D5 | WHEN ↔ Marks-Complete pairing | 12 | `KN/facts/pairing.yaml` |
| D6 | Case completion = root rule, ≥1 `marksCaseComplete: true` | 10 | `KN/facts/pairing.yaml` (+ prose in `KN/semantics/stages.md`) |
| D7 | Sequential/parallel task-set modelling (`runs-sequentially` incl. first task) | 14 / 9 files | `KN/semantics/sequencing.md` |
| D8 | `adhoc` = activation mode, task-entry only, never selected by required flow | 13 | `KN/semantics/sequencing.md` |
| D9 | "No omission — one T-entry per SDD declaration" (4 noun-swapped copies) | 6 | `MC references/planning.md` (once) |
| D10 | Outputs-row grammar (`->` vs `=`; target pre-exists; ≤1 row/target/task) | 9 | `KN/semantics/variables-io.md` |
| D11 | Variable Category semantics + sourceTriggers/sourceFields legality | ~5 full copies | `KN/semantics/variables-io.md` |
| D12 | Edges retired; reachability is condition-only | 11 | `KN/semantics/edges-retired.md` |
| D13 | Display-name rules (no `:`, scopes) | ~16 | `KN/facts/naming.yaml` |
| D14 | 9-type task enum + SDD-name↔discriminator asymmetry + never-author list | 8 | `KN/facts/types.yaml` |
| D15 | `registry-resolved.json` exact key set | 4 | `KN/contracts/resolution-ledger.md` |
| D16 | `conditionExpression` gates case state only (no `event` namespace) | 10 | `KN/semantics/expressions.md` |

## 5. File disposition map

| Current file | Lines | Disposition |
|---|---|---|
| planner `case-authoring-rules-guide.md` | 1040 | Dissolve → `PL/` activity files + `KN` facts/semantics; retire file (marker fixed first, C11) |
| planner `case-design-lane-guide.md` | 314 | Keep path; flow-only ≤180; content rules → `PL`/`KN` |
| planner `case-sdd-template.md` | 486 | Keep path; pure skeleton; embedded rules → citations; C7/C10 + §3 change |
| planner `case-sdd-examples.md` | 532 | Keep path; pure examples; rule restatements + 4th checklist deleted |
| maestro `SKILL.md` | 260 | Keep skeleton; 25 paragraph-rules → atomic gates; 4 nav surfaces → 1 router |
| maestro `planning.md` / `implementation.md` / `phased-execution.md` | 1133 | Keep paths; workflow-only; restatements → citations |
| maestro `case-schema.md` | 580 | Keep path; document-level shape only; rule prose → `KN` |
| maestro `case-commands.md`, `case-editing-operations.md`, `registry-discovery.md`, `brownfield.md`, connector refs, bindings refs | — | Keep paths; single-job shrink; C11 marker fix |
| maestro `sla-response-shapes.md` | 76 | **Retire** → `KN/facts/sla.yaml` (it declared itself single-source; now enforced) |
| maestro `plugins/**` (planning.md + impl-json.md per type) | 5706 | **Keep all paths** (user constraint); dedupe in place; C1/C2/C3/C6 fixes |

## 6. Probe appendix

Probe generator + 16 case variants archived in the PR description. Key rows:

| Probe | Setup | Result (uip 1.198.0-preview.102) |
|---|---|---|
| p00 | Baseline 2-stage v27 case | Valid |
| p01/p02 | `wait-for-user` exit, `marksStageComplete` true/false | Both valid |
| p03/p04 | SLA entry missing displayName / id | `SLA name is missing` / zod `expected string` |
| p05 | SLA `count:10, unit:min` | Stage SLA validation error |
| p06 | Variable `type: jsonSchema` + `body` | Valid |
| p07b | Two secondary stages, identical entry rules (vars declared) | **Valid** (dup check not enforced) |
| p08 | `required-tasks-completed`, no required task | `…has no task(s) marked as required` |
| p09/p10 | `required-stages-completed`, `isRequired` false / absent | Identical error — absent ≡ false |
| p11 / p11b | Task-output xref, partial vs full bare-mint entry | Partial fails (`Variable…does not exist`); full **valid** |
| p12 / p12b | Trigger output self-declared vs + root companion | Self-declared fails; companion **valid** |
| p13 | Manual trigger with explicit `serviceType: "None"` | Valid (absent also valid — p00). Emit `"None"` per the build plugin; tolerate absent on read |
| p14 | `wait-for-user` exit, no `user-selected-stage` anywhere | `Stage rule '<name>' has no possible stage options.` |
| p15 | `user-selected-stage` entry, no `wait-for-user` anywhere | `Stage entry rule '<name>' will never be met.` |

### Adversarial-review addendum (2026-08-17)

An independent review of the shared layer surfaced 15 findings; all fixed in place. Rulings it forced:
**R1** — manual-trigger emit shape: sources conflicted (planner guide: absent; maestro manual plugin:
always `"None"`); probes p00+p13 show both validate → emit `"None"`, read-tolerate absent (K-TYP-4).
**R2** — the wait-for-user↔user-selected-stage pairing IS validate-enforced (p14/p15, messages above) —
kept in K-PAIR-4 with quotes. Scoping fixes: case-completion rows are `exit-only` only (K-PAIR-3);
`stageType: "primary"` is never emitted (K-TYP-3); `<UNRESOLVED>` stays legal on identity/folder cells with
a paired review item (K-SDD-3); only `selected-stage-exited` lanes need an origin diverting exit (K-STG-5);
action-task SLA is not a `slaRules[]` entry (K-SLA-1); escalation-only SLA entries may omit count/unit
(K-SLA-2); `=js:` namespaces are `vars, response, bindings, iterator, metadata` — the vars/metadata
restriction is conditionExpression-only (K-EXPR-1/2; assignment ban sourced to FE
`ValidateCaseManagementNoAssignmentsUtils.ts`); binding-form list completed (literals, `=datafabric.*`,
`=orchestrator.JobAttachments`, `=response`/`=result`/`=Error`); `wait-for-timer` has no `tasks describe`
flag (K-TYP-1); both whole-value xref spellings sanctioned (K-VAR-1).

<!-- END: case-knowledge-ledger.md -->
