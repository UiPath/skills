# Active Directory Domain Services — Full API Reference

Complete reference for `IActiveDirectoryDomainServicesService` accessed via the `activeDirectoryDomainServices` service accessor and all sub-services. For general info see [active-directory.md](active-directory.md).

**Note:** All methods in this API are **synchronous** (not async). They return values directly, not `Task<T>`.

---

## Users

Sub-service: `IActiveDirectoryUserService` — obtained via `activeDirectoryDomainServices.ActiveDirectoryUserService(clientProvider)`.

### CreateUser

Creates a new AD user account. Returns the distinguished name (DN) of the created user.

```csharp
string CreateUser(string cn, string sAMAccountName, string password, string locationDn,
    IDictionary<string, object> properties, bool enabled, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cn` | `string` | — | Common name for the user |
| `sAMAccountName` | `string` | — | SAM account name (pre-Windows 2000 logon) |
| `password` | `string` | — | Initial password |
| `locationDn` | `string` | — | DN of the parent OU/container (e.g., `"OU=Users,DC=corp,DC=com"`) |
| `properties` | `IDictionary<string, object>` | — | Additional AD properties (e.g., `mail`, `givenName`, `sn`, `userPrincipalName`) |
| `enabled` | `bool` | — | Whether the account is enabled |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `string` — the distinguished name of the created user.

### GetUserStatus

Gets the lock status and active status of a user.

