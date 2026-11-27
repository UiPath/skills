# Azure Examples

Examples using the `azure` service from `UiPath.Azure.Activities` package.

**Required package:** `"UiPath.Azure.Activities": "[2.0.0]"`

---

## List and Manage Resource Groups

```csharp
using System.Data;

namespace MyProject
{
    public class ResourceGroupWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var rgService = azure.AzureResourceGroupService(clientProvider);

            // List all resource groups
            ResourceGroup[] groups = await rgService.GetResourceGroupList();
            foreach (var rg in groups)
            {
                Log($"Resource Group: {rg.Name}");
            }

            // Get a specific resource group
            ResourceGroup myGroup = await rgService.GetResourceGroup("my-resource-group");
            Log($"Found: {myGroup.Name}");

            // Create a new resource group with tags
            var tags = new DataTable();
            tags.Columns.Add("Key", typeof(string));
            tags.Columns.Add("Value", typeof(string));
            tags.Rows.Add("Environment", "Production");
            tags.Rows.Add("Team", "DevOps");

            ResourceGroup newGroup = await rgService.CreateResourceGroup(
                "new-resource-group", "eastus", tags);
            Log($"Created: {newGroup.Name}");
        }
    }
}
```

## Manage Virtual Machines

```csharp
using System.Data;
using System.Security;

namespace MyProject
{
    public class VirtualMachineWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var vmService = azure.AzureVirtualMachineService(clientProvider);

            // List all VMs in a resource group
            VirtualMachine[] vms = await vmService.GetListAsync(
                "my-resource-group",
                includeNetworkingDetails: true,
                filter: VmPowerStateFilter.All);

            foreach (var vm in vms)
            {
                Log($"VM: {vm.Name}");
            }

            // Get a specific VM
            VirtualMachine myVm = await vmService.GetAsync("my-resource-group", "my-vm");

            // Start the VM
            await vmService.StartAsync(myVm, waitForCompletion: true);
            Log("VM started");

            // Restart the VM
            await vmService.RestartAsync(myVm, waitForCompletion: true);
            Log("VM restarted");

            // Stop (deallocate) the VM, preserving public IP
            await vmService.StopAsync(myVm, reservePublicIpAddress: true, waitForCompletion: true);
            Log("VM stopped");
        }
    }
}
```

## Run a Script on a Virtual Machine

```csharp
using System.Data;

namespace MyProject
{
    public class RunScriptOnVmWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var vmService = azure.AzureVirtualMachineService(clientProvider);

            VirtualMachine vm = await vmService.GetAsync("my-resource-group", "my-vm");

            // Prepare script arguments
            var args = new DataTable();
            args.Columns.Add("Key", typeof(string));
            args.Columns.Add("Value", typeof(string));
            args.Rows.Add("ServiceName", "MyAppService");

            // Run a PowerShell script on the VM
            ScriptOutput[] output = await vmService.RunScriptAsync(
                vm,
                "Get-Service -Name $ServiceName | Select-Object Status, DisplayName",
                ScriptType.PowerShell,
                args);

            foreach (var line in output)
            {
                Log($"Script output: {line}");
            }
        }
    }
}
```

## Blob Storage Operations

