# Active Directory Domain Services Activities API Reference

Reference for the `activeDirectoryDomainServices` service from `UiPath.ActiveDirectoryDomainServices.Activities` package.

**Required package:** `"UiPath.ActiveDirectoryDomainServices.Activities": "[1.4.1]"`

**Auto-imported namespaces:** `UiPath.ActiveDirectoryDomainServices.Core`, `UiPath.Core`

**Service accessor:** `activeDirectoryDomainServices` (type `IActiveDirectoryDomainServicesService`)

---

## Overview

The Active Directory Domain Services API provides coded workflow access to manage AD DS objects — users, computers, groups, organizational units, and common directory operations (search, move, rename, property management).

The main entry point is `IActiveDirectoryDomainServicesService`, accessed via the `activeDirectoryDomainServices` service accessor. This service acts as a factory: each method takes an `ActiveDirectoryClientProvider` (obtained from an Active Directory Domain Services Scope activity) and returns a sub-service bound to your AD connection.

**Important:** All methods in this API are **synchronous** (not async/Task-based). They return values directly.

### Usage Pattern

```csharp
// 1. Obtain sub-services from the factory
IActiveDirectoryUserService userService = activeDirectoryDomainServices.ActiveDirectoryUserService(clientProvider);
IActiveDirectoryGroupService groupService = activeDirectoryDomainServices.ActiveDirectoryGroupService(clientProvider);
IActiveDirectoryCommonService commonService = activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

// 2. Call operations on the sub-services
string dn = commonService.GetDistinguishedName("john.doe");
var (lockStatus, activeStatus) = userService.GetUserStatus(dn);
```

### Connection Parameter

Most methods accept a `Connection` or `ConnectionWithoutAuto` parameter that specifies which AD connection to use (when the scope has primary and secondary connections configured):

- `Connection.Auto` — Automatically select the connection
- `Connection.Primary` — Use the primary connection (default)
- `Connection.Secondary` — Use the secondary connection
- `ConnectionWithoutAuto.Primary` / `ConnectionWithoutAuto.Secondary` — Same but without the `Auto` option

### API Categories

| Category | Sub-Service | Description | Reference |
|---|---|---|---|
| **Users** | `IActiveDirectoryUserService` | Create, delete, status, password, groups, expiration | [api.md - Users](api.md#users) |
| **Computers** | `IActiveDirectoryComputerService` | Create, status, domain join/unjoin | [api.md - Computers](api.md#computers) |
| **Groups** | `IActiveDirectoryGroupService` | Create groups, manage membership | [api.md - Groups](api.md#groups) |
| **Organizational Units** | `IActiveDirectoryOrganizationUnitService` | Create and delete OUs | [api.md - Organizational Units](api.md#organizational-units) |
| **Common Operations** | `IActiveDirectoryCommonService` | DN lookup, properties, search/filter, exists checks, move, rename | [api.md - Common Operations](api.md#common-operations) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Service Factory Methods

The `IActiveDirectoryDomainServicesService` (accessed via `activeDirectoryDomainServices`) exposes these factory methods. Each takes an `ActiveDirectoryClientProvider` and returns a sub-service:

| Method | Returns | Description |
|---|---|---|
| `ActiveDirectoryUserService(clientProvider)` | `IActiveDirectoryUserService` | User management |
| `ActiveDirectoryComputerService(clientProvider)` | `IActiveDirectoryComputerService` | Computer management |
| `ActiveDirectoryGroupService(clientProvider)` | `IActiveDirectoryGroupService` | Group management |
| `ActiveDirectoryOrganizationUnitService(clientProvider)` | `IActiveDirectoryOrganizationUnitService` | OU management |
| `ActiveDirectoryCommonService(clientProvider)` | `IActiveDirectoryCommonService` | Common directory operations |

---

## Type Reference

### ActiveDirectoryClientProvider

Connection configuration for the AD DS scope. Obtained from the Active Directory Domain Services Scope activity.

| Property | Type | Description |
|---|---|---|
| `_server` | `string` | AD server hostname or IP |
| `_username` | `string` | Username for authentication |
| `_password` | `SecureString` | Password for authentication |
| `_connectionType` | `ConnectionType` | LDAP or LDAPS |
| `_port` | `int` | Port number |
| `_secondaryConnection` | `ActiveDirectoryClientProvider` | Optional secondary connection |

### FilterProperty

Used to build LDAP search filters for `FilterObjectsByProperty`.

```csharp
// Constructor
new FilterProperty(string name, string value, Relation relation)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `string` | AD property name (e.g., `"sAMAccountName"`, `"cn"`, `"mail"`) |
| `value` | `string` | Value to match |
| `relation` | `Relation` | Comparison operator |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `Connection` | `Auto`, `Primary`, `Secondary` | Which AD connection to use |
| `ConnectionWithoutAuto` | `Primary`, `Secondary` | Connection without auto-select |
| `ConnectionType` | `LDAP`, `LDAPS` | Connection protocol |
| `EntryType` | `User`, `Group`, `Computer`, `OrganizationalUnit` | Type of AD directory entry |
| `ActiveStatus` | `Disabled` (0), `Enabled` (1) | Account enabled/disabled state |
| `LockStatus` | `Unlocked` (0), `Locked` (1) | Account lock state |
| `UserStatus` | `Disabled` (0), `Enabled` (1), `Unlocked` (2) | User status to set (includes unlock) |
| `GroupType` | `LocalDistribution`, `LocalSecurity`, `GlobalDistribution`, `GlobalSecurity`, `UniversalDistribution`, `UniversalSecurity` | AD group type and scope |
| `Relation` | `EqualTo`, `NotEqual`, `GreaterThanOrEqualTo`, `LessThanOrEqualTo` | Filter comparison operator |
| `ValidateCredentialsUserFilter` | `SAMAccountName`, `UserPrincipalName`, `DistinguishedName` | How to identify the user for credential validation |
| `ObjectPropertyFilter` | `SAMAccountName`, `CommonName` | Property to filter by |
| `UserPropertyFilter` | `SAMAccountName`, `CommonName`, `UserPrincipalName` | User property to filter by |
