# Raw XAML: what the SDK cannot model yet

The SDK does not yet model `Pick` or `FlowSwitch`.
Write such an element as XAML inside `rawActivity(xml)`, which carries it verbatim:

```ts
import { rawActivity } from '@uipath/rpa-builder-sdk';

s.rawActivity(`<Pick DisplayName="Wait">
  <PickBranch DisplayName="Soon">
    <PickBranch.Trigger>
      <Delay Duration="00:00:01" />
    </PickBranch.Trigger>
    <WriteLine Text="[&quot;reviewing &quot; &amp; in_Path]" />
  </PickBranch>
</Pick>`)
```

`rawActivity(xml)` is the same as a slot's one activity: `Then: rawActivity(…)`.

- The XML may use, undeclared, the prefixes compile always declares: the default namespace (CoreWF's activities), `x:`, `ui:`, `scg:`, `mc:`, `sap:` and `sap2010:`.
  Declare any other on the element itself, as decompile writes it: `<sd:DataTable xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common" …>`; `check` refuses an undeclared one (`RAW_PREFIX_UNDECLARED`).
- Its expressions are VB, as written; arrows cannot reach inside it. It can read the workflow's arguments and variables.
- Keep everything around the raw element in the SDK: variables, assignments, logging, and invocations before and after it.
- When only one property of a catalog activity is beyond the SDK (`check` refuses it as a type the SDK cannot write), carry just that property with `rawProperty('<ui:Activity.Prop>…</ui:Activity.Prop>')` and keep the activity typed.
