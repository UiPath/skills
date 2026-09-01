---
name: uipath-maestro-case
description: "UiPath Maestro Case Management authoring — `caseplan.json` built from a `<Name>.case.ts` TypeScript builder source (`@uipath/flow-sdk/case`), via the check/compile/validate loop. Covers stages, tasks, rules, bindings, published-resource references, SLA/escalation, and brownfield decompile/edit/recompile. Install the SDK first (§ Step 0). API sections are GENERATED from the SDK's built `.d.ts` — do not hand-edit them. For .flow→uipath-maestro-flow. For .bpmn→uipath-maestro-bpmn. For .xaml/C#→uipath-rpa. For PDD/SDD design and case SDD authoring→uipath-planner. For runtime task management→uipath-tasks."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---
<!--
Provenance — READ BEFORE EDITING.

  source repo    UiPath/flow-builder-sdk
  source file    typescript/sdk/skill/SKILL-case.md
  source branch  case-sdk/experimental-codegen-skill
  source commit  e011feef8b49a6d13b915bdd2a6956e70b497053
  landed         2026-09-01

THIS SKILL REPLACED THE DIRECT-JSON CASE SKILL (fork-only decision, 2026-09-01).
Until this commit, `uipath-maestro-case` was 67 files / 11,928 lines that authored
`caseplan.json` directly with Write/Edit, with the shapes encoded in prose. It was
replaced wholesale by this builder-SDK path, where the shapes live in the type system.
Both mechanisms are legitimate; this fork chose types over prose. Recover the previous
skill with:

    git checkout 8b0ae9e96 -- skills/uipath-maestro-case

Consequences a reader should know:
  * `tests/tasks/uipath-maestro-case/` still holds 65 task YAMLs written against the
    OLD mechanism (they assert hand-authored caseplan.json, tasks.md, the phase
    protocol, scripts/audit_plan.py). They target this skill by name and have NOT been
    ported. Expect them to fail until triaged. The two tasks under
    `init_validate/` and `skill_routing/` are the ported ones.
  * The old skill's `scripts/audit_plan.py` is gone with it. Upstream PR #2943 was
    replacing it with `scripts/audit_caseplan.py` (a caseplan-vs-sdd completeness
    auditor); that work is unaffected by this fork but is no longer wired here.
  * 14 files in sibling skills (mostly uipath-planner, plus uipath-human-in-the-loop
    and uipath-maestro-bpmn) redirect to `uipath-maestro-case`. Those arrows still
    resolve — the name was deliberately kept — but they now lead to a skill that
    teaches a different mechanism. Their surrounding prose was NOT audited.

This is pinned to a BRANCH, not to origin/main. At the time of landing that branch was
52 commits ahead of origin/main and 217 behind, and none of the 52 were upstream by
patch-id. The `preview/uipath-maestro-*` snapshots in this repo are produced by
scripts/sync-maestro-sdk-preview.mjs, which tracks origin/main ONLY and does not manage
this directory. So this skill is deliberately outside that pipeline and will NOT be
refreshed by it. Note `preview/uipath-maestro-case/` ALSO declares
`name: uipath-maestro-case`; that is not a live conflict because `plugin.json` ships
`./skills/` only and npm `files` excludes `preview/`.

The API sections between GEN markers were generated from the built
`dist/case/case-sdk.d.ts` by `typescript/sdk/scripts/gen-case-skill.mjs`, verified with
`gen-case-skill.mjs --check` -> OK at commit e011fee. Do not hand-edit them; regenerate
upstream and re-land, or the types and the prose drift apart.

Version pins in force at landing (measured 2026-09-01, not copied):
  launcher (uip --version)  1.202.0   <- NOT what validates
  @uipath/maestro-tool    1.198.0   <- the bundled validator `uip maestro case validate` runs
  schema authority        V13 (14 task types, 15 rules)
  document version        20.0.0    <- the `version` field in caseplan.json
  mainline PO.Frontend    0b11f5660 (V31, 16 rules; `api-event` is PREVIEW, not emitted)

