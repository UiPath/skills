# Catalog activities, collections, Invoke Method and Switch

Any activity the catalog lists goes through `.activity(id, catalogActivity(className), props, slots)`.
Read the activity's catalog entry for its property names, their kinds and their types before writing it.

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

Property names and kinds come from the catalog entry: `InArgument` takes an expression or literal, `OutArgument` a reference, `Literal` a plain value or enum member, `Activity` a slot (in the fourth argument, `{ Then: (t) => t… }`), `Object` an `objectValue({…})`, `Arguments` an `invokeArguments([…])`.
`Unsupported` properties can only be `null`.

- A catalog activity with a body (`TimeoutScope`, `RepeatNumberOfTimesX`) takes `body('item', Type, (t) => t…)`, or `body((t) => t…)` when it hands its body no item, in the fourth argument of `.activity`.

## Collections, Invoke Method, Switch

```ts
import { AddToCollection, arg, clrType, InvokeMethod, String, Switch, vb } from '@uipath/rpa-builder-sdk';

s.step('add', AddToCollection({ type: String, Collection: (v) => v.names, Item: (v) => v.name }))
  .step('column', InvokeMethod({
    MethodName: 'Add',
    TargetObject: arg(clrType({ name: 'System.Data.DataColumnCollection', xmlns: 'clr-namespace:System.Data;assembly=System.Data.Common',
      local: 'DataColumnCollection', prefix: 'sd', clrNamespace: 'System.Data', assembly: 'System.Data.Common' }), vb('out_Summary.Columns')),
    Parameters: [arg(String, 'Region'), arg(SystemType, vb('GetType(String)'))],
  }))
  .step('route', Switch({ type: String, Expression: (v) => v.status, Cases: { HIGH: (c) => c…, LOW: (c) => c… }, Default: (d) => d… }))
```

- `AddToCollection`, `RemoveFromCollection`, `ExistsInCollection` and `ClearCollection` take the item `type` and a `Collection` of it.
- `InvokeMethod({ MethodName, TargetObject?, TargetType?, Parameters?, Result? })`: `arg(Type, value)` is an argument that names its type, `arg(Type, (v) => v.x, 'Out')` an Out one; `TargetType` a type, for a static method. `SystemType` above stands for `clrType({ name: 'System.Type', xmlns: 'clr-namespace:System;assembly=System.Private.CoreLib', local: 'Type', prefix: 's' })`.
- `Switch({ type, Expression, Cases, Default? })`: each key of `Cases` is a case, as text.
- Often an expression is shorter than an activity: `vb('out_Summary.Columns.Add("Region", GetType(String))')` cannot stand alone, but `Assign` takes `vb('dt.Compute("Sum(Amount)", "")')` and the like.

