using System.Activities;
using System.Activities.Tracking;
using System.Activities.Validation;
using System.Globalization;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Xaml;
using XamlRunner;

// xaml-runner inspect <file.xaml> [--out result.json]
// xaml-runner run <file.xaml> [--input-file args.json] [--cwd dir] [--timeout seconds] [--out result.json]
//
// Both print one JSON object. The exit code is 0 whenever the runner did its job, including
// for a workflow that failed to load or faulted: those are verdicts, carried in the JSON.

if (args.Length < 2 || args[0] is not ("inspect" or "run"))
{
    Console.Error.WriteLine("usage: xaml-runner inspect|run <file.xaml> [--input-file f] [--cwd d] [--timeout s] [--out f]");
    return 64;
}

// Pinned so a scenario's decimal and date formatting does not depend on the grading host's locale.
CultureInfo.DefaultThreadCurrentCulture = CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentCulture = CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;

var opts = new Dictionary<string, string>();
for (var i = 2; i + 1 < args.Length; i += 2) opts[args[i].TrimStart('-')] = args[i + 1];
var xamlPath = Path.GetFullPath(args[1]);

// Force the activity assembly into the load context so the XAML schema context can resolve
// the http://schemas.uipath.com/workflow/activities namespace.
_ = typeof(UiPath.Core.Activities.LogMessage).Assembly;
_ = typeof(UiPath.Core.BusinessRuleException).Assembly;

var result = args[0] == "inspect" ? Inspect(xamlPath) : Run(xamlPath, opts);
var text = result.ToJsonString(new JsonSerializerOptions { WriteIndented = true, Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping });
if (opts.TryGetValue("out", out var outPath)) File.WriteAllText(outPath, text);
else Console.Out.WriteLine(text);
return 0;

static JsonObject LoadError(Exception ex)
{
    var inner = ex;
    while (inner.InnerException is not null && inner is not XamlException) inner = inner.InnerException;
    var err = new JsonObject { ["type"] = inner.GetType().FullName, ["message"] = inner.Message };
    if (inner is XamlException xe && xe.LineNumber > 0) { err["line"] = xe.LineNumber; err["column"] = xe.LinePosition; }
    return err;
}

static JsonArray Issues(IEnumerable<ValidationError> errors) => new(errors
    .Select(e => (JsonNode)new JsonObject { ["message"] = e.Message, ["activity"] = e.Source?.DisplayName, ["property"] = e.PropertyName })
    .ToArray());

static JsonArray Arguments(Activity activity)
{
    var list = new JsonArray();
    if (activity is not DynamicActivity dyn) return list;
    foreach (var p in dyn.Properties)
    {
        var generic = p.Type.IsGenericType ? p.Type.GetGenericTypeDefinition() : null;
        var direction = generic == typeof(InArgument<>) ? "In" : generic == typeof(OutArgument<>) ? "Out" : generic == typeof(InOutArgument<>) ? "InOut" : "Property";
        var type = generic is null ? p.Type : p.Type.GetGenericArguments()[0];
        list.Add(new JsonObject { ["name"] = p.Name, ["direction"] = direction, ["type"] = type.FullName });
    }
    return list;
}

static bool IsExpression(Activity a)
{
    var ns = a.GetType().Namespace ?? "";
    return ns.StartsWith("Microsoft.VisualBasic.Activities") || ns.StartsWith("Microsoft.CSharp.Activities") || ns == "System.Activities.Expressions";
}

static JsonArray Activities(Activity root)
{
    var list = new JsonArray();
    var seen = new HashSet<Activity>(ReferenceEqualityComparer.Instance);
    void Walk(Activity a)
    {
        if (!seen.Add(a)) return;
        if (!IsExpression(a) && a != root)
            list.Add(new JsonObject { ["type"] = a.GetType().FullName?.Split('`')[0], ["displayName"] = a.DisplayName });
        foreach (var child in WorkflowInspectionServices.GetActivities(a)) Walk(child);
    }
    Walk(root);
    return list;
}

static JsonObject Inspect(string path)
{
    var result = new JsonObject { ["file"] = path };
    Activity activity;
    ValidationResults vr;
    try { (activity, vr, var retries) = XamlLoader.LoadAndValidate(path); result["compile_retries"] = retries; }
    catch (Exception ex)
    {
        result["loaded"] = false;
        result["errors"] = new JsonArray(LoadError(ex));
        return result;
    }
    result["loaded"] = true;
    result["errors"] = Issues(vr.Errors);
    result["warnings"] = Issues(vr.Warnings);
    result["arguments"] = Arguments(activity);
    result["activities"] = Activities(activity);
    return result;
}

