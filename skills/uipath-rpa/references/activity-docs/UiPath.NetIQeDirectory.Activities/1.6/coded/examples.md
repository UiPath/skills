# NetIQ eDirectory Examples

Examples using the `netiq` service from `UiPath.NetIQeDirectory.Activities` package.

**Required package:** `"UiPath.NetIQeDirectory.Activities": "[1.4.1]"`

---

## Create a User and Check Status

```csharp
using System.Collections.Generic;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class CreateUserWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider)
        {
            INetIQeDirectoryUserService userService =
                netiq.NetIQeDirectoryUserService(clientProvider);

            // Create a new user
            var properties = new Dictionary<string, object>
            {
                { "givenName", "John" },
                { "sn", "Doe" },
                { "mail", "john.doe@corp.com" },
                { "userPrincipalName", "john.doe@corp.com" }
            };

            string userDn = await userService.CreateUser(
                commonName: "John Doe",
                sAMAccountName: "john.doe",
                password: "P@ssw0rd123!",
                locationDn: "OU=Users,O=corp",
                properties: properties,
                enabled: true,
                connection: Connection.Primary);

            Log($"Created user: {userDn}");

            // Check user status
            (LockStatus lockStatus, ActiveStatus activeStatus) =
                await userService.GetUserStatus(userDn, Connection.Primary);
            Log($"Lock: {lockStatus}, Active: {activeStatus}");
        }
    }
}
```

## Password Management

```csharp
using System;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class PasswordWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider, string userDn)
        {
            INetIQeDirectoryUserService userService =
                netiq.NetIQeDirectoryUserService(clientProvider);

            // Check password expiration
            DateTime? pwdExpiry = await userService.GetPasswordExpirationDate(
                userDn, Connection.Primary);
            if (pwdExpiry.HasValue)
                Log($"Password expires: {pwdExpiry.Value}");
            else
                Log("Password never expires.");

            // Change password
            await userService.ChangeUserPassword(userDn, "NewP@ss456!", Connection.Primary);
            Log("Password changed.");

            // Force change at next logon
            await userService.ForcePasswordChange(userDn, Connection.Primary);
            Log("Must change password at next logon.");

            // Validate credentials
            bool isValid = await userService.ValidateUserCredentials(
                ValidateCredentialsUserFilter.SAMAccountName,
                "john.doe",
                "NewP@ss456!",
                ConnectionWithoutAuto.Primary);
            Log($"Credentials valid: {isValid}");
        }
    }
}
```

## User Status and Expiration

```csharp
using System;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class UserStatusWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider, string userDn)
        {
            INetIQeDirectoryUserService userService =
                netiq.NetIQeDirectoryUserService(clientProvider);

            // Unlock user
            await userService.SetUserStatus(userDn, UserStatus.Unlocked, Connection.Primary);
            Log("User unlocked.");

            // Set account expiration
            await userService.SetUserExpirationDate(
                userDn, DateTime.Now.AddMonths(6), Connection.Primary);
            Log("Expiration date set.");

            // Get groups
            string[] groups = await userService.GetUserGroups(userDn, Connection.Primary);
            foreach (string groupDn in groups)
            {
                Log($"Member of: {groupDn}");
            }
        }
    }
}
```

## Group Management

```csharp
using System.Collections.Generic;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Enums;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class GroupWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider)
        {
            INetIQeDirectoryGroupService groupService =
                netiq.NetIQeDirectoryGroupService(clientProvider);
            INetIQeDirectoryUserService userService =
                netiq.NetIQeDirectoryUserService(clientProvider);
            INetIQeDirectoryObjectService objectService =
                netiq.NetIQeDirectoryObjectService(clientProvider);

            // Create a group
            string groupDn = await groupService.CreateGroup(
                commonName: "Engineering",
                sAMAccountName: "Engineering",
                locationDn: "OU=Groups,O=corp",
                properties: new Dictionary<string, object>
                {
                    { "description", "Engineering team" }
                },
                type: GroupType.GlobalSecurity,
                connection: Connection.Primary);

            Log($"Created group: {groupDn}");

            // Add a user to the group
            string userDn = await objectService.GetDistinguishedName(
                "john.doe", ConnectionWithoutAuto.Primary);
            await userService.AddUserToGroup(
                userDn, groupDn, Connection.Primary, Connection.Primary);
            Log("User added to group.");

            // List user members
            string[] members = await groupService.GetMembersDN(
                groupDn, EntryType.User, Connection.Primary);
            foreach (string memberDn in members)
            {
                Log($"Member: {memberDn}");
            }

            // Check membership
            bool isMember = await objectService.IsObjectMemberOfGroup(
                userDn, groupDn, Connection.Primary, Connection.Primary,
                recurseIntoChildGroups: true);
            Log($"Is member: {isMember}");

            // Remove user from group
            await userService.RemoveUserFromGroup(
                userDn, groupDn, Connection.Primary, Connection.Primary);
            Log("User removed.");
        }
    }
}
```

