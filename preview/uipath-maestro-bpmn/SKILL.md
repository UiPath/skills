---
name: uipath-maestro-bpmn
description: "TRIGGER for authoring structural-core UiPath Maestro BPMN as `<Name>.bpmn.ts` with the TypeScript builder SDK (`@uipath/flow-sdk/bpmn`) and running the `uip maestro bpmn` check/compile/format/validate loop. Covers events, gateways, tasks, sub-processes, sequence flows, bindings, static rules, and semantic `.bpmn` output. Flow builder authoring → uipath-maestro-flow; case plans → uipath-maestro-case. DO NOT TRIGGER for registry-backed typed BPMN nodes beyond the structural core."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL-bpmn.md` @ efd27ce. Canonical source lives there;
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
| `.http(id, { url, method?, headers?, parameters?, body?, name?, outputVar?, skipCondition?, retry?, loop? })` | `bpmn:sendTask` (`uipath:activity` / `Intsvc.UnifiedHttpRequest`) — an HTTP request. See **HTTP request** below. |
| `.humanTask(id, { app, title?, actions?, input?, outputs?, appVersion?, key?, … })` | `bpmn:userTask` (`uipath:activity` / `Actions.HITL`) — a task a person completes. See **Human task** below. |
| `.businessRule(id, { process, folder?, input?, outputs?, … })` | `bpmn:businessRuleTask` (`uipath:activity` / `Orchestrator.BusinessRules`) — executes a business rule. Despite the element, this is a **job start**, not a decision table. See **Orchestrator** below. |
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

## HTTP request

`.http(id, opts)` emits an `Intsvc.UnifiedHttpRequest` node — the platform's HTTP
activity, and the first **registry-backed** typed node. Its wire shape comes from
the committed registry snapshot, so it cannot drift from what
`uip maestro bpmn validate` accepts. No connector library and no tenant needed.

```ts
export default bpmn('sync')
  .binding('apiBase', { name: 'API base URL', value: 'https://api.example.com' })
  .var('orders', 'object')
  .startEvent('start')
  .http('fetch', {
    method: 'GET',
    url: '=js:bindings.apiBase + "/v1/orders"',
    headers: { accept: 'application/json' },
    parameters: { limit: 50 },
    retry: { maxRetries: 2, backoff: 'PT5S', allErrors: true },
  })
  .task('keep', { set: { orders: '=js:vars.fetch_response' } })
  .endEvent('done')
  .sequenceFlow('start', 'fetch')
  .sequenceFlow('fetch', 'keep')
  .sequenceFlow('keep', 'done')
  .build();
```

- The response lands in **`<id>_response`** (`fetch_response` above) unless
  `outputVar` says otherwise, and it is readable downstream with no `.var()`.
- `url` takes an `=`-expression, so `=bindings.<id>` works — which is how the same
  process points at different environments.
- `method` defaults to `GET`. `headers` / `parameters` / `body` are plain objects;
  the SDK serializes them the way the platform reads them.
- Accepts the shared activity options (`retry`, `loop`, `skipCondition`) and takes
  a `boundaryEvent` like any other activity.

## Human task (approval gates)

`.humanTask(id, opts)` emits an `Actions.HITL` Action App task — work a person
completes. `app` is the Action App id and comes from the tenant.

**Always set `outputs` if anything branches on the decision.** The type's own
output is a typed one the designer resolves but a local run leaves empty, so
without a mapped field a gateway cannot read the outcome offline.

```ts
export default bpmn('invoice')
  .var('outcome', 'string', { default: 'none' })
  .startEvent('start')
  .humanTask('approve', {
    app: 'app-123',
    title: 'Approve the invoice',
    actions: ['approve', 'reject'],
    input: { amount: 100 },
    outputs: { decision: '=Action' },      // <- what the gateway reads
  })
  .exclusiveGateway('gw', { default: 'fReject' })
  .task('ok', { set: { outcome: 'approved' } })
  .task('no', { set: { outcome: 'rejected' } })
  .exclusiveGateway('join', { default: 'fJoin' })
  .endEvent('done')
  .sequenceFlow('start', 'approve')
  .sequenceFlow('approve', 'gw')
  .sequenceFlow('gw', 'ok', { id: 'fApprove', condition: '=js:vars.decision == "approve"' })
  .sequenceFlow('gw', 'no', { id: 'fReject' })
  .sequenceFlow('ok', 'join', { id: 'fOk' })
  .sequenceFlow('no', 'join', { id: 'fNo' })
  .sequenceFlow('join', 'done', { id: 'fJoin' })
  .build();
