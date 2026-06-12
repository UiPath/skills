# XAML Critical Rules & Quick Reference

XAML-mode companion to SKILL.md. Read IN FULL before creating or editing any `.xaml` workflow. Rules below carry numbers 16–24, continuing SKILL.md's Critical Rules numbering — citations to "Rule 16"–"Rule 24" with the `[XAML]` prefix across this skill resolve here. Common Rules 1–12 and Coded Rules 13–19 live in SKILL.md.

## XAML-Specific Rules (16–24)

16. **[XAML] Activity docs are the source of truth** — check `{projectRoot}/.local/docs/packages/{PackageId}/` first. Always.
17. **[XAML] MUST understand project structure** — read `project.json`, check expression language, scan existing patterns. NEVER generate XAML blind.
18. **[XAML] Start minimal, iterate to correct** — build one activity at a time, validate after each addition.
19. **[XAML] Fix errors by category** — Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] ViewState handling depends on the operation.** When editing existing files, do NOT modify ViewState on nodes you are not changing. When generating new Flowchart/StateMachine/ProcessDiagram workflows, generate ViewState for each node (see [canvas-layout-guide.md](canvas-layout-guide.md)). For Sequences, ViewState is optional.
21. **[XAML] Reading `<Activity>.md` from `{PROJECT_DIR}/.local/docs/packages/...` is a precondition for `activities get-default-xaml` — for every activity not on the common-activity card.**
    - **Card-listed activities:** check [../common-activity-card.md](../common-activity-card.md) first; if the activity is on the card, author from the card entry alone — skip `activities find`, skip `activities get-default-xaml`, skip the per-activity MD read.
    - **All other activities:** (1) `activities find` → class name, (2) **read `<Activity>.md` first** and extract a property checklist (required + use-case-relevant), (3) `activities get-default-xaml` → starter element, (4) **diff your checklist against the starter and add what's missing** — an empty checklist means you skipped step 2, go back.
    - **Doc lookup order:** primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; fallback `references/activity-docs/<PackageId>/<closest-version>/<Activity>.md` for older package versions where `.local/docs` is empty. **Exception — `UiPath.UIAutomation.Activities` has no bundled fallback:** `.local/docs` (present only after the package is installed) is its sole activity-doc source. If it is absent, do not hunt for a bundled copy — follow SKILL.md Rule 7a (install with consent per [../uia-prerequisites.md](../uia-prerequisites.md), or use the Placeholder-Selector Stub Pattern — [../ui-automation-guide.md § Placeholder-Selector Stub Pattern](../ui-automation-guide.md)).
    - **Trigger activities are special — read BOTH docs.** When the class name ends in `Trigger`, the namespace contains `.Triggers`, or the description mentions "starts a job" / "Monitor Events" / "Trigger Scope", also read the bundled `references/activity-docs/<PackageId>/<closest-version>/activities/<Activity>.md` **and** the package's bundled `overview.md`. The auto-generated `.local/docs` version is sparse for triggers; the bundled hand-written docs carry placement guidance (entry-point vs. `ui:TriggerScope`), deployment context, and cross-cutting namespace/assembly gotchas that the extractor does not capture. See SKILL.md Common Rule 12 and [../trigger-pattern-guide.md](../trigger-pattern-guide.md).
    - **Skip-tax — concrete:** `activities get-default-xaml` omits any property whose value equals the type default. For `NGetText` the starter is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />` with **zero** output properties — authoring from this alone produces `NGetText.Value="..."` (does not exist; the property is `Text`), which `validate` accepts and `build` rejects. For `NTypeInto` that's 2 of 20 properties hidden.
    - **Self-extending the card — "this activity feels simple, I'll add it to the card mentally" — is the failure mode.** The card is the only allowlist; for non-card activities the MD read is the only check.
    - Full procedure: [xaml-basics-and-rules.md § Activity Property Surface](xaml-basics-and-rules.md).
21a. **[XAML] Built-in workflow activities: use the card only for this allowlist.** Fast-path card activities are: `Sequence`, `If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`, `Assign`, `LogMessage`, `WriteLine`, `Delay`, `Throw`, `Rethrow`. If the activity is on this list, open [../common-activity-card.md](../common-activity-card.md) and author from the card. If it is not on this list, follow full Rule 21. `InvokeWorkflowFile`, `Pick`, `Parallel`, and `ParallelForEach<T>` are intentionally off-card; use full Rule 21. Studio's "While" / "Do While" / "For Each" toolbox items emit UiPath wraps (`UiPath.Core.Activities.InterruptibleWhile` / `InterruptibleDoWhile` / `UiPath.Core.Activities.ForEach<T>`), not the framework `System.Activities.Statements.While`/`DoWhile`/`ForEach<T>`.
22. **[XAML] MUST read [xaml-basics-and-rules.md](xaml-basics-and-rules.md)** before generating or editing any XAML.
23. **[XAML] NEVER change `expressionLanguage` or `targetFramework` on an existing project.** Decide both proactively at init time (SKILL.md Common Rule 2a); this rule covers the immutability afterward. Both fields in `project.json` are fixed at creation time and apply to every XAML file in the project — flipping `expressionLanguage` (VisualBasic ↔ CSharp) invalidates every expression, and flipping `targetFramework` (Windows ↔ Portable/cross-platform, or Legacy) invalidates package references and activity compatibility. **Do not attempt in-place conversion.** If the user wants to convert an existing project, confirm with them, copy the project to a temporary folder, create a new project via `uip rpa init --expression-language <VisualBasic|CSharp> --target-framework <Windows|Portable>` (for a target of Windows - Legacy, create it in Legacy mode instead — modern `init` is not the legacy creation path), make sure all the defined workflows in the old project have an equivalent in the new project. Delete the copied project just after the new project has been successfully generated and the user agree with the changes.
24. **[XAML] Wrap every container-activity body/branch in `<Sequence>` — even single-activity bodies.** Studio's designer expects the wrap as a drop zone; Studio's emitter produces it. `validate` and `build` accept the bare form, so neither catches missing wrappers. Applies to creation and editing alike. Slots include `If.Then`/`If.Else`, `While`/`DoWhile` body, `ForEach.Body`, `TryCatch.Try`/`Catch`/`Finally`, `Switch.Default` + each case, `PickBranch.Trigger`/`Action`, `NApplicationCard.Body`. Full table with examples: [xaml-basics-and-rules.md § Container Activity Bodies — Wrap in Sequence](xaml-basics-and-rules.md).

## XAML Workflows Quick Reference

XAML workflows follow a **discovery-first, phase-based approach**: Discovery → Generate/Edit → Validate & Fix → Response. See [workflow-guide.md](workflow-guide.md) for the full phase workflow.

### Workflow Types

| Type | When to Use |
|------|-------------|
| **Sequence** | Linear step-by-step logic; most common for simple automations |
| **Flowchart** | Branching/looping logic with multiple decision points |
| **State Machine** | Long-running processes with distinct states and transitions |
| **Long Running Workflow** | BPMN-style horizontal flow; event-driven processes with long waits. Requires `UiPath.FlowchartBuilder.Activities` — see [long-running-workflow-guide.md](long-running-workflow-guide.md) |

### Expression Language

Check `expressionLanguage` in `project.json`. VB.NET uses `[brackets]` for expressions; C# uses `CSharpValue<T>` / `CSharpReference<T>`. Default for new XAML projects is VB.NET.

### Key CLI Commands

| Command | Purpose |
|---------|---------|
| `activities find --query "<keyword>"` | Discover activities by keyword |
| `activities get-default-xaml --activity-class-name "<class>"` | Get starter XAML for an activity |
| `analyzer-rules list --project-dir "<dir>"` | List enabled Workflow Analyzer rules — run before generating |
| `validate --file-path "<file>"` | Per-file static validation (structure, references, analyzer rules) |
| `build "<PROJECT_DIR>"` | Compile-time validation (member names, enum values, JIT expressions) — run after `validate` is clean |

### Common Activities

| Activity | Package | Purpose |
|----------|---------|---------|
| **UI automation** (Use Application/Browser, Click, Type Into, Get Text, Select Item, …) | `UiPath.UIAutomation.Activities` | **Never author from memory or from this row.** Selectors and targets are captured, not hand-written — read [../ui-automation-guide.md](../ui-automation-guide.md) in full first (SKILL.md Rule 7). |
| If | built-in | Conditional branching |
| Assign | built-in | Set variable/argument values |
| For Each | built-in | Iterate over a collection |
| Invoke Workflow File | built-in | Call another workflow file |
| Create Entity Record | `UiPath.DataService.Activities` | Create a Data Fabric entity record |
| Query Entity Records | `UiPath.DataService.Activities` | Query Data Fabric records with filters — see [filter builder guide](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) |

### XAML File Anatomy

The XAML file anatomy template (namespace declarations, root Activity element, body structure) is in [xaml-basics-and-rules.md](xaml-basics-and-rules.md) — read it before generating or editing any XAML.

### Key References

- [xaml-basics-and-rules.md](xaml-basics-and-rules.md) — XAML anatomy, safety rules, editing operations (read before any XAML work)
- [common-pitfalls.md](common-pitfalls.md) — Activity gotchas, scope requirements, property conflicts
- [../reframework-guide.md](../reframework-guide.md) — REFramework execution modes, SetTransactionStatus queue-guard fix, Config.xlsx leftover trap
- [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md) — Canonical C# binding forms per common activity property (LogMessage, GetText, StartProcess, …) — flat lookup table + recipes
- [csharp-expression-pitfalls.md](csharp-expression-pitfalls.md) — C#-specific expression failures (attribute-form VB JIT, ThrowIfNotInTree, OutArgument parse errors)
- [canvas-layout-guide.md](canvas-layout-guide.md) — Flowchart, State Machine, and Long Running Workflow canvas layout with ViewState
- [long-running-workflow-guide.md](long-running-workflow-guide.md) — LRW package dependency, node vocabulary, gateway patterns, suspend/resume persistence
- [jit-custom-types-schema.md](jit-custom-types-schema.md) — JIT custom type discovery
- [../library-authoring-guide.md](../library-authoring-guide.md) — Produce reusable libraries: public-workflow contract, activity layout sidecar (display name, icon, widgets), error contract, SemVer, pack & publish to the libraries feed

For XAML workflows spanning multiple capture screens, see [../ui-automation-guide.md § Multi-Screen Authoring](../ui-automation-guide.md) and [../uia-configure-target-workflows.md § Multi-Step UI Flows](../uia-configure-target-workflows.md) — both read IN FULL first per SKILL.md Rule 7.
