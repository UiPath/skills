# Azure — Full API Reference

Complete API reference for all Azure sub-services accessed via the `azure` service accessor. For general info see [azure.md](azure.md).

---

## Blob Storage Service (`IAzureBlobService`)

Accessed via `azure.AzureBlobService` (property, no client provider needed).

### GetBlobContainerAsync

Gets a blob container from a storage account.

```csharp
Task<BlobContainer> GetBlobContainerAsync(
    StorageAccount storageAccount,
    string containerName,
    SecureString key,
    SecureString sasToken,
    string storageAccountName,
    string resourceGroupName,
    bool createContainer = false,
    EnvironmentType environmentType = EnvironmentType.Global
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | — | The storage account object |
| `containerName` | `string` | Yes | — | Name of the blob container |
| `key` | `SecureString` | Yes | — | Storage account key |
| `sasToken` | `SecureString` | Yes | — | SAS token for authentication |
| `storageAccountName` | `string` | Yes | — | Name of the storage account |
| `resourceGroupName` | `string` | Yes | — | Resource group name |
| `createContainer` | `bool` | No | `false` | Create the container if it does not exist |
| `environmentType` | `EnvironmentType` | No | `Global` | Azure environment type |

**Returns:** `Task<BlobContainer>`

---

### GetBlobContainerListAsync

Gets a list of blob containers from a storage account.

```csharp
Task<BlobContainer[]> GetBlobContainerListAsync(
    StorageAccount storageAccount,
    SecureString storageAccountKey,
    SecureString sasToken,
    string storageAccountName,
    string resourceGroupName,
    int? maximumItems,
    string nameStartsWith,
    EnvironmentType environmentType = EnvironmentType.Global
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | — | The storage account object |
| `storageAccountKey` | `SecureString` | Yes | — | Storage account key |
| `sasToken` | `SecureString` | Yes | — | SAS token for authentication |
| `storageAccountName` | `string` | Yes | — | Name of the storage account |
| `resourceGroupName` | `string` | Yes | — | Resource group name |
| `maximumItems` | `int?` | Yes | — | Maximum number of containers to return (`null` for all) |
| `nameStartsWith` | `string` | Yes | — | Filter containers by name prefix |
| `environmentType` | `EnvironmentType` | No | `Global` | Azure environment type |

**Returns:** `Task<BlobContainer[]>`

---

### GetBlobAsync

Gets blob information.

```csharp
Task<Blob> GetBlobAsync(BlobContainer blobContainer, string blobName, bool skipOnError = false);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `blobContainer` | `BlobContainer` | Yes | — | The blob container |
| `blobName` | `string` | Yes | — | Name of the blob |
| `skipOnError` | `bool` | No | `false` | Skip errors instead of throwing |

**Returns:** `Task<Blob>`

---

### GetBlobsListAsync

Gets a list of blobs in a container.

```csharp
Task<Blob[]> GetBlobsListAsync(BlobContainer blobContainer, int? maximumItems, string nameStartsWith);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blobContainer` | `BlobContainer` | Yes | The blob container |
| `maximumItems` | `int?` | Yes | Maximum number of blobs to return (`null` for all) |
| `nameStartsWith` | `string` | Yes | Filter blobs by name prefix |

**Returns:** `Task<Blob[]>`

---

### CopyBlobAsync

Copies a blob to a destination container.

```csharp
Task<Blob> CopyBlobAsync(
    BlobContainer sourceBlobContainer,
    string sourceBlobName,
    BlobContainer destinationBlobContainer,
    string destinationBlobName,
    bool awaitForCompletion,
    int timeout
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `sourceBlobContainer` | `BlobContainer` | Yes | Source blob container |
| `sourceBlobName` | `string` | Yes | Name of the source blob |
| `destinationBlobContainer` | `BlobContainer` | Yes | Destination blob container |
| `destinationBlobName` | `string` | Yes | Name for the destination blob |
| `awaitForCompletion` | `bool` | Yes | Wait for copy to complete |
| `timeout` | `int` | Yes | Timeout in milliseconds |

**Returns:** `Task<Blob>` — The copied blob.

---

### DownloadBlobToDiskAsync

Downloads a blob to local disk.

```csharp
Task<ILocalResource> DownloadBlobToDiskAsync(Blob blob, string folder, string filename, bool overwrite);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blob` | `Blob` | Yes | The blob to download |
| `folder` | `string` | Yes | Destination folder path |
| `filename` | `string` | Yes | Destination file name |
| `overwrite` | `bool` | Yes | Overwrite existing file |

**Returns:** `Task<ILocalResource>`

---

### AppendToBlob

Appends content to an append blob.

```csharp
Task AppendToBlob(Blob blob, string path);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blob` | `Blob` | Yes | The append blob |
| `path` | `string` | Yes | Path of the file to append |

---

### DeleteBlobAsync

Deletes a blob.

```csharp
Task<bool> DeleteBlobAsync(Blob blob, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blob` | `Blob` | Yes | The blob to delete |
| `waitForCompletion` | `bool` | Yes | Wait for deletion to complete |

**Returns:** `Task<bool>` — `true` if deleted successfully.

---

### UploadBlobFromFileAsync

Uploads a blob from a local file.

```csharp
Task<Blob> UploadBlobFromFileAsync(
    BlobContainer blobContainer,
    string name,
    AzureBlobType type,
    bool uploadVhdFileAsPageBlob,
    string path,
    string contentType,
    DataTable metadata,
    AccessTierBlob accessTier
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blobContainer` | `BlobContainer` | Yes | Target blob container |
| `name` | `string` | Yes | Blob name |
| `type` | `AzureBlobType` | Yes | Blob type (Block, Page, Append) |
| `uploadVhdFileAsPageBlob` | `bool` | Yes | Upload VHD files as page blobs |
| `path` | `string` | Yes | Local file path |
| `contentType` | `string` | Yes | MIME content type |
| `metadata` | `DataTable` | Yes | Blob metadata (key-value pairs) |
| `accessTier` | `AccessTierBlob` | Yes | Blob access tier |

**Returns:** `Task<Blob>` — The uploaded blob.

---

### SetBlobTier

Sets the access tier of a blob.

```csharp
Task SetBlobTier(Blob blob, AccessTierBlob accessTier);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blob` | `Blob` | Yes | The blob |
| `accessTier` | `AccessTierBlob` | Yes | New access tier |

---

### CreateBlobContainerAsync

Creates a new blob container.

```csharp
Task<BlobContainer> CreateBlobContainerAsync(
    StorageAccount storageAccount,
    SecureString storageAccountKey,
    SecureString sasToken,
    string storageAccountName,
    string resourceGroupName,
    string containerName,
    ContainerPublicAccessLevel publicAccessLevel,
    DataTable metadata,
    EnvironmentType environmentType = EnvironmentType.Global
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | — | The storage account |
| `storageAccountKey` | `SecureString` | Yes | — | Storage account key |
| `sasToken` | `SecureString` | Yes | — | SAS token |
| `storageAccountName` | `string` | Yes | — | Storage account name |
| `resourceGroupName` | `string` | Yes | — | Resource group name |
| `containerName` | `string` | Yes | — | Name for the new container |
| `publicAccessLevel` | `ContainerPublicAccessLevel` | Yes | — | Public access level |
| `metadata` | `DataTable` | Yes | — | Container metadata |
| `environmentType` | `EnvironmentType` | No | `Global` | Azure environment type |

**Returns:** `Task<BlobContainer>`

---

### DeleteBlobContainerAsync

Deletes a blob container.

```csharp
Task<bool> DeleteBlobContainerAsync(BlobContainer blobContainer, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `blobContainer` | `BlobContainer` | Yes | The container to delete |
| `waitForCompletion` | `bool` | Yes | Wait for deletion to complete |

**Returns:** `Task<bool>` — `true` if deleted successfully.

---

## Key Vault Service (`IAzureKeyVaultService`)

Accessed via `azure.AzureKeyVaultService(clientProvider, keyVaultName)`.

### GetSecrets

Gets secrets from a Key Vault.

```csharp
Task<SecretInfo[]> GetSecrets(string KeyVaultName, string[] secretsToRetrieve = null);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `KeyVaultName` | `string` | Yes | — | Name of the Key Vault |
| `secretsToRetrieve` | `string[]` | No | `null` | Specific secret names to retrieve (`null` for all) |

**Returns:** `Task<SecretInfo[]>`

---

### DeleteSecret

Deletes a secret from a Key Vault.

```csharp
Task DeleteSecret(string KeyVaultName, string secretName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `KeyVaultName` | `string` | Yes | Name of the Key Vault |
| `secretName` | `string` | Yes | Name of the secret to delete |

---

## Virtual Machine Service (`IAzureVirtualMachineService`)

Accessed via `azure.AzureVirtualMachineService(clientProvider)`.

### GetAsync

Gets virtual machine information.

```csharp
Task<VirtualMachine> GetAsync(string resourceGroupName, string name);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroupName` | `string` | Yes | Resource group name |
| `name` | `string` | Yes | VM name |

**Returns:** `Task<VirtualMachine>`

---

### GetListAsync

Gets a list of virtual machines in a resource group.

```csharp
Task<VirtualMachine[]> GetListAsync(
    string resourceGroupName,
    bool includeNetworkingDetails = false,
    VmPowerStateFilter filter = VmPowerStateFilter.All
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `resourceGroupName` | `string` | Yes | — | Resource group name |
| `includeNetworkingDetails` | `bool` | No | `false` | Include networking details |
| `filter` | `VmPowerStateFilter` | No | `All` | Filter by power state |

**Returns:** `Task<VirtualMachine[]>`

---

### GetVmCustomImageListAsync

Gets a list of custom VM images in a resource group.

```csharp
Task<VirtualMachineImage[]> GetVmCustomImageListAsync(string resourceGroupName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroupName` | `string` | Yes | Resource group name |

**Returns:** `Task<VirtualMachineImage[]>`

---

### GetVirtualMachineCustomImageAsync

Gets a specific custom VM image.

```csharp
Task<VirtualMachineImage> GetVirtualMachineCustomImageAsync(string resourceGroupName, string imageName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroupName` | `string` | Yes | Resource group name |
| `imageName` | `string` | Yes | Image name |

**Returns:** `Task<VirtualMachineImage>`

---

### GetVirtualMachineImageByPublisherAsync

Gets a VM image by publisher details.

```csharp
Task<VirtualMachineImage> GetVirtualMachineImageByPublisherAsync(
    string region, string publisher, string offer, string sku, string version
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `region` | `string` | Yes | Azure region |
| `publisher` | `string` | Yes | Image publisher name |
| `offer` | `string` | Yes | Image offer |
| `sku` | `string` | Yes | Image SKU |
| `version` | `string` | Yes | Image version |

**Returns:** `Task<VirtualMachineImage>`

---

### CreateAsync

Creates a virtual machine.

```csharp
Task<VirtualMachine> CreateAsync(
    string resourceGroupName, string virtualMachineName, string computerName,
    string region, DataTable tags, VirtualMachineDisk disk, VirtualMachineImage image,
    ImageLicenseType imageLicensed, string size, SkuNameDisk osDiskType, string dnsName,
    string username, SecureString password, SecureString sshPublicKey,
    string virtualNetworkName, string subnetName, bool hasPublicIpAddress,
    string publicIpAddressName, NicNetworkSecurityGroup nicNetworkSecurityGroup,
    int[] publicInboundPorts, string networkSecurityGroupName, bool waitForCompletion
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroupName` | `string` | Yes | Resource group name |
| `virtualMachineName` | `string` | Yes | Name for the VM |
| `computerName` | `string` | Yes | Computer name (hostname) |
| `region` | `string` | Yes | Azure region |
| `tags` | `DataTable` | Yes | Tags as key-value pairs |
| `disk` | `VirtualMachineDisk` | Yes | Existing disk to attach (or `null`) |
| `image` | `VirtualMachineImage` | Yes | OS image for the VM |
| `imageLicensed` | `ImageLicenseType` | Yes | Image license type |
| `size` | `string` | Yes | VM size (e.g., "Standard_D2s_v3") |
| `osDiskType` | `SkuNameDisk` | Yes | OS disk SKU type |
| `dnsName` | `string` | Yes | DNS name label |
| `username` | `string` | Yes | Admin username |
| `password` | `SecureString` | Yes | Admin password |
| `sshPublicKey` | `SecureString` | Yes | SSH public key (for Linux VMs) |
| `virtualNetworkName` | `string` | Yes | Virtual network name |
| `subnetName` | `string` | Yes | Subnet name |
| `hasPublicIpAddress` | `bool` | Yes | Whether to assign a public IP |
| `publicIpAddressName` | `string` | Yes | Public IP resource name |
| `nicNetworkSecurityGroup` | `NicNetworkSecurityGroup` | Yes | NIC-level NSG configuration |
| `publicInboundPorts` | `int[]` | Yes | Inbound ports to open |
| `networkSecurityGroupName` | `string` | Yes | NSG name |
| `waitForCompletion` | `bool` | Yes | Wait for VM creation to complete |

**Returns:** `Task<VirtualMachine>`

---

### DeleteByNameAsync

Deletes a virtual machine with optional cleanup of attached resources.

```csharp
Task DeleteByNameAsync(
    VirtualMachine virtualMachine, bool waitForCompletion,
    bool deleteAttachedDisks, bool deleteAttachedNetworkInterfaces,
    bool deleteAttachedPublicIps, bool deleteAttachedVirtualNetworks,
    bool deleteAttachedNetworkSecurityGroups
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `virtualMachine` | `VirtualMachine` | Yes | The VM to delete |
| `waitForCompletion` | `bool` | Yes | Wait for deletion to complete |
| `deleteAttachedDisks` | `bool` | Yes | Also delete attached disks |
| `deleteAttachedNetworkInterfaces` | `bool` | Yes | Also delete attached NICs |
| `deleteAttachedPublicIps` | `bool` | Yes | Also delete attached public IPs |
| `deleteAttachedVirtualNetworks` | `bool` | Yes | Also delete attached VNets |
| `deleteAttachedNetworkSecurityGroups` | `bool` | Yes | Also delete attached NSGs |

---

### GetDisksList

Gets a list of disks in a resource group.

```csharp
Task<VirtualMachineDisk[]> GetDisksList(string resourceGroupName);
```

---

### GetVirtualMachineDisksList

Gets a list of disks attached to a VM.

```csharp
Task<VirtualMachineDisk[]> GetVirtualMachineDisksList(VirtualMachine virtualMachine);
```

---

### GetDiskByNameAsync

Gets a disk by name.

```csharp
Task<VirtualMachineDisk> GetDiskByNameAsync(string resourceGroupName, string diskName);
```

---

### StartAsync

Starts a virtual machine.

```csharp
Task StartAsync(VirtualMachine virtualMachine, bool waitForCompletion);
```

---

### ShutdownAsync

Shuts down a virtual machine (OS-level shutdown).

```csharp
Task ShutdownAsync(VirtualMachine virtualMachine, bool waitForCompletion);
```

---

### StopAsync

Stops (deallocates) a virtual machine.

```csharp
Task StopAsync(VirtualMachine virtualMachine, bool reservePublicIpAddress, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `virtualMachine` | `VirtualMachine` | Yes | The VM to stop |
| `reservePublicIpAddress` | `bool` | Yes | Keep the public IP reserved |
| `waitForCompletion` | `bool` | Yes | Wait for the operation to complete |

---

### RestartAsync

Restarts a virtual machine.

```csharp
Task RestartAsync(VirtualMachine virtualMachine, bool waitForCompletion);
```

---

### RunScriptAsync

Runs a script on a virtual machine.

```csharp
Task<ScriptOutput[]> RunScriptAsync(
    VirtualMachine virtualMachine, string script,
    ScriptType scriptType, DataTable scriptArguments
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `virtualMachine` | `VirtualMachine` | Yes | Target VM |
| `script` | `string` | Yes | Script content |
| `scriptType` | `ScriptType` | Yes | Type of script (PowerShell, Shell, etc.) |
| `scriptArguments` | `DataTable` | Yes | Script arguments as key-value pairs |

**Returns:** `Task<ScriptOutput[]>`

---

### GetRdpFilesAsync

Gets RDP files for connecting to a VM.

```csharp
Task<ILocalResource[]> GetRdpFilesAsync(
    VirtualMachine virtualMachine, int port, string folder, string filenamePrefix
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `virtualMachine` | `VirtualMachine` | Yes | Target VM |
| `port` | `int` | Yes | RDP port number |
| `folder` | `string` | Yes | Output folder path |
| `filenamePrefix` | `string` | Yes | Filename prefix for RDP files |

**Returns:** `Task<ILocalResource[]>`

---

### AttachDataDiskAsync

Attaches a data disk to a VM.

```csharp
Task AttachDataDiskAsync(
    VirtualMachine virtualMachine, VirtualMachineDisk virtualMachineDisk,
    HostCaching? hostHostCaching, int logicalUnitNumber
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `virtualMachine` | `VirtualMachine` | Yes | Target VM |
| `virtualMachineDisk` | `VirtualMachineDisk` | Yes | Disk to attach |
| `hostHostCaching` | `HostCaching?` | Yes | Host caching mode (`null` for default) |
| `logicalUnitNumber` | `int` | Yes | LUN for the disk |

---

### DetachDataDiskAsync

Detaches a data disk from a VM.

```csharp
Task DetachDataDiskAsync(VirtualMachine virtualMachine, VirtualMachineDisk virtualMachineDisk);
```

---

## Resource Group Service (`IAzureResourceGroupService`)

Accessed via `azure.AzureResourceGroupService(clientProvider)`.

### GetResourceGroupList

Gets a list of all resource groups.

```csharp
Task<ResourceGroup[]> GetResourceGroupList();
```

**Returns:** `Task<ResourceGroup[]>`

---

### CreateResourceGroup

Creates a new resource group.

```csharp
Task<ResourceGroup> CreateResourceGroup(string resourceGroupName, string region, DataTable tags);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroupName` | `string` | Yes | Name for the resource group |
| `region` | `string` | Yes | Azure region |
| `tags` | `DataTable` | Yes | Tags as key-value pairs |

**Returns:** `Task<ResourceGroup>`

---

### DeleteResourceGroup

Deletes a resource group.

```csharp
Task<bool> DeleteResourceGroup(ResourceGroup resourceGroup, bool waitForCompletion);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `resourceGroup` | `ResourceGroup` | Yes | The resource group to delete |
| `waitForCompletion` | `bool` | Yes | Wait for deletion to complete |

**Returns:** `Task<bool>` — `true` if deleted successfully.

---

### GetResourceGroup

Gets a specific resource group by name.

```csharp
Task<ResourceGroup> GetResourceGroup(string name);
```

**Returns:** `Task<ResourceGroup>`

---

## Storage Account Service (`IAzureStorageAccountService`)

Accessed via `azure.AzureStorageAccountService(clientProvider)`.

### CreateStorageAccount

Creates a new storage account.

```csharp
Task<StorageAccount> CreateStorageAccount(
    string resourceGroupName, string name, string region,
    SkuNameStorage sku, AccountKindStorage accountKind, AccessTierStorage accessTier,
    DataTable tags, bool secureTransferRequired = true, bool waitForCompletion = true
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `resourceGroupName` | `string` | Yes | — | Resource group name |
| `name` | `string` | Yes | — | Storage account name |
| `region` | `string` | Yes | — | Azure region |
| `sku` | `SkuNameStorage` | Yes | — | Storage SKU |
| `accountKind` | `AccountKindStorage` | Yes | — | Account kind |
| `accessTier` | `AccessTierStorage` | Yes | — | Access tier |
| `tags` | `DataTable` | Yes | — | Tags as key-value pairs |
| `secureTransferRequired` | `bool` | No | `true` | Require HTTPS |
| `waitForCompletion` | `bool` | No | `true` | Wait for creation to complete |

**Returns:** `Task<StorageAccount>`

---

### GetStorageAccountKey

Gets a storage account key.

```csharp
Task<SecureString> GetStorageAccountKey(StorageAccount storageAccount, KeyNumber keyNumber);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | The storage account |
| `keyNumber` | `KeyNumber` | Yes | Which key to retrieve |

**Returns:** `Task<SecureString>`

---

### GetStorageAccountList

Gets a list of storage accounts in a resource group.

```csharp
Task<StorageAccount[]> GetStorageAccountList(string resourceGroupName);
```

---

### DeleteStorageAccountById

Deletes a storage account by its Azure resource ID.

```csharp
Task DeleteStorageAccountById(string id);
```

---

### DeleteStorageAccountByName

Deletes a storage account by name.

```csharp
Task DeleteStorageAccountByName(string resourceGroupName, string name);
```

---

### GetStorageAccount

Gets storage account information.

```csharp
Task<StorageAccount> GetStorageAccount(string resourceGroupName, string storageAccountName);
```

---

### RegenerateStorageAccountKey

Regenerates a storage account key.

```csharp
Task<SecureString> RegenerateStorageAccountKey(
    KeyNumber keyNumber, string resourceGroupName, string storageAccountName
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keyNumber` | `KeyNumber` | Yes | Which key to regenerate |
| `resourceGroupName` | `string` | Yes | Resource group name |
| `storageAccountName` | `string` | Yes | Storage account name |

**Returns:** `Task<SecureString>` — The new key.

---

## Table Service (`IAzureTableService`)

Accessed via `azure.AzureTableService` (property, no client provider needed).

### CreateTableAsync

Creates a table in a storage account.

```csharp
Task<Table> CreateTableAsync(StorageAccount storageAccount, SecureString storageAccountKey, string tableName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | The storage account |
| `storageAccountKey` | `SecureString` | Yes | Storage account key |
| `tableName` | `string` | Yes | Name for the new table |

**Returns:** `Task<Table>`

---

### GetTableListAsync

Gets a list of tables in a storage account.

```csharp
Task<Table[]> GetTableListAsync(
    StorageAccount storageAccount, SecureString storageAccountKey,
    string nameStartsWith, int? maximumItems
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `storageAccount` | `StorageAccount` | Yes | The storage account |
| `storageAccountKey` | `SecureString` | Yes | Storage account key |
| `nameStartsWith` | `string` | Yes | Filter tables by name prefix |
| `maximumItems` | `int?` | Yes | Maximum tables to return (`null` for all) |

**Returns:** `Task<Table[]>`

---

### GetTableAsync

Gets a specific table.

```csharp
Task<Table> GetTableAsync(StorageAccount storageAccount, SecureString storageAccountKey, string tableName);
```

---

### DeleteTableAsync

Deletes a table.

```csharp
Task DeleteTableAsync(Table table);
```

---

### InsertTableRowsAsync

Inserts rows into a table.

```csharp
Task InsertTableRowsAsync(Table table, Row[] rows, TableInsertType insertType);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `table` | `Table` | Yes | Target table |
| `rows` | `Row[]` | Yes | Rows to insert |
| `insertType` | `TableInsertType` | Yes | Insert mode |

---

### GetTableRowAsync

Gets a specific row by its partition key and row key.

```csharp
Task<Row> GetTableRowAsync(Table table, string partitionKey, string rowKey);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `table` | `Table` | Yes | The table |
| `partitionKey` | `string` | Yes | Partition key of the row |
| `rowKey` | `string` | Yes | Row key |

**Returns:** `Task<Row>`

---

### DeleteTableRowsAsync

Deletes rows from a table.

```csharp
Task DeleteTableRowsAsync(Table table, Row[] rows);
```

---

### GetRowsByFilterAsync

Gets rows matching an OData filter.

```csharp
Task<Row[]> GetRowsByFilterAsync(Table table, int? maximumItems, string[] select, string oDataFilter);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `table` | `Table` | Yes | The table |
| `maximumItems` | `int?` | Yes | Maximum rows to return (`null` for all) |
| `select` | `string[]` | Yes | Column names to select |
| `oDataFilter` | `string` | Yes | OData filter expression |

**Returns:** `Task<Row[]>`

---

## Network Interface Service (`IAzureNetworkInterfaceService`)

Accessed via `azure.AzureNetworkInterfaceService(clientProvider)`.

### CreateNetworkInterface

Creates a network interface.

```csharp
Task<NetworkInterface> CreateNetworkInterface(
    string networkInterface, string virtualNetworkName, string subnetName,
    string rgName, string location, bool keepExisting = false,
    string privateIpAddress = null, string publicIpAddressName = null,
    string nsgName = null, DataTable tags = null,
    bool enableIpForwarding = false, bool enableAcceleratedNetworking = false
);
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `networkInterface` | `string` | Yes | — | NIC name |
| `virtualNetworkName` | `string` | Yes | — | Virtual network name |
| `subnetName` | `string` | Yes | — | Subnet name |
| `rgName` | `string` | Yes | — | Resource group name |
| `location` | `string` | Yes | — | Azure region |
| `keepExisting` | `bool` | No | `false` | Keep existing NIC if found |
| `privateIpAddress` | `string` | No | `null` | Static private IP address |
| `publicIpAddressName` | `string` | No | `null` | Public IP resource name |
| `nsgName` | `string` | No | `null` | Associated NSG name |
| `tags` | `DataTable` | No | `null` | Tags |
| `enableIpForwarding` | `bool` | No | `false` | Enable IP forwarding |
| `enableAcceleratedNetworking` | `bool` | No | `false` | Enable accelerated networking |

**Returns:** `Task<NetworkInterface>`

---

### GetNetworkInterface

Gets a network interface.

```csharp
Task<NetworkInterface> GetNetworkInterface(string interfaceName, string resourceGroupName);
```

---

### DeleteNetworkInterface

Deletes a network interface.

```csharp
Task DeleteNetworkInterface(NetworkInterface networkInterface, bool waitForCompletion);
```

---

### GetNetworkInterfacesForNSG

Gets network interfaces associated with a given NSG.

```csharp
Task<NetworkInterface[]> GetNetworkInterfacesForNSG(string nsgName, string resourceGroup);
```

---

### GetNetworkInterfacesForVM

Gets network interfaces attached to a VM.

```csharp
Task<NetworkInterface[]> GetNetworkInterfacesForVM(string vmName, string resourceGroup);
```

---

### CreateIpConfiguration

Creates an IP configuration on a NIC.

```csharp
Task<IPConfiguration> CreateIpConfiguration(
    string name, NetworkInterface networkInterface,
    string privateIpAddress, string publicIpAddressName
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | IP configuration name |
| `networkInterface` | `NetworkInterface` | Yes | Parent NIC |
| `privateIpAddress` | `string` | Yes | Private IP address |
| `publicIpAddressName` | `string` | Yes | Public IP resource name |

**Returns:** `Task<IPConfiguration>`

---

### DeleteIpConfiguration

Deletes an IP configuration from a NIC.

```csharp
Task DeleteIpConfiguration(string ipConfigurationName, NetworkInterface networkInterface);
```

---

## Network Security Group Service (`IAzureNetworkSecurityGroupService`)

Accessed via `azure.AzureNetworkSecurityGroupService(clientProvider)`.

### CreateNetworkSecurityGroup

Creates a network security group.

```csharp
Task<NetworkSecurityGroup> CreateNetworkSecurityGroup(
    string networkSecurityGroup, string resourceGroup, string region, DataTable tags
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `networkSecurityGroup` | `string` | Yes | NSG name |
| `resourceGroup` | `string` | Yes | Resource group name |
| `region` | `string` | Yes | Azure region |
| `tags` | `DataTable` | Yes | Tags as key-value pairs |

**Returns:** `Task<NetworkSecurityGroup>`

---

### GetNetworkSecurityGroup

Gets a network security group.

```csharp
Task<NetworkSecurityGroup> GetNetworkSecurityGroup(string networkSecurityGroupName, string resourceGroupName);
```

---

### DeleteNetworkSecurityGroup

Deletes a network security group.

```csharp
Task DeleteNetworkSecurityGroup(NetworkSecurityGroup nsg, bool waitForCompletion);
```

---

### GetVMNetworkSecurityGroupList

Gets network security groups associated with a VM.

```csharp
Task<NetworkSecurityGroup[]> GetVMNetworkSecurityGroupList(string vmName, string resourceGroupName);
```

---

## Security Rules Service (`IAzureSecurityRulesService`)

Accessed via `azure.AzureSecurityRulesService(clientProvider)`.

### CreateSecurityRule

Creates a security rule in a network security group.

```csharp
Task<NSGSecurityRule> CreateSecurityRule(
    NetworkSecurityGroup nsg, SecurityRuleAction access, string description,
    SecurityRuleDirection direction, string name, int priority,
    SecurityRuleProtocol protocol, string sourcePortRange, string sourceAddressPrefix,
    string destinationPortRange, string destinationAddressPrefix
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `nsg` | `NetworkSecurityGroup` | Yes | Parent NSG |
| `access` | `SecurityRuleAction` | Yes | `Allow` or `Deny` |
| `description` | `string` | Yes | Rule description |
| `direction` | `SecurityRuleDirection` | Yes | `Inbound` or `Outbound` |
| `name` | `string` | Yes | Rule name |
| `priority` | `int` | Yes | Priority (100-4096, lower = higher priority) |
| `protocol` | `SecurityRuleProtocol` | Yes | Network protocol |
| `sourcePortRange` | `string` | Yes | Source port range (e.g., `"*"`, `"80"`, `"1024-65535"`) |
| `sourceAddressPrefix` | `string` | Yes | Source address prefix (e.g., `"*"`, `"10.0.0.0/24"`) |
| `destinationPortRange` | `string` | Yes | Destination port range |
| `destinationAddressPrefix` | `string` | Yes | Destination address prefix |

**Returns:** `Task<NSGSecurityRule>`

---

### GetSecurityRule

Gets a security rule.

```csharp
Task<NSGSecurityRule> GetSecurityRule(string ruleName, string nsgName, string resourceGroupName);
```

---

### DeleteSecurityRule

Deletes a security rule.

```csharp
Task DeleteSecurityRule(NSGSecurityRule securityRule, bool waitForCompletion);
```

---

### GetSecurityRuleList

Gets all security rules in an NSG.

```csharp
Task<NSGSecurityRule[]> GetSecurityRuleList(string nsgName, string resourceGroupName);
```

---

## Security Alert Service (`IAzureSecurityAlertService`)

Accessed via `azure.AzureSecurityAlertService(clientProvider)`.

### GetSecurityAlert

Gets a security alert.

```csharp
Task<SecurityAlert> GetSecurityAlert(string uniqueName, string location, string resourceGroup);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `uniqueName` | `string` | Yes | Unique name of the alert |
| `location` | `string` | Yes | Azure region |
| `resourceGroup` | `string` | Yes | Resource group name |

**Returns:** `Task<SecurityAlert>`

---

### SetSecurityAlertState

Sets the state of a security alert.

```csharp
Task SetSecurityAlertState(
    string uniqueName, string location, SecurityAlertState newState, string resourceGroup
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `uniqueName` | `string` | Yes | Unique name of the alert |
| `location` | `string` | Yes | Azure region |
| `newState` | `SecurityAlertState` | Yes | New alert state |
| `resourceGroup` | `string` | Yes | Resource group name |

---

## UiPath Service (`IAzureUiPathService`)

Accessed via `azure.AzureUiPathService` (property, no client provider needed).

### ConfigureRobot (Orchestrator URL)

Configures a UiPath robot on a VM using Orchestrator URL and machine key.

```csharp
Task ConfigureRobot(VirtualMachine vm, string orchestratorURL, string machineKey);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `vm` | `VirtualMachine` | Yes | Target VM |
| `orchestratorURL` | `string` | Yes | Orchestrator URL |
| `machineKey` | `string` | Yes | Machine key |

---

### ConfigureRobot (Connection String)

Configures a UiPath robot on a VM using a connection string.

```csharp
Task ConfigureRobot(VirtualMachine vm, string connectionString);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `vm` | `VirtualMachine` | Yes | Target VM |
| `connectionString` | `string` | Yes | Connection string |
