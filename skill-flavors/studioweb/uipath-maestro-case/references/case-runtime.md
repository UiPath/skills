<!--skill-flavor:bindings-refresh:start-->
  `bindings_v2.json`. Studio Web has no `uip solution resources refresh`: add
  each connection the solution does not list with `uip solution resources add`
  (the [Validation loop](../SKILL.md#validation-loop)).
<!--skill-flavor:bindings-refresh:end-->

<!--skill-flavor:orphan-cleanup:start-->
- Compiling does not remove solution resources. After removing or repointing a
  resource-bound task, list local solution resources with `uip solution
  resources list --source local --output json`. Studio Web has no `uip solution
  resources remove`: name each orphaned process or app the list still shows,
  with its listed key, and ask the user to remove it from the solution in
  Studio Web. Never name the Case project's own process/package pair, or a
  package entry.
<!--skill-flavor:orphan-cleanup:end-->

<!--skill-flavor:docextraction-refresh:start-->
<!--skill-flavor:docextraction-refresh:end-->

<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.50.1 or later, which resolves the decompiled
  labels (for example `bOC1`) against that plan's own `bindings` array. Studio Web
  ships its own SDK: when the compiled plan has a decompiled label as a binding key,
  copy `.flow-sdk/original/<Plan>` back over the target and tell the user that this
  Studio Web build cannot keep a Designer-saved plan's binding map yet.
<!--skill-flavor:sdk-upgrade:end-->
