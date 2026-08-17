# Stage Shaping — derive the case shape, then render it

Reason the shape from the process the user describes — never reach for the template first. Build the model
in order: **stages → tasks → types → sweep other paths**. Reason first; render second. Shared semantics:
cite, don't restate — stages/lanes ([K-STG](../case-knowledge/semantics/stages.md)), activation
([K-SEQ](../case-knowledge/semantics/sequencing.md)), gates
([K-PAIR](../case-knowledge/facts/pairing.yaml)).

## Deriving stages

**Stage** — a bounded milestone with an entry, tasks, and a completion/exit (K-STG-1). Derive one stage per
milestone the user names. Ask: *what is the case working toward right now, and what makes that done?* A
stage that marks the case complete is main-flow (`Required: Yes`, K-PAIR-5).

**Secondary stage** — semantics in K-STG-2..6. Ask: *does this work belong at one fixed point (regular
stage), or could it happen at several points / only on a condition (secondary)?* "Handle rejected
application", "escalate on SLA breach", "rework loop" → secondary. Returning work exits `return-to-origin`;
terminal rejection/withdrawal/cancel exits `exit-only` + a §1.4a case-exit row (K-STG-4). An optional
one-off inside the current stage stays an `adhoc` task (K-SEQ-4), not a lane. Global events are modeled
once on the destination lane (K-STG-6). Entry shape follows the lane's trigger (K-STG-5).

**Task** — one unit of work, owned by a persona or the system. One verb in the user's description ≈ one
task. Type selection: [task-typing.md](task-typing.md).

### Worked pass (vendor onboarding)

> "Vendors sign up through our portal. We screen them, run a compliance check, set them up in our finance
> system, then activate. If compliance fails it goes back for remediation."

- Milestones → stages: Intake → Screening → Compliance → Finance Setup → Activation (primary).
- "goes back for remediation" → secondary stage, condition-entered, `return-to-origin` — never a sixth
  inline primary.
- "sign up through portal" → event trigger, not Manual — assume and disclose.
- Verbs → task types per [task-typing.md](task-typing.md); ambiguous verbs decided by playbook, disclosed.

## Other-path sweep — mandatory before confirmation

Actively look beyond the primary flow: rework / needs-info loops; rejection, withdrawal, cancellation; SLA
escalation; external-system failure; manual override / worker-selected side work; optional side work;
terminal outcomes differing from success. Choose the smallest faithful model per path: secondary stage,
terminal case-exit, non-completing case-exit, task-level branch, `adhoc` task, or SLA notification-only
row. Clear source signal → model by best assumption + disclose in **Other Paths Considered**. No signal at
all → spend the one bounded question before confirmation; "primary-flow-only" is then a recorded decision,
not an omission.

## Case execution patterns

Classify before choosing rule types (grammar: K-SEQ-2/3/4):

| Pattern | Signal | Model |
|---|---|---|
| Strict sequence | "then", "after", "before", direct prerequisite | consecutive single-task sets; every task `runs-sequentially` (K-SEQ-2) |
| Parallel after predecessor | "after A, do B and C", independent | B and C share one next task set, each `runs-sequentially`; never duplicate `selected-tasks-completed("A")` (K-SEQ-2) |
| Race | confirmation vs timeout/cancel/withdrawal | listener + clock armed while the obligation is pending; downstream gated on the winning fact (K-SEQ-3) |
| Optional side work | "may", "can manually", no required downstream dependency | `adhoc`, `Required: No` (K-SEQ-4) |

**Producer rule:** every non-start stage/task entry names its concrete producer before the Case Review —
source stage exit/completion, task completion, connector event detail, paired `wait-for-user`, or declared
SLA reference. A schema-valid rule without a producer is a design defect (K-STG-7).

## Stage render contract

### Headings

- Primary: `### Stage {N}: {Stage Name} (\`{stage_id}\`)` — N is 1-based flow order.
- Secondary: `### Secondary Stage: {Stage Name} (\`{stage_id}\`)`.
- The trailing code-formatted `{stage_id}` MUST appear; every by-name stage reference in any cell appends
  the id in code-formatted parens (greppable cross-references).

### Stage fields

