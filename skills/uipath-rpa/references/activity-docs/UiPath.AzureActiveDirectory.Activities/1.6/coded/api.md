# Azure Active Directory API Reference

Complete API reference for the `azureAD` service from `UiPath.AzureActiveDirectory.Activities` package.

**Required package:** `"UiPath.AzureActiveDirectory.Activities": "[1.6.3]"`

**Auto-imported namespaces:** `UiPath.AzureActiveDirectory.Activities.API`, `UiPath.AzureActiveDirectory.Activities.API.Util`, `UiPath.AzureActiveDirectory.Contracts`, `UiPath.AzureActiveDirectory.Contracts.Users`, `UiPath.AzureActiveDirectory.Contracts.Groups`, `UiPath.AzureActiveDirectory.Contracts.Groups.LifecyclePolicies`, `UiPath.AzureActiveDirectory.Contracts.Roles`, `UiPath.AzureActiveDirectory.Contracts.Devices`, `UiPath.Core`

---

## IGraphServiceClientProvider

Creates authenticated Microsoft Graph clients. Access via `graphServiceClientProvider` in coded workflows.

```csharp
public interface IGraphServiceClientProvider
{
    GraphServiceClient CreateWithAppCredentials(string tenantId, string clientId, SecureString clientSecret);
    GraphServiceClient CreateWithUserCredentials(string tenantId, string clientId, string username, SecureString password);
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenantId` | `string` | Azure AD tenant ID |
| `clientId` | `string` | Azure AD application (client) ID |
| `clientSecret` | `SecureString` | Application client secret |
| `username` | `string` | User principal name for delegated auth |
| `password` | `SecureString` | User password for delegated auth |

---

## IAzureADService

Root service accessor. Access via `azureAD` in coded workflows.

```csharp
public interface IAzureADService
{
    IAzureADGroupService AzureADGroupService(GraphServiceClient client);
    IAzureADLifecyclePolicyService AzureADLifecyclePolicyService(GraphServiceClient client);
    IAzureADRoleService AzureADRoleService(GraphServiceClient client);
    IAzureADUserService AzureADUserService(GraphServiceClient client);
}
```

---

## IAzureADUserService

Access: `azureAD.AzureADUserService(client)`

### Create User

```csharp
Task<UserInfo> CreateUserAsync(
    bool enabled,
    string displayName,
    string mailNickname,
    string userPrincipalName,
    string firstName,
    string lastName,
    string initialPassword,
    bool forcePasswordChange,
    bool forceMfa,
    string jobTitle,
    string department)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `enabled` | `bool` | Yes | Whether the account is enabled (default: `true`) |
| `displayName` | `string` | Yes | User's display name |
| `mailNickname` | `string` | Yes | Mail alias for the user |
| `userPrincipalName` | `string` | Yes | User principal name (e.g., `user@domain.com`) |
| `firstName` | `string` | No | User's first name |
| `lastName` | `string` | No | User's last name |
| `initialPassword` | `string` | Yes | Initial password for the account |
| `forcePasswordChange` | `bool` | Yes | Force password change at next login (default: `false`) |
| `forceMfa` | `bool` | Yes | Force MFA at next login (default: `false`) |
| `jobTitle` | `string` | No | User's job title |
| `department` | `string` | No | User's department |

**Returns:** `UserInfo` — the created user

### Get User by ID

```csharp
Task<UserInfo> GetByIdAsync(string id)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `string` | User ID (GUID) or User Principal Name |

**Returns:** `UserInfo`

### Get Users by Filter

```csharp
Task<ICollectionPageProvider<UserInfo>> GetByFilterAsync(int? top, string oDataFilter)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `top` | `int?` | Maximum number of results per page (nullable) |
| `oDataFilter` | `string` | OData filter expression (e.g., `"startsWith(displayName, 'John')"`) |

**Returns:** `ICollectionPageProvider<UserInfo>` — paginated user collection

### Update User

```csharp
Task UpdateAsync(UserInfo userInfo)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userInfo` | `UserInfo` | User object with updated properties. Set writable properties before calling. |

### Delete User

```csharp
Task DeleteByIdAsync(string id)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `string` | User ID or User Principal Name |

### Check User Existence

