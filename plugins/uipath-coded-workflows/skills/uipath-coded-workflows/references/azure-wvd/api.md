# Azure Windows Virtual Desktop — Full API Reference

Complete reference for `IAzureWindowsVirtualDesktopService` accessed via the `azureWVD` service accessor and all sub-services. For general info see [azure-wvd.md](azure-wvd.md).

**Note:** All methods are **asynchronous** (return `Task` or `Task<T>`) and should be awaited.

---

## Host Pools

Sub-service: `IHostPoolService` — obtained via `azureWVD.HostPoolService(clientProvider)`.

### GetHostPool

Gets a host pool by name.

```csharp
Task<WVDHostPool> GetHostPool(string hostPoolName, string resourceGroupName);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPoolName` | `string` | Name of the host pool |
| `resourceGroupName` | `string` | Resource group name |

**Returns:** `WVDHostPool` — the host pool details.

### CreateHostPool

Creates a new host pool.

```csharp
Task<WVDHostPool> CreateHostPool(HostPoolCreateParams createParams);
```

| Parameter | Type | Description |
|---|---|---|
| `createParams` | `HostPoolCreateParams` | Creation parameters (name, resource group, region, type, etc.) |

**Returns:** `WVDHostPool` — the created host pool.

### UpdateHostPool

Updates an existing host pool's properties.

```csharp
Task UpdateHostPool(WVDHostPool hostPool, HostPoolUpdateParams properties);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPool` | `WVDHostPool` | The host pool to update |
| `properties` | `HostPoolUpdateParams` | Properties to update |

### DeleteHostPool

Deletes a host pool.

```csharp
Task DeleteHostPool(WVDHostPool hostPool);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPool` | `WVDHostPool` | The host pool to delete |

### ListHostPools

Lists host pools in a resource group. Supports pagination.

```csharp
Task<HostPoolList> ListHostPools(string resourceGroup, string token);
```

| Parameter | Type | Description |
|---|---|---|
| `resourceGroup` | `string` | Resource group name |
| `token` | `string` | Pagination skip token (`null` for first page) |

**Returns:** `HostPoolList` — paginated list with `Value` and `NextLink`.

### AddVMToHostPool

Adds an existing Azure VM to a host pool as a session host by joining it to the domain and installing the WVD agent.

```csharp
Task<WVDSessionHost> AddVMToHostPool(WVDHostPool hostPool, string vmName, string vmResourceGroupName,
    string domainName, string domainOU, string domainUser, SecureString domainPassword,
    bool waitForCompletion);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPool` | `WVDHostPool` | Target host pool |
| `vmName` | `string` | Name of the Azure VM |
| `vmResourceGroupName` | `string` | Resource group of the VM |
| `domainName` | `string` | Active Directory domain name |
| `domainOU` | `string` | Organizational unit for domain join |
| `domainUser` | `string` | Domain admin username |
| `domainPassword` | `SecureString` | Domain admin password |
| `waitForCompletion` | `bool` | Whether to wait for the operation to complete |

**Returns:** `WVDSessionHost` — the new session host.

---

## Session Hosts

Sub-service: `ISessionHostService` — obtained via `azureWVD.SessionHostService(clientProvider)`.

### GetSessionHost

Gets a session host by name.

```csharp
Task<WVDSessionHost> GetSessionHost(WVDHostPool hostPool, string sessionHostName);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPool` | `WVDHostPool` | The parent host pool |
| `sessionHostName` | `string` | Session host name |

**Returns:** `WVDSessionHost` — the session host details.

### UpdateSessionHost

Updates a session host's settings.

```csharp
Task UpdateSessionHost(WVDSessionHost sessionHost, bool? allowNewSession, string assignedUser);
```

| Parameter | Type | Description |
|---|---|---|
| `sessionHost` | `WVDSessionHost` | The session host to update |
| `allowNewSession` | `bool?` | Whether to allow new sessions (`null` to keep current) |
| `assignedUser` | `string` | Assigned user for personal pools (`null` to keep current) |

### DeleteSessionHost

Deletes a session host from its host pool.

```csharp
Task DeleteSessionHost(WVDSessionHost sessionHost);
```

| Parameter | Type | Description |
|---|---|---|
| `sessionHost` | `WVDSessionHost` | The session host to delete |

### ListSessionHosts

Lists session hosts in a host pool. Supports pagination.

```csharp
Task<SessionHostList> ListSessionHosts(WVDHostPool hostPool, string token);
```

| Parameter | Type | Description |
|---|---|---|
| `hostPool` | `WVDHostPool` | The parent host pool |
| `token` | `string` | Pagination skip token (`null` for first page) |

**Returns:** `SessionHostList` — paginated list with `Value` and `NextLink`.

---

## User Sessions

Sub-service: `IUserSessionService` — obtained via `azureWVD.UserSessionService(clientProvider)`.

### SendMessageToUserSession

Sends a message to a user session.

```csharp
Task SendMessageToUserSession(WVDUserSession userSession, string messageTitle, string messageBody);
```

| Parameter | Type | Description |
|---|---|---|
| `userSession` | `WVDUserSession` | The target user session |
| `messageTitle` | `string` | Message title |
| `messageBody` | `string` | Message body |

