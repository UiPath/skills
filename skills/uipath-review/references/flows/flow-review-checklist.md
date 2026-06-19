# Flow Review Checklist

Comprehensive quality checklist for UiPath Flow projects (`.flow` files) — orchestration of RPA processes, agents, apps, and human tasks.

> **Unit of Work:** Before running the technical checks below, complete Step 3a (Unit of Work Discovery) from SKILL.md. For flows, the declared unit is in the `.flow` file under `variables.globals` with `direction: "in"` or `"inout"`. The actual unit is what the flow body produces — count downstream resource-node invocations and side effects per flow execution. If one flow invocation fans out to N downstream calls over a sub-collection of the input, that is a Granularity Mismatch (see [rpa-common-issues.md](../rpa/rpa-common-issues.md)).

## 1. Structural Validation

### File Presence

| Check | Severity | How to Verify |
|---|---|---|
| `.flow` file exists and is valid JSON | Critical | `cat *.flow \| python -m json.tool` |
| `project.uiproj` exists with `"ProjectType": "Flow"` | Critical | Read project.uiproj |
| `bindings_v2.json` exists (if external resources used) | Warning | `ls bindings_v2.json` |
| `entry-points.json` present | Warning | `ls entry-points.json` |
| `operate.json` present | Info | `ls operate.json` |

### JSON Schema Compliance

Run the CLI validator first:

```bash
uip flow validate <ProjectName>.flow --output json
```

| Check | Severity | How to Verify |
|---|---|---|
| Flow validates without errors | Critical | `uip flow validate` returns 0 errors |
| All node IDs are unique | Critical | Check for duplicate IDs in nodes array |
| All edge IDs are unique | Critical | Check for duplicate IDs in edges array |
| Every edge has `targetPort` field | Critical | Check all edges for targetPort |
| Every node type has a matching `definitions` entry | Critical | Compare node types to definitions array |
| All nodeIds referenced in edges exist in nodes array | Critical | Cross-reference edge source/target with node IDs |

### Node Integrity

| Check | Severity | How to Verify |
|---|---|---|
| Start node exists (`core.trigger.manual` or `core.trigger.scheduled`) | Critical | Check nodes for trigger type |
| At least one End node exists (`core.control.end`) | Critical | Check nodes for end type |
| No orphan nodes (every node reachable from Start) | Warning | Trace edges from start to verify reachability |
| Every `out` variable mapped on every reachable End node | Critical | Check End node output mappings |
| No `core.logic.mock` placeholder nodes in production flows | Critical | Grep for `core.logic.mock` in nodes |

## 2. Design Quality

### Script Nodes

| Check | Severity | How to Verify |
|---|---|---|
| Script nodes return objects (not bare scalars) | Warning | Check script node output types |
| No `console.log` in script nodes | Warning | Grep for `console.log` in script content |
| Expressions use `=js:` prefix correctly | Warning | Check expression syntax |
| ES2020 subset used (no modern JS features beyond ES2020) | Warning | Check for unsupported syntax |
| Script logic is testable and not overly complex | Info | Review script content |

### Variable Management

| Check | Severity | How to Verify |
|---|---|---|
| Variables have correct direction (`in`, `out`, `inout`) | Warning | Read `.flow` variables section |
| `in` variables are NOT mutated (only `inout` can be modified) | Critical | Check for variable mutations |
| Subflows don't reference parent `$vars` (own scope only) | Critical | Check subflow variable references |
| Variable names are descriptive and consistent | Info | Review variable names |
| No unnecessary variables (unused declarations) | Info | Cross-reference variable usage |

### Edge and Port Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Every edge has both `sourcePort` and `targetPort` | Critical | Check edge definitions |
| Decision node edges use correct port names (`true`/`false`) | Critical | Check decision node edges |
| Switch node edges use correct case port names | Warning | Check switch node edges |
| No duplicate edges between the same node pair on the same ports | Warning | Check for duplicate edges |

## 3. Node-Specific Quality

### Decision Nodes (`core.logic.decision`)

| Check | Severity | How to Verify |
|---|---|---|
| Both `true` and `false` branches defined | Warning | Check outgoing edges |
| Default branch defined (to avoid runtime faults) | Warning | Check for default path |
| Condition expression is valid and testable | Warning | Read condition |
| Fail-fast patterns used (check errors before processing) | Info | Review decision placement |

### Loop Nodes (`core.logic.loop`)

| Check | Severity | How to Verify |
|---|---|---|
| Loop has a clear exit condition | Critical | Check loop configuration |
| Loop variable correctly references the collection | Warning | Check loop input |
| Actions inside loop don't modify the collection being iterated | Warning | Check for collection mutation |
| Parallel multi-instance batch size appropriate | Info | Check batch configuration |

### Merge Nodes (`core.logic.merge`)

