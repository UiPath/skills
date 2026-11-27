# System Center Examples

Examples using the `systemCenter` service from `UiPath.SystemCenter.Activities` package.

**Required package:** `"UiPath.SystemCenter.Activities": "[1.0.0]"`

---

## List Runbook Servers

```csharp
namespace MyProject
{
    public class ListServersWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // Get all available runbook servers
            RunbookServer[] servers = await runbookService.GetRunbookServers();

            foreach (var server in servers)
            {
                Log($"Server: {server.Name}, ID: {server.Id}");
            }
        }
    }
}
```

## Get a Runbook by ID or Path

```csharp
namespace MyProject
{
    public class GetRunbookWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // Get by ID
            Runbook runbookById = await runbookService.GetRunbookById("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
            Log($"Runbook: {runbookById.Name}");

            // Get by path
            Runbook runbookByPath = await runbookService.GetRunbookByPath(@"\IT Operations\Restart Service");
            Log($"Runbook: {runbookByPath.Name}, ID: {runbookByPath.Id}");
        }
    }
}
```

## Start a Runbook with Parameters

```csharp
using System.Data;

namespace MyProject
{
    public class StartRunbookWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // Get the runbook and a server to run it on
            Runbook runbook = await runbookService.GetRunbookByPath(@"\IT Operations\Restart Service");
            RunbookServer[] servers = await runbookService.GetRunbookServers();
            string serverId = servers[0].Id;

            // Build input parameters
            var parameters = new DataTable();
            parameters.Columns.Add("Name", typeof(string));
            parameters.Columns.Add("Value", typeof(string));
            parameters.Rows.Add("ServiceName", "MyAppService");
            parameters.Rows.Add("ServerName", "PROD-SERVER-01");

            // Start the runbook
            RunbookJob job = await runbookService.StartRunbook(
                runbook.Id, serverId, parameters);
            Log($"Runbook started, Job ID: {job.Id}");
        }
    }
}
```

## Monitor Runbook Job and Instances

```csharp
using System.Data;

namespace MyProject
{
    public class MonitorRunbookWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // Start a runbook
            Runbook runbook = await runbookService.GetRunbookByPath(@"\IT Operations\Health Check");
            RunbookServer[] servers = await runbookService.GetRunbookServers();

            var parameters = new DataTable();
            parameters.Columns.Add("Name", typeof(string));
            parameters.Columns.Add("Value", typeof(string));
            parameters.Rows.Add("Environment", "Production");

            RunbookJob job = await runbookService.StartRunbook(
                runbook.Id, servers[0].Id, parameters);
            Log($"Job started: {job.Id}");

            // Get the job status
            RunbookJob jobStatus = await runbookService.GetJob(job.Id);
            Log($"Job status: {jobStatus.Status}");

            // Get runbook instances for this job
            RunbookInstance[] instances = await runbookService.GetRunbookInstances(
                runbook.Id, job.Id);

            foreach (var instance in instances)
            {
                Log($"Instance: {instance.Id}, Status: {instance.Status}");
            }
        }
    }
}
```

## Stop a Running Runbook and Job

```csharp
namespace MyProject
{
    public class StopRunbookWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // Stop a runbook by its ID
            await runbookService.StopRunbook("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
            Log("Runbook stopped");

            // Stop a specific job
            await runbookService.StopJob("f1e2d3c4-b5a6-7890-1234-567890abcdef");
            Log("Job stopped");
        }
    }
}
```

## End-to-End: Find, Start, Monitor, and Stop a Runbook

```csharp
using System.Data;

namespace MyProject
{
    public class FullRunbookLifecycleWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(ISystemCenterClientProvider clientProvider)
        {
            var runbookService = systemCenter.RunbookService(clientProvider);

            // 1. Find the runbook and pick a server
            Runbook runbook = await runbookService.GetRunbookByPath(@"\Deployments\Deploy App");
            RunbookServer[] servers = await runbookService.GetRunbookServers();
            Log($"Using server: {servers[0].Name}");

            // 2. Start with parameters
            var parameters = new DataTable();
            parameters.Columns.Add("Name", typeof(string));
            parameters.Columns.Add("Value", typeof(string));
            parameters.Rows.Add("AppVersion", "2.5.1");
            parameters.Rows.Add("TargetEnvironment", "Staging");

            RunbookJob job = await runbookService.StartRunbook(
                runbook.Id, servers[0].Id, parameters);
            Log($"Deployment started, Job: {job.Id}");

            // 3. Check job status
            RunbookJob status = await runbookService.GetJob(job.Id);
            Log($"Job status: {status.Status}");

            // 4. Get instances
            RunbookInstance[] instances = await runbookService.GetRunbookInstances(
                runbook.Id, job.Id);
            Log($"Running instances: {instances.Length}");

            // 5. Stop the job if needed
            await runbookService.StopJob(job.Id);
            Log("Job stopped");
        }
    }
}
```