```csharp
Task<bool> CheckExistenceAsync(string id)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `string` | User ID or User Principal Name |

**Returns:** `bool` — `true` if user exists

### Reset Password

> **Important:** Requires a `GraphServiceClient` created with `CreateWithUserCredentials` (delegated permissions).

```csharp
Task ResetPasswordAsync(
    string userIdOrUpn,
    string password,
    bool forcePasswordChangeNextLogin,
    bool forcePasswordChangeNextLoginMfa)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | User ID or User Principal Name |
| `password` | `string` | New password |
| `forcePasswordChangeNextLogin` | `bool` | Force password change at next sign-in (default: `false`) |
| `forcePasswordChangeNextLoginMfa` | `bool` | Force MFA at next sign-in (default: `false`) |

### Get User Groups

```csharp
Task<ICollectionPageProvider<GroupInfo>> GetUserGroupsAsync(string userIdOrUpn, int? top)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | User ID or User Principal Name |
| `top` | `int?` | Maximum results per page |

**Returns:** `ICollectionPageProvider<GroupInfo>`

### Get User Roles

```csharp
Task<ICollectionPageProvider<DirectoryRoleInfo>> GetUserRolesAsync(string userIdOrUpn, int? top)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | User ID or User Principal Name |
| `top` | `int?` | Maximum results per page |

**Returns:** `ICollectionPageProvider<DirectoryRoleInfo>`

### Get Manager

```csharp
Task<DirectoryObjectInfo> GetManager(string userIdOrUpn)
```

**Returns:** `DirectoryObjectInfo` — the user's manager

### Set Manager

```csharp
Task SetManager(string userIdOrUpn, string managerIdOrUpn)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | Target user ID or UPN |
| `managerIdOrUpn` | `string` | Manager's user ID or UPN |

### Get Manager's Direct Reports

```csharp
Task<ICollectionPageProvider<DirectoryObjectInfo>> GetManagerDirectReports(string managerIdOrUpn, int? top)
```

**Returns:** `ICollectionPageProvider<DirectoryObjectInfo>`

### Assign License to User

```csharp
Task<User> AssignLicenseToUserAsync(string userIdOrUpn, string licenseID, string[] disabledServicePlans)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | User ID or User Principal Name |
| `licenseID` | `string` | The SKU ID of the license to assign |
| `disabledServicePlans` | `string[]` | Optional array of service plan IDs to disable |

**Returns:** `User` (Microsoft.Graph.User object)

### Remove License from User

```csharp
Task<User> RemoveLicenseFromUserAsync(string userIdOrUpn, string licenseID)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `userIdOrUpn` | `string` | User ID or User Principal Name |
| `licenseID` | `string` | The SKU ID of the license to remove |

**Returns:** `User` (Microsoft.Graph.User object)

---

## IAzureADGroupService

Access: `azureAD.AzureADGroupService(client)`

### Create Assigned Group

```csharp
Task<GroupInfo> CreateAssignedGroupAsync(
    GroupType groupType,
    string name,
    string description,
    string mailNickname,
    bool mailEnabled,
    bool securityEnabled,
    string visibility)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `groupType` | `GroupType` | Yes | Group type (default: `Security`) |
| `name` | `string` | Yes | Display name of the group |
| `description` | `string` | No | Group description |
| `mailNickname` | `string` | Yes | Mail alias for the group |
| `mailEnabled` | `bool` | Yes | Whether mail is enabled (default: `false`) |
| `securityEnabled` | `bool` | Yes | Whether security is enabled (default: `true`) |
| `visibility` | `string` | No | Group visibility (e.g., `"Public"`, `"Private"`) |

**Returns:** `GroupInfo` — the created group

### Get Group by ID

```csharp
Task<GroupInfo> GetByIdAsync(string id)
```

**Returns:** `GroupInfo`

### Get Group by Name

```csharp
Task<GroupInfo> GetByNameAsync(string groupName)
```

**Returns:** `GroupInfo`

### Get Groups by Filter

