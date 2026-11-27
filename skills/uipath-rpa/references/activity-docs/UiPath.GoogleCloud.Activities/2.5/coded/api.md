# Google Cloud — Full API Reference

Complete API reference for all Google Cloud sub-services accessed via the `gcp` service accessor. For general info see [google-cloud.md](google-cloud.md).

---

## Bucket Service (`IBucketService`)

Accessed via `gcp.BucketService(clientProvider)`.

### GetBucket

Gets a Cloud Storage bucket by name.

```csharp
Task<GCPBucket> GetBucket(string bucketName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `bucketName` | `string` | Yes | Name of the bucket |

**Returns:** `Task<GCPBucket>`

---

### CreateBucket

Creates a new Cloud Storage bucket.

```csharp
Task<GCPBucket> CreateBucket(BucketCreateParameters createParams);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `createParams` | `BucketCreateParameters` | Yes | Bucket creation parameters (name, location, storage class, etc.) |

**Returns:** `Task<GCPBucket>`

---

### UpdateBucket

Updates an existing Cloud Storage bucket.

```csharp
Task UpdateBucket(BucketUpdateParameters updateParams);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `updateParams` | `BucketUpdateParameters` | Yes | Bucket update parameters |

---

### DeleteBucket

Deletes a Cloud Storage bucket.

```csharp
Task DeleteBucket(GCPBucket bucket, bool isDeleteObjects);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `bucket` | `GCPBucket` | Yes | The bucket to delete |
| `isDeleteObjects` | `bool` | Yes | Also delete all objects inside the bucket |

---

## Instance Service (`IInstanceService`)

Accessed via `gcp.InstanceService(clientProvider)`. Manages Compute Engine VM instances.

### CreateInstance

Creates a new Compute Engine instance.

```csharp
Task<GCPInstance> CreateInstance(InstanceCreationParameters creationParams);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `creationParams` | `InstanceCreationParameters` | Yes | Instance creation parameters (name, zone, machine type, image, etc.) |

**Returns:** `Task<GCPInstance>`

---

### CreateInstance (from template)

Creates a new Compute Engine instance from an instance template.

```csharp
Task<GCPInstance> CreateInstance(InstanceCreationParameters creationParams, string instanceTemplate);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `creationParams` | `InstanceCreationParameters` | Yes | Instance creation parameters |
| `instanceTemplate` | `string` | Yes | Name of the instance template to use |

**Returns:** `Task<GCPInstance>`

---

### GetInstance

Gets a Compute Engine instance.

```csharp
Task<GCPInstance> GetInstance(string instanceName, string projectId, string zone);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instanceName` | `string` | Yes | Name of the instance |
| `projectId` | `string` | Yes | GCP project ID |
| `zone` | `string` | Yes | Compute Engine zone (e.g., `"us-central1-a"`) |

**Returns:** `Task<GCPInstance>`

---

### StartInstance

Starts a stopped Compute Engine instance.

