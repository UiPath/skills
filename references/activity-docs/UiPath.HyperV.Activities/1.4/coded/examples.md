# Hyper-V Examples

Examples using the `hyperv` service from `UiPath.HyperV.Activities` package.

**Required package:** `"UiPath.HyperV.Activities": "[1.4.0]"`

> **Prerequisites:** All examples require access to a Hyper-V host. Use `HyperVClientProvider` to create a connection. Pass `null`/empty for host, username, and password to connect to the local machine with current Windows credentials.

---

## Connect to Local Hyper-V Host

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;

namespace MyProject
{
    public class LocalConnection : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Connect to local Hyper-V using current Windows credentials
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vms = await vmService.GetVMList(null, null, null, null, null, false);
            Log($"Found {vms.Length} virtual machines.");
        }
    }
}
```

## Connect to Remote Hyper-V Host

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;

namespace MyProject
{
    public class RemoteConnection : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "your-password") password.AppendChar(c);

            var clientProvider = new HyperVClientProvider(
                "hyperv-host01.company.com",
                "DOMAIN\\admin",
                password);

            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vms = await vmService.GetVMList(null, null, null, null, null, false);
            Log($"Found {vms.Length} VMs on remote host.");
        }
    }
}
```

## Create a Virtual Machine

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class CreateVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vm = await vmService.CreateVM(
                name: "TestServer01",
                vhdFile: @"C:\VMs\Disks\server.vhdx",
                description: "Test server for automation",
                location: @"C:\VMs\TestServer01",
                generation: VMGeneration.Generation2,
                powerOnAfterCreation: true,
                startupMemory: 4096,
                useDynamicMemory: true);

            Log($"Created VM: {vm.Name} (ID: {vm.Id}, State: {vm.State})");
        }
    }
}
```

## List and Filter Virtual Machines

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class ListVMs : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            // List all VMs
            var allVMs = await vmService.GetVMList(null, null, null, null, null, false);
            Log($"Total VMs: {allVMs.Length}");

            // Filter by name containing "Server"
            var serverVMs = await vmService.GetVMList(
                filterBy: FilterBy.Name,
                filterOperator: FilterOperator.Contains,
                filterValue: "Server",
                generation: null,
                state: null,
                includeGuestOSDetails: false);

            Log($"Server VMs: {serverVMs.Length}");

            // Filter by generation and state, include guest OS details
            var runningGen2 = await vmService.GetVMList(
                filterBy: null,
                filterOperator: null,
                filterValue: null,
                generation: VMGeneration.Generation2,
                state: VMState.Enabled,
                includeGuestOSDetails: true);

            foreach (var vm in runningGen2)
            {
                Log($"VM: {vm.Name} | OS: {vm.GuestOS} | FQDN: {vm.FullyQualifiedDomainName}");
                if (vm.Adapters != null)
                {
                    foreach (var adapter in vm.Adapters)
                    {
                        Log($"  NIC: {adapter.Name} | IPv4: {adapter.IPv4Address} | MAC: {adapter.MACAddress}");
                    }
                }
            }
        }
    }
}
```

## Get VM by ID

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;

namespace MyProject
{
    public class GetVMById : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vm = await vmService.GetVMByID("a1b2c3d4-e5f6-7890-abcd-ef1234567890", includeAdditionalDetails: true);

            Log($"VM: {vm.Name}");
            Log($"  State: {vm.State}");
            Log($"  Generation: {vm.Generation}");
            Log($"  RAM: {vm.RAM}");
            Log($"  Location: {vm.Location}");
        }
    }
}
```

## VM Power State Operations

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class VMPowerOps : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            // Get a specific VM
            var vms = await vmService.GetVMList(
                FilterBy.Name, FilterOperator.Equals, "TestServer01",
                null, null, false);
            var vm = vms[0];

            // Start the VM
            await vmService.StartVM(vm);
            Log($"Started {vm.Name}");

            // Pause the VM
            await vmService.PauseVM(vm);
            Log($"Paused {vm.Name}");

            // Resume the VM
            await vmService.ResumeVM(vm);
            Log($"Resumed {vm.Name}");

            // Graceful shutdown (requires integration services in guest OS)
            await vmService.ShutdownVM(vm);
            Log($"Shutdown initiated for {vm.Name}");

            // Force power off (immediate, no graceful shutdown)
            await vmService.TurnOffVM(vm);
            Log($"Turned off {vm.Name}");

            // Hard reset
            await vmService.ResetVM(vm);
            Log($"Reset {vm.Name}");
        }
    }
}
```

## Rename and Delete a VM

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class RenameDeleteVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vms = await vmService.GetVMList(
                FilterBy.Name, FilterOperator.Equals, "OldName",
                null, null, false);
            var vm = vms[0];

            // Rename
            await vmService.RenameVM(vm, "NewServerName");
            Log($"Renamed VM to NewServerName");

            // Delete (also remove VHD files)
            await vmService.DeleteVM(vm, deleteVhds: true);
            Log("VM and VHD files deleted.");
        }
    }
}
```

## Import and Export VMs

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class ImportExportVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            // Export a VM
            var vms = await vmService.GetVMList(
                FilterBy.Name, FilterOperator.Equals, "ProductionServer",
                null, null, false);
            var vm = vms[0];

            await vmService.ExportVM(vm, @"C:\Exports\ProductionServer");
            Log($"Exported {vm.Name}");

            // Import a VM (Copy mode — copies files to new location)
            var imported = await vmService.ImportVM(
                sourceVMFile: @"C:\Exports\ProductionServer\Virtual Machines\config.vmcx",
                snapshotFolder: null,
                importType: VMImportType.Copy,
                vhdFolder: @"C:\VMs\ImportedDisks",
                configurationFolder: @"C:\VMs\ImportedConfig",
                storageFolder: @"C:\VMs\ImportedStorage",
                vmName: "ImportedServer");

            Log($"Imported VM: {imported.Name} (ID: {imported.Id})");
        }
    }
}
```