```csharp
Task<ICollectionPageProvider<GroupInfo>> GetByFilterAsync(int? top, string oDataFilter)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `top` | `int?` | Maximum results per page |
| `oDataFilter` | `string` | OData filter expression |

**Returns:** `ICollectionPageProvider<GroupInfo>`

### Update Group

```csharp
Task UpdateAsync(GroupInfo groupInfo)
```

### Delete Group

```csharp
Task DeleteByIdAsync(string id)
```

### Check Group Existence

```csharp
Task<bool> CheckExistenceAsync(string name)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `string` | Group display name |

**Returns:** `bool`

### Add Member to Group

```csharp
Task AddMemberToGroupAsync(string memberId, string groupId)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `memberId` | `string` | ID of the user or group to add |
| `groupId` | `string` | ID of the target group |

### Remove Member from Group

```csharp
Task RemoveMemberFromGroupAsync(string memberId, string groupId)
```

### Check Group Membership

```csharp
Task<bool> IsMemberOfGroupAsync(string memberId, string groupId, bool recurseIntoChildGroups)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `memberId` | `string` | ID of the user or group to check |
| `groupId` | `string` | ID of the group |
| `recurseIntoChildGroups` | `bool` | Check transitive (nested) membership |

**Returns:** `bool`

### Get User Members in Group

```csharp
Task<ICollectionPageProvider<UserInfo>> GetGroupUserMembersAsync(string groupId)
```

### Get Group Members in Group

```csharp
Task<ICollectionPageProvider<GroupInfo>> GetGroupGroupMembersAsync(string groupId)
```

### Get Parent Groups

```csharp
Task<ICollectionPageProvider<GroupInfo>> GetGroupParentsAsync(string groupId, bool transitive)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `groupId` | `string` | ID of the group |
| `transitive` | `bool` | Include indirect parent groups |

### Add Owner to Group

```csharp
Task AddOwnerToGroupAsync(string ownerId, string groupId)
```

### Remove Owner from Group

```csharp
Task RemoveOwnerFromGroupAsync(string ownerId, string groupId)
```

### Check Group Ownership

```csharp
Task<bool> IsOwnerOfGroupAsync(string ownerId, string groupId)
```

**Returns:** `bool`

### Get Group Owners

```csharp
Task<ICollectionPageProvider<UserInfo>> GetGroupUserOwnersAsync(string groupId)
```

---

## IAzureADRoleService

Access: `azureAD.AzureADRoleService(client)`

### Add Member to Role

```csharp
Task AddMemberToRoleAsync(string roleId, string memberId)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `roleId` | `string` | Directory role ID |
| `memberId` | `string` | User or service principal ID to add |

### Remove Member from Role

```csharp
Task RemoveMemberFromRoleAsync(string roleId, string memberId)
```

### Check Role Membership

```csharp
Task<bool> IsMemberInRoleAsync(string roleId, string memberId)
```

**Returns:** `bool`

### Get Users in Role

```csharp
Task<ICollectionPageProvider<UserInfo>> GetUsersInRoleAsync(string roleId)
```

### Get Roles

```csharp
Task<ICollectionPageProvider<DirectoryRoleInfo>> GetRolesAsync(int? top, string oDataFilter)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `top` | `int?` | Maximum results per page |
| `oDataFilter` | `string` | OData filter expression |

---

## IAzureADLifecyclePolicyService

Access: `azureAD.AzureADLifecyclePolicyService(client)`

### Create Lifecycle Policy

```csharp
Task<LifecyclePolicyInfo> CreateLifecyclePolicyAsync(
    int groupLifetime,
    string alternateNotificationEmails,
    ManagedGroupTypes managedGroupTypes)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `groupLifetime` | `int` | Group lifetime in days |
| `alternateNotificationEmails` | `string` | Semicolon-separated notification email addresses |
| `managedGroupTypes` | `ManagedGroupTypes` | Which groups the policy applies to (default: `Selected`) |

**Returns:** `LifecyclePolicyInfo`

### Get Lifecycle Policy by ID

```csharp
Task<LifecyclePolicyInfo> GetByIdAsync(string id)
```

### Get All Lifecycle Policies

```csharp
Task<ICollectionPageProvider<LifecyclePolicyInfo>> GetLifecyclePoliciesAsync()
```

### Update Lifecycle Policy

```csharp
Task UpdateAsync(LifecyclePolicyInfo lifecyclePolicy)
```

