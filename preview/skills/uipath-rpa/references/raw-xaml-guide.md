# Raw XAML: what the SDK cannot model yet

The SDK does not yet model `Pick` or `FlowSwitch`.
Write such an element as XAML inside `rawActivity(xml)`, which carries it verbatim:

```ts
import { rawActivity } from '@uipath/rpa-builder-sdk';

rpa('Main')
  …
  .step('wait', rawActivity(`<Pick DisplayName="Wait">
  <PickBranch DisplayName="Soon">
    <PickBranch.Trigger>
      <Delay Duration="00:00:01" />
    </PickBranch.Trigger>
    <WriteLine Text="[&quot;reviewing &quot; &amp; in_Path]" />
  </PickBranch>
</Pick>`))
```

- The XML uses the workflow's prefixes: the default namespace is CoreWF's activities, `x:` is XAML's, and any other prefix it uses (`ui:`, `sd:`, `s:`, `scg:`) must be declared with `.namespaces({…})`; declaring one compile also declares is harmless.
- Its expressions are VB, as written; arrows cannot reach inside it. It can read the workflow's arguments and variables.
- Keep everything around the raw element in the SDK: variables, assignments, logging, and invocations before and after it.
- When only one property of a catalog activity is beyond the SDK (`check` refuses it as a type the SDK cannot write), carry just that property with `rawProperty('<ui:Activity.Prop>…</ui:Activity.Prop>')` and keep the activity typed.
