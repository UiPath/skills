# Coded-Workflow Service Internals (shared reference)

Shared mechanics behind all three `uipath-activity-service-*` skills. Read this before
generating any service code.

**Provenance.** Every claim below was verified by decompilation in August 2026 against:

| Component | Version |
|---|---|
| UiPath Studio / Robot | `26.0.198-cloud.24248` |
| `UiPath.CodedWorkflows` | `24.10.2` (latest on the UiPath-Official feed) |
| `UiPath.DocumentUnderstanding.Activities` | `3.4.0-preview` |
| `UiPath.Activities.Contracts` | `23.4.1` (latest on the feed) and `26.0.198` (shipped inside Robot) |

**Note on `UiPath.Activities.Contracts`.** The newest version *published to NuGet* is
`23.4.1`, but the Robot loads its own `26.0.198` copy at runtime, so you always compile
against an older contract than you execute against. On the surface these skills use —
`IWorkflowRuntime.CreateWorkflowExecutor`, `WorkflowParameters`, `IWorkflowExecutor`,
the `Execute()` extension — the two versions **agree**, so the gap is benign. 26.0 adds
`IWorkflowExecutor.GetSuspendedInstanceId()` and extra `IInvokeParameters` members; neither
is used here, and `WorkflowParameters` is a class, so the added interface members do not
affect us. Re-check this if you start using anything beyond that surface.

If the user is on a materially different Studio major version, re-verify §2 and §6 before
relying on them — see §8 for the exact commands. Do not silently assume they still hold.

---

## 1. The service registry contract

Three pieces, all in one assembly, make `myservice.DoThing()` resolve inside a consuming
coded workflow with no `using` and no declaration:

```csharp
[assembly: CodedWorkflowsServiceRegistry(typeof(MyRegistry))]

public class MyRegistry : ICodedWorkflowsServiceRegistry
{
    // namespaces injected into every generated coded workflow in consuming projects
    public IEnumerable<string> AutoImportedNamespaces => new[] { "My.Service.Namespace" };

    // dictionary KEY becomes the member name the user types: `myservice.`
    public IDictionary<string, Type> AutoImportedTypes =>
        new Dictionary<string, Type> { { "myservice", typeof(IMyService) } };

    public void Register(ICodedWorkflowsServiceLocator serviceLocator,
                         ActivityContext initialActivityContext)
        => serviceLocator.RegisterType<IMyService, MyService>();
}
```

Facts that matter:

- `CodedWorkflowsServiceRegistryAttribute` is an **ordinary assembly-level attribute**.
  Nothing infers it from implementing the interface, and Studio has no UI for it. Studio's
  generated `AssemblyInfo` carries only `project.json` metadata.
- You **can** declare it from inside a Studio project by putting it in a Coded **Source
  File** — C# permits `[assembly: ...]` in any file of the compilation, after the `using`
  directives and before any type declaration.
- Discovery happens by scanning **referenced** assemblies at runtime init of the consuming
  project. **Testing the registry inside its own authoring project does not work.** Build,
  publish, and consume from a separate project.
- `AutoImportedNamespaces` is injected into consumers' generated workflows. Only list
  namespaces whose types appear on your public service surface. Importing namespaces from a
  transitive dependency needlessly risks breaking a consumer's compile.
- `RegisterType<TService, TImpl>` defaults to `CodeServiceRegistrationType.Singleton`.

## 2. The `MapFilePathToActivity` constant

The runtime resolves a workflow "relative path" to an `Activity` through a generated type
whose fully-qualified name is a **hardcoded global constant** — not a per-project hash:

```
UiPath.MapFilePathToActivity_93063903935340c8aab522ec692cb083
```

Source, in `UiPath.ActivityCompiler.dll`:

```csharp
internal static class CompilerConstants
{
    public static readonly string MapperKey   = "MapFilePathToActivity";
    public static readonly string MapperValue = "UiPath." + MapperKey + "_93063903935340c8aab522ec692cb083";
}
```

Every compiled UiPath project gets that identical type name. A generated instance looks like:

```csharp
namespace UiPath
{
    public static class MapFilePathToActivity_93063903935340c8aab522ec692cb083
    {
        public static Activity MapFilePathToActivity(string relativePath)
        {
            relativePath = relativePath?.Replace("\\\\", "\\").Replace('\\', '/');
            if (relativePath == "Populate Razor Template.xaml") return new Populate_Razor_Template();
            if (relativePath == "Add Razor Template.cs")        return new Add_Razor_TemplateActivity();
            return null;
        }
    }
}
```

