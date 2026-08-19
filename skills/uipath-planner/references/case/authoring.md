# Authoring — from described process to case model

How to turn the user's process into stages, tasks, and types. Reason the shape from the process —
never reach for the template first. Build in order: **stages → tasks → types → sweep other paths**.
Model semantics (gates, secondary stages, activation grammar): [model.md](model.md). Authority order and
provenance: [principles.md](principles.md).

## Derivation questions

| Concept | Ask of the user's process |
|---|---|
| Stage | *What is the case working toward right now, and what makes that done?* One stage per named milestone. A stage that marks the case complete is main-flow (`Required: Yes`). |
| Secondary stage | *Does this work belong at one fixed point (regular stage), or could it happen at several points / only on a condition?* "Handle rejected application", "escalate on breach", "rework loop" → secondary ([model.md § Secondary stages](model.md#secondary-stages)). An optional one-off inside the current stage stays an `adhoc` task, not a lane. |
| Task | *Who or what performs this, and how?* One verb in the description ≈ one task. The "how" answer is the task type (below). |

### Worked pass — vendor onboarding

> "Vendors sign up through our portal. We screen them, run a compliance check, set them up in our finance
> system, then activate. If compliance fails it goes back for remediation."

- Milestones → stages: Intake → Screening → Compliance → Finance Setup → Activation (primary).
- "goes back for remediation" → a returning secondary lane (condition-entered, `return-to-origin`) — never a sixth inline primary stage.
- "sign up through portal" → event trigger, not Manual — assume and disclose.
- Verbs → types: *screen* (AI over unstructured docs) → `agent`; *compliance check* (connector call vs human sign-off) → decide per the playbook, a "licensed officer signs off" phrase forces `action`; *set up in finance system* → `execute-connector-activity` (or `process` when a deployed process packages it); *activate* → confirm with the user.

## Other-path sweep — mandatory before confirmation

Look beyond the primary flow. Check the source for each scenario; pick the smallest faithful model:

| Scenario | Candidate models |
|---|---|
| Rework / needs-info loop | Returning secondary lane (`return-to-origin`) |
| Rejection, withdrawal, cancellation | Terminal secondary lane + non-completing case exit |
| SLA escalation | Response per [slas.md](slas.md) — notification only unless the source creates work |
| External-system failure | Secondary lane on the failure event, or an advisory review item |
| Manual override / worker-launched side work | `adhoc` task (`Required: No`) or `user-selected-stage` lane |
| Terminal outcomes different from success | Non-completing case-exit rows; XOR terminals (below) |

Clear source signal → model it by best assumption and disclose in **Other Paths Considered**. No signal at
all → spend the one bounded question before the confirmation; "primary flow only" is then a recorded
decision, never an omission.

## Execution patterns

Classify before choosing entry rules (grammar: [model.md § Task activation](model.md#sequencing--activation)):

| Pattern | Signal | Model |
|---|---|---|
| Strict sequence | "then", "after", "before", direct prerequisite | Consecutive single-task sets, every task `runs-sequentially` |
| Parallel after predecessor | "after A, do B and C", both independent | B and C share one next task set, each `runs-sequentially` — never duplicate `selected-tasks-completed("A")` |
| Race | Confirmation vs timeout/cancel/withdrawal | Listener + clock armed while the obligation is pending; downstream work gated on the winning fact |
| Optional side work | "may", "can manually", no required downstream dependency | `adhoc`, `Required: No` |

**Producer rule:** every non-start stage/task entry names its concrete producer before the confirmation —
a source stage exit/completion, a task completion, a connector event, a paired `wait-for-user` exit, or a
declared SLA reference. A schema-valid rule without a producer is a design defect.

## Choosing the task type

The `type` says **how the work gets done**, not what it is about. Read the verb + the actor, ask the
matching question. The enum is closed ([model.md § Task types](model.md#task-types)).

| Type | Pick when the work is… | The question that selects it |
|---|---|---|
| `action` | a **person** must do, decide, approve, review, or sign off — in a form | Does a human need to act or judge here? |
| `agent` | an **AI agent** reasons over unstructured input: classify, extract, summarize, draft, score | Is this judgment over unstructured content an AI can do unattended? |
| `rpa` | deterministic **UI / desktop** automation of a legacy app with no API | Is this clicking through a UI with no API? |
| `process` | invoking a **deployed orchestration process** that already packages the automation | Is there a deployed process that already does this end-to-end? |
| `api-workflow` | calling a **coded / API workflow** directly (HTTP, serverless logic) | Is this an API we call directly? |
| `execute-connector-activity` | one **operation on an Integration Service connector** | Is this a single connector operation against a SaaS system? |
| `wait-for-connector` | the case **pauses until an external system calls back** | Is the case waiting for an external system to respond? |
| `wait-for-timer` | the case **pauses for a duration or until a datetime** | Is the case just waiting on time? |
| `case-management` | the step **launches / coordinates a child case** | Does this spin up a sub-case? |

**Tie-breakers:** SaaS integration with a tenant connector → `execute-connector-activity` over
`api-workflow`. Ambiguous "approve / review / decide" verbs → `action` (human) vs `agent` (AI) per the
assumption playbook ([case-design-lane-guide.md § Sketch](../case-design-lane-guide.md#sketch--best-assumption-every-field)),
decided and disclosed. A compliance trigger phrase forces `action` regardless (below).

## Task-type override priority

Apply in order:

1. **User decision pinned to a type** — honor unless schema-invalid or conflicting with tier 2.
2. **Regulatory constraint requiring human sign-off** — the task MUST be `action`. Trigger phrases:
   - "only a licensed X may decide / sign off / certify / approve"
   - "regulation requires human review"
   - "ECOA adverse-action notice" / "FCRA adverse action"
   - "NCQA UM 3 adverse determination"
   - "HIPAA-protected approval"
   - "SOC 2 attestation"
   - any `<role>-licensed` or `<role>-credentialed` gate ("licensed underwriter", "credentialed clinician")
   - "fiduciary review", "legal sign-off", "auditor review"

   If the user proposes a non-`action` type AND any phrase above appears anywhere in the conversation →
   ask to confirm; never silently accept. Ask phrasing: name the regulation and propose `action` with the
   LLM/agent work bound to the action's form and recipient.
3. **Tenant evidence** — the registry cache resolves a deployed Action App / process / agent /
   api-workflow / RPA that fits → prefer that resource's type and surface the match.
4. **Connector availability** — an Integration Service connector matches the integration →
   `execute-connector-activity` over `api-workflow`.
5. **Verb signal** — fall through to the assumption playbook.
6. **Fallback** — keep the user's stated value if any; otherwise a placeholder plus a `high` review item
   ([principles.md § Review items](principles.md#review-items)).

**Worked examples:**

| Case context | User stated | Override fires | Final type |
|---|---|---|---|
| Adverse-action notice (lending) — "ECOA mandates licensed compliance officer signs off" | `agent` (LLM drafts the notice) | Yes — tier 2 | `action` (Compliance Officer recipient; LLM-drafted body bound to the action's form) |
| Vendor scoring on intake | `agent` | No — no regulation, no licensed role | `agent` |
| Underwriting decision on mortgage | `agent` | Jurisdiction-dependent; no tier-2 phrase in the transcript → keep `agent`, disclose the compliance caveat as a decision line | `agent` (disclosed) |
| Inbound webhook from Salesforce | `api-workflow` | Tier 4 prefers the connector | `execute-connector-activity` when a Salesforce connector exists in the tenant; else `api-workflow` |
| Process orchestration call | `process` | No | `process` |

**Compliance-trigger scan.** Scan the whole conversation for the tier-2 phrases BEFORE recording any
non-`action` type. A phrase surfacing after a non-`action` type was provisionally recorded → re-ask
before continuing.

**Activation is a separate axis.** How a task starts (sequential, event-triggered, manually triggered,
stage-started) maps to entry rules ([model.md § Task activation](model.md#sequencing--activation)) and never
changes the `type`: a manually triggered task can still be `action`, `agent`, `api-workflow`, or
`process`. `sequential` requires an explicit order or dependency in the source.

**Externally-hosted AI agents** (CrewAI, Salesforce Einstein, Databricks, LangChain, …) are not
first-class: model as `api-workflow` (system-to-system) or `execute-connector-activity` when a connector
exists.

## Trigger derivation

| Source says | Trigger |
|---|---|
| External system, portal, form, inbound event, or record-created start | Connector Event — a tenant object start stays an event trigger even when provisioning is missing (unresolved detail becomes a placeholder later; never downgrade to Manual) |
| Schedule / recurring | Timer |
| Otherwise | Manual |

On-disk trigger values and enums: [model.md § Triggers](model.md#document-structure).

## XOR terminal stages

Mutually-exclusive happy-path terminals ("Funding on approve, Adverse Action Notice on decline"): case
completion accepts only `required-stages-completed` ([model.md § Lifecycle gates](model.md#lifecycle-gates)),
so the XOR lives at stage entry. Two sanctioned patterns — when detected at sketch time (multiple terminal
candidates plus an earlier branching decision), surface both in one question before drafting rows:

**Gated entry + required terminals (default — works on every tenant):**

1. Both terminal stages `Required for case completion: Yes`.
2. Each terminal's entry: `selected-stage-completed("<DecisionStage>")` + its lane guard `IF`
   (`=js:vars.decision === "Approve"` / `!== "Approve"` — exact inverses).
3. Each terminal completes normally: `required-tasks-completed`, `Marks Stage Complete: Yes`.
4. Runtime stage-skip: entry `IF` is evaluated at activation; a terminal whose `IF` is false
   auto-completes with status `Skipped` and still counts toward `required-stages-completed` closure.
5. Case exit: ONE row, `required-stages-completed`, `Marks Case Complete: Yes`, `IF: —`.

**Connector-event close** (only when both terminals genuinely emit a shared case-done event): terminals
`Required: No`; entries as above; each terminal's last task emits the shared event; the case exit is ONE
`wait-for-connector` row keyed on it.
