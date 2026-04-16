# Amazon WorkSpaces Activities API Reference

Reference for the `awrks` service from `UiPath.AmazonWorkSpaces.Activities` package.

**Required package:** `"UiPath.AmazonWorkSpaces.Activities": "[1.4.1]"`

**Auto-imported namespaces:** `UiPath.AmazonWorkSpaces.Activities.API`, `UiPath.AmazonWorkSpaces.Core`, `UiPath.Core`, `UiPath.AmazonWorkSpaces.Models`

**Service accessor:** `awrks` (type `IAmazonWorkSpacesService`)

---

## Overview

The Amazon WorkSpaces API provides coded workflow access to manage AWS WorkSpaces — cloud-based virtual desktops. You can create, start, stop, reboot, rebuild, restore, migrate, update, remove, and query WorkSpaces programmatically.

The main entry point is `IAmazonWorkSpacesService`, accessed via the `awrks` service accessor. This service acts as a factory: you call `awrks.AmazonWorkSpacesService(clientProvider)` with an `IAWRKSClientProvider` to obtain an `IWorkSpacesService` instance bound to your AWS credentials. All workspace operations are on `IWorkSpacesService`.

### Usage Pattern

```csharp
// 1. Obtain the IWorkSpacesService from the factory
IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);

// 2. Call operations on the service
AWRKSWorkspace info = await workSpacesService.GetWorkSpaceInfo("ws-abc123");
await workSpacesService.StopWorkSpace(info, isWaitForCompletion: true);
```

### API Categories