## Search and Filter Objects

```csharp
using System.Collections.Generic;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class SearchWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider)
        {
            INetIQeDirectoryObjectService objectService =
                netiq.NetIQeDirectoryObjectService(clientProvider);

            // Resolve SAM account name to DN
            string dn = await objectService.GetDistinguishedName(
                "john.doe", ConnectionWithoutAuto.Primary);
            Log($"DN: {dn}");

            // Get all properties
            Dictionary<string, object> props = objectService.GetObjectProperties(
                dn, Connection.Primary);
            foreach (var kvp in props)
            {
                Log($"{kvp.Key} = {kvp.Value}");
            }

            // Search with LDAP filter
            string[] results = await objectService.FilterObjects(
                "(&(objectClass=user)(department=Engineering))",
                "OU=Users,O=corp",
                ConnectionWithoutAuto.Primary);
            Log($"Found {results.Length} users in Engineering.");

            // Update properties
            await objectService.UpdateProperties(dn,
                new Dictionary<string, object>
                {
                    { "title", "Senior Engineer" },
                    { "department", "Platform" }
                },
                Connection.Primary);
            Log("Properties updated.");
        }
    }
}
```

## Computer Management

```csharp
using System.Collections.Generic;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class ComputerWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider)
        {
            INetIQeDirectoryComputerService computerService =
                netiq.NetIQeDirectoryComputerService(clientProvider);

            // Create a computer
            string computerDn = await computerService.CreateComputer(
                commonName: "WORKSTATION01",
                sAMAccountName: "WORKSTATION01$",
                locationDn: "OU=Computers,O=corp",
                properties: new Dictionary<string, object>
                {
                    { "description", "Dev workstation" }
                },
                enabled: true,
                connection: Connection.Primary);

            Log($"Created computer: {computerDn}");

            // Check status
            ActiveStatus status = await computerService.GetComputerStatus(
                computerDn, Connection.Primary);
            Log($"Status: {status}");

            // Add to group
            await computerService.AddComputerToGroup(
                computerDn,
                "CN=DevMachines,OU=Groups,O=corp",
                Connection.Primary, Connection.Primary);
            Log("Added to group.");

            // Disable
            await computerService.SetComputerStatus(
                computerDn, ActiveStatus.Disabled, Connection.Primary);
            Log("Computer disabled.");
        }
    }
}
```

## Move, Rename, and Manage OUs

```csharp
using System.Collections.Generic;
using UiPath.NetIQeDirectory;
using UiPath.NetIQeDirectory.Activities.API;
using UiPath.NetIQeDirectory.Interfaces;

namespace MyProject
{
    public class MoveRenameOUWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(INetIQeDirectoryClientProvider clientProvider)
        {
            INetIQeDirectoryObjectService objectService =
                netiq.NetIQeDirectoryObjectService(clientProvider);
            INetIQeDirectoryOrganizationService ouService =
                netiq.NetIQeDirectoryOrganizationService(clientProvider);

            // Create an OU
            string ouDn = await ouService.CreateOrganizationalUnit(
                organizationUnitName: "Contractors",
                locationDn: "O=corp",
                properties: new Dictionary<string, object>
                {
                    { "description", "Contractor accounts" }
                },
                connection: Connection.Primary);
            Log($"Created OU: {ouDn}");

            // Move an object to the new OU
            string userDn = await objectService.GetDistinguishedName(
                "john.doe", ConnectionWithoutAuto.Primary);
            await objectService.MoveObject(userDn, ouDn, Connection.Primary);
            Log("User moved to Contractors OU.");

            // Rename an object
            string newDn = await objectService.GetDistinguishedName(
                "john.doe", ConnectionWithoutAuto.Primary);
            await objectService.RenameObject(newDn, "John M. Doe", Connection.Primary);
            Log("User renamed.");

            // Delete the OU
            await ouService.DeleteOrganizationalUnit(ouDn, recursive: true, Connection.Primary);
            Log("OU deleted.");
        }
    }
}
```
