---
name: uipath-activity-service-studio
description: "Expose the workflows of a UiPath Studio **library** project (XAML activities and coded workflows you own) as a coded-workflow service, so consumers call them as `myservice.DoThing(...)` instead of dragging activities. Inventories the library's workflows, confirms which to expose and what to name the service, then generates the interface, service and registry classes and verifies the build."
when_to_use: "User owns a UiPath **Studio library** project (has project.uiproj with designOptions.outputType == 'Library') and wants its activities callable from coded workflows. Triggers: 'expose these activities to coded workflows', 'make a coded API for my library', 'call my library from a coded workflow', 'add a service to my UiPath library'. NOT for C# activity projects built in Visual Studio (use uipath-activity-service-vs) and NOT for third-party activities you do not own (use uipath-activity-service-unowned)."
---

# Expose a UiPath Studio Library as a Coded-Workflow Service

Turns a Studio library's workflows into a typed service that consuming coded workflows call
as `myservice.DoThing(...)`.

> **Read `references/internals.md` in full before generating any code.** It carries the
> verified mechanics — the two-assembly split, the mapper constant, the registry contract,
> the generated `WorkflowRunnerService` naming rules. Most failures in this area trace back
> to a fact in that file that was skipped or half-remembered. Do not substitute prior
> knowledge; the details are version-specific and counter-intuitive.

---

## Step 0 — Confirm you are in the right skill

Check the project root for `project.uiproj` and read `project.json`:

- `designOptions.outputType` must be `"Library"`. If it is `"Process"`, the user wants to
  *consume* a service, not author one — stop and clarify.
- No `project.uiproj` but a `.csproj` with `CodeActivity` subclasses → wrong skill, use
  **`uipath-activity-service-vs`**.
- The activities belong to a NuGet package the user did not author → wrong skill, use
  **`uipath-activity-service-unowned`**.

Note `project.json` → `name`, and `dependencies` (you will need `UiPath.CodedWorkflows`;
if absent, it must be added before the generated code will compile).

## Step 1 — Inventory the workflows

Enumerate candidates from the project directory:

- `*.xaml` — read each one's `x:Property` elements for argument names, directions and
  types. `Type="InArgument(x:String)"` → in, `OutArgument(...)` → out. Note
  `RequiredArgumentAttribute` where present.
- `*.cs` coded workflows — find the `[Workflow]`-attributed method; its parameters are the
  in-arguments and its return type is the output.

Exclude from the candidate list:

- Anything listed in `project.json` → `designOptions.libraryOptions.privateWorkflows`.
- Test cases: files whose `fileInfoCollection` entry has `testCaseType`, or that match
  `*_Test.xaml` / `*Test.cs` conventions.
- `.local/`, `.tmh/`, `.objects/`, `.templates/`, `.entities/` — build and tooling folders.

## Step 2 — Confirm scope with the user

Present the inventory as a table: workflow file, in-arguments, out-arguments, and a
proposed service method name. Ask which to expose. Default to all non-test, non-private
workflows, but **do not proceed without confirmation** — exposing a workflow makes it public
API for every consumer of the package.

Where a workflow's arguments are unclear or the name is cryptic, ask rather than guess.

## Step 3 — Agree the service name

The service name is the member consumers type (`razor.`, `du.`, `excel.`). Rules:

- Short, lowercase, no punctuation — it reads as a variable in consumer code.
- Distinct enough not to collide with another library's service name in the same project;
  a collision here is a consumer-side compile break the user cannot easily fix.
- Derive a suggestion from the project name: `Roboyo.Razor.Activities` → `razor`,
  `Contoso.Excel.Helpers` → `excel`.

**Suggest one and ask for confirmation.** Also confirm the .NET namespace for the generated
classes; default to `<ProjectName>.CodedWorkflowService`.

## Step 4 — Build first, then read the generated runner

The generated `WorkflowRunnerService` must exist before your service can delegate to it.
If the project has never been built, or workflows changed since the last build, build now.

**Chicken-and-egg for XAML-only libraries:** the compiler only generates
`WorkflowRunnerService` when the project contains at least one coded `.cs` file. A library
whose workflows are all XAML has *no* runner yet, and a build produces none — so there is
nothing to read at this step. That is expected. Your Step 5 service files are themselves
coded source files, so writing them is what triggers generation: the runner appears in the
*same* build that first compiles your service. In that case, treat Step 4 as "build to
confirm the project is healthy", write the files in Step 5, and let the Step 6 build
generate the runner and check your delegating calls together. Do not chase a missing runner
before any coded file exists — see `references/internals.md` §6.

