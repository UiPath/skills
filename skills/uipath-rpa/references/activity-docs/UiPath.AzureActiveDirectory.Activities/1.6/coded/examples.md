# Azure Active Directory Examples

Examples using the `azureAD` service from `UiPath.AzureActiveDirectory.Activities` package.

**Required package:** `"UiPath.AzureActiveDirectory.Activities": "[1.6.3]"`

> **Prerequisites:** All examples require an Azure AD app registration with appropriate Microsoft Graph API permissions. Use `graphServiceClientProvider` to create an authenticated `GraphServiceClient`, then pass it to `azureAD` sub-services.

---

## Authenticate with App Credentials

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class AppAuth : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                tenantId: "your-tenant-id",
                clientId: "your-client-id",
                clientSecret: clientSecret);

            var userService = azureAD.AzureADUserService(client);
            var groupService = azureAD.AzureADGroupService(client);

            Log("Authenticated with app credentials.");
        }
    }
}
```

## Authenticate with User Credentials (Delegated)

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class DelegatedAuth : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "user-password") password.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithUserCredentials(
                tenantId: "your-tenant-id",
                clientId: "your-client-id",
                username: "admin@company.com",
                password: password);

            // Delegated client required for password reset
            var userService = azureAD.AzureADUserService(client);

            Log("Authenticated with delegated credentials.");
        }
    }
}
```

## Create a New User

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;
using UiPath.AzureActiveDirectory.Contracts.Users;

namespace MyProject
{
    public class CreateUser : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);

            var newUser = await userService.CreateUserAsync(
                enabled: true,
                displayName: "Jane Smith",
                mailNickname: "janesmith",
                userPrincipalName: "jane.smith@company.com",
                firstName: "Jane",
                lastName: "Smith",
                initialPassword: "TempPass123!",
                forcePasswordChange: true,
                forceMfa: false,
                jobTitle: "Software Engineer",
                department: "Engineering");

            Log($"Created user: {newUser.DisplayName} ({newUser.Id})");
        }
    }
}
```

## Get and Update a User

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;
using UiPath.AzureActiveDirectory.Contracts.Users;

namespace MyProject
{
    public class GetUpdateUser : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);

            // Get user by UPN
            var user = await userService.GetByIdAsync("jane.smith@company.com");
            Log($"Found user: {user.DisplayName}, Department: {user.Department}");

            // Update user properties
            user.JobTitle = "Senior Software Engineer";
            user.Department = "Platform Engineering";
            user.OfficeLocation = "Building A, Floor 3";
            await userService.UpdateAsync(user);

            Log($"Updated user: {user.DisplayName}");
        }
    }
}
```

## Check User Existence and Delete

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class CheckDeleteUser : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);

            var exists = await userService.CheckExistenceAsync("jane.smith@company.com");
            Log($"User exists: {exists}");

            if (exists)
            {
                await userService.DeleteByIdAsync("jane.smith@company.com");
                Log("User deleted.");
            }
        }
    }
}
```

## Reset User Password (Delegated Auth Required)

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ResetPassword : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var password = new SecureString();
            foreach (char c in "admin-password") password.AppendChar(c);

            // Password reset requires delegated (user) credentials
            var client = graphServiceClientProvider.CreateWithUserCredentials(
                "your-tenant-id", "your-client-id",
                "admin@company.com", password);

            var userService = azureAD.AzureADUserService(client);

            await userService.ResetPasswordAsync(
                userIdOrUpn: "jane.smith@company.com",
                password: "NewSecurePass456!",
                forcePasswordChangeNextLogin: true,
                forcePasswordChangeNextLoginMfa: false);

            Log("Password reset successfully.");
        }
    }
}
```

