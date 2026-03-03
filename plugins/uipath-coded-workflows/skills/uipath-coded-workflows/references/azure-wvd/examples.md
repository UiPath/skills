# Azure Windows Virtual Desktop Examples

Examples using the `azureWVD` service from `UiPath.AzureWindowsVirtualDesktop.Activities` package.

**Required package:** `"UiPath.AzureWindowsVirtualDesktop.Activities": "[1.4.1]"`

---

## Create and Manage a Host Pool

```csharp
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Core;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class HostPoolWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IHostPoolService hostPoolService =
                azureWVD.HostPoolService(clientProvider);

            // Create a pooled host pool
            var createParams = new HostPoolCreateParams
            {
                Name = "Engineering-Pool",
                ResourceGroupName = "rg-wvd-prod",
                Region = "eastus",
                FriendlyName = "Engineering Host Pool",
                Description = "Host pool for engineering team",
                Type = HostPoolType.Pooled,
                PooledMaxSessionLimit = 10,
                PooledLoadBalancing = LoadBalancerType.BreadthFirst,
                ValidationEnvironment = false
            };

            WVDHostPool hostPool = await hostPoolService.CreateHostPool(createParams);
            Log($"Created host pool: {hostPool.Name} ({hostPool.ID})");

            // Update the host pool
            var updateParams = new HostPoolUpdateParams
            {
                FriendlyName = "Engineering Host Pool (Updated)",
                PooledMaxSessionLimit = 15
            };
            await hostPoolService.UpdateHostPool(hostPool, updateParams);
            Log("Host pool updated.");

            // List all host pools in the resource group
            HostPoolList pools = await hostPoolService.ListHostPools("rg-wvd-prod", null);
            foreach (var pool in pools.Value)
            {
                Log($"Host pool: {pool.Name}");
            }
        }
    }
}
```

## Manage Session Hosts

```csharp
using System.Security;
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Core;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class SessionHostWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IHostPoolService hostPoolService =
                azureWVD.HostPoolService(clientProvider);
            ISessionHostService sessionHostService =
                azureWVD.SessionHostService(clientProvider);

            // Get the host pool
            WVDHostPool hostPool = await hostPoolService.GetHostPool(
                "Engineering-Pool", "rg-wvd-prod");

            // Add a VM to the host pool
            var domainPassword = new SecureString();
            foreach (char c in "DomainP@ss123!") domainPassword.AppendChar(c);

            WVDSessionHost newHost = await hostPoolService.AddVMToHostPool(
                hostPool,
                vmName: "vm-wvd-001",
                vmResourceGroupName: "rg-wvd-vms",
                domainName: "corp.com",
                domainOU: "OU=WVD,DC=corp,DC=com",
                domainUser: "admin@corp.com",
                domainPassword: domainPassword,
                waitForCompletion: true);
            Log($"Added session host: {newHost.Name}, Status: {newHost.Status}");

            // List all session hosts
            SessionHostList hosts = await sessionHostService.ListSessionHosts(hostPool, null);
            foreach (var host in hosts.Value)
            {
                Log($"Session host: {host.Name}, Status: {host.Status}, Sessions: {host.Sessions}");
            }

            // Put a session host in drain mode (no new sessions)
            WVDSessionHost sessionHost = await sessionHostService.GetSessionHost(
                hostPool, "vm-wvd-001.corp.com");
            await sessionHostService.UpdateSessionHost(sessionHost, allowNewSession: false, assignedUser: null);
            Log("Session host set to drain mode.");
        }
    }
}
```

## Manage User Sessions

```csharp
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Core;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class UserSessionWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IHostPoolService hostPoolService =
                azureWVD.HostPoolService(clientProvider);
            ISessionHostService sessionHostService =
                azureWVD.SessionHostService(clientProvider);
            IUserSessionService userSessionService =
                azureWVD.UserSessionService(clientProvider);

            // Get host pool and session host
            WVDHostPool hostPool = await hostPoolService.GetHostPool(
                "Engineering-Pool", "rg-wvd-prod");
            WVDSessionHost sessionHost = await sessionHostService.GetSessionHost(
                hostPool, "vm-wvd-001.corp.com");

            // List user sessions on the session host
            UserSessionList sessions = await userSessionService.ListUserSessions(
                sessionHost, null);
            foreach (var session in sessions.Value)
            {
                Log($"Session: {session.Name}, User: {session.UserPrincipalName}, State: {session.SessionState}");
            }

            // Send a message to the first session
            if (sessions.Value.Count > 0)
            {
                var firstSession = sessions.Value.First();
                await userSessionService.SendMessageToUserSession(
                    firstSession,
                    "Maintenance Notice",
                    "This session host will restart in 30 minutes for maintenance.");
                Log("Message sent.");

                // Disconnect the session
                await userSessionService.DisconnectUserSession(firstSession);
                Log("Session disconnected.");
            }
        }
    }
}
```