```

**Test both arms offline** — the runtime stands in for the person:

```bash
flow-debug Invoice.bpmn --mock --virtual-time --hitl-response 'approve={"Action":"approve"}'
flow-debug Invoice.bpmn --mock --virtual-time --hitl-response 'approve={"Action":"reject"}'
```

- `=Action` is the response field the runtime's outcome routing reads.
- With **no** outcome injected the mapped field is empty and the gateway takes its
  `default` arm — an un-decided task does not hang, it falls through. Design the
  default accordingly.
- `actions` is comma-joined. The platform does not validate its encoding, so if a
  live run mis-reads the outcomes, compare against a Studio Web export.

## Orchestrator: start work elsewhere

Seven methods over ten registry types — the sync/async and wait choices are
options, not separate methods.

| Method | What it starts |
| --- | --- |
| `.startProcess(id, opts)` | an RPA process, and waits |
| `.startAgent(id, opts)` | an agent, and waits |
| `.startAgenticProcess(id, { …, async? })` | an agentic process (call activity) |
| `.startCaseProcess(id, { …, async? })` | a case-management process (call activity) |
| `.executeApiWorkflow(id, opts)` | an API workflow, fire-and-forget |
| `.queueItem(id, { queue, folder, item?, wait? })` | adds an Orchestrator queue item |
| `.businessRule(id, opts)` | a business rule, and waits |

```ts
export default bpmn('nightly')
  .startEvent('start')
  .startProcess('post', { process: 'InvoicePosting', folder: 'Finance', input: { batch: 42 } })
  .queueItem('audit', { queue: 'AuditTrail', folder: 'Finance', item: { source: 'nightly', batch: 42 } })
  .endEvent('done')
  .sequenceFlow('start', 'post')
  .sequenceFlow('post', 'audit')
  .sequenceFlow('audit', 'done')
  .build();
```

- A process is addressed by **name** (`process: 'InvoicePosting'`), not by key —
  the runtime resolves the key, so the same artifact works on any tenant that has
  a process by that name.
- `input` becomes the job's arguments; a queue item's `item` becomes its content.
- The response lands in `<id>_processResponse` (jobs) or `<id>_response` (queues).
- `folder` is **required** for `.queueItem()` — queue items are folder-scoped and
  the runtime refuses to dispatch without it.
- `.startAgent()` needs its process and folder supplied as **bindings**; the SDK
  declares them for you from the plain names you pass, so just pass names.
- `.businessRule()` is in this table, not a separate section, because that is what
  it is. `Orchestrator.BusinessRules` rides a `bpmn:businessRuleTask` and its label
  reads "Execute business rule", so it looks like a DMN decision table — but its
  registry spec is `releaseKey`/`folderPath`/`name` + `JobArguments`, identical to
  `.startProcess()`. `process` names a package whose Orchestrator process type is
  `BusinessRules`; the decision logic lives inside that package, not in your `.bpmn`.
  Nothing to do with the Case SDK's `rule()`, which declares stage lifecycle
  conditions. Its response lands in `<id>_businessRuleResponse` — pinned by the SDK,
  not derived, because the registry's output name for this type is its
  `[Preview]` label. The extension type is marked `[Preview]`: its shape can change.
- `metadata.*` (e.g. `metadata.instanceId`) is **empty in a local run**, so an
  `item`/`input` field built from it silently arrives as nothing. Use `vars.*` or a
  literal when you want to see the value in a `flow-debug` dry run.

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

## Importing an existing `.bpmn`

`npx flow-sdk bpmn decompile <Name.bpmn>` writes `<Name>.bpmn.ts` whose default export
recompiles to an **equivalent** process — every element, id, extension type,
graph edge and metadata row survives. Use it to bring a process authored in
Studio Web (or handed over as a file) under SDK authoring.

Use the package's family-first CLI for the complete round-trip:

```bash
npx flow-sdk bpmn decompile Invoice.bpmn                 # -> Invoice.bpmn.ts
npx flow-sdk bpmn compile   Invoice.bpmn.ts -o out.bpmn  # equivalent to Invoice.bpmn
```

### Editing an existing `.bpmn`: decompile, edit, compile, **merge**

If the file is yours to own from now on, recompiling over it is fine. If you are making a
**targeted change to a process someone else authored** — and must leave the rest of it
alone — add a merge step. Recompiling rewrites every element in the file, including the
ones you never looked at; merging rewrites only the ones you actually changed.

```bash
npx flow-sdk bpmn decompile Invoice.bpmn                             # -> Invoice.bpmn.ts
npx flow-sdk bpmn compile   Invoice.bpmn.ts -o baseline.bpmn         # BEFORE editing — keep this
#   ... make your change in Invoice.bpmn.ts ...
npx flow-sdk bpmn compile   Invoice.bpmn.ts -o edited.bpmn
npx flow-sdk bpmn merge     Invoice.bpmn edited.bpmn --baseline baseline.bpmn -o Invoice.bpmn
uip maestro bpmn format Invoice.bpmn                        # only if you ADDED elements
```

`baseline.bpmn` is what a faithful round trip of the original produces before you touch
anything. Comparing your `edited.bpmn` against it is how the merge tells which elements
you changed: anything identical to the baseline you did not touch, so it is emitted from
the **original**, byte for byte — original attribute order, original formatting, original
`uipath:*` payloads, and the original diagram. It reports the split when it runs
(`4 preserved, 1 authored, 0 removed`); if `authored` is larger than the change you meant
to make, something else moved too.

Skip `--baseline` for a two-way merge: takes your edited process and re-attaches the
original diagram. Less precise, still better than a bare recompile, which drops layout.

Run `format` only when you added elements — new ones have no diagram shape yet. It
re-lays-out the whole file, so running it needlessly discards the geometry the merge just
preserved.

- **Not byte-for-byte, and not attribute-for-attribute.** One payload detail is
  normalised, because the builder models authoring intent and not wire text: an
  **output row keyed by a variable** loses a row `name` that differs from the
  variable id — `name="total" var="Var_Total"` returns as `name="Var_Total"`.
  `var` and `source` are intact, so the mapping still resolves the same way.

  It is harmless to the runtime. It matters if something downstream compares XML
  attribute-by-attribute — then a round trip is not a no-op. `flow-sdk bpmn merge` above is
  the answer: on an element you did not edit, the row comes from the original and
  keeps its name.

- **An `args` input row comes back with `type="json" target="bodyField"` added, and
  that is a repair rather than a loss.** `uip maestro bpmn validate` REJECTS a bare
  `<uipath:input name="args">`, so an artifact missing them is invalid and the
  recompiled one is correct. Do not try to preserve the bare form.

- **Diagram layout is not read or written.** The SDK emits semantic-only XML; run
  `format`/`tidy` on the recompiled file when a canvas needs one.
- **A connector task comes back as a generic `.activity()`**, not as a
  `.connector()` call — the library's action slug is not in the XML, only its
  `objectName`. Everything the platform needs IS in the artifact, so it recompiles
  byte-identically with no connector library involved. Editing one means editing the
  context/input rows directly rather than the friendlier `.connector()` arguments.
- Types with no typed method decompile to `.activity(id, type, { … })`, the generic
  form. That is faithful, just less readable than the typed methods.
- Comments and method order are not preserved — the source is regenerated.

## Project package files (`project.uiproj`, `operate.json`, …)

The SDK emits the `.bpmn` and nothing else. A Maestro BPMN **project** — what packs,
uploads, publishes, or deploys — also needs five local metadata files alongside it:

    project.uiproj  operate.json  entry-points.json  bindings_v2.json  package-descriptor.json

You author these yourself. Three details are enforced, and each has a plausible-looking
wrong answer that still parses as JSON:

- **`project.uiproj`** uses lowercase `"main"` pointing at the BPMN file.
- **`operate.json`** uses `"main"` with the **bare BPMN filename** — *not* a
  `/content/<file>.bpmn#<start-event-id>` entry-point path — plus
  `"contentType": "ProcessOrchestration"`. Mixing up these two `main` formats is the
  single most common mistake here, because `entry-points.json` genuinely does use the
  `#<start-event-id>` form.
