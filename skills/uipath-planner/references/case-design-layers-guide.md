# Case Design in Layers

Everything a case design must respect about the Case Management platform, ordered the way a design is actually made. A case is a versioned JSON document of **stages**, **tasks**, and **conditions** that compiles into a deterministic rule plan evaluated on every case event. Identity is by **display name** at runtime — names are load-bearing, not labels (§ Naming rules below). This skill designs the document (`sdd.md`); the build skill (`uipath-maestro-case`) emits and validates `caseplan.json` from it.

Design in four layers, each settled before the next refines it:

1. **Skeleton** — trigger(s), stages, tasks + types. *What work exists and who/what performs it.*
2. **Gates** — entry/exit conditions, sequencing. *When each piece activates, completes, routes.*
3. **Data** — variables, outputs, expressions. *What each piece reads and writes.*
4. **Time** — SLAs and escalations. *What happens when work runs late.*

Close with [§ Layer closure](#layer-closure--the-design-checklist) — the single cross-layer checklist run at Sketch and re-walked at Confirm.

**Best assumption is the design mode.** Every open field takes the **Default** stated in its layer — decided and disclosed, never asked. An optional field the source never touches renders `—`. Every non-verbatim value carries a Design Rationale plus a decision line in the confirmation.

---

## Layer 1 — Skeleton: trigger, stages, tasks

Reason the shape from the process — never reach for the template first. Build in order: **stages → tasks → types → sweep other paths**.

### Derivation questions

| Concept | Ask of the user's process |
|---|---|
| Stage | *What is the case working toward right now, and what makes that done?* One stage per named milestone. A stage that marks the case complete is main-flow (`Required: Yes`). |
| Secondary stage | *Does this work belong at one fixed point (regular stage), or could it happen at several points / only on a condition?* "Handle rejected application", "escalate on breach", "rework loop" → secondary ([§ Secondary stages](#secondary-stages)). An optional one-off inside the current stage stays an `adhoc` task, not a lane. |
| Task | *Who or what performs this, and how?* One verb in the description ≈ one task. The "how" answer is the task type. |
| Persona | *Who acts?* Named roles verbatim, exact casing. **Default:** none named → one `Process Owner`. |
| "Manual" work | *Does it start a case, or happen inside one?* Starts a case → Manual trigger; optional worker-launched step → `adhoc` + `Required: No`; worker-chosen exception lane → secondary stage with `user-selected-stage`. |

### Triggers

≥ 1 per case; one primary trigger, more allowed. SDD author tokens (on-disk enum mapping is build-side):

| Source says | Author token |
|---|---|
| External system, portal, form, inbound event, or record-created start | `Intsvc.EventTrigger` — a tenant object start stays an event trigger even when provisioning is missing (unresolved detail becomes a placeholder later; never downgrade to Manual) |
| Schedule / recurring | `Intsvc.TimerTrigger` |
| Otherwise (user or API call) | `Manual` |

### Task types

<!-- parsed at runtime by scripts/audit_sdd.py — do not rename this heading or reshape this table/fence; a rename disarms the checks and audit_sdd.py will report "model checks disarmed" -->

The enum is closed — exactly these nine literals, used verbatim as the SDD `Type:` value. The `type` says **how the work gets done**, not what it is about — read the verb + the actor:

| Type | Pick when the work is… |
|---|---|
| `process` | invoking a **deployed orchestration process** that already packages the automation |
| `action` | a **person** must do, decide, approve, review, or sign off — in a form |
| `agent` | an **AI agent** reasons over unstructured input: classify, extract, summarize, draft, score |
| `rpa` | deterministic **UI / desktop** automation of a legacy app with no API |
| `api-workflow` | calling a **coded / API workflow** directly (HTTP, serverless logic) |
| `case-management` | the step **launches / coordinates a child case** |
| `execute-connector-activity` | one **operation on an Integration Service connector** against a SaaS system (push) |
| `wait-for-connector` | the case **pauses until an external system calls back** (pull) |
| `wait-for-timer` | the case **pauses for a duration or until a datetime** |

Never author: `external-agent`, `external-workflow`, `document-extraction`, `flow-process` (unsupported), and `wait-for-event` / `connector-activity` / `connector-trigger` (not schema literals). Externally-hosted AI agents (CrewAI, Einstein, Databricks, …) model as `api-workflow`, or `execute-connector-activity` when a tenant connector exists.

**Tie-breakers:** SaaS integration with a tenant connector → `execute-connector-activity` over `api-workflow`. Ambiguous "approve / review / decide" verbs: named human role or implied judgment → `action`; framed as automated/AI → `agent`. **Default when truly even: `action`** — it keeps a human in the loop and one correction flips it. Decide, disclose, never ask. A compliance trigger phrase forces `action` (below).

**Activation is a separate axis.** How a task starts (sequential, event-triggered, manually triggered, stage-started) maps to entry rules (Layer 2) and never changes the `type`.

### Task-type override priority

Apply in order:

1. **User decision pinned to a type** — honor unless schema-invalid or conflicting with tier 2.
2. **Regulatory constraint requiring human sign-off** — the task MUST be `action`. Trigger phrases: "only a licensed X may decide / sign off / certify / approve"; "regulation requires human review"; "ECOA adverse-action notice" / "FCRA adverse action"; "NCQA UM 3 adverse determination"; "HIPAA-protected approval"; "SOC 2 attestation"; any `<role>-licensed` / `<role>-credentialed` gate; "fiduciary review", "legal sign-off", "auditor review". If the user proposes a non-`action` type AND any phrase appears anywhere in the conversation → ask to confirm; never silently accept. Ask phrasing: name the regulation and propose `action` with the LLM/agent work bound to the action's form and recipient. Example: ECOA adverse-action notice with user-stated `agent` → `action` (Compliance Officer recipient; LLM-drafted body bound to the action's form).
3. **Tenant evidence** — the registry cache resolves a deployed Action App / process / agent / api-workflow / RPA that fits → prefer that resource's type and surface the match.
4. **Connector availability** — an Integration Service connector matches → `execute-connector-activity` over `api-workflow`.
5. **Verb signal** — fall through to the § Task types tie-breakers.
6. **Fallback** — keep the user's stated value if any; otherwise a placeholder plus a `high` review item ([case-design-lane-guide.md § Review items](case-design-lane-guide.md#review-items)).

**Compliance-trigger scan.** Scan the whole conversation for tier-2 phrases BEFORE recording any non-`action` type. A phrase surfacing after a non-`action` type was provisionally recorded → re-ask before continuing. No tier-2 phrase in the transcript (e.g. jurisdiction-dependent underwriting) → keep the stated type, disclose the compliance caveat as a decision line.

### Secondary stages

A secondary stage is an **interrupting exception lane**: `Stage Kind: secondary`, `Required: No`, excluded from `required-stages-completed`, with `Interrupting: Yes` on the stage AND on every entry row. Model errors, escalations, rejections, rework, and cancellations here — never as inline primary stages. Optional one-off work inside the current stage stays an `adhoc` task, not a lane.

**One carve-out:** an `sla-status-change` entry whose response is parallel oversight — the breached work keeps running; nothing is paused, taken over, or rerouted — reads `Interrupting: No` on the stage and on that entry row. The lane stays secondary and `Required: No`, and it completes `exit-only` (never `return-to-origin`).

**Exits by intent:**

| Lane intent | Completion row |
|---|---|
| Returning / rework | `return-to-origin` + `Marks Stage Complete: Yes` + `required-tasks-completed` |

**Hard rule — a returning lane's exit selector.** `return-to-origin` pairs ONLY with `required-tasks-completed` or `wait-for-connector`, always with `Marks Stage Complete: Yes`. `selected-tasks-completed(...)` on a `return-to-origin` exit is illegal and is rejected by the mechanical gate: a selector-scoped exit cannot express "this lane finished, resume the origin". If you want the lane to end after one specific task, that task is the lane's required task — declare it `required-tasks-completed`, not `selected-`.
| Terminal (Rejected / Withdrawn / Cancelled) | `exit-only` + `Yes`, plus a root case-exit row with `Marks Case Complete: No` |

### Other-path sweep — mandatory before confirmation

Look beyond the primary flow. Check the source for each scenario; pick the smallest faithful model:

| Scenario | Candidate models |
|---|---|
| Rework / needs-info loop | Returning secondary lane (`return-to-origin`) |
| Rejection, withdrawal, cancellation | Terminal secondary lane + non-completing case exit |
| SLA escalation | Response per [Layer 4](#layer-4--time-slas--escalations) — notification only unless the source creates work |
| External-system failure | Secondary lane on the failure event, or an advisory review item |
| Manual override / worker-launched side work | `adhoc` task (`Required: No`) or `user-selected-stage` lane |
| Terminal outcomes different from success | Non-completing case-exit rows; XOR terminals ([Layer 2](#xor-terminal-stages)) |

Clear source signal → model it by best assumption and disclose in **Other Paths Considered**. No signal at all → spend the one bounded question before the confirmation; "primary flow only" is then a recorded decision, never an omission.

---

## Layer 2 — Gates: entry, exit, sequencing

The case, each stage, and each task move through gates driven by **rules** in disjunctive normal form: the outer rule array is OR, each inner array is AND. **Edges are retired** — flow is condition-driven: each destination stage declares its own entries, and the case starts at the first stage's `case-entered` entry. Reachability is therefore condition-only — a missing or malformed entry condition is the only thing that can orphan a stage.

### Lifecycle gates

<!-- parsed at runtime by scripts/audit_sdd.py — do not rename this heading or reshape this table/fence; a rename disarms the checks and audit_sdd.py will report "model checks disarmed" -->

| Gate | Marks complete | Legal WHEN rules |
|---|---|---|
| Stage entry | — | `case-entered` (first stage only), `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`, `user-selected-stage`, `sla-status-change` |
| Stage completion | Yes | `required-tasks-completed`, `wait-for-connector` |
| Stage exit | No | `selected-tasks-completed`, `wait-for-connector` |
| Task entry | — | `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`, `adhoc`, `runs-sequentially` |
| Case completion | Yes | `required-stages-completed`, `wait-for-connector` |
| Case exit | No | `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector` |

1. Tasks have NO exit or completion conditions — a task completes when its own work finishes; downstream gates key off `required-tasks-completed` / `selected-tasks-completed`.
2. `Marks Complete: Yes` pairs only with `required-*` rules (or `wait-for-connector`). A `Yes` + `selected-*` pair is a schema error.
3. `required-*` rules are vacuous without an explicit `isRequired: true` member. Required status is explicit end-to-end — the SDD declares it per stage and task, and emission writes it verbatim. An absent flag equals `false` at the validator: `Case rule '<name>' has no required stage(s) selected` / `Stage exit rule '<name>' has no task(s) marked as required`.
4. **Case completion is a root rule.** At least one case-exit row carries `Marks Case Complete: Yes` (normally `required-stages-completed`). A stage completing never closes the case by itself; alternate outcomes (Rejected, Withdrawn, Cancelled) are case-exit rows with `Marks Case Complete: No`. **Default:** the last primary stage completing closes the case unless the source describes another close-out.
5. **A gate sees case state as of its own event.** The extract of the task that fired the gate has not run yet, so an `IF` that reads a case variable that task writes is stale — read the producing output instead ([Layer 3 § Gate on the producer](#gate-on-the-producer-never-on-the-variable-it-writes)).
6. **Evaluation precedence: case exit/completion → stage exit → stage completion → stage entry.** Two consequences: a stage entry identical to a case-exit row (same rule, selector, IF) leaves the stage permanently unreachable — differentiate the guards; an unguarded stage exit (`No`, empty IF) sharing its WHEN with a guarded completion (`Yes` + IF) always fires first and the stage never completes — the exit carries the completion's inverse IF. Both validator-enforced.

### Exit types

| Row kind | Legal exit types |
|---|---|
| Stage completion (Yes) | `exit-only`, `return-to-origin`, `wait-for-user` |
| Stage exit (No) | `exit-only`, `wait-for-user` |
| Case completion (Yes) | `exit-only` |
| Case exit (No) | `exit-only`, `wait-for-user` |

- `wait-for-user` + `Marks Stage Complete: Yes` is legal and canonical for user-routed completion.
- `return-to-origin` is completion-only, and its lane is always interrupting.

**`wait-for-user` ↔ `user-selected-stage` pairing.** Validate enforces the pair both ways: a `wait-for-user` exit with no `user-selected-stage` entry anywhere fails with `Stage rule '<name>' has no possible stage options.`; a `user-selected-stage` entry with no `wait-for-user` exit fails with `Stage entry rule '<name>' will never be met.`. `user-selected-stage` is picker exposure — a user choosing the next stage — never deterministic routing. Deterministic rejection, approval, send-back, and SLA routing use decision facts plus guarded entries instead.

### Secondary-lane entry shapes

Entry shape follows the lane's trigger source:

| Lane trigger | Entry shape |
|---|---|
| A person launches it | `user-selected-stage`, paired with an upstream `wait-for-user` exit |
| External / global event | ONE `wait-for-connector` entry on the destination lane — never duplicated per origin stage |
| SLA response | ONE `sla-status-change` entry ([Layer 4](#layer-4--time-slas--escalations)) |
| Decision / signal divert | The origin stage carries a gated diverting exit — `Marks Stage Complete: No`, WHEN `selected-tasks-completed("<decider task>")`, `IF` on the signal, exit target → the lane — and the origin's completion exit carries the exact inverse `IF`. The lane enters via `selected-stage-exited("<origin>")` + the same `IF`. |

Omitting the diverting exit makes a decision path dual-fire (ungated completion → the next stage AND the lane both enter) or deadlock (gated completion with no alternative exit). Only a `selected-stage-exited` lane entry needs a diverting exit; a `selected-stage-completed("<origin>")` + `IF` lane keys off the origin's normal completion — guard only.

Two lanes with identical entry rules (same rule, selectors, and expression) are ambiguous routing — give each a distinct selector or guard. This is a design requirement; validate does not reject the duplicate.

### Sequencing & activation

Task-entry mode is exclusive — one mode, one rule, never combined:

| Described timing | Activation Mode token | Entry rule |
|---|---|---|
| Ordered run (`then`, `after`, `before`, a dependency) | `sequential` | One `runs-sequentially` row — on EVERY task in the run, including the first |
| Independent, starts with the stage | `parallel` | `current-stage-entered` |
| Independent siblings after one predecessor | `parallel-after-predecessor` | `runs-sequentially`; the siblings share the next task set |
| External callback | `event-triggered` | `wait-for-connector` (or `sla-status-change` for an SLA-started task) |
| User launches it from the Case App | `adhoc` | One `adhoc` row + `Required: No` |
| Fan-in, convergence, conditional gate | `fan-in` / `conditional-gate` | `selected-tasks-completed("<tasks>")` |

- Structure mirrors the mode in the stage's task sets: a strict chain is consecutive single-task sets; parallel-after-predecessor siblings share one set. Never duplicate `selected-tasks-completed("<previous>")` to express simple order.
- `selected-tasks-completed` selects only non-`adhoc` tasks in the SAME stage.
- A task with no entry condition never starts — validate accepts the omission silently.
- Race (confirmation vs timeout/cancel/withdrawal) → listener + clock armed while the obligation is pending; downstream work gated on the winning fact.
- Conditional-branch stages (mutually-exclusive tasks, one per outcome, all `Required: No`): add ONE required convergence task whose entry is an OR over every branch — one `selected-tasks-completed("<branch>")` row each — plus a `current-stage-entered` + inverse-guard row for the no-branch path. `required-tasks-completed` then resolves on every path.

**Producer rule:** every non-start stage/task entry names its concrete producer before the confirmation — a source stage exit/completion, a task completion, a connector event, a paired `wait-for-user` exit, or a declared SLA reference. A schema-valid rule without a producer is a design defect.

**Re-entry (`return-to-origin` loops)** — classify before setting `Run Only Once`:

| Loop kind | Signal | Handling |
|---|---|---|
| New attempt | corrected, resubmitted, retry, appeal | Producers rerunnable (`Run Only Once: No`); reset or attempt-scope the live routing variables |
| Re-evaluate an existing fact | the lane changes a fact and the origin re-reads it | `Run Only Once: Yes` on preserved producers; state which rule re-reads the fact |
| Optional repeat | the user may repeat work nothing depends on | `adhoc`, not required |

### XOR terminal stages

Mutually-exclusive happy-path terminals ("Funding on approve, Adverse Action Notice on decline"): case completion accepts only `required-stages-completed`, so the XOR lives at stage entry. Two sanctioned patterns — when detected at sketch time (multiple terminal candidates plus an earlier branching decision), surface both in one question before drafting rows:

**Gated entry + required terminals (default — works on every tenant):**

1. Both terminal stages `Required for case completion: Yes`.
2. Each terminal's entry: `selected-stage-completed("<DecisionStage>")` + its lane guard `IF` (`=js:vars.decision === "Approve"` / `!== "Approve"` — exact inverses).
3. Each terminal completes normally: `required-tasks-completed`, `Marks Stage Complete: Yes`.
4. Runtime stage-skip: entry `IF` is evaluated at activation; a terminal whose `IF` is false auto-completes with status `Skipped` and still counts toward `required-stages-completed` closure.
5. Case exit: ONE row, `required-stages-completed`, `Marks Case Complete: Yes`, `IF: —`.

**Connector-event close** (only when both terminals genuinely emit a shared case-done event): terminals `Required: No`; entries as above; each terminal's last task emits the shared event; the case exit is ONE `wait-for-connector` row keyed on it.

---

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
- **Unsourced casing is `<UNRESOLVED>`, not a guess.** Schema discovery is build work (§ lane guide § Tenant grounding) — so when a design needs a field whose exact spelling nothing in the conversation supplies, render the field as `<UNRESOLVED>` and pair it with a review item. A plausible-looking guess is the one outcome that cannot be caught downstream.

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
| `enter-stage` | A separate lane owns it ("hand it to", "escalate into <Lane>") | A separate stage carrying the `sla-status-change` entry row | `Yes` when the response pauses, takes over, or reroutes active work; `No` for parallel oversight |
| `exit-stage` | The breached stage should end or route away | A stage-exit row | Per exit semantics |
| `exit-case` | The case should close, cancel, or reach an alternate terminal | A case-exit row | Per exit semantics |

**Hard rule — resumption decides between `enter-stage` and `exit-case`.** Ask one question: after the response runs, does the case CONTINUE? "A lane takes the case over until a manager clears it, then work resumes where it left off" continues — that is `enter-stage` with `Interrupting: Yes` and a `return-to-origin` exit, never `exit-case`. `exit-case` is TERMINAL: use it only when the case genuinely ends there (cancelled, withdrawn, closed early) and nothing resumes. A row that names a target stage to enter and then returns is an `enter-stage` row no matter how severe the breach that triggered it.

Never author `start-task` as a stage-entry row on the breached stage: it validates, but stage re-entry re-runs every task whose `Run Only Once` is `No` — a breach meant to add one manager check silently re-runs the whole stage.

### Defaults when the source is silent

- SLA exists only where the source mentions timing, read literally ("about a day" → 1 day). No timing → `—`, no SLA rule. Scope, status, and response are chosen separately (§ Choosing the response).
- No stated response → both statuses `notify-only`. Never invent a stage, task, or routing change.
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

<!-- parsed at runtime by scripts/audit_sdd.py — do not rename this heading or reshape this table/fence; a rename disarms the checks and audit_sdd.py will report "model checks disarmed" -->

Safe display characters for stage labels, task display names, and condition/SLA/escalation titles:

```
^[A-Za-z0-9 _-]+$
```

**`:` is the hard ban** — case-execution events are colon-delimited, so a colon in a name breaks routing. It is the one character `audit_sdd.py` gates on, in every mode, including names read from a draft: surface and ask, never silently keep or repair.

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

ONE checklist. Settle every item by assumption during Sketch; re-walk at Confirm (fix failures silently — authoring defects, not user decisions; unfixable → Review Flags). Mechanical shape/contract checks are NOT here — `scripts/audit_sdd.py` owns them (enforcement list: template § Validation); run it on the written file.

**Blocking — the design is unbuildable or unreviewable until fixed:**

1. **Other-path trigger source** — every modeled path's entry shape matches its trigger source (§ Secondary-lane entry shapes); interrupting flags set on the stage AND on every entry row; terminal `exit-only` vs returning `return-to-origin` chosen; a warning-only escalation stays a notification; an SLA response needing case work carries ONE `sla-status-change` entry with declared target + titles; never duplicate a global-event entry or exit across primary stages.
2. **Reachability walk** — every stage reachable from a trigger or SLA source (walk entries forward); every primary stage's completion consumed downstream, referenced by another entry, or feeding a lane; ≥ 1 primary stage `Required: Yes`; `adhoc` never a stage entry. Decision-reachable lanes and duplicate-entry ambiguity per § Secondary-lane entry shapes.
3. **Entry producer** — every non-start entry names its concrete producer (source stage/task, connector event, paired `wait-for-user` exit, declared SLA reference); at-risk rows name the escalation, breach rows the SLA alone.
4. **Decision-routing closure — the most-missed item on this list.** Walk EVERY outcome of EVERY decision task and name where it goes; an outcome you cannot name a destination for is the defect. The recurring misses are the unhappy ones the source mentions only in passing — a declined or expired offer, a rejected application, a withdrawn or on-hold case: they need a lane or a declared terminal exactly like the approve path does. Every decision outcome routes somewhere: no dead-end status values; an outcome targeting a lane keys that lane's entry; every routing button's variable+value is consumed downstream or a declared terminal; a fully-orphaned decision variable on a decision task is blocking.
5. **Gate reads the producer** — no condition whose WHEN names a task reads a case variable that task writes (§ Gate on the producer).
6. **Data closure** — every configure/decide output lands in a variable or direct reference; every send/connector/agent required input maps to variables/literals/upstream outputs as far as knowable without schemas (rest resolves at build); thresholded policy in executable cells (§ Expressions).
7. **Task-surface classification** — human-performed required work `action`, optional user-launched `adhoc`; no compliance trigger phrase paired with a non-`action` type without explicit user reconciliation (§ Task-type override priority).
8. **Required-task presence** — a `required-tasks-completed` completion over a stage with zero `Required: Yes` tasks fails validate: `Stage exit rule '<name>' has no task(s) marked as required`; offer marking the terminal task required.
9. **Resources** — intended names concrete everywhere (`Resolved Resource`, Action App title, `Child Case` — never `<UNRESOLVED>`); identities per the lane's tenant grounding, unresolved only with a paired high review item; when a live contract is in memory: required inputs bound, extract fields exist verbatim, declared action-app fields ⊆ app schema.
10. **Durable rationale** — every stage (kind + routing), task (type + activation, incl. why sequential/parallel/shared-set), and configured SLA (thresholds, recipients, response) carries Design Rationale; provenance on every non-user-stated value ([lane § Authoring policy](case-design-lane-guide.md#authoring-policy)).
11. **Alt dispositions & obligations** — ≥ 1 secondary stage ⟹ non-completing case-exit rows exist (or an open high item); `In` + `file` row ⟹ the Caller-obligation block; SLA Response Map closes both ways with agreeing Interrupting cells (template § SLA Response Map); re-entry loops classified (§ Sequencing & activation).
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