## Create and Manage Workspaces

```csharp
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class WorkspaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IWorkspaceService workspaceService =
                azureWVD.WorkspaceService(clientProvider);

            // Create a workspace
            var createParams = new WorkspaceCreateParams
            {
                Name = "Engineering-Workspace",
                ResourceGroupName = "rg-wvd-prod",
                Region = "eastus",
                FriendlyName = "Engineering Workspace",
                Description = "Workspace for engineering team"
            };

            WVDWorkspace workspace = await workspaceService.CreateWorkspace(createParams);
            Log($"Created workspace: {workspace.Name} ({workspace.ID})");

            // Get workspace by name
            WVDWorkspace fetched = await workspaceService.GetWorkspace(
                "Engineering-Workspace", "rg-wvd-prod");
            Log($"Workspace: {fetched.FriendlyName}, Region: {fetched.Region}");

            // Update workspace
            var updateParams = new WorkspaceUpdateParams
            {
                Name = "Engineering-Workspace",
                ResourceGroupName = "rg-wvd-prod",
                FriendlyName = "Engineering Workspace (Updated)",
                Description = "Updated workspace for engineering team"
            };
            await workspaceService.UpdateWorkspace(updateParams);
            Log("Workspace updated.");

            // List workspaces
            WorkspaceList workspaces = await workspaceService.ListWorkspaces(
                "rg-wvd-prod", null);
            foreach (var wrks in workspaces.Value)
            {
                Log($"Workspace: {wrks.Name}");
            }

            // Delete workspace
            await workspaceService.DeleteWorkspace(fetched);
            Log("Workspace deleted.");
        }
    }
}
```

## Application Groups and Role Assignments

```csharp
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Core;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class AppGroupWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IApplicationGroupService appGroupService =
                azureWVD.ApplicationGroupService(clientProvider);
            IRoleAssignmentService roleService =
                azureWVD.RoleAssignmentService(clientProvider);

            // Get an application group
            WVDApplicationGroup appGroup = await appGroupService.GetApplicationGroup(
                "rg-wvd-prod", "Engineering-Pool-DAG");
            Log($"App group: {appGroup.Name}, Type: {appGroup.ApplicationGroupType}");
            Log($"Host pool: {appGroup.HostPoolName}");

            // List application groups in a resource group
            ApplicationGroupList appGroups = await appGroupService.ListApplicationGroups(
                "rg-wvd-prod", null, null);
            foreach (var ag in appGroups.Value)
            {
                Log($"App group: {ag.Name}");
            }

            // Assign users to the application group
            string[] userIds = new[]
            {
                "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",  // Azure AD object ID
                "ffffffff-1111-2222-3333-444444444444"
            };
            await roleService.AssignObjectsToApplicationGroup(appGroup, userIds);
            Log("Users assigned to application group.");

            // Remove users from the application group
            await roleService.RemoveObjectsFromApplicationGroup(appGroup, userIds);
            Log("Users removed from application group.");
        }
    }
}
```

## Paginated Listing

```csharp
using System.Collections.Generic;
using UiPath.AzureWVD.Models;
using UiPath.AzureWindowsVirtualDesktop.Activities.API;
using UiPath.Shared.Interfaces;

namespace MyProject
{
    public class PaginationWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(IClientProvider clientProvider)
        {
            IHostPoolService hostPoolService =
                azureWVD.HostPoolService(clientProvider);
            ISessionHostService sessionHostService =
                azureWVD.SessionHostService(clientProvider);

            // Get host pool
            WVDHostPool hostPool = await hostPoolService.GetHostPool(
                "Engineering-Pool", "rg-wvd-prod");

            // Paginate through all session hosts
            var allHosts = new List<WVDSessionHost>();
            string token = null;

            do
            {
                SessionHostList page = await sessionHostService.ListSessionHosts(
                    hostPool, token);
                foreach (var host in page.Value)
                {
                    allHosts.Add(new WVDSessionHost(host, hostPool));
                }
                token = page.NextLink;
            } while (!string.IsNullOrEmpty(token));

            Log($"Total session hosts: {allHosts.Count}");
            foreach (var host in allHosts)
            {
                Log($"  {host.Name} - Status: {host.Status}, Sessions: {host.NumberOfSessions}");
            }
        }
    }
}
```
