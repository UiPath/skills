---
name: uipath-activity-service-vs
description: "Expose C# activities you own — a Visual Studio class library of CodeActivity/NativeActivity types — as a coded-workflow service, so consumers call them as `myservice.DoThing(...)`. Inventories the activity classes and their arguments, confirms which to expose and what to name the service, then generates the mapper shim, registry, and an Execute<T> harness that runs each activity through the UiPath workflow runtime."
when_to_use: "User owns a **Visual Studio C# project** (.csproj, no project.uiproj) containing activity classes deriving from CodeActivity, AsyncCodeActivity or NativeActivity, and wants them callable from coded workflows. Triggers: 'expose my custom activities to coded workflows', 'coded API for my activity package', 'call my CodeActivity from C#'. NOT for UiPath Studio library projects (use uipath-activity-service-studio) and NOT for third-party activities you do not own (use uipath-activity-service-unowned)."
---

# Expose Visual Studio C# Activities as a Coded-Workflow Service

Adds a coded-workflow service to a C# activity library, so consumers call
`myservice.DoThing(...)` instead of dragging activities onto a canvas.

> **Read `../uipath-activity-service-studio/references/internals.md` in full before
> generating any code** — absolute path:
> `~/.claude/skills/uipath-activity-service-studio/references/internals.md`.
> §2 (the mapper constant), §5 (`IWorkflowRuntime`) and §7 (argument construction) are load
> bearing here. The constant in §2 must be reproduced *exactly*; a custom name silently
> resolves to null and throws `NullReferenceException` at execution.

This skill reproduces the pattern UiPath itself ships in
`UiPath.DocumentUnderstanding.Activities.Api` — that package is the reference implementation
if you need a second opinion on shape.

## How to verify things in this skill

**The compiler is the verification tool. Write the code, build it, read the errors.**

A build takes seconds and answers almost every question that comes up here — does this
member exist, what is that property's type, is this overload real, does the reference
resolve. `CS1061` naming a missing member is a *better* answer than a decompiled listing,
because it is about the exact assembly your project actually binds to.

Decompilation earns its place in exactly two cases, both listed in internals §8:

1. The hardcoded mapper constant (internals §2) — a magic string no compiler can check.
2. Compile-time vs runtime version divergence — the Robot loads its own
   `UiPath.Activities.Contracts`, newer than anything on the NuGet feed.

Everywhere else it is slower than building and answers a question the build would have
answered anyway. In particular, **never decompile to inventory the user's own activities
(Step 1) or to look up a property's type** — that source is in the working directory, and
the type is one build away.

If you catch yourself on a third `ilspycmd` invocation before a single file has been
written, stop and run the build instead.

> Contrast with `uipath-activity-service-unowned`: there the activities live in a package
> the user did not author and has no source for, so decompiling the host assembly *is* the
> method. That does not apply here.

---

## Step 0 — Confirm you are in the right skill

- `.csproj` present, **no** `project.uiproj` → right skill.
- `project.uiproj` with `outputType: "Library"` → wrong skill, use
  **`uipath-activity-service-studio`**.
- Activities come from a NuGet package the user did not author → wrong skill, use
  **`uipath-activity-service-unowned`**.

Note the target framework. It must be loadable by the consuming projects — modern Studio
projects are `net8.0`; UiPath's own API packages target `net6.0`. If the project targets
`net48` only, a modern coded workflow cannot consume it; raise that before doing any work.

## Step 1 — Inventory the activities

**From the project's own `.cs` files. Grep and Read — never decompile.** You own this
source; it is sitting in the working directory. `ilspycmd` has no role in this step, and
neither does reading `bin/` or `obj/`.

```
Grep: "CodeActivity|AsyncCodeActivity|NativeActivity|Activity<" over the project's *.cs
```

Find classes deriving from `CodeActivity`, `CodeActivity<T>`, `AsyncCodeActivity`,
`AsyncCodeActivity<T>`, `NativeActivity`, `NativeActivity<T>`, or `Activity<T>`.

For each, record:

- Public properties of type `InArgument<T>` — these become method parameters.
- Public properties of type `OutArgument<T>` — these become return values. **The property
  name is the output dictionary key.** For `CodeActivity<T>` the key is `"Result"`.
- `[RequiredArgument]` attributes — required parameters, worth validating in the service.
- Whether `Execute` touches `context.GetExtension<...>()`, `ObjectContainer`, or other
  runtime extensions. Record this; Step 3 depends on it.

