# Azure Windows Virtual Desktop Activities API Reference

Reference for the `azureWVD` service from `UiPath.AzureWindowsVirtualDesktop.Activities` package.

**Required package:** `"UiPath.AzureWindowsVirtualDesktop.Activities": "[1.4.1]"`

**Auto-imported namespaces:** `UiPath.AzureWindowsVirtualDesktop.Activities.API`, `UiPath.AzureWVD.Models`, `UiPath.Core`, `UiPath.AzureWVD.Core`

**Service accessor:** `azureWVD` (type `IAzureWindowsVirtualDesktopService`)

---

## Overview

The Azure Windows Virtual Desktop API provides coded workflow access to manage Azure Virtual Desktop (formerly Windows Virtual Desktop) resources — host pools, session hosts, workspaces, application groups, user sessions, and role assignments.

The main entry point is `IAzureWindowsVirtualDesktopService`, accessed via the `azureWVD` service accessor. This service acts as a factory: each method takes an `IClientProvider` (obtained from an Azure WVD Scope activity) and returns a sub-service bound to your Azure connection.

**Note:** All methods in this API are **asynchronous** (return `Task` or `Task<T>`) and should be awaited.

### Usage Pattern

```csharp
// 1. Obtain sub-services from the factory
IHostPoolService hostPoolService = azureWVD.HostPoolService(clientProvider);
ISessionHostService sessionHostService = azureWVD.SessionHostService(clientProvider);
IWorkspaceService workspaceService = azureWVD.WorkspaceService(clientProvider);

// 2. Call operations on the sub-services
WVDHostPool hostPool = await hostPoolService.GetHostPool("myHostPool", "myResourceGroup");
SessionHostList sessionHosts = await sessionHostService.ListSessionHosts(hostPool, null);
```

### Client Provider

The `IClientProvider` parameter is obtained from an Azure WVD Scope activity. It provides authenticated access to Azure WVD REST APIs and the Azure Management SDK using either service principal credentials or Integration Service tokens.

### API Categories

