# Catalog activities, collections, Invoke Method and Switch

Any activity the catalog lists goes through `.activity(id, catalogActivity(className), props, slots)`, or `activity(…)` with the same arguments as a slot's one activity.
Look the activity up before writing it: `npx rpa-sdk catalog <word>` finds its class name, and `npx rpa-sdk catalog <className>` lists its property names, their kinds and their types.

## Activities from the catalog

```ts
import { catalogActivity, invokeArguments, Decimal, String } from '@uipath/rpa-builder-sdk';

s.activity('read', catalogActivity('UiPath.Core.Activities.ReadTextFile'), {
  FileName: (v) => v.in_InputPath,
  Content: (v) => v.text,                       // an OutArgument takes a reference to a variable
})
s.activity('validate', catalogActivity('UiPath.Core.Activities.InvokeWorkflowFile'), {
  WorkflowFileName: 'Workflows\\ValidateInvoice.xaml',
  ArgumentsVariable: null,
  Arguments: invokeArguments([
    { key: 'in_Amount', direction: 'In', type: Decimal, value: vb('CDec(row("Amount"))') },
    { key: 'out_AmountEur', direction: 'Out', type: Decimal, value: (v) => v.amountEur },
  ]),
})
```

Property names and kinds come from that listing: `InArgument` takes an expression or literal, `OutArgument` a reference, `Literal` a plain value or enum member, `Activity` a slot, one activity (in the fourth argument, `{ Then: LogMessage(…) }`), `Object` an `objectValue({…})`, `Arguments` an `invokeArguments([…])`.
Invoke Workflow File's `WorkflowFileName` is relative to the project root (the folder with `project.json`), wherever the invoking workflow is; `check` reports a file the project has in neither its `.xaml` nor its `.rpa.ts` form (`INVOKE_FILE_MISSING`).
`Condition` is an `Activity<T>`: an expression, or for a value an activity computes (UI Automation's `AnchorProvider`), that one activity, `activityValue(activity('find', …))`.
`ActivityFunc` is a delegate whose one activity computes the value, as `RetryScope`'s `Condition`: one activity in the fourth argument, `noActivity` for none.
`ArgumentList` is a list of arguments of one type, as `RemoveLogFields`' `Fields`: a plain array, `['logF_TransactionID', (v) => v.name]`.
`Unsupported` properties can only be `null`.

- A generic activity (its class name ends in `` `1 `` and `rpa-sdk catalog` lists properties of type `T`, as `DeserializeJson`, `AddDataColumn`) takes its type argument as the fifth argument of `.activity`, after the slots: `.activity('column', catalogActivity('UiPath.Core.Activities.AddDataColumn`1'), { DataTable: (v) => v.table, ColumnName: 'Count', DefaultValue: 0 }, {}, Int32)`.
- A catalog activity with a body (`TimeoutScope`, `RepeatNumberOfTimesX`, `RetryScope`'s `ActivityBody`) takes `body('item', Type, activity)`, or `body(activity)` when it hands its body no item, in the fourth argument of `.activity`.

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

