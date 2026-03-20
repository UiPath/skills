# Citrix Examples

Examples using the `citrix` service from `UiPath.Citrix.Activities` package.

**Required package:** `"UiPath.Citrix.Activities": "[1.5.0]"`

> **Prerequisites:** All examples require access to a Citrix XenServer / Citrix Hypervisor host. Provide the server address, port, username, and password to create a `CitrixService`.

---

## Connect to XenServer and List VMs

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class ListAllVMs : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                serverAddress: "xenserver.company.com",
                port: 443,
                userName: "root",
                password: password);

            // List all VMs (no filters)
            var vms = await citrixService.GetVMListAsync(
                filterBy: FilterByEnum.All,
                filterValue: "",
                includeSubfolders: false,
                powerStateFilter: PowerStateFilter.All,
                includeGuestOSDetails: false);

            Log($"Found {vms.Length} virtual machines.");

            foreach (var vm in vms)
            {
                Log($"VM: {vm.Name} | UUID: {vm.UUID} | State: {vm.PowerState}");
            }
        }
    }
}
```

## Filter VMs by Name and Power State

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class FilterVMs : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            // Filter by name, only running VMs, include guest OS details
            var runningVMs = await citrixService.GetVMListAsync(
                filterBy: FilterByEnum.Name,
                filterValue: "prod-",
                includeSubfolders: false,
                powerStateFilter: PowerStateFilter.Running,
                includeGuestOSDetails: true);

            foreach (var vm in runningVMs)
            {
                Log($"VM: {vm.Name} | OS: {vm.GuestOS} | Server: {vm.HomeServer}");
                if (vm.IPv4Addresses != null)
                {
                    foreach (var ip in vm.IPv4Addresses)
                    {
                        Log($"  IPv4: {ip}");
                    }
                }
            }

            // Filter by folder
            var folderVMs = await citrixService.GetVMListAsync(
                filterBy: FilterByEnum.Folder,
                filterValue: "/Production",
                includeSubfolders: true,
                powerStateFilter: PowerStateFilter.All,
                includeGuestOSDetails: false);

            Log($"Found {folderVMs.Length} VMs in /Production folder.");

            // Filter by tag
            var taggedVMs = await citrixService.GetVMListAsync(
                filterBy: FilterByEnum.Tag,
                filterValue: "automation",
                includeSubfolders: false,
                powerStateFilter: PowerStateFilter.All,
                includeGuestOSDetails: false);

            Log($"Found {taggedVMs.Length} VMs tagged 'automation'.");
        }
    }
}
```