## Manage User Licenses

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ManageLicenses : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);

            // Assign a license (e.g., Microsoft 365 E3)
            await userService.AssignLicenseToUserAsync(
                userIdOrUpn: "jane.smith@company.com",
                licenseID: "05e9a617-0261-4cee-bb44-138d3ef5d965",
                disabledServicePlans: new string[] { "service-plan-id-to-disable" });

            Log("License assigned.");

            // Remove a license
            await userService.RemoveLicenseFromUserAsync(
                userIdOrUpn: "jane.smith@company.com",
                licenseID: "05e9a617-0261-4cee-bb44-138d3ef5d965");

            Log("License removed.");
        }
    }
}
```

## Get and Set User Manager

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ManageManager : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);

            // Set manager
            await userService.SetManager(
                userIdOrUpn: "jane.smith@company.com",
                managerIdOrUpn: "manager@company.com");
            Log("Manager set.");

            // Get manager
            var manager = await userService.GetManager("jane.smith@company.com");
            Log($"Manager: {manager.Id} (Type: {manager.ODataType})");

            // Get direct reports
            var reports = await userService.GetManagerDirectReports("manager@company.com", top: 50);
            Log("Retrieved direct reports.");
        }
    }
}
```

## Create a Security Group

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;
using UiPath.AzureActiveDirectory.Contracts.Groups;

namespace MyProject
{
    public class CreateGroup : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var groupService = azureAD.AzureADGroupService(client);

            var group = await groupService.CreateAssignedGroupAsync(
                groupType: GroupType.Security,
                name: "Engineering Team",
                description: "All engineering staff",
                mailNickname: "eng-team",
                mailEnabled: false,
                securityEnabled: true,
                visibility: "Private");

            Log($"Created group: {group.DisplayName} ({group.Id})");
        }
    }
}
```

## Manage Group Members and Owners

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ManageGroupMembers : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var groupService = azureAD.AzureADGroupService(client);
            var userService = azureAD.AzureADUserService(client);

            // Get group by name
            var group = await groupService.GetByNameAsync("Engineering Team");
            var user = await userService.GetByIdAsync("jane.smith@company.com");

            // Add member
            await groupService.AddMemberToGroupAsync(user.Id, group.Id);
            Log($"Added {user.DisplayName} to {group.DisplayName}");

            // Check membership (with transitive check)
            var isMember = await groupService.IsMemberOfGroupAsync(
                user.Id, group.Id, recurseIntoChildGroups: true);
            Log($"Is member: {isMember}");

            // Add owner
            await groupService.AddOwnerToGroupAsync(user.Id, group.Id);
            Log($"Added {user.DisplayName} as owner of {group.DisplayName}");

            // Check ownership
            var isOwner = await groupService.IsOwnerOfGroupAsync(user.Id, group.Id);
            Log($"Is owner: {isOwner}");

            // Remove member and owner
            await groupService.RemoveMemberFromGroupAsync(user.Id, group.Id);
            await groupService.RemoveOwnerFromGroupAsync(user.Id, group.Id);
            Log("Removed member and owner.");
        }
    }
}
```

## List Group Members and Parent Groups

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ListGroupInfo : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var groupService = azureAD.AzureADGroupService(client);

            var group = await groupService.GetByNameAsync("Engineering Team");

            // Get user members
            var userMembers = await groupService.GetGroupUserMembersAsync(group.Id);
            Log("User members retrieved.");

            // Get nested group members
            var groupMembers = await groupService.GetGroupGroupMembersAsync(group.Id);
            Log("Group members retrieved.");

            // Get parent groups (transitive)
            var parentGroups = await groupService.GetGroupParentsAsync(group.Id, transitive: true);
            Log("Parent groups retrieved.");

            // Get group owners
            var owners = await groupService.GetGroupUserOwnersAsync(group.Id);
            Log("Group owners retrieved.");
        }
    }
}
```

## Manage Directory Roles

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;

namespace MyProject
{
    public class ManageRoles : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var roleService = azureAD.AzureADRoleService(client);
            var userService = azureAD.AzureADUserService(client);

            // List all directory roles
            var roles = await roleService.GetRolesAsync(top: 100, oDataFilter: null);
            Log("Retrieved directory roles.");

            // Add user to a role
            var user = await userService.GetByIdAsync("jane.smith@company.com");
            string roleId = "role-id-guid";

            await roleService.AddMemberToRoleAsync(roleId, user.Id);
            Log($"Added {user.DisplayName} to role.");

            // Check role membership
            var isInRole = await roleService.IsMemberInRoleAsync(roleId, user.Id);
            Log($"Is in role: {isInRole}");

            // Get users in a role
            var usersInRole = await roleService.GetUsersInRoleAsync(roleId);
            Log("Retrieved users in role.");

            // Remove user from role
            await roleService.RemoveMemberFromRoleAsync(roleId, user.Id);
            Log("Removed user from role.");
        }
    }
}
```

