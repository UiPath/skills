# NetIQ eDirectory — Full API Reference

Complete reference for `INetIQeDirectoryService` accessed via the `netiq` service accessor and all sub-services. For general info see [netiq-edirectory.md](netiq-edirectory.md).

**Note:** Most methods are **asynchronous** (return `Task` or `Task<T>`) and should be awaited. The `Connection` parameter has **no default** and must always be specified.

---

## Objects

Sub-service: `INetIQeDirectoryObjectService` — obtained via `netiq.NetIQeDirectoryObjectService(clientProvider)`.

### GetDistinguishedName

Resolves a SAM account name to a distinguished name.

```csharp
Task<string> GetDistinguishedName(string SAMAccountName, ConnectionWithoutAuto connection);
```

| Parameter | Type | Description |
|---|---|---|
| `SAMAccountName` | `string` | SAM account name to look up |
| `connection` | `ConnectionWithoutAuto` | Which connection to use |

**Returns:** `string` — the distinguished name.

### GetObjectProperties

Gets all properties of a directory object. **This method is synchronous.**

```csharp
Dictionary<string, object> GetObjectProperties(string distinguishedName, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | Object's DN |
| `connection` | `Connection` | Which connection to use |

**Returns:** `Dictionary<string, object>` — all property name-value pairs.

### FilterObjects

Searches for directory objects using an LDAP filter. Returns matching distinguished names.

```csharp
Task<string[]> FilterObjects(string ldapFilter, string locationDn, ConnectionWithoutAuto connection);
```

| Parameter | Type | Description |
|---|---|---|
| `ldapFilter` | `string` | LDAP filter string (e.g., `"(&(objectClass=user)(mail=*@corp.com))"`) |
| `locationDn` | `string` | Base DN to search from |
| `connection` | `ConnectionWithoutAuto` | Which connection to use |

**Returns:** `string[]` — array of distinguished names matching the filter.

### UpdateProperties

Updates properties on a directory object.

```csharp
Task UpdateProperties(string distinguishedName, Dictionary<string, object> dictionary, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | Object's DN |
| `dictionary` | `Dictionary<string, object>` | Properties to set (name-value pairs) |
| `connection` | `Connection` | Which connection to use |

### DeleteObject

Deletes a directory object.

```csharp
Task DeleteObject(string distinguishedName, bool recursive, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | Object's DN |
| `recursive` | `bool` | Delete child objects |
| `connection` | `Connection` | Which connection to use |

### MoveObject

Moves a directory object to a new parent container.

```csharp
Task MoveObject(string objectDistinguishedName, string newParentDistinguishedName, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `objectDistinguishedName` | `string` | DN of the object to move |
| `newParentDistinguishedName` | `string` | DN of the new parent container |
| `connection` | `Connection` | Which connection to use |

### RenameObject

Renames a directory object (changes its CN).

```csharp
Task RenameObject(string objectDistinguishedName, string newCommonName, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `objectDistinguishedName` | `string` | Object's DN |
| `newCommonName` | `string` | New common name |
| `connection` | `Connection` | Which connection to use |

### AddObjectToGroup

Adds an object to a group.

```csharp
Task AddObjectToGroup(string objectDistinguishedName, string groupDistinguishedName,
    Connection objectConnection, Connection groupConnection);
```

| Parameter | Type | Description |
|---|---|---|
| `objectDistinguishedName` | `string` | DN of the object to add |
| `groupDistinguishedName` | `string` | DN of the target group |
| `objectConnection` | `Connection` | Connection for the object |
| `groupConnection` | `Connection` | Connection for the group |

### RemoveObjectFromGroup

Removes an object from a group.

```csharp
Task RemoveObjectFromGroup(string objectDistinguishedName, string groupDistinguishedName,
    Connection objectConnection, Connection groupConnection);
```

| Parameter | Type | Description |
|---|---|---|
| `objectDistinguishedName` | `string` | DN of the object to remove |
| `groupDistinguishedName` | `string` | DN of the group |
| `objectConnection` | `Connection` | Connection for the object |
| `groupConnection` | `Connection` | Connection for the group |

### IsObjectMemberOfGroup

Checks if an object is a member of a group.

```csharp
Task<bool> IsObjectMemberOfGroup(string objectDistinguishedName, string groupDistinguishedName,
    Connection objConnection, Connection grpConnection, bool recurseIntoChildGroups);
```

| Parameter | Type | Description |
|---|---|---|
| `objectDistinguishedName` | `string` | DN of the object to check |
| `groupDistinguishedName` | `string` | DN of the group |
| `objConnection` | `Connection` | Connection for the object |
| `grpConnection` | `Connection` | Connection for the group |
| `recurseIntoChildGroups` | `bool` | Check nested group membership |

---

## Users

Sub-service: `INetIQeDirectoryUserService` — obtained via `netiq.NetIQeDirectoryUserService(clientProvider)`.

### CreateUser

Creates a new user. Returns the distinguished name.

```csharp
Task<string> CreateUser(string commonName, string sAMAccountName, string password, string locationDn,
    Dictionary<string, object> properties, bool enabled, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `commonName` | `string` | Common name for the user |
| `sAMAccountName` | `string` | SAM account name |
| `password` | `string` | Initial password |
| `locationDn` | `string` | DN of the parent OU/container |
| `properties` | `Dictionary<string, object>` | Additional LDAP properties |
| `enabled` | `bool` | Whether the account is enabled |
| `connection` | `Connection` | Which connection to use |

**Returns:** `string` — distinguished name of the created user.

### GetUserStatus

Gets the lock status and active status of a user.

```csharp
Task<(LockStatus, ActiveStatus)> GetUserStatus(string distinguishedName, Connection connection);
```

**Returns:** `(LockStatus lockStatus, ActiveStatus activeStatus)`.

### SetUserStatus

Sets the status of a user (enable, disable, or unlock).

```csharp
Task SetUserStatus(string distinguishedName, UserStatus status, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | User's DN |
| `status` | `UserStatus` | `Disabled`, `Enabled`, or `Unlocked` |
| `connection` | `Connection` | Which connection to use |

### ChangeUserPassword

Changes a user's password.

```csharp
Task ChangeUserPassword(string distinguishedName, string password, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | User's DN |
| `password` | `string` | New password |
| `connection` | `Connection` | Which connection to use |

### ForcePasswordChange

Forces the user to change their password at next logon.

```csharp
Task ForcePasswordChange(string distinguishedName, Connection connection);
```

### GetPasswordExpirationDate

Gets the date when the user's password expires. Returns `null` if never.

```csharp
Task<DateTime?> GetPasswordExpirationDate(string distinguishedName, Connection connection);
```

### GetUserExpirationDate

Gets the user's account expiration date. Returns `null` if never.

```csharp
Task<DateTime?> GetUserExpirationDate(string distinguishedName, Connection connection);
```

### SetUserExpirationDate

Sets the user's account expiration date.

```csharp
Task SetUserExpirationDate(string distinguishedName, DateTime expirationDate, Connection connection);
```

### GetUserGroups

Gets the distinguished names of all groups the user belongs to.

```csharp
Task<string[]> GetUserGroups(string userDistinguishedName, Connection connection);
```

**Returns:** `string[]` — array of group distinguished names.

### ValidateUserCredentials

Validates a user's credentials. Returns `true` if valid.

```csharp
Task<bool> ValidateUserCredentials(ValidateCredentialsUserFilter user, string value,
    string password, ConnectionWithoutAuto connection);
```

| Parameter | Type | Description |
|---|---|---|
| `user` | `ValidateCredentialsUserFilter` | How to identify the user: `SAMAccountName`, `UserPrincipalName`, or `DistinguishedName` |
| `value` | `string` | The user identifier value |
| `password` | `string` | Password to validate |
| `connection` | `ConnectionWithoutAuto` | Which connection to use |

### AddUserToGroup

Adds a user to a group.

```csharp
Task AddUserToGroup(string userDistinguishedName, string groupDistinguishedName,
    Connection userConnection, Connection groupConnection);
```

| Parameter | Type | Description |
|---|---|---|
| `userDistinguishedName` | `string` | User's DN |
| `groupDistinguishedName` | `string` | Group's DN |
| `userConnection` | `Connection` | Connection for the user |
| `groupConnection` | `Connection` | Connection for the group |

### RemoveUserFromGroup

Removes a user from a group.

```csharp
Task RemoveUserFromGroup(string userDistinguishedName, string groupDistinguishedName,
    Connection userConnection, Connection groupConnection);
```

### DeleteUser

Deletes a user.

```csharp
Task DeleteUser(string distinguishedName, bool recursive, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | User's DN |
| `recursive` | `bool` | Delete child objects |
| `connection` | `Connection` | Which connection to use |

---

## Computers

Sub-service: `INetIQeDirectoryComputerService` — obtained via `netiq.NetIQeDirectoryComputerService(clientProvider)`.

### CreateComputer

Creates a new computer account. Returns the distinguished name.

```csharp
Task<string> CreateComputer(string commonName, string sAMAccountName, string locationDn,
    Dictionary<string, object> properties, bool enabled, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `commonName` | `string` | Common name for the computer |
| `sAMAccountName` | `string` | SAM account name |
| `locationDn` | `string` | DN of the parent OU/container |
| `properties` | `Dictionary<string, object>` | Additional LDAP properties |
| `enabled` | `bool` | Whether the account is enabled |
| `connection` | `Connection` | Which connection to use |

**Returns:** `string` — distinguished name of the created computer.

### GetComputerStatus

Gets the enabled/disabled status of a computer.

```csharp
Task<ActiveStatus> GetComputerStatus(string distinguishedName, Connection connection);
```

**Returns:** `ActiveStatus` — `Enabled` or `Disabled`.

### SetComputerStatus

Sets the enabled/disabled status of a computer.

```csharp
Task SetComputerStatus(string distinguishedName, ActiveStatus status, Connection connection);
```

### AddComputerToGroup

Adds a computer to a group.

```csharp
Task AddComputerToGroup(string computerDistinguishedName, string groupDistinguishedName,
    Connection computerConnection, Connection groupConnection);
```

### RemoveComputerFromGroup

Removes a computer from a group.

```csharp
Task RemoveComputerFromGroup(string computerDistinguishedName, string groupDistinguishedName,
    Connection computerConnection, Connection groupConnection);
```

### DeleteComputer

Deletes a computer.

```csharp
Task DeleteComputer(string distinguishedName, bool recursive, Connection connection);
```

---

## Groups

Sub-service: `INetIQeDirectoryGroupService` — obtained via `netiq.NetIQeDirectoryGroupService(clientProvider)`.

### CreateGroup

Creates a new group. Returns the distinguished name.

```csharp
Task<string> CreateGroup(string commonName, string sAMAccountName, string locationDn,
    Dictionary<string, object> properties, GroupType type, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `commonName` | `string` | Common name for the group |
| `sAMAccountName` | `string` | SAM account name |
| `locationDn` | `string` | DN of the parent OU/container |
| `properties` | `Dictionary<string, object>` | Additional LDAP properties |
| `type` | `GroupType` | Group type and scope (e.g., `GlobalSecurity`) |
| `connection` | `Connection` | Which connection to use |

**Returns:** `string` — distinguished name of the created group.

**Note:** `GroupType` is in the `UiPath.NetIQeDirectory.Enums` namespace.

### GetMembersDN

Gets the distinguished names of members of a specific type in a group.

```csharp
Task<string[]> GetMembersDN(string distinguishedName, EntryType entryType, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | Group's DN |
| `entryType` | `EntryType` | Type of members to list (`User`, `Group`, `Computer`) |
| `connection` | `Connection` | Which connection to use |

**Returns:** `string[]` — array of distinguished names.

### AddGroupToGroup

Adds a group as a member of another group (nesting).

```csharp
Task AddGroupToGroup(string groupDistinguishedName, string parentGroupDistinguishedName,
    Connection groupConnection, Connection parentGroupConnection);
```

| Parameter | Type | Description |
|---|---|---|
| `groupDistinguishedName` | `string` | DN of the child group |
| `parentGroupDistinguishedName` | `string` | DN of the parent group |
| `groupConnection` | `Connection` | Connection for the child group |
| `parentGroupConnection` | `Connection` | Connection for the parent group |

### RemoveGroupFromGroup

Removes a group from another group.

```csharp
Task RemoveGroupFromGroup(string groupDistinguishedName, string parentGroupDistinguishedName,
    Connection groupConnection, Connection parentGroupConnection);
```

### DeleteGroup

Deletes a group.

```csharp
Task DeleteGroup(string distinguishedName, bool recursive, Connection connection);
```

---

## Organizational Units

Sub-service: `INetIQeDirectoryOrganizationService` — obtained via `netiq.NetIQeDirectoryOrganizationService(clientProvider)`.

### CreateOrganizationalUnit

Creates a new OU. Returns the distinguished name.

```csharp
Task<string> CreateOrganizationalUnit(string organizationUnitName, string locationDn,
    Dictionary<string, object> properties, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `organizationUnitName` | `string` | Name of the OU |
| `locationDn` | `string` | DN of the parent container |
| `properties` | `Dictionary<string, object>` | Additional LDAP properties |
| `connection` | `Connection` | Which connection to use |

**Returns:** `string` — distinguished name of the created OU.

### DeleteOrganizationalUnit

Deletes an OU.

```csharp
Task DeleteOrganizationalUnit(string distinguishedName, bool recursive, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `distinguishedName` | `string` | OU's DN |
| `recursive` | `bool` | Delete child objects |
| `connection` | `Connection` | Which connection to use |
