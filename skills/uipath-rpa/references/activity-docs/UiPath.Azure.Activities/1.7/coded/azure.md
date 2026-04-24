# Azure Activities API Reference

Reference for the `azure` service from `UiPath.Azure.Activities` package.

**Required package:** `"UiPath.Azure.Activities": "[2.0.0]"`

**Auto-imported namespaces:** `UiPath.Azure.Activities.API`, `UiPath.Azure.Models`, `UiPath.Core`, `UiPath.Azure.Core`

**Service accessor:** `azure` (type `IAzureService`)

---

## Architecture

The Azure API is a facade that provides access to 11 specialized sub-services. Most sub-services require an `IAzureClientProvider` to authenticate with Azure. Three services (`AzureBlobService`, `AzureTableService`, `AzureUiPathService`) are accessed as properties (no client provider needed at creation).

### Accessing Sub-Services

```csharp
// Property-based (no client provider)
var blobService = azure.AzureBlobService;
var tableService = azure.AzureTableService;
var uipathService = azure.AzureUiPathService;

// Method-based (requires IAzureClientProvider)
var keyVaultService = azure.AzureKeyVaultService(clientProvider, "myKeyVault");
var vmService = azure.AzureVirtualMachineService(clientProvider);
var rgService = azure.AzureResourceGroupService(clientProvider);
var storageService = azure.AzureStorageAccountService(clientProvider);
var nicService = azure.AzureNetworkInterfaceService(clientProvider);
var nsgService = azure.AzureNetworkSecurityGroupService(clientProvider);
var alertService = azure.AzureSecurityAlertService(clientProvider);
var rulesService = azure.AzureSecurityRulesService(clientProvider);
```

---

## Sub-Services Summary

| Service | Accessor | Requires ClientProvider | Description |
|---|---|---|---|
| `IAzureBlobService` | `azure.AzureBlobService` | No | Blob storage and container operations |
| `IAzureKeyVaultService` | `azure.AzureKeyVaultService(provider, vaultName)` | Yes | Secret management |
| `IAzureVirtualMachineService` | `azure.AzureVirtualMachineService(provider)` | Yes | VM lifecycle, disks, images, scripts |
| `IAzureResourceGroupService` | `azure.AzureResourceGroupService(provider)` | Yes | Resource group CRUD |
| `IAzureStorageAccountService` | `azure.AzureStorageAccountService(provider)` | Yes | Storage account management |
| `IAzureTableService` | `azure.AzureTableService` | No | Table storage operations |
| `IAzureNetworkInterfaceService` | `azure.AzureNetworkInterfaceService(provider)` | Yes | NIC and IP configuration |
| `IAzureNetworkSecurityGroupService` | `azure.AzureNetworkSecurityGroupService(provider)` | Yes | NSG management |
| `IAzureSecurityRulesService` | `azure.AzureSecurityRulesService(provider)` | Yes | NSG security rules |
| `IAzureSecurityAlertService` | `azure.AzureSecurityAlertService(provider)` | Yes | Security alert management |
| `IAzureUiPathService` | `azure.AzureUiPathService` | No | UiPath robot configuration on VMs |

---

## Key Enum Reference Summary

| Enum | Values |
|---|---|
| `EnvironmentType` | `Global` |
| `AzureBlobType` | Block, Page, Append blob types |
| `ContainerPublicAccessLevel` | Public access level for blob containers |
| `AccessTierBlob` | Access tier for individual blobs |
| `AccessTierStorage` | Access tier for storage accounts |
| `SkuNameStorage` | Storage account SKU (e.g., Standard_LRS, Standard_GRS) |
| `AccountKindStorage` | Storage account kind (e.g., StorageV2, BlobStorage) |
| `KeyNumber` | Storage account key number |
| `SecurityAlertState` | Security alert state values |
| `SecurityRuleAction` | `Allow`, `Deny` |
| `SecurityRuleDirection` | `Inbound`, `Outbound` |
| `SecurityRuleProtocol` | Network protocol for security rules |
| `VmPowerStateFilter` | `All`, `Running`, `Stopped`, etc. |
| `ImageLicenseType` | VM image license type |
| `SkuNameDisk` | OS disk type SKU |
| `NicNetworkSecurityGroup` | NIC-level NSG configuration |
| `HostCaching` | Disk host caching mode |
| `ScriptType` | Script type for VM script execution |
| `TableInsertType` | Table row insert mode |

---

## Key Model Types

| Type | Description |
|---|---|
| `IAzureClientProvider` | Azure authentication/client provider (from `UiPath.Azure.Interfaces`) |
| `StorageAccount` | Represents an Azure storage account |
| `BlobContainer` | Represents a blob container within a storage account |
| `Blob` | Represents a single blob |
| `Table` | Represents an Azure Table Storage table |
| `Row` | Represents a row in an Azure table |
| `SecretInfo` | Key Vault secret information |
| `VirtualMachine` | Represents an Azure VM |
| `VirtualMachineImage` | VM image (custom or marketplace) |
| `VirtualMachineDisk` | VM disk |
| `NetworkInterface` | Azure network interface |
| `IPConfiguration` | IP configuration on a NIC |
| `NetworkSecurityGroup` | Azure NSG |
| `NSGSecurityRule` | A rule within an NSG |
| `ResourceGroup` | Azure resource group |
| `SecurityAlert` | Azure security alert |
| `ScriptOutput` | Output from a VM script execution |
| `ILocalResource` | Local file resource (from `UiPath.Platform.ResourceHandling`) |

---

For the full API reference of all sub-services, see [api.md](api.md).

For complete coded workflow examples, see [examples.md](examples.md).
