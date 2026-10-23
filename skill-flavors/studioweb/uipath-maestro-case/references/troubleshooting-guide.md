<!--skill-flavor:troubleshoot-intro:start-->
Diagnostic workflow for failed debug runs and deployed case process runs. The Studio Web host injects the session; never run `uip login`.
<!--skill-flavor:troubleshoot-intro:end-->

<!--skill-flavor:step-one-instance-id:start-->
A Studio Web debug (`uip maestro case debug`) prints no instance ID or folder key, only status, `Trace ID` when one was found, run logs and the execution trace. For a debug run, find the faulting element and its error in those, skip Steps 2, 3 and 5, and in Step 4 correlate against the local `caseplan.case` only: its `instance` reads need an instance ID. A `TimedOut after <N>s` status is a run still going, not a fault: do not troubleshoot or re-run it.

For a deployed process run, get the instance ID from the job:

```bash
uip maestro case job status <JOB_KEY> --output json
```

Parse the instance ID and folder key from the response.

> **No instance ID / `job status` fails →** halt. Report job key to user; downstream steps need the instance ID.
<!--skill-flavor:step-one-instance-id:end-->

<!--skill-flavor:escalation-report:start-->
5. **Escalate to user** if Steps 1–5 yield no root cause, or all paths blocked. Report: instance ID and folder key (the `Trace ID`, if one was printed, for a Studio Web debug), incident IDs/messages, faulting element ID, variable snapshot. Do not propose `caseplan.case` edits without confirmed cause.
<!--skill-flavor:escalation-report:end-->
