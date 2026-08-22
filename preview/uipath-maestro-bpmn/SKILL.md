---
name: uipath-maestro-bpmn
description: "TRIGGER for authoring structural-core UiPath Maestro BPMN as `<Name>.bpmn.ts` with the TypeScript builder SDK (`@uipath/flow-sdk/bpmn`) and running the `uip maestro bpmn` check/compile/format/validate loop. Covers events, gateways, tasks, sub-processes, sequence flows, bindings, static rules, and semantic `.bpmn` output. Flow builder authoring → uipath-maestro-flow; case plans → uipath-maestro-case. DO NOT TRIGGER for registry-backed typed BPMN nodes beyond the structural core."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL-bpmn.md` @ fd0070d. Canonical source lives there;
edit upstream and re-sync (see UiPath/flow-builder-sdk#405).
-->

# UiPath Maestro BPMN — TypeScript Builder SDK (structural core)

Author a UiPath **Maestro process** by writing TypeScript that builds a **graph**
of BPMN elements — events, gateways, tasks, sub-processes — wired by
`sequenceFlow`s, then serialize it to a `.bpmn` file. Like the Flow and Case
builders, the methods are **1-1 with BPMN**: `.startEvent()` ↔ `bpmn:startEvent`,
`.exclusiveGateway()` ↔ `bpmn:exclusiveGateway`, `.sequenceFlow()` ↔
`bpmn:sequenceFlow`. `.build()` returns the in-memory graph; `serialize()` turns
it into the XML.

> This is the **structural core** — the elements Maestro lets you author
> directly. Registry-backed *typed* nodes (service/user/send/receive tasks and
> call activities that reference published processes/agents/connectors) are a
> later phase.

Exact function signatures and option shapes, including every builder method
(`BpmnBuilder`, `ScopeBuilder`, `SubProcessBuilder`):
[`references/api.md`](references/api.md).

## Authoring

A worked example is available at `examples/NotifyChannel.bpmn.ts`.

A representative process — a **message-triggered** expense approval that scripts a
decision, **branches**, calls a **connector**, waits for a reply **message**, then
merges before notifying. It touches every core piece; the sections below break each
one down.

```ts
import { bpmn } from '@uipath/flow-sdk/bpmn';

export default bpmn('expense-approval')
  .name('Expense Approval')
  .var('Var_Amount', 'number')                        // → uipath:inputOutput (root variable)
  .var('Var_Employee', 'string')
  .var('Var_Category', 'string')
  .var('Var_Approved', 'boolean')

  // Kicked off by an inbound message (a message start event declares `bpmn:message`).
  .startEvent('Start', { name: 'Expense submitted', message: 'ExpenseSubmitted' })

  // Script a decision: read a variable in, map a result field back out.
  // 1000 is the capitalization boundary — a different axis from the 100
  // auto-approval limit on the gateway below.
  .scriptTask('Classify', {
    script: 'return { category: amount > 1000 ? "capital" : "operating" };',
    inputs:  { amount: '=vars.Var_Amount' },          // read into the script as top-level `amount`
    outputs: { Var_Category: '=result.category' },     // map result back to a variable
  })

  // Branch: small claims auto-approve; everything else needs a manager (the default).
  .exclusiveGateway('Triage', { name: 'Auto-approvable?', default: 'Flow_Manager' })

  // ── auto-approve branch: a plain variable-assignment task ──
  .task('AutoApprove', { name: 'Auto-approve', set: { Var_Approved: '=true' } })

  // ── manager branch: post to Slack (a connector service task), then wait for a reply ──
  .connector('AskManager', 'uipath-salesforce-slack', 'send-message-to-channel',
    { channel: '#approvals',
      messageToSend: '=vars.Var_Employee + " needs approval for a " + vars.Var_Category + " expense of $" + vars.Var_Amount' },
    { connection: 'slack', folder: 'shared', name: 'Ping approvers' })
  .intermediateCatchEvent('Decision', { name: 'Await manager', message: 'ManagerDecision' })

  // Both branches must leave `Var_Approved` set — `Notify` below reads it on
  // either path. (A catch event carries no payload binding, so this example
  // treats the awaited reply as the approval; a real process would branch on it.)
  .task('RecordDecision', { name: 'Record decision', set: { Var_Approved: '=true' } })

  // Merge the two branches. A joining gateway names its lone outgoing as `default`
  // so it needs no condition (the static check requires one or the other).
  .exclusiveGateway('Join', { name: 'Merge', default: 'Flow_Notify' })
  .connector('Notify', 'uipath-salesforce-slack', 'send-message-to-channel',
    { channel: '#expenses',
      messageToSend: '=vars.Var_Employee + " expense approved: " + vars.Var_Approved' },
    { connection: 'slack', folder: 'shared', name: 'Notify employee' })
  .endEvent('Done', { name: 'Done' })

  .sequenceFlow('Start', 'Classify', { id: 'Flow_1' })
  .sequenceFlow('Classify', 'Triage', { id: 'Flow_2' })
  .sequenceFlow('Triage', 'AutoApprove', { id: 'Flow_Auto', condition: '=vars.Var_Amount <= 100' })
  .sequenceFlow('Triage', 'AskManager', { id: 'Flow_Manager' })  // the gateway default (no condition)
  .sequenceFlow('AutoApprove', 'Join')
  .sequenceFlow('AskManager', 'Decision')
  .sequenceFlow('Decision', 'RecordDecision')
  .sequenceFlow('RecordDecision', 'Join')
  .sequenceFlow('Join', 'Notify', { id: 'Flow_Notify' })         // the merge default (no condition)
  .sequenceFlow('Notify', 'Done')

  .build();