| Check | Severity | How to Verify |
|---|---|---|
| Merge node present where parallel branches reconverge | Warning | Check parallel branch endings |
| Merge type matches the gateway type (inclusive merge for inclusive gateway) | Warning | Compare gateway and merge types |

### Subflow Nodes

| Check | Severity | How to Verify |
|---|---|---|
| Subflow has its own Start and End nodes | Critical | Check subflow structure |
| Nesting depth <=3 levels | Warning | Count nesting levels |
| Input variables map to subflow `in` direction globals | Warning | Check variable mapping |
| Output variables map to subflow `out` direction globals | Warning | Check output mapping |
| Subflow used for repeated logic (not one-off sequences) | Info | Evaluate reuse potential |

## 4. Resource Node Quality

### Published Resources

| Check | Severity | How to Verify |
|---|---|---|
| All resource nodes reference published resources (not stale/missing) | Critical | Verify referenced resources exist |
| Resource input schemas match flow variable types | Warning | Compare schemas |
| Resource output mapped to flow variables correctly | Warning | Check output mappings |
| Error handling configured on resource nodes | Warning | Check for error edges |

### Resource Type Appropriateness

| Resource Type | Correct Usage | Flag If |
|---|---|---|
| `uipath.core.rpa-workflow.*` | Invoking published RPA processes | Used for agent-type tasks |
| `uipath.core.agent.*` | Invoking published AI agents | Used for deterministic rule-based tasks |
| `uipath.core.human-task.*` | Requiring human input/approval | Used for automated decisions |
| `uipath.agent.autonomous` | Classification, triage, reasoning | Used for simple data transformation |
| `core.action.script` | Deterministic data transformation | Used for LLM reasoning tasks |

### Agent Node vs Script Node Decision

| Use Script When | Use Agent When |
|---|---|
| Logic is deterministic and rule-based | Input is ambiguous, requires reasoning |
| Rules are known and enumerable | Natural language generation needed |
| Data transformation, filtering, mapping | Classification, triage, or summarization |
| Calculations, lookups, formatting | Understanding unstructured content |

**Flag:** Agent nodes used for deterministic tasks as **Info** (unnecessary cost). Script nodes used for tasks requiring reasoning as **Warning** (insufficient capability).

## 5. Orchestration Patterns

### Dispatcher-Performer (Queue-Based)

If the flow uses queues for work distribution:

| Check | Severity | How to Verify |
|---|---|---|
| Queue create node properly configured | Warning | Check queue node inputs |
| Wait-for-completion used when results needed | Warning | Check if `create-and-wait` vs `create` |
| Queue name externalized (not hardcoded) | Warning | Check for literal strings |
| Error handling for queue failures | Warning | Check error edges |

### Sequential Pipeline

| Check | Severity | How to Verify |
|---|---|---|
| Steps in correct order (no forward dependencies on undefined data) | Critical | Trace data flow |
| Each step's output feeds correctly into next step's input | Warning | Check variable references |
| Error at any step handled gracefully | Warning | Check error paths |

### Fan-Out / Fan-In

| Check | Severity | How to Verify |
|---|---|---|
| Loop properly splits work | Warning | Check loop node |
| Results properly aggregated after loop | Warning | Check post-loop data handling |
| Parallel batch size appropriate for workload | Info | Check batch configuration |

## 6. Error Handling

| Check | Severity | How to Verify |
|---|---|---|
| Resource nodes have error paths (not just success) | Warning | Check for error edges from resource nodes |
| Terminate node used for unrecoverable errors | Info | Check for `core.logic.terminate` nodes |
| Error information propagated to End node output | Warning | Check error variable mapping |
| Timeout handling for long-running resource calls | Info | Check for timeout configuration |
| Retry logic for transient failures | Info | Check retry configuration |

## 7. Definitions Quality

| Check | Severity | How to Verify |
|---|---|---|
| Definitions copied from registry (not hand-written) | Critical | Definitions should match registry format exactly |
| Every node type has exactly one definitions entry | Critical | Cross-reference nodes and definitions |
| No orphan definitions (types not used by any node) | Info | Cross-reference definitions and nodes |
| Definition versions match node `typeVersion` | Warning | Compare versions |

## 8. BPMN / Maestro Compliance (If Using Maestro)

For flows that target UiPath Maestro execution:

### BPMN Element Support (Execution-Ready)

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
| One clear start event and explicit end events | Critical | Check node structure |
| Parallel gateways have matching parallel join gateways | Critical | Verify parallel synchronization |
| Inclusive gateways have matching inclusive merge | Critical | Verify inclusive synchronization |
| Default path defined on exclusive gateways (prevents runtime faults) | Warning | Check gateway configuration |
| Task sizes are uniform in diagrams | Info | Visual review |
| Flow direction is left-to-right or top-to-bottom | Info | Check node positions |
| Separate process flow from business rules (use DMN Business Rule Tasks) | Info | Check for complex conditionals |

