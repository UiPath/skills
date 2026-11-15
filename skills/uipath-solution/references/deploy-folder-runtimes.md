# Folder Runtime Check

What `uip solution deploy run` and `deploy upgrade` report when the deployment's folder has no runtime for a process's unattended jobs, and how to fix the folder. Newer CLI builds only.

> For full option details, use `--help` (e.g., `uip or folders runtimes --help`).

## What is checked

On newer CLI builds, once the package is installed, `deploy run` (and `deploy upgrade`) checks that the deployment's folder has a runtime its processes' **unattended** jobs can start on. The check counts machines the folder inherits from its parents. Only the processes whose unattended jobs need a machine in the folder are checked:

| Process type | Starts unattended on (any one, with slots in the folder) |
|---|---|
| RPA process | Serverless, Unattended, NonProduction, TestAutomation, AutomationCloud, AutomationCloudTestAutomation, AppTest, PerformanceTest (plus Development in a Personal Workspace) |
| Test case | Serverless, ServerlessTestAutomation, TestAutomation, AutomationCloud, AutomationCloudTestAutomation, AppTest, Unattended |
| MCP server | Serverless |

Apps, agents, flows, API workflows, functions, cases, business rules and BPMN processes are not checked: Orchestrator gives their jobs a machine without one in the folder. One exception the check cannot see: a **coded** agent needs a serverless machine in the folder, so give its folder one yourself. A coded agent packaged as an RPA `Process` is checked as one, and the serverless half of the fix is the one that applies. Neither is a process the deployment links to an existing one (`deploy config link`): its jobs run in the linked process's folder. Attended runs are licensed per user, not per folder, so the check says nothing about running the process attended from Assistant.

Each process the folder cannot run unattended is one line in `Data.Warnings`. Read the warnings there: that is the source of truth. The same line is also logged as a warning on stderr at the default log level, but `--log-level error` hides it and `--log-file` sends it to the file instead:

```text
Folder 'Shared/MySolutionFolder' has no runtime for unattended jobs of the Process process 'InvoiceBot' (none of ... has slots there): its triggers and the jobs Orchestrator starts will not run until one is assigned. Running it attended from Assistant is not affected. ... Check with: uip or folders runtimes --folder-path 'Shared/MySolutionFolder'
```

The run is still `Result: Success` with its usual exit code. The deployment exists, so do **not** deploy again; fix the folder instead:

```bash
uip or machines list --output json                                   # pick a machine with slots of a type from the table row for the warned process
uip or machines assign "<MACHINE_KEY>" --folder-path "<FOLDER_PATH>" --output json
uip or folders runtimes --folder-path "<FOLDER_PATH>" --output json   # a row of a type from that table row now has Total > 0
```

`<FOLDER_PATH>` is the `Data.FolderPath` the deploy returned. Pick the machine by the table row for the process type the warning names: Unattended or serverless slots for an RPA process, test slots (TestAutomation, ServerlessTestAutomation, AppTest) or Unattended for a test case, the serverless machine for an MCP server. A **Windows** (non-portable) RPA process cannot run on serverless, yet the check counts a serverless machine as enough. For one, assign a machine with Unattended slots even when the folder already has the serverless machine. A brand-new top-level folder often already has the tenant's serverless machine, and some tenants also assign it to the solution folder the install creates, so a deploy there may correctly report nothing for a portable process.

When the check itself cannot run, the single `Data.Warnings` line starts `Could not check that folder ...` and gives the reason. That happens when the login cannot read the folder's runtimes (an external app without the `OR.Machines` scope, say), a lookup fails, or the check does not finish within 10 seconds. Run `uip or folders runtimes` yourself before you rely on the folder. When a user session's read of the deployment's links fails, the warning ends by saying the process may be linked. Then check the linked folder instead. `Data.Warnings` is absent when there is nothing to report.
