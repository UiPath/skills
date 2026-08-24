# Final Resolution

Root Cause: The `If` activity **Check Feature Enabled** in `Main.xaml` evaluates the condition `config["FeatureEnabled"] == "true"`, but the `config` dictionary only holds the key `Environment`. The key `FeatureEnabled` is absent, so resolving the `If` condition throws `System.Collections.Generic.KeyNotFoundException: The given key 'FeatureEnabled' was not present in the dictionary.` before either branch runs.

Evidence:

### Orchestrator
- Process **FeatureToggleGate**, release version **10008**, folder **Shared**, job key `b8d9e0f1-8888-4abc-9def-000000000008` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.Collections.Generic.KeyNotFoundException` — "The given key 'FeatureEnabled' was not present in the dictionary.".
- Faulted activity: `If` **Check Feature Enabled** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code — the `If` **Condition** expression, resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`, throws **before** either branch runs. It is not inside an activity package.

Immediate fix:

1. The config dictionary is missing the `FeatureEnabled` entry for this environment. Use `config.TryGetValue("FeatureEnabled", out var v)` (or a `ContainsKey` guard) in the condition instead of the raw indexer, and add the `FeatureEnabled` key to the config source (Config sheet / asset) for the failing environment. Watch for case/typo mismatches.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `If` **Check Feature Enabled** Condition.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/key-not-found-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `If` **Check Feature Enabled** Condition expression throws `System.Collections.Generic.KeyNotFoundException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user condition expression |
| H3 | Fault is inside a Then/Else branch activity | Low | Rejected | No — condition resolution precedes branch execution; no branch frame in the stack |
