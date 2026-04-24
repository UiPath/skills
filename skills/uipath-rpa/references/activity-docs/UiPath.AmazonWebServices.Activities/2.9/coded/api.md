# Amazon Web Services — Full API Reference

Complete reference for `IAWSService` accessed via the `aws` service accessor and all sub-services. For general info see [amazon-web-services.md](amazon-web-services.md).

---

## EC2 Instances

Sub-service: `IAWSEC2InstanceService` — obtained via `aws.EC2InstanceService(clientProvider)`.

### GetEC2Instance

Retrieves an EC2 instance by its ID.

```csharp
Task<AWSEc2Instance> GetEC2Instance(string instanceId);
```

| Parameter | Type | Description |
|---|---|---|
| `instanceId` | `string` | The EC2 instance ID (e.g., `"i-0abc123"`) |

### GetInstanceList

Lists EC2 instances with optional filters.

```csharp
Task<AWSEc2Instance[]> GetInstanceList(
    Ec2InstanceState state = Ec2InstanceState.All,
    string tagKey = default,
    string tagValue = default,
    string availabilityZone = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `state` | `Ec2InstanceState` | `All` | Filter by instance state |
| `tagKey` | `string` | `null` | Filter by tag key |
| `tagValue` | `string` | `null` | Filter by tag value |
| `availabilityZone` | `string` | `null` | Filter by availability zone |

### CreateEC2Instance

Creates a new EC2 instance with full configuration.

```csharp
Task<AWSEc2Instance> CreateEC2Instance(
    string instanceName,
    string zone,
    string instanceType,
    string imageId,
    bool isWaitForCompletion = true,
    bool enableHibernation = false,
    InstanceShutdownBehavior value = InstanceShutdownBehavior.Stop,
    DataTable tags = default,
    string userData = null,
    string subnetId = default,
    Ec2InstanceAutoAssignPublicIP autoAssignPublicIp = Ec2InstanceAutoAssignPublicIP.Disable,
    string iamrole = default,
    string[] securityGroupsIds = default,
    string keyPairName = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `instanceName` | `string` | — | Name for the instance |
| `zone` | `string` | — | Availability zone |
| `instanceType` | `string` | — | Instance type (e.g., "t2.micro") |
| `imageId` | `string` | — | AMI image ID |
| `isWaitForCompletion` | `bool` | `true` | Wait for instance to be running |
| `enableHibernation` | `bool` | `false` | Enable hibernation |
| `value` | `InstanceShutdownBehavior` | `Stop` | Shutdown behavior |
| `tags` | `DataTable` | `null` | Instance tags |
| `userData` | `string` | `null` | User data script |
| `subnetId` | `string` | `null` | Subnet ID |
| `autoAssignPublicIp` | `Ec2InstanceAutoAssignPublicIP` | `Disable` | Public IP assignment |
| `iamrole` | `string` | `null` | IAM role name |
| `securityGroupsIds` | `string[]` | `null` | Security group IDs |
| `keyPairName` | `string` | `null` | Key pair name for SSH access |

### CreateEc2InstanceByTemplate

Creates an EC2 instance from a launch template.

```csharp
Task<AWSEc2Instance> CreateEc2InstanceByTemplate(
    string instanceName, string templateId, bool waitForCompletion = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `instanceName` | `string` | — | Name for the instance |
| `templateId` | `string` | — | Launch template ID |
| `waitForCompletion` | `bool` | `true` | Wait for instance to be running |

### StartInstance

Starts a stopped EC2 instance.

```csharp
Task StartInstance(AWSEc2Instance ec2Instance, bool isWaitForCompletion = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ec2Instance` | `AWSEc2Instance` | — | The instance to start |
| `isWaitForCompletion` | `bool` | `true` | Wait for running state |

### StopInstance

Stops a running EC2 instance.

```csharp
Task StopInstance(AWSEc2Instance ec2Instance, bool isHibernate, bool isForce,
    bool isWaitForCompletion = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ec2Instance` | `AWSEc2Instance` | — | The instance to stop |
| `isHibernate` | `bool` | — | Hibernate instead of stop |
| `isForce` | `bool` | — | Force stop |
| `isWaitForCompletion` | `bool` | `true` | Wait for stopped state |

### RebootInstance

Reboots an EC2 instance.

```csharp
Task RebootInstance(AWSEc2Instance ec2Instance, bool isWaitForCompletion = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ec2Instance` | `AWSEc2Instance` | — | The instance to reboot |
| `isWaitForCompletion` | `bool` | `true` | Wait for running state |

### TerminateInstance

Terminates (permanently deletes) an EC2 instance.

```csharp
Task TerminateInstance(AWSEc2Instance ec2Instance, bool isWaitForCompletion = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ec2Instance` | `AWSEc2Instance` | — | The instance to terminate |
| `isWaitForCompletion` | `bool` | `true` | Wait for terminated state |

### RunPowerShellCommand

Runs a PowerShell command on an EC2 instance via SSM.

```csharp
Task<AWSPSCommandOutput> RunPowerShellCommand(
    AWSEc2Instance instance, string commands, string workingDirectory, string comment);
```

| Parameter | Type | Description |
|---|---|---|
| `instance` | `AWSEc2Instance` | Target instance |
| `commands` | `string` | PowerShell commands to execute |
| `workingDirectory` | `string` | Working directory for the command |
| `comment` | `string` | Comment for the command invocation |

**Returns:** `AWSPSCommandOutput` with `StandardOutputContent`, `StandardErrorContent`, `ResponseCode`, and `Status`.

### ConfigureRobot

Configures a UiPath Robot on an EC2 instance. Two overloads:

```csharp
// Using Orchestrator URL and machine key
Task ConfigureRobot(AWSEc2Instance instance, string orchestratorURL, string machineKey);

// Using a connection string
Task ConfigureRobot(AWSEc2Instance instance, string connectionString);
```

| Parameter | Type | Description |
|---|---|---|
| `instance` | `AWSEc2Instance` | Target EC2 instance |
| `orchestratorURL` | `string` | Orchestrator URL |
| `machineKey` | `string` | Machine key |
| `connectionString` | `string` | Full connection string |

---

## S3 Buckets

Sub-service: `IAWSS3BucketService` — obtained via `aws.S3BucketService(clientProvider)`.

### CreateBucket

Creates a new S3 bucket.

```csharp
Task<AWSS3Bucket> CreateBucket(
    string bucketName,
    bool isVersionsEnabled = false,
    bool isObjectLockEnabled = false,
    DataTable tags = null,
    AWSEncryptionMethod encryptionType = AWSEncryptionMethod.None,
    string encryptionKey = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucketName` | `string` | — | Bucket name |
| `isVersionsEnabled` | `bool` | `false` | Enable versioning |
| `isObjectLockEnabled` | `bool` | `false` | Enable object lock |
| `tags` | `DataTable` | `null` | Bucket tags |
| `encryptionType` | `AWSEncryptionMethod` | `None` | Default encryption |
| `encryptionKey` | `string` | `null` | KMS key (for `AWS_KMS`) |

### GetBucket

Retrieves a bucket by name.

```csharp
Task<AWSS3Bucket> GetBucket(string bucketName, bool includeDetails = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucketName` | `string` | — | Bucket name |
| `includeDetails` | `bool` | `false` | Include extended details (`AWSS3BucketDetails`) |

### GetBucketList

Lists buckets with optional tag filters.

```csharp
Task<AWSS3Bucket[]> GetBucketList(string region, string tagKey = default, string tagValue = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `region` | `string` | — | AWS region |
| `tagKey` | `string` | `null` | Filter by tag key |
| `tagValue` | `string` | `null` | Filter by tag value |

### UpdateBucket

Updates bucket settings.

```csharp
Task UpdateBucket(AWSS3Bucket bucket, bool isVersionsEnabled = false, DataTable tags = null,
    AWSEncryptionMethod encryptionType = AWSEncryptionMethod.None, string encryptionKey = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket` | `AWSS3Bucket` | — | The bucket to update |
| `isVersionsEnabled` | `bool` | `false` | Enable/disable versioning |
| `tags` | `DataTable` | `null` | New tags |
| `encryptionType` | `AWSEncryptionMethod` | `None` | Encryption method |
| `encryptionKey` | `string` | `null` | KMS key |

### EmptyBucket

Deletes all objects in a bucket.

```csharp
Task EmptyBucket(AWSS3Bucket bucket);
```

### DeleteBucket

Deletes a bucket. Returns `true` if successful.

```csharp
Task<bool> DeleteBucket(AWSS3Bucket bucket);
```

### GetBucketPolicy

Gets the bucket policy JSON.

```csharp
Task<string> GetBucketPolicy(AWSS3Bucket bucket);
```

### SetBucketPolicy

Sets the bucket policy.

```csharp
Task SetBucketPolicy(AWSS3Bucket bucket, string policy);
```

| Parameter | Type | Description |
|---|---|---|
| `bucket` | `AWSS3Bucket` | Target bucket |
| `policy` | `string` | Policy document (JSON) |

### DeleteBucketPolicy

Deletes the bucket policy.

```csharp
Task DeleteBucketPolicy(AWSS3Bucket bucket);
```

### ConfigurePublicAccess

Configures public access block settings.

```csharp
Task ConfigurePublicAccess(AWSS3Bucket bucket,
    bool isBlockPublicAcls = true,
    bool isIgnorePublicAcls = true,
    bool isBlockPublicPolicy = true,
    bool isRestrictPublicBuckets = true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket` | `AWSS3Bucket` | — | Target bucket |
| `isBlockPublicAcls` | `bool` | `true` | Block public ACLs |
| `isIgnorePublicAcls` | `bool` | `true` | Ignore public ACLs |
| `isBlockPublicPolicy` | `bool` | `true` | Block public bucket policies |
| `isRestrictPublicBuckets` | `bool` | `true` | Restrict public bucket access |

### ConfigureLogging

Configures server access logging.

```csharp
Task ConfigureLogging(AWSS3Bucket bucket,
    bool isEnableLogging, string targetBucketName, string targetPrefix);
```

| Parameter | Type | Description |
|---|---|---|
| `bucket` | `AWSS3Bucket` | Target bucket |
| `isEnableLogging` | `bool` | Enable or disable logging |
| `targetBucketName` | `string` | Bucket to store access logs |
| `targetPrefix` | `string` | Prefix for log object keys |

---

## S3 Objects

Sub-service: `IAWSS3ObjectService` — obtained via `aws.S3ObjectService(clientProvider)`.

### GetObject

Retrieves an S3 object's metadata.

```csharp
Task<AWSS3Object> GetObject(AWSS3Bucket bucket, string objectKey, bool isIncludeVersions = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket` | `AWSS3Bucket` | — | Parent bucket |
| `objectKey` | `string` | — | Object key |
| `isIncludeVersions` | `bool` | `false` | Include version history |

### UploadSingleObject

Uploads a single file to S3.

```csharp
Task<AWSS3Object> UploadSingleObject(
    AWSS3Bucket bucket,
    string s3ObjectKey,
    string filePath,
    string contentType = default,
    S3ObjectStorageType storageClass = default,
    DataTable tags = default,
    List<AWSS3ObjectACL> permissions = default,
    AWSEncryptionMethod encryptionMethod = default,
    string encryptionKey = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket` | `AWSS3Bucket` | — | Target bucket |
| `s3ObjectKey` | `string` | — | Destination key in S3 |
| `filePath` | `string` | — | Local file path to upload |
| `contentType` | `string` | `null` | MIME content type |
| `storageClass` | `S3ObjectStorageType` | `Standard` | Storage class |
| `tags` | `DataTable` | `null` | Object tags |
| `permissions` | `List<AWSS3ObjectACL>` | `null` | ACL permissions |
| `encryptionMethod` | `AWSEncryptionMethod` | `None` | Encryption method |
| `encryptionKey` | `string` | `null` | KMS key |

### UploadMultipleObjects

Uploads all files from a local folder to S3.

```csharp
Task UploadMultipleObjects(
    AWSS3Bucket bucket,
    string folderPath,
    bool isIncludeSubfolders = false,
    S3ObjectStorageType storageClass = default,
    DataTable tags = null,
    AWSEncryptionMethod encrytionType = default,
    string encryptionKey = default,
    string keyPrefix = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket` | `AWSS3Bucket` | — | Target bucket |
| `folderPath` | `string` | — | Local folder path |
| `isIncludeSubfolders` | `bool` | `false` | Include subfolders |
| `storageClass` | `S3ObjectStorageType` | `Standard` | Storage class |
| `tags` | `DataTable` | `null` | Object tags |
| `encrytionType` | `AWSEncryptionMethod` | `None` | Encryption method |
| `encryptionKey` | `string` | `null` | KMS key |
| `keyPrefix` | `string` | `null` | Key prefix in S3 |

### DownloadSingleObject

Downloads an S3 object to a local file.

```csharp
Task<ILocalResource> DownloadSingleObject(
    AWSS3Object s3Object,
    string destinationFolder,
    string versionId = default,
    string destinationFile = default,
    bool isOverWrite = true,
    bool createSubFolderStructure = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `s3Object` | `AWSS3Object` | — | Object to download |
| `destinationFolder` | `string` | — | Local destination folder |
| `versionId` | `string` | `null` | Specific version to download |
| `destinationFile` | `string` | `null` | Override destination filename |
| `isOverWrite` | `bool` | `true` | Overwrite existing file |
| `createSubFolderStructure` | `bool` | `false` | Recreate S3 folder structure locally |

**Returns:** `ILocalResource` — reference to the downloaded file.

### CopyObject

Copies an S3 object to another bucket/key.

```csharp
Task<AWSS3Object> CopyObject(AWSS3Object s3Object, string versionId,
    AWSS3Bucket destinationBucket, string destinationKey);
```

| Parameter | Type | Description |
|---|---|---|
| `s3Object` | `AWSS3Object` | Source object |
| `versionId` | `string` | Source version ID (or `null` for latest) |
| `destinationBucket` | `AWSS3Bucket` | Destination bucket |
| `destinationKey` | `string` | Destination object key |

### DeleteSingleObject

Deletes a single S3 object.

```csharp
Task DeleteSingleObject(AWSS3Object s3Object, string versionId = default);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `s3Object` | `AWSS3Object` | — | Object to delete |
| `versionId` | `string` | `null` | Specific version to delete |

### DeleteMultipleObjects

Deletes multiple S3 objects by key-version pairs.

```csharp
Task DeleteMultipleObjects(AWSS3Bucket bucket, DataTable keyVersions);
```

| Parameter | Type | Description |
|---|---|---|
| `bucket` | `AWSS3Bucket` | Target bucket |
| `keyVersions` | `DataTable` | Table with key-version pairs to delete |

### GetObjectACL

Gets the ACL for an S3 object.

```csharp
Task<AWSS3ObjectACL[]> GetObjectACL(AWSS3Object s3Object);
```

### SetObjectACL

Sets the ACL for an S3 object.

```csharp
Task SetObjectACL(AWSS3Object s3Object, IList<AWSS3ObjectACL> grants);
```

| Parameter | Type | Description |
|---|---|---|
| `s3Object` | `AWSS3Object` | Target object |
| `grants` | `IList<AWSS3ObjectACL>` | ACL entries to set |

---

## IAM Users

Sub-service: `IAWSIAMUserService` — obtained via `aws.IAMUserService(clientProvider)`.

### GetUser

Retrieves an IAM user.

```csharp
Task<AWSIAMUser> GetUser(string userName);
```

### CreateUser

Creates an IAM user. Returns a tuple of `(AWSIAMUser, accessKeyId, secretAccessKey)`.

```csharp
Task<(AWSIAMUser, string, string)> CreateUser(
    string userName,
    string path,
    string permissionsBoundaryArn,
    DataTable tags,
    string password,
    bool forcePasswordChange,
    bool generateAwsAccessKeys);
```

| Parameter | Type | Description |
|---|---|---|
| `userName` | `string` | User name |
| `path` | `string` | IAM path |
| `permissionsBoundaryArn` | `string` | Permissions boundary policy ARN |
| `tags` | `DataTable` | User tags |
| `password` | `string` | Login password |
| `forcePasswordChange` | `bool` | Require password change at first login |
| `generateAwsAccessKeys` | `bool` | Generate access key and secret key |

**Returns:** `(AWSIAMUser user, string accessKeyId, string secretAccessKey)` — the `accessKeyId` and `secretAccessKey` are only populated when `generateAwsAccessKeys` is `true`.

### UpdateUser

Updates an IAM user.

```csharp
Task<AWSIAMUser> UpdateUser(
    string userName, string newName, string newPath,
    bool deletePermissionsBoundary, string newPermissionsBoundaryArn,
    string[] tagsToRemove, DataTable tagsToAdd);
```

| Parameter | Type | Description |
|---|---|---|
| `userName` | `string` | Current user name |
| `newName` | `string` | New user name |
| `newPath` | `string` | New IAM path |
| `deletePermissionsBoundary` | `bool` | Remove the permissions boundary |
| `newPermissionsBoundaryArn` | `string` | New permissions boundary ARN |
| `tagsToRemove` | `string[]` | Tag keys to remove |
| `tagsToAdd` | `DataTable` | Tags to add |

### DeleteUser

Deletes an IAM user.

```csharp
Task DeleteUser(string userName, bool removeAllAttachedEntities);
```

| Parameter | Type | Description |
|---|---|---|
| `userName` | `string` | User name |
| `removeAllAttachedEntities` | `bool` | Remove all attached policies, access keys, etc. before deleting |

### ChangeUserPassword

Changes an IAM user's password.

```csharp
Task ChangeUserPassword(string userName, string password, bool forcePasswordChange = false);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `userName` | `string` | — | User name |
| `password` | `string` | — | New password |
| `forcePasswordChange` | `bool` | `false` | Require change at next login |

---

## IAM Groups

Sub-service: `IAWSIAMGroupService` — obtained via `aws.IAMGroupService(clientProvider)`.

### GetGroup

Retrieves an IAM group.

```csharp
Task<AWSIAMGroup> GetGroup(string groupName);
```

### CreateGroup

Creates an IAM group.

```csharp
Task<AWSIAMGroup> CreateGroup(string groupName, string path);
```

| Parameter | Type | Description |
|---|---|---|
| `groupName` | `string` | Group name |
| `path` | `string` | IAM path |

### UpdateGroup

Updates an IAM group's name or path.

```csharp
Task<AWSIAMGroup> UpdateGroup(string groupName, string newName, string newPath);
```

| Parameter | Type | Description |
|---|---|---|
| `groupName` | `string` | Current group name |
| `newName` | `string` | New group name |
| `newPath` | `string` | New IAM path |

### DeleteGroup

Deletes an IAM group.

```csharp
Task DeleteGroup(string groupName, bool removeAllAttachedEntities);
```

| Parameter | Type | Description |
|---|---|---|
| `groupName` | `string` | Group name |
| `removeAllAttachedEntities` | `bool` | Remove all attached policies and users before deleting |

### GetUsersInGroup

Lists users in a group. Returns AWS SDK `User` objects.

```csharp
Task<List<User>> GetUsersInGroup(string groupName);
```

### AddUserToGroup

Adds a user to a group.

```csharp
Task AddUserToGroup(string groupName, string userName);
```

### RemoveUserFromGroup

Removes a user from a group.

```csharp
Task RemoveUserFromGroup(string groupName, string userName);
```

---

## IAM Roles

Sub-service: `IAWSIAMRoleService` — obtained via `aws.IAMRoleService(clientProvider)`.

### GetRole

Retrieves an IAM role.

```csharp
Task<AWSIAMRole> GetRole(string roleName);
```

### CreateRole

Creates an IAM role.

```csharp
Task<AWSIAMRole> CreateRole(
    string policyDocument, string description, int? sessionDuration,
    string path, string permissionBoundary, string roleName, DataTable tags);
```

| Parameter | Type | Description |
|---|---|---|
| `policyDocument` | `string` | Trust policy document (JSON) |
| `description` | `string` | Role description |
| `sessionDuration` | `int?` | Maximum session duration in seconds |
| `path` | `string` | IAM path |
| `permissionBoundary` | `string` | Permissions boundary policy ARN |
| `roleName` | `string` | Role name |
| `tags` | `DataTable` | Role tags |

### UpdateRole

Updates an IAM role.

```csharp
Task<AWSIAMRole> UpdateRole(
    string roleName, string newDescription, int newMaxSessionDuration,
    bool deletePermissionsBoundary, string newPermissionsBoundaryArn,
    string[] tagsToRemove, DataTable tagsToAdd);
```

| Parameter | Type | Description |
|---|---|---|
| `roleName` | `string` | Role name |
| `newDescription` | `string` | New description |
| `newMaxSessionDuration` | `int` | New max session duration in seconds |
| `deletePermissionsBoundary` | `bool` | Remove permissions boundary |
| `newPermissionsBoundaryArn` | `string` | New permissions boundary ARN |
| `tagsToRemove` | `string[]` | Tag keys to remove |
| `tagsToAdd` | `DataTable` | Tags to add |

### DeleteRole

Deletes an IAM role.

```csharp
Task DeleteRole(string roleName, bool removeAllAttachedEntities, bool deleteDefaultInstanceProfile);
```

| Parameter | Type | Description |
|---|---|---|
| `roleName` | `string` | Role name |
| `removeAllAttachedEntities` | `bool` | Remove attached policies before deleting |
| `deleteDefaultInstanceProfile` | `bool` | Delete the default instance profile |

### AddRoleToInstanceProfile

Adds a role to an instance profile.

```csharp
Task AddRoleToInstanceProfile(string roleName, string instanceProfileName, bool removeExistingRole);
```

| Parameter | Type | Description |
|---|---|---|
| `roleName` | `string` | Role name |
| `instanceProfileName` | `string` | Instance profile name |
| `removeExistingRole` | `bool` | Remove the existing role from the profile first |

### RemoveRoleFromInstanceProfile

Removes a role from an instance profile.

```csharp
Task RemoveRoleFromInstanceProfile(string roleName, string instanceProfileName);
```

---

## IAM Policies

Sub-service: `IAWSIAMPolicyService` — obtained via `aws.IAMPolicyService(clientProvider)`.

### GetPolicy

Retrieves a managed policy by ARN.

```csharp
Task<AWSIAMManagedPolicy> GetPolicy(string policyArn, bool includeVersions);
```

| Parameter | Type | Description |
|---|---|---|
| `policyArn` | `string` | Policy ARN |
| `includeVersions` | `bool` | Include policy version history |

### GetPolicyVersions

Lists all versions of a managed policy.

```csharp
Task<List<AWSIAMPolicyVersion>> GetPolicyVersions(string policyArn);
```

### CreatePolicy

Creates a new managed policy.

```csharp
Task<AWSIAMManagedPolicy> CreatePolicy(
    string name, string document, string description, string path, DataTable tags);
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `string` | Policy name |
| `document` | `string` | Policy document (JSON) |
| `description` | `string` | Policy description |
| `path` | `string` | IAM path |
| `tags` | `DataTable` | Policy tags |

### UpdatePolicy

Updates a managed policy (versions, tags).

```csharp
Task<AWSIAMManagedPolicy> UpdatePolicy(
    string policyArn,
    string[] tagsToRemove,
    DataTable tagsToAdd,
    string newPolicyVersionDocument,
    string versionToRemove,
    string versionToSetAsDefault);
```

| Parameter | Type | Description |
|---|---|---|
| `policyArn` | `string` | Policy ARN |
| `tagsToRemove` | `string[]` | Tag keys to remove |
| `tagsToAdd` | `DataTable` | Tags to add |
| `newPolicyVersionDocument` | `string` | New policy version document (JSON) |
| `versionToRemove` | `string` | Version ID to delete |
| `versionToSetAsDefault` | `string` | Version ID to set as default |

### DeletePolicy

Deletes a managed policy.

```csharp
Task DeletePolicy(string policyArn, bool isDetachPolicyFromIAMIdentities);
```

| Parameter | Type | Description |
|---|---|---|
| `policyArn` | `string` | Policy ARN |
| `isDetachPolicyFromIAMIdentities` | `bool` | Detach from all identities before deleting |

### GetManagedPolicies

Lists managed policies attached to an identity.

```csharp
Task<AWSIAMManagedPolicyBasic[]> GetManagedPolicies(
    string policyPathPrefix, string identityName, IAMIdentityType identityType);
```

| Parameter | Type | Description |
|---|---|---|
| `policyPathPrefix` | `string` | Filter by policy path prefix |
| `identityName` | `string` | IAM identity name (user, group, or role) |
| `identityType` | `IAMIdentityType` | Identity type (`User`, `Group`, or `Role`) |

### GetInlinePolicies

Lists inline policies for an identity.

```csharp
Task<AWSIAMInlinePolicy[]> GetInlinePolicies(string identityName, IAMIdentityType identityType);
```

| Parameter | Type | Description |
|---|---|---|
| `identityName` | `string` | IAM identity name |
| `identityType` | `IAMIdentityType` | Identity type |

### AttachDetachManagedPolicy

Attaches or detaches a managed policy from an identity.

```csharp
Task AttachDetachManagedPolicy(
    ManagedPolicyAction action, string identityName,
    IAMIdentityType identityType, string policyArn);
```

| Parameter | Type | Description |
|---|---|---|
| `action` | `ManagedPolicyAction` | `Attach` or `Detach` |
| `identityName` | `string` | IAM identity name |
| `identityType` | `IAMIdentityType` | Identity type |
| `policyArn` | `string` | Policy ARN |

### AddRemoveInlinePolicy

Adds or removes an inline policy on an identity.

```csharp
Task AddRemoveInlinePolicy(
    InlinePolicyAction action, string identityName,
    IAMIdentityType identityType, string policyName, string policyDocument);
```

| Parameter | Type | Description |
|---|---|---|
| `action` | `InlinePolicyAction` | `Add` or `Remove` |
| `identityName` | `string` | IAM identity name |
| `identityType` | `IAMIdentityType` | Identity type |
| `policyName` | `string` | Inline policy name |
| `policyDocument` | `string` | Policy document JSON (required for `Add`) |

### GetEntitiesAttachedToPolicy

Lists entities (groups, roles, users) attached to a policy.

```csharp
Task<(List<PolicyGroup>, List<PolicyRole>, List<PolicyUser>)> GetEntitiesAttachedToPolicy(
    string policyArn, IAMIdentityTypeExtended identityType,
    string pathPrefix, IAMPolicyUsage policyUsage);
```

| Parameter | Type | Description |
|---|---|---|
| `policyArn` | `string` | Policy ARN |
| `identityType` | `IAMIdentityTypeExtended` | Filter by identity type (`All`, `Group`, `Role`, `User`) |
| `pathPrefix` | `string` | Filter by IAM path prefix |
| `policyUsage` | `IAMPolicyUsage` | Filter by usage type |

**Returns:** Tuple of `(List<PolicyGroup>, List<PolicyRole>, List<PolicyUser>)` — AWS SDK types.

---

## EBS Volumes

Sub-service: `IAWSStorageVolumeService` — obtained via `aws.StorageVolumeService(clientProvider)`.

### CreateVolumeAsync

Creates a new EBS volume.

```csharp
Task<AWSEBSVolume> CreateVolumeAsync(
    string availabilityZone, string volumeType, int sizeInGBs,
    int iops = 0, int throughput = 0, string snapshotId = null,
    bool enableEncryption = false, DataTable tags = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `availabilityZone` | `string` | — | Availability zone |
| `volumeType` | `string` | — | Volume type (e.g., "gp3", "io1") |
| `sizeInGBs` | `int` | — | Volume size in GB |
| `iops` | `int` | `0` | Provisioned IOPS |
| `throughput` | `int` | `0` | Provisioned throughput |
| `snapshotId` | `string` | `null` | Source snapshot ID |
| `enableEncryption` | `bool` | `false` | Enable encryption |
| `tags` | `DataTable` | `null` | Volume tags |

### GetVolumeByIdAsync

Retrieves an EBS volume by ID.

```csharp
Task<AWSEBSVolume> GetVolumeByIdAsync(string volumeId);
```

### GetVolumeListAsync

Lists EBS volumes in an availability zone.

```csharp
Task<AWSEBSVolume[]> GetVolumeListAsync(string availabilityZone);
```

### GetInstanceVolumesAsync

Lists EBS volumes attached to an EC2 instance.

```csharp
Task<AWSEBSVolume[]> GetInstanceVolumesAsync(AWSEc2Instance instance);
```

### DeleteVolumeAsync

Deletes an EBS volume.

```csharp
Task DeleteVolumeAsync(AWSEBSVolume volume);
```

### AttachVolumeToInstanceAsync

Attaches an EBS volume to an EC2 instance.

```csharp
Task AttachVolumeToInstanceAsync(AWSEBSVolume volume, AWSEc2Instance instance, string deviceName);
```

| Parameter | Type | Description |
|---|---|---|
| `volume` | `AWSEBSVolume` | Volume to attach |
| `instance` | `AWSEc2Instance` | Target instance |
| `deviceName` | `string` | Device name (e.g., "/dev/sdf") |