Then write your delegating calls using the naming rules in `references/internals.md` §6 and
**let the build check them**. A wrong method name or parameter list is a compile error
naming the exact problem — that is the cheapest and most reliable check available, and it is
about the assembly you actually reference.

Decompile the Core assembly only when the build has already disagreed with you, or when a
target workflow has **two or more Out arguments** — §6 flags that return shape as
unverified, so it is the one case worth reading rather than guessing:

```powershell
ilspycmd "<project>\.local\Compiler\<newest-hash>\<Name>\lib\net8.0\<Name>.Core.dll" -o out
# grep output for: class WorkflowRunnerService
```

Pick the **newest** directory under `.local\Compiler\` by last-write time. If `ilspycmd` is
not installed, `dotnet tool install -g ilspycmd`.

Do not decompile pre-emptively to confirm names the rules already cover — that is slower
than building and answers a question the build would have answered anyway.

## Step 5 — Generate the three files

Create a `Coded Workflow Service/` folder in the project root containing
`I<Name>Service.cs`, `<Name>Service.cs`, `<Name>Registry.cs`.

Use `assets/service-templates.md` for the exact shapes. Non-negotiables:

- The service class takes **`ICodedWorkflowServices`** by constructor injection and
  delegates to `WorkflowRunnerService`. How you construct that runner is version-dependent
  (`new WorkflowRunnerService(services)` vs a delegate handler) — see §6a and let the build
  confirm the shape. Never `new` a `CodedWorkflow` (`references/internals.md` §4).
- Never set an assembly name by hand. `WorkflowRunnerService` resolves it through
  `ILibraryAssemblyProvider` — that is what makes the Core-vs-outer split work (§3).
- The `AutoImportedTypes` dictionary key **is** the service name from Step 3.
- `AutoImportedNamespaces` lists only the service's own namespace unless a dependency's
  types genuinely appear on the public surface.
- Keep the public interface in terms of plain types (`string`, `object`, `Type`, your own
  models). Every type on the surface becomes a dependency for consumers.
- Validate arguments in the service and throw `ArgumentException`/`ArgumentNullException`
  with the parameter name — the failure then names the caller's mistake instead of surfacing
  as an opaque workflow fault.

## Step 6 — Build and verify

Build the library. Then confirm honestly:

- It compiles.
- The `[assembly: CodedWorkflowsServiceRegistry(...)]` attribute landed in the Core
  assembly.

**You cannot verify service resolution from inside the authoring project** — discovery scans
*referenced* assemblies (§1). Real verification needs the package published and consumed
from a separate process project. Say so rather than implying it is proven.

## Step 7 — Hand over

Show the consumer usage:

```csharp
razor.AddRazorTemplate("welcome-layout", layoutCshtml);
var html = razor.PopulateRazorTemplate("welcome-body", model);
```

Tell the user what remains: publish the package, reference it from a process project, and
confirm the service member resolves.

---

## Judgement calls worth surfacing

- **A coded workflow that is pure C# does not need a runtime round trip.** If a workflow is
  a few lines with no activities, the service can do the work directly and log via
  `_services.OutputLoggerService`. Going through `RunWorkflow` costs a workflow execution.
  Keep the invocation when the workflow must stay a published activity with identical
  behaviour both ways; skip it when the service is the only consumer. Raise the trade-off,
  let the user choose.
- **XAML workflows must go through the runner.** There is no alternative for them.
- **Renaming a workflow file breaks the generated runner method name**, which surfaces as a
  compile error in the service. That is desirable — mention it so the user is not surprised.

## Failure modes

| Symptom | Cause |
|---|---|
| `NullReferenceException` inside `Log(...)` | A `CodedWorkflow` was constructed with `new` instead of invoked through the runtime (§4) |
| `NullReferenceException` from `ExecuteWorkflow` | Assembly name resolved to `.Core`, which has no mapper (§3) |
| Service member does not resolve in the consumer | Registry attribute missing, or being tested from inside the authoring project (§1) |
| `KeyNotFoundException` on the output | Wrong out-argument key; it is the argument's declared name (§6) |
| Consumer project fails to compile after referencing | `AutoImportedNamespaces` names a namespace the consumer cannot resolve (§1) |
