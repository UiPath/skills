# Case Management Product Guide

What a Case Management design must respect. `design` reads it when Level 1 picks Case Management or a Solution includes a case ([design-guide.md](design-guide.md) § Read Plan); the design process — phases, review, write, genome — is the same as for every product. It holds Layers 1–2; Layers 3–4, § Layer closure, § Files and Attachments, § Resources and Identities and § Review Items continue in [case-data-and-time-guide.md](case-data-and-time-guide.md) — read both whole. [case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) holds § Presenting the Case Design (Phase 2 Step 5), § Finalizing a Case Draft and § SDD Conformance Checklist, which is read at the template-superset check ([sdd-writing-guide.md](sdd-writing-guide.md) Step 2 item 8).

Everything a case design must respect about the Case Management platform, ordered the way a design is actually made. A case is a versioned JSON document of **stages**, **tasks**, and **conditions** that compiles into a deterministic rule plan evaluated on every case event. Identity is by **display name** at runtime — names are load-bearing, not labels ([case-data-and-time-guide.md](case-data-and-time-guide.md) § Naming rules). This skill designs the document (`sdd.md`); the build skill (`uipath-maestro-case`) emits and validates `caseplan.json` from it.

Design in four layers, each settled before the next refines it:

1. **Skeleton** — trigger(s), stages, tasks + types. *What work exists and who/what performs it.*
2. **Gates** — entry/exit conditions, sequencing. *When each piece activates, completes, routes.*
3. **Data** — variables, outputs, expressions. *What each piece reads and writes.*
4. **Time** — SLAs and escalations. *What happens when work runs late.*