### DisconnectUserSession

Disconnects a user session.

```csharp
Task DisconnectUserSession(WVDUserSession userSession);
```

| Parameter | Type | Description |
|---|---|---|
| `userSession` | `WVDUserSession` | The user session to disconnect |

### DeleteUserSession

Deletes (logs off) a user session.

```csharp
Task DeleteUserSession(WVDUserSession userSession, bool? force);
```

| Parameter | Type | Description |
|---|---|---|
| `userSession` | `WVDUserSession` | The user session to delete |
| `force` | `bool?` | Force logoff (`true` to force, `null`/`false` for graceful) |

### ListUserSessions

Lists user sessions on a session host. Supports pagination.

```csharp
Task<UserSessionList> ListUserSessions(WVDSessionHost sessionHost, string skipToken);
```

| Parameter | Type | Description |
|---|---|---|
| `sessionHost` | `WVDSessionHost` | The parent session host |
| `skipToken` | `string` | Pagination skip token (`null` for first page) |

**Returns:** `UserSessionList` — paginated list with `Value` and `NextLink`.

---

## Workspaces

Sub-service: `IWorkspaceService` — obtained via `azureWVD.WorkspaceService(clientProvider)`.

### CreateWorkspace

Creates a new workspace.

```csharp
Task<WVDWorkspace> CreateWorkspace(WorkspaceCreateParams createParams);
```

| Parameter | Type | Description |
|---|---|---|
| `createParams` | `WorkspaceCreateParams` | Creation parameters (name, resource group, region, etc.) |

**Returns:** `WVDWorkspace` — the created workspace.

### GetWorkspace

Gets a workspace by name.

```csharp
Task<WVDWorkspace> GetWorkspace(string wrksName, string resourceGroupName);
```

| Parameter | Type | Description |
|---|---|---|
| `wrksName` | `string` | Workspace name |
| `resourceGroupName` | `string` | Resource group name |

**Returns:** `WVDWorkspace` — the workspace details.

### UpdateWorkspace

Updates an existing workspace.

```csharp
Task UpdateWorkspace(WorkspaceUpdateParams updateParams);
```

| Parameter | Type | Description |
|---|---|---|
| `updateParams` | `WorkspaceUpdateParams` | Update parameters |

### DeleteWorkspace

Deletes a workspace.

```csharp
Task DeleteWorkspace(WVDWorkspace wrks);
```

| Parameter | Type | Description |
|---|---|---|
| `wrks` | `WVDWorkspace` | The workspace to delete |

### ListWorkspaces

Lists workspaces in a resource group. Supports pagination.

```csharp
Task<WorkspaceList> ListWorkspaces(string resourceGroup, string token);
```

| Parameter | Type | Description |
|---|---|---|
| `resourceGroup` | `string` | Resource group name |
| `token` | `string` | Pagination skip token (`null` for first page) |

**Returns:** `WorkspaceList` — paginated list with `Value` and `NextLink`.

---

## Application Groups

Sub-service: `IApplicationGroupService` — obtained via `azureWVD.ApplicationGroupService(clientProvider)`.

### GetApplicationGroup

Gets an application group by name.

```csharp
Task<WVDApplicationGroup> GetApplicationGroup(string resourceGroupName, string applicationGroupName);
```

| Parameter | Type | Description |
|---|---|---|
| `resourceGroupName` | `string` | Resource group name |
| `applicationGroupName` | `string` | Application group name |

**Returns:** `WVDApplicationGroup` — the application group details.

### ListApplicationGroups

Lists application groups in a resource group. Supports filtering and pagination.

```csharp
Task<ApplicationGroupList> ListApplicationGroups(string resourceGroupName, string filter, string skipToken);
```

| Parameter | Type | Description |
|---|---|---|
| `resourceGroupName` | `string` | Resource group name |
| `filter` | `string` | OData filter expression (e.g., filter by host pool) |
| `skipToken` | `string` | Pagination skip token (`null` for first page) |

**Returns:** `ApplicationGroupList` — paginated list with `Value` and `NextLink`.

---

## Role Assignments

Sub-service: `IRoleAssignmentService` — obtained via `azureWVD.RoleAssignmentService(clientProvider)`.

### AssignObjectsToApplicationGroup

Assigns users and/or groups to an application group (grants the Desktop Virtualization User role).

```csharp
Task AssignObjectsToApplicationGroup(WVDApplicationGroup appGroup, string[] usersAndGroupsIds);
```

| Parameter | Type | Description |
|---|---|---|
| `appGroup` | `WVDApplicationGroup` | The target application group |
| `usersAndGroupsIds` | `string[]` | Azure AD object IDs of users/groups to assign |

### RemoveObjectsFromApplicationGroup

Removes users and/or groups from an application group (removes the Desktop Virtualization User role).

```csharp
Task RemoveObjectsFromApplicationGroup(WVDApplicationGroup appGroup, string[] usersAndGroupsIds);
```

| Parameter | Type | Description |
|---|---|---|
| `appGroup` | `WVDApplicationGroup` | The target application group |
| `usersAndGroupsIds` | `string[]` | Azure AD object IDs of users/groups to remove |
