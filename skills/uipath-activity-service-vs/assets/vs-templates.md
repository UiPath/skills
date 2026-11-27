# Templates — Visual Studio C# activity service

Substitute:

- `<Ns>` — namespace, default `<RootNamespace>.Api`
- `<Name>` — PascalCase service name, e.g. `Excel`
- `<servicename>` — the member consumers type, e.g. `excel`

---

## 1. `MapFilePathToActivity.cs`

**The type name is a fixed constant. Do not rename it, do not add a suffix of your own, do
not "tidy" it.** A different name resolves to null and throws `NullReferenceException`.

```csharp
using System.Activities;
using System.Collections.Concurrent;

namespace UiPath
{
    /// <summary>
    /// Shim that lets the workflow runtime resolve an in-memory Activity instance.
    ///
    /// The runtime resolves a workflow "relative path" to an Activity through a type with
    /// this exact fully-qualified name, taken from CompilerConstants.MapperValue in
    /// UiPath.ActivityCompiler.dll. In a compiled UiPath project this class is generated
    /// with a switch over the project's XAML files; here it is dictionary-backed so an
    /// arbitrary Activity can be handed to the runtime under a synthetic key.
    ///
    /// One declaration per assembly — the name is fixed, so a second is a duplicate type.
    /// </summary>
    public static class MapFilePathToActivity_93063903935340c8aab522ec692cb083
    {
        internal static readonly ConcurrentDictionary<string, Activity> DynamicMapper
            = new ConcurrentDictionary<string, Activity>();

        public static Activity MapFilePathToActivity(string relativePath)
            => DynamicMapper.TryRemove(relativePath, out var activity) ? activity : null;
    }
}
```

Keep the comment. Without it the name looks like line noise and someone will rename it.

---

## 2. `I<Name>Service.cs`

```csharp
using System;

namespace <Ns>
{
    public interface I<Name>Service
    {
        /// <summary>One line, in the caller's terms.</summary>
        /// <param name="sheetName">What it is and any constraint worth knowing.</param>
        string[][] ReadRange(string sheetName, string range, int timeoutMs = 3600000);
    }
}
```

Design rules:

- One in-argument → one parameter, named for the caller not the activity property.
- Single out-argument → return it directly. Several → return a small result type; do not
  leak `IDictionary<string, object>`.
- Give timeouts and other rarely-set arguments defaults.
- Keep the surface to plain types and your own models; every type here is a dependency for
  consumers.
- XML-doc everything — it is all a package consumer gets.

---

## 3. `<Name>Service.cs`

```csharp
using System;
using System.Activities;
using System.Activities.Expressions;
using System.Collections.Generic;
using System.Linq.Expressions;
using UiPath.Activities.Contracts;

namespace <Ns>
{
    internal class <Name>Service : I<Name>Service
    {
        private readonly IWorkflowRuntime _workflowRuntime;

        public <Name>Service(IWorkflowRuntime workflowRuntime)
        {
            _workflowRuntime = workflowRuntime
                ?? throw new ArgumentNullException(nameof(workflowRuntime));
        }

        public string[][] ReadRange(string sheetName, string range, int timeoutMs = 3600000)
        {
            if (string.IsNullOrEmpty(sheetName))
                throw new ArgumentException("sheetName is required.", nameof(sheetName));
            if (string.IsNullOrEmpty(range))
                throw new ArgumentException("range is required.", nameof(range));

            var activity = new ReadRangeActivity
            {
                SheetName = CreateInArgument(sheetName),
                Range     = CreateInArgument(range),
                Timeout   = CreateInArgument(timeoutMs),
                Values    = new OutArgument<string[][]>(),   // REQUIRED, or nothing is collected
            };

            return Execute<string[][]>(activity, "Values");  // key = OutArgument property name
        }

        /// <summary>
        /// Runs an Activity through the UiPath workflow runtime and returns one output.
        ///
        /// The runtime only executes workflows identified by relative path, so the activity
        /// is stashed under a synthetic GUID key that the mapper shim resolves. AssemblyName
        /// must name the assembly containing that shim.
        /// </summary>
        private TResult Execute<TResult>(Activity activity, string outputKey)
        {
            var key = Guid.NewGuid().ToString();

            var parameters = new WorkflowParameters(key, new Dictionary<string, object>())
            {
                AssemblyName = typeof(<Name>Service).Assembly.FullName
            };

            UiPath.MapFilePathToActivity_93063903935340c8aab522ec692cb083
                  .DynamicMapper.TryAdd(key, activity);
            try
            {
                // Execute() is an extension method on IWorkflowExecutor, from
                // UiPath.Activities.Contracts — it wraps BeginExecute/EndExecute and
                // returns the output dictionary. There is no ExecuteWorkflow overload.
                var outputs = _workflowRuntime.CreateWorkflowExecutor(parameters)
                                              .Execute();
                return (TResult)outputs[outputKey];
            }
            finally
            {
                UiPath.MapFilePathToActivity_93063903935340c8aab522ec692cb083
                      .DynamicMapper.TryRemove(key, out _);
            }
        }

        /// <summary>
        /// Literal&lt;T&gt; is rejected for reference types at validation, so those go
        /// through LambdaValue&lt;T&gt;.
        /// </summary>
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
    }
}
```

Notes:

- `internal` on the implementation is deliberate — consumers bind to the interface, and the
  registry can still register a non-public implementation.
- If the mapper lives in a **different** assembly from the service, `AssemblyName` must name
  the mapper's assembly, not `typeof(<Name>Service).Assembly`.
- If the service calls refactored plain methods instead (Step 3 of the skill), drop
  `Execute<T>`, `CreateInArgument<T>` and the mapper entirely — do not keep dead scaffolding.

---

## 4. `<Name>Registry.cs`

```csharp
using System;
using System.Activities;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using <Ns>;

[assembly: CodedWorkflowsServiceRegistry(typeof(<Name>Registry))]

namespace <Ns>
{
    internal class <Name>Registry : ICodedWorkflowsServiceRegistry
    {
        internal const string ServiceName = "<servicename>";

        public IEnumerable<string> AutoImportedNamespaces => new string[]
        {
            "<Ns>"
        };

        public IDictionary<string, Type> AutoImportedTypes => new Dictionary<string, Type>
        {
            { ServiceName, typeof(I<Name>Service) }
        };

        public void Register(
            ICodedWorkflowsServiceLocator serviceLocator,
            ActivityContext initialActivityContext)
        {
            serviceLocator.RegisterType<I<Name>Service, <Name>Service>();
        }
    }
}
```

`AutoImportedNamespaces` should list the namespaces of types appearing on the public service
surface — add the namespace of any model type you return. Nothing more, or you risk breaking
a consumer's compile with a namespace they cannot resolve.

The assembly attribute goes after the `using` directives, before the `namespace`.

---

## Consumer snippet for the handover

```csharp
var values = <servicename>.ReadRange("Sheet1", "A1:D20");
```
