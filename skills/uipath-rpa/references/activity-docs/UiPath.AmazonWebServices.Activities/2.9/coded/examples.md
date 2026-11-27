# Amazon Web Services Examples

Examples using the `aws` service from `UiPath.AmazonWebServices.Activities` package.

**Required package:** `"UiPath.AmazonWebServices.Activities": "[1.4.1]"`

---

## EC2 — Create, Start, and Stop an Instance

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class EC2LifecycleWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSEC2InstanceService ec2 = aws.EC2InstanceService(clientProvider);

            // Create a new EC2 instance
            AWSEc2Instance instance = await ec2.CreateEC2Instance(
                instanceName: "MyAutomationVM",
                zone: "us-east-1a",
                instanceType: "t2.micro",
                imageId: "ami-0abc123def456",
                isWaitForCompletion: true);

            Log($"Created instance: {instance.InstanceId}, State: {instance.State}");

            // Stop the instance
            await ec2.StopInstance(instance, isHibernate: false, isForce: false, isWaitForCompletion: true);
            Log("Instance stopped.");

            // Start the instance again
            await ec2.StartInstance(instance, isWaitForCompletion: true);
            Log("Instance started.");
        }
    }
}
```

## EC2 — List Instances and Run PowerShell

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class EC2ListAndCommandWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSEC2InstanceService ec2 = aws.EC2InstanceService(clientProvider);

            // List all running instances
            AWSEc2Instance[] runningInstances = await ec2.GetInstanceList(
                state: Ec2InstanceState.Running);

            foreach (AWSEc2Instance inst in runningInstances)
            {
                Log($"Instance: {inst.InstanceId} - {inst.Name} ({inst.InstanceType})");
            }

            // Run a PowerShell command on the first instance
            if (runningInstances.Length > 0)
            {
                AWSPSCommandOutput output = await ec2.RunPowerShellCommand(
                    runningInstances[0],
                    commands: "Get-Process | Select-Object -First 5",
                    workingDirectory: "C:\\",
                    comment: "List top 5 processes");

                Log($"Command status: {output.Status}");
                Log($"Output: {output.StandardOutputContent}");
            }
        }
    }
}
```

## EC2 — Create Instance from Launch Template

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class EC2TemplateWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSEC2InstanceService ec2 = aws.EC2InstanceService(clientProvider);

            AWSEc2Instance instance = await ec2.CreateEc2InstanceByTemplate(
                instanceName: "TemplateBasedVM",
                templateId: "lt-0abc123def456",
                waitForCompletion: true);

            Log($"Created from template: {instance.InstanceId}");
        }
    }
}
```

## S3 — Create Bucket and Upload File

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class S3UploadWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSS3BucketService s3Buckets = aws.S3BucketService(clientProvider);
            IAWSS3ObjectService s3Objects = aws.S3ObjectService(clientProvider);

            // Create a bucket with versioning
            AWSS3Bucket bucket = await s3Buckets.CreateBucket(
                bucketName: "my-automation-bucket",
                isVersionsEnabled: true,
                encryptionType: AWSEncryptionMethod.AES_256);

            Log($"Created bucket: {bucket.Name}");

            // Upload a single file
            AWSS3Object uploaded = await s3Objects.UploadSingleObject(
                bucket: bucket,
                s3ObjectKey: "reports/monthly-report.pdf",
                filePath: @"C:\Output\report.pdf",
                contentType: "application/pdf",
                storageClass: S3ObjectStorageType.Standard);

            Log($"Uploaded: {uploaded.KeyName} to {uploaded.BucketName}");
        }
    }
}
```

## S3 — Download and Copy Objects

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;
using UiPath.Platform.ResourceHandling;

namespace MyProject
{
    public class S3DownloadWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSS3BucketService s3Buckets = aws.S3BucketService(clientProvider);
            IAWSS3ObjectService s3Objects = aws.S3ObjectService(clientProvider);

            AWSS3Bucket bucket = await s3Buckets.GetBucket("my-automation-bucket");

            // Get object metadata
            AWSS3Object obj = await s3Objects.GetObject(bucket, "reports/monthly-report.pdf");
            Log($"Object size: {obj.Size} bytes, Last modified: {obj.LastModified}");

            // Download to local folder
            ILocalResource downloaded = await s3Objects.DownloadSingleObject(
                obj, @"C:\Downloads", isOverWrite: true);

            // Copy to another bucket
            AWSS3Bucket archiveBucket = await s3Buckets.GetBucket("my-archive-bucket");
            AWSS3Object copied = await s3Objects.CopyObject(
                obj, versionId: null, archiveBucket, "archive/monthly-report.pdf");

            Log($"Copied to: {copied.Path}");
        }
    }
}
```

## S3 — Manage Bucket Policies and Public Access

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class S3BucketPolicyWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSS3BucketService s3Buckets = aws.S3BucketService(clientProvider);

            AWSS3Bucket bucket = await s3Buckets.GetBucket("my-automation-bucket", includeDetails: true);
            AWSS3BucketDetails details = bucket.GetDetails();
            Log($"Versioning: {details.VersioningEnabled}, Encryption: {details.DefaultEncryption}");

            // Block all public access
            await s3Buckets.ConfigurePublicAccess(bucket,
                isBlockPublicAcls: true,
                isIgnorePublicAcls: true,
                isBlockPublicPolicy: true,
                isRestrictPublicBuckets: true);

            // Enable access logging
            await s3Buckets.ConfigureLogging(bucket,
                isEnableLogging: true,
                targetBucketName: "my-logs-bucket",
                targetPrefix: "access-logs/");

            Log("Bucket security configured.");
        }
    }
}
```

