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
  The catalog is a folder or a `.zip`; look activities up with the CLI, not by reading its files: `npx rpa-sdk catalog <word>` lists the activities whose name matches (`npx rpa-sdk catalog textfile`), and `npx rpa-sdk catalog <className>` lists one activity's properties, their kinds, types, and which are required (`npx rpa-sdk catalog UiPath.Core.Activities.AppendLine`).
- `check` reports refusals and lint findings; with `--json` it prints `{"ok":true,"warnings":0,…}` when the file is clean.
  `ok` is false only for a refusal, which compile cannot write; `ok` with warnings is still not clean.
- `compile` writes the XAML. A file in a subfolder compiles the same way: `npx rpa-sdk compile Workflows/ValidateInvoice.rpa.ts -o Workflows/ValidateInvoice.xaml`.
- **Editing an existing workflow:** `decompile` it to a `.rpa.ts`, edit that, compile it to a new file, and `merge` the new file into the original, which keeps the original's layout and ids for everything you did not change.
  The decompiled source keeps the file's activity ids as step ids and its annotations as `.note(…)`; a state or flowchart node Studio named `__ReferenceID<n>` gets a readable key with its old name as `xName`, and each type it names is declared once at the top (`const QueueItemType = clrType(…)`).
  Leave `xName` as it is.
  The source carries no namespaces and no root: compile derives them, and `merge` puts the original's own spelling back (its prefixes, `mc:Ignorable`, `VisualBasic.Settings`, its references).
  `.imports([…])` lists the namespaces the file imports beyond the ones compile adds; add one there when a `vb(…)` expression needs it.
  What decompile could not read stays as XML: a whole element as `rawActivity(…)`, or one property of an otherwise typed activity as `rawProperty(…)`; edit around them, or replace one with typed code when you change it.
- **Running it:** where the host serves `uip rpa run` (Studio Web does), run the compiled workflow to test what it does: `uip rpa run --file-path Main.xaml --input-arguments name=value --output json` (`name:=<json>` for a typed value). It prints the workflow's log lines, then `{Result, Code, Data}`; `Data.output` holds the output arguments, and `Data.errorMessage` a fault.
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
import { DataTable, Decimal, Int32, LogMessage, rpa, String, vb } from '@uipath/rpa-builder-sdk';

export default rpa('Main')                      // the x:Class; the project is VB, the default
  .argument('in_Amount', Decimal, 'In')         // x:Members: 'In', 'Out' or 'InOut'
  .argument('in_Region', String, 'In', { default: 'EMEA' })  // the value when the caller passes none
  .argument('in_Orders', DataTable, 'In')
  .argument('out_Route', String, 'Out')
  .Sequence('Sequence_1', 'Main', (s) => s      // the root activity: one, usually a Sequence
    .variable('count', Int32, 0)                // a variable on this Sequence, with a default
    .Assign('route', { to: (v) => v.out_Route, value: 'Manager' })
    .If('big', {
      Condition: (v) => v.in_Amount > 10000,
      Then: LogMessage('warn', { Level: 'Warn', Message: (v) => `large: ${v.in_Amount}` }),
      Else: LogMessage('ok', { Level: 'Info', Message: 'small' }),
    })
    .Assign('rows', { to: (v) => v.count, value: vb('in_Orders.Rows.Count') }))
  .build();                                     // the finished workflow, the file's default export
