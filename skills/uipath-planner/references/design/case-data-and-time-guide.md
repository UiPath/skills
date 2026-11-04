# Case Management Product Guide — Data and Time

Layers 3 and 4 of a case design, the cross-layer § Layer closure, and the files, resources and review-item rules. Continues [case-product-guide.md](case-product-guide.md) (Layers 1–2); read both whole.

## Layer 3 — Data: variables & expressions

### Grammar — pick the shape from the need

Every data pattern is one row of this table. Mechanism sections below state the rules each cell obeys.

| What the case needs | Category | Declared in | Operator |
|---|---|---|---|
| Caller supplies a value at start | `In` | Case Variables row | — |
| Same, but the start is an event/timer (no caller) | `In` + `Default` | Case Variables row | — |
| A value returned to the caller | `Out` | Case Variables row + the producer's Outputs | `->` (or `Default` as fallback) |
| A trigger payload field readable as `=vars.X` | `Variable` + `sourceTriggers` + `sourceFields` | Case Variables row | — |
| The same slot filled by several triggers | `Variable`, CSV `sourceTriggers`, keyed `sourceFields` | Case Variables row | — |
| A task's response field captured into case state | any | the producer's Outputs row | `->` |
| A literal or computed value written to an existing variable | any | the producer's Outputs row | `=` |
| One consumer reading one upstream output | **no row** | reference the producer directly | — |
| A sub-field of structured state | `jsonSchema` (+ `body`) | Case Variables row, read `=vars.X.sub` | — |
| A document the caller pre-uploads | `In`, `Type: file` | Case Variables row | — |
| A document a connector fetches mid-case | `Variable`, `Type: file` | the producer's Outputs row | `->` |
| A stored document sent back out | — | task Inputs, whole-record bind | — |
| Only the link or document id, not the bytes | `string` (URL) / `jsonSchema` (metadata) | Case Variables row | — |

**Files.** A connector activity whose spec returns `type: "file"` extracts with `response -> <fileVar>`; the runtime writes the JobAttachment record `{ID, FullName, MimeType, Metadata}`, and downstream reads `=vars.<fileVar>` or a sub-field (`.FullName`). A file **input** binds the whole record — `=vars.<fileVar>`; a sub-field (`.ID`), a path, or a URL is rejected by the picker. A file `In` argument carries the caller pre-upload obligation.

**No `InOut`.** Declare separate `In` and `Out` names; copy with `<outVar> = =vars.<inVar>` on the first task, or produce the Out via `->`.

### Reference producers directly

A downstream input or condition that consumes one upstream task's output references the output directly — the emitting task's output entry is its own declaration, and no Case Variables row exists:

| Where the value is used | SDD spelling |
|---|---|
| The output IS the whole input value | `<- "Stage"."Task".out` — the bare `"<Stage>"."<Task>".<outputName>` cell form is equivalent |
| One term inside a larger `=js:` expression | `vars.$xref('Stage','Task','out')` |

The build resolves both spellings to the output's reference id. Direct references close lineage by ordering alone (producer task before consumer).

### When to declare a Case Variables row

Declare a row ONLY when one of these holds:

1. `In` / `Out` argument (the case boundary).
2. Trigger-payload extraction (below — the only way a trigger field becomes referenceable).
3. Case-level state read by a condition (`IF`) or by ≥ 2 consumers.
4. The value needs a rename or a custom `Default` / `Type` / `Description`.

A row that relays one task's output to one consumer is the relay anti-pattern — flagged as `rev_relay_var` (§ Layer closure, advisory lens). Declaring a row does not make the value readable earlier — see next.

### Gate on the producer, never on the variable it writes

A rule is evaluated **before** the extract of the task that triggered it. So a gate keyed on a task's completion that reads the case variable that task's Outputs row feeds sees the value from the previous pass — `null` on the first one. The branch silently never fires, the stage stalls, and nothing errors.

| Gate | `IF` reads | At gate time |
|---|---|---|
| `selected-tasks-completed("Decide")` + `=js:vars.decision === "reject"`, where `Decide` declares `Action -> decision` | the case variable `Decide` writes | ✗ stale / `null` |
| `selected-tasks-completed("Decide")` + `=js:vars.action === "reject"`, where `action` is `Decide`'s own output | the producing output | ✓ populated |