### Timer Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Timer events use valid ISO 8601 durations (e.g., `PT1H`, `P1D`, `R/PT5M`) | Critical | Check timer values |
| Timer boundary events configured for long-running tasks (SLA enforcement) | Info | Check boundary events |
| Non-interrupting timers used when parallel execution is needed | Info | Check timer interrupt mode |
| Cycle timers use correct repeat format (`R/P[duration]`) | Warning | Check cycle syntax |

### Multi-Instance Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Parallel multi-instance batch size appropriate (runs in batches of 50) | Info | Check batch config |
| Sequential multi-instance used when item ordering matters | Warning | Verify ordering requirement |
| Multi-instance loops configured to **continue on individual item failure** (one item's error does not halt the entire batch) | Warning | Check multi-instance configuration for continueOnException/continue-on-failure flag. Batches of 50 where item #15 fails should still process items 16..50 |
| Entry-points UUIDs are unique (no duplicates across entries in `entry-points.json`) | Critical | Parse `entry-points.json`, check for duplicate `uniqueId` values. Duplicates block publishing |
| Nested loops use subprocess pattern (outer sequential, inner parallel) | Info | Check nesting pattern |

### Error Handling in BPMN

| Check | Severity | How to Verify |
|---|---|---|
| Error boundary events attached to tasks with failure risk | Warning | Check boundary events |
| Error end events used for unrecoverable failures | Info | Check error paths |
| Event subprocesses configured for centralized error handling | Info | Check event subprocesses |
| Error mappings configured at element level (first match wins) | Warning | Check error mapping order |

### Maestro vs Flow Decision

If the project uses the simple Flow format (not full Maestro BPMN):

| Check | Severity | How to Verify |
|---|---|---|
| Flow complexity appropriate (simple flows don't need Maestro) | Info | Assess process complexity |
| Long-running processes use Maestro (not simple flows) | Warning | Check process duration |
| Human-in-the-loop steps use Maestro User Tasks | Warning | Check for HITL requirements |
| Process mining integration needed → use Maestro (auto-creates Process Optimization apps) | Info | Check monitoring needs |

## 9. Performance and Optimization

| Check | Severity | How to Verify |
|---|---|---|
| Decision nodes placed early (fail-fast patterns) | Info | Review decision placement |
| Large payloads not carried through unnecessary nodes | Info | Check variable lifecycle |
| Subflows used for repeated logic (DRY principle) | Info | Identify duplicated patterns |
| Parallel execution used where items are independent | Info | Check for sequential processing of independent items |
| Script nodes don't perform work that should be in RPA/agent resources | Warning | Review script complexity |

## 10. Deployment Readiness

| Check | Severity | How to Verify |
|---|---|---|
| Flow validates without errors | Critical | `uip flow validate` |
| All resource bindings resolved | Critical | Check bindings_v2.json |
| No mock placeholder nodes remain | Critical | Grep for `core.logic.mock` |
| Entry points correctly defined | Warning | Check entry-points.json |
| Environment-specific values externalized | Warning | Check for hardcoded URLs/paths |
| Debug flow succeeds end-to-end | Warning | `uip flow debug <project-dir>` |

## 11. Action Center / Human-in-the-Loop

For flows that create human tasks via Action Center:

### Task Design

| Check | Severity | How to Verify |
|---|---|---|
| Actions have clear descriptions telling the user what to do and why | Warning | Review form task content |
| Data is pre-filled — ask only for the decision the automation cannot make | Warning | Check form pre-population |
| Deadlines configured on all human tasks (actions must not sit indefinitely) | Warning | Check deadline/SLA configuration |
| Escalation rules defined (auto-escalate to manager if unresponded) | Warning | Check escalation configuration |
| Assignment rules route actions to appropriate users/roles | Warning | Check task assignment logic |

### Long-Running Workflow Patterns

| Check | Severity | How to Verify |
|---|---|---|
| `Suspend` activity used to release robot while waiting (not `Delay` or loop-wait) | Critical | Grep for Wait/Delay patterns — should use Suspend |
| Timeout handling defined for unresponded actions | Warning | Check what happens if no one completes the task |
| Process state serializable (all variables must survive suspend/resume) | Critical | Check for non-serializable variable types |
| Robot is NOT held during human wait (process properly suspends) | Critical | Verify long-running workflow template is used |

### Maestro Orchestration Patterns

| Check | Severity | How to Verify |
|---|---|---|
| Each task assigned to correct executor type (robot, agent, or human) | Warning | Review task executor assignments |
| Case management configured for individual case tracking | Info | Check case/instance management setup |
| Process Apps configured for user-initiated process starts | Info | Check if Process Apps are set up for business user access |
| End-to-end cycle time monitored (identify bottlenecks across actors) | Info | Check monitoring dashboards |
| Agent tasks have guardrails and fallback to human escalation | Warning | Review agent task configuration |
