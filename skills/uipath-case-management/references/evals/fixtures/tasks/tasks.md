# Tasks — Chrysanthemum Claims Triage (TEST)

Generated from `../sdd-placeholder-test.md`. Every registry lookup failed (by design — see fixture notes). Every task is a placeholder.

## T01: Create case file "Chrysanthemum Claims Triage (TEST)"
- case-identifier: TST
- identifier-type: constant
- description: Fictitious claim triage for placeholder-path testing
- case-app-enabled: false
- order: first
- verify: Confirm Result: Success, capture root file path

## T02: Create stage "Intake"
- isRequired: true
- order: after T01
- verify: Confirm Result: Success, capture StageId

## T03: Create stage "Triage"
- isRequired: true
- order: after T02
- verify: Confirm Result: Success, capture StageId

## T04: Add edge Trigger → "Intake"
- source: default Trigger (trig_1)
- target: Intake stage
- order: after T03
- verify: Confirm Result: Success

## T05: Add edge "Intake" → "Triage"
- source: Intake stage
- target: Triage stage
- label: Intake completed
- order: after T04
- verify: Confirm Result: Success

## T06: Add wait-for-connector task "Chrysanthemum Mailbox" to "Intake"
- placeholder: true
- placeholderReason: CONNECTOR_TRIGGER "Chrysanthemum Mailbox" — no match in typecache-triggers-index.json after registry pull --force
- order: after T05
- verify: Expect validation warning "task with no configuration"

## T07: Add api-workflow task "Chrysanthemum Claim Fetcher" to "Intake"
- placeholder: true
- placeholderReason: API_WORKFLOW — no match in api-index.json or any fallback cache for "Chrysanthemum Claim Fetcher" in /Shared/Claims/Fictional after registry pull --force
- order: after T06
- verify: Expect validation warning "task with no configuration"

## T08: Add rpa task "Obsidian Claim Registrar" to "Intake"
- placeholder: true
- placeholderReason: RPA — no match in process-index.json or any fallback cache for "Obsidian Claim Registrar" in /Shared/Claims/Fictional after registry pull --force
- order: after T07
- verify: Expect validation warning "task with no configuration"

## T09: Add agent task "Claim Classifier Agent" to "Intake"
- placeholder: true
- placeholderReason: AGENT — no match in agent-index.json or any fallback cache for "Claim Classifier Agent" in /Shared/Claims/Fictional after registry pull --force
- order: after T08
- verify: Expect validation warning "task with no configuration"

## T10: Add action task "Triage Review Action App" to "Triage"
- placeholder: true
- placeholderReason: HITL — no match in action-apps-index.json for "Triage Review Action App" in /Shared/Claims/Fictional after registry pull --force
- taskTitle: Triage Review Action App
- priority: Medium
- order: after T09
- verify: Expect validation warning "task with no configuration"

## T11: Add execute-connector-activity task "Send Quantum Pager Notification" to "Triage"
- placeholder: true
- placeholderReason: CONNECTOR_ACTIVITY "Quantum Pager" — no match in typecache-activities-index.json after registry pull --force
- order: after T10
- verify: Expect validation warning "task with no configuration"

## T12: Set default SLA for root case to 1 hour
- count: 1
- unit: h
- order: after T11
- verify: Confirm Result: Success

## T13: Add stage exit condition for "Intake" — all tasks done
- rule-type: required-tasks-completed
- type: exit-only
- marks-stage-complete: true
- order: after T12
- verify: Confirm Result: Success

## T14: Add stage exit condition for "Triage" — all tasks done
- rule-type: required-tasks-completed
- type: exit-only
- marks-stage-complete: true
- order: after T13
- verify: Confirm Result: Success

## T15: Add case exit condition — case resolved
- rule-type: required-stages-completed
- marks-case-complete: true
- order: after T14
- verify: Confirm Result: Success

## Not Covered

- No Data Fabric entities were specified in this fixture; none configured.
- Case-level SLA escalation rules, stage-level SLA/escalation per stage omitted (simplified for placeholder-path testing).