## IAM — Create User and Manage Groups

```csharp
using System.Collections.Generic;
using Amazon.IdentityManagement.Model;
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class IAMUserGroupWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSIAMUserService iamUsers = aws.IAMUserService(clientProvider);
            IAWSIAMGroupService iamGroups = aws.IAMGroupService(clientProvider);

            // Create a new user with access keys
            (AWSIAMUser user, string accessKeyId, string secretKey) = await iamUsers.CreateUser(
                userName: "automation-user",
                path: "/automation/",
                permissionsBoundaryArn: null,
                tags: null,
                password: "TempP@ss123!",
                forcePasswordChange: true,
                generateAwsAccessKeys: true);

            Log($"Created user: {user.Name}, ARN: {user.Arn}");
            Log($"Access Key ID: {accessKeyId}");

            // Create a group and add the user
            AWSIAMGroup group = await iamGroups.CreateGroup("AutomationTeam", "/automation/");
            await iamGroups.AddUserToGroup("AutomationTeam", "automation-user");

            // List users in the group
            List<User> groupUsers = await iamGroups.GetUsersInGroup("AutomationTeam");
            foreach (User u in groupUsers)
            {
                Log($"Group member: {u.UserName}");
            }
        }
    }
}
```

## IAM — Create Role and Attach Policy

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class IAMRolePolicyWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSIAMRoleService iamRoles = aws.IAMRoleService(clientProvider);
            IAWSIAMPolicyService iamPolicies = aws.IAMPolicyService(clientProvider);

            // Create a role with a trust policy
            string trustPolicy = @"{
                ""Version"": ""2012-10-17"",
                ""Statement"": [{
                    ""Effect"": ""Allow"",
                    ""Principal"": {""Service"": ""ec2.amazonaws.com""},
                    ""Action"": ""sts:AssumeRole""
                }]
            }";

            AWSIAMRole role = await iamRoles.CreateRole(
                policyDocument: trustPolicy,
                description: "Role for EC2 automation",
                sessionDuration: 3600,
                path: "/automation/",
                permissionBoundary: null,
                roleName: "AutomationEC2Role",
                tags: null);

            Log($"Created role: {role.Name}, ARN: {role.Arn}");

            // Attach a managed policy to the role
            await iamPolicies.AttachDetachManagedPolicy(
                action: ManagedPolicyAction.Attach,
                identityName: "AutomationEC2Role",
                identityType: IAMIdentityType.Role,
                policyArn: "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess");

            // Add role to an instance profile
            await iamRoles.AddRoleToInstanceProfile(
                roleName: "AutomationEC2Role",
                instanceProfileName: "AutomationEC2Role",
                removeExistingRole: true);

            Log("Role configured with policy and instance profile.");
        }
    }
}
```

## IAM — Manage Inline Policies

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class IAMInlinePolicyWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSIAMPolicyService iamPolicies = aws.IAMPolicyService(clientProvider);

            // Add an inline policy to a user
            string policyDoc = @"{
                ""Version"": ""2012-10-17"",
                ""Statement"": [{
                    ""Effect"": ""Allow"",
                    ""Action"": ""s3:GetObject"",
                    ""Resource"": ""arn:aws:s3:::my-bucket/*""
                }]
            }";

            await iamPolicies.AddRemoveInlinePolicy(
                action: InlinePolicyAction.Add,
                identityName: "automation-user",
                identityType: IAMIdentityType.User,
                policyName: "S3ReadAccess",
                policyDocument: policyDoc);

            // List inline policies
            AWSIAMInlinePolicy[] inlinePolicies = await iamPolicies.GetInlinePolicies(
                "automation-user", IAMIdentityType.User);

            foreach (AWSIAMInlinePolicy policy in inlinePolicies)
            {
                Log($"Inline policy: {policy.Name}");
            }
        }
    }
}
```

## EBS — Create Volume and Attach to Instance

```csharp
using UiPath.AmazonWebServices.Activities.API;
using UiPath.AmazonWebServices.Models;

namespace MyProject
{
    public class EBSVolumeWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IAWSClientProvider clientProvider)
        {
            IAWSEC2InstanceService ec2 = aws.EC2InstanceService(clientProvider);
            IAWSStorageVolumeService volumes = aws.StorageVolumeService(clientProvider);

            // Get an existing instance
            AWSEc2Instance instance = await ec2.GetEC2Instance("i-0abc123def456");

            // Create a new EBS volume in the same AZ
            AWSEBSVolume volume = await volumes.CreateVolumeAsync(
                availabilityZone: instance.AvailabilityZone,
                volumeType: "gp3",
                sizeInGBs: 100,
                iops: 3000,
                throughput: 125,
                enableEncryption: true);

            Log($"Created volume: {volume.VolumeId}, State: {volume.VolumeState}");

            // Attach to the instance
            await volumes.AttachVolumeToInstanceAsync(volume, instance, "/dev/sdf");
            Log("Volume attached.");

            // List all volumes for the instance
            AWSEBSVolume[] instanceVolumes = await volumes.GetInstanceVolumesAsync(instance);
            foreach (AWSEBSVolume vol in instanceVolumes)
            {
                Log($"Volume: {vol.VolumeId}, Size: {vol.Size}GB, Type: {vol.VolumeType}");
            }
        }
    }
}
```
