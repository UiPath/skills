# Google Cloud Activities API Reference

Reference for the `gcp` service from `UiPath.GoogleCloud.Activities` package.

**Required package:** `"UiPath.GoogleCloud.Activities": "[1.0.0]"`

**Auto-imported namespaces:** `UiPath.GoogleCloud.Core`, `UiPath.Core`, `UiPath.GoogleCloud.Models`

**Service accessor:** `gcp` (type `IGoogleCloudService`)

---

## Architecture

The Google Cloud API is a facade that provides access to 7 specialized sub-services. All sub-services require an `IGCPClientProvider` for authentication.

### Accessing Sub-Services

```csharp
var bucketService = gcp.BucketService(clientProvider);
var instanceService = gcp.InstanceService(clientProvider);
var objectService = gcp.ObjectService(clientProvider);
var policyService = gcp.PolicyService(clientProvider);
var projectService = gcp.ProjectService(clientProvider);
var roleService = gcp.RoleService(clientProvider);
var secretService = gcp.SecretDataService(clientProvider);
```

---

## Sub-Services Summary

| Service | Accessor | Description |
|---|---|---|
| `IBucketService` | `gcp.BucketService(provider)` | Cloud Storage bucket CRUD |
| `IInstanceService` | `gcp.InstanceService(provider)` | Compute Engine instance lifecycle, scripts, UiPath robot config |
| `IObjectService` | `gcp.ObjectService(provider)` | Cloud Storage object operations (upload, download, copy, delete) |
| `IPolicyService` | `gcp.PolicyService(provider)` | IAM policy get/set |
| `IProjectService` | `gcp.ProjectService(provider)` | GCP project retrieval |
| `IRoleService` | `gcp.RoleService(provider)` | IAM role CRUD and undelete |
| `ISecretDataService` | `gcp.SecretDataService(provider)` | Secret Manager secret retrieval |

---

## Key Enum Reference Summary

| Enum | Used In | Description |
|---|---|---|
| `ResourceType` | `IPolicyService` | Type of GCP resource for IAM policy operations |
| `RoleType` | `IRoleService` | Type of IAM role (predefined, custom, etc.) |
| `RoleLaunchStage` | `IRoleService` | Launch stage of a custom IAM role (Alpha, Beta, GA, etc.) |
| `Storage` | `IObjectService` | Storage class for uploaded objects |

---

## Key Model Types

| Type | Description |
|---|---|
| `IGCPClientProvider` | GCP authentication/client provider (from `UiPath.GoogleCloud.Interfaces`) |
| `GCPBucket` | Represents a Cloud Storage bucket |
| `BucketCreateParameters` | Parameters for creating a bucket |
| `BucketUpdateParameters` | Parameters for updating a bucket |
| `GCPInstance` | Represents a Compute Engine VM instance |
| `InstanceCreationParameters` | Parameters for creating a VM instance |
| `GCPObject` | Represents a Cloud Storage object (blob) |
| `GCPIAMPolicy` | Represents an IAM policy |
| `GCPProject` | Represents a GCP project |
| `GCPIAMRole` | Represents an IAM role |
| `ILocalResource` | Local file resource (from `UiPath.Platform.ResourceHandling`) |

---

For the full API reference of all sub-services, see [api.md](api.md).

For complete coded workflow examples, see [examples.md](examples.md).