static JsonObject Run(string path, Dictionary<string, string> opts)
{
    var result = new JsonObject { ["file"] = path };
    Activity activity;
    ValidationResults vr;
    try { (activity, vr, var retries) = XamlLoader.LoadAndValidate(path); result["compile_retries"] = retries; }
    catch (Exception ex)
    {
        result["state"] = "LoadError";
        result["fault"] = LoadError(ex);
        return result;
    }

    if (vr.Errors.Count > 0)
    {
        result["state"] = "Invalid";
        result["errors"] = Issues(vr.Errors);
        return result;
    }

    var inputs = new Dictionary<string, object?>();
    if (opts.TryGetValue("input-file", out var inputFile))
    {
        var declared = (activity as DynamicActivity)?.Properties.ToDictionary(p => p.Name) ?? new();
        using var doc = JsonDocument.Parse(File.ReadAllText(inputFile));
        foreach (var arg in doc.RootElement.EnumerateObject())
        {
            if (!declared.TryGetValue(arg.Name, out var prop) || !prop.Type.IsGenericType)
            {
                result["state"] = "InvalidInput";
                result["fault"] = new JsonObject { ["message"] = $"the workflow declares no argument named {arg.Name}" };
                return result;
            }
            try { inputs[arg.Name] = Values.FromJson(arg.Value, prop.Type.GetGenericArguments()[0]); }
            catch (Exception ex)
            {
                result["state"] = "InvalidInput";
                result["fault"] = new JsonObject { ["message"] = $"{arg.Name}: cannot convert to {prop.Type.GetGenericArguments()[0].Name}: {ex.Message}" };
                return result;
            }
        }
    }

    if (opts.TryGetValue("cwd", out var cwd)) Directory.SetCurrentDirectory(cwd);
    var timeout = TimeSpan.FromSeconds(opts.TryGetValue("timeout", out var t) ? double.Parse(t) : 30);

    var tracker = new Tracker();
    var console = new StringWriter();
    var runtime = new OfflineRuntime(activity, Path.GetDirectoryName(path)!, tracker, console);
    var app = new WorkflowApplication(activity, inputs);
    runtime.Attach(app);

    var done = new ManualResetEventSlim();
    string state = "Unknown";
    IDictionary<string, object>? outputs = null;
    Exception? fault = null;
    string? faultSource = null;
    app.OnUnhandledException = e =>
    {
        fault = e.UnhandledException;
        faultSource = e.ExceptionSource?.DisplayName;
        return UnhandledExceptionAction.Terminate;
    };
    app.Completed = e =>
    {
        state = e.CompletionState.ToString();
        outputs = e.Outputs;
        fault ??= e.TerminationException;
        done.Set();
    };
    app.Aborted = e => { state = "Aborted"; fault ??= e.Reason; done.Set(); };

    var sw = System.Diagnostics.Stopwatch.StartNew();
    app.Run();
    var timedOut = !done.Wait(timeout);
    // Abort raises Aborted on another thread, so the verdict comes from the flag, not from `state`.
    if (timedOut) app.Abort("timeout");
    result["state"] = timedOut ? "Timeout" : state;
    result["elapsed_ms"] = sw.ElapsedMilliseconds;
    // Workflow Foundation hands back default values for a run that did not complete; reporting
    // them would read as the workflow having produced them.
    var outs = new JsonObject();
    if (outputs is not null && state == "Closed") foreach (var kv in outputs) outs[kv.Key] = Values.ToJson(kv.Value);
    result["outputs"] = outs;
    if (fault is not null)
        result["fault"] = new JsonObject { ["type"] = fault.GetType().FullName, ["message"] = fault.Message, ["activity"] = faultSource };
    // Capped: a runaway loop records hundreds of thousands of entries a second.
    const int cap = 5000;
    lock (tracker.Records)
    {
        result["trace"] = new JsonArray(tracker.Records.Take(cap).Select(r => r.DeepClone()).ToArray());
        result["trace_truncated"] = tracker.Records.Count > cap;
    }
    lock (runtime.Logs)
    {
        result["logs"] = new JsonArray(runtime.Logs.Take(cap)
            .Select(l => (JsonNode)new JsonObject { ["level"] = l.Level, ["message"] = l.Message }).ToArray());
        result["logs_truncated"] = runtime.Logs.Count > cap;
    }
    result["console"] = console.ToString();
    return result;
}

sealed class Tracker : TrackingParticipant
{
    public List<JsonNode> Records { get; } = new();

    public Tracker()
    {
        TrackingProfile = new TrackingProfile
        {
            Queries = { new ActivityStateQuery { ActivityName = "*", States = { ActivityStates.Closed, ActivityStates.Faulted, ActivityStates.Canceled } } },
        };
    }

    protected override void Track(TrackingRecord record, TimeSpan timeout)
    {
        if (record is not ActivityStateRecord a) return;
        var type = a.Activity.TypeName.Split(',')[0];
        if (type.StartsWith("Microsoft.VisualBasic.Activities") || type.StartsWith("Microsoft.CSharp.Activities")
            || type.StartsWith("System.Activities.Expressions") || type == "System.Activities.DynamicActivity") return;
        lock (Records) Records.Add(new JsonObject { ["displayName"] = a.Activity.Name, ["type"] = type.Split('`')[0], ["state"] = a.State });
    }
}
