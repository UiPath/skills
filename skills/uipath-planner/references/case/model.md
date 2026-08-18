# Case Model

Everything a case design must respect about the Case Management platform model. Read once per session;
the authoring method, render contracts, SLA model, and data-flow rules all build on this file.

A case is a versioned JSON document of **stages**, **tasks**, and **conditions** that compiles into a
deterministic rule plan evaluated on every case event. Identity is by **display name** at runtime — names
are load-bearing, not labels. This skill designs the document (`sdd.md`); the build skill
(`uipath-maestro-case`) emits and validates `caseplan.json` from it.

## Document structure

| Node kind | JSON `type` | Notes |
|---|---|---|
| Trigger | `uipath.case.trigger` | How a case instance is born. One primary trigger; more allowed. |
| Stage | `case-management:Stage` | Primary or secondary. A secondary stage carries `data.stageType: "secondary"`; a primary stage OMITS the key — never emit `"primary"`. |
| Sticky note | `case-management:StickyNote` | Canvas annotation only. |

Trigger `serviceType` (under `data.inputs`):

| Start | Emitted `serviceType` | SDD author token |
|---|---|---|
| Manual (user or API call) | `"None"` — never `"Manual"` | `Manual` |
| Schedule | `"timer"` | `Intsvc.TimerTrigger` |
| Connector event | `"Intsvc.EventTrigger"` | `Intsvc.EventTrigger` |

### Task types

The enum is closed — exactly these nine literals, used verbatim as the SDD `Type:` value and the JSON `type`:

| Type | Work it performs |
|---|---|
| `process` | Invoke a deployed orchestration process |
| `action` | Human-in-the-loop form: decide, approve, review, sign off |
| `agent` | AI agent reasoning over unstructured input |
| `rpa` | Deployed UI/desktop automation of a system with no API |
| `api-workflow` | Direct call to a coded / API workflow |
| `case-management` | Launch and coordinate a child case |
| `execute-connector-activity` | One Integration Service connector operation (push) |
| `wait-for-connector` | Pause until an external system calls back (pull) |
| `wait-for-timer` | Pause for a duration or until a datetime |

Never author: `external-agent`, `external-workflow`, `document-extraction`, `flow-process` (unsupported),
and `wait-for-event` / `connector-activity` / `connector-trigger` (not schema literals). Externally-hosted
AI agents (CrewAI, Einstein, Databricks, …) model as `api-workflow`, or `execute-connector-activity` when
a tenant connector exists.

## Lifecycle

The case, each stage, and each task move through gates driven by **rules** in disjunctive normal form:
the outer rule array is OR, each inner array is AND.

### Lifecycle gates

| Gate | Marks complete | Legal WHEN rules |
|---|---|---|
| Stage entry | — | `case-entered` (first stage only), `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`, `user-selected-stage`, `sla-status-change` |
| Stage completion | Yes | `required-tasks-completed`, `wait-for-connector` |
| Stage exit | No | `selected-tasks-completed`, `wait-for-connector` |
| Task entry | — | `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`, `adhoc`, `runs-sequentially` |
| Case completion | Yes | `required-stages-completed`, `wait-for-connector` |
| Case exit | No | `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector` |

1. Tasks have NO exit or completion conditions — a task completes when its own work finishes; downstream
   gates key off `required-tasks-completed` / `selected-tasks-completed`.
2. `Marks Complete: Yes` pairs only with `required-*` rules (or `wait-for-connector`). A `Yes` +
   `selected-*` pair is a schema error.
3. `required-*` rules are vacuous without an explicit `isRequired: true` member. Required status is
   explicit end-to-end — the SDD declares it per stage and task, and emission writes it verbatim. An
   absent flag equals `false` at the validator: `Case rule '<name>' has no required stage(s) selected` /
   `Stage exit rule '<name>' has no task(s) marked as required` (verified on uip 1.198.0-preview.102).
4. **Case completion is a root rule.** At least one `metadata.caseExitRules[]` row carries
   `marksCaseComplete: true` (normally `required-stages-completed`). A stage completing never closes the
   case by itself; alternate outcomes (Rejected, Withdrawn, Cancelled) are case-exit rows with
   `marksCaseComplete: false`.