```

```bash
uip maestro bpmn check <Name>.bpmn.ts --source  # fast source validation (no output)
uip maestro bpmn compile <Name>                 # <Name>.bpmn.ts → <Name>.bpmn
uip maestro bpmn format <Name>.bpmn             # add diagram layout when a canvas needs it
uip maestro bpmn validate <Name>.bpmn --output json
```

## Builder methods

### `bpmn(id)` / sub-process body

| Method | BPMN element |
| --- | --- |
| `.name(str)` | process name (top level only) |
| `.var(id, type, opts?)` / `.input(...)` / `.output(...)` | `uipath:inputOutput` / `input` / `output` |
| `.startEvent(id, { name?, message?, timer? })` | `bpmn:startEvent` (+ message/timer definition) |
| `.endEvent(id, { name?, terminate?, error?, message? })` | `bpmn:endEvent` (+ terminate/error/message) |
| `.intermediateCatchEvent(id, { message?, timer? })` | `bpmn:intermediateCatchEvent` |
| `.intermediateThrowEvent(id, { message? })` | `bpmn:intermediateThrowEvent` |
| `.boundaryEvent(id, { attachedTo, cancelActivity?, message?/timer?/error? })` | `bpmn:boundaryEvent` |
| `.exclusiveGateway(id, { name?, default? })` | `bpmn:exclusiveGateway` |
| `.parallelGateway(id, { name? })` | `bpmn:parallelGateway` |
| `.inclusiveGateway(id, { name?, default? })` | `bpmn:inclusiveGateway` |
| `.eventBasedGateway(id, { name? })` | `bpmn:eventBasedGateway` |
| `.scriptTask(id, { script, inputs?, outputs?, name?, retry?, loop? })` | `bpmn:scriptTask` (Jint JS + `BPMN.ScriptTask` mapping) |
| `.task(id, { set?, name?, retry?, loop? })` | `bpmn:task` (`BPMN.Variables` variable assignment) |
| `.connector(id, key, action, inputs, { connection?, folder?, name?, outputVar?, skipCondition?, retry?, loop? })` | `bpmn:sendTask` (`uipath:activity` / `Intsvc.ActivityExecution`) — an IS connector op. See **Connector service task** below. |
| `.subProcess(id, sp => …, { name?, triggeredByEvent?, loop?, retry? })` | `bpmn:subProcess` (nested graph) |
| `.binding(id, { name?, value?, resource?, propertyAttribute? })` | `uipath:binding` (top level only) — an identifier supplied per environment, read as `=bindings.<id>` |
| `.sequenceFlow(source, target, { id?, name?, condition? })` | `bpmn:sequenceFlow` |

- **Timers** accept an ISO-8601 string shorthand (`timer: 'PT15M'`) or a full
  `{ duration | date | cycle }`.
- **Errors** accept a name string or `{ name, code }`. A boundary error event
  needs a `code`.
- **Multi-instance** loops: `loop: { collection: '=vars.X', itemVar: 'item', sequential?, completion? }`
  on **any activity**, not just a sub-process; read the current item as
  `iterator.item` (or `iterator.<itemVar>`). `completion` is emitted for the
  platform but is not evaluated by the local engine, so a local run always
  iterates the whole collection.
- **Retry**: `retry: { maxRetries, backoff?: 'PT30S', backoffType?: 'static'|'exponential', exponentialBase?, allErrors?, maxDuration? }`
  on any activity. `maxRetries` counts retries AFTER the first attempt (`3` = four
  runs). Add **`allErrors: true`** unless you mean only platform-retryable
  failures — without it an ordinary activity failure is not retried at all.
  Durations are days/hours/minutes/seconds only: `PT30S`, `P1DT12H`. Not `P1W`.
- **Skip**: `skipCondition: '=js:vars.X'` skips an activity when it is truthy (the
  step records as not executed; the rest of the path still runs). Available on
  `.connector()` only — a script or variable task emits a `uipath:mapping`, which
  cannot carry it.
- **Bindings**: `.binding('apiBase', { value: 'https://api.example.com' })` declares
  an identifier configured per environment; read it as `=bindings.apiBase`. A
  connector's `connection`/`folder` already declare their own.

## Connector service task

`.connector(id, key, action, inputs, { connection?, folder?, name? })` runs an
Integration Service connector op (Slack, Jira, Outlook, …) as a BPMN service task
— a `bpmn:sendTask` carrying a `uipath:activity` of type `Intsvc.ActivityExecution`.
Same surface as the Flow/Case connector: identify the op by `key`/`action` (or a
typed descriptor from `./sdk/connectors/<key>.ts`), pass its `inputs`, and name the
`connection`/`folder` bindings.

Typed descriptor imports require the separately staged connector library; they
are not included in the npm package. The string `key`/`action` form works with
the package and a library supplied through `FLOW_SDK_LIBRARY_JSON`.

```ts
import { bpmn } from '@uipath/flow-sdk/bpmn';