## Get VM by UUID

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class GetVMByUUID : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            var vm = await citrixService.GetVMByUUIDAsync("a1b2c3d4-e5f6-7890-abcd-ef1234567890");

            Log($"VM: {vm.Name}");
            Log($"  UUID: {vm.UUID}");
            Log($"  State: {vm.PowerState}");
            Log($"  Server: {vm.HomeServer}");
            Log($"  Folder: {vm.Folder}");
            Log($"  Guest OS: {vm.GuestOS}");
            Log($"  Is Template: {vm.IsTemplate}");

            if (vm.Tags != null && vm.Tags.Length > 0)
            {
                Log($"  Tags: {string.Join(", ", vm.Tags)}");
            }
        }
    }
}
```

## Create VM from Template

```csharp
using System;
using System.Linq;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class CreateFromTemplate : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            // Get available templates
            var templates = await citrixService.GetTemplateListAsync(
                filterBy: FilterByEnum.Name,
                filterValue: "Windows Server 2022",
                includeSubfolders: true);

            Log($"Found {templates.Length} matching templates.");

            // Get server list to pick a host
            var servers = await citrixService.GetServerListAsync();
            var targetServer = servers.First(s => s.PowerState == ServerPowerState.Running);
            Log($"Target server: {targetServer.Name} (UUID: {targetServer.UUID})");

            // Get storage repositories on the target server
            var storageRepos = await citrixService.GetHostStorageRepositoriesAsync(targetServer);
            var targetStorage = storageRepos.First(sr => sr.FreeSpace > 0);
            Log($"Target storage: {targetStorage.Name} ({targetStorage.PercentFree}% free)");

            // Create VM from template
            var newVM = await citrixService.CreateVMFromTemplateAsync(
                customTemplate: templates[0],
                homeServerUUID: targetServer.UUID,
                storageRepositoryUUID: targetStorage.UUID,
                virtualMachineName: "AutoBot-" + DateTime.Now.ToString("yyyyMMdd"),
                virtualMachineDescription: "Auto-provisioned robot VM",
                powerOnAfterCreation: true);

            Log($"Created VM: {newVM.Name} (UUID: {newVM.UUID})");
        }
    }
}
```

## VM Power Operations

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class VMPowerOps : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            var vm = await citrixService.GetVMByUUIDAsync("vm-uuid-here");

            // Power on
            await citrixService.PowerOnVMAsync(vm, waitForCompletion: true);
            Log($"Powered on: {vm.Name}");

            // Graceful shutdown
            await citrixService.PowerOffVMAsync(vm,
                forcedShutDown: false,
                waitForCompletion: true);
            Log($"Gracefully shut down: {vm.Name}");

            // Force power off
            await citrixService.PowerOffVMAsync(vm,
                forcedShutDown: true,
                waitForCompletion: true);
            Log($"Forced power off: {vm.Name}");

            // Restart (graceful)
            await citrixService.RestartVMAsync(vm,
                forcedReboot: false,
                waitForCompletion: true);
            Log($"Restarted: {vm.Name}");

            // Suspend
            await citrixService.SuspendVMAsync(vm, waitForCompletion: true);
            Log($"Suspended: {vm.Name}");

            // Resume
            await citrixService.ResumeVMAsync(vm, waitForCompletion: true);
            Log($"Resumed: {vm.Name}");
        }
    }
}
```

## Manage VM Tags and Folders

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class ManageTagsAndFolders : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            var vm = await citrixService.GetVMByUUIDAsync("vm-uuid-here");

            // Add tags
            vm = await citrixService.AddTagToVMAsync(vm, "automation");
            vm = await citrixService.AddTagToVMAsync(vm, "production");
            Log($"Tags added. Current tags: {string.Join(", ", vm.Tags)}");

            // Remove a tag
            vm = await citrixService.RemoveTagFromVMAsync(vm, "production");
            Log($"Tag removed. Current tags: {string.Join(", ", vm.Tags)}");

            // Set folder
            vm = await citrixService.SetFolderForVMAsync(vm, "/Production/Robots");
            Log($"Folder set to: {vm.Folder}");

            // Remove from folder
            vm = await citrixService.RemoveVMFromFolderAsync(vm, "/Production/Robots");
            Log($"Removed from folder. Current folder: {vm.Folder}");
        }
    }
}
```

## Rename and Delete VM

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class RenameDeleteVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            var vm = await citrixService.GetVMByUUIDAsync("vm-uuid-here");

            // Rename
            vm = await citrixService.RenameVMAsync(vm, "Decommissioned-" + vm.Name);
            Log($"Renamed to: {vm.Name}");

            // Power off before delete
            if (vm.PowerState == VirtualMachinePowerState.Running)
            {
                await citrixService.PowerOffVMAsync(vm, forcedShutDown: true, waitForCompletion: true);
            }

            // Delete (including disks and snapshots)
            await citrixService.DeleteVMAsync(vm,
                deleteDisks: true,
                deleteSnapshots: true,
                waitForCompletion: true);
            Log("VM deleted.");
        }
    }
}
```