Close with [§ Layer closure](case-data-and-time-guide.md#layer-closure--the-design-checklist) — the single cross-layer checklist, walked before the Phase 2 Step 5 review and again before the write.

**Best assumption is the design mode.** Every open field takes the **Default** stated in its layer — decided and disclosed, never asked. An optional field the source never touches renders `—`. Every non-verbatim value carries a Design Rationale plus a line in the review's **Decisions I Made** ([case-review-and-conformance-guide.md](case-review-and-conformance-guide.md) § Presenting the Case Design).

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

<!-- named by case-review-and-conformance-guide.md § SDD Conformance Checklist — do not rename this heading or reshape this table/fence; the checklist sends authors here by heading name -->

The enum is closed — exactly these sixteen literals, used verbatim as the SDD `Type:` value. The `type` says **how the work gets done**, not what it is about — read the verb + the actor:

| Type | Pick when the work is… |
|---|---|
| `process` | invoking a **deployed orchestration process** that already packages the automation |
| `action` | a **person** must do, decide, approve, review, or sign off — in a form |
| `agent` | an **AI agent** reasons over unstructured input: classify, extract, summarize, draft, score |
| `rpa` | deterministic **UI / desktop** automation of a legacy app with no API |
| `api-workflow` | calling a **coded / API workflow** directly (multi-step HTTP, serverless logic) |
| `flow-process` | starting a **deployed Maestro Flow** that already packages the steps, named by its flow name and folder |
| `function` | invoking a **deployed Coded Function** — deterministic Python / JS/TS logic, no LLM, no UI |
| `business-rule` | evaluating a **deployed Business Rule** (a decision table) on case data and storing the decision it returns |
| `document-extraction` | reading fields from a **document (invoice, form, contract) with a deployed IXP model**, named by its deployment |
| `case-management` | the step **launches / coordinates a child case** |
| `execute-connector-activity` | one **operation on an Integration Service connector** against a SaaS system (push) |
| `http-request` | **one HTTP call** the SDD spells out (method, URL, headers, query, body), sent directly or with a connector's connection for authentication, with no logic around it |
| `wait-for-connector` | the case **pauses until an external system calls back** (pull) |
| `external-agent` | handing the work to an **externally hosted AI agent** through its connector (CrewAI, Snowflake Cortex, Salesforce Agentforce, Azure AI Foundry…) |
| `external-workflow` | starting an **external automation** through its connector (Power Automate, Salesforce flows) |
| `wait-for-timer` | the case **pauses for a duration or until a datetime** |

<!-- task-types:not-authorable:start (generated by tests/tasks/uipath-maestro-case/_shared/task_types.py --write-guide; do not edit) -->
Never author these. Each is a real task type, but an SDD cannot declare it; a person authors it in Studio Web: `script`.

Never write these as a `Type:` either. Each names the same work in another layer, and none is a task type. Write the plan type instead:

- `connector-activity` → write `execute-connector-activity` (`connector-activity` is from `uip maestro case tasks describe --type`)
- `connector-trigger` → write `wait-for-connector` (`connector-trigger` is from `uip maestro case tasks describe --type`)
- `wait-for-event` → write `wait-for-connector` (`wait-for-event` is from `data.serviceType (Intsvc.WaitForEvent)`)
<!-- task-types:not-authorable:end -->

Externally hosted AI agents and automations with a tenant connection are `external-agent` / `external-workflow`; without one, model the call as `api-workflow`. The Case Designer offers `external-workflow` only where its `panel-showCaseExternalAutomations` flag is on (off by default, set per environment); `external-agent` is not gated. Model an external automation as `external-workflow` only when the request or the user says their Designer shows the External workflow task; otherwise model it as `api-workflow` and record that in Decisions I Made.

**Tie-breakers:** SaaS integration with a tenant connector → `execute-connector-activity` over `api-workflow`. An operation in the external-agent or external-automation catalog → `external-agent` / `external-workflow`, never `execute-connector-activity`. A single request the SDD can state in full → `http-request` over `api-workflow`; a curated connector operation exists for it → `execute-connector-activity` over `http-request`; more than one call, or logic between calls → `api-workflow`. Fields read from a semi-structured document with a deployed IXP model → `document-extraction` over `agent`; no deployment yet → still `document-extraction`, with the model build routed to `uipath-ixp` (template Section 4). Deterministic coded logic → `function` only when tenant evidence (tier 3) resolves a deployed Function; otherwise `api-workflow`. Ambiguous "approve / review / decide" verbs: named human role or implied judgment → `action`; framed as automated/AI → `agent`. **Default when truly even: `action`** — it keeps a human in the loop and one correction flips it. Decide, disclose, never ask. A compliance trigger phrase forces `action` (below).

**Activation is a separate axis.** How a task starts (sequential, event-triggered, manually triggered, stage-started) maps to entry rules (Layer 2) and never changes the `type`.

### Task-type override priority

Apply in order:

1. **User decision pinned to a type** — honor unless schema-invalid or conflicting with tier 2.
2. **Regulatory constraint requiring human sign-off** — the task MUST be `action`. Trigger phrases: "only a licensed X may decide / sign off / certify / approve"; "regulation requires human review"; "ECOA adverse-action notice" / "FCRA adverse action"; "NCQA UM 3 adverse determination"; "HIPAA-protected approval"; "SOC 2 attestation"; any `<role>-licensed` / `<role>-credentialed` gate; "fiduciary review", "legal sign-off", "auditor review". If the user proposes a non-`action` type AND any phrase appears anywhere in the conversation → ask to confirm; never silently accept. Ask phrasing: name the regulation and propose `action` with the LLM/agent work bound to the action's form and recipient. Example: ECOA adverse-action notice with user-stated `agent` → `action` (Compliance Officer recipient; LLM-drafted body bound to the action's form).
3. **Tenant evidence** — the registry cache resolves a deployed Action App / process / agent / api-workflow / function / RPA that fits → prefer that resource's type and surface the match.
4. **Connector availability** — an Integration Service connector matches → `execute-connector-activity` over `api-workflow`.
5. **Verb signal** — fall through to the § Task types tie-breakers.
6. **Fallback** — keep the user's stated value if any; otherwise a placeholder plus a `high` review item ([case-data-and-time-guide.md](case-data-and-time-guide.md) § Review Items).