VERIFIED GAP AT LANDING (2026-09-01) — the documented check/compile loop did NOT run.
`uip maestro case check <f>.case.ts --source` returns `unknown command 'check'` on the
`uip` installed here (1.202.0 global, from ~/.bun/install/global/node_modules/@uipath/cli).
`uip maestro case --help` lists no check, compile, or decompile.

The verbs are real, just not reachable from this install:
  * assets/uip-catalog-snapshot.json (uip 1.202.0-dev.8414) DOES list `maestro case
    check`, `compile`, `decompile` — which is why this repo's verb gate passes.
  * ~/src/cli/packages/case-tool asserts the tool exposes ["compile","check","decompile"].
  * Installed @uipath/maestro-tool is 1.198.0; npm's published @uipath/cli is 1.200.0.

So this is the SAME launcher-vs-tool split documented below, one layer down: the launcher
is 1.202.0, the tools behind it are older, and the case verbs live in the newer tool.
Before relying on the check/compile loop, confirm the verb exists in YOUR install:

    uip maestro case --help | grep -E 'check|compile|decompile'

If absent, the SDK ships its own binaries (`case-check`, `case-compile`, `case-decompile`
in @uipath/flow-sdk) and `uip maestro case validate` still owns compiled-artifact
validation. Do not assume the loop below is executable because it is written down.

Ceiling: every member here is VALIDATOR-confirmed. Nothing in this skill proves the
platform EXECUTES a plan — live case rungs need a personal/debug robot the tenant does
not currently have.

`uip maestro case validate` IS A SHAPE GATE, NOT A COMPLETENESS GATE. Do not treat a
Valid verdict as evidence a plan will run. Independently reproduced on the golden eval
(2026-09-01): it returned Valid for a caseplan with 8 stages and 0 tasks, while the
authoring agent's own closing message said the artifact was incomplete. Known blind
spots — it does NOT check:

  * cross-task output reference ids
  * `caseShape.context` completeness
  * formal-argument id/var distinctness
  * whether `vars.$xref` markers were ever resolved
  * that any stage contains a task at all

This matters more for the SDK path than for hand-authored JSON, because compile+validate
is the whole loop here: a compiler that emits a well-shaped empty plan gets a green
verdict. If you need a completeness check, write an explicit assertion over the compiled
`caseplan.json`; do not delegate it to `validate`. (A `caseplan.json`-vs-`sdd.md`
completeness auditor is in flight in the skills repo under a separate PR — worth
consuming rather than reinventing once it lands, but this skill does not depend on it.)
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

## Step 0 — make sure the builder is present, before authoring

Nothing else in this skill works until the case builder is resolvable. **Check
first — in many environments it is already provided and installing again is
wasted work:**

```bash
ls node_modules/.bin/case-compile 2>/dev/null || npm ls @uipath/flow-sdk 2>/dev/null
```

If it is there, skip the rest of this section and go to **Authoring**.

> **Why a package called `flow-sdk` when this is Case.** There is no case-only
> package. Upstream ships the case builder as the `./case` subpath of
> `@uipath/flow-sdk`, and `case-compile` / `case-check` / `case-decompile` are
> bins of that same package (`@uipath/case-sdk` does not exist). So the import is
> `@uipath/flow-sdk/case` and the install is `@uipath/flow-sdk` — one package,
> three builders. Installing it does not pull in Flow authoring work; it is just
> where the case code lives.

If absent, install it in the project directory:

```bash
npm install @uipath/flow-sdk
```