**Rule:** when a condition's WHEN names a task, its `IF` MUST read that task's own output. Keep the `->` extract whenever the value must persist (Case App, audit, a later stage reads it) — the extract is not what the gate reads. Applies wherever the WHEN names the producer: stage-exit `selected-tasks-completed`, task-entry `selected-tasks-completed`, and the `selected-stage-exited` lane entry paired with a diverting exit — that entry repeats the origin exit's guard, so it repeats the producer reference too. Guard pairs stay exact inverses of each other.

### Trigger payloads

Validation never reads trigger-node outputs. A trigger payload field is referenceable as `=vars.<name>` ONLY through a Case Variables `Variable` row carrying `sourceTriggers` (the trigger's T-number) + `sourceFields` (the payload path).

### Category semantics

| Category | Meaning | sourceTriggers | sourceFields | Closure |
|---|---|---|---|---|
| `In` | Caller-supplied at start; `Default`-initialized for event/timer triggers (no caller) | blank = primary trigger; a single `T<N>` selects another — never CSV | always empty (an In-arg selects a trigger, extracts nothing) | closed at case start |
| `Out` | Returned to the caller | forbidden | empty | needs a producer Outputs row or a `Default` |
| `Variable` | Internal state | single `T<N>`, or CSV for multi-trigger | bare path for one trigger; keyed `T<N>: <path>; T<M>: <path>` for CSV — one entry per listed T-number | producer or `Default` |

**Types:** `string`, `integer`, `float`, `double`, `boolean`, `date`, `datetime`, `jsonSchema`, `file`. `json` is not a type. Use `jsonSchema` (with `body`) when downstream picks sub-fields; `string` for opaque JSON blobs nothing dereferences. `file` is a JobAttachment record (§ Grammar — Files); the lane's confirmation surfaces the caller pre-upload obligation.

**Config-as-In:** runtime business rules (priority bands, thresholds, taxonomies) ride ONE `In` variable — `string` with a JSON `Default` for opaque rule-sets; `jsonSchema` + `body` when the picker must navigate sub-fields.

### Outputs rows

| Operator | Cell form | `Field` cell | Purpose |
|---|---|---|---|
| Extract | `-> caseVar` | Non-empty runtime path (`response.status`, `Action`, `Error.code`) — emitted as the source verbatim | Capture a response field into a declared variable |
| Set / compute / copy | `caseVar = <expr>` | `—` | Assign a literal, `=js:(...)`, or `=vars.X.Y` copy at task completion |

1. The target variable is already declared per the rules above; a `->` to a new name is valid only as the task's own self-declaring output.
2. One row per target per task; never mix `->` and `=` on the same target in one task.
3. Self-binding no-ops (`x = =vars.x`) are forbidden — they mask a missing producer. Computed self-references (`x = =js:(vars.x + 1)`) are fine.
4. Never alias a produced datum into an unrelated existing variable to close lineage — declare a dedicated row or confirm the reuse.

### Lineage closure

Every consumer of `vars.X` needs a producer that fires earlier — stage order first, then task order within the stage: a trigger extraction, a task Outputs row, an action button's `Maps To`, `Category: In`, or a non-empty `Default`. Checked at [§ Layer closure](#layer-closure--the-design-checklist) and by the validator.

### Expressions

- `=js:`-prefixed JavaScript. Namespaces available to `=js:` evaluation: `vars`, `response`, `bindings`, `iterator`, `metadata`. Assignment operators are forbidden in every case expression.
- A rule's condition expression gates CASE STATE only (`vars.*`, `metadata.*`) — there is no `event` namespace. In-rule extract-then-gate does not work at runtime (the gate evaluates before the extract writes): extract `response.field -> caseVar` on the connector rule and gate a DOWNSTREAM condition instead.
- Use strict equality (`===` / `!==`); write mutually exclusive branch guards as exact inverses so completion and divert rows cannot dual-fire.
- Thresholded policy ("Credit Analyst only over $5M") lands in an executable cell — owner/recipient, WHEN/IF, or a task input — with the numeral written out (`5000000`), actor and attribute on one line. Prose or a persona-table mention alone is a render failure.

### External names — schema fields are lookup keys

A schema field name is an **external lookup key**, not a label: the runtime matches it byte-for-byte, so `request_body`, `requestBody`, and `RequestBody` are three different fields and only one of them exists. This covers every place a design names a field it did not invent — `Input`/`Output Schema` cells, `response.<field>`, `=vars.<id>.<sub>`, `=trigger.<field>`, `<- "Stage"."Task".<out>`, and the Section 4 Output Fields list.

- **Carry the spelling, never derive it.** Copy the name from the user, the source document, or (at build time) the resource's own schema. Never re-case it, never convert between conventions, never make it match the case name or a neighbouring variable.
- **Never read names off a `--output json` envelope.** `case spec` and `registry search` PascalCase object **keys** recursively (`request_body` → `RequestBody`, `poText` → `PoText`); the true names are the **values** under `Outputs.ResponseFields[].Name`. Wiring against the keys binds to fields the resource does not have and fails only after build — Studio Web reports *"RequestBody not found, did you mean request_body"*. Canonical statement of the trap, build side: the `uipath-maestro-case` skill, its registry-discovery reference, § "Do NOT read I/O field names from `Resource.{Inputs,Outputs}`".
- **Unsourced casing is `<UNRESOLVED>`, not a guess.** Schema discovery is build work (§ Resources and Identities) — so when a design needs a field whose exact spelling nothing in the conversation supplies, render the field as `<UNRESOLVED>` and pair it with a review item. A plausible-looking guess is the one outcome that cannot be caught downstream.

### Binding-cell forms (task Inputs)

| Form | Meaning |
|---|---|
| `<literal>` | Plain string / number / boolean |
| `=vars.<id>` / `=vars.<id>.<sub>` | Declared variable or upstream output; dot-path into structured values |
| `<- "Stage"."Task".out` / `vars.$xref('Stage','Task','out')` | Direct output references (above) |
| `=bindings.<id>` | Registered resource (app, process, connection) |
| `=metadata.<key>` | Case metadata |
| `=metadata.ExternalId` | The platform-minted case identity — the canonical `caseId` binding; NOT a task output, never a `->` extraction |
| `=trigger.<field>` | Trigger payload field |
| `=js:<expr>` | Inline JavaScript (required when operators are involved) |
| `=jsonString:<json>` | JSON-as-string — connector `Operation Configuration` carry-through only |
| `=datafabric.<path>` | Data Fabric reference |
| `=orchestrator.JobAttachments` | File slot |
| `=response` / `=result` / `=Error` | Conventional response handles |

Bare field-name lists (`**Inputs:** a, b, c`) are forbidden — use the table with one form per cell.

---

## Layer 4 — Time: SLAs & escalations

> **Canonical + twin.** This layer owns the case SLA response model. The build skill `uipath-maestro-case` carries an operational twin of it (its SLA response-shapes reference), because skills here must work with siblings absent and a brownfield edit runs with no SDD and no planner in the loop. Twin, not a second source of truth: a change to the model lands here first, then there, in the same PR — parity is pinned by `tests/tasks/uipath-planner/_shared/test_case_twin_parity.py`.

### Where SLAs live

| Surface | Location | Notes |
|---|---|---|
| Case | root SLA rules | |
| Stage | stage SLA rules | Secondary stages included |
| `action` task | The task's own timer/SLA fields | NOT an SLA-rules entry. Add case behavior only when the missed task must change the case graph |

No SLA cells on any other task type.

### SLA rule entries

Conditional overrides first (priority order), then a trailing default entry with expression `=js:true`; the first truthy expression wins.

1. Every entry requires an id AND a non-empty target-unique display name without `:` — validate rejects a missing name (`SLA name is missing`) and a missing id (schema error).
2. `count`/`unit` may be omitted only as a pair, on a bare escalation-only entry. Units: `min | h | d | w | m`; minute counts bounded 15–1000.
3. Non-default entries require a non-empty expression.
4. Escalations: id + non-empty element-unique display name + ≥ 1 recipient (scope `User` / `UserGroup`); an at-risk percentage is required exactly when the trigger type is `at-risk`.

### Breached vs at-risk — how status is selected

| Status | The `sla-status-change` rule references | Requires |
|---|---|---|
| Breached | The SLA alone — an absent escalation reference IS the persisted breached shape | Nothing else. Never "complete" a breach rule with an escalation: that converts it to at-risk |
| At-risk | The SLA + one concrete at-risk escalation declared on that same SLA | That escalation must exist on that SLA |

Never the designer's `any` escalation sentinel. Borrowed and dangling references fail validate: `The escalation referenced by rule … no longer exists` / `The SLA referenced by rule … no longer exists`.

### Choosing the response

Pick from the source's words — WHERE the work lives, never whether it interrupts. A named task never justifies a new stage.

| Response | Source says | What you author | Interrupting cell |
|---|---|---|---|
| `notify-only` | notify / alert / page someone, nothing more | An escalation on the target's SLA rules — no stage, task, or condition | `n/a` |
| `start-task` | Follow-up work inside the SAME breached stage ("as part of the review", a named task for a manager or peer) | One task in the breached stage carrying `sla-status-change` as its OWN task-entry row, against that stage's (or the case's) SLA | `—` — a task entry interrupts nothing; never `Yes`/`No` |
| `enter-stage` | A separate lane owns it ("hand it to", "escalate into <Lane>") | A separate stage carrying the `sla-status-change` entry row | `Yes` when the source says **interrupt**, **global interrupt**, **take over**, **stop** or **pause** the work, or when the lane must be cleared **before the case or stage can close**; `No` ONLY for parallel oversight that leaves the work running |
| `exit-stage` | The breached stage should end or route away | A stage-exit row | Per exit semantics |
| `exit-case` | The case should close, cancel, or reach an alternate terminal | A case-exit row | Per exit semantics |

