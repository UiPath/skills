---
name: uipath-maestro-case
description: "TRIGGER for authoring UiPath Maestro Case plans as `<Name>.case.ts` with the reference-mode TypeScript builder SDK (`@uipath/flow-sdk/case`), compiling to `caseplan.json`, and running the `uip maestro case` check/compile/validate loop. Covers stages, tasks, rules, bindings, published-resource references, and brownfield decompile/edit/recompile. Flow builder authoring → uipath-maestro-flow; structural-core BPMN → uipath-maestro-bpmn. DO NOT TRIGGER for C#/XAML automation → uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance: snapshot of UiPath/flow-builder-sdk
`typescript/sdk/skill/SKILL-case.md` @ ddf9da1. Canonical source lives there;
edit upstream and re-sync (see UiPath/flow-builder-sdk#405).

This is a snapshot of a generated file. In flow-builder-sdk,
`typescript/sdk/scripts/gen-case-skill.mjs` renders it from
`typescript/sdk/skill/SKILL-case.template.md` and the built `.d.ts`; edits
belong upstream.
-->
# UiPath Case Management — TypeScript Builder SDK (reference-mode)

Author a UiPath **Case plan** by writing TypeScript that builds a hierarchy of
**stages** and **tasks**, then serialize it to a `caseplan.json` (schema
**V20**). Like the Flow builder, this is a *builder*, not a program: you declare
the case's shape by calling methods, and flow between stages is expressed with
**conditions** (`rule(...)`), not edges — a case plan has **no edges**.

> `casePlan(...)` is the entry point, **not** `case(...)` — `case` is a reserved
> word in JavaScript/TypeScript.

This is **reference-mode**: a task points at an *already-published*
process/agent/rpa/workflow by name + folder. (Embedding an inline flow/bpmn body
in a task is a later phase.)

Exact function signatures and option shapes, including every builder method
(`CaseBuilder`, `StageBuilder`, `TaskBuilder`):
[`references/api.md`](references/api.md).

## Authoring

```ts
import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('loan-approval')
  .name('Loan Approval')
  .identifier('LOAN')                       // metadata.caseIdentifier (constant)

  .stage('Review', s => s
    .required()
    .entryWhen(rule('case-entered'), { displayName: 'Case entered' })
    .exitWhen(rule('required-tasks-completed'), { displayName: 'All done', marksStageComplete: true })
    .task('Check Policy', t => t
      .process('check-policy', { folder: 'Shared' })   // reference a published process
      .required()
      .entryWhen(rule('current-stage-entered')))
    .task('Manager Approval', t => t
      .action({ title: 'Approve loan', priority: 'High', recipient: 'manager@corp.com' })
      .entryWhen(rule('selected-tasks-completed', { tasks: ['Check Policy'] }))))

  .stage('Decision', s => s
    .required()
    .entryWhen(rule('selected-stage-completed', { stage: 'Review' }), { displayName: 'After review' })
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Notify', t => t.process('notify').required().entryWhen(rule('current-stage-entered'))))

  .completeWhen(rule('required-stages-completed'), { displayName: 'Case resolved' })
  .build();
```

> **Import from `@uipath/flow-sdk/case`.** It has everything you need:
> `casePlan`, `rule`, `escalation`, `toUser`, `toGroup`, `manualTrigger`,
> `timerTrigger`, and `eventTrigger`. The installed package carries its runtime
> dependencies and exposes this stable subpath directly.

For a file-based authoring loop, use the CLIs (see **Compile & check** below):

```bash
uip maestro case check <Name>.case.ts --source  # fast source validation (no output)
uip maestro case compile <Name>                 # <Name>.case.ts → caseplan.json
uip maestro case validate caseplan.json --output json
```

> `uip maestro case check caseplan.json --compiled` intentionally points to
> `uip maestro case validate`: the SDK has a source checker today, while the
> product CLI owns compiled-artifact validation.

## Builder methods

### `casePlan(id)` — case-level builder

<!-- GEN:case-builder -->

```ts
/**
 * Start building a case plan with the given id. (`casePlan`, not `case` — reserved word.)
 *
 * @param id - The plan's stable identifier.
 * @returns A {@link CaseBuilder} to declare stages and tasks on.
 */
export declare function casePlan(id: string): CaseBuilder;

/**
     * Set the case plan's display name.
     *
     * @param n - The name the designer shows.
     * @returns This builder, so calls chain.
     */
    name(n: string): this;

/**
     * Set the runtime case identifier (constant prefix, or an `=`-expression when type is `external`).
     *
     * @param id - The prefix, or an `=`-expression when `type` is `'external'`.
     * @param type - `'constant'` for a fixed prefix, `'external'` to compute it.
     * @returns This builder, so calls chain.
     */
    identifier(id: string, type?: 'constant' | 'external'): this;

/**
     * Describe the case plan.
     *
     * @param text - Prose the designer shows alongside the plan.
     * @returns This builder, so calls chain.
     */
    description(text: string): this;

/**
     * Turn the generated Case App on or off.
     *
     * @param enabled - Whether the plan ships a Case App.
     * @returns This builder, so calls chain.
     */
    caseApp(enabled?: boolean): this;

/**
     * Declare a read/write case variable.
     *
     * @remarks
     * Readable from a `=js:vars.<name>` expression, like a trigger-bound In-arg.
     *
     * This comment used to say the opposite — that only `.input(shape, { from })`
     * could be read, and that a bare `.var()` failed `uip maestro case validate`
     * with "Variable 'vars.<name>' does not exist". That was true when written and
     * stopped being true at #257, which made the serializer emit the `inputOutputs`
     * companion (`id: <name>`, `elementId: "root"`) the platform resolves
     * `vars.<name>` against. `check` carried a matching `VAR_NOT_REFERENCEABLE`
     * error and dropped it for the same reason.
     *
     * Binding is about WHEN a value arrives, not whether it can be read. An
     * UNDECLARED `vars.<x>` is still a hard error, thrown by `.build()`.
     *
     * @param name - The variable's name; read it as `=vars.<name>`.
     * @param type - A `types.*` descriptor, or {@link jsonSchema} for a structured one.
     * @param defaultValue - Its initial value. Omit it to start unset.
     * @returns This builder, so calls chain.
     */
    var(name: string, type: TypeDesc | JsonSchemaType, defaultValue?: unknown): this;

/**
     * Declare case In-args. Each value is a {@link TypeDesc}, or `{ type, default }`
     * to set a default. Pass `{ from: <trigger> }` to bind the args to a trigger —
     * their value arrives when it fires, readable as `=vars.<name>` — and they are
     * projected into that trigger's `entry-points.json` input schema. A declared
     * In-arg is readable as `=vars.<name>` (its `inputOutputs` companion resolves it).
     *
     * @example
     * **Bind case In-args to a trigger's payload**
     * ```ts
     * const t = manualTrigger();
     * casePlan('x').trigger(t)
     *   .input({ claimId: 'string', riskScore: { type: 'float', default: '1.5' } }, { from: t })
     * ```
     *
     * @param shape - In-arg names to types, or `{ type, default }`.
     * @param opts - `{ from: <trigger> }` binds the args to a trigger's payload.
     * @returns This builder, so calls chain.
     */
    input(shape: Record<string, TypeDesc | JsonSchemaType | {
        type: TypeDesc;
        default?: unknown;
        body?: unknown;
    }>, opts?: {
        from?: BuiltTrigger;
    }): this;

/**
     * Declare case Out-args. Each value is a {@link TypeDesc}, or `{ type, default }`
     * to set a default. Out-args are readable as `=vars.<name>` and projected into
     * every trigger's `entry-points.json` output schema (with their default).
     *
     * @param shape - Out-arg names to types, or `{ type, default }`.
     * @returns This builder, so calls chain.
     */
    output(shape: Record<string, TypeDesc | JsonSchemaType | {
        type: TypeDesc;
        default?: unknown;
        body?: unknown;
    }>): this;

/**
     * Add a primary stage. `fn` receives a stage sub-builder.
     *
     * @param label - The stage's display name.
     * @param fn - Receives a sub-builder for the stage's tasks and conditions.
     * @returns This builder, so calls chain.
     */
    stage(label: string, fn: (s: StageBuilder) => void): this;

/**
     * Add a secondary/exception stage (`case-management:ExceptionStage`).
     *
     * @param label - The stage's display name.
     * @param fn - Receives a sub-builder for the stage's tasks and conditions.
     * @returns This builder, so calls chain.
     */
    exceptionStage(label: string, fn: (s: StageBuilder) => void): this;

/**
     * Add a case-completion rule (`metadata.caseExitRules`, `marksCaseComplete: true` by default).
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName`, and whether meeting it completes the case.
     * @returns This builder, so calls chain.
     */
    completeWhen(rules: CaseRule | CaseRule[], opts?: {
        displayName?: string;
        marksCaseComplete?: boolean;
    }): this;

/**
     * Set a case-level SLA (deadline + escalations for the whole case), emitted to
     * `metadata.slaRules`. Call more than once for conditional SLAs; the default
     * (no `when`) must be last.
     *
     * @param opts - The deadline, its escalations, and an optional `when` gate.
     * @returns This builder, so calls chain.
     */
    sla(opts: SlaOpts): this;

/**
     * Add a case trigger (what starts the case). Call more than once for
     * multiple triggers; the first is the primary. Omit entirely for the default
     * single manual trigger. Build specs with {@link manualTrigger}/{@link timerTrigger}.
     *
     * @param t - A trigger from `manualTrigger` / `timerTrigger` / `eventTrigger`.
     * @returns This builder, so calls chain.
     */
    trigger(t: BuiltTrigger): this;

/**
     * Finish the plan and return the description the serializer writes.
     *
     * @returns The built case — its stages, tasks, triggers and variables.
     */
    build(): BuiltCase;

export type TypeDesc = (typeof types)[keyof typeof types];

export interface CaseVarDecl {
    name: string;
    type: TypeDesc;
    direction: 'in' | 'out' | 'inout';
    default?: unknown;
    /** For `type: 'jsonSchema'` — the structured var's JSON-schema `body`. */
    body?: unknown;
    /**
     * In-args only: the trigger this argument is bound to (its value arrives when
     * that trigger fires). Set via `.input(shape, { from })`. When present, the arg
     * emits the full three-entry binding (formal slot + companion + trigger-output
     * bridge); when absent it stays a bare declaration.
     */
    sourceTrigger?: BuiltTrigger;
}

/**
 * Declare a structured (object/array) variable type. Pass the JSON schema — object
 * vs array is `body.type`. Use in `.var()`/`.input()`/`.output()` where a
 * {@link TypeDesc} is expected.
 *
 * @example
 * **Declare an object variable and an array variable**
 * ```ts
 * .var('caseData', jsonSchema({ type: 'object', properties: { status: { type: 'string' } } }))
 * .var('attachments', jsonSchema({ type: 'array', items: { type: 'string' } }))
 * ```
 *
 * @param body - The JSON schema. Its `type` decides object vs array.
 * @returns A type descriptor for `.var()` / `.input()` / `.output()`.
 */
export declare function jsonSchema(body: unknown): JsonSchemaType;

/**
 * A structured (object/array) variable type + its JSON-schema `body`, as returned
 * by {@link jsonSchema}. Persists as `type: 'jsonSchema'` with the object/array
 * shape carried in `body.type`.
 */
export interface JsonSchemaType {
    type: 'jsonSchema';
    body: unknown;
}
```

<!-- /GEN:case-builder -->

### stage (`s`)

<!-- GEN:stage-builder -->

```ts
/**
     * Describe this stage.
     *
     * @param text - Prose the designer shows on the stage.
     * @returns This builder, so calls chain.
     */
    description(text: string): this;

/**
     * Mark this stage required, so the case cannot complete without it.
     *
     * @param value - Whether the stage is required.
     * @returns This builder, so calls chain.
     */
    required(value?: boolean): this;

/**
     * Add a stage-entry condition (OR-group). Pass an array of rules for an AND-group.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName`, and the entry behaviour flags.
     * @returns This builder, so calls chain.
     */
    entryWhen(rules: CaseRule | CaseRule[], opts?: EntryOpts): this;

/**
     * Add a stage-exit condition (OR-group). Pass an array of rules for an AND-group.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName`, and whether meeting it completes the stage.
     * @returns This builder, so calls chain.
     */
    exitWhen(rules: CaseRule | CaseRule[], opts?: ExitOpts): this;

/**
     * Add a task. `fn` receives a task sub-builder. `lane` selects a parallel lane (default 0).
     *
     * @param displayName - The task's display name.
     * @param fn - Receives a sub-builder for what the task does.
     * @param opts - `lane` places the task in a parallel lane (default 0).
     * @returns This builder, so calls chain.
     */
    task(displayName: string, fn: (t: TaskBuilder) => void, opts?: {
        lane?: number;
    }): this;

/**
     * Set an SLA (deadline + escalations) on this stage. Call more than once for
     * conditional SLAs (each with a `when` gate); the default SLA (no `when`) must
     * be last.
     *
     * @param opts - The deadline, its escalations, and an optional `when` gate.
     * @returns This builder, so calls chain.
     */
    sla(opts: SlaOpts): this;

/** Options common to a stage/task entry condition. */
export interface EntryOpts {
    displayName?: string;
    isInterrupting?: boolean;
}

/** Options for `stage.exitWhen(rules, opts)` — one call per outcome. */
export interface ExitOpts {
    displayName?: string;
    /** Mark the stage complete on this exit. Every stage needs at least one. */
    marksStageComplete?: boolean;
    /**
     * `wait-for-user` holds the case until a person chooses the onward path — use it
     * when the process must not advance by itself. See {@link StageExitType}.
     */
    type?: StageExitType;
    /**
     * Route this exit to a named stage (a stage LABEL). For multi-way branching give
     * the stage one `.exitWhen(...)` per outcome, each with its own rules and
     * `exitToStage` — including backward edges (returning to an earlier stage is just
     * an exit that routes there).
     *
     * @remarks
     * The destination still evaluates its own `entryWhen(...)`, and only
     * STAGE-ENTRY rules are legal there: `selected-stage-completed` /
     * `selected-stage-exited` / `user-selected-stage` / `case-entered`. Do NOT try to
     * gate a destination on `selected-tasks-completed` — that is a task-entry /
     * stage-exit rule, and `uip maestro case validate` rejects it at stage entry with
     * "task selection missing" (`check` now catches this as RULE_PLACEMENT).
     *
     * Consequence for >2-way branching: `selected-stage-completed`/`-exited` name only
     * the SOURCE stage, so sibling branches out of one stage cannot be told apart by
     * the destination's entry rule alone. The workable pattern is to let exactly ONE
     * exit carry `marksStageComplete: true` (the success path, matched by
     * `selected-stage-completed`) and gate the others on `selected-stage-exited`; for
     * a human-chosen path use `type: 'wait-for-user'` here plus a
     * `user-selected-stage` entry on each destination.
     */
    exitToStage?: string;
}

export type StageExitType = 'exit-only' | 'wait-for-user' | 'return-to-origin';
```

<!-- /GEN:stage-builder -->

### task (`t`) — set exactly one kind, then envelope options

<!-- GEN:task-builder -->

```ts
export type TaskKind = 'process' | 'agent' | 'rpa' | 'api-workflow' | 'case-management' | 'action' | 'connector' | 'wait-for-timer' | 'wait-for-connector';

/**
     * Reference a published Maestro process.
     *
     * @param name - The published process's name.
     * @param opts - `folder` — the Orchestrator folder it lives in.
     * @returns This builder, so calls chain.
     */
    process(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * Reference a published agent.
     *
     * @param name - The published agent's name.
     * @param opts - `folder` — the Orchestrator folder it lives in.
     * @returns This builder, so calls chain.
     */
    agent(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * Reference a published RPA process.
     *
     * @param name - The published RPA process's name.
     * @param opts - `folder` — the Orchestrator folder it lives in.
     * @returns This builder, so calls chain.
     */
    rpa(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * Reference a published API workflow.
     *
     * @param name - The published API workflow's name.
     * @param opts - `folder` — the Orchestrator folder it lives in.
     * @returns This builder, so calls chain.
     */
    apiWorkflow(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * Reference another published case (a **sub-case**). Pass data into the child
     * with `.inputs({...})` and read results back with `.outputs({...})` — the same
     * io-binding as reference-mode tasks.
     *
     * @param name - The published child case's name.
     * @param opts - `folder` — the Orchestrator folder it lives in.
     * @returns This builder, so calls chain.
     */
    caseManagement(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * An Action Center human task. `recipient` may be an email (→ Type 2) or
     * `{ type, value }`. `inputs`/`outputs` declare the task's form fields — inputs
     * are read-only context the assignee sees, outputs are what they fill in.
     * `labels` and `actionCatalogName` tag the task and name its action app.
     *
     * @param spec - The human task: its `title`, `priority`, `recipient`, and the `inputs` / `outputs` its form shows and collects.
     * @returns This builder, so calls chain.
     */
    action(spec?: {
        title?: string;
        priority?: 'Low' | 'Medium' | 'High' | 'Critical';
        recipient?: string | {
            type: RecipientType;
            value: string;
        };
        labels?: string;
        actionCatalogName?: string;
        inputs?: ActionField[];
        outputs?: ActionField[];
    }): this;

/**
     * Stringly form, for a connector with no prepared module.
     *
     * @param key - The connector library key, e.g. `'uipath-salesforce-slack'`.
     * @param action - The operation id, e.g. `'send-message-to-channel'`.
     * @param inputs - The activity's inputs.
     * @param opts - Symbolic `connection` / `folder`, an action `version`, and the
     * `object` a generic operation addresses.
     * @returns This builder, so calls chain.
     */
    connector(key: string, action: string, inputs?: Record<string, unknown>, opts?: ConnectorOpts): this;

/**
     * A wait-for-timer task (ISO-8601 `duration`, ISO `date`, or repeating `cycle`).
     *
     * @param spec - How long to wait: an ISO-8601 `duration`, a `date`, or a repeating `cycle`.
     * @returns This builder, so calls chain.
     */
    waitForTimer(spec?: TimerSpecData): this;

/**
     * A wait-for-connector task — suspend the stage until an Integration Service
     * **event** fires. Omit the spec (or `connectorKey`/`operation`) for a
     * **placeholder** (a connector not yet registered): `data.uipath` carries only
     * `serviceType: "Intsvc.WaitForEvent"`. Naming the connector/operation emits the
     * `context` subscription. (A fully *resolved* subscription — real
     * connection/typeId — needs live connector resolution and is out of scope.)
     *
     * @param spec - The event to wait for. Omit it, or its `connectorKey` / `operation`, for a placeholder to fill in later.
     * @returns This builder, so calls chain.
     */
    waitForConnector(spec?: WaitConnectorSpec): this;

/**
 * A `wait-for-connector` subscription: suspend on an Integration Service event.
 * Omit `connectorKey`/`operation` for a bare **placeholder** (for a connector not
 * yet registered — `data.uipath` carries only `serviceType`).
 */
export interface WaitConnectorSpec {
    /** Connector key, e.g. `uipath-microsoft-outlook365`. */
    connectorKey?: string;
    /** Event operation, e.g. `EMAIL_RECEIVED`. */
    operation?: string;
}

/**
     * Mark this task required, so its stage cannot complete without it.
     *
     * @param value - Whether the task is required.
     * @returns This builder, so calls chain.
     */
    required(value?: boolean): this;

/**
     * Run this task at most once, even if its entry condition is met again.
     *
     * @param value - Whether the task runs only once.
     * @returns This builder, so calls chain.
     */
    runOnce(value?: boolean): this;

/**
     * Describe this task.
     *
     * @param text - Prose the designer shows on the task.
     * @returns This builder, so calls chain.
     */
    description(text: string): this;

/**
     * Skip this task when the `=js:` expression is truthy.
     *
     * @param expression - An `=js:` expression; the task is skipped when it is truthy.
     * @returns This builder, so calls chain.
     */
    skipWhen(expression: string): this;

/**
     * Bind resource **input** parameters (reference-mode tasks). Each key is a
     * declared input parameter name; each value is a literal, a case-variable read
     * `=vars.<name>`, or a `=js:` expression. Pass `{ value, type }` to set a
     * non-string type (default `string`).
     *
     * @param shape - Input parameter names to literals, case-variable references, or `{ value, type }`.
     * @returns This builder, so calls chain.
     */
    inputs(shape: Record<string, string | {
        value: string;
        type?: TypeDesc;
    }>): this;

/**
     * Extract fields of the task's **result** into case variables (reference-mode
     * tasks). Each key is the case-variable name a later task/condition reads as
     * `=vars.<name>`; each value is the source field expression (e.g. `=response`,
     * `=Error.Message`). Pass `{ source, type }` to set a non-string type. Emits a
     * `data.outputs[]` row plus a root `inputOutputs` companion so the name resolves.
     *
     * @param shape - Case-variable names to the result field they take, or `{ source, type }`.
     * @returns This builder, so calls chain.
     */
    outputs(shape: Record<string, string | {
        source: string;
        type?: TypeDesc;
    }>): this;

/**
     * Add a task-entry condition (OR-group). Pass an array of rules for an AND-group.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName` for the condition.
     * @returns This builder, so calls chain.
     */
    entryWhen(rules: CaseRule | CaseRule[], opts?: {
        displayName?: string;
    }): this;

export interface ActionSpecData {
    title?: string;
    priority?: 'Low' | 'Medium' | 'High' | 'Critical';
    recipient?: {
        type: RecipientType;
        value: string;
    };
    /** Action Center labels (persisted as a single `data.labels` string). */
    labels?: string;
    /** The Action Center action-app / catalog this task instantiates. */
    actionCatalogName?: string;
    /** Read-only context fields the assignee sees (`data.inputs[]`). */
    inputs?: ActionField[];
    /** Fields the assignee fills in (`data.outputs[]`). */
    outputs?: ActionField[];
}

/**
 * One field of an Action Center task's form. **Inputs** are read-only context the
 * assignee sees; **outputs** are the values they fill in. Emitted as a schema
 * `InputOutput` row (`{ name, type, displayName? }`) under `data.inputs[]` /
 * `data.outputs[]`.
 *
 * @remarks
 * Note: no `required` flag — on a task's io row `required` means "must hold a
 * value now", which `uip maestro case validate` rejects as an empty required
 * field at author time. Whether the assignee must fill a field is governed by the
 * resolved action app's own form schema; here the reviewer-must-fill semantic is
 * carried by the input (context) vs output (fill-in) split itself.
 */
export interface ActionField {
    /** Field key. */
    name: string;
    /** Field type (default `string`). */
    type?: TypeDesc;
    /** Human-facing label (defaults to `name` in the UI when omitted). */
    displayName?: string;
}

/**
 * Action-task recipient type. `2` = a single user by email — the only value the
 * platform corpus exercises for case action tasks; `0`/`1`/`3` are reserved for
 * other assignee kinds. A bare email string on `.action({ recipient })` becomes
 * `{ type: 2, value: email }`.
 */
export type RecipientType = 0 | 1 | 2 | 3;

export interface TimerSpecData {
    duration?: string;
    date?: string;
    cycle?: string;
}
```

<!-- /GEN:task-builder -->

### Task io-binding — pass inputs, capture outputs

Reference-mode tasks (`process`/`agent`/`rpa`/`api-workflow`, and
`case-management` sub-cases) can bind input parameters and extract result fields
into readable case variables, so a later task or a `=vars.<name>` gate consumes a
task's result:

```ts
.task('Lookup age', t => t
  .apiWorkflow('NameToAge', { folder: 'Shared' })
  .inputs({ name: 'Ada', threshold: { value: '10', type: 'number' } }) // literal / typed
  .outputs({ estimatedAge: { source: '=age', type: 'number' } })       // field → case variable
  .entryWhen(rule('current-stage-entered')))
// downstream — read it by its friendly name:
.task('Notify', t => t
  .process('Notifier', { folder: 'Shared' })
  .inputs({ age: '=vars.estimatedAge' })
  .skipWhen('=js:vars.estimatedAge > 65')
  .entryWhen(rule('current-stage-entered')))
```

- `.inputs({ param: value })` — `value` is a literal, a `=vars.<name>` read, or a
  `=js:` expression. `{ value, type }` sets a non-`string` type.
- `.outputs({ caseVar: source })` — the **key** is the case-variable name read
  downstream as `=vars.<caseVar>`; `source` is the result field (`=response`,
  `=Error.Message`). `{ source, type }` sets a non-`string` type. Each output
  registers a readable companion, and `build()` knows the name (a gate reading it
  passes the expression check).

A **sub-case** (`.caseManagement(name, { folder })`) uses the same binding to pass
data into the child case and read its results back:

```ts
.task('Track Payment', t => t
  .caseManagement('PaymentTracking', { folder: 'Shared' })
  .inputs({ invoiceId: '=vars.invoiceId', amount: { value: '250', type: 'number' } })
  .outputs({ paymentStatus: { source: '=status', type: 'string' } })  // read downstream as =vars.paymentStatus
  .entryWhen(rule('current-stage-entered')))
```

### Action Center tasks — form fields, labels, action app

`.action({ ... })` is a human task. Beyond `title` / `priority` / `recipient`
(an email → recipient Type 2), it takes:

```ts
.task('Approve expense', t => t
  .action({
    title: 'Review this expense reimbursement',
    priority: 'Medium',
    recipient: 'finance-approvals@corp.com',
    labels: 'finance',                     // a single string (not a list)
    actionCatalogName: 'Expense Review',   // the action app this task instantiates
    inputs: [                              // read-only context the assignee SEES
      { name: 'employeeName', type: 'string', displayName: 'Employee' },
      { name: 'amount', type: 'number', displayName: 'Amount' },
    ],
    outputs: [                             // fields the assignee FILLS IN
      { name: 'approved', type: 'boolean' },
      { name: 'comment', type: 'string' },
    ],
  })
  .required()
  .entryWhen(rule('current-stage-entered')))
```

- **`inputs` vs `outputs`** is the reviewer-must-fill split: inputs are shown
  read-only, outputs are what they submit. Each is `{ name, type?, displayName? }`
  (`type` defaults to `string`).
- There is deliberately **no `required` flag** on a field — on a task io row
  `required` means "must already hold a value", which `uip maestro case validate`
  rejects as an empty required field at author time. Model mandatory-ness with the
  input/output split, not a flag.

### wait-for-connector — suspend on an Integration Service event

Two forms, both emitting `serviceType: "Intsvc.WaitForEvent"`:

```ts
// as a TASK node — suspends the stage until the event fires:
.task('Wait for reply', t => t
  .waitForConnector({ connectorKey: 'uipath-microsoft-outlook365', operation: 'EMAIL_RECEIVED' })
  .required().entryWhen(rule('current-stage-entered')))
// as a task/stage-entry RULE — the task activates when the event fires:
.task('Process reply', t => t
  .process('Handler', { folder: 'Shared' })
  .entryWhen(rule('wait-for-connector', { connector: { connectorKey: 'uipath-microsoft-outlook365', operation: 'EMAIL_RECEIVED' } })))
```

Omit `connectorKey`/`operation` for a **placeholder** (a connector not yet
registered) — a task's `data.uipath` is then `serviceType` only; a rule still
carries a `uipath` bag (a bare rule is rejected by `validate`). A fully *resolved*
subscription (real connection / typeId) needs live connector resolution and is not
authored offline.

## Conditions — `rule(type, opts?)`

Combine rules into an **AND-group** by passing an array to
`entryWhen`/`exitWhen`/`completeWhen`; call those methods multiple times for
**OR-groups** (DNF).

<!-- GEN:conditions -->

```ts
/**
 * Declare a condition rule. Combine rules into AND-groups by passing an array to
 * `entryWhen`/`exitWhen`/etc.; call those methods multiple times for OR-groups.
 *
 * @param type - Which condition, e.g. `'case-entered'` or `'selected-tasks-completed'`.
 * @param opts - What the rule needs, e.g. the `tasks` a task-completion rule waits on.
 * @returns A rule to pass to `entryWhen` / `exitWhen` / `completeWhen`.
 */
export declare function rule(type: CaseRuleType, opts?: RuleOpts): CaseRule;

export type CaseRuleType = 'case-entered' | 'required-tasks-completed' | 'required-stages-completed' | 'selected-stage-completed' | 'selected-stage-exited' | 'selected-tasks-completed' | 'current-stage-entered' | 'adhoc' | 'runs-sequentially' | 'user-selected-stage' | 'wait-for-connector' | 'sla-status-change';

export interface RuleOpts {
    /**
     * Symbolic stage label (for `selected-stage-completed` / `selected-stage-exited`).
     *
     * @remarks
     * Both rules serialize identically — to `selectedStageId` — so this SDK draws no
     * distinction between them; the difference is interpreted at runtime. Use
     * `selected-stage-exited` for an interrupting exception-stage entry (what the
     * shipped example does) and `selected-stage-completed` when you mean the stage
     * finished normally.
     */
    stage?: string;
    /**
     * Task references for `selected-tasks-completed`. Resolved **case-wide, not
     * per-stage** — a rule in one stage may reference a task in another.
     *
     * @remarks
     * Two forms:
     * - bare `'Task Name'` — the normal form.
     * - qualified `'<Stage Label>/<Task Name>'` — also accepted, and clearer when a
     *   name's stage is not obvious from context.
     *
     * Task names must be UNIQUE CASE-WIDE: `uip maestro case validate` rejects
     * duplicates outright ("Task name 'X' is duplicate"), and `check` now flags them
     * as DUP_TASK. Names that naturally recur across stages ("Withdraw Request",
     * "Reject") must be qualified at the source, e.g. `'Withdraw Request (Counsel)'`.
     */
    tasks?: string[];
    /**
     * For a `wait-for-connector` rule — the connector event to suspend on. Omit for
     * a placeholder (both fields default to `"placeholder"`). Emits the rule's
     * `uipath` subscription bag (`serviceType: "Intsvc.WaitForEvent"` + a `context`
     * naming the connector/operation).
     */
    connector?: WaitConnectorSpec;
    /**
     * For a `sla-status-change` rule — the **displayName of the SLA** whose status
     * change fires this rule (react to a deadline breach / at-risk). Declare the SLA
     * with that `displayName` via `.sla({ displayName, … })`; resolved to `slaId`.
     */
    sla?: string;
    /**
     * For an **at-risk** `sla-status-change` rule — the displayName of the escalation
     * (declared on the referenced SLA, `trigger: 'at-risk'`) that fires it. Omit for
     * a **breach** rule (`slaId` alone). Resolved to `escalationId`.
     */
    escalation?: string;
    /** A `=js:` gate on case state (for `adhoc`, or as an extra guard on any rule). */
    expression?: string;
}
```

<!-- /GEN:conditions -->

Rule **placement** (which the types cannot express):

| Rule | Legal position |
| --- | --- |
| `case-entered` | stage entry (case start) |
| `current-stage-entered` | task entry |
| `required-tasks-completed` | stage exit |
| `required-stages-completed` | case completion |
| `selected-stage-completed` / `selected-stage-exited` | stage entry (needs `{ stage }`) |
| `selected-tasks-completed` | task entry / stage exit ONLY (needs `{ tasks }`) — **illegal at stage entry**, `uip` rejects it with "task selection missing" |
| `user-selected-stage` | stage entry (with a `wait-for-user` exit elsewhere) |
| `adhoc` | task entry, **and stage entry**. `{ expression }` is **optional** — bare `rule('adhoc')` is Valid (verified). Add an expression only to gate availability on case state. |
| `runs-sequentially` | task entry |

`stage`/`tasks` references use the **labels/names you gave** in the builder; the
serializer resolves them to the generated ids.

## Rules the validator enforces (common gotchas)

- **Every task needs an entry rule** — add `.entryWhen(rule('current-stage-entered'))`
  (or another task-entry rule). A task with no entry condition is an error.
- **`required-tasks-completed` needs a required task** in that stage — mark at
  least one task `.required()`.
- **A case needs a completion rule** — call `.completeWhen(...)` (normally
  `required-stages-completed`), or validation fails with "Case has no completion rules".
- **A stage needs a completion/exit rule** — give each stage an `.exitWhen(...,
  { marksStageComplete: true })`.
- Reference-mode task `data.name`/`folderPath` are **literal strings**. Top-level
  `bindings` stays `[]` **unless** a `.connector(...)` task is present — those emit
  `=bindings.<id>` refs and populate the root `bindings[]` (see below).

## On-demand actions — `rule('adhoc')`

A task whose entry rule is `adhoc` is **not part of the sequence**. It becomes
available when its stage is active and is taken only if someone judges it
necessary — "attach another document", "ask the requester a question", "order an
outside opinion", "withdraw the request". Requirements phrased as *"the people on a
case must be able to do X whenever they need to, but only while phase P is
active"* are `adhoc` tasks in stage P; they are **not** extra sequenced steps and
not a separate stage.

```ts
import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('contract-review')
  .name('ContractReview').identifier('CR')
  .stage('Counsel Review', s => s
    .required()
    .entryWhen(rule('case-entered'))
    // sequenced work — gates the exit
    .task('Review contract', t => t.action({ title: 'Review and decide' })
      .required().entryWhen(rule('current-stage-entered')))
    // on-demand: available while this stage is active, taken only if needed.
    // NOT .required() — a required task must complete before the stage can exit.
    .task('Ask business team a question', t => t
      .action({ title: 'Ask the requester a question' })
      .entryWhen(rule('adhoc'), { displayName: 'On demand while counsel has the contract' }))
    .task('Order outside opinion', t => t
      .action({ title: 'Order an outside-firm opinion' })
      .entryWhen(rule('adhoc'), { displayName: 'On demand while counsel has the contract' }))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed'))
  .build();
```

(Verified: this exact plan compiles and `uip maestro case validate` returns
`Status: Valid` with no warnings.)

- **Scoping is automatic.** An `adhoc` task is reachable only while its own stage is
  active — that is what "only while phase P is active" means. No extra guard needed.
- **Never `.required()` an `adhoc` task.** `required-tasks-completed` would then wait
  for an action that may never be taken, and the stage could not exit.
- `{ expression }` is optional; add one (`rule('adhoc', { expression: '=js:…' })`) only
  to further gate availability on case state.
- The same action offered in several stages needs a **distinct name per stage**
  ("Withdraw Request (Counsel)"), since task names must be unique case-wide.

## `skipWhen` and the exit gates — a known unknown

`.skipWhen('=js:…')` marks a task skipped when the expression is truthy — the usual
way to express "contracts under $25,000 are approved automatically". It compiles and
validates.

> **Unverified:** whether a skipped task counts as *completed* for a downstream
> `selected-tasks-completed` or `required-tasks-completed` exit rule is **not
> settled**. `uip maestro case validate` is a schema/structure check, not a runtime
> engine, so it cannot answer this — a plan that gates a stage exit on a task that
> gets skipped may validate and still stall at runtime. If a value-tier
> auto-approval path matters, confirm it on a live case run before relying on it, or
> avoid the dependency: give the stage a **separate exit** for the auto-approve path
> (its own `exitWhen` with the `=js:` value test) instead of gating on the skipped
> task.

## Exception (secondary) stages

Use `.exceptionStage(label, s => …)` for a stage that interrupts the main flow
(e.g. handle a rejection). It's entered by an **interrupting** entry condition
that references the primary stage — pass `{ isInterrupting: true }` to
`.entryWhen(...)`, and give the condition a `displayName`:

```ts
export default casePlan('order-review')
  .name('OrderReview').identifier('OR')
  .stage('Review', s => s
    .required()
    .entryWhen(rule('case-entered'))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Check order', t => t.process('check-order', { folder: 'Shared' })
      .required().entryWhen(rule('current-stage-entered'))))
  .exceptionStage('Handle Rejection', s => s
    .entryWhen(rule('selected-stage-exited', { stage: 'Review' }),
               { isInterrupting: true, displayName: 'On review exit' })
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Escalate', t => t.agent('rejection-agent', { folder: 'Shared' })
      .required().entryWhen(rule('current-stage-entered'))))
  .completeWhen(rule('required-stages-completed'))
  .build();
```

> **Expect one benign warning.** `uip maestro case validate` prints
> `Entry rule "…" has no matching stage rule` for the interrupting entry (the
> referenced stage has no reciprocal rule). It is a **warning, not an error** —
> `Status` stays `Valid` and `uip maestro case compile` succeeds. Don't chase it; a
> `displayName` on the condition just makes the message legible.

## Triggers

<!-- GEN:triggers -->

```ts
/**
 * A manual (user-initiated) case trigger.
 *
 * @param opts - Display name and other trigger metadata.
 * @returns A trigger to pass to `.trigger(...)`.
 */
export declare function manualTrigger(opts?: ManualTriggerOpts): BuiltTrigger;

export interface ManualTriggerOpts {
    name?: string;
    description?: string;
}

/**
 * A timer (scheduled) case trigger. `every` is an ISO-8601 repeating interval.
 *
 * @param opts - The schedule — `every`, as an ISO-8601 repeating interval.
 * @returns A trigger to pass to `.trigger(...)`.
 */
export declare function timerTrigger(opts: TimerTriggerOpts): BuiltTrigger;

export interface TimerTriggerOpts {
    /**
     * The schedule, as an
     * {@link https://docs.digi.com/resources/documentation/digidocs/90001488-13/reference/r_iso_8601_duration_format.htm | ISO-8601 repeating interval}
     * (emitted verbatim as
     * `timeCycle`): `R/PT1H` (every hour, unbounded), `R5/P1D` (5 times, daily), or
     * bounded-with-start `R5/2026-04-26T09:00:00Z/P1D` (5 times, daily from that
     * instant). `R` = repeat, `R<n>` = repeat n times.
     */
    every: string;
    name?: string;
    description?: string;
}

/**
 * An Integration Service **event** trigger — an external event (a new row, an
 * email, a webhook) starts the case. Emits `data.uipath.serviceType:
 * "Intsvc.EventTrigger"`; payload fields map onto its `outputs[]`.
 *
 * @param opts - The connector event to subscribe to, and its connection.
 * @returns A trigger to pass to `.trigger(...)`.
 */
export declare function eventTrigger(opts?: EventTriggerOpts): BuiltTrigger;

export interface EventTriggerOpts {
    name?: string;
    description?: string;
    /**
     * Optional event-payload extractions. Each key is a case-variable name read
     * downstream as `=vars.<name>`; each value is the payload field expression
     * (`=response.<field>`). Pass `{ source, type }` for a non-`string` type. Each
     * emits a trigger `outputs[]` row plus a readable root `inputOutputs` companion.
     *
     * @remarks
     * With **no** outputs the event trigger is a **placeholder** (`data.uipath`
     * carries only `serviceType`) — the offline shape for an event on a connector
     * not yet registered; attach the real connection after registering it.
     */
    outputs?: Record<string, string | {
        source: string;
        type?: TypeDesc;
    }>;
}

export interface BuiltTrigger {
    kind: CaseTriggerKind;
    /** Node label (defaults to `Trigger <n>` at serialize when omitted). */
    name?: string;
    description?: string;
    /** Timer only: an ISO-8601 repeating interval (see {@link TimerTriggerOpts.every}). */
    timeCycle?: string;
    /** Event only: payload-field extractions onto the trigger's `outputs[]` (see {@link EventTriggerOpts.outputs}). */
    eventOutputs?: TaskOutputBinding[];
}

export type CaseTriggerKind = 'manual' | 'timer' | 'event';
```

<!-- /GEN:triggers -->

A case starts at its **first stage's `case-entered` entry** — the trigger nodes are
what the platform subscribes to fire that start (edges stay `[]`). Every case has
at least one trigger; **omit `.trigger(...)` entirely for the default single manual
trigger** (what all the examples above do). Declare triggers to add a schedule or
extra entry points — all of them start the same first stage:

```ts
import { casePlan, rule, manualTrigger, timerTrigger } from '@uipath/flow-sdk/case';

export default casePlan('nightly-sweep')
  .name('NightlySweep').identifier('NS')
  .trigger(manualTrigger())                              // user-initiated
  .trigger(timerTrigger({ every: 'R/PT1H' }))            // every hour (unbounded)
  .trigger(timerTrigger({ every: 'R5/2026-04-26T09:00:00.000Z/P1D' })) // 5×, daily from that instant
  .stage('Run', s => s
    .required().entryWhen(rule('case-entered'))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Work', t => t.rpa('Worker', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered'))))
  .completeWhen(rule('required-stages-completed'))
  .build();
```

- **`manualTrigger({ name?, description? })`** — a `case-management:Trigger` node
  with **no `data.uipath`** (that absence is the manual signature).
- **`timerTrigger({ every, name?, description? })`** — `every` is an **ISO-8601
  repeating interval**, emitted verbatim as `timeCycle`: `R/PT1H` (hourly,
  unbounded), `R5/P1D` (5×, daily), `R5/<iso>/P1D` (5×, daily from an explicit
  start). Emits `data.uipath = { serviceType: 'Intsvc.TimerTrigger', timerType:
  'timeCycle', timeCycle }`.
- **`eventTrigger({ name?, description?, outputs? })`** — an Integration Service
  **event** start. Emits `data.uipath.serviceType: 'Intsvc.EventTrigger'`. With no
  `outputs` it is a **placeholder** (`data.uipath` = only `serviceType`) — the
  offline shape for an event on a connector not yet registered. `outputs` maps
  payload fields to readable case variables, e.g.
  `eventTrigger({ name: 'Order', outputs: { orderId: '=response.id' } })` →
  `=vars.orderId` downstream.
- The **first** `.trigger(...)` is the primary. Compile also syncs the sibling
  `entry-points.json` (one entry per trigger) so the runtime can discover them.

### Variable types

A variable's `type` is one of: `string`, `number`, `integer`, `float`, `double`,
`boolean`, `date`, `datetime`, `file`. Declare with a default via the
`{ type, default }` form on `.input` / `.output` (defaults are written
**verbatim as strings**, e.g. `'1.5'`):

```ts
.input({ claimId: 'string', riskScore: { type: 'float', default: '1.5' } }, { from: manual })
.output({ decision: { type: 'string', default: 'Pending' }, closedAt: 'datetime' })
```

**Structured (object/array) variables** use the `jsonSchema(body)` helper — they
persist as `type: 'jsonSchema'` with the shape carried in the JSON-schema `body`
(object vs array is `body.type`). Works on `.var` / `.input` / `.output`:

```ts
.var('caseMetadata', jsonSchema({ type: 'object', properties: { status: { type: 'string' } } }))
.var('attachments', jsonSchema({ type: 'array', items: { type: 'string' } }))
.input({ eventPayload: jsonSchema({ type: 'object', properties: { orderId: { type: 'string' } } }) }, { from: evt })
```

At compile, In/Out args are projected into `entry-points.json`: each type maps to
its JSON-Schema (`datetime`→`{type:'string',format:'date-time'}`,
`float`→`{type:'number',format:'float'}`, `file`→`{$ref:'#/definitions/job-attachment'}`,
…), each trigger's input holds only the In-args bound to it, and every Out-arg
projects to every entry with its default.

### Binding an In-arg to a trigger

Case inputs can be **bound to a trigger** — their value arrives when that trigger
fires, and is then readable as `=vars.<name>`. Hold the trigger in a `const` and
pass it as `{ from }` to `.input(...)`:

```ts
const manual = manualTrigger();
const hourly = timerTrigger({ every: 'R/PT1H' });

casePlan('intake').name('Intake').identifier('IN')
  .trigger(manual).trigger(hourly)
  .input({ caseId: 'string' }, { from: manual })       // arrives with the manual start
  .input({ runId: 'string' },  { from: hourly })        // arrives when the timer fires
  .input({ note: 'string' })                            // BARE — declared, not trigger-bound
  // …stages…
```

A bound In-arg emits three coordinated pieces: a **formal slot**
(`variables.inputs[]`, `elementId` = the trigger node), a **companion**
(`variables.inputOutputs[]`, `id` = the arg name, what `=vars.<name>` resolves),
and a **bridge** on the trigger node's `data.uipath.outputs[]` that copies the slot
into the companion at fire. Binding an In-arg to a **manual** trigger gives that
node a `data.uipath = { outputs: … }` **with no `serviceType`** (it stays manual).
An `.input(...)` **without** `{ from }` stays a bare declaration (no binding).
`from` must be a trigger you added with `.trigger(...)`.

A plain `.var(name, type)` is **also readable** as `=js:vars.<name>` — it emits the
same companion. Binding is about *when a value arrives*, not about readability. An
**undeclared** `vars.<x>` is a hard error thrown by `.build()`.

## SLA & escalation

<!-- GEN:sla -->

```ts
export interface SlaOpts {
    /** Deadline magnitude (with {@link SlaUnit}). */
    count: number;
    unit: SlaUnit;
    /**
     * A human title, emitted as the SLA's `displayName`. Required to reference this
     * SLA from a `sla-status-change` rule (`rule('sla-status-change', { sla })`).
     * Must be unique across the case and contain no `:`.
     */
    displayName?: string;
    /**
     * A `=js:` gate deciding when this SLA applies — for conditional SLAs (e.g. a
     * tighter deadline for high-priority cases). Omit for the default SLA (the one
     * that always applies); the default must be the LAST `.sla(...)` declared and
     * emits the always-true gate `=js:true`.
     */
    when?: string;
    /** Escalations fired off this deadline. */
    escalations?: BuiltEscalation[];
}

/** SLA deadline unit. `min` = minutes, `h` = hours, `d` = days, `w` = weeks, `m` = months. */
export type SlaUnit = 'min' | 'h' | 'd' | 'w' | 'm';

/**
 * Declare an escalation. `notify` recipients come from {@link toUser}/{@link toGroup}.
 *
 * @param opts - When it fires (`after`) and who it notifies (`notify`).
 * @returns An escalation to attach to an SLA.
 */
export declare function escalation(opts: EscalationOpts): BuiltEscalation;

export interface EscalationOpts {
    /** Fire as the deadline nears (`at-risk`) or after it is missed (`sla-breached`). */
    trigger: EscalationTrigger;
    /** Who to notify (at least one). Build with {@link toUser}/{@link toGroup}. */
    notify: EscalationRecipient[];
    /**
     * For an `at-risk` trigger, the percentage of the SLA elapsed when it fires
     * (e.g. `80` = at 80% of the deadline). Ignored for `sla-breached`.
     */
    atRiskPercentage?: number;
    displayName?: string;
}

/** When an escalation fires: as the deadline approaches (`at-risk`) or once it passes (`sla-breached`). */
export type EscalationTrigger = 'at-risk' | 'sla-breached';

/** Who an escalation notifies. `scope` picks a single user or a whole group. */
export interface EscalationRecipient {
    scope: 'User' | 'UserGroup';
    /** The user/group identifier (email, id, or name the tenant resolves). */
    target: string;
    /** Optional display value; defaults to `target` when omitted. */
    value?: string;
}

/**
 * An escalation recipient that is a single user.
 *
 * @param target - How the user is addressed, e.g. `'email'`.
 * @param value - The address itself, when `target` names a lookup rather than a value.
 * @returns A recipient for an escalation's `notify` list.
 */
export declare function toUser(target: string, value?: string): EscalationRecipient;

/**
 * An escalation recipient that is a user group.
 *
 * @param target - How the group is addressed, e.g. `'name'`.
 * @param value - The value itself, when `target` names a lookup rather than a value.
 * @returns A recipient for an escalation's `notify` list.
 */
export declare function toGroup(target: string, value?: string): EscalationRecipient;
```

<!-- /GEN:sla -->

An **SLA** sets a deadline on a stage (or the whole case): `count` units of time
(`unit`: `'min'|'h'|'d'|'w'|'m'`) from when the stage is entered. **Escalations**
fire off that deadline and notify a user or group — either when it is `at-risk`
(a percentage of the time elapsed) or once it is `sla-breached`. `.sla(...)` on a
stage emits `data.slaRules`; on `casePlan(...)` it emits `metadata.slaRules`.

### Reacting to a deadline — the `sla-status-change` rule

A `sla-status-change` rule makes a deadline **start real work**: a task or stage
activates when an SLA breaches or goes at-risk. Give the SLA (and, for at-risk,
the escalation) a `displayName` and reference it by name — the serializer resolves
it to the generated `slaId`/`escalationId`:

```ts
.sla({ displayName: 'Review SLA', count: 2, unit: 'd' })   // on the stage
// BREACH — start a follow-up task in the SAME stage on its own entry (slaId alone):
.task('Manager Check', t => t
  .action({ title: 'Manager check', priority: 'High', recipient: 'mgr@corp.com' })
  .entryWhen(rule('sla-status-change', { sla: 'Review SLA' })))
// AT-RISK — an interrupting secondary lane takes over (add the escalation name):
.exceptionStage('Escalation', s => s
  .entryWhen(rule('sla-status-change', { sla: 'Case SLA', escalation: 'Notify Owner' }), { isInterrupting: true })
  …)
```

- **Breach** = `{ sla }` alone (no `escalation`). **At-risk** = add `escalation`
  (an `at-risk` escalation declared on that same SLA). Never invent an escalation
  to "repair" a breach rule — that silently converts it to at-risk.

```ts
import { casePlan, rule, escalation, toUser, toGroup } from '@uipath/flow-sdk/case';

export default casePlan('claim-review')
  .name('ClaimReview').identifier('CR')
  .stage('Review', s => s
    .required()
    .entryWhen(rule('case-entered'))
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
    .task('Assess', t => t.action({ title: 'Assess claim', recipient: 'adjuster@corp.com' })
      .required().entryWhen(rule('current-stage-entered')))
    // deadline: 2 days; warn the owner at 80%, escalate to a group on breach
    .sla({ count: 2, unit: 'd', escalations: [
      escalation({ trigger: 'at-risk', atRiskPercentage: 80, notify: [toUser('adjuster@corp.com')] }),
      escalation({ trigger: 'sla-breached', notify: [toGroup('Claims Managers')] }),
    ] }))
  .completeWhen(rule('required-stages-completed'))
  .build();
```

- **`escalation({ trigger, notify, atRiskPercentage?, displayName? })`** — `notify`
  is a list from **`toUser(target, value?)`** / **`toGroup(target, value?)`**
  (`value` defaults to `target`). Give an `at-risk` escalation an
  `atRiskPercentage`; `sla-breached` ignores it.
- **Conditional SLAs:** call `.sla(...)` more than once. A rule with `when: '=js:…'`
  applies only when its gate is truthy (e.g. a tighter deadline for high-priority
  cases); the **default** SLA (no `when`) must be **last** and emits the always-true
  gate `=js:true`.
- **Guardrails (warnings, non-blocking):** `check` and `uip maestro case validate`
  warn on an `at-risk` escalation with no `atRiskPercentage`, an escalation that
  notifies no one, and a deadline with no escalations at all.
- **`unit` is CALENDAR time, and there is no business-day unit.** `uip` enforces
  exactly `min|h|d|w|m` (`Invalid option: expected one of "min"|"h"|"d"|"w"|"m"`), so
  a requirement written in **business days** cannot be expressed exactly — `'d'` runs
  through weekends and holidays. Pick the calendar value deliberately and **say so in
  a comment** (`// Target: 4 business days — APPROXIMATED as 4 calendar days`); do not
  silently treat the two as the same.
  **Do not compute a conversion.** "5 business days ≈ 7 calendar days" depends on the
  start weekday, the holiday calendar and the region; it is wrong for most start
  dates, it drifts, and **nothing in the toolchain will catch it** — the deadline just
  fires on the wrong day. An honest approximation you flag beats a clever one you
  can't verify.

## Integration Service connectors

A `.connector(...)` task runs an IS connector operation (Slack, Jira, Outlook, …)
as a case task. Same surface as the Flow SDK's connector action:

```ts
.stage('Notify', s => s
  .required()
  .entryWhen(rule('selected-stage-completed', { stage: 'Approve' }))
  .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
  .task('Post to Slack', t => t
    .connector(
      'uipath-salesforce-slack', 'send-message-to-user',
      // inputs = the op's fields BY NAME (query params like `send_as` and body
      // fields like `channel`/`messageToSend` are auto-split into the caseplan's
      // pathParameters/queryParameters/body slots)
      { channel: '@requester', messageToSend: 'Approved.', send_as: 'bot' },
      { connection: 'slack', folder: 'shared' })
    .required()
    .entryWhen(rule('current-stage-entered'))))
```

- **Discovering connectors + field names** — identical to Flow: find the op and
  read its fields from the markdown library at `$FLOW_SDK_LIBRARY_MD`.

  `$FLOW_SDK_LIBRARY_MD` (markdown, for reading) and `$FLOW_SDK_LIBRARY_JSON`
  (machine-readable, for compiling) point at a **separately staged** connector
  library. It is not part of the npm package and there is no default: if the
  variables are unset, the library is not on this machine, so search the paths
  your environment provides and pass `--library <dir>` explicitly.

  ```bash
  jq '.entries[] | select(.label | test("send message"; "i")) | {label, nodeType, path}' \
     "$FLOW_SDK_LIBRARY_MD/index.json"
  cat "$FLOW_SDK_LIBRARY_MD/uipath-salesforce-slack/send-message-to-user@1.0.0.md"
  ```

  `uip maestro case compile` points the compiler at the library automatically (via
  `$FLOW_SDK_LIBRARY_JSON`). `key`/`action` are the connector key + the op's
  action segment (`uipath.connector.<key>.<action>`). Inputs are validated when
  the connector resolves; an unknown field or missing required field fails compile
  with an actionable message. (For a connector whose schema needs a live
  connection, the offline library may be thin — see the Flow SKILL's "query the
  live connection" note.)
- **`connection` / `folder`** are symbolic names you declare in `bindings.json`
  (next to your `.case.ts`), exactly like the Flow arm. The compiler resolves them
  to a root `bindings[]` entry and references it as `=bindings.<id>` in the task.
  `bindings.json` format:

  ```json
  {
    "schemaVersion": "1",
    "bindings": [
      { "id": "slack", "name": "slack", "resource": "Connection",
        "resourceKey": "<slack-connection-id>", "default": "<slack-connection-id>",
        "propertyAttribute": "ConnectionId" },
      { "id": "shared", "name": "shared", "resource": "Connection",
        "resourceKey": "<folder-key>", "default": "<folder-key>",
        "propertyAttribute": "folderKey" }
    ]
  }
  ```

A full worked example ships at `examples/NotifyOnApproval.case.ts` (+
`examples/bindings.json`): a human approval stage followed by a Slack
connector task.

## Compile & check (CLI)

Author `<Name>.case.ts` with a default export ending in `.build()`, then:

Both ship in the package: as the bins `case-check` / `case-compile`, or run
directly with `node node_modules/@uipath/flow-sdk/dist/case/<name>-cli.js`.

- **`check`** (`case-check <Name>.case.ts`) — fast static validation of the built
  case; surfaces the common validator failures (task without an entry rule,
  case/stage without a completion rule, unsatisfiable `required-tasks-completed`,
  unresolved stage/task references) without writing a file. Exits non-zero on any
  error.
- **`compile`** (`case-compile <Name>.case.ts [-o caseplan.json]`) — runs the
  static check, then serializes to `caseplan.json` (default output name). Pair it
  with `uip maestro case validate` for the authoritative gate.
- **`decompile`** (`uip maestro case decompile <caseplan.json> [-o Name.case.ts]`)
  — the reverse: reads an existing V20 caseplan and emits builder source whose
  default export re-serializes to the same caseplan. This is how you edit a case
  you did not author in this session: **decompile → edit the `.case.ts` →
  recompile**. The emitted `import` resolves to `@uipath/flow-sdk/case`; override
  it with `--import <specifier>` when placing the file elsewhere.

  > Not reconstructed by decompile: triggers of any kind (a manual trigger is
  > assumed), SLAs/escalations, and the Gap-E action fields (labels, catalog,
  > form `inputs`/`outputs`). Re-add those by hand after decompiling, or the
  > recompiled caseplan will silently drop them.

Programmatic equivalents (`checkCase(built)` / `serializeCase(built)`) exist on the
barrel, but the barrel is not importable from the authoring workspace (see the
import note above) — in this workspace, use the CLI commands above.

## Validation

The generated `caseplan.json` is validated against the authoritative
**`@uipath/case-schema`** package (disk-schema + canvas rules) in the test
suite — the same checks `uip maestro case validate --full` runs. That package is
on GitHub Packages; installing it needs a token with `read:packages` (see
`typescript/.npmrc`, which reads `NODE_AUTH_TOKEN`).

```bash
uip maestro case validate <file>.json          # full gate
uip maestro case validate <file>.json --skeleton  # structural only (fast)
```
