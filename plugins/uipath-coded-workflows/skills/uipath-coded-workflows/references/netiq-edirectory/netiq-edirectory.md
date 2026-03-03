# NetIQ eDirectory Activities API Reference

Reference for the `netiq` service from `UiPath.NetIQeDirectory.Activities` package.

**Required package:** `"UiPath.NetIQeDirectory.Activities": "[1.4.1]"`

**Auto-imported namespaces:** `UiPath.NetIQeDirectory.Activities.API`, `UiPath.Core`, `UiPath.NetIQeDirectory`, `UiPath.NetIQeDirectory.Models`, `UiPath.NetIQeDirectory.Core`

**Service accessor:** `netiq` (type `INetIQeDirectoryService`)

---

## Overview

The NetIQ eDirectory API provides coded workflow access to manage NetIQ/Micro Focus eDirectory (LDAP-based directory service) objects — users, computers, groups, organizational units, and common directory operations (search, move, rename, property management).

The main entry point is `INetIQeDirectoryService`, accessed via the `netiq` service accessor. This service acts as a factory: each method takes an `INetIQeDirectoryClientProvider` (obtained from a NetIQ eDirectory Scope activity) and returns a sub-service bound to your LDAP connection.

**Note:** Most methods in this API are **asynchronous** (return `Task` or `Task<T>`), except `GetObjectProperties` which is synchronous.

### Usage Pattern

```csharp
// 1. Obtain sub-services from the factory
INetIQeDirectoryUserService userService = netiq.NetIQeDirectoryUserService(clientProvider);
INetIQeDirectoryGroupService groupService = netiq.NetIQeDirectoryGroupService(clientProvider);
INetIQeDirectoryObjectService objectService = netiq.NetIQeDirectoryObjectService(clientProvider);

// 2. Call operations on the sub-services
string dn = await objectService.GetDistinguishedName("john.doe", ConnectionWithoutAuto.Primary);
var (lockStatus, activeStatus) = await userService.GetUserStatus(dn, Connection.Primary);
```

### Connection Parameter

Most methods accept a `Connection` or `ConnectionWithoutAuto` parameter that specifies which eDirectory connection to use (when the scope has primary and secondary connections configured):

- `Connection.Auto` — Automatically select based on the DN suffix
- `Connection.Primary` — Use the primary connection
- `Connection.Secondary` — Use the secondary connection
- `ConnectionWithoutAuto.Primary` / `ConnectionWithoutAuto.Secondary` — Same but without the `Auto` option

**Important:** Unlike Active Directory Domain Services, the `Connection` parameter in NetIQ methods has **no default value** — it must always be specified explicitly.

### API Categories

| Category | Sub-Service | Description | Reference |
|---|---|---|---|
| **Objects** | `INetIQeDirectoryObjectService` | DN lookup, properties, search, move, rename, group membership | [api.md - Objects](api.md#objects) |
| **Users** | `INetIQeDirectoryUserService` | Create, delete, status, password, groups, expiration | [api.md - Users](api.md#users) |
| **Computers** | `INetIQeDirectoryComputerService` | Create, delete, status, group membership | [api.md - Computers](api.md#computers) |
| **Groups** | `INetIQeDirectoryGroupService` | Create, delete groups, manage membership | [api.md - Groups](api.md#groups) |
| **Organizational Units** | `INetIQeDirectoryOrganizationService` | Create and delete OUs | [api.md - Organizational Units](api.md#organizational-units) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Service Factory Methods

The `INetIQeDirectoryService` (accessed via `netiq`) exposes these factory methods. Each takes an `INetIQeDirectoryClientProvider` and returns a sub-service:

| Method | Returns | Description |
|---|---|---|
| `NetIQeDirectoryObjectService(clientProvider)` | `INetIQeDirectoryObjectService` | Common object operations |
| `NetIQeDirectoryUserService(clientProvider)` | `INetIQeDirectoryUserService` | User management |
| `NetIQeDirectoryComputerService(clientProvider)` | `INetIQeDirectoryComputerService` | Computer management |
| `NetIQeDirectoryGroupService(clientProvider)` | `INetIQeDirectoryGroupService` | Group management |
| `NetIQeDirectoryOrganizationService(clientProvider)` | `INetIQeDirectoryOrganizationService` | OU management |

---

## Type Reference

### INetIQeDirectoryClientProvider

LDAP connection provider obtained from the NetIQ eDirectory Scope activity. Provides authenticated `LdapConnection` instances for primary and optional secondary connections.

### FilterProperty

Used to build LDAP search filters.

```csharp
// Constructor
new FilterProperty(string name, string value, Relation relation)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `string` | LDAP attribute name (e.g., `"sAMAccountName"`, `"cn"`, `"mail"`) |
| `value` | `string` | Value to match |
| `relation` | `Relation` | Comparison operator |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `Connection` | `Auto`, `Primary`, `Secondary` | Which eDirectory connection to use |
| `ConnectionWithoutAuto` | `Primary`, `Secondary` | Connection without auto-select |
| `ConnectionType` | `LDAP`, `LDAPS` | Connection protocol |
| `EntryType` | `User`, `Group`, `Computer`, `OrganizationalUnit` | Type of directory entry |
| `ActiveStatus` | `Disabled` (0), `Enabled` (1) | Account enabled/disabled state |
| `LockStatus` | `Unlocked` (0), `Locked` (1) | Account lock state |
| `UserStatus` | `Disabled` (0), `Enabled` (1), `Unlocked` (2) | User status to set (includes unlock) |
| `GroupType` | `LocalDistribution`, `LocalSecurity`, `GlobalDistribution`, `GlobalSecurity`, `UniversalDistribution`, `UniversalSecurity` | Group type and scope |
| `Relation` | `EqualTo`, `NotEqual`, `GreaterThanOrEqualTo`, `LessThanOrEqualTo` | Filter comparison operator |
| `ValidateCredentialsUserFilter` | `SAMAccountName`, `UserPrincipalName`, `DistinguishedName` | How to identify user for credential validation |
