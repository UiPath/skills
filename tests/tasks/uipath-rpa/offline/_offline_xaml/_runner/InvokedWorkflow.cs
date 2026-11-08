using System.Activities;
using UiPath.Activities.Contracts;

namespace XamlRunner;

// Invoke Workflow File, run in-process the way a non-isolated invoke runs on the Robot: the
// invoked file shares the job's log, trace and console, its outputs come back as the
// activity's out arguments, and an exception it does not handle surfaces from the Invoke
// activity with its original type, so the caller can catch it.
public sealed class InvokedWorkflow : IWorkflowExecutor
{
    private readonly string _path;
    private readonly IDictionary<string, object> _inputs;
    private readonly Action<WorkflowApplication> _attach;
    private WorkflowApplication? _app;

    public InvokedWorkflow(string path, IDictionary<string, object> inputs, Action<WorkflowApplication> attach)
    {
        _path = path;
        _inputs = inputs;
        _attach = attach;
    }

    public IAsyncResult BeginExecute(AsyncCallback callback, object state)
    {
        var tcs = new TaskCompletionSource<IDictionary<string, object>>(state, TaskCreationOptions.RunContinuationsAsynchronously);
        tcs.Task.ContinueWith(t => callback?.Invoke(t), TaskScheduler.Default);
        try { Start(tcs); }
        catch (Exception ex) { tcs.TrySetException(ex); }
        return tcs.Task;
    }

    private void Start(TaskCompletionSource<IDictionary<string, object>> tcs)
    {
        if (!File.Exists(_path)) throw new FileNotFoundException($"Could not find the workflow file {_path}.", _path);
        var (activity, results, _) = XamlLoader.LoadAndValidate(_path);
        if (results.Errors.Count > 0)
            throw new InvalidWorkflowException($"{Path.GetFileName(_path)} is not valid: {string.Join("; ", results.Errors.Select(e => e.Message))}");

        Exception? fault = null;
        _app = new WorkflowApplication(activity, _inputs);
        _attach(_app);
        _app.OnUnhandledException = e => { fault = e.UnhandledException; return UnhandledExceptionAction.Terminate; };
        _app.Completed = e =>
        {
            if (e.CompletionState == ActivityInstanceState.Closed) tcs.TrySetResult(e.Outputs);
            else if (e.CompletionState == ActivityInstanceState.Canceled) tcs.TrySetCanceled();
            else tcs.TrySetException(fault ?? e.TerminationException ?? new InvalidOperationException($"{Path.GetFileName(_path)} faulted"));
        };
        _app.Aborted = e => tcs.TrySetException(e.Reason);
        _app.Run();
    }

    public IDictionary<string, object> EndExecute(IAsyncResult result) =>
        ((Task<IDictionary<string, object>>)result).GetAwaiter().GetResult();

    public void Cancel() => _app?.Cancel();
}
