# Citrix API Reference

Complete API reference for the `citrix` service from `UiPath.Citrix.Activities` package.

**Required package:** `"UiPath.Citrix.Activities": "[1.5.0]"`

**Auto-imported namespaces:** `UiPath.Citrix.Contracts`, `UiPath.Citrix`

---

## ICitrix

Root service accessor. Access via `citrix` in coded workflows.

```csharp
public interface ICitrix
{
    ICitrixService CitrixService(string serverAddress, int port, string userName, SecureString password);
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `serverAddress` | `string` | XenServer/Citrix Hypervisor host address |
| `port` | `int` | Connection port (typically `443` for HTTPS) |
| `userName` | `string` | Username for authentication (e.g., `"root"`) |
| `password` | `SecureString` | Password for authentication |

---

## ICitrixService

Access: `citrix.CitrixService(serverAddress, port, userName, password)`

### Get VM List

```csharp
Task<VirtualMachine[]> GetVMListAsync(
    FilterByEnum filterBy,
    string filterValue,
    bool includeSubfolders,
    PowerStateFilter powerStateFilter,
    bool includeGuestOSDetails)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `filterBy` | `FilterByEnum` | Filter field: `All`, `Name`, `Folder`, or `Tag` |
| `filterValue` | `string` | Value to filter by (ignored when `filterBy` is `All`) |
| `includeSubfolders` | `bool` | Include VMs in subfolders when filtering by `Folder` |
| `powerStateFilter` | `PowerStateFilter` | Filter by power state: `Halted`, `Paused`, `Running`, `Suspended`, `Unknown`, or `All` |
| `includeGuestOSDetails` | `bool` | Include guest OS information (slower) |

**Returns:** `VirtualMachine[]`

### Get Template List

```csharp
Task<VirtualMachine[]> GetTemplateListAsync(
    FilterByEnum filterBy,
    string filterValue,
    bool includeSubfolders)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `filterBy` | `FilterByEnum` | Filter field: `All`, `Name`, `Folder`, or `Tag` |
| `filterValue` | `string` | Value to filter by |
| `includeSubfolders` | `bool` | Include templates in subfolders |

**Returns:** `VirtualMachine[]` — array of template VMs (where `IsTemplate` is `true`)

### Get VM by UUID

```csharp
Task<VirtualMachine> GetVMByUUIDAsync(string vmUUID)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `vmUUID` | `string` | UUID of the virtual machine |

**Returns:** `VirtualMachine`

### Create VM from Template