### Delete Lifecycle Policy

```csharp
Task DeleteByIdAsync(string id)
```

### Add Group to Lifecycle Policy

```csharp
Task AddGroupToLifecyclePolicyAsync(string groupId, string lifecyclePolicyId)
```

### Remove Group from Lifecycle Policy

```csharp
Task RemoveGroupFromLifecyclePolicyAsync(string groupId, string lifecyclePolicyId)
```

### Check Group in Lifecycle Policy

```csharp
Task<bool> IsGroupInLifecyclePolicyAsync(string groupId, string lifecyclePolicyId)
```

**Returns:** `bool`

---

## Data Models

### DirectoryObjectInfo (Base Class)

```csharp
[DataContract]
public class DirectoryObjectInfo
{
    string Id { get; }            // Read-only. Object ID (GUID)
    string ODataType { get; }     // Read-only. OData type name
}
```

### UserInfo : DirectoryObjectInfo

```csharp
[DataContract]
public class UserInfo : DirectoryObjectInfo
{
    // Read/Write properties (can be set for Create/Update)
    string UserPrincipalName { get; set; }
    string DisplayName { get; set; }
    string FirstName { get; set; }
    string LastName { get; set; }
    string MailNickname { get; set; }
    bool? AccountEnabled { get; set; }
    string JobTitle { get; set; }
    string Department { get; set; }
    string CompanyName { get; set; }
    string City { get; set; }
    string State { get; set; }
    string Country { get; set; }
    string PostalCode { get; set; }
    string StreetAddress { get; set; }
    string OfficeLocation { get; set; }
    string MobilePhone { get; set; }
    string BusinessPhone { get; set; }
    string PreferredLanguage { get; set; }
    string UsageLocation { get; set; }

    // Read-only properties
    string UserType { get; }
    string Mail { get; }
    string LegalAgeGroupClassification { get; }
    string OnPremisesUserPrincipalName { get; }
    string OnPremisesDistinguishedName { get; }
    string OnPremisesSamAccountName { get; }
    string OnPremisesDomainName { get; }
    string OnPremisesSecurityIdentifier { get; }
    bool? OnPremisesSyncEnabled { get; }
    DateTimeOffset? OnPremisesLastSyncDateTime { get; }
}
```

### GroupInfo : DirectoryObjectInfo

```csharp
[DataContract]
public class GroupInfo : DirectoryObjectInfo
{
    // Read/Write properties
    string DisplayName { get; set; }
    string Description { get; set; }
    string Classification { get; set; }
    bool? MailEnabled { get; set; }
    string MailNickname { get; set; }
    bool? SecurityEnabled { get; set; }
    string PreferredDataLocation { get; set; }

    // Read-only properties
    GroupType GroupType { get; }
    MembershipType MembershipType { get; }
    DateTimeOffset? CreatedDateTime { get; }
    string Mail { get; }
    string OnPremisesSecurityIdentifier { get; }
    IEnumerable<string> ProxyAddresses { get; }
    DateTimeOffset? RenewedDateTime { get; }
    string Visibility { get; }
    bool? OnPremisesSyncEnabled { get; }
    DateTimeOffset? OnPremisesLastSyncDateTime { get; }
}
```

### DirectoryRoleInfo : DirectoryObjectInfo

```csharp
[DataContract]
public class DirectoryRoleInfo : DirectoryObjectInfo
{
    string DisplayName { get; set; }
    string Description { get; set; }
}
```

### LifecyclePolicyInfo : DirectoryObjectInfo

```csharp
[DataContract]
public class LifecyclePolicyInfo : DirectoryObjectInfo
{
    int? GroupLifetimeInDays { get; set; }
    ManagedGroupTypes ManagedGroupTypes { get; set; }
    string AlternateNotificationEmails { get; set; }
}
```

---

## Enums

| Enum | Values | Description |
|------|--------|-------------|
| `GroupType` | `Security`, `Office365`, `MailEnabledSecurityGroup`, `DistributionGroup`, `None` | Type of Azure AD group |
| `MembershipType` | `Assigned`, `Dynamic` | How group membership is managed |
| `ManagedGroupTypes` | `None`, `Selected`, `All` | Which groups a lifecycle policy manages |