| Category | Sub-Service | Description | Reference |
|---|---|---|---|
| **Host Pools** | `IHostPoolService` | Create, update, delete, list host pools; add VMs | [api.md - Host Pools](api.md#host-pools) |
| **Session Hosts** | `ISessionHostService` | Get, update, delete, list session hosts | [api.md - Session Hosts](api.md#session-hosts) |
| **User Sessions** | `IUserSessionService` | Send messages, disconnect, delete, list sessions | [api.md - User Sessions](api.md#user-sessions) |
| **Workspaces** | `IWorkspaceService` | Create, update, delete, get, list workspaces | [api.md - Workspaces](api.md#workspaces) |
| **Application Groups** | `IApplicationGroupService` | Get and list application groups | [api.md - Application Groups](api.md#application-groups) |
| **Role Assignments** | `IRoleAssignmentService` | Assign/remove users from application groups | [api.md - Role Assignments](api.md#role-assignments) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Service Factory Methods

The `IAzureWindowsVirtualDesktopService` (accessed via `azureWVD`) exposes these factory methods. Each takes an `IClientProvider` and returns a sub-service:

| Method | Returns | Description |
|---|---|---|
| `HostPoolService(clientProvider)` | `IHostPoolService` | Host pool management |
| `SessionHostService(clientProvider)` | `ISessionHostService` | Session host management |
| `UserSessionService(clientProvider)` | `IUserSessionService` | User session management |
| `WorkspaceService(clientProvider)` | `IWorkspaceService` | Workspace management |
| `ApplicationGroupService(clientProvider)` | `IApplicationGroupService` | Application group queries |
| `RoleAssignmentService(clientProvider)` | `IRoleAssignmentService` | Role assignment management |

---

## Type Reference

### WVDHostPool

Represents an Azure Virtual Desktop host pool.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Azure resource ID |
| `Name` | `string` | Host pool name |
| `ResourceGroupName` | `string` | Resource group name |
| `FriendlyName` | `string` | Display name |
| `Description` | `string` | Description |
| `HostPoolType` | `HostPoolType?` | `Personal` or `Pooled` |
| `Region` | `string` | Azure region |
| `PreferredAppGroupType` | `PreferredAppGroupType?` | Preferred app group type |
| `PersonalDesktopAssignmentType` | `PersonalDesktopAssignmentType?` | `Automatic` or `Direct` |
| `MaxSessionLimit` | `int` | Maximum concurrent sessions |
| `LoadBalancerType` | `LoadBalancerType?` | `BreadthFirst` or `DepthFirst` |
| `IsValidationEnvironment` | `bool` | Whether this is a validation environment |
| `VMTemplate` | `string` | VM template JSON |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |
| `DefaultDesktopApplicationGroupName` | `string` | Default desktop app group name |
| `DefaultDesktopApplicationGroupId` | `string` | Default desktop app group ID |

### WVDSessionHost

Represents a session host in a host pool.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Azure resource ID |
| `Name` | `string` | Session host name |
| `HostPoolId` | `string` | Parent host pool ID |
| `HostPoolName` | `string` | Parent host pool name |
| `ResourceGroupName` | `string` | Resource group name |
| `AgentVersion` | `string` | WVD agent version |
| `AllowNewSession` | `bool` | Whether new sessions are allowed |
| `AssignedUser` | `string` | Assigned user (personal pools) |
| `LastHeartBeat` | `DateTime?` | Last heartbeat time |
| `LastUpdateTime` | `DateTime?` | Last update time |
| `OsVersion` | `string` | OS version |
| `VirtualMachineID` | `string` | VM ID |
| `VirtualMachineResourceID` | `string` | VM Azure resource ID |
| `NumberOfSessions` | `int` | Current session count |
| `Status` | `SessionHostStatus?` | Current status |
| `StatusTimestamp` | `DateTime?` | Status timestamp |
| `SxSStackVersion` | `string` | Side-by-side stack version |
| `UpdateState` | `SessionHostUpdateState?` | Update state |
| `UpdateErrorMessage` | `string` | Update error message |

### WVDUserSession

Represents a user session on a session host.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Azure resource ID |
| `Name` | `string` | Session name |
| `ResourceGroupName` | `string` | Resource group name |
| `ActiveDirectoryUserName` | `string` | AD username |
| `UserPrincipalName` | `string` | User principal name |
| `SessionState` | `SessionState?` | Current session state |
| `CreateTime` | `DateTime` | Session creation time |
| `ApplicationType` | `ApplicationType?` | `RemoteApp` or `Desktop` |

### WVDWorkspace

Represents an Azure Virtual Desktop workspace.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Azure resource ID |
| `ResourceGroupName` | `string` | Resource group name |
| `Region` | `string` | Azure region |
| `Name` | `string` | Workspace name |
| `FriendlyName` | `string` | Display name |
| `Description` | `string` | Description |
| `ApplicationGroupsIds` | `string[]` | Associated application group IDs |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |

### WVDApplicationGroup

Represents an application group.

| Property | Type | Description |
|---|---|---|
| `ID` | `string` | Azure resource ID |
| `ResourceGroupName` | `string` | Resource group name |
| `Region` | `string` | Azure region |
| `Name` | `string` | Application group name |
| `FriendlyName` | `string` | Display name |
| `Description` | `string` | Description |
| `ApplicationGroupType` | `ApplicationGroupType` | `RemoteApp` or `Desktop` |
| `WorkspaceName` | `string` | Parent workspace name |
| `WorkspaceResourceGroupName` | `string` | Parent workspace resource group |
| `HostPoolName` | `string` | Associated host pool name |
| `HostPoolResourceGroupName` | `string` | Associated host pool resource group |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |

### HostPoolCreateParams

Parameters for creating a host pool.

| Property | Type | Description |
|---|---|---|
| `Description` | `string` | Description |
| `FriendlyName` | `string` | Display name |
| `Name` | `string` | Host pool name |
| `ResourceGroupName` | `string` | Resource group name |
| `Region` | `string` | Azure region |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |
| `ValidationEnvironment` | `bool` | Whether this is a validation environment |
| `Workspace` | `string` | Workspace to associate |
| `Type` | `HostPoolType` | `Personal` or `Pooled` |
| `PersonalDesktopAssignmentType` | `PersonalDesktopAssignmentType` | `Automatic` or `Direct` |
| `PooledMaxSessionLimit` | `int?` | Max sessions for pooled pools |
| `PooledLoadBalancing` | `LoadBalancerType` | Load balancing type for pooled pools |

### HostPoolUpdateParams

Parameters for updating a host pool.

| Property | Type | Description |
|---|---|---|
| `Description` | `string` | Description |
| `FriendlyName` | `string` | Display name |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |
| `ValidationEnvironment` | `bool?` | Whether this is a validation environment |
| `PooledMaxSessionLimit` | `int?` | Max sessions for pooled pools |
| `PooledLoadBalancing` | `LoadBalancerType?` | Load balancing type |
| `PersonalDesktopAssignmentType` | `PersonalDesktopAssignmentType?` | Assignment type |

### WorkspaceCreateParams

Parameters for creating a workspace.

| Property | Type | Description |
|---|---|---|
| `Description` | `string` | Description |
| `FriendlyName` | `string` | Display name |
| `Name` | `string` | Workspace name |
| `ResourceGroupName` | `string` | Resource group name |
| `Region` | `string` | Azure region |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |
| `ApplicationGroups` | `string[]` | Application group IDs to associate |

### WorkspaceUpdateParams

Parameters for updating a workspace.

| Property | Type | Description |
|---|---|---|
| `Description` | `string` | Description |
| `FriendlyName` | `string` | Display name |
| `Name` | `string` | Workspace name |
| `ResourceGroupName` | `string` | Resource group name |
| `Tags` | `DataTable` | Resource tags (2-column: key, value) |
| `ApplicationGroups` | `string[]` | Application group IDs to associate |

### Paginated List Types

List methods return paginated results with these wrapper types:

| Type | `Value` Property Type | Description |
|---|---|---|
| `HostPoolList` | `ICollection<HostPool>` | Paginated host pool list |
| `SessionHostList` | `ICollection<SessionHost>` | Paginated session host list |
| `UserSessionList` | `ICollection<UserSession>` | Paginated user session list |
| `WorkspaceList` | `ICollection<Workspace>` | Paginated workspace list |
| `ApplicationGroupList` | `ICollection<ApplicationGroup>` | Paginated application group list |

All list types have a `NextLink` (`string`) property containing the URL for the next page, or `null` if no more pages. Pass the skip token from `NextLink` as the `token`/`skipToken` parameter to retrieve subsequent pages.

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `HostPoolType` | `Personal`, `Pooled` | Host pool type |
| `LoadBalancerType` | `BreadthFirst`, `DepthFirst` | Load balancing algorithm for pooled pools |
| `PersonalDesktopAssignmentType` | `Automatic`, `Direct` | How users are assigned to personal desktops |
| `PreferredAppGroupType` | `None`, `Desktop`, `RailApplications` | Preferred application group type |
| `ApplicationGroupType` | `RemoteApp`, `Desktop` | Application group type |
| `ApplicationType` | `RemoteApp`, `Desktop` | Application type in user sessions |
| `SessionHostStatus` | `Available`, `Unavailable`, `Shutdown`, `Disconnected`, `Upgrading`, `UpgradeFailed`, `NoHeartbeat`, `NotJoinedToDomain`, `DomainTrustRelationshipLost`, `SxSStackListenerNotReady`, `FSLogixNotHealthy`, `NeedsAssistance` | Session host health status |
| `SessionHostUpdateState` | `Failed`, `Initial`, `Pending`, `Started`, `Succeeded` | Session host update state |
| `SessionState` | `Active`, `Disconnected`, `LogOff`, `Pending`, `Unknown`, `UserProfileDiskMounted` | User session state |
| `AzureWVDEnvironment` | `Global` (0), `Germany` (1), `China` (2), `USGovernment` (3) | Azure cloud environment |
