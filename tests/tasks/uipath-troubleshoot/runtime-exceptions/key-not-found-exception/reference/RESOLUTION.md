# Final Resolution

Root Cause: The `Assign` **Read Api Base Url** in `Main.xaml` indexes `config["ApiBaseUrl"]`, but the `config` dictionary only holds the keys `Environment` and `Timeout`. The key `ApiBaseUrl` is absent, so the dictionary indexer throws `System.Collections.Generic.KeyNotFoundException: The given key 'ApiBaseUrl' was not present in the dictionary.`

Evidence:

### Orchestrator
- Process **ConfigReader**, release version **10005**, folder **Shared**, job key `e5a6c7d8-5555-4abc-9def-000000000005` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.Collections.Generic.KeyNotFoundException` — "The given key 'ApiBaseUrl' was not present in the dictionary.".
- Faulted activity: `Assign` **Read Api Base Url** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. The config dictionary is missing the `ApiBaseUrl` entry for this environment. Use `config.TryGetValue("ApiBaseUrl", out var url)` (or `ContainsKey`) with a default instead of the raw indexer, and add the `ApiBaseUrl` key to the config source (Config sheet / asset) for the failing environment. Watch for case/typo mismatches.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **Read Api Base Url**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/key-not-found-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **Read Api Base Url** expression throws `System.Collections.Generic.KeyNotFoundException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