```csharp
using System.Data;
using System.Security;

namespace MyProject
{
    public class BlobStorageWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(
            IAzureClientProvider clientProvider,
            string storageAccountName,
            string resourceGroupName,
            SecureString storageKey)
        {
            var blobService = azure.AzureBlobService;
            var storageService = azure.AzureStorageAccountService(clientProvider);

            // Get the storage account
            StorageAccount account = await storageService.GetStorageAccount(
                resourceGroupName, storageAccountName);

            // Get a blob container (create if it doesn't exist)
            BlobContainer container = await blobService.GetBlobContainerAsync(
                account, "my-container", storageKey, null,
                storageAccountName, resourceGroupName,
                createContainer: true);

            // List blobs in the container
            Blob[] blobs = await blobService.GetBlobsListAsync(container, maximumItems: 100, nameStartsWith: "data-");
            Log($"Found {blobs.Length} blobs starting with 'data-'");

            // Upload a file as a blob
            Blob uploaded = await blobService.UploadBlobFromFileAsync(
                container, "report.pdf", AzureBlobType.Block,
                uploadVhdFileAsPageBlob: false,
                path: @"C:\Output\report.pdf",
                contentType: "application/pdf",
                metadata: null,
                accessTier: AccessTierBlob.Hot);
            Log($"Uploaded: {uploaded.Name}");

            // Download a blob to disk
            Blob existingBlob = await blobService.GetBlobAsync(container, "report.pdf");
            ILocalResource downloaded = await blobService.DownloadBlobToDiskAsync(
                existingBlob, @"C:\Downloads", "report.pdf", overwrite: true);
            Log("Downloaded blob to disk");

            // Copy a blob to another container
            BlobContainer archiveContainer = await blobService.GetBlobContainerAsync(
                account, "archive", storageKey, null,
                storageAccountName, resourceGroupName,
                createContainer: true);

            await blobService.CopyBlobAsync(
                container, "report.pdf",
                archiveContainer, "archive-report.pdf",
                awaitForCompletion: true, timeout: 60000);
            Log("Blob copied to archive");

            // Delete a blob
            bool deleted = await blobService.DeleteBlobAsync(existingBlob, waitForCompletion: true);
            Log($"Blob deleted: {deleted}");
        }
    }
}
```

## Key Vault Secrets

```csharp
namespace MyProject
{
    public class KeyVaultWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var kvService = azure.AzureKeyVaultService(clientProvider, "my-key-vault");

            // Get all secrets
            SecretInfo[] allSecrets = await kvService.GetSecrets("my-key-vault");
            foreach (var secret in allSecrets)
            {
                Log($"Secret: {secret.Name}");
            }

            // Get specific secrets
            SecretInfo[] specificSecrets = await kvService.GetSecrets(
                "my-key-vault",
                new[] { "db-connection-string", "api-key" });

            foreach (var secret in specificSecrets)
            {
                Log($"Retrieved secret: {secret.Name}");
            }

            // Delete a secret
            await kvService.DeleteSecret("my-key-vault", "old-api-key");
            Log("Secret deleted");
        }
    }
}
```

## Table Storage Operations

```csharp
using System.Security;

namespace MyProject
{
    public class TableStorageWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(
            IAzureClientProvider clientProvider,
            SecureString storageKey)
        {
            var tableService = azure.AzureTableService;
            var storageService = azure.AzureStorageAccountService(clientProvider);

            StorageAccount account = await storageService.GetStorageAccount("my-rg", "mystorageaccount");

            // Create a table
            Table table = await tableService.CreateTableAsync(account, storageKey, "AuditLogs");
            Log($"Table created: {table.Name}");

            // List tables
            Table[] tables = await tableService.GetTableListAsync(
                account, storageKey, nameStartsWith: "Audit", maximumItems: 10);
            Log($"Found {tables.Length} tables");

            // Get a specific table
            Table auditTable = await tableService.GetTableAsync(account, storageKey, "AuditLogs");

            // Insert rows
            var rows = new Row[]
            {
                // Construct Row objects with partition key, row key, and properties
            };
            await tableService.InsertTableRowsAsync(auditTable, rows, TableInsertType.Insert);

            // Get a specific row
            Row row = await tableService.GetTableRowAsync(auditTable, "partition1", "row1");
            Log($"Retrieved row: {row.RowKey}");

            // Query rows with OData filter
            Row[] filtered = await tableService.GetRowsByFilterAsync(
                auditTable,
                maximumItems: 50,
                select: new[] { "Timestamp", "Action", "User" },
                oDataFilter: "Action eq 'Login' and Timestamp gt datetime'2025-01-01'");
            Log($"Found {filtered.Length} matching rows");

            // Delete rows
            await tableService.DeleteTableRowsAsync(auditTable, filtered);

            // Delete the table
            await tableService.DeleteTableAsync(auditTable);
        }
    }
}
```

## Network Security Group and Rules

