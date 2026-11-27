# Azure Active Directory Activities API Reference

Reference for the `azureAD` service from `UiPath.AzureActiveDirectory.Activities` package.

**Required package:** `"UiPath.AzureActiveDirectory.Activities": "[1.6.3]"`

**Auto-imported namespaces:** `UiPath.AzureActiveDirectory.Activities.API`, `UiPath.AzureActiveDirectory.Activities.API.Util`, `UiPath.AzureActiveDirectory.Contracts`, `UiPath.AzureActiveDirectory.Contracts.Users`, `UiPath.AzureActiveDirectory.Contracts.Groups`, `UiPath.AzureActiveDirectory.Contracts.Groups.LifecyclePolicies`, `UiPath.AzureActiveDirectory.Contracts.Roles`, `UiPath.AzureActiveDirectory.Contracts.Devices`, `UiPath.Core`

**Service accessors:**
- `azureAD` (type `IAzureADService`) — main service providing access to user, group, role, and lifecycle policy sub-services
- `graphServiceClientProvider` (type `IGraphServiceClientProvider`) — creates authenticated Microsoft Graph clients

---

## Overview

The Azure Active Directory API provides coded workflow access to **Users, Groups, Roles, Licenses, Managers, and Lifecycle Policies** via the Microsoft Graph API. Authentication is handled by creating a `GraphServiceClient` through the `graphServiceClientProvider`, which supports both app-only and delegated (user) credentials.

### Architecture

```
graphServiceClientProvider (IGraphServiceClientProvider)
├── .CreateWithAppCredentials(tenantId, clientId, clientSecret)    → GraphServiceClient
└── .CreateWithUserCredentials(tenantId, clientId, user, password) → GraphServiceClient

azureAD (IAzureADService)
├── .AzureADUserService(client)             → IAzureADUserService
├── .AzureADGroupService(client)            → IAzureADGroupService
├── .AzureADRoleService(client)             → IAzureADRoleService
└── .AzureADLifecyclePolicyService(client)  → IAzureADLifecyclePolicyService
```

### Workflow Pattern

1. Create a `GraphServiceClient` using `graphServiceClientProvider`
2. Get a sub-service from `azureAD` by passing the client
3. Call async methods on the sub-service

```csharp
var client = graphServiceClientProvider.CreateWithAppCredentials(
    tenantId, clientId, clientSecret);
var userService = azureAD.AzureADUserService(client);
var user = await userService.GetByIdAsync("user@company.com");
```

### Authentication Methods

| Method | Use Case | Requirements |
|--------|----------|--------------|
| `CreateWithAppCredentials` | App-only / daemon scenarios | Azure AD app registration with client secret |
| `CreateWithUserCredentials` | Delegated / user context (required for password reset) | Azure AD app registration + user credentials |

> **Note:** `ResetPasswordAsync` requires a client created with `CreateWithUserCredentials` (delegated permissions).

---

## Sub-Services Summary

| Service | Accessor | Description |
|---------|----------|-------------|
| `IAzureADUserService` | `azureAD.AzureADUserService(client)` | Create, read, update, delete users; manage passwords, licenses, managers |
| `IAzureADGroupService` | `azureAD.AzureADGroupService(client)` | Create, read, update, delete groups; manage members and owners |
| `IAzureADRoleService` | `azureAD.AzureADRoleService(client)` | Manage directory role memberships |
| `IAzureADLifecyclePolicyService` | `azureAD.AzureADLifecyclePolicyService(client)` | Create and manage group lifecycle policies |

---

## Key Enum Reference Summary

| Enum | Values | Description |
|------|--------|-------------|
| `GroupType` | `Security`, `Office365`, `MailEnabledSecurityGroup`, `DistributionGroup`, `None` | Type of Azure AD group |
| `MembershipType` | `Assigned`, `Dynamic` | How group membership is determined |
| `ManagedGroupTypes` | `None`, `Selected`, `All` | Which groups a lifecycle policy applies to |

---

## Key Model Types

| Type | Description |
|------|-------------|
| `GraphServiceClient` | Microsoft Graph API client (from `Microsoft.Graph`) |
| `SecureString` | .NET secure string for secrets (from `System.Security`) |
| `UserInfo` | Azure AD user with profile properties |
| `GroupInfo` | Azure AD group with membership and mail properties |
| `DirectoryRoleInfo` | Azure AD directory role |
| `DirectoryObjectInfo` | Base type for directory objects (users, groups, etc.) |
| `LifecyclePolicyInfo` | Group lifecycle policy configuration |
| `ICollectionPageProvider<T>` | Paginated collection for iterating large result sets |

---

## Reference Files

- **Full API reference** → [api.md](api.md) — all service interfaces, method signatures, parameters, return types, and model definitions
- **Code examples** → [examples.md](examples.md) — complete coded workflow examples for each service
