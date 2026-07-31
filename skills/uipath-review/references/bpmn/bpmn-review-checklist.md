# Maestro BPMN Review Checklist

Quality checklist for UiPath Maestro BPMN (Process Orchestration) projects — `.bpmn` process models orchestrating RPA processes, agents, API workflows, and human tasks.

> **Unit of Work:** Before the technical checks below, complete Step 3a (Unit of Work Discovery) from SKILL.md. For BPMN the declared unit is the process start-event payload / process input variables. The actual unit is the external effects per process instance — count service tasks, agent calls, and human tasks executed per instance. One instance fanning out to N external writes over a sub-collection of the input is one-to-many — assess per Step 3a.

> **Read-only:** never run, publish, or migrate the process during review. Fixes route to `uipath-maestro-bpmn`.

## 1. Structural Validation

### Project Markers and Required Files

| Check | Severity | How to Verify |
|---|---|---|
| `project.uiproj` exists with `"ProjectType": "ProcessOrchestration"` | Critical | Read project.uiproj |
| At least one `.bpmn` file exists and is well-formed XML | Critical | `ls *.bpmn` + parse check |
| `entry-points.json` present; entry `filePath` points to an existing `.bpmn` element | Critical | Read entry-points.json |
| Entry-point `uniqueId` values unique across entries | Critical | Parse entry-points.json for duplicate `uniqueId` — duplicates block publishing |
| `bindings_v2.json` present (if external resources used) | Warning | `ls bindings_v2.json` |
| `operate.json` and `package-descriptor.json` present | Info | `ls operate.json package-descriptor.json` |

### CLI Validation

```bash
uip maestro bpmn validate "<FILE>.bpmn" --output json
```

> Requires a current CLI. If the CLI reports an unknown command, record `uip maestro bpmn validate` under "Rules Skipped" and run the manual structural checks below.

## 2. BPMN Element Support (Execution-Ready)

| Element Category | Supported for Execution | Modeling Only |
|---|---|---|
| **Start Events** | None, Message, Timer | Error, Signal, Conditional, Compensation, Escalation |
| **Intermediate Catch** | Message, Timer | Signal, Conditional, Link |
| **Boundary (Interrupting)** | Message, Timer, Error | Signal, Conditional, Escalation, Compensation |
| **Boundary (Non-Interrupting)** | Message, Timer | Signal, Conditional, Escalation |
| **End Events** | None, Message, Error, Terminate | Signal, Escalation, Compensation |
| **Tasks** | User, Service, Send, Receive, Business Rule, Script, Manual | — |
| **Gateways** | Exclusive, Parallel, Inclusive, Event-Based | Complex |
| **Markers** | Multi-instance (parallel/sequential) | Loop, Compensation |
| **Subprocesses** | Sub-process, Call Activity, Event Sub-process | Transaction |

### Structural Checks

| Check | Severity | How to Verify |
|---|---|---|
| All BPMN elements used are execution-ready (not modeling-only) | Critical | Compare against support table above |
| One clear start event and explicit end events | Critical | Check process structure |
| Parallel gateways have matching parallel join gateways | Critical | Verify parallel synchronization |
| Inclusive gateways have matching inclusive merge | Critical | Verify inclusive synchronization |
| No mixed gateway split/merge pairs (Parallel split → Exclusive merge, etc.) | Critical | Deadlock risk — trace every diverging gateway to its merge; types MUST match |
| Default path defined on exclusive gateways (prevents runtime faults) | Warning | Check gateway configuration |
| Task sizes are uniform in diagrams | Info | Visual review |
| Flow direction is left-to-right or top-to-bottom | Info | Check element positions |
| Separate process flow from business rules (use DMN Business Rule Tasks) | Info | Check for complex conditionals |

## 3. Timer Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Timer events use valid ISO 8601 durations (e.g., `PT1H`, `P1D`, `R/PT5M`) | Critical | Check timer values |
| Timer boundary events configured for long-running tasks (SLA enforcement) | Info | Check boundary events |
| Non-interrupting timers used when parallel execution is needed | Info | Check timer interrupt mode |
| Cycle timers use correct repeat format (`R/P[duration]`) | Warning | Check cycle syntax |

## 4. Multi-Instance Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Parallel multi-instance batch size appropriate (runs in batches of 50) | Info | Check batch config |
| Sequential multi-instance used when item ordering matters | Warning | Verify ordering requirement |
| Multi-instance loops configured to **continue on individual item failure** (one item's error does not halt the entire batch) | Warning | Check multi-instance configuration for continueOnException/continue-on-failure flag. Batches of 50 where item #15 fails should still process items 16..50 |
| Nested loops use subprocess pattern (outer sequential, inner parallel) | Info | Check nesting pattern |

## 5. Error Handling

| Check | Severity | How to Verify |
|---|---|---|
| Error boundary events attached to tasks with failure risk | Warning | Check boundary events |
| Error end events used for unrecoverable failures | Info | Check error paths |
| Event subprocesses configured for centralized error handling | Info | Check event subprocesses |
| Error mappings configured at element level (first match wins) | Warning | Check error mapping order |

## 6. Actor Fitness

| Check | Severity | How to Verify |
|---|---|---|
| Each task assigned to the correct executor type (robot, agent, human, API) | Warning | Review task executor assignments |
| Agent tasks have guardrails and fallback to human escalation | Warning | Review agent task configuration |
| Deterministic rule-based logic not assigned to agents (unnecessary cost) | Info | Compare task nature to executor type |
| Human steps use User Tasks with deadlines and escalation rules | Warning | Check user task configuration |