## Manage VM Checkpoints (Snapshots)

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Services;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class ManageCheckpoints : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            // CheckPointService requires the concrete VirtualMachineService
            var concreteVmService = new VirtualMachineService(clientProvider);
            var checkpointService = hyperv.CheckPointService(clientProvider, concreteVmService);

            // Get a VM
            var vm = await vmService.GetVMByID("a1b2c3d4-e5f6-7890-abcd-ef1234567890");

            // Take a checkpoint
            var checkpoint = await checkpointService.TakeVMCheckpoint(
                vm,
                checkpointName: "Before Update",
                checkpointDescription: "Snapshot taken before applying OS updates");

            Log($"Checkpoint created: {checkpoint.Name} (ID: {checkpoint.Id}, Date: {checkpoint.CreationDate})");

            // List all checkpoints
            var checkpoints = await checkpointService.GetVMCheckpointList(vm);
            Log($"Total checkpoints: {checkpoints.Count}");

            foreach (var cp in checkpoints)
            {
                Log($"  {cp.Name} — {cp.CreationDate}");
            }

            // Revert to a checkpoint
            await checkpointService.RevertVMCheckpoint(vm, checkpoint);
            Log($"Reverted to checkpoint: {checkpoint.Name}");

            // Delete a single checkpoint (without children)
            await checkpointService.DeleteVMCheckpoint(vm, checkpoint, includeAllChildCheckpoints: false);
            Log("Checkpoint deleted.");

            // Delete all checkpoints for the VM
            await checkpointService.DeleteAllVMCheckpoints(vm);
            Log("All checkpoints deleted.");
        }
    }
}
```

## Configure UiPath Robot on VM

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class ConfigureRobotOnVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            var vms = await vmService.GetVMList(
                FilterBy.Name, FilterOperator.Equals, "RobotVM01",
                null, null, false);
            var vm = vms[0];

            var vmPassword = new SecureString();
            foreach (char c in "vm-login-password") vmPassword.AppendChar(c);

            // Option 1: Configure with Orchestrator URL + Machine Key
            await vmService.ConfigureRobot(
                virtualMachine: vm,
                orchestratorURL: "https://cloud.uipath.com/org/tenant/orchestrator_",
                machineKey: "your-machine-key",
                username: "Administrator",
                password: vmPassword);

            Log("Robot configured with Orchestrator URL and machine key.");

            // Option 2: Configure with connection string
            await vmService.ConfigureRobot(
                virtualMachine: vm,
                connectionString: "your-connection-string",
                username: "Administrator",
                password: vmPassword);

            Log("Robot configured with connection string.");
        }
    }
}
```

## End-to-End: Provision and Configure VM

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.HyperV.Core;
using UiPath.HyperV.Services;
using UiPath.HyperV.Activities.API;
using UiPath.HyperV.Models;

namespace MyProject
{
    public class ProvisionVM : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientProvider = new HyperVClientProvider(null, null, null);
            var vmService = hyperv.VirtualMachineService(clientProvider);

            // 1. Create VM
            var vm = await vmService.CreateVM(
                name: "AutoBot-" + DateTime.Now.ToString("yyyyMMdd-HHmmss"),
                vhdFile: @"C:\Templates\windows-server-template.vhdx",
                description: "Auto-provisioned robot VM",
                location: @"C:\VMs\AutoBots",
                generation: VMGeneration.Generation2,
                powerOnAfterCreation: true,
                startupMemory: 8192,
                useDynamicMemory: true);

            Log($"Created VM: {vm.Name} (ID: {vm.Id})");

            // 2. Take initial checkpoint
            var concreteVmService = new VirtualMachineService(clientProvider);
            var checkpointService = hyperv.CheckPointService(clientProvider, concreteVmService);

            var initialCheckpoint = await checkpointService.TakeVMCheckpoint(
                vm, "Initial State", "Clean VM before robot configuration");
            Log($"Initial checkpoint taken: {initialCheckpoint.Name}");

            // 3. Configure UiPath Robot
            var vmPassword = new SecureString();
            foreach (char c in "vm-password") vmPassword.AppendChar(c);

            await vmService.ConfigureRobot(
                virtualMachine: vm,
                orchestratorURL: "https://cloud.uipath.com/org/tenant/orchestrator_",
                machineKey: "machine-key-here",
                username: "Administrator",
                password: vmPassword);

            Log("Robot configured.");

            // 4. Take post-config checkpoint
            await checkpointService.TakeVMCheckpoint(
                vm, "Robot Configured", "VM with robot installed and connected");

            Log($"VM {vm.Name} provisioned and robot configured.");
        }
    }
}
```
