# Google Cloud Examples

Examples using the `gcp` service from `UiPath.GoogleCloud.Activities` package.

**Required package:** `"UiPath.GoogleCloud.Activities": "[1.0.0]"`

---

## Bucket Operations

```csharp
namespace MyProject
{
    public class BucketWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var bucketService = gcp.BucketService(clientProvider);

            // Get a bucket
            GCPBucket bucket = await bucketService.GetBucket("my-storage-bucket");
            Log($"Bucket: {bucket.Name}");

            // Create a new bucket
            GCPBucket newBucket = await bucketService.CreateBucket(new BucketCreateParameters
            {
                // Set bucket creation parameters (name, location, storage class, etc.)
            });
            Log($"Created bucket: {newBucket.Name}");

            // Update a bucket
            await bucketService.UpdateBucket(new BucketUpdateParameters
            {
                // Set bucket update parameters
            });
            Log("Bucket updated");

            // Delete a bucket and all its objects
            await bucketService.DeleteBucket(bucket, isDeleteObjects: true);
            Log("Bucket deleted with all objects");
        }
    }
}
```

## Upload, Download, and Copy Objects

```csharp
using System.Data;

namespace MyProject
{
    public class ObjectStorageWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var bucketService = gcp.BucketService(clientProvider);
            var objectService = gcp.ObjectService(clientProvider);

            GCPBucket bucket = await bucketService.GetBucket("my-data-bucket");

            // Upload a file
            var metadata = new DataTable();
            metadata.Columns.Add("Key", typeof(string));
            metadata.Columns.Add("Value", typeof(string));
            metadata.Rows.Add("department", "finance");

            GCPObject uploaded = await objectService.UploadObject(
                bucket,
                objectName: "reports/monthly-report.pdf",
                fileToUpload: @"C:\Output\monthly-report.pdf",
                contentType: "application/pdf",
                storage: Storage.Standard,
                metadata: metadata,
                predefinedAcl: "private",
                customerManagedKey: null);
            Log($"Uploaded: {uploaded.Name}");

            // Get object info
            GCPObject obj = await objectService.GetObject(bucket, "reports/monthly-report.pdf", generation: null);
            Log($"Object: {obj.Name}");

            // Download an object
            ILocalResource downloaded = await objectService.DownloadObject(
                obj, generation: obj.Generation,
                folder: @"C:\Downloads",
                filename: "monthly-report.pdf",
                overwrite: true);
            Log("Object downloaded");

            // Copy to another bucket
            GCPBucket archiveBucket = await bucketService.GetBucket("my-archive-bucket");
            GCPObject copied = await objectService.CopyObject(
                obj, obj.Generation,
                archiveBucket, "archived/monthly-report.pdf",
                predefinedACL: "private");
            Log($"Copied to archive: {copied.Name}");

            // Delete the original object
            await objectService.DeleteObject(obj, generation: null);
            Log("Original object deleted");
        }
    }
}
```

## Compute Engine Instance Lifecycle

```csharp
namespace MyProject
{
    public class InstanceLifecycleWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var instanceService = gcp.InstanceService(clientProvider);

            // Create a new instance
            GCPInstance instance = await instanceService.CreateInstance(new InstanceCreationParameters
            {
                // Set instance creation parameters (name, zone, machine type, image, etc.)
            });
            Log($"Created instance: {instance.Name}");

            // Get an existing instance
            GCPInstance existing = await instanceService.GetInstance(
                "my-worker-vm", "my-gcp-project", "us-central1-a");
            Log($"Instance: {existing.Name}");

            // Start the instance
            await instanceService.StartInstance(existing, waitForCompletion: true);
            Log("Instance started");

            // Stop the instance
            await instanceService.StopInstance(existing, waitForCompletion: true);
            Log("Instance stopped");

            // Reset (hard reboot) the instance
            await instanceService.ResetInstance(existing, waitForCompletion: true);
            Log("Instance reset");

            // Delete the instance
            await instanceService.DeleteInstance(existing, waitForCompletion: true);
            Log("Instance deleted");
        }
    }
}
```

## Create Instance from Template

```csharp
namespace MyProject
{
    public class InstanceFromTemplateWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var instanceService = gcp.InstanceService(clientProvider);

            // Create an instance from a predefined template
            GCPInstance instance = await instanceService.CreateInstance(
                new InstanceCreationParameters
                {
                    // Override specific parameters from the template
                },
                instanceTemplate: "my-worker-template");

            Log($"Created instance from template: {instance.Name}");
        }
    }
}
```

