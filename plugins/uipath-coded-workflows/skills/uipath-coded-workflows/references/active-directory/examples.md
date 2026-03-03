# Active Directory Domain Services Examples

Examples using the `activeDirectoryDomainServices` service from `UiPath.ActiveDirectoryDomainServices.Activities` package.

**Required package:** `"UiPath.ActiveDirectoryDomainServices.Activities": "[1.4.1]"`

---

## Create a User and Set Properties

```csharp
using System.Collections.Generic;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class CreateUserWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryUserService userService =
                activeDirectoryDomainServices.ActiveDirectoryUserService(clientProvider);

            // Create a new user with additional properties
            var properties = new Dictionary<string, object>
            {
                { "givenName", "John" },
                { "sn", "Doe" },
                { "mail", "john.doe@corp.com" },
                { "userPrincipalName", "john.doe@corp.com" },
                { "department", "Engineering" }
            };

            string userDn = userService.CreateUser(
                cn: "John Doe",
                sAMAccountName: "john.doe",
                password: "P@ssw0rd123!",
                locationDn: "OU=Users,OU=Engineering,DC=corp,DC=com",
                properties: properties,
                enabled: true);

            Log($"Created user: {userDn}");
        }
    }
}
```

## Check and Manage User Status

```csharp
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class ManageUserStatusWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryUserService userService =
                activeDirectoryDomainServices.ActiveDirectoryUserService(clientProvider);
            IActiveDirectoryCommonService commonService =
                activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

            // Resolve SAM account name to DN
            string userDn = commonService.GetDistinguishedName("john.doe");

            // Check current status
            (LockStatus lockStatus, ActiveStatus activeStatus) = userService.GetUserStatus(userDn);
            Log($"User lock: {lockStatus}, active: {activeStatus}");

            // Unlock the user if locked
            if (lockStatus == LockStatus.Locked)
            {
                userService.SetUserStatus(userDn, UserStatus.Unlocked);
                Log("User unlocked.");
            }

            // Disable the user
            userService.SetUserStatus(userDn, UserStatus.Disabled);
            Log("User disabled.");
        }
    }
}
```

## Password Management

```csharp
using System;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class PasswordManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider, string userDn)
        {
            IActiveDirectoryUserService userService =
                activeDirectoryDomainServices.ActiveDirectoryUserService(clientProvider);

            // Check password expiration
            DateTime? pwdExpiry = userService.GetUserPasswordExpirationDate(userDn);
            if (pwdExpiry.HasValue)
            {
                Log($"Password expires: {pwdExpiry.Value}");
            }
            else
            {
                Log("Password never expires.");
            }

            // Change the password
            userService.ChangeUserPassword(userDn, "NewP@ssw0rd456!");
            Log("Password changed.");

            // Force password change at next logon
            userService.ForcePasswordChange(userDn);
            Log("User must change password at next logon.");

            // Validate credentials
            bool isValid = userService.ValidateUserCredentials(
                ValidateCredentialsUserFilter.SAMAccountName,
                "john.doe",
                "NewP@ssw0rd456!");
            Log($"Credentials valid: {isValid}");
        }
    }
}
```

## Create Group and Manage Membership

```csharp
using System.Collections.Generic;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class GroupManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryGroupService groupService =
                activeDirectoryDomainServices.ActiveDirectoryGroupService(clientProvider);
            IActiveDirectoryCommonService commonService =
                activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

            // Create a global security group
            string groupDn = groupService.CreateGroup(
                cn: "Engineering Team",
                sAMAccountName: "EngineeringTeam",
                locationDn: "OU=Groups,DC=corp,DC=com",
                type: GroupType.GlobalSecurity,
                properties: new Dictionary<string, object>
                {
                    { "description", "Engineering department team" }
                });

            Log($"Created group: {groupDn}");

            // Add a user to the group
            string userDn = commonService.GetDistinguishedName("john.doe");
            groupService.AddObjectToGroup(userDn, EntryType.User, groupDn);
            Log("User added to group.");

            // List all users in the group
            string[] members = groupService.GetObjectsInGroup(groupDn, EntryType.User);
            foreach (string memberDn in members)
            {
                Log($"Member: {memberDn}");
            }

            // Remove user from group
            groupService.RemoveObjectFromGroup(userDn, EntryType.User, groupDn);
            Log("User removed from group.");
        }
    }
}
```

## Search and Filter AD Objects

