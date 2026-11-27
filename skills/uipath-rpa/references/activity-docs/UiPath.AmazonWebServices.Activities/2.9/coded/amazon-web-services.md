# Amazon Web Services Activities API Reference

Reference for the `aws` service from `UiPath.AmazonWebServices.Activities` package.

**Required package:** `"UiPath.AmazonWebServices.Activities": "[1.4.1]"`

**Auto-imported namespaces:** `UiPath.AmazonWebServices.Activities.API`, `UiPath.AmazonWebServices.Models`, `UiPath.Core`, `UiPath.AmazonWebServices.Core`

**Service accessor:** `aws` (type `IAWSService`)

---

## Overview

The Amazon Web Services API provides coded workflow access to manage AWS resources — EC2 instances, S3 buckets and objects, IAM users/groups/roles/policies, and EBS storage volumes.

The main entry point is `IAWSService`, accessed via the `aws` service accessor. This service acts as a factory: each method takes an `IAWSClientProvider` (obtained from an Amazon Scope activity) and returns a sub-service bound to your AWS credentials.

### Usage Pattern

```csharp
// 1. Obtain sub-services from the factory
IAWSEC2InstanceService ec2 = aws.EC2InstanceService(clientProvider);
IAWSS3BucketService s3Buckets = aws.S3BucketService(clientProvider);
IAWSS3ObjectService s3Objects = aws.S3ObjectService(clientProvider);
IAWSIAMUserService iamUsers = aws.IAMUserService(clientProvider);

// 2. Call operations on the sub-services
AWSEc2Instance instance = await ec2.GetEC2Instance("i-0abc123");
AWSS3Bucket bucket = await s3Buckets.GetBucket("my-bucket");
```

### API Categories