| Field | Required? | Value |
|---|---|---|
| Type | yes | `Stage` (literal) |
| Stage Kind | optional | `primary` (default — omit) / `secondary` (K-STG-2) |
| Design Rationale | yes | One concrete sentence: why primary/secondary, why the entry/exit behavior fits. Global-event lanes name the event + state that one interrupting entry replaces per-stage duplication (K-STG-6); SLA lanes name SLA, response, and why it interrupts or not (K-SLA-4) |
| Description | yes (primary) / optional (secondary) | One sentence |
| Required for case completion | yes | Explicit `Yes`/`No` — design default: primary `Yes`, secondary always `No` (K-PAIR-5) |
| Interrupting | secondary only | `Yes`; `No` only on the SLA parallel-oversight carve-out (K-STG-3) |
| Stage SLA | when stage has SLA | Duration + `time-based`/`condition-based` + `SLA Title` (K-SLA-2) + conditional-rule and escalation tables ([case-render.md §1.2](case-render.md)) |

**Stage SLA rendering:** when the source says every primary stage has an SLA target, every named primary
stage renders its own `#### Stage SLA` block. Deterministic titles when unnamed: `**SLA Title:** <Stage
Name> SLA`, at-risk `<Stage Name> SLA at risk`, breach `<Stage Name> SLA breached`; every
`sla-status-change` reference uses those exact strings. Render `**SLA Type:**` and `**SLA Title:**` as two
separate lines — a collapsed single line hides the title from line-start tooling and the reference never
resolves.

### Stage Entry Conditions table

≥ 1 row. Columns `WHEN | IF | Interrupting | Display Name`. Legal WHEN: K-PAIR-1 stage-entry set;
`sla-status-change` arg forms per [case-knowledge/contracts/sdd-contract.md](../case-knowledge/contracts/sdd-contract.md)
(K-SDD-3). Interrupting cell per K-STG-2/3. Write call forms ONLY in condition rows, always with complete
args; prose uses bare rule names. `user-selected-stage` requires the upstream `wait-for-user` pair
(K-PAIR-4) and is never the rule for deterministic rejection/approval/send-back/SLA routing — use decision
facts + guarded entries.

### Stage Completion + Exit Conditions — one rendered table

Completion (`Yes`) and exit (`No`) rows render together: `WHEN | IF | Exit Type | Marks Stage Complete |
Display Name`. ≥ 1 completion row per primary stage. Legal/forbidden WHEN and exit types: K-PAIR-1/2/3 —
a `Yes` + `selected-*` pair blocks Approve. `return-to-origin` is completion-only (K-PAIR-3). Regular
stage-to-stage routing is NOT carried here — destination stages declare it via their own entry conditions
(K-STG-1). **One carve-out:** routing INTO a decision/signal-routed lane IS carried here — the gated
diverting exit + inverse-`IF` completion pair (K-STG-5); omitting it dual-fires or deadlocks the decision
path.

### Stage Task Summary table

In plan order, ≥ 1 task per stage: `# | Task ID | Task | Type | Owner`. `Task ID` code-formatted
(`` `t11` ``); Required-Tasks cells elsewhere use those bare ids. Owner = persona or `system`.

### Deterministic stage completion

- **Conditional-branch stages:** mutually-exclusive conditional tasks are all `Required: No`; add ONE
  required convergence task with the DNF OR entry covering every branch + the no-branch guard (K-SEQ-6).
- **Re-entry safety** (`return-to-origin` loops): classify each loop and set `Run Only Once` + variable
  reset per K-SEQ-7. New-attempt loops keep producer/review/decision tasks rerunnable.

### XOR terminal stages

Mutually-exclusive happy-path terminals ("Funding on approve, AAN on decline"): K-PAIR-2 forbids
`selected-stage-*` on case-completion rows, so the XOR lives at stage entry. Two sanctioned patterns —
narrate the choice and surface BOTH via AskUserQuestion when detected at Sketch time (multiple terminal
candidates + an earlier branching decision):

**X1 — gated entry + required terminals (default; no connector needed):**
1. Both terminals `Required for case completion: Yes`.
2. Each terminal's entry: `selected-stage-completed("<DecisionStage>")` + lane guard `IF`
   (`=js:vars.decision === "Approve"` / `"Decline"` — exact inverses, K-EXPR-3).
3. Each terminal completes normally: `required-tasks-completed`, `Marks Stage Complete: Yes`.
4. Stage-skip rule: the runtime evaluates entry `IF` at activation; a terminal whose `IF` is false
   auto-completes (`Skipped`) and still counts toward `required-stages-completed` closure.
5. Case exit §1.4: ONE row, `required-stages-completed`, `Marks Case Complete: Yes`, `IF: —`.

**X2 — connector-event close** (only when both terminals genuinely emit a shared case-done event):
terminals `Required: No`; entries as X1; each terminal's last task emits the shared event; case exit = ONE
`wait-for-connector` row keyed on it.

<!-- END: stage-shaping.md -->