## Run Script on Instance

```csharp
namespace MyProject
{
    public class RunScriptWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var instanceService = gcp.InstanceService(clientProvider);

            GCPInstance instance = await instanceService.GetInstance(
                "my-worker-vm", "my-gcp-project", "us-central1-a");

            // Run a script on the instance
            string output = await instanceService.RunScriptOnInstance(
                instance,
                script: "#!/bin/bash\necho 'Hello from GCP'\nhostname\ndate",
                scriptKey: "startup-script",
                consoleTimeout: 120);

            Log($"Script output: {output}");
        }
    }
}
```

## Configure UiPath Robot on Instance

```csharp
namespace MyProject
{
    public class ConfigureRobotWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var instanceService = gcp.InstanceService(clientProvider);

            GCPInstance instance = await instanceService.GetInstance(
                "robot-vm", "my-gcp-project", "us-central1-a");

            // Configure robot using Orchestrator URL and machine key
            await instanceService.ConfigureRobot(
                instance,
                orchestratorURL: "https://cloud.uipath.com/org/tenant/orchestrator_",
                machineKey: "my-machine-key");
            Log("Robot configured with Orchestrator URL");

            // Alternative: configure using connection string
            await instanceService.ConfigureRobot(
                instance,
                connectionString: "my-connection-string");
            Log("Robot configured with connection string");
        }
    }
}
```

## Secret Manager — Retrieve Secrets

```csharp
using System.Security;

namespace MyProject
{
    public class SecretManagerWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var secretService = gcp.SecretDataService(clientProvider);

            // Get the latest version of a secret
            (string name, SecureString value) = await secretService.GetSecretData(
                projectId: "my-gcp-project",
                secretName: "db-connection-string",
                secretVersion: "latest");
            Log($"Retrieved secret: {name}");

            // Get a specific version
            (string name2, SecureString value2) = await secretService.GetSecretData(
                projectId: "my-gcp-project",
                secretName: "api-key",
                secretVersion: "3");
            Log($"Retrieved secret version 3: {name2}");
        }
    }
}
```

## IAM Role Management

```csharp
namespace MyProject
{
    public class RoleManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var roleService = gcp.RoleService(clientProvider);

            // Get an existing role
            GCPIAMRole role = await roleService.GetRole(
                "myCustomRole", RoleType.Project, "my-gcp-project");
            Log($"Role: {role.Name}");

            // Create a custom role
            GCPIAMRole newRole = await roleService.CreateRole(
                roleName: "storageViewer",
                title: "Storage Viewer",
                description: "Can view storage buckets and objects",
                permissions: new[] { "storage.buckets.list", "storage.objects.list", "storage.objects.get" },
                launchStage: RoleLaunchStage.GA,
                parentId: "my-gcp-project",
                roleType: RoleType.Project);
            Log($"Created role: {newRole.Name}");

            // Update a role — add and remove permissions
            GCPIAMRole updated = await roleService.UpdateRole(
                newRole,
                newDescription: "Can view and create storage objects",
                newLaunchStage: null,
                newTitle: "Storage Viewer+",
                permissionsToRemove: null,
                permissionsToAdd: new[] { "storage.objects.create" });
            Log($"Updated role: {updated.Name}");

            // Delete a role (soft-delete)
            await roleService.DeleteRole(updated);
            Log("Role deleted");

            // Restore a deleted role
            await roleService.UndeleteRole(updated);
            Log("Role restored");
        }
    }
}
```

## IAM Policy Operations

```csharp
namespace MyProject
{
    public class PolicyWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var policyService = gcp.PolicyService(clientProvider);

            // Get IAM policy for a project
            GCPIAMPolicy policy = await policyService.GetIAMPolicy(
                resourceType: ResourceType.Project,
                fullResourceName: "projects/my-gcp-project",
                policyVersion: null);
            Log("Retrieved IAM policy");

            // Set IAM policy
            await policyService.SetIAMPolicy(
                resourceType: ResourceType.Project,
                fullResourceName: "projects/my-gcp-project",
                policyData: null,
                policy: policy);
            Log("IAM policy updated");
        }
    }
}
```

## Get Project Info

```csharp
namespace MyProject
{
    public class ProjectInfoWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IGCPClientProvider clientProvider)
        {
            var projectService = gcp.ProjectService(clientProvider);

            GCPProject project = await projectService.GetProject("my-gcp-project");
            Log($"Project: {project.Name}, ID: {project.ProjectId}");
        }
    }
}
```
