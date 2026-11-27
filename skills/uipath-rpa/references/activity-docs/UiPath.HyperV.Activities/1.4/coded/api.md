# Hyper-V API Reference

Complete API reference for the `hyperv` service from `UiPath.HyperV.Activities` package.

**Required package:** `"UiPath.HyperV.Activities": "[1.4.0]"`

**Auto-imported namespaces:** `UiPath.HyperV.Core`, `UiPath.Core`, `UiPath.HyperV.Models`

---

## HyperVClientProvider

Creates WMI connections to Hyper-V hosts. Import from `UiPath.HyperV.Core`.

```csharp
public class HyperVClientProvider : IHyperVClientProvider
{
    public HyperVClientProvider(string host, string userName, SecureString secretKey);
    public ManagementScope GetManagementScope();
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `host` | `string` | Hyper-V host name or IP. Pass `null` or empty for local machine. |
| `userName` | `string` | Username for remote connection. Pass `null` for current Windows credentials. |
| `secretKey` | `SecureString` | Password for remote connection. Pass `null` for current Windows credentials. |

> **Note:** The provider connects to `\\{host}\root\virtualization\v2` via WMI. Throws `HyperVException` if the host is unreachable.

---

## IHyperVService

Root service accessor. Access via `hyperv` in coded workflows.

```csharp
public interface IHyperVService
{
    IVirtualMachineService VirtualMachineService(IHyperVClientProvider hyperVClientProvider);
    ICheckPointService CheckPointService(IHyperVClientProvider hyperVClientProvider, VirtualMachineService virtualMachineService);
}
```

> **Note:** `CheckPointService` requires a concrete `VirtualMachineService` (from `UiPath.HyperV.Services`), not the `IVirtualMachineService` interface.

---

## IVirtualMachineService

Access: `hyperv.VirtualMachineService(clientProvider)`

### Create VM

```csharp
Task<VirtualMachine> CreateVM(
    string name,
    string vhdFile,
    string description,
    string location,
    VMGeneration generation,
    bool powerOnAfterCreation,
    int? startupMemory,
    bool useDynamicMemory)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the virtual machine |
| `vhdFile` | `string` | Yes | Path to the VHD/VHDX file to attach |
| `description` | `string` | No | Description of the VM |
| `location` | `string` | No | Path where the VM files will be stored |
| `generation` | `VMGeneration` | Yes | VM generation (`Generation1` or `Generation2`) |
| `powerOnAfterCreation` | `bool` | Yes | Whether to start the VM after creation |
| `startupMemory` | `int?` | No | Startup memory in MB (nullable) |
| `useDynamicMemory` | `bool` | Yes | Whether to use dynamic memory allocation |

**Returns:** `VirtualMachine` — the created VM

### Get VM List

```csharp
Task<VirtualMachine[]> GetVMList(
    FilterBy? filterBy,
    FilterOperator? filterOperator,
    string filterValue,
    VMGeneration? generation,
    VMState? state,
    bool includeGuestOSDetails)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filterBy` | `FilterBy?` | No | Filter field: `Name` or `Location` |
| `filterOperator` | `FilterOperator?` | No | Filter operator: `Equals`, `Contains`, `StartsWith`, `EndsWith` |
| `filterValue` | `string` | No | Filter value to match |
| `generation` | `VMGeneration?` | No | Filter by VM generation |
| `state` | `VMState?` | No | Filter by VM state |
| `includeGuestOSDetails` | `bool` | Yes | Include guest OS name and FQDN (slower) |

**Returns:** `VirtualMachine[]` — array of matching VMs

> **Note:** Pass `null` for all filter parameters to get all VMs.

### Get VM by ID

```csharp
Task<VirtualMachine> GetVMByID(string vmId, bool includeAdditionalDetails = true)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vmId` | `string` | VM identifier (GUID) |
| `includeAdditionalDetails` | `bool` | Include extra details like network adapters (default: `true`) |