## Step 2 — Confirm scope and service name

Present the inventory as a table: activity class, in-arguments, out-arguments, proposed
method name. Ask which to expose — **do not proceed without confirmation**, since each one
becomes public API.

Then agree the service name — the member consumers type (`du.`, `razor.`). Short,
lowercase, no punctuation, unlikely to collide with another library in the same consuming
project. Suggest one derived from the assembly name (`Contoso.Excel.Activities` → `excel`)
and confirm. Also confirm the namespace for the generated classes; default to
`<RootNamespace>.Api`.

## Step 3 — Decide whether the harness is needed at all

This matters, and it is the step most worth thinking about rather than defaulting.

- **The activity's `Execute` is pure C#** — no `ActivityContext` use beyond reading
  arguments. Then routing through the workflow runtime buys nothing. Refactor the logic into
  a plain method and have the service call it directly. Simpler, faster, no mapper, no
  runtime dependency. Suggest this.
- **The activity depends on runtime extensions** — `context.GetExtension<T>()`, job
  context, Orchestrator services, `ObjectContainer` state shared with other activities. Then
  it must run through the runtime; a hand-rolled call would hand it a bare context and it
  would fail or return nulls. Use the harness.
- **Mixed set** — do both, per activity. The service interface looks identical either way,
  which is the point.

Put the recommendation to the user with the reason. Do not quietly pick.

## Step 4 — Where the mapper goes

The harness needs `UiPath.MapFilePathToActivity_93063903935340c8aab522ec692cb083` in an
assembly you control, and `WorkflowParameters.AssemblyName` pointing at that assembly.

- A VS class library has **no** compiler-generated mapper, so declaring it is safe. This is
  the whole reason this pattern works here and not inside a Studio project.
- **One mapper per assembly** — it is a fixed type name, so a second declaration in the same
  assembly is a duplicate-type error.
- Same assembly as the activities, or a separate `<Name>.Api` assembly? UiPath ships theirs
  separately. Either works; a separate API assembly keeps the activity library free of the
  `UiPath.CodedWorkflows` dependency. Recommend separate when the activity library is
  already published and consumed elsewhere, same-assembly when it is small and internal.

## Step 5 — Add the package references

The assembly hosting the service needs:

- `UiPath.CodedWorkflows` — registry contract, `ICodedWorkflowsServiceRegistry`
- `UiPath.Activities.Contracts` — `IWorkflowRuntime`, `WorkflowParameters`

### Pin to the OLDEST host version you support, not the newest

This is the single easiest thing to get wrong here, and it fails in someone else's project
rather than yours.

Both packages are **supplied by the Robot/Studio host at runtime**. Your DLL is compiled
against whatever version you reference, and .NET assembly binding **rolls forward but never
back**:

| Compiled against | Host carries | Result |
|---|---|---|
| 24.10.1 | 24.10.2 | Binds — higher version is accepted |
| 24.10.2 | 24.10.1 | **Fails at load.** No compile-time warning |

So reference the **lowest** version the estate runs. Reaching for the newest on the feed is
the right instinct for an application and the wrong one for a library other people consume.

Ask the user what the oldest Robot/Studio in their estate is. If they do not know, match the
version already used by the other UiPath references in the project — that is usually what
consuming projects resolve — and say plainly that you did so and what it commits them to.

Two consequences worth stating to the user:

- The floor is a **support commitment**. Anything below it fails at load with a version
  error rather than degrading, and nothing in the build warns you if you later use an API
  that only exists above the floor.
- Going lower costs nothing but access to newer API. The registry and runtime contracts
  used here have been stable across the 23.10–24.10 range.

### Do not declare them as dependencies, and do not pack them

Keep `PrivateAssets="All"` on both, matching how UiPath's own activity packages behave.

- **Packing copies** of them is wrong: the host loads its own, and a second copy invites
  duplicate-type and load-context conflicts. The registry contract in particular must be
  *the host's* type or it will not match.
- **Declaring them as NuGet dependencies** is also wrong: Studio would install them into the
  consuming process project alongside the host's copy. And it would not help anyway — a
  NuGet version range decides which *package* restores; the CLR still resolves the assembly
  version your DLL was compiled with. Fixing a load failure by widening a NuGet range is
  treating the wrong layer.

Verify after packing: the nuspec `<dependencies>` group should be **empty**.