Consequences:

- A **custom-named** mapper is invisible to the runtime. The lookup returns `null` and the
  executor throws `NullReferenceException` — the single most common failure in this area.
- The mapper **cannot** live in a Studio-compiled project assembly. The compiler injects its
  own generated `MapFilePathToActivity.cs` into that same compilation, so declaring your own
  is a duplicate-type error. This is why UiPath ships theirs in a plain C# classlib.
- Backslashes are normalised to forward slashes and the comparison is otherwise exact,
  including spaces and case.

## 3. The Studio library two-assembly split

A Studio **library** project compiles to two assemblies:

| Assembly | Contains |
|---|---|
| `<Name>.Core.dll` | hand-written coded workflows, your service/registry classes, the generated `WorkflowRunnerService` |
| `<Name>.dll` | `UiPath.MapFilePathToActivity_9306...`, XAML-compiled activities, generated wrapper activities |

So `this.GetType().Assembly.FullName` evaluated inside a service class yields **`.Core`**,
which has no mapper → null activity → `NullReferenceException`.

Resolve it properly:

```csharp
_services.Container.Resolve<ILibraryAssemblyProvider>()
         .GetLibraryAssemblyName(GetType().Assembly)   // Core -> outer
```

## 4. Never `new` a CodedWorkflow

```csharp
var wf = new My_Coded_Workflow();
wf.Execute(a, b);          // NullReferenceException inside Log(...)
```

`CodedWorkflowBase.services` is `{ get; private set; }`, populated by
`OnWorkflowInitialization` when the **runtime** hosts the workflow. A constructed instance
has `services`, `serviceContainer`, `workflowRuntime` and `executorRuntime` all null, so the
first call to `Log(...)`, `system.*`, or `workflows.*` throws.

Always invoke through the runtime instead (§5 / §6).

## 5. Key interfaces

In `UiPath.CodedWorkflows.Interfaces`:

```csharp
public interface ICodedWorkflowServices
{
    IOutputLoggerService       OutputLoggerService { get; }
    IWorkflowInvocationService WorkflowInvocationService { get; }
    IOrchestratorClientService OrchestratorClientService { get; }
    ICodedWorkflowsServiceContainer Container { get; }
}

public interface IWorkflowInvocationService
{
    IDictionary<string, object> RunWorkflow(
        string workflowFilePath, IDictionary<string, object> inputArguments = null,
        TimeSpan? timeout = null, bool isolated = false,
        InvokeTargetSession targetSession = 0, string assemblyName = null);

    Task<IDictionary<string, object>> RunWorkflowAsync(/* same shape */);
}

public interface ILibraryAssemblyProvider
{
    string GetLibraryAssemblyName(Assembly codeAssembly);
}
```

`ICodedWorkflowServices` is registered in the same locator your registry uses
(`locator.RegisterType<ICodedWorkflowServices, CodedWorkflowServices>()`), so it
**constructor-injects into your service class**. `IWorkflowRuntime` (from
`UiPath.Activities.Contracts`) also injects — that is what UiPath's own DU package takes.

Which to inject:

- **Studio library exposing its own workflows** → `ICodedWorkflowServices`. Higher-level,
  handles assembly-name resolution for you.
- **Plain classlib executing raw `Activity` instances** → `IWorkflowRuntime`, and drive
  `CreateWorkflowExecutor(parameters).Execute()` yourself (§7).

`IWorkflowExecutor` itself is minimal — `BeginExecute`, `EndExecute`, `Cancel`, and (26.0
only) `GetSuspendedInstanceId`. The synchronous `Execute()` used throughout these skills is
an extension method over the Begin/End pair, not an interface member.

## 6. The generated `WorkflowRunnerService` (Studio libraries only)

The Studio compiler emits a `public class WorkflowRunnerService` into `<Name>.Core.dll`,
with one method per workflow file:

```csharp
public class WorkflowRunnerService
{
    public WorkflowRunnerService(ICodedWorkflowServices services) { ... }

    public void Add_Razor_Template(string templateKey, string templateSourceText, bool isolated = false)
        => _services.WorkflowInvocationService.RunWorkflow("Add Razor Template.cs",
               new Dictionary<string, object> { { "templateKey", templateKey },
                                                { "templateSourceText", templateSourceText } },
               null, isolated, 0, GetAssemblyName());

    private string GetAssemblyName()
        => _services.Container.Resolve<ILibraryAssemblyProvider>()
                    .GetLibraryAssemblyName(GetType().Assembly);
}
```

Naming rules observed:

