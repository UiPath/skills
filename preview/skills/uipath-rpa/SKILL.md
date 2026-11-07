---
name: uipath-rpa
description: "UiPath RPA XAML workflows authored with the TypeScript builder SDK (`@uipath/rpa-builder-sdk`): write `<Name>.rpa.ts` and compile it to `<Name>.xaml`, or decompile an existing `.xaml`, edit the source, compile and merge it back. Run the `rpa-sdk` check/compile/decompile/merge loop. Covers Sequence, If, Assign, Log Message, loops (For Each, For Each Row, While, Do While, Parallel For Each), Try Catch and Throw, Switch, collections, Invoke Method, State Machine (REFramework), Parallel, Flowchart, any catalogued activity through `.activity()` (Invoke Workflow File with arguments, file and DataTable activities), VB expressions and their runtime traps, and raw XAML for what the SDK cannot model yet. Coded `.cs` workflows, UI automation targets, Legacy projects and Orchestrator operations are out of this preview's scope."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---
<!-- PREVIEW — the builder-SDK flavor of uipath-rpa. Source of the SDK: UiPath/flow-builder-sdk, typescript/rpa-sdk. -->

# UiPath RPA — TypeScript Builder SDK

Write each workflow as TypeScript, `<Name>.rpa.ts`, and compile it to the `<Name>.xaml` beside it.
The `.xaml` is what Studio opens, what runs and what is tested; keep the `.rpa.ts` next to it.
The SDK is the npm package `@uipath/rpa-builder-sdk`, installed in the project folder; its types are in `node_modules/@uipath/rpa-builder-sdk/dist/*.d.ts`.

This file is a router: the core of authoring is below, and the table names the reference to read, in full, before using what it covers.

## Critical Rules

1. Never hand-write or hand-edit a workflow's XAML. Change the `.rpa.ts` and compile it; for an existing `.xaml`, decompile it first and merge the result back.
2. Run `check` before every `compile`, and fix every finding it prints, warnings included.
   A warning is a workflow that compiles but that CoreWF refuses or runs differently from how it reads.
3. Use only activities the catalog lists: it describes exactly the packages the project has.
   An activity the catalog does not list fails to load at run time.
4. Expressions are VB unless the project says C#; `check` checks their names, not their types, so read [Expressions](#expressions) before writing one.
5. Keep the project's `project.json` settings (target framework, expression language, dependencies) as they are.

## Commands

Run them from the project folder.

```
npx rpa-sdk check   Main.rpa.ts --json
npx rpa-sdk compile Main.rpa.ts -o Main.xaml
npx rpa-sdk decompile Main.xaml -o Main.rpa.ts
npx rpa-sdk merge Main.xaml Main.edited.xaml --in-place
```

- Each command reads the activity catalog from `$RPA_SDK_CATALOG`, or from `--catalog <dir>`, which wins.
  The catalog's `index.json` lists every activity by `className`; `activities/<package>/<className>@<version>.json` lists its properties, their kinds and types.
- `check` reports refusals and lint findings; with `--json` it prints `{"ok":true,"warnings":0,…}` when the file is clean.
  `ok` is false only for a refusal, which compile cannot write; `ok` with warnings is still not clean.
- `compile` writes the XAML. A file in a subfolder compiles the same way: `npx rpa-sdk compile Workflows/ValidateInvoice.rpa.ts -o Workflows/ValidateInvoice.xaml`.
- **Editing an existing workflow:** `decompile` it to a `.rpa.ts`, edit that, compile it to a new file, and `merge` the new file into the original, which keeps the original's layout and ids for everything you did not change.
- Neither `check` nor `compile` compiles the VB expressions: an expression is checked for its surface only (names in scope, the language), not for types.

## Router

