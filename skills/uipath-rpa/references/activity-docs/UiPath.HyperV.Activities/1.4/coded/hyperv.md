# Hyper-V Activities API Reference

Reference for the `hyperv` service from `UiPath.HyperV.Activities` package.

**Required package:** `"UiPath.HyperV.Activities": "[1.4.0]"`

**Auto-imported namespaces:** `UiPath.HyperV.Core`, `UiPath.Core`, `UiPath.HyperV.Models`

**Service accessor:** `hyperv` (type `IHyperVService`)

---

## Overview

The Hyper-V API provides coded workflow access to **Virtual Machine management and Checkpoint (snapshot) operations** on Microsoft Hyper-V hosts via WMI. Authentication is handled by creating a `HyperVClientProvider` with host credentials, which is then passed to sub-services.

### Architecture

```
HyperVClientProvider(host, userName, secretKey) → IHyperVClientProvider

hyperv (IHyperVService)
├── .VirtualMachineService(clientProvider)                          → IVirtualMachineService
└── .CheckPointService(clientProvider, virtualMachineService)       → ICheckPointService
```

### Workflow Pattern

1. Create a `HyperVClientProvider` with Hyper-V host credentials
2. Get a sub-service from `hyperv` by passing the client provider
3. Call async methods on the sub-service

```csharp
var clientProvider = new HyperVClientProvider(host, userName, password);
var vmService = hyperv.VirtualMachineService(clientProvider);
var vms = await vmService.GetVMList(null, null, null, null, null, false);
```

> **Note:** `HyperVClientProvider` connects to the Hyper-V host's WMI namespace (`root\virtualization\v2`). Pass `null`/empty for `host` to connect to the local machine. Pass `null` for `userName` and `secretKey` to use current Windows credentials.

> **Note:** The `CheckPointService` requires both an `IHyperVClientProvider` and a concrete `VirtualMachineService` instance (from `UiPath.HyperV.Services`).

---

## Sub-Services Summary

| Service | Accessor | Description |
|---------|----------|-------------|
| `IVirtualMachineService` | `hyperv.VirtualMachineService(clientProvider)` | Create, delete, import, export, rename VMs; control power state; configure UiPath robots |
| `ICheckPointService` | `hyperv.CheckPointService(clientProvider, vmService)` | Create, delete, list, and revert VM checkpoints (snapshots) |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|------|--------|-------------|
| `VMGeneration` | `Generation1`, `Generation2` | Hyper-V VM generation |
| `VMState` | `Enabled` (2), `Disabled` (3), `ShutDown` (4), `Offline` (6), `Pause` (9), `Reset` (11) | VM power state |
| `VMImportType` | `Restore`, `Copy` | How to import a VM |
| `FilterBy` | `Name`, `Location` | VM list filter field |
| `FilterOperator` | `Equals`, `Contains`, `StartsWith`, `EndsWith` | VM list filter operator |
| `VmStateFilter` | `Running` (2), `Stopped` (3), `Paused` (9) | VM state filter for listing |
| `VMBootOrder` | `Floppy`, `CD`, `IDE`, `PXE`, `SCSI` | VM boot device order |
| `VMSnapshotType` | `Full` (2), `Disk` (3) | Checkpoint type |

---

## Key Model Types

| Type | Description |
|------|-------------|
| `HyperVClientProvider` | Creates WMI connection to Hyper-V host (from `UiPath.HyperV.Core`) |
| `IHyperVClientProvider` | Interface for Hyper-V client provider (from `UiPath.HyperV.Interfaces`) |
| `VirtualMachine` | Represents a Hyper-V virtual machine with ID, name, state, generation, network adapters |
| `Checkpoint` | Represents a VM checkpoint (snapshot) with ID, name, description, creation date |
| `NetworkAdapter` | Network adapter info with name, MAC, IP addresses, connection |
| `VirtualMachineService` | Concrete VM service class (from `UiPath.HyperV.Services`, needed for `CheckPointService`) |

---

## Reference Files

- **Full API reference** → [api.md](api.md) — all service interfaces, method signatures, parameters, return types, and model definitions
- **Code examples** → [examples.md](examples.md) — complete coded workflow examples for VM and checkpoint operations