- Method name = file name minus extension, with non-identifier characters replaced by `_`.
  `Add Razor Template.cs` → `Add_Razor_Template`;
  `Populate Razor Template_Test.xaml` → `Populate_Razor_Template_Test`.
- Parameters = the workflow's **In** arguments in declaration order, named exactly as
  declared (XAML `x:Property Name`, or the `[Workflow]` method's parameter names), plus a
  trailing `bool isolated = false`.
- A workflow with exactly one Out argument returns it **unwrapped and cast**
  (`...RunWorkflow(...)["PopulatedText"]`). No Out arguments → `void`.
- **Unverified:** the shape for two or more Out arguments. If a target workflow has
  several, read the generated signature (§8) rather than guessing.

Prefer delegating to this class over hand-rolling `RunWorkflow` calls: it keeps argument
names and the assembly-name resolution correct, and a renamed workflow file becomes a
compile error instead of a runtime null.

### 6a. Version-dependent constructor shape — build and read it, don't assume

The **method** signatures above (name, In-argument params, unwrapped single Out) are stable
across versions. The **constructor** is not. Two shapes are confirmed in the wild:

- `UiPath.CodedWorkflows` **24.10.2**: `WorkflowRunnerService(ICodedWorkflowServices services)`
  — the shape the templates in `assets/service-templates.md` assume. Construct with
  `new WorkflowRunnerService(services)` and you are done; it resolves the assembly name
  internally.
- Older builds (seen on **23.10.x**, and on projects still pinned to an older package):
  a delegate-handler constructor
  ```csharp
  public WorkflowRunnerService(
      Func<string, IDictionary<string, object>, TimeSpan?, bool, InvokeTargetSession,
           IDictionary<string, object>> runWorkflowHandler)
  ```
  Here `new WorkflowRunnerService(services)` does **not** compile. The handler has five
  parameters — no `assemblyName` — so *you* must inject the resolved assembly name (§3) when
  wiring it up:
  ```csharp
  var assemblyName = services.Container.Resolve<ILibraryAssemblyProvider>()
                             .GetLibraryAssemblyName(GetType().Assembly);
  _workflows = new WorkflowRunnerService(
      (path, args, timeout, isolated, targetSession) =>
          services.WorkflowInvocationService.RunWorkflow(
              path, args, timeout, isolated, targetSession, assemblyName));
  ```

The fastest way to settle which shape you have is the Step 6 build: `new
WorkflowRunnerService(services)` either compiles or fails with `CS1729` naming the real
constructor. If it fails, switch to the delegate form above. Bumping the package to 24.10.2
(and rebuilding) is the other option — it regenerates the runner in the `ICodedWorkflowServices`
shape — but that raises the consumer's runtime version floor (§9), so confirm the upgrade
with the user rather than doing it silently.

### 6b. The runner is only generated when a coded file exists, and may be inline-only

Two facts that make the runner hard to *find* before it exists:

- **Generation trigger.** The compiler emits `WorkflowRunnerService` only when the project
  contains at least one coded `.cs` file. A library with purely XAML workflows produces no
  runner on build. The service classes you author (`assets/service-templates.md`) are
  themselves coded source files, so they are what trips generation — the runner materialises
  in the same build that first compiles them. Do not hunt for it, or try to `new` it, before
  any coded file is in the project.
- **Location varies.** On some versions the runner is persisted as a source file at
  `.local/.codedworkflows/WorkflowRunnerService.cs`; on others (observed with 24.10.2) it is
  emitted straight into `<Name>.Core.dll` at compile time with **no** intermediate `.cs`. So
  a missing source file does **not** mean a missing runner. To read its real signature,
  decompile the compiled `Core.dll` (§8) rather than relying on the `.local` source.

## 7. Argument construction (raw `Activity` execution only)

When you build `Activity` instances by hand (skills `-vs` and `-unowned`):

```csharp
private static InArgument<T> CreateInArgument<T>(T value)
{
    var arg = Argument.Create(typeof(T), ArgumentDirection.In);
    if (value == null) return arg as InArgument<T>;

    if (typeof(T).IsValueType || typeof(T) == typeof(string))
        arg.Expression = new Literal<T>(value) { DisplayName = value.ToString() };
    else
        arg.Expression = new LambdaValue<T>(c => value) { DisplayName = value.ToString() };

    return arg as InArgument<T>;
}
```

- `Literal<T>` rejects reference types at validation — use `LambdaValue<T>` for those.
- Guard the null case first; `value.ToString()` on the `DisplayName` would throw.
- **Every Out argument you want back must be assigned a fresh `new OutArgument<T>()`**, or
  the executor will not bind and collect it.
- Outputs come back keyed by the root activity's **OutArgument property name**. For
  `CodeActivity<T>` / `Activity<T>` that key is `"Result"`.
- **`Execute()` returns the output dictionary.** It is an extension method on
  `IWorkflowExecutor`, in `UiPath.Activities.Contracts`:

  ```csharp
  public static class WorflowExecutorExtensions   // sic — UiPath's typo, not ours
  {
      public static IDictionary<string, object> Execute(this IWorkflowExecutor executor)
          => Task.Factory.FromAsync(executor.BeginExecute, executor.EndExecute, null).Result;
  }
  ```

  Because it is an extension method, `using UiPath.Activities.Contracts;` is required or it
  will not resolve. There is **no** `ExecuteWorkflow(bool)` overload — earlier revisions of
  this document claimed one, and code written against it does not compile.

## 8. Re-verifying after a Studio upgrade

```bash
dotnet tool install -g ilspycmd     # once
```

Confirm the mapper constant still matches §2:

```powershell
ilspycmd "$env:LOCALAPPDATA\Programs\UiPathPlatform\Studio\<version>\UiPath.ActivityCompiler.dll" -o out
# then grep the output for: MapperValue
```

Read the generated runner signatures for a built Studio library:

```powershell
ilspycmd "<project>\.local\Compiler\<hash>\<Name>\lib\net8.0\<Name>.Core.dll" -o out
# then grep the output for: class WorkflowRunnerService
```

Confirm the executor surface in §7 — do this against the **Robot's** copy, which is what
actually runs, not just the NuGet package you compile against:

```powershell
ilspycmd "$env:LOCALAPPDATA\Programs\UiPathPlatform\Robot\<version>\UiPath.Activities.Contracts.dll" -o out
# then grep the output for: interface IWorkflowExecutor
# and for:                  WorflowExecutorExtensions      <- UiPath's typo, spell it this way
```

Studio and Robot live under `%LOCALAPPDATA%\Programs\UiPathPlatform`.

**These three checks are the whole list.** They exist because each has an answer no compiler
can give you: a magic string, a generated signature, and an assembly the Robot substitutes
at runtime. Everything else in this document is ordinary API surface — if it has moved, the
build will say so, by name, about the exact assembly you bind to.

So the order is: **write the code, build, and decompile only what the build could not
settle.** Never decompile to inventory the user's own activities or workflows — that source
is in the working directory. Never decompile to look up a property's type — that is one
build away. If nothing has been written to the project yet and `ilspycmd` has already run
more than once, the sequence has gone wrong; build first.

**Scanning tip.** When string-searching UiPath DLLs, decode as **UTF-16** as well as UTF-8 —
type/member names sit in the UTF-8 metadata heap, but `ldstr` literals are UTF-16, so a
UTF-8-only scan silently misses them. Try **both byte alignments**: a UTF-16 literal
starting at an odd offset is missed by a single aligned decode, which reads as absent when
it is present.

## 9. Host-supplied assemblies and version floors

`UiPath.CodedWorkflows`, `UiPath.Activities.Contracts` and `UiPath.Activities.Api` are
**supplied by the Robot/Studio host at runtime**. You compile against them; you do not ship
them. Three rules follow, and all three fail in a *consumer's* project rather than yours.

**1. Reference the oldest host version you support, never the newest.** .NET assembly
binding rolls forward but never back:

| Compiled against | Host carries | Result |
|---|---|---|
| 24.10.1 | 24.10.2 | Binds — a higher version is accepted |
| 24.10.2 | 24.10.1 | **Fails at load**, with no compile-time warning |

Picking the newest on the feed is correct for an application and wrong for a library other
people consume. This is why compiling `UiPath.Activities.Contracts` at 23.4.1 works against
a Robot carrying 26.0.198 — forward roll — while the reverse would not.

**2. Keep `PrivateAssets="All"`.** The package must not carry them as dependencies. Studio
would install them into the consuming process project alongside the host's own copy. After
packing, the nuspec `<dependencies>` group should be **empty**.

**3. Never pack copies of them.** The host loads its own. A second copy invites duplicate
type identities and load-context conflicts — and the registry contract in §1 must be *the
host's* type or it will not match at all.

A corollary worth stating to users: widening a **NuGet** version range does not fix an
assembly-load failure. NuGet decides which package restores; the CLR still resolves the
assembly version stamped into your DLL at compile time. They are different layers, and only
the compile-time reference moves the binding.
