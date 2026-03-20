# Citrix Activities API Reference

Reference for the `citrix` service from `UiPath.Citrix.Activities` package.

**Required package:** `"UiPath.Citrix.Activities": "[1.5.0]"`

**Auto-imported namespaces:** `UiPath.Citrix.Contracts`, `UiPath.Citrix`

**Service accessor:** `citrix` (type `ICitrix`)

---

## Overview

The Citrix API provides coded workflow access to **Citrix XenServer / Citrix Hypervisor** for managing virtual machines, snapshots, servers, storage repositories, and VM templates. Authentication is handled by creating a `CitrixService` through the `citrix` accessor with XenServer host credentials.

### Architecture

```
citrix (ICitrix)
└── .CitrixService(serverAddress, port, userName, password) → ICitrixService
    ├── VM Operations     (list, get, create, delete, rename, power, tags, folders)
    ├── Template Operations (list templates, create VM from template)
    ├── Snapshot Operations (take, delete, revert, list snapshots)
    └── Server Operations  (list servers, get host storage repositories)
```

### Workflow Pattern

1. Get an `ICitrixService` from `citrix` by providing XenServer credentials
2. Call async methods on the service

```csharp
var citrixService = citrix.CitrixService(
    serverAddress: "xenserver.company.com",
    port: 443,
    userName: "root",
    password: securePassword);
var vms = await citrixService.GetVMListAsync(FilterByEnum.All, "", false, PowerStateFilter.All, false);
```

---

## Key Enum Reference Summary

| Enum | Values | Description |
|------|--------|-------------|
| `FilterByEnum` | `All` (0), `Name` (1), `Folder` (2), `Tag` (3) | Filter field for VM/template queries |
| `PowerStateFilter` | `Halted` (0), `Paused` (1), `Running` (2), `Suspended` (3), `Unknown` (4), `All` (5) | Power state filter for VM listing |
| `VirtualMachinePowerState` | `Halted` (0), `Paused` (1), `Running` (2), `Suspended` (3), `Unknown` (4) | Actual VM power state |
| `ServerPowerState` | `Halted` (0), `Running` (1) | XenServer host power state |

---

## Key Model Types

| Type | Description |
|------|-------------|
| `VirtualMachine` | Citrix VM with UUID, name, power state, tags, IP addresses, guest OS |
| `Snapshot` | VM snapshot with UUID, name, description, creation date |
| `Server` | XenServer host with UUID, name, power state, master/maintenance flags |
| `StorageRepository` | Storage repository with UUID, name, capacity, free space |

---

## Reference Files

- **Full API reference** → [api.md](api.md) — all service interfaces, method signatures, parameters, return types, and model definitions
- **Code examples** → [examples.md](examples.md) — complete coded workflow examples for Citrix operations