## Manage VM Snapshots

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class ManageSnapshots : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            var vm = await citrixService.GetVMByUUIDAsync("vm-uuid-here");

            // Take a snapshot
            var snapshot = await citrixService.TakeVMSnapshotAsync(
                virtualMachine: vm,
                snapshotName: "Before Update",
                snapshotDescription: "Snapshot before applying patches",
                snapshotVmMemory: false,
                quiesce: true,
                waitForCompletion: true);

            Log($"Snapshot created: {snapshot.Name} (UUID: {snapshot.UUID}, Date: {snapshot.CreationDate})");

            // List all snapshots
            var snapshots = await citrixService.GetVMSnapshotsListAsync(vm);
            Log($"Total snapshots: {snapshots.Length}");

            foreach (var snap in snapshots)
            {
                Log($"  {snap.Name} — {snap.CreationDate} — {snap.Description}");
            }

            // Revert to a snapshot
            await citrixService.RevertVMToSnapshotAsync(vm, snapshot, waitForCompletion: true);
            Log($"Reverted to snapshot: {snapshot.Name}");

            // Delete a specific snapshot
            await citrixService.DeleteVMSnapshotAsync(vm, snapshot, waitForCompletion: true);
            Log("Snapshot deleted.");

            // Delete all snapshots
            await citrixService.DeleteAllVMSnapshotAsync(vm, waitForCompletion: true);
            Log("All snapshots deleted.");
        }
    }
}
```

## List Servers and Storage

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class ListServersAndStorage : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            // List all servers in the pool
            var servers = await citrixService.GetServerListAsync();
            Log($"Found {servers.Length} servers.");

            foreach (var server in servers)
            {
                Log($"Server: {server.Name} (UUID: {server.UUID})");
                Log($"  State: {server.PowerState}");
                Log($"  Master: {server.IsMaster}");
                Log($"  Maintenance Mode: {server.InMaintenanceMode}");

                // Get storage repositories for each server
                var storageRepos = await citrixService.GetHostStorageRepositoriesAsync(server);
                Log($"  Storage Repositories: {storageRepos.Length}");

                foreach (var sr in storageRepos)
                {
                    Log($"    {sr.Name} | Shared: {sr.Shared} | Free: {sr.PercentFree}% | Total: {sr.TotalCapacity} | Free: {sr.FreeSpace}");
                }
            }
        }
    }
}
```

## End-to-End: Provision Robot VM

```csharp
using System;
using System.Linq;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.Citrix.Activities.API;
using UiPath.Citrix.Contracts;

namespace MyProject
{
    public class ProvisionRobotVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var citrixService = citrix.CitrixService(
                "xenserver.company.com", 443, "root", password);

            // 1. Find the template
            var templates = await citrixService.GetTemplateListAsync(
                FilterByEnum.Name, "Robot-Template", true);

            if (templates.Length == 0)
            {
                Log("ERROR: No matching template found.");
                return;
            }

            // 2. Find a running server with available storage
            var servers = await citrixService.GetServerListAsync();
            var runningServers = servers.Where(s =>
                s.PowerState == ServerPowerState.Running &&
                !s.InMaintenanceMode).ToArray();

            var targetServer = runningServers[0];
            var storageRepos = await citrixService.GetHostStorageRepositoriesAsync(targetServer);
            var targetStorage = storageRepos
                .Where(sr => sr.Shared && sr.PercentFree > 20)
                .OrderByDescending(sr => sr.FreeSpace)
                .First();

            Log($"Using server: {targetServer.Name}, storage: {targetStorage.Name} ({targetStorage.PercentFree}% free)");

            // 3. Create VM from template
            string vmName = "Robot-" + DateTime.Now.ToString("yyyyMMdd-HHmmss");
            var newVM = await citrixService.CreateVMFromTemplateAsync(
                customTemplate: templates[0],
                homeServerUUID: targetServer.UUID,
                storageRepositoryUUID: targetStorage.UUID,
                virtualMachineName: vmName,
                virtualMachineDescription: "Auto-provisioned UiPath robot",
                powerOnAfterCreation: true);

            Log($"Created VM: {newVM.Name} (UUID: {newVM.UUID})");

            // 4. Tag and organize
            newVM = await citrixService.AddTagToVMAsync(newVM, "automation");
            newVM = await citrixService.AddTagToVMAsync(newVM, "robot");
            newVM = await citrixService.SetFolderForVMAsync(newVM, "/Production/Robots");
            Log($"VM organized: tags={string.Join(",", newVM.Tags)}, folder={newVM.Folder}");

            // 5. Take initial snapshot
            var snapshot = await citrixService.TakeVMSnapshotAsync(
                newVM, "Initial State", "Clean VM before configuration",
                snapshotVmMemory: false, quiesce: false, waitForCompletion: true);

            Log($"Initial snapshot: {snapshot.Name} (UUID: {snapshot.UUID})");
            Log($"Provisioning complete for {newVM.Name}.");
        }
    }
}
```