Never author `start-task` as a stage-entry row on the breached stage: it validates, but stage re-entry re-runs every task whose `Run Only Once` is `No` — a breach meant to add one manager check silently re-runs the whole stage.

Read the Interrupting cell off the SOURCE's words, exactly like the Response cell — it is not a judgement call you make after choosing the lane. A source that says "globally interrupt into <Lane>" has already said `Yes`; treating it as parallel oversight contradicts the sentence you are modelling. A case-scope breach that must be resolved before the case can close is a takeover, never oversight.

### Defaults when the source is silent

- SLA exists only where the source mentions timing, read literally ("about a day" → 1 day). No timing → `—`, no SLA rule. Scope, status, and response are chosen separately (§ Choosing the response).
- Every (scope, SLA) authors BOTH statuses, always. The rule is per status, not per SLA: a stated
  response for one status never removes the other status's row, and a status the source is silent on is
  `notify-only` with Target and Interrupting `—` — an omitted row is an unauthored response, not a way to
  write "nothing happens". Never invent a stage, task, or routing change.
- At-risk threshold: SLA ≤ 3 days → 75%; 3–10 days → 70%; > 10 days → 80%.
- Recipients: at-risk → the owner persona's user group; breached → the leadership tier (Compliance for regulation-driven cases). Record substituted defaults with provenance.