```csharp
(LockStatus, ActiveStatus) GetUserStatus(string distinguishedName, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `(LockStatus lockStatus, ActiveStatus activeStatus)` — tuple indicating whether the account is locked and enabled/disabled.

### SetUserStatus

Sets the status of a user (enable, disable, or unlock).

```csharp
void SetUserStatus(string distinguishedName, UserStatus status, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `status` | `UserStatus` | — | `Disabled`, `Enabled`, or `Unlocked` |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### ForcePasswordChange

Forces the user to change their password at next logon.

```csharp
void ForcePasswordChange(string distinguishedName, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### ChangeUserPassword

Changes a user's password.

```csharp
void ChangeUserPassword(string distinguishedName, string password, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `password` | `string` | — | New password |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### GetUserGroups

Gets the distinguished names of all groups the user belongs to.

```csharp
string[] GetUserGroups(string distinguishedName, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `string[]` — array of group distinguished names.

### ValidateUserCredentials

Validates a user's credentials against AD. Returns `true` if valid.

```csharp
bool ValidateUserCredentials(ValidateCredentialsUserFilter propertyFilter, string filterValue,
    string password, ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `propertyFilter` | `ValidateCredentialsUserFilter` | — | How to identify the user: `SAMAccountName`, `UserPrincipalName`, or `DistinguishedName` |
| `filterValue` | `string` | — | The user identifier value |
| `password` | `string` | — | Password to validate |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |

### GetUserPasswordExpirationDate

Gets the date when the user's password expires. Returns `null` if the password never expires.

```csharp
DateTime? GetUserPasswordExpirationDate(string distinguishedName, Connection connection = Connection.Primary);
```

### GetUserExpirationDate

Gets the user's account expiration date. Returns `null` if the account never expires.

```csharp
DateTime? GetUserExpirationDate(string distinguishedName, Connection connection = Connection.Primary);
```

### SetUserExpirationDate

Sets the user's account expiration date.

```csharp
void SetUserExpirationDate(string distinguishedName, DateTime expirationDate, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `expirationDate` | `DateTime` | — | New expiration date |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### DeleteUser

Deletes a user account.

```csharp
void DeleteUser(string distinguishedName, bool recursive, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | User's DN |
| `recursive` | `bool` | — | Whether to delete child objects |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

---

## Computers

Sub-service: `IActiveDirectoryComputerService` — obtained via `activeDirectoryDomainServices.ActiveDirectoryComputerService(clientProvider)`.

### CreateComputer

Creates a new computer account. Returns the distinguished name.

```csharp
string CreateComputer(string cn, string accountName, string locationDn,
    Dictionary<string, object> properties, bool enabled, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cn` | `string` | — | Common name for the computer |
| `accountName` | `string` | — | SAM account name |
| `locationDn` | `string` | — | DN of the parent OU/container |
| `properties` | `Dictionary<string, object>` | — | Additional AD properties |
| `enabled` | `bool` | — | Whether the account is enabled |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `string` — distinguished name of the created computer.

### GetComputerStatus

Gets the enabled/disabled status of a computer account.

```csharp
ActiveStatus GetComputerStatus(string distinguishedName, Connection connection = Connection.Primary);
```

**Returns:** `ActiveStatus` — `Enabled` or `Disabled`.

### SetComputerStatus

Sets the enabled/disabled status of a computer account.

```csharp
void SetComputerStatus(string distinguishedName, ActiveStatus status, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | Computer's DN |
| `status` | `ActiveStatus` | — | `Enabled` or `Disabled` |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### JoinComputerToDomain

Joins a computer to the AD domain.

```csharp
void JoinComputerToDomain(string computerName, bool createComputerAccount, string locationDn,
    bool rejoin, string localComputerAccount, SecureString localComputerAccountPassword,
    ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `computerName` | `string` | — | Computer name to join |
| `createComputerAccount` | `bool` | — | Create the computer account if it doesn't exist |
| `locationDn` | `string` | — | DN of the OU to place the computer account |
| `rejoin` | `bool` | — | Rejoin if already joined |
| `localComputerAccount` | `string` | — | Local admin account on the computer |
| `localComputerAccountPassword` | `SecureString` | — | Local admin password |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |

### UnjoinComputerFromDomain

Removes a computer from the AD domain.

```csharp
void UnjoinComputerFromDomain(string computerName, bool disableComputerAccount,
    string localComputerAccount, SecureString localComputerAccountPassword,
    ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `computerName` | `string` | — | Computer name to unjoin |
| `disableComputerAccount` | `bool` | — | Disable the computer account after unjoining |
| `localComputerAccount` | `string` | — | Local admin account |
| `localComputerAccountPassword` | `SecureString` | — | Local admin password |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |

---

## Groups

Sub-service: `IActiveDirectoryGroupService` — obtained via `activeDirectoryDomainServices.ActiveDirectoryGroupService(clientProvider)`.

### CreateGroup

Creates a new AD group. Returns the distinguished name.

```csharp
string CreateGroup(string cn, string sAMAccountName, string locationDn, GroupType type,
    IDictionary<string, object> properties, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cn` | `string` | — | Common name for the group |
| `sAMAccountName` | `string` | — | SAM account name |
| `locationDn` | `string` | — | DN of the parent OU/container |
| `type` | `GroupType` | — | Group type and scope (e.g., `GlobalSecurity`, `UniversalDistribution`) |
| `properties` | `IDictionary<string, object>` | — | Additional AD properties |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `string` — distinguished name of the created group.

### AddObjectToGroup

Adds an object (user, computer, or group) to a group.

```csharp
void AddObjectToGroup(string objectDn, EntryType objectType, string groupDn,
    Connection objConnection = Connection.Primary, Connection grpConnection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `objectDn` | `string` | — | DN of the object to add |
| `objectType` | `EntryType` | — | Type of the object (`User`, `Group`, `Computer`) |
| `groupDn` | `string` | — | DN of the target group |
| `objConnection` | `Connection` | `Primary` | Connection for the object |
| `grpConnection` | `Connection` | `Primary` | Connection for the group |

### RemoveObjectFromGroup

Removes an object from a group.

```csharp
void RemoveObjectFromGroup(string objectDn, EntryType objectType, string groupDn,
    Connection objConnection = Connection.Primary, Connection grpConnection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `objectDn` | `string` | — | DN of the object to remove |
| `objectType` | `EntryType` | — | Type of the object |
| `groupDn` | `string` | — | DN of the group |
| `objConnection` | `Connection` | `Primary` | Connection for the object |
| `grpConnection` | `Connection` | `Primary` | Connection for the group |

### GetObjectsInGroup

Gets the distinguished names of all objects of a specific type in a group.

```csharp
string[] GetObjectsInGroup(string groupDn, EntryType objectType, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `groupDn` | `string` | — | DN of the group |
| `objectType` | `EntryType` | — | Type of objects to list (`User`, `Group`, `Computer`) |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `string[]` — array of distinguished names.

---

## Organizational Units

Sub-service: `IActiveDirectoryOrganizationUnitService` — obtained via `activeDirectoryDomainServices.ActiveDirectoryOrganizationUnitService(clientProvider)`.

### CreateOrganizationalUnit

Creates a new OU. Returns the distinguished name.

```csharp
string CreateOrganizationalUnit(string cn, string locationDn,
    Dictionary<string, object> properties, Connection connection);
```

| Parameter | Type | Description |
|---|---|---|
| `cn` | `string` | Name of the OU |
| `locationDn` | `string` | DN of the parent container |
| `properties` | `Dictionary<string, object>` | Additional AD properties |
| `connection` | `Connection` | Which AD connection to use (**no default — must be specified**) |

**Returns:** `string` — distinguished name of the created OU.

### DeleteOrganizationalUnit

Deletes an OU or other entry.

```csharp
void DeleteOrganizationalUnit(string distinguishedName, EntryType type, bool recursive,
    Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | DN of the entry to delete |
| `type` | `EntryType` | — | Type of the entry |
| `recursive` | `bool` | — | Delete child objects |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

---

## Common Operations

Sub-service: `IActiveDirectoryCommonService` — obtained via `activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider)`.

### GetDistinguishedName

Resolves a SAM account name to a distinguished name.

```csharp
string GetDistinguishedName(string sAMAccountName, ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sAMAccountName` | `string` | — | SAM account name to look up |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |

**Returns:** `string` — the distinguished name.

### GetObjectProperties

Gets all properties of an AD object.

```csharp
Dictionary<string, object> GetObjectProperties(string distinguishedName, Connection connection = Connection.Primary);
```

**Returns:** `Dictionary<string, object>` — all property name-value pairs.

### GetObjectProperty

Gets a single property value of an AD object.

```csharp
object GetObjectProperty(string distinguishedName, string propertyName, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | Object's DN |
| `propertyName` | `string` | — | AD property name (e.g., `"mail"`, `"givenName"`) |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

**Returns:** `object` — the property value.

### FilterObjectsByProperty

Searches for AD objects matching a property filter. Returns matching distinguished names.

```csharp
string[] FilterObjectsByProperty(FilterProperty property,
    ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary,
    string objectClass = null, string objectCategory = null, string locationDn = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `property` | `FilterProperty` | — | Filter criteria (name, value, relation) |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |
| `objectClass` | `string` | `null` | Filter by objectClass (e.g., `"user"`, `"group"`) |
| `objectCategory` | `string` | `null` | Filter by objectCategory (e.g., `"person"`, `"computer"`) |
| `locationDn` | `string` | `null` | Restrict search to this OU/container DN |

**Returns:** `string[]` — array of distinguished names matching the filter.

**FilterProperty construction:**

```csharp
var filter = new FilterProperty("mail", "john@corp.com", Relation.EqualTo);
var filter = new FilterProperty("sAMAccountName", "john*", Relation.EqualTo); // wildcard
var filter = new FilterProperty("whenCreated", "20240101000000.0Z", Relation.GreaterThanOrEqualTo);
```

### FilterObjectsByLDAPFilter

Searches for AD objects using a raw LDAP filter string. Returns matching distinguished names.

```csharp
string[] FilterObjectsByLDAPFilter(string filter,
    ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary, string locationDn = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filter` | `string` | — | Raw LDAP filter (e.g., `"(&(objectClass=user)(mail=*@corp.com))"`) |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |
| `locationDn` | `string` | `null` | Restrict search to this DN |

**Returns:** `string[]` — array of distinguished names.

### EntryExistsBySAMAccountName

Checks if an AD entry exists by SAM account name.

```csharp
bool EntryExistsBySAMAccountName(string sAMAccountName, EntryType type,
    string locationDn = null, ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sAMAccountName` | `string` | — | SAM account name |
| `type` | `EntryType` | — | Entry type to search for |
| `locationDn` | `string` | `null` | Restrict to this DN |
| `connection` | `ConnectionWithoutAuto` | `Primary` | Which AD connection to use |

### EntryExistsByUPN

Checks if a user exists by User Principal Name.

```csharp
bool EntryExistsByUPN(string userPrincipalName, EntryType type,
    string locationDn = null, ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

### EntryExistsByCN

Checks if an entry exists by Common Name.

```csharp
bool EntryExistsByCN(string commonName, EntryType type,
    string locationDn = null, ConnectionWithoutAuto connection = ConnectionWithoutAuto.Primary);
```

### DeleteEntry

Deletes any AD entry by distinguished name.

```csharp
void DeleteEntry(string distinguishedName, EntryType type, bool recursive, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | DN of the entry to delete |
| `type` | `EntryType` | — | Entry type |
| `recursive` | `bool` | — | Delete child objects |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### UpdateProperties

Updates properties on an AD object.

```csharp
void UpdateProperties(string distinguishedName, Dictionary<string, object> properties, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | Object's DN |
| `properties` | `Dictionary<string, object>` | — | Properties to set (name-value pairs) |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### IsObjectMemberOfGroup

Checks if an object is a member of a group.

```csharp
bool IsObjectMemberOfGroup(string objectDistinguishedName, string groupDistinguishedName,
    bool recurseIntoChildGroups,
    Connection objConnection = Connection.Primary, Connection grpConnection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `objectDistinguishedName` | `string` | — | DN of the object to check |
| `groupDistinguishedName` | `string` | — | DN of the group |
| `recurseIntoChildGroups` | `bool` | — | Check nested group membership |
| `objConnection` | `Connection` | `Primary` | Connection for the object |
| `grpConnection` | `Connection` | `Primary` | Connection for the group |

### MoveObject

Moves an AD object to a new parent OU/container.

```csharp
void MoveObject(string objectDistinguishedName, string newParentDistinguishedName,
    Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `objectDistinguishedName` | `string` | — | DN of the object to move |
| `newParentDistinguishedName` | `string` | — | DN of the new parent container |
| `connection` | `Connection` | `Primary` | Which AD connection to use |

### RenameObject

Renames an AD object (changes its CN).

```csharp
void RenameObject(string distinguishedName, string newName, Connection connection = Connection.Primary);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `distinguishedName` | `string` | — | Object's DN |
| `newName` | `string` | — | New common name |
| `connection` | `Connection` | `Primary` | Which AD connection to use |
