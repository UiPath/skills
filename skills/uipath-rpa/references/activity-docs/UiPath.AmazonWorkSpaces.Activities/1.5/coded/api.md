# Amazon WorkSpaces — Full API Reference

Complete reference for `IAmazonWorkSpacesService` accessed via the `awrks` service accessor, and `IWorkSpacesService` obtained from it. For general info see [amazon-workspaces.md](amazon-workspaces.md).

---

## Service Factory

### AmazonWorkSpacesService

Creates an `IWorkSpacesService` instance bound to the given client provider. All workspace operations are performed on the returned service.

```csharp
IWorkSpacesService AmazonWorkSpacesService(IAWRKSClientProvider clientProvider);
```

| Parameter | Type | Description |
|---|---|---|
| `clientProvider` | `IAWRKSClientProvider` | The AWS client provider that supplies authenticated `AmazonWorkSpacesClient` and `AmazonWorkDocsClient` instances |

**Usage:**

```csharp
IWorkSpacesService workSpacesService = awrks.AmazonWorkSpacesService(clientProvider);
```

---

## Query

### GetWorkSpaceInfo

Retrieves detailed information about a specific WorkSpace by its ID.

```csharp
Task<AWRKSWorkspace> GetWorkSpaceInfo(string id);
```

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` | The WorkSpace identifier (e.g., `"ws-abc123def"`) |

**Returns:** `AWRKSWorkspace` — the full WorkSpace data object with all properties populated.

---

## Provisioning

### CreateWorkSpace

Creates a new WorkSpace with the specified parameters. Returns the created WorkSpace.

```csharp
Task<AWRKSWorkspace> CreateWorkSpace(AWRKSCreateWorkspaceParam param, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `param` | `AWRKSCreateWorkspaceParam` | The creation parameters (bundle, directory, user, compute type, volumes, etc.) |
| `isWaitForCompletion` | `bool` | If `true`, waits for the WorkSpace to reach `AVAILABLE` state before returning |

**Returns:** `AWRKSWorkspace` — the newly created WorkSpace.

**AWRKSCreateWorkspaceParam properties:**

| Property | Type | Required | Description |
|---|---|---|---|
| `BundleId` | `string` | Yes | The bundle identifier (hardware + software config) |
| `DirectoryId` | `string` | Yes | The directory identifier |
| `UserName` | `string` | Yes | The user to assign |
| `ComputeType` | `string` | No | Compute type name (e.g., `"STANDARD"`, `"PERFORMANCE"`) |
| `RunningMode` | `AWRKSRunningMode` | No | `AutoStop` or `AlwaysOn` |
| `RunningModeAutoStopTimeout` | `int?` | No | Auto-stop timeout in minutes |
| `Tags` | `DataTable` | No | Tags to assign |
| `RootVolumeEncryptionEnabled` | `bool` | No | Enable root volume encryption |
| `RootVolumeSizeGb` | `int?` | No | Root volume size in GB |
| `UserVolumeEncryptionEnabled` | `bool` | No | Enable user volume encryption |
| `UserVolumeSizeGb` | `int?` | No | User volume size in GB |
| `VolumeEncryptionKey` | `string` | No | KMS key for encryption |

---

## Lifecycle Operations

### StartWorkSpace

Starts a stopped WorkSpace.

```csharp
Task StartWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to start (must have `WorkSpaceId` set) |
| `isWaitForCompletion` | `bool` | If `true`, waits for the WorkSpace to reach `AVAILABLE` state |

### StopWorkSpace

Stops a running WorkSpace.

```csharp
Task StopWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to stop |
| `isWaitForCompletion` | `bool` | If `true`, waits for the WorkSpace to reach `STOPPED` state |

### RebootWorkSpace

Reboots a WorkSpace.

```csharp
Task RebootWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to reboot |
| `isWaitForCompletion` | `bool` | If `true`, waits for the WorkSpace to reach `AVAILABLE` state |

### RebuildWorkSpace

Rebuilds a WorkSpace from its original bundle image. User data on the D: drive is preserved, but the C: drive is restored to its original state.

```csharp
Task RebuildWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to rebuild |
| `isWaitForCompletion` | `bool` | If `true`, waits for the rebuild to complete |

### RestoreWorkSpace

Restores a WorkSpace to its last known healthy state.

```csharp
Task RestoreWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to restore |
| `isWaitForCompletion` | `bool` | If `true`, waits for the restore to complete |

### RemoveWorkSpace

Terminates (deletes) a WorkSpace permanently.

```csharp
Task RemoveWorkSpace(AWRKSWorkspace workspace, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to remove |
| `isWaitForCompletion` | `bool` | If `true`, waits for the WorkSpace to reach `TERMINATED` state |

---

## Migration

### MigrateWorkSpace

Migrates a WorkSpace to a different bundle. Returns the migrated WorkSpace with its new configuration.

```csharp
Task<AWRKSWorkspace> MigrateWorkSpace(AWRKSWorkspace workspace, string targetBundleId, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `workspace` | `AWRKSWorkspace` | The WorkSpace to migrate |
| `targetBundleId` | `string` | The target bundle identifier to migrate to |
| `isWaitForCompletion` | `bool` | If `true`, waits for the migration to complete |

**Returns:** `AWRKSWorkspace` — the migrated WorkSpace with updated properties.

---

## Update

### UpdateWorkSpace

Modifies a WorkSpace property. The `AWRKSUpdateWorkspaceParam.UpdateAction` field determines which property is changed.

```csharp
Task UpdateWorkSpace(AWRKSUpdateWorkspaceParam updateParam, bool isWaitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `updateParam` | `AWRKSUpdateWorkspaceParam` | The update parameters specifying what to change |
| `isWaitForCompletion` | `bool` | If `true`, waits for the modification to complete |

**AWRKSUpdateWorkspaceParam properties:**

| Property | Type | Description |
|---|---|---|
| `Workspace` | `AWRKSWorkspace` | The WorkSpace to update |
| `UpdateAction` | `AWRKSUpdateAction` | The type of modification (see below) |
| `ComputeType` | `string` | New compute type (used with `ModifyComputeType`) |
| `RunningMode` | `string` | New running mode (used with `ModifyRunningMode`) |
| `RunningModeAutoStopTimeout` | `int?` | New auto-stop timeout in minutes |
| `Tags` | `DataTable` | New tags (used with `ModifyTags`) |
| `IntendedState` | `string` | Target state (used with `ModifyState`) |
| `VolumeToResize` | `string` | `"RootVolume"` or `"UserVolume"` (used with `ModifyVolumeSize`) |
| `VolumeNewSize` | `int?` | New volume size in GB (used with `ModifyVolumeSize`) |
| `DeleteAllExistingTags` | `bool` | Delete all existing tags before adding new ones |

**Update actions (`AWRKSUpdateAction`):**

| Value | Fields Used | Description |
|---|---|---|
| `ModifyRunningMode` | `RunningMode`, `RunningModeAutoStopTimeout` | Change between AutoStop and AlwaysOn |
| `ModifyComputeType` | `ComputeType` | Change the compute tier |
| `ModifyTags` | `Tags`, `DeleteAllExistingTags` | Add/replace tags |
| `ModifyState` | `IntendedState` | Change the WorkSpace state |
| `ModifyVolumeSize` | `VolumeToResize`, `VolumeNewSize` | Resize root or user volume |
