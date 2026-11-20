using System.Activities;
using System.Activities.Tracking;
using UiPath.Activities.Contracts;
using UiPath.Activities.Contracts.Telemetry;

namespace XamlRunner;

// Stands in for the Robot's executor. UiPath activities reach the host through this
// extension (LogMessage calls GetWorkflowRuntime().Log), and without one they fault on a
// null reference. Invoke Workflow File runs in-process; everything that needs a Robot, an
// Orchestrator or a second process refuses loudly instead of pretending to work.
public sealed class OfflineRuntime : IWorkflowRuntime
{
    private readonly Activity _root;
    private readonly string _projectDir;
    private readonly TrackingParticipant _tracker;
    private readonly TextWriter _console;

    public OfflineRuntime(Activity root, string projectDir, TrackingParticipant tracker, TextWriter console)
    {
        _root = root;
        _projectDir = projectDir;
        _tracker = tracker;
        _console = console;
    }

    public void Attach(WorkflowApplication app)
    {
        app.Extensions.Add(_tracker);
        app.Extensions.Add(this);
        app.Extensions.Add<TextWriter>(() => _console);
    }

    public List<LogEntry> Logs { get; } = new();

    public Version Version => new(26, 0);
    public IRobotSettings RobotSettings => null!;
    public IStudioSettings StudioSettings => null!;
    public IOrchestratorSettings OrchestratorSettings => null!;
    public ITelemetryProxy TelemetryProxy => null!;

    public Activity GetRootActivity(Guid workflowInstanceId) => _root;

    public void Log(LogMessage logMessage, Guid workflowInstanceId)
    {
        lock (Logs) Logs.Add(new LogEntry(LevelName(logMessage.EventType), logMessage.Message ?? ""));
    }

    // Log Message casts UiPath's LogLevel onto TraceEventType; report the names Studio shows.
    private static string LevelName(System.Diagnostics.TraceEventType level) => level switch
    {
        System.Diagnostics.TraceEventType.Critical => "Fatal",
        System.Diagnostics.TraceEventType.Error => "Error",
        System.Diagnostics.TraceEventType.Warning => "Warn",
        System.Diagnostics.TraceEventType.Information => "Info",
        System.Diagnostics.TraceEventType.Verbose => "Trace",
        _ => level.ToString(),
    };

    public void ReportStatus(StatusParameters statusParameters, Guid workflowInstanceId) { }

    public bool HasFeature(string featureName) => false;

    // Studio writes WorkflowFileName relative to the project folder, with Windows separators.
    public IWorkflowExecutor CreateWorkflowExecutor(WorkflowParameters workflowParameters)
    {
        if (workflowParameters.InArguments is null)
            throw new NotSupportedException("Invoke Workflow File with serialized arguments is not available offline.");
        var relative = workflowParameters.FileName.Replace('\\', '/');
        var path = Path.GetFullPath(Path.Combine(_projectDir, relative));
        return new InvokedWorkflow(path, workflowParameters.InArguments, Attach);
    }

    public IWorkflowExecutor CreateWorkflowExecutor(ProcessParameters processParameters) =>
        throw new NotSupportedException("Invoke Process needs an Orchestrator and is not available offline.");

    public Guid BeginProcess(BeginProcessParameters beginProcessParameters) =>
        throw new NotSupportedException("Starting a process needs a Robot and is not available offline.");

    public Task<bool> AcquireForeground(AcquireForegroundParameters acquireForegroundParameters) => Task.FromResult(true);

    public Task ReleaseForeground() => Task.CompletedTask;

    public Task<int> StartProcessInSession(InvokeTargetSession invokeTargetSession, string path, string arguments, CancellationToken ct = default) =>
        throw new NotSupportedException("Starting a process in a session is not available offline.");
}

public sealed record LogEntry(string Level, string Message);