| You need | Read |
| --- | --- |
| An activity beyond the built-in factories: file, DataTable and text activities, Invoke Workflow File and its arguments, an activity with a body | [catalog-activities-guide.md](references/catalog-activities-guide.md) |
| Collections, Invoke Method, Switch | [catalog-activities-guide.md](references/catalog-activities-guide.md#collections-invoke-method-switch) |
| A State Machine (REFramework), Parallel or Flowchart | [containers-guide.md](references/containers-guide.md) |
| Something the SDK cannot model yet (`Pick`, `FlowSwitch`, one property `check` refuses) | [raw-xaml-guide.md](references/raw-xaml-guide.md) |

## A workflow

```ts
import { Assign, DataTable, Decimal, Int32, LogMessage, rpa, String, vb } from '@uipath/rpa-builder-sdk';

export default rpa('Main')                      // the x:Class; the project is VB, the default
  .argument('in_Amount', Decimal, 'In')         // x:Members: 'In', 'Out' or 'InOut'
  .argument('in_Orders', DataTable, 'In')
  .argument('out_Route', String, 'Out')
  .variable('count', Int32, 0)                  // a variable on the root Sequence, with a default
  .steps((s) => s
    .step('route', Assign({ to: (v) => v.out_Route, value: 'Manager' }))
    .if('big', (v) => v.in_Amount > 10000, {
      then: (t) => t.step('warn', LogMessage({ Level: 'Warn', Message: (v) => `large: ${v.in_Amount}` })),
      else: (e) => e.step('ok', LogMessage({ Level: 'Info', Message: 'small' })),
    })
    .step('rows', Assign({ to: (v) => v.count, value: vb('in_Orders.Rows.Count') })));
```

- A slot with several steps, or with variables, becomes a Sequence; a single step is written alone. `Sequence({ DisplayName }, (t) => t…)` keeps an explicit one; `.variable(…)` inside any slot scopes a variable to it.
- The first argument of `.step` and `.if` is the step's id (`IdRef`); `undefined` lets compile number it.
- `.note(text)` after a step adds Studio's annotation to it.
- Types: `String`, `Int32`, `Int64`, `Boolean`, `Double`, `Decimal`, `Object`, `DateTime`, `TimeSpan`, `Exception`, `BusinessRuleException`, `DataTable`, `DataRow`, `arrayOf(String)` (`String[]`), and `clrType({ name, xmlns, local, prefix, clrNamespace, assembly })` for any other.
- Factories: `Assign({ to, value, type? })`, `LogMessage({ Level, Message })` (levels `Trace`, `Info`, `Warn`, `Error`, `Fatal`), `WriteLine({ Text })`, `Delay({ Duration })`, `Throw({ Exception })`, `If({ Condition, Then, Else })`, `Sequence`, and the loops and `TryCatch` below.

## Loops and Try Catch

A loop's body is a slot whose arrows read the item by the name given as `item`; the item is in scope only inside the body.

```ts
import { BusinessRuleException, Catch, DataTable, Exception, ForEach, ForEachRow, Int32, String, TryCatch, vb, While } from '@uipath/rpa-builder-sdk';

s.step('rows', ForEachRow({ item: 'row', DataTable: (v) => v.in_Orders, Body: (b) => b
    .step('add', Assign({ to: (v) => v.total, value: vb('total + CDec(row("Amount"))') })) }))
  .step('each', ForEach({ item: 'name', type: String, Values: (v) => v.in_Names, Body: (b) => b
    .step('log', LogMessage({ Message: (v) => `name ${v.name}` })) }))
  .step('retry', While({ Condition: (v) => v.attempt < 3, Body: (b) => b.step('inc', Assign({ to: (v) => v.attempt, value: (v) => v.attempt + 1 })) }))
  .step('guard', TryCatch({
    Try: (t) => t.step('validate', …),
    Catches: [
      Catch(BusinessRuleException, 'rule', (c) => c.step('warn', LogMessage({ Level: 'Warn', Message: vb('rule.Message') }))),
      Catch(Exception, 'fault', (c) => c.step('rethrow', Throw({ Exception: vb('fault') }))),
    ],
    Finally: (f) => f…,
  }))
```

- `ForEach({ item, type, Values, Body, CurrentIndex?, MaxIterations? })` is Studio's For Each; `kind: 'CoreWF'` makes it CoreWF's plain `ForEach<T>`.
- `ParallelForEach({ item, type, Values, Body })`, `ForEachRow({ item, DataTable, Body, CurrentIndex? })` (the item is a `DataRow`), `While({ Condition, Body })`, `DoWhile({ Body, Condition })`.
- `TryCatch({ Try, Catches, Finally })`: the first `Catch(type, name, fill)` whose type matches handles the exception, which its steps read by `name`. `BusinessRuleException` is UiPath's business exception (`New BusinessRuleException("…")` in VB).
- `While` and `DoWhile` can declare variables of their own, in scope for the condition and the body: `While({ Variables: { attempt: [Int32, 0] }, Condition: (v) => v.attempt < 3, Body: … })`.

## Expressions

An expression is an arrow over the scope, a raw VB string, or a literal.

- An arrow `(v) => …` reads arguments and variables as `v.<name>` and is lowered to VB: `===` to `=`, `&&` to `AndAlso`, `!` to `Not`, `` `a ${x}` `` to `$"a {x}"`, string `+` to `&`, `? :` to `If(…, …, …)`.
  Member and method names pass through as written, so `v.name.Trim()` is `name.Trim()`; TypeScript types a `String` as `string`, which has no `Trim`, so write .NET calls with `vb()`.
- `vb('…')` is VB as written, for anything the arrow subset does not cover: .NET calls, `CDec(…)`, `New ArgumentException("…")`, `row("Amount")`, LINQ.
  Inside an arrow, `vb('…')` stands for a part of it: `(v) => v.i < vb('rows.Length')`.
- A literal (`'Manager'`, `0`, `true`) is written as the property's text.
- A new workflow imports what Studio's template does, so an expression can name `File` and `Path` (`System.IO`), `DataTable` (`System.Data`), `BusinessRuleException` (`UiPath.Core`) and the rest without qualifying them.

These pass `compile` and then go wrong when the workflow loads or runs; `check` reports each one by the code named, where there is one.

- **A variable named like a type** (`EXPR_NAME_CASE`): VB ignores case, so a variable or loop item named `file` hides the type `File` in every expression in its scope. Do not name a variable after a type you use.
- **A DataRow item read as a type** (`EXPR_DATAROW_ITEM`): `row("Email")` is an `Object`, and VB's Option Strict refuses it as any other type. Read it with `row("Email").ToString()` or `CDec(row("Amount"))`, and write it with `Assign({ type: Object, to: vb('row("Email")'), value: … })`.
- **`.Count(…)` on a collection with a `Count` property**: a `List`, a `Dictionary` or its `.Values`, a `DataRowCollection`. VB takes the property, so `results.Values.Count(Function(r) r.StartsWith("x"))` fails to compile and the workflow does not load. Write `results.Values.Where(Function(r) r.StartsWith("x")).Count()`; `check` does not catch this one.
- **A name VB reserves** (`RESERVED_NAME`): a variable, argument or loop item named `stop`, `next`, `error` or any other VB keyword, in any case, cannot be read: `[stop]` fails to compile and the workflow does not load. Pick another name.
- **A `ByRef` result** (`EXPR_BYREF_RESULT`): an expression cannot write to a variable through a `ByRef` argument, so `Decimal.TryParse(text, amount)` leaves `amount` unchanged and returns False, with no error. Test with `Decimal.TryParse(text, Nothing)` and assign `Decimal.Parse(text)` in its own step.

## Anti-patterns

- Editing the compiled `.xaml` by hand, or compiling over an existing `.xaml` without merging: both lose what Studio wrote there.
- Compiling while `check` still prints a warning.
- Reaching for `rawActivity` for something the SDK models: raw XAML is unchecked, and arrows cannot reach inside it.
- Guessing an activity's property names: read its catalog entry.