**`@uipath/flow-sdk` is published to GitHub Packages, not the public npm registry.**
A plain `npm install` therefore 404s unless the `@uipath` scope is pointed at
GitHub Packages with a token that has `read:packages`. If the install 404s, write a
project-level `.npmrc` **in the project directory** (never `$HOME` — that clobbers
the developer's global config) and retry:

```bash
printf '%s\n' \
  '@uipath:registry=https://npm.pkg.github.com/' \
  '//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}' \
  > .npmrc
npm install @uipath/flow-sdk
```

Keep `${NODE_AUTH_TOKEN}` literal as written — npm expands it at read time, so no
token is written to disk. Verify before authoring:

```bash
ls node_modules/.bin/case-compile && ls node_modules/.bin/case-check
```

> **Do not search the filesystem for the compiler.** It is not preinstalled, it is
> not global, and it is not shipped inside this skill. In measured runs
> (2026-09-01) agents that skipped this step spent **over half the entire run** —
> ~240s of 415s — on `find /Users/... -name "flow-sdk"` sweeps before installing
> it, and one such run gave up and hand-wrote `caseplan.json` instead, silently
> abandoning the builder. If `case-compile` is absent, install it; do not hunt for
> it, and do not fall back to writing the JSON by hand.

## Step 0.5 — pull the tenant registry, before authoring any task reference

**Gate, not a suggestion.** If any task in the case will reference a published
process, agent, rpa, api-workflow, child case, or Action Center app — i.e. anything
except a pure timer/wait case — run this before you author:

```bash
uip maestro case registry pull
```

Then resolve every reference against the cache, as described in **Reference a REAL
resource — discover before you invent** below. Two reasons this is a gate:

1. `uip maestro case validate` **cannot tell an invented name from a published one.**
   A case full of plausible-sounding names validates cleanly, packs, uploads, and
   then fails on its first task. Skipping the pull moves the failure from build time
   to run time.
2. `registry get` / `registry search` answer from a **local cache that does not
   refresh itself.** A stale cache reports a resource as missing (or reports an old
   shape) while the tenant already serves a richer one. When freshness matters, use
   `uip maestro case registry pull --force`.

A missing `<type>-index.json` **before** a pull is a precondition failure, not a
zero-result lookup. After a successful pull, a still-absent index means the tenant
genuinely has zero resources of that type.

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
     * Hand the "what runs next" decision to the **Case Manager** agent.
     *
     * Use this when the requirements name a process or agent that decides which work starts,
     * rather than the plan's own rules deciding. Emits `metadata.caseManagerData`.
     *
     * WHAT THIS UNLOCKS, AND WHY IT MATTERS (MST-13857). A task with NO entry conditions never
     * enters the scheduler's rule set, so only the Case Manager's decisions can start it —
     * that absence is the mechanism, not an omission. Without this surface the builder forced
     * an entry rule on every task, and the fallback was `adhoc`: on one real build 6 of 8
     * tasks compiled to `UserAdhocTrigger`, giving case workers a play button the requirements
     * never described, while the hand-built reference had zero `adhoc` rules and five tasks
     * with no entry conditions at all. Enabling this turns TASK_NO_ENTRY from an error into a
     * warning, and the frontend already filters its own equivalent error the same way.
     *
     * Stages can likewise be left without entry rules, so the Case Manager decides when they
     * open rather than every stage opening the moment the case starts.
     *
     * @param enabled - Whether a Case Manager decides what runs next.
     * @returns This builder, so calls chain.
     */
    caseManager(enabled?: boolean): this;

/**
     * Declare a read/write case variable.
     *
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
    completeWhen(rules: RuleArg<'case-exit'>, opts?: {
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

private _caseApp;

private readonly _caseExit;

private _caseManager;

private _description?;

private readonly _id;

private _identifier?;

private _identifierType;

private _name;

private readonly _sla;

private readonly _stages;

private readonly _triggers;

private readonly _vars;

private _version;

/**
     * Set the case plan's version.
     *
     * @param v - The version string written into the plan.
     * @returns This builder, so calls chain.
     */
    version(v: string): this;

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
     * `current-stage-entered` is rejected here at compile time — it is a TASK-entry rule
     * (scheduler `StageEntered`, admitted only by `TaskEntryCondition`). A stage that
     * should start when another finishes wants `selected-stage-completed`.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName`, and the entry behaviour flags.
     * @returns This builder, so calls chain.
     */
    entryWhen(rules: RuleArg<'stage-entry'>, opts?: EntryOpts): this;

/**
     * Add a stage-exit condition (OR-group). Pass an array of rules for an AND-group.
     *
     * Accepts the task-completion family, not the stage-completion one: a stage exits on
     * what happened INSIDE it. `selected-stage-exited` and friends are rejected at compile
     * time — the scheduler's exit/completion conditions cannot evaluate them.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName`, and whether meeting it completes the stage.
     * @returns This builder, so calls chain.
     */
    exitWhen(rules: RuleArg<'stage-exit'>, opts?: ExitOpts): this;

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

/** @internal */
    _build(): BuiltStage;

private _description?;

private readonly _entry;

private readonly _exception;

private readonly _exit;

private readonly _label;

private readonly _lanes;

private _required?;

private readonly _sla;

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
export type TaskKind = 'process' | 'agent' | 'rpa' | 'api-workflow' | 'case-management' | 'action' | 'connector' | 'wait-for-timer' | 'wait-for-connector' | 'flow-process' | 'function' | 'document-extraction' | 'external-agent' | 'external-workflow';

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
        /**
         * WHICH Action Center app, path-qualified — emitted as `name`/`folderPath`
         * `=bindings.<id>` refs. Without it Studio Web's app picker is empty, and a bare
         * `actionCatalogName` cannot choose among same-titled apps in different folders.
         */
        app?: TaskRef;
        inputs?: ActionField[];
        outputs?: ActionField[];
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
     * Reference an **IXP document-extraction** task.
     *
     * The converter assigns `serviceType: "IXP.Extraction"` itself. `.inputs()`/`.outputs()`
     * work as on any reference task, which is how you get the extracted fields back out.
     * @param name Published name of the extraction resource.
     * @param opts `folder` — Orchestrator folder path holding it.
     */
    documentExtraction(name: string, opts?: {
        folder?: string;
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
     * Reference an **external agent** — an agent published outside this case's solution.
     *
     * `serviceType` IS the author's decision here: the converter reads
     * `data.serviceType` and only falls back to `"Intsvc.SyncAgentExecution"` when absent.
     * We therefore emit it explicitly rather than relying on that fallback, so the wire says
     * what was meant instead of what the converter guessed.
     *
     * Pass `serviceType` to override. Values other than the sync default are NOT enumerated
     * anywhere we can read, so this is deliberately an open string — inventing an "async"
     * literal would be a guess encoded as an API.
     * @param name Published name of the agent, in whichever solution owns it.
     * @param opts `folder` — its folder path; `serviceType` — overrides the
     * `Intsvc.SyncAgentExecution` fallback when the call should not be synchronous.
     */
    externalAgent(name: string, opts?: {
        folder?: string;
        serviceType?: string;
    }): this;

/**
     * Reference an **external workflow** — a workflow published outside this solution.
     *
     * Same `serviceType` story as `externalAgent`: the converter falls back to
     * `"Intsvc.SyncWorkflowExecution"`, and this emits it explicitly. Worth stating because a
     * sync default is the load-bearing kind of default — it decides whether the case waits.
     * @param name Published name of the workflow, in whichever solution owns it.
     * @param opts `folder` — its folder path; `serviceType` — overrides the
     * `Intsvc.SyncWorkflowExecution` fallback when the call should not be synchronous.
     */
    externalWorkflow(name: string, opts?: {
        folder?: string;
        serviceType?: string;
    }): this;

/**
     * Reference a published **flow process** (a Maestro flow, as opposed to a BPMN process).
     *
     * The converter assigns `serviceType: "Orchestrator.StartFlowProcess"` itself, so this
     * emits none — a value here would be overwritten.
     * @param name Published name of the flow process.
     * @param opts `folder` — Orchestrator folder path holding it.
     */
    flowProcess(name: string, opts?: {
        folder?: string;
    }): this;

/**
     * Reference a published **function**.
     *
     * The converter assigns `serviceType: "Orchestrator.ExecuteFunctionAsync"` itself. Note
     * the name says Async: the platform runs a function task asynchronously, and that is not
     * ours to choose.
     *
     * Named `function` to match the schema type, consistent with `apiWorkflow`/`api-workflow`.
     * It is a valid method name — `function` is reserved for identifiers, not properties.
     * @param name Published name of the function.
     * @param opts `folder` — Orchestrator folder path holding it.
     */
    function(name: string, opts?: {
        folder?: string;
    }): this;

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
     * A wait-for-timer task (ISO-8601 `duration`, ISO `date`, or repeating `cycle`).
     *
     * @param spec - How long to wait: an ISO-8601 `duration`, a `date`, or a repeating `cycle`.
     * @returns This builder, so calls chain.
     */
    waitForTimer(spec?: TimerSpecData): this;

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
        /**
         * WHICH Action Center app, path-qualified — emitted as `name`/`folderPath`
         * `=bindings.<id>` refs. Without it Studio Web's app picker is empty, and a bare
         * `actionCatalogName` cannot choose among same-titled apps in different folders.
         */
        app?: TaskRef;
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
 * A `wait-for-connector` subscription: suspend on an Integration Service event.
 * Omit `connectorKey`/`operation` for a bare **placeholder** (for a connector not
 * yet registered — `data.uipath` carries only `serviceType`).
 */
export interface WaitConnectorSpec {
    /** Connector key, e.g. `uipath-microsoft-outlook365`. */
    connectorKey?: string;
    /** Event operation, e.g. `EMAIL_RECEIVED`. */
    operation?: string;
    /**
     * The Integration Service connection, by the name it carries in `bindings.json` —
     * emitted as a `=bindings.<id>` reference the way a connector *activity*'s connection
     * already is.
     *
     * Without it there is no way to reach the connection at all, so a case whose stage waits
     * on a posted webhook has an empty connector panel in Studio Web and nothing wired to
     * wait on (MST-13859). A requirements document can supply a `connectionId` and it had
     * nowhere to go.
     */
    connection?: string;
    /** The connection's folder, by its `bindings.json` name — emitted as a `=bindings.<id>` ref. */
    folder?: string;
    /** The object the event is about, e.g. `message`. */
    objectName?: string;
    /** HTTP method of the subscription endpoint. */
    method?: string;
    /** Path of the subscription endpoint. */
    path?: string;
    /** `uiPathActivityTypeId` for the event activity, carried on the `metadata` row. */
    activityTypeId?: string;
    /** `eventMode` on the `metadata` row, e.g. `Automatic`. */
    eventMode?: string;
    /** The `configuration` blob on the `metadata` row (emitted as a `=jsonString:` payload). */
    configuration?: unknown;
    /**
     * What to KEEP of the arriving event. A stage whose entry waits on a webhook otherwise
     * keeps nothing of what arrived: the rule came out with `inputs: []` / `outputs: []` and
     * no surface to fill them, so case variables declared to hold the event body and headers
     * were dead on arrival (MST-13864).
     */
    inputs?: WaitConnectorField[];
    /** Fields of the arriving event to bind into case variables (read as `=vars.<var>`). */
    outputs?: WaitConnectorField[];
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
     * Accepts only rules a task-entry condition can carry downstream. `case-entered` and
     * the stage-completion family are rejected at compile time: the validator accepts them
     * here, but the scheduler's `TaskEntryCondition` has no branch that can evaluate them,
     * so such a plan packs, publishes and silently never fires.
     *
     * @param rules - One rule, or an array for an AND-group.
     * @param opts - `displayName` for the condition.
     * @returns This builder, so calls chain.
     */
    entryWhen(rules: RuleArg<'task-entry'>, opts?: {
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
    /**
     * WHICH app, path-qualified. Emitted as `name` / `folderPath` `=bindings.<id>` references
     * the way a reference-mode task's resource is.
     *
     * `actionCatalogName` alone cannot select one: apps in different folders share a title
     * (three published `SimpleApprovalApp`s, three different `actionDefinitionId`s, one a
     * version behind), and Studio Web's properties panel resolves the selection from `name` +
     * `folderPath` — so without this the app picker is empty before anything runs. It also
     * registers the app in the root bindings, which is what lets a deployment re-point it.
     */
    app?: TaskRef;
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
    /**
     * INPUT rows — the value pushed into the form field: a literal, `=vars.<name>`, or a
     * `=js:` expression. Without it the field renders with a label and nothing in it.
     */
    value?: string;
    /**
     * OUTPUT rows — the case variable the assignee's answer is written to, read downstream
     * as `=vars.<var>`.
     *
     * Omitting this is the defect behind MST-13862: a plan can declare a decision variable,
     * have five rules read it, validate clean, and have NOTHING write it — so on a live run
     * every branch out of the stage is dead. An output row without `var` is a label with no
     * destination, so `check` reports it (ACTION_OUTPUT_NO_VAR).
     */
    var?: string;
    /**
     * OUTPUT rows — the app's outcome set, e.g. `['approve', 'reject']`.
     *
     * Declare it and the decision rules that compare against this variable are checked
     * against it, which is the only thing standing between an author and MST-13866: the SDK
     * emitted `=js:vars.approvalDecision === "Reject"` while the app submits `"reject"`, the
     * comparison is JavaScript `===`, and the case could never leave Approval. `validate`
     * passes — both sides are just strings.
     *
     * CASE MATTERS AND THE APP IS NOT READABLE. Action Center apps submit their outcomes
     * lower-case, and the app record does not publish them: `definition.appFields` is `[]` on
     * every published copy, and `appFields` appears nowhere in PO.Frontend. So the value has
     * to be stated here, and a stated value is at least checkable — which an invented literal
     * buried in an expression is not.
     */
    options?: string[];
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

### Reference a REAL resource — discover before you invent

A reference-mode task is just a `name` + `folderPath` string on the wire. **The validator
cannot tell an invented name from a published one** — that is not its job — so a case full of
plausible-sounding names validates cleanly, packs, uploads, and then fails on its first task.
This is the single widest gap between "my case is Valid" and "my case runs".

So resolve every task reference against the tenant before writing it.

```bash
uip maestro case registry pull                     # populates ~/.uip/case-resources/ — do this FIRST
ls ~/.uip/case-resources/                          # which index files the tenant actually has
python3 -c "import json;[print(e.get('name'),'|',e.get('entityKey')) for e in json.load(open('$HOME/.uip/case-resources/agent-index.json'))]"
```

Discovery reads those cache files directly rather than using `uip maestro case registry
search`, which has known gaps and returns empty for types that are present in the cache
(most often Action Center apps). Read the `<type>-index.json` for the task kind you are
resolving; a **missing** index file before a pull is a precondition failure, not a
zero-result lookup — pull, then re-read.

For a task's input/output contract, use the CLI rather than guessing:

```bash
uip maestro case tasks describe --type <kind> --id <entityKey> --output json
```

> `uip or processes get` **without** `--all-fields` returns an EMPTY `InputArguments`.
> Do not derive argument names from it.

Three rules that matter more than they look:

- **A missing index file is NOT "the tenant has none".** It means the pull never ran. Absence
  of evidence and evidence of absence have very different consequences here: one is a
  precondition failure, the other is a real answer that licenses a placeholder.
- **The cache does not refresh itself.** Pull before trusting an absence, or you are reading
  a snapshot of whenever someone last pulled.

#### Then read the resource's io contract — do not guess argument names

Having found the resource, you still need its **input and output argument names**. Get them
from the resource, never from the requirements document:

```bash
uip maestro case tasks describe --type <type> --id <entityKey> --output json
```

`--type` takes `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`,
`flow-process`, `connector-activity`, `connector-trigger`, `external-workflow`,
`external-agent`. The `--id` is the `entityKey` from discovery. Read `.Data.Inputs[].Name`
and `.Data.Outputs[].Name` and use them verbatim in `.inputs()` / `.outputs()`.

**Why this step is not optional.** Two runs of the same task, same SDK, same requirements
document, went opposite ways: the one that read the contract got every argument name right,
character for character; the one that guessed got **all of them wrong on all five
resources**. Both plans validated clean. A wrong argument name is a runtime null, never a
validation error — so nothing between you and the live run will tell you.

**Do not use `uip or processes get <id>` to derive argument names.** Its `InputArguments`
field comes back empty, which reads as "this resource has no arguments" rather than "you
asked the wrong way", and that is exactly how the guessing run got there. (If you must use
it, the real data is at `--all-fields` → `.Data.ArgumentsV2`.)

**`tasks describe` is not `case spec`.** `uip maestro case spec` is for connector activities
and triggers; it does not answer reference-mode io.

**Watch the `process` / `rpa` split.** `process-index.json` (`entitySubType: Process`) and
`processOrchestration-index.json` (`ProcessOrchestration`) are disjoint sets — measured
24 and 21 entries with **zero overlap** — and `tasks describe --type process` reads the
*orchestration* one. The SDK's `.process()` maps to `processOrchestration-index.json` and
`.rpa()` to `process-index.json`; reading the wrong index is why a name that plainly
exists on the tenant appears to be missing.
- **`external-agent` / `external-workflow` are not separate registry types.** "External" is
  about WHERE the resource lives — published in a different solution from this case — so they
  come from the same `agent-index.json` / `api-index.json`, and the folder path is what tells
  you. (The `typecache-external-agent-*` indexes look like the right source and are not: every
  entry is `UiPath.IntegrationService.Activities`, an activity package, not a resource.)

`document-extraction`, `function`, `wait-for-timer` and `wait-for-connector` have no registry
index — those references resolve elsewhere and cannot be checked this way.

When a resource genuinely does not exist, say so and use a placeholder deliberately. Do not
quietly invent a name that looks right; a wrong name is indistinguishable from a right one
until run time, which is the most expensive moment to find out.

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
 * Generic in the rule name so the literal survives into the slot check: `rule('adhoc')`
 * has type `CaseRule<'adhoc'>`, not `CaseRule`. Without that neither the slot narrowing
 * nor the per-rule options above could see which rule it was given.
 *
 * The rest parameter makes the options argument REQUIRED exactly when that rule has a
 * mandatory field, and optional otherwise — so `rule('sla-status-change')` fails to
 * compile while `rule('case-entered')` stays a bare call.
 *
 * @param type - Which condition, e.g. `'case-entered'` or `'selected-tasks-completed'`.
 * @param args - What the rule needs, e.g. the `tasks` a task-completion rule waits on.
 * Required when the rule has a mandatory field; omit it otherwise.
 * @returns A rule to pass to `entryWhen` / `exitWhen` / `completeWhen`.
 */
export declare function rule<T extends CaseRuleType>(type: T, ...args: Record<string, never> extends OptsFor<T> ? [opts?: OptsFor<T>] : [opts: OptsFor<T>]): CaseRule<T>;

export type CaseRuleType = 'case-entered' | 'required-tasks-completed' | 'required-stages-completed' | 'selected-stage-completed' | 'selected-stage-exited' | 'selected-tasks-completed' | 'current-stage-entered' | 'adhoc' | 'runs-sequentially' | 'user-selected-stage' | 'wait-for-connector' | 'sla-status-change';

export interface RuleOpts {
    /**
     * Symbolic stage label (for `selected-stage-completed` / `selected-stage-exited`).
     *
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
- Reference-mode task `data.name`/`folderPath` are **`=bindings.<id>` references**, and the
  root `bindings[]` carries a `name` + `folderPath` pair per referenced resource. This is
  what makes the resource a declared dependency, so `uip solution deploy config get` can
  re-point it at deploy time; with literal paths the case only ever runs in the folder it was
  authored in. The five kinds with no binding shape on record (`flow-process`, `function`,
  `document-extraction`, `external-agent`, `external-workflow`) still emit literal paths.

## Validates clean, cannot run — the five traps

Everything below **passes `uip maestro case validate`** and fails only on a live run, or
renders empty in Studio Web. They were all found by comparing SDK-authored plans against
product-authored plans of the same case. Check each one before you ship.

### 1. Human-task decision literals are lower-case

An Action Center app submits its outcomes lower-case (`"approve"`, `"reject"`). A rule
comparing `=js:vars.decision === "Reject"` uses JavaScript `===`, so it **never fires and
the case is stuck in that stage forever**. Both sides are strings, so validate is silent.

Declare the app's outcome set and the compiler checks your rules against it:

```ts
.task('Approve', (t) => t.action({
  title: 'Approve the request',
  app: { name: 'SimpleApprovalApp', folderPath: 'Shared/Apps' },
  outputs: [{ name: 'Action', var: 'approvalDecision', options: ['approve', 'reject'] }],
}))
// then: rule('adhoc', { expression: '=js:vars.approvalDecision === "reject"' })
```

A literal outside the declared set is a `DECISION_LITERAL_UNMATCHABLE` **error**, and a
case-only mismatch is reported as such. Declaring `options` is the only way to get this
check — the app does not publish its outcomes anywhere readable, so with none declared the
compiler has nothing to compare against and stays quiet.

### 2. An action task's outputs must name the variable they write

`outputs: [{ name: 'Action' }]` renders a labelled box that writes **nothing**. If rules
read `=vars.approvalDecision` and no output declares `var: 'approvalDecision'`, the plan
validates, the rules parse, and every branch is dead. Always give an output row its `var`,
and an input row its `value`.

### 3. Escalation recipients are GUIDs, not emails

`toUser('ops@example.com')` now throws. The converter maps `target` to the notification
service's `id`, discards `value`, and the backend requires a GUID — so an email means every
escalation notification fails, silently, until the SLA fires. Write
`toUser('<user-guid>', 'ops@example.com')`.

### 4. Name the app's folder, or the picker is empty

`actionCatalogName` alone cannot identify an app: the same title is published in several
folders with different action-definition ids. Pass `app: { name, folderPath }` — Studio Web
resolves the selection from those two fields, so without them the app picker is blank before
anything runs.

### 5. Give every step its own error output

`.outputs({ stepError: '=Error.Message' })` works on `action`, `wait-for-connector` and
`wait-for-timer` as well as the reference-mode kinds. One slot per step, never shared.

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
    /**
     * The recipient's **GUID**. PO.Frontend maps this to the notification service's `id`
     * (`BpmnCaseTaskNodeConverterUtils`) and the backend requires a GUID
     * (`NotificationServiceArgs.cs` → `Guid.TryParse`), so anything else fails with
     * `recipient 'id' is missing or not a valid GUID`.
     */
    target: string;
    /**
     * The human-readable address (an email, a group name). Carried for display only —
     * the converter DISCARDS it, so it can never stand in for `target`.
     */
    value?: string;
}

/**
 * An escalation recipient that is a single user.
 *
 * The old JSDoc here said `target` was "how the user is addressed, e.g. 'email'", which
 * read as an invitation to pass an email — and an email is exactly what the notification
 * service cannot use. `target` is the user's GUID; the email goes in `value`.
 *
 * ```ts
 * toUser('4f2a1c88-9d3e-4b7a-8c11-0a5e6f7b2d34', 'ops@example.com')
 * ```
 *
 * @param target - The user's GUID.
 * @param value - The human-readable address (an email), for display.
 * @returns A recipient for an escalation's `notify` list.
 */
export declare function toUser(target: string, value?: string): EscalationRecipient;

/**
 * An escalation recipient that is a user group.
 *
 * `target` is the group's GUID; the group name goes in `value`.
 *
 * @param target - The group's GUID.
 * @param value - The group's name, for display.
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
        "resourceKey": "<slack-connection-id>", "default": "<folder-key>",
        "propertyAttribute": "folderKey" }
    ]
  }
  ```

  > **`resourceKey` is the CONNECTION id on BOTH rows.** The folder key appears
  > only as the folder row's `default`. Same two GUIDs, different roles — a pair of
  > rows describing one connection, one of which carries the folder as its value.
  >
  > This example previously told you to put the folder key in the folder row's
  > `resourceKey`, on a row declared `resource: "Connection"`. Nothing catches it:
  > `UiPathBindingJsonSchema` types both fields as plain strings and the compiler
  > passes the value straight through, so **the first signal is Studio Web reporting
  > "resource not found" when the case is opened**. If you have a case that fails to
  > open, check this first.

A full worked example ships at `examples/NotifyOnApproval.case.ts` (+
`examples/bindings.json`): a human approval stage followed by a Slack
connector task.

## Compile & check (CLI)

Author `<Name>.case.ts` with a default export ending in `.build()`, then:

Both ship in the package (install it first — see **Step 0**). Three equivalent ways
to invoke them, all verified working 2026-09-01:

```bash
./node_modules/.bin/case-compile <Name>.case.ts -o caseplan.json   # explicit, no resolution guesswork
npx case-compile <Name>.case.ts -o caseplan.json                   # same binary via npx
node node_modules/@uipath/flow-sdk/dist/case/compile-cli.js <Name>.case.ts
```

Prefer the `./node_modules/.bin/` form: it fails loudly and immediately if Step 0
was skipped, whereas `npx` may pause to fetch, and a bare `case-compile` only works
if the bin directory is on `PATH`, which it usually is not.

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