```csharp
using System.Data;

namespace MyProject
{
    public class NsgWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var nsgService = azure.AzureNetworkSecurityGroupService(clientProvider);
            var rulesService = azure.AzureSecurityRulesService(clientProvider);

            // Create an NSG
            var tags = new DataTable();
            tags.Columns.Add("Key", typeof(string));
            tags.Columns.Add("Value", typeof(string));
            tags.Rows.Add("Purpose", "WebServer");

            NetworkSecurityGroup nsg = await nsgService.CreateNetworkSecurityGroup(
                "web-nsg", "my-resource-group", "eastus", tags);

            // Create an inbound rule to allow HTTPS
            NSGSecurityRule httpsRule = await rulesService.CreateSecurityRule(
                nsg,
                access: SecurityRuleAction.Allow,
                description: "Allow HTTPS inbound",
                direction: SecurityRuleDirection.Inbound,
                name: "Allow-HTTPS",
                priority: 100,
                protocol: SecurityRuleProtocol.Tcp,
                sourcePortRange: "*",
                sourceAddressPrefix: "*",
                destinationPortRange: "443",
                destinationAddressPrefix: "*");
            Log($"Created rule: {httpsRule.Name}");

            // Create a deny rule for all other inbound
            await rulesService.CreateSecurityRule(
                nsg,
                access: SecurityRuleAction.Deny,
                description: "Deny all other inbound",
                direction: SecurityRuleDirection.Inbound,
                name: "Deny-All-Inbound",
                priority: 4096,
                protocol: SecurityRuleProtocol.Any,
                sourcePortRange: "*",
                sourceAddressPrefix: "*",
                destinationPortRange: "*",
                destinationAddressPrefix: "*");

            // List all rules
            NSGSecurityRule[] rules = await rulesService.GetSecurityRuleList("web-nsg", "my-resource-group");
            foreach (var rule in rules)
            {
                Log($"Rule: {rule.Name}, Priority: {rule.Priority}");
            }
        }
    }
}
```

## Network Interface Management

```csharp
using System.Data;

namespace MyProject
{
    public class NetworkInterfaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var nicService = azure.AzureNetworkInterfaceService(clientProvider);

            // Create a network interface
            NetworkInterface nic = await nicService.CreateNetworkInterface(
                networkInterface: "my-nic",
                virtualNetworkName: "my-vnet",
                subnetName: "default",
                rgName: "my-resource-group",
                location: "eastus",
                keepExisting: false,
                privateIpAddress: "10.0.0.10",
                publicIpAddressName: "my-public-ip",
                nsgName: "web-nsg",
                tags: null,
                enableIpForwarding: false,
                enableAcceleratedNetworking: true);
            Log($"Created NIC: {nic.Name}");

            // Get a network interface
            NetworkInterface existingNic = await nicService.GetNetworkInterface("my-nic", "my-resource-group");

            // Get NICs for a VM
            NetworkInterface[] vmNics = await nicService.GetNetworkInterfacesForVM("my-vm", "my-resource-group");
            Log($"VM has {vmNics.Length} NICs");

            // Create an IP configuration
            IPConfiguration ipConfig = await nicService.CreateIpConfiguration(
                "secondary-ip", existingNic, "10.0.0.11", null);
            Log($"Added IP config: {ipConfig.Name}");

            // Delete an IP configuration
            await nicService.DeleteIpConfiguration("secondary-ip", existingNic);
        }
    }
}
```

## Configure UiPath Robot on Azure VM

```csharp
namespace MyProject
{
    public class ConfigureRobotWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var vmService = azure.AzureVirtualMachineService(clientProvider);
            var uipathService = azure.AzureUiPathService;

            // Get the target VM
            VirtualMachine vm = await vmService.GetAsync("my-resource-group", "robot-vm");

            // Configure robot using Orchestrator URL and machine key
            await uipathService.ConfigureRobot(
                vm,
                orchestratorURL: "https://cloud.uipath.com/org/tenant/orchestrator_",
                machineKey: "my-machine-key");
            Log("Robot configured with Orchestrator URL");

            // Alternative: configure using connection string
            await uipathService.ConfigureRobot(
                vm,
                connectionString: "my-connection-string");
            Log("Robot configured with connection string");
        }
    }
}
```