```csharp
Task<VirtualMachine> CreateVMFromTemplateAsync(
    VirtualMachine customTemplate,
    string homeServerUUID,
    string storageRepositoryUUID,
    string virtualMachineName,
    string virtualMachineDescription,
    bool powerOnAfterCreation)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `customTemplate` | `VirtualMachine` | Template VM to clone from |
| `homeServerUUID` | `string` | UUID of the target XenServer host |
| `storageRepositoryUUID` | `string` | UUID of the storage repository for the new VM |
| `virtualMachineName` | `string` | Name for the new VM |
| `virtualMachineDescription` | `string` | Description for the new VM |
| `powerOnAfterCreation` | `bool` | Whether to power on after creation |

**Returns:** `VirtualMachine` — the created VM

### Delete VM

```csharp
Task DeleteVMAsync(
    VirtualMachine virtualMachine,
    bool deleteDisks,
    bool deleteSnapshots,
    bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to delete |
| `deleteDisks` | `bool` | Also delete associated disks |
| `deleteSnapshots` | `bool` | Also delete associated snapshots |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Rename VM

```csharp
Task<VirtualMachine> RenameVMAsync(VirtualMachine virtualMachine, string newName)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to rename |
| `newName` | `string` | New display name |

**Returns:** `VirtualMachine` — updated VM

### Power On VM

```csharp
Task PowerOnVMAsync(VirtualMachine virtualMachine, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to power on |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Power Off VM

```csharp
Task PowerOffVMAsync(VirtualMachine virtualMachine, bool forcedShutDown, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to power off |
| `forcedShutDown` | `bool` | Force shutdown (hard power off) instead of graceful |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Restart VM

```csharp
Task RestartVMAsync(VirtualMachine virtualMachine, bool forcedReboot, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to restart |
| `forcedReboot` | `bool` | Force reboot (hard reset) instead of graceful restart |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Suspend VM

```csharp
Task SuspendVMAsync(VirtualMachine virtualMachine, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to suspend |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Resume VM

```csharp
Task ResumeVMAsync(VirtualMachine virtualMachine, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | VM to resume from suspended state |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Add Tag to VM

```csharp
Task<VirtualMachine> AddTagToVMAsync(VirtualMachine virtualMachine, string tagToBeAdded)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `tagToBeAdded` | `string` | Tag value to add |

**Returns:** `VirtualMachine` — updated VM

### Remove Tag from VM

```csharp
Task<VirtualMachine> RemoveTagFromVMAsync(VirtualMachine virtualMachine, string tagToRemove)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `tagToRemove` | `string` | Tag value to remove |

**Returns:** `VirtualMachine` — updated VM

### Set Folder for VM

```csharp
Task<VirtualMachine> SetFolderForVMAsync(VirtualMachine virtualMachine, string newFolder)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `newFolder` | `string` | Folder path to assign the VM to |

**Returns:** `VirtualMachine` — updated VM

### Remove VM from Folder

```csharp
Task<VirtualMachine> RemoveVMFromFolderAsync(VirtualMachine virtualMachine, string folderToRemoveFrom)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `folderToRemoveFrom` | `string` | Folder path to remove the VM from |

**Returns:** `VirtualMachine` — updated VM

### Take VM Snapshot

```csharp
Task<Snapshot> TakeVMSnapshotAsync(
    VirtualMachine virtualMachine,
    string snapshotName,
    string snapshotDescription,
    bool snapshotVmMemory,
    bool quiesce,
    bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `snapshotName` | `string` | Name for the snapshot |
| `snapshotDescription` | `string` | Description for the snapshot |
| `snapshotVmMemory` | `bool` | Include VM memory in snapshot |
| `quiesce` | `bool` | Quiesce the file system before snapshot (requires VM tools) |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

**Returns:** `Snapshot` — the created snapshot

### Get VM Snapshots List

```csharp
Task<Snapshot[]> GetVMSnapshotsListAsync(VirtualMachine virtualMachine)
```

**Returns:** `Snapshot[]` — all snapshots for the VM

### Delete VM Snapshot

```csharp
Task DeleteVMSnapshotAsync(VirtualMachine virtualMachine, Snapshot snapshot, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `snapshot` | `Snapshot` | Snapshot to delete |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Delete All VM Snapshots

```csharp
Task DeleteAllVMSnapshotAsync(VirtualMachine virtualMachine, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Revert VM to Snapshot

```csharp
Task RevertVMToSnapshotAsync(VirtualMachine virtualMachine, Snapshot snapshot, bool waitForCompletion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `virtualMachine` | `VirtualMachine` | Target VM |
| `snapshot` | `Snapshot` | Snapshot to revert to |
| `waitForCompletion` | `bool` | Wait for the operation to complete |

### Get Server List

```csharp
Task<Server[]> GetServerListAsync()
```

**Returns:** `Server[]` — all XenServer hosts in the pool

### Get Host Storage Repositories

```csharp
Task<StorageRepository[]> GetHostStorageRepositoriesAsync(Server host)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `host` | `Server` | XenServer host to query |

**Returns:** `StorageRepository[]` — storage repositories available on the host

---

## Data Models

### VirtualMachine

```csharp
[DataContract]
public class VirtualMachine
{
    [DataMember] public string UUID { get; }
    [DataMember] public string Name { get; }
    [DataMember] public string HomeServer { get; }
    [DataMember] public string Folder { get; }
    [DataMember] public string[] Tags { get; }
    [DataMember] public string[] IPv4Addresses { get; }
    [DataMember] public string[] IPv6Addresses { get; }
    [DataMember] public string GuestOS { get; }
    [DataMember] public VirtualMachinePowerState PowerState { get; }
    [DataMember] public bool IsTemplate { get; }
}
```

### Snapshot

```csharp
[DataContract]
public class Snapshot
{
    [DataMember] public string UUID { get; }
    [DataMember] public string Name { get; }
    [DataMember] public string Description { get; }
    [DataMember] public DateTime CreationDate { get; }
}
```

### Server

```csharp
[DataContract]
public class Server
{
    [DataMember] public string UUID { get; }
    [DataMember] public string Name { get; }
    [DataMember] public ServerPowerState PowerState { get; }
    [DataMember] public bool IsMaster { get; }
    [DataMember] public bool InMaintenanceMode { get; }
}
```

### StorageRepository

```csharp
[DataContract]
public class StorageRepository
{
    [DataMember] public string UUID { get; }
    [DataMember] public string Name { get; }
    [DataMember] public bool Shared { get; }
    [DataMember] public long TotalCapacity { get; }
    [DataMember] public long FreeSpace { get; }
    [DataMember] public decimal PercentFree { get; }
    [DataMember] public long VirtualAllocationSize { get; }
}
```

---

## Enums

### FilterByEnum

```csharp
public enum FilterByEnum
{
    All = 0,        // No filter, return all
    Name = 1,       // Filter by VM/template name
    Folder = 2,     // Filter by folder path
    Tag = 3         // Filter by tag value
}
```

### PowerStateFilter

```csharp
public enum PowerStateFilter
{
    Halted = 0,
    Paused = 1,
    Running = 2,
    Suspended = 3,
    Unknown = 4,
    All = 5         // No filter, return all power states
}
```

### VirtualMachinePowerState

```csharp
[DataContract]
public enum VirtualMachinePowerState
{
    Halted = 0,
    Paused = 1,
    Running = 2,
    Suspended = 3,
    Unknown = 4
}
```

### ServerPowerState

```csharp
[DataContract]
public enum ServerPowerState
{
    Halted = 0,
    Running = 1
}
```