## Step 6 — Generate the files

Use `assets/vs-templates.md`. Four pieces:

1. `MapFilePathToActivity.cs` — the shim, **exact constant name**, dictionary-backed.
2. `I<Name>Service.cs` — the public surface.
3. `<Name>Service.cs` — constructor-injected `IWorkflowRuntime`, plus the `Execute<T>` and
   `CreateInArgument<T>` helpers.
4. `<Name>Registry.cs` — the registry and the `[assembly: CodedWorkflowsServiceRegistry]`
   attribute.

Non-negotiables:

- Every Out argument you want back gets a fresh `new OutArgument<T>()` assigned, or the
  executor never collects it (internals §7).
- `Literal<T>` for value types and `string`; `LambdaValue<T>` for reference types
  (internals §7).
- `Execute()` — the extension method on `IWorkflowExecutor` from
  `UiPath.Activities.Contracts`, which returns the output dictionary. There is no
  `ExecuteWorkflow(bool)`; `using UiPath.Activities.Contracts;` is required for `Execute()`
  to resolve at all (internals §7).
- `AssemblyName` = the assembly containing the mapper. Use
  `typeof(<Name>Service).Assembly.FullName`, and only if the service and mapper share an
  assembly; otherwise name the mapper's assembly explicitly.
- Always `TryRemove` the key in a `finally`.

## Step 7 — Build, pack, verify

Build. Then pack as a NuGet package the consuming project can reference.

Build **early** — as soon as the first generated file is on disk, before the set is
complete. A compile error at that point costs one edit; the same error found after eight
files have been written costs eight. This is also how you catch a stale claim in the
templates or in internals.md: if the compiler says a member does not exist, the compiler is
right and the document is out of date. Fix the code, then go back and fix the document —
see §8 of internals.md for the re-verification commands.

Check the produced `.nupkg` before handing it over — it is a zip:

- `lib/<tfm>/` contains **your** assembly and no host-supplied ones (Step 5, internals §9).
- The nuspec `<dependencies>` group is **empty**.
- The mapper type name and the registry attribute are present in the packed DLL. A string
  scan works if you follow the UTF-8/UTF-16 and byte-alignment caveats in internals §8.

Be honest about what is verified: **service resolution cannot be tested from inside the
authoring assembly** — discovery scans *referenced* assemblies. Real verification requires
consuming the package from a separate project and confirming the service member resolves and
a call returns. Say so rather than implying the package is proven.

## Step 8 — Hand over

Show consumer usage and state what remains untested.

```csharp
var result = excel.ReadRange("Sheet1", "A1:D20");
```

---

## Failure modes

| Symptom | Cause |
|---|---|
| `NullReferenceException` from `ExecuteWorkflow` | Mapper type name is not the exact constant, or `AssemblyName` names an assembly without the mapper (internals §2) |
| Duplicate type / CS0101 on the mapper | Two mapper declarations in one assembly, or it was placed in a Studio-compiled project (internals §2) |
| `KeyNotFoundException` on the output | Output key is the OutArgument **property name**; `"Result"` for `CodeActivity<T>` |
| Output is always null | The OutArgument was left unassigned instead of `new OutArgument<T>()` (internals §7) |
| Validation error on an argument | Reference type passed through `Literal<T>` instead of `LambdaValue<T>` (internals §7) |
| Activity returns nulls / throws on job context | It needs runtime extensions and was called directly instead of through the harness (Step 3) |
| Service member does not resolve in the consumer | Registry attribute missing, version mismatch, or being tested from the authoring assembly |
| `FileLoadException` / "could not load ... Version=24.10.2.0" in a consuming project, but it builds fine for you | Compiled against a **newer** host assembly than the consumer's host carries. Binding rolls forward, never back — lower the reference to the oldest supported version (Step 5, internals §9). Widening a NuGet range does not fix this |
| Duplicate type identity, or the registry contract not matching at runtime | A host-supplied assembly was packed into the package instead of left `PrivateAssets="All"` (internals §9) |

## Fragility note

This pattern depends on `UiPath.MapFilePathToActivity_93063903935340c8aab522ec692cb083`
being a stable compiler constant. It has held across the versions in internals §Provenance,
and UiPath's own shipped package depends on it too, which makes it unlikely to churn
casually — but it is not a documented API. After a Studio major upgrade, re-verify with the
commands in internals §8 before assuming a runtime failure is your own bug.
