# Choosing the task type

The `type` says **how the work gets done**, not what it's about. Read the verb + actor, ask the matching
question, pick the type. The enum is closed (K-TYP-1); never-author list in K-TYP-2. Pick the baseline
here; [§ Override priority](#task-type-override-priority) resolves conflicts on top.

| Type | Pick when the work is… | The question that selects it |
|---|---|---|
| `action` | a **person** must do, decide, approve, review, or sign off — in a form (human-in-the-loop) | Does a human need to act or judge here? |
| `agent` | an **AI agent** reasons over unstructured input: classify, extract, summarize, draft, score | Is this judgment over unstructured content an AI can do unattended? |
| `rpa` | deterministic **UI / desktop** automation of a legacy app with no API (an existing RPA process) | Is this clicking through a UI / legacy system with no API? |
| `process` | invoking a **deployed orchestration process** that already packages this automation | Is there a deployed process that already does this end-to-end? |
| `api-workflow` | calling a **coded / API workflow** directly (HTTP, serverless business logic) | Is this an API / coded workflow we call directly? |
| `execute-connector-activity` | one **operation on an Integration Service connector** (Salesforce create record, send email) | Is this a single connector operation against a SaaS system? |
| `wait-for-connector` | the case **pauses until an external system calls back** (webhook, inbound event) | Is the case waiting for an external system to respond? |
| `wait-for-timer` | the case **pauses for a duration or until a datetime** | Is the case just waiting on time? |
| `case-management` | the step **launches / coordinates a child case** | Does this spin up a sub-case? |

**Tie-breakers:** SaaS integration with a tenant connector → `execute-connector-activity` over
`api-workflow`. "Approve / review / decide" verbs are ambiguous between `action` (human) and `agent` (AI)
— decide per the assumption playbook ([case-design-lane-guide.md § Sketch](../case-design-lane-guide.md#sketch--best-assumption-every-field))
and disclose. A compliance trigger phrase forces `action` regardless (below).

## Task-type override priority

Apply in order when picking `type`:

1. **User decision pinned to a type** — honor unless schema-invalid (K-TYP-1) or conflicting with (2).
2. **Regulatory constraint requiring human sign-off** — task MUST be `action`. Trigger phrases that force
   `action` regardless of user preference:
   - "only a licensed X may decide / sign off / certify / approve"
   - "regulation requires human review"
   - "ECOA adverse-action notice" / "FCRA adverse action"
   - "NCQA UM 3 adverse determination"
   - "HIPAA-protected approval"
   - "SOC 2 attestation"
   - any `<role>-licensed` or `<role>-credentialed` gate ("licensed underwriter", "credentialed clinician")
   - "fiduciary review", "legal sign-off", "auditor review"

   If the user proposes any non-`action` type AND any phrase above appears in the conversation → Ask to
   confirm; never silently accept. Ask phrasing: name the regulation and propose `action` with the
   LLM/agent work bound to the action's form/recipient.
3. **Tenant evidence** — the registry cache resolves a deployed Action App / process / agent /
   api-workflow / RPA that fits → prefer that resource's type and surface the match.
4. **Connector availability** — an IS connector matches the integration → `execute-connector-activity`
   over `api-workflow`.
5. **Verb signal** — fall through to the assumption playbook.
6. **Fallback** — keep the user's stated value if any; otherwise emit a placeholder per the build skill's
   placeholder contract + a `high` review item ([authoring-core.md § Review items](authoring-core.md#review-items)).

**Worked examples:**

| Case context | User stated | Override fires | Final type |
|---|---|---|---|
| Adverse-action notice (lending) — "ECOA mandates licensed compliance officer signs off" | `agent` (LLM drafts notice) | Yes — tier 2 | `action` (Compliance Officer recipient; LLM-drafted body bound to the action's form context) |
| Vendor scoring on intake | `agent` (LLM scores docs) | No — no regulation, no licensed role | `agent` |
| Underwriting decision on mortgage | `agent` (LLM applies criteria) | Maybe — jurisdiction-dependent; no tier-2 phrase in transcript → keep `agent`, disclose the compliance caveat as a decision line | `agent` (disclosed) |
| Inbound webhook from Salesforce | `api-workflow` | No — but tier 4 prefers the connector | `execute-connector-activity` if a Salesforce connector exists in tenant; else `api-workflow` |
| Process orchestration call | `process` | No | `process` |

**Compliance trigger detection.** Scan the entire Listen + Ask transcript for the tier-2 phrases BEFORE
recording any non-`action` type. If a phrase surfaces after a non-`action` type was provisionally
recorded, re-Ask before continuing to resolution.

## Activation is a separate axis

Task activation modes (`sequential`, `event-triggered`, `manually-triggered`, stage-started) map to entry
rules per K-SEQ-1 — they never change the `type`. `adhoc` decides how a task STARTS, not what it is: a
manually triggered task may still be `action`, `agent`, `api-workflow`, `process`, etc. Downstream plans
preserve the confirmed SDD mode and rule exactly; `sequential` requires an explicit order or dependency in
the source (K-SEQ-2).

**Externally-hosted AI agents** (CrewAI, Salesforce Einstein, Databricks, LangChain, …) are NOT
first-class: model as `api-workflow` (system-to-system) or `execute-connector-activity` when a connector
exists. Never invent `external-agent` (K-TYP-2).

<!-- END: task-typing.md -->