export default bpmn('notify')
  .name('Notify')
  .startEvent('start')
  .connector('post', 'uipath-salesforce-slack', 'send-message-to-channel',
    { channel: '#general', messageToSend: 'BPMN says hi' },
    { connection: 'slack', folder: 'shared', name: 'Post to Slack' })
  .endEvent('done')
  .sequenceFlow('start', 'post')
  .sequenceFlow('post', 'done')
  .build();
```

- Compile with the connector library on `$FLOW_SDK_LIBRARY_JSON` (`compile-cli`
  reads it, or pass `--library`) — the op's method/path/objectName and the
  path/query/body input split come from the library, exactly like Flow/Case.
- `connection`/`folder` are **symbolic binding names**; the offline rungs compile
  them as `=bindings.<name>` (a process-level `uipath:bindings` block is emitted).
  Real connection ids are only needed for a live run. Discover ops + field names in
  the markdown library at `$FLOW_SDK_LIBRARY_MD`.

## Rules the static check enforces (mirrors `uip maestro bpmn validate`)

- An exclusive gateway with **more than one** outgoing flow needs a `condition`
  on each non-`default` one. A gateway with a single outgoing flow is a JOIN and
  needs none. (An unconditioned inclusive-gateway branch is a warning — the
  platform's rule does not cover it.)
- **Every id in the document must be unique** — across elements, flows, variables,
  bindings, and message/error declarations. Not a style rule: the XML parser drops
  the second element that reuses an id, so it vanishes from the process while both
  validators still report the file valid.
- A boundary event attaches to an **activity** (including a connector), and its
  `attachedTo` must resolve; so must a gateway `default` and every sequence-flow
  endpoint. Each scope has a start event; timers have a value; a variable's
  `elementId` names a real element.
- `retry.maxRetries` is a positive integer, and `backoff`/`maxDuration` are
  durations the runtime can parse.
- Warnings, not errors: a **superfluous gateway** (one in, one out) and an
  **implicit join** (an activity/event with more than one incoming flow) — the
  platform accepts both, but a gateway is clearer.

## Notes

- **No diagram is emitted.** BPMN validation is layout-independent, so the SDK
  emits semantic-only XML. A separate `format` step (auto-layout) produces the
  `bpmndi` diagram when a visual canvas needs it — importing into Studio Web also
  lays it out.
- **Expressions** lead with `=` (`=vars.Var_X`, `=bindings.<id>`, `=result.<x>`);
  gateway conditions must be comparisons/boolean logic (no assignment) — hoist
  real computation into a script task before the gateway.