```

- Every activity is one call with its id first (`IdRef`; `undefined` lets compile number it): a method in a Sequence's chain (`s.LogMessage('warn', { … })`), or the function of the same name where a slot holds one activity (`Then: LogMessage('warn', { … })`).
- A slot (`Then`, `Else`, `Body`, `Try`, `Finally`, a state's `Entry`, a case, a branch) holds exactly one activity. Several steps are a `Sequence(id, displayName?, (s) => s…)`, as Studio writes them, with an id of their own; `.variable(…)` scopes a variable to that Sequence.
- The workflow's root is one activity too, as the workflow's own method: `rpa('Main').Sequence(…)`, `.StateMachine(…)`.
- `.note(text)` after a chain call adds Studio's annotation to it; a slot's activity takes it as `Then: note('why', LogMessage(…))`.
- Types: `String`, `Int32`, `Int64`, `Boolean`, `Double`, `Decimal`, `Object`, `DateTime`, `TimeSpan`, `Exception`, `BusinessRuleException`, `DataTable`, `DataRow`, `arrayOf(String)` (`String[]`), and `clrType({ name, local, clrNamespace, assembly })` for any other (`xmlns` too for a type under a URI, `ui:QueueItem`; `args: [String]` for a generic one).
- Activities: `Assign(id, { to, value, type? })`, `LogMessage(id, { Level, Message })` (levels `Trace`, `Info`, `Warn`, `Error`, `Fatal`), `WriteLine(id, { Text })`, `Delay(id, { Duration })`, `Throw(id, { Exception })`, `If(id, { Condition, Then, Else })`, `Sequence`, and the loops and `TryCatch` below.

## Loops and Try Catch

A loop's body is one activity whose arrows read the item by the name given after the id; the item is in scope only inside the body.

```ts
import { Assign, BusinessRuleException, Catch, Exception, Int32, LogMessage, Sequence, String, Throw, vb } from '@uipath/rpa-builder-sdk';

s.ForEachRow('rows', 'row', { DataTable: (v) => v.in_Orders, Body: Assign('add', { to: (v) => v.total, value: vb('total + CDec(row("Amount"))') }) })
  .ForEach('each', 'name', String, { Values: (v) => v.in_Names, Body: LogMessage('log', { Message: (v) => `name ${v.name}` }) })
  .While('retry', { attempt: [Int32, 0] }, { Condition: (v) => v.attempt < 3, Body: Assign('inc', { to: (v) => v.attempt, value: (v) => v.attempt + 1 }) })
  .TryCatch('guard', {
    Try: Sequence('Sequence_2', 'Validate', (t) => t…),
    Catches: [
      Catch(BusinessRuleException, 'rule', LogMessage('warn', { Level: 'Warn', Message: vb('rule.Message') })),
      Catch(Exception, 'fault', Throw('rethrow', { Exception: vb('fault') })),
    ],
    Finally: …,
  })
```

- `ForEach(id, item, type, { Values, Body, CurrentIndex?, MaxIterations? })` is Studio's For Each; `kind: 'CoreWF'` makes it CoreWF's plain `ForEach<T>`.
- `ParallelForEach(id, item, type, { Values, Body })`, `ForEachRow(id, item, { DataTable, Body, CurrentIndex? })` (the item is a `DataRow`), `While(id, { Condition, Body })`, `DoWhile(id, { Body, Condition })`.
- `TryCatch(id, { Try, Catches, Finally })`: the first `Catch(type, name, activity)` whose type matches handles the exception, which its activity reads by `name`. `BusinessRuleException` is UiPath's business exception (`New BusinessRuleException("…")` in VB).
- `While`, `DoWhile`, `Parallel`, `StateMachine` and `Flowchart` can declare variables of their own, after the id and before the props, in scope for all of it: `While('retry', { attempt: [Int32, 0] }, { … })`.
- A type the activity takes (`Switch`, the collection activities) comes after the id too: `Switch('route', String, { Expression, Cases, Default })`.

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
- **`vbCr`, `vbLf` and `vbCrLf` are strings, not characters**: `TrimEnd(vbCr)` fails to compile under Option Strict. Use `ControlChars.Cr`, or `vbCr(0)`, where a `Char` is wanted; `Split(vbLf)` is fine.
- **A `ByRef` result** (`EXPR_BYREF_RESULT`): an expression cannot write to a variable through a `ByRef` argument, so `Decimal.TryParse(text, amount)` leaves `amount` unchanged and returns False, with no error. Test with `Decimal.TryParse(text, Nothing)` and assign `Decimal.Parse(text)` in its own step.

## Anti-patterns

- Editing the compiled `.xaml` by hand, or compiling over an existing `.xaml` without merging: both lose what Studio wrote there.
- Compiling while `check` still prints a warning.
- Reaching for `rawActivity` for something the SDK models: raw XAML is unchecked, and arrows cannot reach inside it.
- Guessing an activity's property names: look them up with `npx rpa-sdk catalog <className>`.