5. **A gate sees case state as of its own event.** The extract of the task that fired the gate has not
   run yet, so an `IF` that reads a case variable that task writes is stale — read the producing output
   instead ([variables.md § Gate on the producer](variables.md#gate-on-the-producer-never-on-the-variable-it-writes)).

### Exit types

| Row kind | Legal exit types |
|---|---|
| Stage completion (Yes) | `exit-only`, `return-to-origin`, `wait-for-user` |
| Stage exit (No) | `exit-only`, `wait-for-user` |
| Case completion (Yes) | `exit-only` |
| Case exit (No) | `exit-only`, `wait-for-user` |

- `wait-for-user` + `Marks Stage Complete: Yes` is legal and canonical for user-routed completion.
- `return-to-origin` is completion-only, and its lane is always interrupting.

**`wait-for-user` ↔ `user-selected-stage` pairing.** Validate enforces the pair both ways (verified on
uip 1.198.0-preview.102): a `wait-for-user` exit with no `user-selected-stage` entry anywhere fails with
`Stage rule '<name>' has no possible stage options.`; a `user-selected-stage` entry with no
`wait-for-user` exit fails with `Stage entry rule '<name>' will never be met.`. `user-selected-stage` is
picker exposure — a user choosing the next stage — never deterministic routing. Deterministic rejection,
approval, send-back, and SLA routing use decision facts plus guarded entries instead.

## Secondary stages

A secondary stage is an **interrupting exception lane**: `data.stageType: "secondary"`,
`isRequired: false`, excluded from `required-stages-completed`, with `Interrupting: Yes` on the stage AND
on every entry row. Model errors, escalations, rejections, rework, and cancellations here — never as
inline primary stages. Optional one-off work inside the current stage stays an `adhoc` task, not a lane.

**One carve-out:** an `sla-status-change` entry whose response is parallel oversight — the breached work
keeps running; nothing is paused, taken over, or rerouted — reads `Interrupting: No` on the stage and on
that entry row. The lane stays secondary and `isRequired: false`, and it completes `exit-only` (never
`return-to-origin`).

**Exits by intent:**

| Lane intent | Completion row |
|---|---|
| Returning / rework | `return-to-origin` + `Marks Stage Complete: Yes` + `required-tasks-completed` |
| Terminal (Rejected / Withdrawn / Cancelled) | `exit-only` + `Yes`, plus a root case-exit row with `marksCaseComplete: false` |

**Entry shape follows the lane's trigger source:**

| Lane trigger | Entry shape |
|---|---|
| A person launches it | `user-selected-stage`, paired with an upstream `wait-for-user` exit |
| External / global event | ONE `wait-for-connector` entry on the destination lane — never duplicated per origin stage |
| SLA response | ONE `sla-status-change` entry ([slas.md](slas.md)) |
| Decision / signal divert | The origin stage carries a gated diverting exit — `Marks Stage Complete: No`, WHEN `selected-tasks-completed("<decider task>")`, `IF` on the signal, `exitToStageId` → the lane — and the origin's completion exit carries the exact inverse `IF`. The lane enters via `selected-stage-exited("<origin>")` + the same `IF`. |

Omitting the diverting exit makes a decision path dual-fire (ungated completion → the next stage AND the
lane both enter) or deadlock (gated completion with no alternative exit). Only a `selected-stage-exited`
lane entry needs a diverting exit; a `selected-stage-completed("<origin>")` + `IF` lane keys off the
origin's normal completion — guard only.

Two lanes with identical entry rules (same rule, selectors, and expression) are ambiguous routing — give
each a distinct selector or guard. This is a design requirement; validate does not reject the duplicate
(as of uip 1.198.0-preview.102).

## Sequencing & activation

Task-entry mode is exclusive — one mode, one rule, never combined:

| Described timing | Activation Mode token | Entry rule |
|---|---|---|
| Ordered run (`then`, `after`, `before`, a dependency) | `sequential` | One `runs-sequentially` row — on EVERY task in the run, including the first |
| Independent, starts with the stage | `parallel` | `current-stage-entered` |
| Independent siblings after one predecessor | `parallel-after-predecessor` | `runs-sequentially`; the siblings share the next task set |
| External callback | `event-triggered` | `wait-for-connector` (or `sla-status-change` for an SLA-started task) |
| User launches it from the Case App | `adhoc` | One `adhoc` row + `Required: No` |
| Fan-in, convergence, conditional gate | `fan-in` / `conditional-gate` | `selected-tasks-completed("<tasks>")` |

- Structure mirrors the mode in the stage's 2D `data.tasks`: a strict chain is consecutive single-task
  sets; parallel-after-predecessor siblings share one set. Never duplicate
  `selected-tasks-completed("<previous>")` to express simple order.
- `selected-tasks-completed` selects only non-`adhoc` tasks in the SAME stage.
- A task with no entry condition never starts — validate accepts the omission silently.
- Conditional-branch stages (mutually-exclusive tasks, one per outcome, all `Required: No`): add ONE
  required convergence task whose entry is an OR over every branch — one
  `selected-tasks-completed("<branch>")` row each — plus a `current-stage-entered` + inverse-guard row for
  the no-branch path. `required-tasks-completed` then resolves on every path.
- Re-entry (`return-to-origin` loops) — classify before setting `Run Only Once`:

| Loop kind | Signal | Handling |
|---|---|---|
| New attempt | corrected, resubmitted, retry, appeal | Producers rerunnable (`Run Only Once: No`); reset or attempt-scope the live routing variables |
| Re-evaluate an existing fact | the lane changes a fact and the origin re-reads it | `Run Only Once: Yes` on preserved producers; state which rule re-reads the fact |
| Optional repeat | the user may repeat work nothing depends on | `adhoc`, not required |

## Edges — retired

`schema.edges` stays `[]`. Flow is condition-driven: each destination stage declares its own entries, and
the case starts at the first stage's `case-entered` entry. Reachability is therefore condition-only — a
missing or malformed entry condition is the only thing that can orphan a stage.

### Naming rules

Safe display characters for stage labels, task display names, and condition/SLA/escalation titles:

```
^[A-Za-z0-9 _-]+$
```

Never `:` — case-execution events are colon-delimited, so a colon in a name breaks routing. The safe
charset governs names being MINTED or first carried into a design: repair those mechanically — replace
runs of disallowed characters with one space, collapse spaces, trim; keep words and casing; on an empty
result or a collision, add a safe qualifier or numeric suffix and disclose the change. A name read from an
existing draft or SDD during finalization is preserved verbatim, punctuation included — finalization
normalizes structure, never names. The one exception is `:` (the structural ban): surface it and ask,
never silently keep or repair it.

| Name | Unique across |
|---|---|
| Task display name | The whole case — every stage, one pool |
| Stage label | All node labels in the case; never the reserved Case Manager stage label |
| SLA rule title | Its target (root or that stage) |
| Escalation title | All SLAs on the element |

Comparison is exact — case-sensitive, untrimmed. Never normalize external lookup names (Action App
titles, process/connector names — they are matching keys); keep a separate safe display name instead.
Never silently clamp a numeric violation (for example an out-of-range SLA duration) to pass validation —
surface it and ask.

## Related

- Data flow, variables, expressions: [variables.md](variables.md)
- SLA clocks, escalations, responses: [slas.md](slas.md)