**Returns:** `VirtualMachine`

### Import VM

```csharp
Task<VirtualMachine> ImportVM(
    string sourceVMFile,
    string snapshotFolder,
    VMImportType importType,
    string vhdFolder,
    string configurationFolder,
    string storageFolder,
    string vmName)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sourceVMFile` | `string` | Yes | Path to the VM definition file (.vmcx or .xml) |
| `snapshotFolder` | `string` | No | Path to snapshot/checkpoint folder |
| `importType` | `VMImportType` | Yes | `Restore` (in-place) or `Copy` (copy files to new location) |
| `vhdFolder` | `string` | No | Destination folder for VHD files (used with `Copy`) |
| `configurationFolder` | `string` | No | Destination folder for configuration files |
| `storageFolder` | `string` | No | Destination folder for storage files |
| `vmName` | `string` | No | New name for the imported VM |

**Returns:** `VirtualMachine` — the imported VM

### Export VM

```csharp
Task ExportVM(VirtualMachine vm, string folder)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vm` | `VirtualMachine` | The VM to export |
| `folder` | `string` | Destination folder path |

### Delete VM

```csharp
Task DeleteVM(VirtualMachine vm, bool deleteVhds)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vm` | `VirtualMachine` | The VM to delete |
| `deleteVhds` | `bool` | Also delete associated VHD files |

### Rename VM

```csharp
Task RenameVM(VirtualMachine virtualMachine, string newName)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | The VM to rename |
| `newName` | `string` | New display name for the VM |

### Power State Operations

All power state methods take a single `VirtualMachine` parameter:

```csharp
Task StartVM(VirtualMachine virtualMachine)
Task ShutdownVM(VirtualMachine virtualMachine)
Task TurnOffVM(VirtualMachine virtualMachine)
Task PauseVM(VirtualMachine virtualMachine)
Task ResumeVM(VirtualMachine virtualMachine)
Task ResetVM(VirtualMachine virtualMachine)
```

| Method | Description | Resulting State |
|--------|-------------|-----------------|
| `StartVM` | Start/power on a stopped VM | `Enabled` (Running) |
| `ShutdownVM` | Graceful OS shutdown (requires integration services) | `Disabled` (Stopped) |
| `TurnOffVM` | Force power off (like pulling the plug) | `Disabled` (Stopped) |
| `PauseVM` | Pause VM execution (freezes state) | `Pause` (Paused) |
| `ResumeVM` | Resume a paused VM | `Enabled` (Running) |
| `ResetVM` | Hard reset (restart) | `Reset` → `Enabled` |

### Configure Robot (Connection String)

```csharp
Task ConfigureRobot(
    VirtualMachine virtualMachine,
    string connectionString,
    string username,
    SecureString password)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `connectionString` | `string` | UiPath Orchestrator connection string |
| `username` | `string` | VM login username |
| `password` | `SecureString` | VM login password |

### Configure Robot (Orchestrator URL + Machine Key)