### SLA reference legality

| Shape | Result |
|---|---|
| Breach entry on a separate stage, either interrupting value | valid |
| Breach / at-risk on a task's entry conditions (stage or case SLA) | valid |
| At-risk with a same-SLA escalation | valid |
| At-risk borrowing another SLA's escalation | invalid |
| `any` escalation reference | invalid |
| Dangling SLA reference | invalid |
| Task with empty or absent entry conditions | valid — and the task never starts |

---

### Naming rules

<!-- named by case-review-and-conformance-guide.md § SDD Conformance Checklist — do not rename this heading or reshape this table/fence; the checklist sends authors here by heading name -->

Safe display characters for stage labels, task display names, and condition/SLA/escalation titles:

```
^[A-Za-z0-9 _-]+$
```

**`:` is the hard ban** — case-execution events are colon-delimited, so a colon in a name breaks routing. It is the one character the conformance checklist (item 11) gates on, in every mode, including names read from a draft: surface and ask, never silently keep or repair.

Everything else in that set is a **minting preference, not a platform limit** — the auditor reports it as an advisory that does not gate. Apply it to names YOU mint: replace disallowed runs with one space, collapse, trim; on an empty result or a collision add a safe qualifier and disclose. **A name the user, the source document, or a draft supplied is kept verbatim, punctuation included** (`Credit & Document Verification` stays). Rewriting one to fit the charset is the domain-fidelity defect the lane's authoring policy forbids, and it costs repair rounds for a display preference.

**Default:** case name = PascalCase from the domain noun; case ID prefix = a 2–4 letter mechanical derivation of it.

| Name | Unique across |
|---|---|
| Task display name | The whole case — every stage, one pool |
| Stage label | All node labels; never the reserved Case Manager stage label |
| SLA rule title | Its target (root or that stage) |
| Escalation title | All SLAs on the element |

