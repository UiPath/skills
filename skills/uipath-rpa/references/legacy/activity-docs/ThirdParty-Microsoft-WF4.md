# Microsoft.Activities & Extensions - Legacy Reference

## Overview
Windows Workflow Foundation 4 (WF4) supplemental activities and testing helpers by Ron Jacobs (Microsoft). Package: `Microsoft.Activities` v1.8.9.17 and `Microsoft.Activities.Extensions`. **#11 (15.1%) and #12 (12.5%) by adoption**. Source: [CodePlex (archived)](http://wf.codeplex.com/). NuGet package inspected directly.

---

## Why 15% Adoption?

The high adoption is mostly **legacy inertia** - these packages were popular in early UiPath (2016-2019) before UiPath had equivalents for many WF4 operations. Many existing projects still reference them. UiPath now provides built-in alternatives for most functionality.

---

## Microsoft.Activities (v1.8.9.17)

### Package Contents (from NuGet inspection)
- `Microsoft.Activities.dll` (Net40, Net401)
- `Microsoft.Activities.Design.dll` (designers)
- `Microsoft.Activities.NuGet.dll` (tools)

### Key Activities & Classes (from package metadata + documentation)
| Activity/Class | Purpose | UiPath Equivalent |
|----------------|---------|-------------------|
| `LoadActivity` | Dynamically load XAML workflow from file | Invoke Workflow File |
| `LoadAndInvokeWorkflow` | Load + execute XAML at runtime | Invoke Workflow File |
| `InvokeWorkflow` | Simplified workflow invocation with args | Invoke Workflow File |
| `DelayUntilTime` | Delay until specific time of day | Delay + DateTime logic |
| `AddToDictionary<K,V>` | Add item to dictionary | Assign activity |
| `RemoveFromDictionary<K,V>` | Remove from dictionary | Invoke Method |
| `ClearDictionary<K,V>` | Clear all dictionary entries | Assign activity |
| `GetWorkflowXaml` | Get XAML definition string | (no equivalent) |
| `StringConcat` | Concatenate strings | Assign + String.Concat |
| `RegexMatch` | Regex pattern matching | System.Text.RegularExpressions |
| `RegexReplace` | Regex find/replace | Matches activity |
| `RegexMatches` | Return all regex matches | Matches activity |
| `RegexIsMatch` | Test if regex matches | Is Match activity |
| `GetFromDictionary<K,V>` | Get value by key | Assign + dict(key) |
| `KeyExistsInDictionary<K,V>` | Check if key exists | dict.ContainsKey() |
| `StringConcat` | Concatenate strings | Assign + String.Concat |

### Why 15% Adoption (The Real Reason)
UiPath's classic designer originally lacked built-in dictionary manipulation activities. `AddToDictionary`, `GetFromDictionary`, `KeyExistsInDictionary` were **the standard way** to work with dictionaries in XAML. The REFramework and early Academy templates included these packages, propagating them across thousands of projects. This is **legacy inertia** - UiPath now has all equivalents built-in.

### Extension Methods (non-activity helpers)
- `WorkflowArguments` - Simplified dictionary building for workflow arguments
- Task-based async helpers for WF4

---

## Microsoft.Activities.Extensions (v2.0.6.9)

### Key Features
| Feature | Purpose | UiPath Equivalent |
|---------|---------|-------------------|
| `WorkflowApplicationTest` | Unit test helper wrapping WorkflowApplication | UiPath Testing Framework |
| `WorkflowInvokerTest` | Simplified test invocation | Testing activities |
| `StateMachineStateTracker` | Track state machine transitions and history | (no equivalent - useful for debugging) |
| `MemoryTrackingParticipant` | In-memory execution event capture | Log Message / Output panel |
| `WorkflowEpisode` | Resume workflows from persistence points | (built into UiPath runtime) |
| `ActivityStateQuery` extensions | Detailed activity execution tracing | UiPath logs |

---

## Critical Gotchas

### Compatibility
1. **.NET Framework 4.0/4.0.1 ONLY** - will NOT work with .NET 5+/6+ projects (UiPath Windows-modern)
2. **Abandoned since 2013** - last NuGet update was v1.8.9.17 (2011 for Microsoft.Activities)
3. **CodePlex source is archived** - no bug fixes, no updates, no support
4. **Can conflict with UiPath's workflow engine** - both use System.Activities; assembly binding redirects may clash

### Why NOT to Use
5. **UiPath has built-in equivalents** for almost everything:
   - Dictionary operations: use `Assign` activity
   - Dynamic workflow loading: use `Invoke Workflow File`
   - Delay until time: use `Delay` with calculated TimeSpan
   - String operations: use `Assign` with VB.NET/C# expressions
6. **Testing helpers don't work** with UiPath's custom workflow host (different runtime)
7. **StateMachineStateTracker is the only unique feature** - useful for debugging state machines but available nowhere else

### Migration
8. **New projects should NOT add these packages** - use UiPath built-in activities instead
9. **Existing projects**: gradually replace Microsoft.Activities calls with UiPath equivalents during maintenance
10. **If you see these in a project**: the project is likely legacy (pre-2020) and may need broader modernization