| Category | Description | Reference |
|---|---|---|
| **Service Factory** | Create an `IWorkSpacesService` from a client provider | [api.md - Service Factory](api.md#service-factory) |
| **Lifecycle Operations** | Start, stop, reboot, rebuild, restore, remove WorkSpaces | [api.md - Lifecycle Operations](api.md#lifecycle-operations) |
| **Provisioning** | Create new WorkSpaces | [api.md - Provisioning](api.md#provisioning) |
| **Query** | Get WorkSpace information | [api.md - Query](api.md#query) |
| **Migration** | Migrate WorkSpaces to a different bundle | [api.md - Migration](api.md#migration) |
| **Update** | Modify WorkSpace properties (compute type, running mode, tags, volume size) | [api.md - Update](api.md#update) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Type Reference

### AWRKSWorkspace

The main WorkSpace data object returned by most operations.

| Property | Type | Description |
|---|---|---|
| `WorkSpaceId` | `string` | The WorkSpace identifier |
| `BundleId` | `string` | The bundle (hardware + software configuration) identifier |
| `DirectoryId` | `string` | The directory identifier |
| `UserName` | `string` | The user associated with the WorkSpace |
| `ComputeType` | `AWRKSComputeType?` | The compute type (Value, Standard, Performance, etc.) |
| `ComputerName` | `string` | The computer name of the WorkSpace |
| `IpAddress` | `string` | The IP address of the WorkSpace |
| `SubnetId` | `string` | The subnet identifier |
| `RootVolumeSizeGb` | `int` | Root volume size in GB |
| `RootVolumeEncryptionEnabled` | `bool` | Whether root volume encryption is enabled |
| `UserVolumeSizeGb` | `int` | User volume size in GB |
| `UserVolumeEncryptionEnabled` | `bool` | Whether user volume encryption is enabled |
| `VolumeEncryptionKey` | `string` | The KMS key used for volume encryption |
| `RunningMode` | `AWRKSRunningMode` | The running mode (AutoStop or AlwaysOn) |
| `RunningModeAutoStopTimeout` | `int` | Auto-stop timeout in minutes |
| `State` | `AWRKSState` | Current state of the WorkSpace |
| `Modificationstate` | `AWRKSModificationState` | Current modification state |
| `Tags` | `DataTable` | Tags associated with the WorkSpace |
| `ConnectionState` | `AWRKSConnectionState` | Current connection state |
| `ConnectionStateCheckTimestamp` | `DateTime` | Timestamp of last connection state check |
| `LastKnownUserConnectionTimestamp` | `DateTime` | Timestamp of last known user connection |
| `UserEmailAddress` | `string` | The user's email address |
| `UserFirstName` | `string` | The user's first name |
| `UserLastName` | `string` | The user's last name |

### AWRKSCreateWorkspaceParam

Parameters for creating a new WorkSpace.

| Property | Type | Description |
|---|---|---|
| `BundleId` | `string` | The bundle identifier for the WorkSpace |
| `DirectoryId` | `string` | The directory identifier |
| `UserName` | `string` | The user to assign to the WorkSpace |
| `ComputeType` | `string` | The compute type name (e.g., "STANDARD", "PERFORMANCE") |
| `RunningMode` | `AWRKSRunningMode` | The running mode (AutoStop or AlwaysOn) |
| `RunningModeAutoStopTimeout` | `int?` | Auto-stop timeout in minutes (optional) |
| `Tags` | `DataTable` | Tags to assign (optional) |
| `RootVolumeEncryptionEnabled` | `bool` | Enable root volume encryption |
| `RootVolumeSizeGb` | `int?` | Root volume size in GB (optional) |
| `UserVolumeEncryptionEnabled` | `bool` | Enable user volume encryption |
| `UserVolumeSizeGb` | `int?` | User volume size in GB (optional) |
| `VolumeEncryptionKey` | `string` | KMS key for volume encryption |

### AWRKSUpdateWorkspaceParam

Parameters for updating an existing WorkSpace.

| Property | Type | Description |
|---|---|---|
| `Workspace` | `AWRKSWorkspace` | The WorkSpace to update |
| `UpdateAction` | `AWRKSUpdateAction` | The type of update to perform |
| `ComputeType` | `string` | New compute type (when action is `ModifyComputeType`) |
| `RunningMode` | `string` | New running mode (when action is `ModifyRunningMode`) |
| `RunningModeAutoStopTimeout` | `int?` | New auto-stop timeout in minutes (optional) |
| `Tags` | `DataTable` | New tags (when action is `ModifyTags`) |
| `IntendedState` | `string` | Target state (when action is `ModifyState`) |
| `VolumeToResize` | `string` | Volume to resize: "RootVolume" or "UserVolume" (when action is `ModifyVolumeSize`) |
| `VolumeNewSize` | `int?` | New volume size in GB (when action is `ModifyVolumeSize`) |
| `DeleteAllExistingTags` | `bool` | Whether to delete all existing tags before adding new ones |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `AWRKSComputeType` | `Value`, `Standard`, `Performance`, `Power`, `PowerPro`, `Graphics`, `GraphicsPro` | WorkSpace compute tier |
| `AWRKSRunningMode` | `AutoStop`, `AlwaysOn` | WorkSpace running mode |
| `AWRKSState` | `PENDING`, `AVAILABLE`, `IMPAIRED`, `UNHEALTHY`, `REBOOTING`, `STARTING`, `REBUILDING`, `RESTORING`, `MAINTENANCE`, `ADMIN_MAINTENANCE`, `TERMINATING`, `TERMINATED`, `SUSPENDED`, `UPDATING`, `STOPPING`, `STOPPED`, `ERROR` | WorkSpace lifecycle state |
| `AWRKSConnectionState` | `CONNECTED`, `DISCONNECTED`, `UNKNOWN` | User connection state |
| `AWRKSModificationState` | `ModifyingCompute`, `ModifyingStorage`, `None` | In-progress modification state |
| `AWRKSUpdateAction` | `ModifyRunningMode`, `ModifyComputeType`, `ModifyTags`, `ModifyState`, `ModifyVolumeSize` | Type of update operation |
| `AWRKSVolume` | `RootVolume`, `UserVolume` | Volume type for resize operations |
| `AWRKSMaintenanceState` | `Available`, `AdminMaintenance` | Maintenance state |
