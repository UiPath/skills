# UI Automation Guide (Shared)

Common rules for UI automation across coded workflows (C#) and RPA workflows (XAML). Each skill has its own `ui-automation-guide.md` with skill-specific target finding steps and patterns.

## Mandatory: Generate Targets Before Writing Any UI Code

Before writing ANY target — whether C# (`uiAutomation.Open(...)`, `Descriptors.App.Screen.Element`) or XAML (`<uix:TargetApp>`, `<uix:TargetAnchorable>`):

1. **NEVER hand-write selectors.** Hand-written selectors will have invalid syntax, wrong attribute names, missing required attributes (`SearchSteps`, `ContentHash`, `Reference`), or target the wrong element. They fail validation or break at runtime.
2. **NEVER guess selector attributes** from HTML/DOM structure, element tag names, or CSS classes. Selectors are generated from the live application tree by probing elements — not from source code inspection.
3. **ALWAYS follow the target configuration steps** from [uia-configure-target-workflows.md](uia-configure-target-workflows.md). Use the returned XAML/references exactly as provided by the configuration steps. Do not modify selectors, content hashes, or reference IDs.

> This gate applies regardless of how simple the target seems. Even a `<webctrl tag='BODY' />` selector will fail validation without proper attributes. The cost of running target configuration is always lower than debugging hand-written selectors.

---

## Common Pitfalls

- **SelectItem on web dropdowns** — `SelectItem` may fail on custom `<select>` elements. Workaround: use `TypeInto` instead.
- **ScreenPlay overuse** — UITask/ScreenPlay is non-deterministic and slow. Always try proper selectors first.
- **Wrong Object Repository references** — never copy references from examples or other projects. Always use `uia-configure-target` to generate them for the current application state.
- **Launching the app before configuring targets** — do NOT launch the target application before running `uia-configure-target`. The skill captures the window tree first and only launches if the app isn't found. Launching preemptively risks targeting the wrong window.
- **Using `InjectJsScript` instead of standard activities** — do NOT use `InjectJsScript` when standard UI activities (GetText, Click, TypeInto, ExtractTableData, etc.) with configured targets would work. `InjectJsScript` is a last resort — it's hard to debug, fragile to page changes, and bypasses the Object Repository.

---

## Related Shared Procedures

- [uia-configure-target-workflows.md](uia-configure-target-workflows.md) — Full configure-target workflow, rules, indication fallback
- [uia-multi-step-flows.md](uia-multi-step-flows.md) — Advancing application state between screens
- [uia-debug-workflow.md](uia-debug-workflow.md) — Running and debugging UI automation workflows
- [uia-selector-recovery.md](uia-selector-recovery.md) — Fixing selectors that fail at runtime
- [uia-prerequisites.md](uia-prerequisites.md) — Package version requirements