## Storage Account Lifecycle

```csharp
using System.Data;
using System.Security;

namespace MyProject
{
    public class StorageAccountWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var storageService = azure.AzureStorageAccountService(clientProvider);

            // Create a storage account
            var tags = new DataTable();
            tags.Columns.Add("Key", typeof(string));
            tags.Columns.Add("Value", typeof(string));
            tags.Rows.Add("Environment", "Dev");

            StorageAccount account = await storageService.CreateStorageAccount(
                resourceGroupName: "my-resource-group",
                name: "mydevstorageacct",
                region: "eastus",
                sku: SkuNameStorage.Standard_LRS,
                accountKind: AccountKindStorage.StorageV2,
                accessTier: AccessTierStorage.Hot,
                tags: tags,
                secureTransferRequired: true,
                waitForCompletion: true);
            Log($"Created storage account: {account.Name}");

            // List storage accounts in a resource group
            StorageAccount[] accounts = await storageService.GetStorageAccountList("my-resource-group");
            foreach (var sa in accounts)
            {
                Log($"Storage Account: {sa.Name}");
            }

            // Get a storage account key
            SecureString key = await storageService.GetStorageAccountKey(account, KeyNumber.Key1);

            // Regenerate a key
            SecureString newKey = await storageService.RegenerateStorageAccountKey(
                KeyNumber.Key2, "my-resource-group", "mydevstorageacct");

            // Delete a storage account
            await storageService.DeleteStorageAccountByName("my-resource-group", "mydevstorageacct");
            Log("Storage account deleted");
        }
    }
}
```

## Security Alert Management

```csharp
namespace MyProject
{
    public class SecurityAlertWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var alertService = azure.AzureSecurityAlertService(clientProvider);

            // Get a security alert
            SecurityAlert alert = await alertService.GetSecurityAlert(
                "alert-unique-name", "eastus", "my-resource-group");
            Log($"Alert: {alert.Name}");

            // Update alert state (e.g., dismiss or resolve)
            await alertService.SetSecurityAlertState(
                "alert-unique-name", "eastus",
                SecurityAlertState.Resolved, "my-resource-group");
            Log("Alert resolved");
        }
    }
}
```

## VM Disk Management

```csharp
namespace MyProject
{
    public class DiskManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var vmService = azure.AzureVirtualMachineService(clientProvider);

            // List all disks in a resource group
            VirtualMachineDisk[] disks = await vmService.GetDisksList("my-resource-group");
            foreach (var disk in disks)
            {
                Log($"Disk: {disk.Name}");
            }

            // Get a specific disk
            VirtualMachineDisk dataDisk = await vmService.GetDiskByNameAsync(
                "my-resource-group", "data-disk-1");

            // Get a VM and its disks
            VirtualMachine vm = await vmService.GetAsync("my-resource-group", "my-vm");
            VirtualMachineDisk[] vmDisks = await vmService.GetVirtualMachineDisksList(vm);
            Log($"VM has {vmDisks.Length} disks");

            // Attach a data disk
            await vmService.AttachDataDiskAsync(vm, dataDisk, HostCaching.ReadOnly, logicalUnitNumber: 1);
            Log("Data disk attached");

            // Detach a data disk
            await vmService.DetachDataDiskAsync(vm, dataDisk);
            Log("Data disk detached");
        }
    }
}
```

## Delete a VM with Full Cleanup

```csharp
namespace MyProject
{
    public class DeleteVmWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute(IAzureClientProvider clientProvider)
        {
            var vmService = azure.AzureVirtualMachineService(clientProvider);

            VirtualMachine vm = await vmService.GetAsync("my-resource-group", "temp-vm");

            // Delete the VM and all attached resources
            await vmService.DeleteByNameAsync(
                vm,
                waitForCompletion: true,
                deleteAttachedDisks: true,
                deleteAttachedNetworkInterfaces: true,
                deleteAttachedPublicIps: true,
                deleteAttachedVirtualNetworks: false,
                deleteAttachedNetworkSecurityGroups: false);
            Log("VM and attached disks/NICs/IPs deleted");
        }
    }
}
```