- **`package-descriptor.json`** uses a top-level `"content"` array of `content/<file>`
  entries. Not `contentFiles`, and not a CLI scaffold `"files"` map.

`entry-points.json` carries one entry per root start event, its `filePath` written
`/content/<file>.bpmn#<the start event's id>` — the id you gave `.startEvent()`.

A minimal, placeholder-safe set for a process whose start event is `start`:

```jsonc
// project.uiproj
{ "name": "Demo", "main": "Demo.bpmn", "designOptions": { "projectType": "ProcessOrchestration" } }
// operate.json          — bare filename, NOT /content/Demo.bpmn#start
{ "main": "Demo.bpmn", "contentType": "ProcessOrchestration" }
// entry-points.json     — here the #<start-event-id> form IS correct
{ "entryPoints": [ { "filePath": "/content/Demo.bpmn#start", "input": [], "output": [] } ] }
// bindings_v2.json
{ "version": "2.0", "resources": [] }
// package-descriptor.json
{ "content": ["content/Demo.bpmn", "content/bindings_v2.json",
              "content/entry-points.json", "content/operate.json"] }
```

Treat all five as **derived** from the `.bpmn`: when the process changes its start
event id, entry points, or root bindings, refresh them rather than hand-patching.

## Notes

- **No diagram is emitted.** BPMN validation is layout-independent, so the SDK
  emits semantic-only XML. A separate `format` step (auto-layout) produces the
  `bpmndi` diagram when a visual canvas needs it — importing into Studio Web also
  lays it out.
- **Expressions** lead with `=` (`=vars.Var_X`, `=bindings.<id>`, `=result.<x>`);
  gateway conditions must be comparisons/boolean logic (no assignment) — hoist
  real computation into a script task before the gateway.