```csharp
using System.Collections.Generic;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class SearchADWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryCommonService commonService =
                activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

            // Search by property filter
            var filter = new FilterProperty("department", "Engineering", Relation.EqualTo);
            string[] engineers = commonService.FilterObjectsByProperty(
                filter,
                objectClass: "user",
                objectCategory: "person",
                locationDn: "OU=Users,DC=corp,DC=com");

            Log($"Found {engineers.Length} engineers.");

            // Search using raw LDAP filter
            string[] disabledUsers = commonService.FilterObjectsByLDAPFilter(
                "(&(objectClass=user)(objectCategory=person)(userAccountControl:1.2.840.113556.1.4.803:=2))");

            Log($"Found {disabledUsers.Length} disabled users.");

            // Check if entry exists
            bool exists = commonService.EntryExistsBySAMAccountName(
                "john.doe", EntryType.User);
            Log($"john.doe exists: {exists}");

            bool existsByUPN = commonService.EntryExistsByUPN(
                "john.doe@corp.com", EntryType.User);
            Log($"john.doe@corp.com exists: {existsByUPN}");
        }
    }
}
```

## Read and Update Object Properties

```csharp
using System.Collections.Generic;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class UpdatePropertiesWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider, string userDn)
        {
            IActiveDirectoryCommonService commonService =
                activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

            // Get all properties
            Dictionary<string, object> allProps = commonService.GetObjectProperties(userDn);
            foreach (var kvp in allProps)
            {
                Log($"{kvp.Key} = {kvp.Value}");
            }

            // Get a single property
            object email = commonService.GetObjectProperty(userDn, "mail");
            Log($"Email: {email}");

            // Update properties
            commonService.UpdateProperties(userDn, new Dictionary<string, object>
            {
                { "title", "Senior Engineer" },
                { "department", "Platform Engineering" },
                { "telephoneNumber", "+1-555-0123" }
            });

            Log("Properties updated.");
        }
    }
}
```

## Move, Rename, and Check Group Membership

```csharp
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class MoveRenameWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryCommonService commonService =
                activeDirectoryDomainServices.ActiveDirectoryCommonService(clientProvider);

            string userDn = commonService.GetDistinguishedName("john.doe");

            // Check group membership (with nested groups)
            bool isMember = commonService.IsObjectMemberOfGroup(
                userDn,
                "CN=Engineering Team,OU=Groups,DC=corp,DC=com",
                recurseIntoChildGroups: true);
            Log($"Is member of Engineering Team: {isMember}");

            // Move user to a different OU
            commonService.MoveObject(userDn, "OU=Contractors,DC=corp,DC=com");
            Log("User moved to Contractors OU.");

            // Rename the user
            string newUserDn = commonService.GetDistinguishedName("john.doe");
            commonService.RenameObject(newUserDn, "John M. Doe");
            Log("User renamed.");
        }
    }
}
```

## Create and Manage Organizational Units

```csharp
using System.Collections.Generic;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class OUManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryOrganizationUnitService ouService =
                activeDirectoryDomainServices.ActiveDirectoryOrganizationUnitService(clientProvider);

            // Create a new OU
            string ouDn = ouService.CreateOrganizationalUnit(
                cn: "Contractors",
                locationDn: "DC=corp,DC=com",
                properties: new Dictionary<string, object>
                {
                    { "description", "Contractor accounts" }
                },
                connection: Connection.Primary);

            Log($"Created OU: {ouDn}");

            // Delete the OU (with child objects)
            ouService.DeleteOrganizationalUnit(
                ouDn, EntryType.OrganizationalUnit, recursive: true);
            Log("OU deleted.");
        }
    }
}
```

## Computer Management and Domain Join

```csharp
using System.Security;
using UiPath.ActiveDirectoryDomainServices.Core;
using UiPath.ActiveDirectoryDomainServices.Activities.API;

namespace MyProject
{
    public class ComputerManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(ActiveDirectoryClientProvider clientProvider)
        {
            IActiveDirectoryComputerService computerService =
                activeDirectoryDomainServices.ActiveDirectoryComputerService(clientProvider);

            // Create a computer account
            string computerDn = computerService.CreateComputer(
                cn: "WORKSTATION01",
                accountName: "WORKSTATION01$",
                locationDn: "OU=Workstations,DC=corp,DC=com",
                properties: new System.Collections.Generic.Dictionary<string, object>
                {
                    { "description", "Engineering workstation" }
                },
                enabled: true);

            Log($"Created computer: {computerDn}");

            // Check status
            ActiveStatus status = computerService.GetComputerStatus(computerDn);
            Log($"Computer status: {status}");

            // Disable the computer account
            computerService.SetComputerStatus(computerDn, ActiveStatus.Disabled);
            Log("Computer disabled.");
        }
    }
}
```