## Manage Lifecycle Policies

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;
using UiPath.AzureActiveDirectory.Contracts.Groups.LifecyclePolicies;

namespace MyProject
{
    public class ManageLifecyclePolicies : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var lifecycleService = azureAD.AzureADLifecyclePolicyService(client);
            var groupService = azureAD.AzureADGroupService(client);

            // Create a lifecycle policy
            var policy = await lifecycleService.CreateLifecyclePolicyAsync(
                groupLifetime: 180,
                alternateNotificationEmails: "admin@company.com;it-team@company.com",
                managedGroupTypes: ManagedGroupTypes.Selected);

            Log($"Created lifecycle policy: {policy.Id}");

            // Add a group to the policy
            var group = await groupService.GetByNameAsync("Engineering Team");
            await lifecycleService.AddGroupToLifecyclePolicyAsync(group.Id, policy.Id);
            Log($"Added group to lifecycle policy.");

            // Check if group is in policy
            var isInPolicy = await lifecycleService.IsGroupInLifecyclePolicyAsync(group.Id, policy.Id);
            Log($"Group in policy: {isInPolicy}");

            // Update the policy
            policy.GroupLifetimeInDays = 365;
            policy.AlternateNotificationEmails = "admin@company.com";
            await lifecycleService.UpdateAsync(policy);
            Log("Updated lifecycle policy.");

            // Remove group and delete policy
            await lifecycleService.RemoveGroupFromLifecyclePolicyAsync(group.Id, policy.Id);
            await lifecycleService.DeleteByIdAsync(policy.Id);
            Log("Removed group and deleted policy.");
        }
    }
}
```

## End-to-End: Onboard New Employee

```csharp
using System;
using System.Security;
using UiPath.CodedWorkflows;
using UiPath.AzureActiveDirectory.Activities.API;
using UiPath.AzureActiveDirectory.Contracts.Users;
using UiPath.AzureActiveDirectory.Contracts.Groups;

namespace MyProject
{
    public class OnboardEmployee : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var clientSecret = new SecureString();
            foreach (char c in "your-client-secret") clientSecret.AppendChar(c);

            var client = graphServiceClientProvider.CreateWithAppCredentials(
                "your-tenant-id", "your-client-id", clientSecret);

            var userService = azureAD.AzureADUserService(client);
            var groupService = azureAD.AzureADGroupService(client);
            var roleService = azureAD.AzureADRoleService(client);

            // 1. Create user account
            var newUser = await userService.CreateUserAsync(
                enabled: true,
                displayName: "Alex Johnson",
                mailNickname: "alexjohnson",
                userPrincipalName: "alex.johnson@company.com",
                firstName: "Alex",
                lastName: "Johnson",
                initialPassword: "Welcome123!",
                forcePasswordChange: true,
                forceMfa: true,
                jobTitle: "Product Manager",
                department: "Product");

            Log($"Created user: {newUser.DisplayName} ({newUser.UserPrincipalName})");

            // 2. Set manager
            await userService.SetManager(newUser.UserPrincipalName, "vp-product@company.com");
            Log("Manager assigned.");

            // 3. Add to department group
            var deptGroup = await groupService.GetByNameAsync("Product Team");
            await groupService.AddMemberToGroupAsync(newUser.Id, deptGroup.Id);
            Log($"Added to group: {deptGroup.DisplayName}");

            // 4. Add to all-company group
            var allCompany = await groupService.GetByNameAsync("All Employees");
            await groupService.AddMemberToGroupAsync(newUser.Id, allCompany.Id);
            Log($"Added to group: {allCompany.DisplayName}");

            // 5. Assign license
            await userService.AssignLicenseToUserAsync(
                userIdOrUpn: newUser.UserPrincipalName,
                licenseID: "05e9a617-0261-4cee-bb44-138d3ef5d965",
                disabledServicePlans: null);
            Log("License assigned.");

            Log($"Onboarding complete for {newUser.DisplayName}.");
        }
    }
}
```
