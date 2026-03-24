# Amazon WorkSpaces Examples

Examples using the `awrks` service from `UiPath.AmazonWorkSpaces.Activities` package.

**Required package:** `"UiPath.AmazonWorkSpaces.Activities": "[1.4.1]"`

---

## Get WorkSpace Info and Stop It

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;

namespace MyProject
{
    public class StopWorkSpaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, string workSpaceId)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            // Get workspace info
            AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(workSpaceId);
            Log($"WorkSpace {workspace.WorkSpaceId} is in state: {workspace.State}");
            Log($"User: {workspace.UserName}, IP: {workspace.IpAddress}");

            // Stop the workspace and wait for completion
            await workSpacesService.StopWorkSpace(workspace, isWaitForCompletion: true);
            Log("WorkSpace stopped successfully.");
        }
    }
}
```

## Create a New WorkSpace

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;
using UiPath.Core;

namespace MyProject
{
    public class CreateWorkSpaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            var createParam = new AWRKSCreateWorkspaceParam
            {
                BundleId = "wsb-abc123def",
                DirectoryId = "d-abc123def",
                UserName = "john.doe",
                ComputeType = "STANDARD",
                RunningMode = AWRKSRunningMode.AutoStop,
                RunningModeAutoStopTimeout = 60,
                RootVolumeEncryptionEnabled = false,
                UserVolumeEncryptionEnabled = false
            };

            AWRKSWorkspace newWorkSpace = await workSpacesService.CreateWorkSpace(createParam, isWaitForCompletion: true);
            Log($"Created WorkSpace: {newWorkSpace.WorkSpaceId}, State: {newWorkSpace.State}");
        }
    }
}
```

## Reboot and Rebuild a WorkSpace

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;

namespace MyProject
{
    public class RebootRebuildWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, string workSpaceId)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(workSpaceId);

            // Reboot the workspace
            Log($"Rebooting WorkSpace {workspace.WorkSpaceId}...");
            await workSpacesService.RebootWorkSpace(workspace, isWaitForCompletion: true);
            Log("Reboot complete.");

            // Rebuild the workspace (restores C: drive to original image, preserves D: drive)
            Log($"Rebuilding WorkSpace {workspace.WorkSpaceId}...");
            await workSpacesService.RebuildWorkSpace(workspace, isWaitForCompletion: true);
            Log("Rebuild complete.");
        }
    }
}
```

## Migrate a WorkSpace to a Different Bundle

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;

namespace MyProject
{
    public class MigrateWorkSpaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, string workSpaceId, string targetBundleId)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(workSpaceId);
            Log($"Current bundle: {workspace.BundleId}");

            AWRKSWorkspace migratedWorkspace = await workSpacesService.MigrateWorkSpace(
                workspace, targetBundleId, isWaitForCompletion: true);

            Log($"Migrated to bundle: {migratedWorkspace.BundleId}");
        }
    }
}
```

## Update WorkSpace Properties

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;
using UiPath.Core;

namespace MyProject
{
    public class UpdateWorkSpaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, string workSpaceId)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(workSpaceId);

            // Change running mode to AlwaysOn
            var updateRunningMode = new AWRKSUpdateWorkspaceParam
            {
                Workspace = workspace,
                UpdateAction = AWRKSUpdateAction.ModifyRunningMode,
                RunningMode = "ALWAYS_ON"
            };
            await workSpacesService.UpdateWorkSpace(updateRunningMode, isWaitForCompletion: true);
            Log("Running mode updated to AlwaysOn.");

            // Change compute type
            var updateCompute = new AWRKSUpdateWorkspaceParam
            {
                Workspace = workspace,
                UpdateAction = AWRKSUpdateAction.ModifyComputeType,
                ComputeType = "PERFORMANCE"
            };
            await workSpacesService.UpdateWorkSpace(updateCompute, isWaitForCompletion: true);
            Log("Compute type updated to Performance.");

            // Resize user volume
            var resizeVolume = new AWRKSUpdateWorkspaceParam
            {
                Workspace = workspace,
                UpdateAction = AWRKSUpdateAction.ModifyVolumeSize,
                VolumeToResize = "UserVolume",
                VolumeNewSize = 100
            };
            await workSpacesService.UpdateWorkSpace(resizeVolume, isWaitForCompletion: true);
            Log("User volume resized to 100 GB.");
        }
    }
}
```

## Remove and Restore a WorkSpace

```csharp
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;

namespace MyProject
{
    public class RemoveRestoreWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, string workSpaceId)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(workSpaceId);

            // Restore workspace to last known healthy state
            Log("Restoring WorkSpace...");
            await workSpacesService.RestoreWorkSpace(workspace, isWaitForCompletion: true);
            Log("WorkSpace restored.");

            // Remove (terminate) workspace permanently
            Log("Removing WorkSpace...");
            await workSpacesService.RemoveWorkSpace(workspace, isWaitForCompletion: true);
            Log("WorkSpace terminated.");
        }
    }
}
```

## Start Multiple WorkSpaces

```csharp
using System.Collections.Generic;
using UiPath.AmazonWorkSpaces.Activities.API;
using UiPath.AmazonWorkSpaces.Models;

namespace MyProject
{
    public class StartMultipleWorkSpacesWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWRKSClientProvider clientProvider, List<string> workSpaceIds)
        {
            IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

            foreach (string id in workSpaceIds)
            {
                AWRKSWorkspace workspace = await workSpacesService.GetWorkSpaceInfo(id);

                if (workspace.State == AWRKSState.STOPPED)
                {
                    Log($"Starting WorkSpace {id}...");
                    await workSpacesService.StartWorkSpace(workspace, isWaitForCompletion: false);
                }
                else
                {
                    Log($"WorkSpace {id} is in state {workspace.State}, skipping.");
                }
            }

            Log("All start requests sent.");
        }
    }
}
```