Comparison exact — case-sensitive, untrimmed. Never normalize external lookup names (Action App titles, process/connector names, and schema field names — all matching keys; § External names); keep a separate safe display name. Never silently clamp a numeric violation (e.g. out-of-range SLA duration) — surface and ask.

---

## Layer closure — the design checklist

ONE checklist. Settle every item before the Phase 2 Step 5 review and re-walk it before the write — a run with no review (autonomous, a draft request) still walks it. Fix failures silently: they are authoring defects, not user decisions; an unfixable one is a Review Flags row. Mechanical shape checks are [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § SDD Conformance Checklist's, walked against the written file.

**Blocking — the design is unbuildable or unreviewable until fixed:**

1. **Other-path trigger source** — every modeled path's entry shape matches its trigger source ([case-product-guide.md](case-product-guide.md) § Secondary-lane entry shapes); interrupting flags set on the stage AND on every entry row; terminal `exit-only` vs returning `return-to-origin` chosen; a warning-only escalation stays a notification; an SLA response needing case work carries ONE `sla-status-change` entry with declared target + titles; never duplicate a global-event entry or exit across primary stages.
2. **Reachability walk** — every stage reachable from a trigger or SLA source: walk entries forward, and walk every conditional entry's FALSE branch too. A stage that does not enter never completes, so a downstream stage keying solely off its completion is unreachable on that branch — when a rule SKIPS a stage and the case continues, the bypass is an explicit extra entry row on the downstream stage (its own condition, negated); when the rule ENDS the case, that branch needs a terminal lane. Never write that a skipped stage "auto-completes" or "counts as complete" — that is an assertion, not a route, and the path stays dead. Every primary stage's completion consumed downstream, referenced by another entry, or feeding a lane; ≥ 1 primary stage `Required: Yes`; `adhoc` never a stage entry. Decision-reachable lanes and duplicate-entry ambiguity per § Secondary-lane entry shapes.
3. **Entry producer** — every non-start entry names its concrete producer (source stage/task, connector event, paired `wait-for-user` exit, declared SLA reference); at-risk rows name the escalation, breach rows the SLA alone.
4. **Decision-routing closure** — every decision outcome routes somewhere: no dead-end status values; an outcome targeting a lane keys that lane's entry; every routing button's variable+value is consumed downstream or a declared terminal; a fully-orphaned decision variable on a decision task is blocking.
5. **Gate reads the producer** — no condition whose WHEN names a task reads a case variable that task writes (§ Gate on the producer).
6. **Data closure** — every configure/decide output lands in a variable or direct reference; every send/connector/agent required input maps to variables/literals/upstream outputs as far as knowable without schemas (rest resolves at build); thresholded policy in executable cells (§ Expressions).
7. **Task-surface classification** — human-performed required work `action`, optional user-launched `adhoc`; no compliance trigger phrase paired with a non-`action` type without explicit user reconciliation ([case-product-guide.md](case-product-guide.md) § Task-type override priority).
8. **Required-task presence** — a `required-tasks-completed` completion over a stage with zero `Required: Yes` tasks fails validate: `Stage exit rule '<name>' has no task(s) marked as required`; offer marking the terminal task required.
9. **Resources** — intended names concrete everywhere (`Resolved Resource`, Action App title, `Child Case` — never `<UNRESOLVED>`); identities per § Resources and Identities, unresolved only with a paired high review item; when a live contract is in memory: required inputs bound, extract fields exist verbatim, declared action-app fields ⊆ app schema.
10. **Durable rationale** — every stage (kind + routing), task (type + activation, incl. why sequential/parallel/shared-set), and configured SLA (thresholds, recipients, response) carries Design Rationale; provenance on every non-user-stated value ([case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Presenting the Case Design, Decisions I Made).
11. **Alt dispositions & obligations** — ≥ 1 secondary stage ⟹ non-completing case-exit rows exist (or an open high item); `In` + `file` row ⟹ the Caller-obligation block; SLA Response Map closes both ways with agreeing Interrupting cells (template § SLA Response Map); re-entry loops classified ([case-product-guide.md](case-product-guide.md) § Sequencing & activation).
12. **Domain fidelity** — verbatim-captured entities render exactly; drift → re-edit with the phrase pre-filled.

**Advisory — architect's lens** (emit medium review items; HIGH variants gate like any high item):

| Check | Trigger | Review item |
|---|---|---|
| Single-recipient bottleneck | `action` recipient is one `User:`/`Email:` AND the stage runs on every case AND no documented volume limit | `rev_bottleneck_<task>`: confirm volume or use UserGroup/Role |
| No escalation on SLA | Stage SLA set, escalation absent | `rev_escalation_<stage>`: no one is paged on breach |
| Escalation loops to the breacher | Escalation recipient = the stage's primary recipient | `rev_escalation_loop_<stage>`: pick a tier-up recipient |
| Sync child case in the critical path | `Wait for Completion: Yes` + parent SLA + no timeout cover | `rev_childcase_<task>`: consider async + completion event, or an exception path |
| All-human stage | 100% `action` tasks, > 2 tasks | `rev_human_only_<stage>`: consider agent/process pre-screening |
| No happy path on the first stage | Only `No` exits, no `required-tasks-completed` completion | `rev_no_happy_path_<stage>` |
| Decision outcome unread | Decision task writes a variable no downstream rule reads | `rev_orphan_decision_<task>`: consume it or drop decision status |
| Connector failure uncovered | Connector task in a primary stage, no failure lane (HIGH when ≥ 2 connector tasks share a critical path, zero cover) | `rev_no_failure_path_<task>` |
| Substitute app (HIGH) | One Action App on ≥ 2 tasks WITHOUT a distinct `actionType` each, or declared fields outside the app schema (code-switched reuse exempt) | `rev_substitute_app_<app>`: code-switch or deploy task-specific apps |
| Parallel bottleneck fan-in | ≥ 2 bottleneck stages fan into one downstream stage | `rev_multi_bottleneck_<stages>` |
| Relay variable | A §1.5 `Variable` with one producing task output and one consuming binding (§ When to declare) | `rev_relay_var_<name>`: reference the output directly, drop the row |
| Aliased output | An Outputs `->` row whose `Field` leaf has no matching §1.5 row and lands in a differently-named variable | `rev_aliased_output_<task>`: declare a dedicated variable or confirm the reuse |


## Files and Attachments

When the source mentions `file`, `attachment`, `PDF`, `upload`, `evidence` or `receipt` as an artifact (not a domain noun), pick the matching pattern and record the decision — ask only when the source's own words point at two patterns at once:

| Pattern | Indicator phrases | SDD shape |
|---|---|---|
| Caller pre-uploads at case start | "caller submits a PDF", "uploaded with the request" | `Category: In`, `Type: file`; caller obligation surfaces in the confirmation. |
| Connector downloads mid-case | "fetch the attachment from email", "pull from Drive / S3" | `Category: Variable`, `Type: file` from a task Outputs `->` row. |
| Stores URL/metadata, not bytes | "we just store the link", "we keep the document ID" | `Type: string` (URL) or `Type: jsonSchema` (metadata). NOT `file`. |

## Resources and Identities

Design resolves identities only: a resource the design names is looked up in the Level 0 estate sweep ([product-selection-guide.md](../shared/product-selection-guide.md) § Estate sweep); one confident match is adopted with its exact folder, anything ambiguous or missing renders `<UNRESOLVED>` with a paired review item, and the build resolves it. Schema discovery (`tasks describe`, `case spec`), project scaffolding and create-on-missing are build work — a needed field name nothing supplied is `<UNRESOLVED>`, never a spec call and never a key read off a `--output json` envelope (those are PascalCased: § External names). Registry data is evidence, not requirements: never add or rename business work to match tenant inventory. Deep runtime metadata (agent prompts, package versions, endpoints) stays out of the SDD — name, folder, identity and sub-type only.

## Review Items

A field the design cannot fully resolve but the build needs is a **review item**: an `[SME REVIEW]` row in the SDD's `Action Required — SME Review Items` table, its id (`rev_<slug>`) in the Item cell and its next step in Question. Severity decides `Blocking` and the review:

| Severity | Meaning | `Blocking` | Examples |
|---|---|---|---|
| **high** | The build cannot complete until resolved | `no` — default `resolve at build`; it labels the handed-over build option `Build despite N flagged items` | Missing `connectionId` / `actionAppId` / deployed runnable; unbound required input; phantom extract field; open variable lineage; missing trigger config; unreconciled compliance override |
| **medium** | The build defaults it | `no` | Missing escalation recipient (default the owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | `no` | Missing case or secondary-stage description |

Never downgrade a severity to pass a gate — it moves only when the issue resolves.