```csharp
Task ConfigureRobot(
    VirtualMachine virtualMachine,
    string orchestratorURL,
    string machineKey,
    string username,
    SecureString password)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `orchestratorURL` | `string` | UiPath Orchestrator URL |
| `machineKey` | `string` | Machine key from Orchestrator |
| `username` | `string` | VM login username |
| `password` | `SecureString` | VM login password |

---

## ICheckPointService

Access: `hyperv.CheckPointService(clientProvider, virtualMachineService)`

### Take VM Checkpoint

```csharp
Task<Checkpoint> TakeVMCheckpoint(VirtualMachine vm, string checkpointName, string checkpointDescription)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vm` | `VirtualMachine` | Target VM |
| `checkpointName` | `string` | Name for the checkpoint |
| `checkpointDescription` | `string` | Description for the checkpoint |

**Returns:** `Checkpoint` — the created checkpoint

### Get VM Checkpoint List

```csharp
Task<List<Checkpoint>> GetVMCheckpointList(VirtualMachine vm)
```

**Returns:** `List<Checkpoint>` — all checkpoints for the VM

### Delete VM Checkpoint

```csharp
Task DeleteVMCheckpoint(VirtualMachine vm, Checkpoint checkpoint, bool includeAllChildCheckpoints)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vm` | `VirtualMachine` | Target VM |
| `checkpoint` | `Checkpoint` | Checkpoint to delete |
| `includeAllChildCheckpoints` | `bool` | Also delete all child checkpoints in the tree |

### Delete All VM Checkpoints

```csharp
Task DeleteAllVMCheckpoints(VirtualMachine virtualMachine)
```

### Revert VM Checkpoint

```csharp
Task RevertVMCheckpoint(VirtualMachine vm, Checkpoint checkpoint)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vm` | `VirtualMachine` | Target VM |
| `checkpoint` | `Checkpoint` | Checkpoint to revert to |

---

## Data Models

### VirtualMachine

```csharp
[DataContract]
public class VirtualMachine
{
    [DataMember] public string Id { get; set; }
    [DataMember] public string Name { get; set; }
    [DataMember] public string Description { get; set; }
    [DataMember] public VMGeneration Generation { get; set; }
    [DataMember] public string Location { get; set; }
    [DataMember] public string RAM { get; set; }
    [DataMember] public NetworkAdapter[] Adapters { get; set; }
    [DataMember] public string GuestOS { get; set; }
    [DataMember] public string FullyQualifiedDomainName { get; set; }
    [DataMember] public VMState State { get; set; }
}
```

### Checkpoint

```csharp
[DataContract]
public class Checkpoint
{
    [DataMember] public string Id { get; set; }
    [DataMember] public string Name { get; set; }
    [DataMember] public string Description { get; set; }
    [DataMember] public DateTime CreationDate { get; set; }
}
```

### NetworkAdapter

```csharp
[DataContract]
public class NetworkAdapter
{
    [DataMember] public string Name { get; set; }
    [DataMember] public string MACAddress { get; set; }
    [DataMember] public string Id { get; set; }
    [DataMember] public string Connection { get; set; }
    [DataMember] public string IPv4Address { get; set; }
    [DataMember] public string IPv6Address { get; set; }
}
```

---

## Enums

### VMGeneration

```csharp
[DataContract]
public enum VMGeneration
{
    Generation1,    // IDE-based boot, legacy BIOS
    Generation2     // SCSI-based boot, UEFI firmware
}
```

### VMState

```csharp
[DataContract]
public enum VMState
{
    Enabled = 2,    // Running
    Disabled = 3,   // Turned off
    ShutDown = 4,   // In the process of shutting down
    Offline = 6,    // Completing commands, dropping new requests
    Pause = 9,      // Paused (frozen)
    Reset = 11      // Resetting
}
```

### VMImportType

```csharp
public enum VMImportType
{
    Restore,    // Import in-place (uses original file paths)
    Copy        // Copy files to new location during import
}
```

### FilterBy

```csharp
public enum FilterBy
{
    Name,       // Filter VMs by display name
    Location    // Filter VMs by file location path
}
```

### FilterOperator

```csharp
public enum FilterOperator
{
    Equals,
    Contains,
    StartsWith,
    EndsWith
}
```

### VmStateFilter

```csharp
public enum VmStateFilter
{
    Running = 2,    // VM is running
    Stopped = 3,    // VM is turned off
    Paused = 9      // VM is paused
}
```

### VMBootOrder

```csharp
public enum VMBootOrder
{
    Floppy,
    CD,
    IDE,
    PXE,
    SCSI
}
```

### VMSnapshotType

```csharp
public enum VMSnapshotType
{
    Full = 2,   // Full checkpoint (memory + disk)
    Disk = 3    // Disk-only checkpoint
}
```