**Compliance-trigger scan.** Scan the whole conversation for tier-2 phrases BEFORE recording any non-`action` type. A phrase surfacing after a non-`action` type was provisionally recorded → re-ask before continuing. No tier-2 phrase in the transcript (e.g. jurisdiction-dependent underwriting) → keep the stated type, disclose the compliance caveat as a decision line.

### Secondary stages

A secondary stage is an **interrupting exception lane**: `Stage Kind: secondary`, `Required: No`, excluded from `required-stages-completed`, with `Interrupting: Yes` on the stage AND on every entry row. Model errors, escalations, rejections, rework, and cancellations here — never as inline primary stages. Optional one-off work inside the current stage stays an `adhoc` task, not a lane.

**One carve-out:** an `sla-status-change` entry whose response is parallel oversight — the breached work keeps running; nothing is paused, taken over, or rerouted — reads `Interrupting: No` on the stage and on that entry row. The lane stays secondary and `Required: No`, and it completes `exit-only` (never `return-to-origin`).

**Exits by intent:**

| Lane intent | Completion row |
|---|---|
| Returning / rework | `return-to-origin` + `Marks Stage Complete: Yes` + `required-tasks-completed` |
| Terminal (Rejected / Withdrawn / Cancelled) | `exit-only` + `Yes`, plus a root case-exit row with `Marks Case Complete: No` |

### Other-path sweep — mandatory before the review

Look beyond the primary flow. Check the source for each scenario; pick the smallest faithful model:

| Scenario | Candidate models |
|---|---|
| Rework / needs-info loop | Returning secondary lane (`return-to-origin`) |
| Rejection, withdrawal, cancellation | Terminal secondary lane + non-completing case exit |
| SLA escalation | Response per [Layer 4](case-data-and-time-guide.md#layer-4--time-slas--escalations) — notification only unless the source creates work |
| External-system failure | Secondary lane on the failure event, or an advisory review item |
| Manual override / worker-launched side work | `adhoc` task (`Required: No`) or `user-selected-stage` lane |
| Terminal outcomes different from success | Non-completing case-exit rows; XOR terminals ([Layer 2](#xor-terminal-stages)) |

Clear source signal → model it by best assumption and disclose in **Other Paths Considered**. No signal at all → ask it among the Phase 1 Step 6 clarifying questions; "primary flow only" is then a recorded decision, never an omission.

---

## Layer 2 — Gates: entry, exit, sequencing

The case, each stage, and each task move through gates driven by **rules** in disjunctive normal form: the outer rule array is OR, each inner array is AND. **Edges are retired** — flow is condition-driven: each destination stage declares its own entries, and the case starts at the first stage's `case-entered` entry. Reachability is therefore condition-only — a missing or malformed entry condition is the only thing that can orphan a stage.

### Lifecycle gates

<!-- named by case-review-and-conformance-guide.md § SDD Conformance Checklist — do not rename this heading or reshape this table/fence; the checklist sends authors here by heading name -->

| Gate | Marks complete | Legal WHEN rules |
|---|---|---|
| Stage entry | — | `case-entered` (first stage only), `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`, `user-selected-stage`, `sla-status-change` |
| Stage completion | Yes | `required-tasks-completed`, `wait-for-connector` |
| Stage exit | No | `selected-tasks-completed`, `wait-for-connector` |
| Task entry | — | `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`, `adhoc`, `runs-sequentially` |
| Case completion | Yes | `required-stages-completed`, `wait-for-connector` |
| Case exit | No | `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector` |

1. Tasks have NO exit or completion conditions — a task completes when its own work finishes; downstream gates key off `required-tasks-completed` / `selected-tasks-completed`.
2. `Marks Complete: Yes` pairs only with `required-*` rules (or `wait-for-connector`), and `Marks Complete: No` pairs only with `selected-*` rules (or `wait-for-connector`). This is planner policy, not a platform rejection: the schema, `validate` and the Case Designer all accept the crossed pairs, so nothing downstream catches them. Never author either. Completion must track the stage's required set; a `selected-tasks-completed` completion row completes the stage as soon as its named tasks finish, including a task on a guarded branch.
3. `required-*` rules are vacuous without an explicit `isRequired: true` member. Required status is explicit end-to-end — the SDD declares it per stage and task, and emission writes it verbatim. An absent flag equals `false` at the validator: `Case rule '<name>' has no required stage(s) selected` / `Stage exit rule '<name>' has no task(s) marked as required`.
4. **Case completion is a root rule.** At least one case-exit row carries `Marks Case Complete: Yes` (normally `required-stages-completed`). A stage completing never closes the case by itself; alternate outcomes (Rejected, Withdrawn, Cancelled) are case-exit rows with `Marks Case Complete: No`. **Default:** the last primary stage completing closes the case unless the source describes another close-out.
5. **A gate sees case state as of its own event.** The extract of the task that fired the gate has not run yet, so an `IF` that reads a case variable that task writes is stale — read the producing output instead ([Layer 3 § Gate on the producer](case-data-and-time-guide.md#gate-on-the-producer-never-on-the-variable-it-writes)).
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

#### Repairing a `user-selected-stage` lane

Diagnose first; the two repairs are opposites.

| The source says | Defect | Repair |
|---|---|---|
| Pulled aside by hand, picked from the stage picker, nothing triggers it | The lane is correct; its other half is missing | Person-launched |
| Entry is automatic from a decision, event, or SLA | The picker rule itself | Decision-routed |
| Nothing either way | Assume person-launched — re-keying on an unstated fact invents a business rule | Person-launched |

**Person-launched.** Give every eligible upstream primary stage a completing `required-tasks-completed` / `wait-for-user` / `Marks Stage Complete: Yes` exit ("any active case" means every primary stage). This REPLACES that stage's existing `required-tasks-completed | exit-only | Yes` row — never a second completion row, never a `Marks Stage Complete: No` row. Add no event, SLA, or decision trigger.

**Decision-routed.** All four edits, or the branch dual-fires or deadlocks:

1. **Lane entry** — REPLACE the `user-selected-stage` row (never keep it alongside) with `selected-stage-completed("<origin stage>")` (or `selected-stage-exited(...)`), `IF` the affirmative guard on the deciding variable — `=js:(vars.<decisionVar> === "<Value>")` — and `Interrupting: Yes`.
2. **Origin diverting exit** — ADD a row carrying that same affirmative guard with `Marks Stage Complete: No`, so taking the branch does not also complete the stage. Its WHEN is `selected-tasks-completed("<deciding task>")` or `wait-for-connector`: `Marks Complete: No` pairs with nothing else, and the planner never writes `required-tasks-completed | No` (§ Lifecycle gates: a planner rule, since nothing downstream rejects it). Stage exit evaluates before stage completion, so an UNguarded diverting row would fire first and the stage would never complete.
3. **Origin completion exit** — its guard becomes the COMPLEMENT, `=js:(vars.<decisionVar> !== "<Value>")`. Unguarded, it fires on the diverted case too; repeating the affirmative guard on both rows fires both. With more than one diverted outcome the complement excludes every diverted value.
4. **Orphaned picker exposure** — once no `user-selected-stage` entry remains anywhere, DROP any upstream `wait-for-user` exit that existed only to expose this lane; the pairing above fails a `wait-for-user` with no picker entry.

Copy a sibling outcome of the same decision already keyed this way verbatim — usually the approve branch.

### Secondary-lane entry shapes

Entry shape follows the lane's trigger source:

| Lane trigger | Entry shape |
|---|---|
| A person launches it | `user-selected-stage`, paired with an upstream `wait-for-user` exit |
| External / global event | ONE `wait-for-connector` entry on the destination lane — never duplicated per origin stage |
| SLA response | ONE `sla-status-change` entry ([Layer 4](case-data-and-time-guide.md#layer-4--time-slas--escalations)) |
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

**Producer rule:** every non-start stage/task entry names its concrete producer before the review — a source stage exit/completion, a task completion, a connector event, a paired `wait-for-user` exit, or a declared SLA reference. A schema-valid rule without a producer is a design defect.

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