```csharp
Task StartInstance(GCPInstance instance, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | The instance to start |
| `waitForCompletion` | `bool` | Yes | Wait for the operation to complete |

---

### StopInstance

Stops a running Compute Engine instance.

```csharp
Task StopInstance(GCPInstance instance, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | The instance to stop |
| `waitForCompletion` | `bool` | Yes | Wait for the operation to complete |

---

### ResetInstance

Resets (hard reboot) a Compute Engine instance.

```csharp
Task ResetInstance(GCPInstance instance, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | The instance to reset |
| `waitForCompletion` | `bool` | Yes | Wait for the operation to complete |

---

### DeleteInstance

Deletes a Compute Engine instance.

```csharp
Task DeleteInstance(GCPInstance instance, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | The instance to delete |
| `waitForCompletion` | `bool` | Yes | Wait for the operation to complete |

---

### RunScriptOnInstance

Runs a script on a Compute Engine instance.

```csharp
Task<string> RunScriptOnInstance(GCPInstance instance, string script, string scriptKey, int? consoleTimeout);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | Target instance |
| `script` | `string` | Yes | Script content to execute |
| `scriptKey` | `string` | Yes | Metadata key for the script |
| `consoleTimeout` | `int?` | Yes | Console output timeout in seconds (`null` for default) |

**Returns:** `Task<string>` — Script output.

---

### ConfigureRobot (Orchestrator URL)

Configures a UiPath robot on a Compute Engine instance using Orchestrator URL and machine key.

```csharp
Task ConfigureRobot(GCPInstance instance, string orchestratorURL, string machineKey);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | Target instance |
| `orchestratorURL` | `string` | Yes | Orchestrator URL |
| `machineKey` | `string` | Yes | Machine key |

---

### ConfigureRobot (Connection String)

Configures a UiPath robot on a Compute Engine instance using a connection string.

```csharp
Task ConfigureRobot(GCPInstance instance, string connectionString);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `instance` | `GCPInstance` | Yes | Target instance |
| `connectionString` | `string` | Yes | Connection string |

---

## Object Service (`IObjectService`)

Accessed via `gcp.ObjectService(clientProvider)`. Manages Cloud Storage objects (blobs).

### GetObject

Gets a Cloud Storage object.

```csharp
Task<GCPObject> GetObject(GCPBucket bucket, string objectName, long? generation);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `bucket` | `GCPBucket` | Yes | The bucket containing the object |
| `objectName` | `string` | Yes | Name of the object |
| `generation` | `long?` | Yes | Object generation number (`null` for latest) |

**Returns:** `Task<GCPObject>`

---

### UploadObject

Uploads a local file as a Cloud Storage object.

```csharp
Task<GCPObject> UploadObject(
    GCPBucket bucket, string objectName, string fileToUpload,
    string contentType, Storage storage, DataTable metadata,
    string predefinedAcl, string customerManagedKey
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `bucket` | `GCPBucket` | Yes | Target bucket |
| `objectName` | `string` | Yes | Name for the object in the bucket |
| `fileToUpload` | `string` | Yes | Local file path to upload |
| `contentType` | `string` | Yes | MIME content type |
| `storage` | `Storage` | Yes | Storage class for the object |
| `metadata` | `DataTable` | Yes | Object metadata as key-value pairs |
| `predefinedAcl` | `string` | Yes | Predefined ACL (e.g., `"private"`, `"publicRead"`) |
| `customerManagedKey` | `string` | Yes | Customer-managed encryption key (or `null`) |

**Returns:** `Task<GCPObject>`

---

### DownloadObject

Downloads a Cloud Storage object to local disk.

```csharp
Task<ILocalResource> DownloadObject(
    GCPObject obj, long generation, string folder, string filename, bool overwrite
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `obj` | `GCPObject` | Yes | The object to download |
| `generation` | `long` | Yes | Object generation number |
| `folder` | `string` | Yes | Local destination folder |
| `filename` | `string` | Yes | Local destination filename |
| `overwrite` | `bool` | Yes | Overwrite existing file |

**Returns:** `Task<ILocalResource>`

---

### CopyObject

Copies a Cloud Storage object to another bucket/name.

```csharp
Task<GCPObject> CopyObject(
    GCPObject sourceObject, long sourceObjectGeneration,
    GCPBucket destinationBucket, string destinationObjectName, string predefinedACL
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `sourceObject` | `GCPObject` | Yes | Source object |
| `sourceObjectGeneration` | `long` | Yes | Generation number of the source object |
| `destinationBucket` | `GCPBucket` | Yes | Destination bucket |
| `destinationObjectName` | `string` | Yes | Name for the copied object |
| `predefinedACL` | `string` | Yes | Predefined ACL for the copy |

**Returns:** `Task<GCPObject>`

---

### DeleteObject

Deletes a Cloud Storage object.

```csharp
Task DeleteObject(GCPObject obj, long? generation);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `obj` | `GCPObject` | Yes | The object to delete |
| `generation` | `long?` | Yes | Generation number (`null` to delete the latest) |

---

## Policy Service (`IPolicyService`)

Accessed via `gcp.PolicyService(clientProvider)`. Manages IAM policies.

### GetIAMPolicy

Gets the IAM policy for a resource.

```csharp
Task<GCPIAMPolicy> GetIAMPolicy(ResourceType? resourceType, string fullResourceName, int? policyVersion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceType` | `ResourceType?` | Yes | Type of the resource (`null` for auto-detect) |
| `fullResourceName` | `string` | Yes | Full resource name (e.g., `"projects/my-project"`) |
| `policyVersion` | `int?` | Yes | Policy version to retrieve (`null` for default) |

**Returns:** `Task<GCPIAMPolicy>`

---

### SetIAMPolicy

Sets the IAM policy for a resource.

```csharp
Task SetIAMPolicy(ResourceType? resourceType, string fullResourceName, string policyData, GCPIAMPolicy policy);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceType` | `ResourceType?` | Yes | Type of the resource (`null` for auto-detect) |
| `fullResourceName` | `string` | Yes | Full resource name |
| `policyData` | `string` | Yes | Policy data as JSON string |
| `policy` | `GCPIAMPolicy` | Yes | Policy object to set |

---

## Project Service (`IProjectService`)

Accessed via `gcp.ProjectService(clientProvider)`.

### GetProject

Gets a GCP project by ID.

```csharp
Task<GCPProject> GetProject(string projectId);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `projectId` | `string` | Yes | GCP project ID |

**Returns:** `Task<GCPProject>`

---

## Role Service (`IRoleService`)

Accessed via `gcp.RoleService(clientProvider)`. Manages IAM roles.

### GetRole

Gets an IAM role.

```csharp
Task<GCPIAMRole> GetRole(string roleName, RoleType roleType, string parentId);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `roleName` | `string` | Yes | Name of the role |
| `roleType` | `RoleType` | Yes | Type of role (predefined, custom, etc.) |
| `parentId` | `string` | Yes | Parent resource ID (project or organization) |

**Returns:** `Task<GCPIAMRole>`

---

### CreateRole

Creates a custom IAM role.

```csharp
Task<GCPIAMRole> CreateRole(
    string roleName, string title, string description,
    string[] permissions, RoleLaunchStage launchStage,
    string parentId, RoleType roleType
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `roleName` | `string` | Yes | Role ID (e.g., `"myCustomRole"`) |
| `title` | `string` | Yes | Human-readable title |
| `description` | `string` | Yes | Role description |
| `permissions` | `string[]` | Yes | Array of permission strings (e.g., `"storage.buckets.list"`) |
| `launchStage` | `RoleLaunchStage` | Yes | Launch stage (Alpha, Beta, GA, etc.) |
| `parentId` | `string` | Yes | Parent resource ID |
| `roleType` | `RoleType` | Yes | Type of role |

**Returns:** `Task<GCPIAMRole>`

---

### UpdateRole

Updates an existing custom IAM role.

```csharp
Task<GCPIAMRole> UpdateRole(
    GCPIAMRole gcpIamRole, string newDescription,
    RoleLaunchStage? newLaunchStage, string newTitle,
    string[] permissionsToRemove, string[] permissionsToAdd
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `gcpIamRole` | `GCPIAMRole` | Yes | The role to update |
| `newDescription` | `string` | Yes | New description (or `null` to keep current) |
| `newLaunchStage` | `RoleLaunchStage?` | Yes | New launch stage (`null` to keep current) |
| `newTitle` | `string` | Yes | New title (or `null` to keep current) |
| `permissionsToRemove` | `string[]` | Yes | Permissions to remove |
| `permissionsToAdd` | `string[]` | Yes | Permissions to add |

**Returns:** `Task<GCPIAMRole>`

---

### DeleteRole

Deletes (soft-deletes) a custom IAM role.

```csharp
Task DeleteRole(GCPIAMRole role);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `role` | `GCPIAMRole` | Yes | The role to delete |

---

### UndeleteRole

Restores a previously deleted custom IAM role.

```csharp
Task UndeleteRole(GCPIAMRole role);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `role` | `GCPIAMRole` | Yes | The role to restore |

---

## Secret Data Service (`ISecretDataService`)

Accessed via `gcp.SecretDataService(clientProvider)`. Retrieves secrets from Secret Manager.

### GetSecretData

Gets a secret value from Secret Manager.

```csharp
Task<(string, SecureString)> GetSecretData(string projectId, string secretName, string secretVersion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `projectId` | `string` | Yes | GCP project ID |
| `secretName` | `string` | Yes | Name of the secret |
| `secretVersion` | `string` | Yes | Version of the secret (e.g., `"latest"`, `"1"`) |

**Returns:** `Task<(string, SecureString)>` — A tuple of (secret name, secret value as SecureString).