| Category | Sub-Service | Description | Reference |
|---|---|---|---|
| **EC2 Instances** | `IAWSEC2InstanceService` | Create, start, stop, reboot, terminate EC2 instances; run PowerShell commands | [api.md - EC2 Instances](api.md#ec2-instances) |
| **S3 Buckets** | `IAWSS3BucketService` | Create, update, delete, query S3 buckets; manage policies, public access, logging | [api.md - S3 Buckets](api.md#s3-buckets) |
| **S3 Objects** | `IAWSS3ObjectService` | Upload, download, copy, delete S3 objects; manage ACLs | [api.md - S3 Objects](api.md#s3-objects) |
| **IAM Users** | `IAWSIAMUserService` | Create, get, update, delete IAM users; change passwords | [api.md - IAM Users](api.md#iam-users) |
| **IAM Groups** | `IAWSIAMGroupService` | Create, get, update, delete IAM groups; manage group membership | [api.md - IAM Groups](api.md#iam-groups) |
| **IAM Roles** | `IAWSIAMRoleService` | Create, get, update, delete IAM roles; manage instance profiles | [api.md - IAM Roles](api.md#iam-roles) |
| **IAM Policies** | `IAWSIAMPolicyService` | Create, get, update, delete policies; attach/detach managed/inline policies | [api.md - IAM Policies](api.md#iam-policies) |
| **EBS Volumes** | `IAWSStorageVolumeService` | Create, get, delete, attach EBS volumes | [api.md - EBS Volumes](api.md#ebs-volumes) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Service Factory Methods

The `IAWSService` (accessed via `aws`) exposes these factory methods. Each takes an `IAWSClientProvider` and returns the sub-service:

| Method | Returns | Description |
|---|---|---|
| `EC2InstanceService(clientProvider)` | `IAWSEC2InstanceService` | EC2 instance management |
| `S3BucketService(clientProvider)` | `IAWSS3BucketService` | S3 bucket management |
| `S3ObjectService(clientProvider)` | `IAWSS3ObjectService` | S3 object management |
| `IAMUserService(clientProvider)` | `IAWSIAMUserService` | IAM user management |
| `IAMGroupService(clientProvider)` | `IAWSIAMGroupService` | IAM group management |
| `IAMRoleService(clientProvider)` | `IAWSIAMRoleService` | IAM role management |
| `IAMPolicyService(clientProvider)` | `IAWSIAMPolicyService` | IAM policy management |
| `StorageVolumeService(clientProvider)` | `IAWSStorageVolumeService` | EBS volume management |

---

## Type Reference

### AWSEc2Instance

EC2 instance data object.

| Property | Type | Description |
|---|---|---|
| `InstanceId` | `string` | The EC2 instance identifier |
| `InstanceType` | `string` | The instance type (e.g., "t2.micro") |
| `Name` | `string` | The instance name (from the "Name" tag) |
| `AvailabilityZone` | `string` | The availability zone |
| `ImageId` | `string` | The AMI image identifier |
| `CreationDate` | `DateTime` | Launch time |
| `KeyPairName` | `string` | The key pair name |
| `VirtualPrivateCloudId` | `string` | The VPC identifier |
| `SubnetId` | `string` | The subnet identifier |
| `IAMRole` | `string` | The IAM role |
| `PublicDns` | `string` | Public DNS name |
| `PublicIPv4Address` | `string` | Public IPv4 address |
| `PrivateDnsName` | `string` | Private DNS name |
| `PrivateIPv4Address` | `string` | Private IPv4 address |
| `IPv6Addresses` | `string` | IPv6 addresses |
| `HibernationEnabled` | `bool` | Whether hibernation is enabled |
| `ShutdownBehavior` | `string` | Shutdown behavior |
| `State` | `string` | Current state (e.g., "running", "stopped") |
| `Tags` | `DataTable` | Instance tags |
| `OSType` | `string` | Operating system type |

### AWSS3Bucket

S3 bucket data object.

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Bucket name |
| `ARN` | `string` | Bucket ARN |
| `CreationDate` | `DateTime?` | Creation date |
| `BucketDetails` | `AWSS3BucketDetails` | Extended details (call `GetDetails()`) |

### AWSS3BucketDetails

Extended S3 bucket details (populated when `includeDetails: true`).

| Property | Type | Description |
|---|---|---|
| `OwnerId` | `string` | Bucket owner ID |
| `OwnerDisplayName` | `string` | Bucket owner display name |
| `Region` | `string` | Bucket region |
| `VersioningEnabled` | `bool` | Whether versioning is enabled |
| `DefaultEncryption` | `AWSEncryptionMethod` | Default encryption method |
| `AWSEncryptionKey` | `string` | Encryption key |
| `Tags` | `DataTable` | Bucket tags |
| `ObjectLockEnabled` | `bool` | Whether object lock is enabled |
| `ServerAccessLoggingEnabled` | `bool` | Whether access logging is enabled |
| `PublicAccessBlocked` | `bool` | Whether public access is blocked |

### AWSS3Object

S3 object data object.

| Property | Type | Description |
|---|---|---|
| `KeyName` | `string` | Object key (path within bucket) |
| `BucketName` | `string` | Parent bucket name |
| `VersionId` | `string` | Object version ID |
| `ETag` | `string` | Entity tag |
| `LastModified` | `DateTime` | Last modified date |
| `Path` | `string` | S3 path (`s3://bucket/key`) |
| `Url` | `string` | Full HTTPS URL |
| `Metadata` | `DataTable` | Object metadata |
| `Versions` | `AWSS3ObjectVersionInfo[]` | Version history (when requested) |
| `Size` | `long` | Object size in bytes |
| `Tags` | `DataTable` | Object tags |
| `StorageClass` | `S3ObjectStorageType` | Storage class |
| `OwnerId` | `string` | Owner ID |
| `OwnerDisplayName` | `string` | Owner display name |
| `IsFolder` | `bool` | Whether this represents a folder |

### AWSS3ObjectVersionInfo

S3 object version information.

| Property | Type | Description |
|---|---|---|
| `VersionId` | `string` | Version identifier |
| `ETag` | `string` | Entity tag |
| `LastModified` | `DateTime` | Last modified date |
| `IsLatest` | `bool` | Whether this is the latest version |
| `Size` | `long` | Version size in bytes |
| `OwnerId` | `string` | Owner ID |
| `OwnerDisplayName` | `string` | Owner display name |

### AWSS3ObjectACL

S3 object access control entry.

| Property | Type | Description |
|---|---|---|
| `Grantee` | `string` | Grantee identifier (canonical user ID or email) |
| `GranteeType` | `string` | Grantee type (e.g., "CanonicalUser", "Email") |
| `CanReadObject` | `bool` | Permission to read the object |
| `CanReadObjectPermissions` | `bool` | Permission to read ACL |
| `CanWriteObjectPermissions` | `bool` | Permission to write ACL |

### AWSIAMUser

IAM user data object.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | User ID |
| `Name` | `string` | User name |
| `Arn` | `string` | User ARN |
| `CreateDate` | `DateTime` | Creation date |
| `PasswordLastUsed` | `DateTime` | Last password usage date |
| `Path` | `string` | IAM path |
| `PermissionsBoundaryArn` | `string` | Permissions boundary ARN |
| `Tags` | `DataTable` | User tags |

### AWSIAMGroup

IAM group data object.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Group ID |
| `Name` | `string` | Group name |
| `Arn` | `string` | Group ARN |
| `CreateDate` | `DateTime` | Creation date |
| `Path` | `string` | IAM path |

### AWSIAMRole

IAM role data object.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Role ID |
| `Name` | `string` | Role name |
| `Arn` | `string` | Role ARN |
| `AssumeRolePolicyDocument` | `string` | Trust policy document (JSON) |
| `Description` | `string` | Role description |
| `MaxSessionDuration` | `int` | Maximum session duration in seconds |
| `CreateDate` | `DateTime` | Creation date |
| `Path` | `string` | IAM path |
| `PermissionsBoundaryArn` | `string` | Permissions boundary ARN |
| `RoleLastUsed` | `DateTime?` | Last used date |
| `RoleLastUsedRegion` | `string` | Region where last used |
| `Tags` | `DataTable` | Role tags |

### AWSIAMManagedPolicy

Full managed policy data object (extends `AWSIAMManagedPolicyBasic`).

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Policy name (inherited) |
| `Arn` | `string` | Policy ARN (inherited) |
| `ID` | `string` | Policy ID |
| `Description` | `string` | Policy description |
| `AttachmentCount` | `int` | Number of attached entities |
| `CreateDate` | `DateTime` | Creation date |
| `UpdateDate` | `DateTime` | Last update date |
| `DefaultVersionId` | `string` | Default version ID |
| `Versions` | `AWSIAMPolicyVersion[]` | All policy versions |
| `IsAttachable` | `bool` | Whether the policy can be attached |
| `Path` | `string` | IAM path |
| `PermissionsBoundaryUsageCount` | `int` | Permissions boundary usage count |
| `Tags` | `DataTable` | Policy tags |

### AWSIAMManagedPolicyBasic

Basic managed policy info (base class for `AWSIAMManagedPolicy`).

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Policy name |
| `Arn` | `string` | Policy ARN |

### AWSIAMInlinePolicy

Inline policy data object.

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Policy name |
| `Document` | `string` | Policy document (JSON) |

### AWSIAMPolicyVersion

Policy version data object.

| Property | Type | Description |
|---|---|---|
| `VersionId` | `string` | Version identifier |
| `IsDefaultVersion` | `bool` | Whether this is the default version |
| `Document` | `string` | Policy document (JSON) |
| `CreateDate` | `DateTime` | Creation date |

### AWSEBSVolume

EBS volume data object.

| Property | Type | Description |
|---|---|---|
| `VolumeId` | `string` | Volume identifier |
| `VolumeType` | `VolumeType` | Volume type (AWS SDK enum) |
| `AvailabilityZone` | `string` | Availability zone |
| `CreationDate` | `DateTime` | Creation date |
| `SnapshotId` | `string` | Source snapshot ID |
| `Size` | `int` | Size in GB |
| `IOPS` | `int` | IOPS |
| `Throughput` | `int` | Throughput |
| `Encrypted` | `bool` | Whether encrypted |
| `Tags` | `DataTable` | Volume tags |
| `VolumeState` | `VolumeState` | Current state (AWS SDK enum) |

### AWSPSCommandOutput

PowerShell command execution result.

| Property | Type | Description |
|---|---|---|
| `StandardOutputContent` | `string` | Standard output |
| `StandardErrorContent` | `string` | Standard error |
| `StatusDetails` | `string` | Status details |
| `ResponseCode` | `int` | Response code |
| `Status` | `PSCommandStatus` | Command status |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `AWSEncryptionMethod` | `None`, `AES_256`, `AWS_KMS` | Encryption method for S3 buckets/objects |
| `S3ObjectStorageType` | `Standard`, `Intelligent_Tiering`, `Standard_IA`, `OneZone_IA`, `Glacier`, `GlacierDeepArchive` | S3 object storage class |
| `Ec2InstanceState` | `All`, `Pending`, `Running`, `ShuttingDown`, `Terminated`, `Stopping`, `Stopped` | EC2 instance state filter |
| `Ec2InstanceAutoAssignPublicIP` | `Disable`, `Enable`, `UseSubNetSettings` | Public IP assignment for new EC2 instances |
| `InstanceShutdownBehavior` | `Stop`, `Terminate` | What happens when an EC2 instance shuts down |
| `PSCommandStatus` | `Cancelled`, `Cancelling`, `Delayed`, `Failed`, `InProgress`, `Pending`, `Success`, `TimedOut` | PowerShell command execution status |
| `IAMIdentityType` | `Group`, `Role`, `User` | IAM identity type |
| `IAMIdentityTypeExtended` | `All`, `Group`, `Role`, `User` | IAM identity type (with All option) |
| `IAMPolicyUsage` | `All`, `PermissionsPolicy`, `PermissionsBoundary` | Policy usage filter |
| `IAMPolicyScope` | `All`, `AWS`, `Local` | Policy scope filter |
| `ManagedPolicyAction` | `Attach`, `Detach` | Attach or detach a managed policy |
| `InlinePolicyAction` | `Add`, `Remove` | Add or remove an inline policy |
