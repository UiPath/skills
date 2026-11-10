# Catalog activities, collections, Invoke Method and Switch

Any activity the catalog lists is written through a typed module generated from its entry.
Find the activity's class name with `npx rpa-sdk catalog <word>`, then `npx rpa-sdk catalog <className>` lists its properties, their kinds and types, and writes its module into the project's `activities/` folder:

```
npx rpa-sdk catalog UiPath.Core.Activities.GetRobotAsset
wrote activities/UiPath.System.Activities/GetRobotAsset.ts: import { GetRobotAsset } from './activities/UiPath.System.Activities/GetRobotAsset.ts'; adds .GetRobotAsset(id, { … }) to the chain
```

## Activities from the catalog

```ts
import { arg, invokeArguments, Decimal, Object, String, vb } from '@uipath/rpa-builder-sdk';
import './activities/UiPath.System.Activities/ReadTextFile.ts';
import './activities/UiPath.System.Activities/InvokeWorkflowFile.ts';
import { GetRobotAsset } from './activities/UiPath.System.Activities/GetRobotAsset.ts';

s.ReadTextFile('read', {
  FileName: (v) => v.in_InputPath,
  Content: (v) => v.text,                       // an OutArgument takes a reference to a variable
})
  .InvokeWorkflowFile('validate', {
    WorkflowFileName: 'Workflows\\ValidateInvoice.xaml',
    ArgumentsVariable: null,
    Arguments: invokeArguments([
      { key: 'in_Amount', direction: 'In', type: Decimal, value: vb('CDec(row("Amount"))') },
      { key: 'out_AmountEur', direction: 'Out', type: Decimal, value: (v) => v.amountEur },
    ]),
  })
  .If('missing', { Condition: (v) => v.text === '', Then: GetRobotAsset('asset', { AssetName: 'Fallback', Value: arg(Object, (v) => v.fallback, 'Out') }) })
```

- Importing a module adds its activity to the chain (`s.ReadTextFile(…)`); import its factory by name to use it as a slot's one activity (`Then: GetRobotAsset(…)`).
- The module types every property from the catalog, so the editor rejects a misspelled property, an enum value that is not a member, and a value of the wrong type; `check` refuses them too.
- A module is generated: regenerate it with `rpa-sdk catalog <className>` rather than edit it. `decompile` writes the ones a file uses beside it.
- `s.activity(id, catalogActivity(className), props, slots)` is the same activity without a module.

Property names and kinds come from that listing: `InArgument` takes an expression or literal, `OutArgument` a reference, `Literal` a plain value or enum member, `Activity` a slot, one activity (`Then: LogMessage(…)`), `Object` an `objectValue({…})`, `Arguments` an `invokeArguments([…])`.
Invoke Workflow File's `WorkflowFileName` is relative to the project root (the folder with `project.json`), wherever the invoking workflow is; `check` reports a file the project has in neither its `.xaml` nor its `.rpa.ts` form (`INVOKE_FILE_MISSING`).
`Condition` is an `Activity<T>`: an expression, or for a value an activity computes (UI Automation's `AnchorProvider`), that one activity, `activityValue(activity('find', …))`.
`ActivityFunc` is a delegate whose one activity computes the value, as `RetryScope`'s `Condition`: one activity, `noActivity` for none.
`ArgumentList` is a list of arguments of one type, as `RemoveLogFields`' `Fields`: a plain array, `['logF_TransactionID', (v) => v.name]`.
`Unsupported` properties can only be `null`.

- A generic activity (its class name ends in `` `1 `` and `rpa-sdk catalog` lists properties of type `T`, as `DeserializeJson`, `AddDataColumn`) takes its type argument after the id: `.AddDataColumn('column', Int32, { DataTable: (v) => v.table, ColumnName: 'Count', DefaultValue: 0 })`.
- A catalog activity with a body (`TimeoutScope`, `RepeatNumberOfTimesX`, `RetryScope`'s `ActivityBody`) takes `body('item', Type, activity)`, or `body(activity)` when it hands its body no item.

## Collections, Invoke Method, Switch

```ts
import { arg, clrType, String, vb } from '@uipath/rpa-builder-sdk';

s.AddToCollection('add', String, { Collection: (v) => v.names, Item: (v) => v.name })
  .InvokeMethod('column', {
    MethodName: 'Add',
    TargetObject: arg(clrType({ name: 'System.Data.DataColumnCollection', local: 'DataColumnCollection', clrNamespace: 'System.Data', assembly: 'System.Data.Common' }), vb('out_Summary.Columns')),
    Parameters: [arg(String, 'Region'), arg(SystemType, vb('GetType(String)'))],
  })
  .Switch('route', String, { Expression: (v) => v.status, Cases: { HIGH: …, LOW: … }, Default: … })
```

- `AddToCollection`, `RemoveFromCollection`, `ExistsInCollection` and `ClearCollection` take the item type after the id, and a `Collection` of it.
- `InvokeMethod(id, { MethodName, TargetObject?, TargetType?, Parameters?, Result? })`: `arg(Type, value)` is an argument that names its type, `arg(Type, (v) => v.x, 'Out')` an Out one; `TargetType` a type, for a static method. `SystemType` above stands for `clrType({ name: 'System.Type', local: 'Type', clrNamespace: 'System', assembly: 'System.Private.CoreLib' })`.
- CoreWF finds the method by the declared types, not by the values at run time: `TargetObject`'s type must declare the method, and each parameter's type must be the method's parameter type exactly.
  `arg(Object, vb('results.Keys'))` has no `CopyTo` (`check` reports it as `INVOKE_METHOD_OBJECT_TARGET`), and `Array.Sort` has no overload taking `(Array, Object)`; a mismatch faults the whole workflow when it loads.
  When a method's types are awkward to name, an `Assign` of a VB expression is simpler: `vb('results.Keys.Cast(Of String).OrderBy(Function(k) k, StringComparer.Ordinal).ToArray()')`.
- `Switch(id, type, { Expression, Cases, Default? })`: each key of `Cases` is a case, as text, holding one activity.
- Often an expression is shorter than an activity: `vb('out_Summary.Columns.Add("Region", GetType(String))')` cannot stand alone, but `Assign` takes `vb('dt.Compute("Sum(Amount)", "")')` and the like.

