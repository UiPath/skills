# Microsoft 365 Scope

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Office365ApplicationScope`

Authentication scope for Microsoft 365. Opens an authenticated Microsoft Graph session using Interactive Token, Username/Password, Integrated Windows Authentication, Application ID + Secret, or Application ID + Certificate, and exposes it to every Office 365 activity placed in its body — classic activities **and** modern `*Connections` activities alike. Activities nested in the scope **do not require Integration Service**; the scope is the single source of authentication for all of them. Authentication scopes are auto-computed at runtime from the child activities' `RequiredScopes`.

**Package:** `UiPath.MicrosoftOffice365.Activities`
**Category:** Microsoft 365
**Platform:** Windows only

## Properties

### General

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConfigLocation` | Connection method | `Property` | [`ActivityConfigLocation`](#activityconfiglocation) | No | `PropertiesPanel` | Whether credentials come from the properties panel or from an Orchestrator asset selected via `BrowserItemId`. |
| `AuthenticationType` | Authentication Type | `Property` | [`AuthenticationType`](#authenticationtype) | Yes | `InteractiveToken` | The authentication method to use. Drives which sub-fields are required. |
| `Environment` | Environment | `Property` | [`HostingEnvironment`](#hostingenvironment) | No | `Global` | Microsoft 365 cloud environment (Global / China / Germany / US Government / US Government DOD). |
| `ApplicationId` | Application ID | `InArgument` | `String` | Conditional | | Azure AD application (client) ID. Required for all auth types **except** `IntegrationService` and `InteractiveToken` with `OAuthApplication = UIPATH`. |
| `TenantId` | Tenant | `InArgument` | `String` | Conditional | | Azure AD tenant ID or domain. Required for `UsernameAndPassword`, `IntegratedWindowsAuthentication`, and `ApplicationIdAndSecret`. |
| `Connector` | Select connector | `Property` | `String` | No | | Studio-side connector selector exposed by the base connection-service plumbing. Not user-meaningful on this scope — the scope authenticates every Office 365 activity in its body regardless of their individual connector. |

### Interactive Token

Required when `AuthenticationType = InteractiveToken`. Launches a browser-based consent flow on first run; refresh tokens are cached per `DataStoreLocation`.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `OAuthApplication` | OAuth Application | `Property` | [`OAuthApplication`](#oauthapplication) | No | `UIPATH` | `UIPATH` uses the public UiPath Azure AD app (no `ApplicationId` needed); `Custom` requires `ApplicationId`. |
| `EmailAddress` | OAuth2 User | `InArgument` | `String` | No | | Username hint passed to the interactive login screen and used to key the token cache. |
| `UseBroker` | Use Broker | `Property` | `Boolean?` | No | `null` | When `true`, uses the Windows Authentication Manager (WAM) broker for interactive auth. |
| `DataStoreLocation` | Connection Data Store Location | `Property` | [`DataStoreLocation`](#datastorelocation) | No | `DISK` | Where to persist the token cache (`office365.tokens.msalcache.bin3`). |
| `Folder` | Connection Orchestrator Folder Path | `InArgument` | `String` | No | | Orchestrator folder path used when `DataStoreLocation = ORCHESTRATOR`. |

### Username and Password

Required when `AuthenticationType = UsernameAndPassword`.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Username` | Username | `InArgument` | `String` | Conditional | | User principal name (UPN). |
| `Password` | Password | `InArgument` | `String` | Conditional | | Plain string password. Mutually exclusive with `SecurePassword`. |
| `SecurePassword` | Secure Password | `InArgument` | `SecureString` | Conditional | | Password as `SecureString`. Prefer this over `Password`. |

### Integrated Windows Authentication

Required when `AuthenticationType = IntegratedWindowsAuthentication`. Uses the current Windows session against a federated tenant — only `ApplicationId` and `TenantId` are needed.

### Application ID and Secret

Required when `AuthenticationType = ApplicationIdAndSecret` (client-credentials flow).

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ApplicationSecret` | Application Secret | `InArgument` | `String` | Conditional | | Azure AD app client secret as plain string. Mutually exclusive with `SecureApplicationSecret`. |
| `SecureApplicationSecret` | Secure Application Secret | `InArgument` | `SecureString` | Conditional | | Azure AD app client secret as `SecureString`. Prefer this over `ApplicationSecret`. |

### Application ID and Certificate

Required when `AuthenticationType = ApplicationIdAndCertificate` (certificate-credentials flow).

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CertificateAsBase64` | Certificate As Base64 | `InArgument` | `String` | Conditional | | PKCS#12 certificate encoded as Base64. |
| `CertificatePassword` | Certificate Password | `InArgument` | `SecureString` | No | | Password protecting the PKCS#12 certificate. |

### Integration Service

Required when `AuthenticationType = IntegrationService`. The base scope reads its configuration from the named connection — no per-type fields are needed here.

### Impersonation (app-only flows)

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ImpersonatedUserEmailAddress` | Impersonated User Email Address | `InArgument` | `String` | No | | When using `ApplicationIdAndSecret` or `ApplicationIdAndCertificate`, route Graph calls on behalf of this user. |

### Orchestrator Asset Configuration

Required when `ConfigLocation = OrchestratorAsset`. In this mode the activity reads its authentication settings from an Orchestrator asset selected at design time; the per-`AuthenticationType` sections above are ignored.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `BrowserItemId` | Office 365 asset ID | `InArgument` | `String` | Yes | | ID of the Orchestrator asset that holds the connection configuration. Set by the Studio asset browser. |
| `BrowserParentItemId` | Office 365 connection method | `InArgument` | `String` | No | | Parent folder/asset identifier emitted by the Studio browser. |
| `BrowserItemFriendlyName` | Connection assets | `InArgument` | `String` | No | | Human-readable name of the selected asset. |
| `BrowserItemFullPath` | O365 Connection Asset Full Path | `InArgument` | `String` | No | | Full Orchestrator path of the selected asset. |

### Runtime Browser Configuration (Robot-side asset selection)

These properties let the robot resolve an Orchestrator asset at runtime rather than at design time. `RuntimeItemInputMode` selects whether to use the Studio-picked runtime asset (`Browse`) or a manually-supplied path (`FullPath`).

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `RuntimeItemInputMode` | Runtime connection asset input mode | `Property` | `EDriveItemMode` | No | `Browse` | `Browse` uses the Studio-picked runtime asset; `FullPath` uses `ManualRuntimeItemFullPath`. |
| `BrowserRuntimeItemId` | Runtime connection assets | `InArgument` | `String` | No | | Runtime asset ID emitted by the Studio browser. |
| `BrowserRuntimeParentItemId` | Runtime parent ID | `InArgument` | `String` | No | | Runtime parent asset ID emitted by the Studio browser. |
| `BrowserRuntimeItemFriendlyName` | Runtime connection assets | `InArgument` | `String` | No | | Runtime asset friendly name. |
| `BrowserRuntimeItemFullPath` | Runtime connection asset full path | `InArgument` | `String` | No | | Full Orchestrator path of the runtime asset (Studio-resolved). |
| `ManualRuntimeItemFullPath` | Runtime connection assets | `InArgument` | `String` | Conditional | | Manually-entered runtime asset path. Required when `RuntimeItemInputMode = FullPath`. |

### Authentication Scopes

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AuthenticationScopes` | Authentication Scopes | `Property` | `List<InArgument<String>>` | No | empty | OAuth scope strings to request. Hidden in the designer — at runtime the scope set is auto-computed from the `RequiredScopes` of every child activity via `IScopeCalculatorService`. |

### Common

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Timeout` | TimeoutMS | `InArgument` | `Int32` | No | | Per-call HTTP timeout in milliseconds. |
| `ContinueOnError` | Continue On Error | `InArgument` | `Boolean` | No | `false` | Whether failures inside the scope propagate or are swallowed. |
| `DisplayName` | Display name | `Property` | `String` | No | `Microsoft 365 Scope` | Activity name shown in the designer. |

### Body

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Body` | (designer-only) | `Property` | `ActivityDelegate` (`ActivityAction<Object>`) | Yes | Empty `Sequence` named "Do" | The Do-sequence that holds child activities. Backwards-compatible: older XAMLs that used `ActivityAction<GraphServiceClient>` are upgraded transparently to `ActivityAction<Object>`. The delegate argument is named `ParentScope`. |

### Obsolete

| Name | Replacement |
|------|-------------|
| `Tenant` (`InArgument<String>`) | Use `TenantId`. Setter forwards `Expression` to `TenantId` for backwards compatibility. |
| `OAuth2Username` (`InArgument<String>`) | Use `EmailAddress`. Setter forwards `Expression` to `EmailAddress`. |
| `Services` (`MicrosoftService`) | Use `AuthenticationScopes`. On .NET Framework only, setting this still derives scopes via `ScopeSelector`; on .NET 6+ the setter is ignored. |

## Enum Reference

### `ActivityConfigLocation`

| Value | Description |
|-------|-------------|
| `PropertiesPanel` | Credentials are configured directly on the activity's properties. |
| `OrchestratorAsset` | Credentials are read from an Orchestrator asset selected via `BrowserItemId`. |

### `AuthenticationType`

| Value | Description |
|-------|-------------|
| `InteractiveToken` | Browser-based OAuth 2.0 user login. Refresh tokens are cached per `DataStoreLocation`. |
| `IntegratedWindowsAuthentication` | Silent auth using the current Windows session against a federated tenant. Requires `ApplicationId` + `TenantId`. |
| `UsernameAndPassword` | ROPC flow. Requires `Username`, `Password` (or `SecurePassword`), `ApplicationId`, `TenantId`. Not supported for federated / MFA-enabled accounts. |
| `ApplicationIdAndSecret` | Client-credentials flow (app-only). Requires `ApplicationId`, `TenantId`, and a secret. |
| `ApplicationIdAndCertificate` | Client-credentials flow using a PKCS#12 certificate. Requires `ApplicationId`, `TenantId`, and `CertificateAsBase64`. |
| `IntegrationService` | Authenticate via a UiPath Integration Service connection. |

### `OAuthApplication`

| Value | Description |
|-------|-------------|
| `UIPATH` | Use the UiPath-provided public Azure AD application. No `ApplicationId` required. Only valid with `AuthenticationType = InteractiveToken`. |
| `CUSTOM` | Use your own Azure AD application. Requires `ApplicationId`. |

### `HostingEnvironment`

| Value | Description |
|-------|-------------|
| `Default` | Default sovereign cloud (resolved by the MSAL configuration). |
| `Global` | Public Microsoft 365 cloud (login.microsoftonline.com). |
| `China` | 21Vianet / China sovereign cloud. |
| `Germany` | Germany sovereign cloud (legacy). |
| `USGovernment` | US Government GCC High cloud. |
| `USGovernmentDOD` | US Government DOD cloud. |

### `DataStoreLocation`

| Value | Description |
|-------|-------------|
| `DISK` | Store the MSAL token cache (`office365.tokens.msalcache.bin3`) on the local disk under the robot user profile. |
| `ORCHESTRATOR` | Store the token cache as an Orchestrator credential asset (use `Folder` to target a folder). |
| `NO_STORAGE` | Never persist tokens; re-authenticate each run. |

## Valid Configurations

The scope has two top-level configuration paths driven by `ConfigLocation`:

**Mode A — Properties Panel (`ConfigLocation = PropertiesPanel`):** authentication fields on the activity itself are required, gated by `AuthenticationType`:

- `InteractiveToken` + `OAuthApplication = UIPATH` → no `ApplicationId` required; optionally set `EmailAddress`, `DataStoreLocation`, `Folder`, `UseBroker`.
- `InteractiveToken` + `OAuthApplication = CUSTOM` → set `ApplicationId`; same optional fields as above.
- `IntegratedWindowsAuthentication` → set `ApplicationId` and `TenantId`.
- `UsernameAndPassword` → set `ApplicationId`, `TenantId`, `Username`, and (`Password` or `SecurePassword`).
- `ApplicationIdAndSecret` → set `ApplicationId`, `TenantId`, and (`ApplicationSecret` or `SecureApplicationSecret`). Optionally set `ImpersonatedUserEmailAddress`.
- `ApplicationIdAndCertificate` → set `ApplicationId`, `TenantId`, and `CertificateAsBase64`. Optionally set `CertificatePassword` and `ImpersonatedUserEmailAddress`.
- `IntegrationService` → no per-type fields required (handled by the base scope).

**Mode B — Orchestrator Asset (`ConfigLocation = OrchestratorAsset`):** set `BrowserItemId` (and usually the other `BrowserItem*` properties populated by Studio). Per-`AuthenticationType` fields are ignored. The runtime browser group (`BrowserRuntime*` / `ManualRuntimeItemFullPath`) further controls how the asset is resolved on the robot.

`Password`/`SecurePassword` and `ApplicationSecret`/`SecureApplicationSecret` are mutually exclusive pairs — set exactly one of each pair when its `AuthenticationType` applies.

## XAML Examples

### Interactive Token with the UiPath OAuth Application

```xml
<o365:Office365ApplicationScope
    DisplayName="Microsoft 365 Scope"
    ConfigLocation="PropertiesPanel"
    AuthenticationType="InteractiveToken"
    OAuthApplication="UIPATH"
    EmailAddress="[userEmail]"
    Environment="Global"
    DataStoreLocation="DISK"
    xmlns:o365="clr-namespace:UiPath.MicrosoftOffice365.Activities;assembly=UiPath.MicrosoftOffice365.Activities">
    <o365:Office365ApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <ActivityAction.Argument>
                <DelegateInArgument x:TypeArguments="x:Object" Name="ParentScope" />
            </ActivityAction.Argument>
            <Sequence DisplayName="Do">
                <!-- Child Office 365 activities here -->
            </Sequence>
        </ActivityAction>
    </o365:Office365ApplicationScope.Body>
</o365:Office365ApplicationScope>
```

### Application ID + Certificate (app-only, with impersonation)

```xml
<o365:Office365ApplicationScope
    DisplayName="Microsoft 365 Scope"
    ConfigLocation="PropertiesPanel"
    AuthenticationType="ApplicationIdAndCertificate"
    ApplicationId="[appId]"
    TenantId="[tenantId]"
    CertificateAsBase64="[certBase64]"
    CertificatePassword="[certPassword]"
    ImpersonatedUserEmailAddress="[targetUser]"
    Environment="Global"
    xmlns:o365="clr-namespace:UiPath.MicrosoftOffice365.Activities;assembly=UiPath.MicrosoftOffice365.Activities">
    <o365:Office365ApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <Sequence DisplayName="Do" />
        </ActivityAction>
    </o365:Office365ApplicationScope.Body>
</o365:Office365ApplicationScope>
```

### Application ID + Secret

```xml
<o365:Office365ApplicationScope
    DisplayName="Microsoft 365 Scope"
    ConfigLocation="PropertiesPanel"
    AuthenticationType="ApplicationIdAndSecret"
    ApplicationId="[appId]"
    TenantId="[tenantId]"
    SecureApplicationSecret="[secureSecret]"
    Environment="Global">
    <o365:Office365ApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <Sequence DisplayName="Do" />
        </ActivityAction>
    </o365:Office365ApplicationScope.Body>
</o365:Office365ApplicationScope>
```

### Username and Password

```xml
<o365:Office365ApplicationScope
    DisplayName="Microsoft 365 Scope"
    ConfigLocation="PropertiesPanel"
    AuthenticationType="UsernameAndPassword"
    ApplicationId="[appId]"
    TenantId="[tenantId]"
    Username="[upn]"
    SecurePassword="[securePassword]"
    Environment="Global">
    <o365:Office365ApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <Sequence DisplayName="Do" />
        </ActivityAction>
    </o365:Office365ApplicationScope.Body>
</o365:Office365ApplicationScope>
```

### Orchestrator Asset (auth config stored in Orchestrator)

```xml
<o365:Office365ApplicationScope
    DisplayName="Microsoft 365 Scope"
    ConfigLocation="OrchestratorAsset"
    BrowserItemId="686995"
    BrowserItemFriendlyName="O365AppIDCertificate"
    BrowserItemFullPath="uipath.settings.config"
    BrowserParentItemId="934580"
    RuntimeItemInputMode="Browse"
    AuthenticationType="InteractiveToken"
    Environment="Global"
    EmailAddress="[userEmail]">
    <o365:Office365ApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <Sequence DisplayName="Do" />
        </ActivityAction>
    </o365:Office365ApplicationScope.Body>
</o365:Office365ApplicationScope>
```

## Notes

- **Windows only** — not available in cross-platform robots.
- **Provides full functionality without Integration Service for every Office 365 activity — classic and `*Connections` alike.** Classic Office 365 activities always rely on this scope for authentication. Modern `*Connections` activities (e.g., `CopyItemConnections`, `SendMailConnections`, `HttpRequestConnections`) normally resolve their own `ConnectionId` via Integration Service when used at the top level — but when nested *inside* an `Office365ApplicationScope`, they auto-detect the parent (`HasAuthProviderParent`), hide their `ConnectionId` in the designer, set `UseConnectionService = False`, and delegate authentication to the scope. The scope therefore authenticates **every Office 365 activity in its body** with Interactive Token / Username+Password / IWA / App+Secret / App+Certificate credentials — useful for offline scenarios, custom Azure AD app registrations, certificate-based auth, sovereign clouds, or any flow that Integration Service can't (or shouldn't) handle.
- **Authentication scopes are auto-computed.** `AuthenticationScopes` is browsable=false; the runtime walks the body, collects `RequiredScopes` from every `IScopedClientActivity` child (including foreach and persistence activities), and asks `IScopeCalculatorService` for the minimum union. Do not set this property manually unless you also disable scope calculation.
- `Password` and `SecurePassword` are mutually exclusive — set exactly one when `AuthenticationType = UsernameAndPassword`. Same applies to `ApplicationSecret`/`SecureApplicationSecret` for `ApplicationIdAndSecret`.
- `UseBroker` is only honored when `AuthenticationType = InteractiveToken` on Windows. Set `true` to use the MSAL WAM broker (smoother SSO, supports passkeys); leave `null` for the default behavior.
- `EmailAddress` keys the on-disk MSAL token cache (file name `office365.tokens.msalcache.bin3`) and is also passed as the login hint to the browser.
- `ImpersonatedUserEmailAddress` is only meaningful with `ApplicationIdAndSecret` or `ApplicationIdAndCertificate` — it routes Graph calls via on-behalf-of for that user.
- The `Body` argument name is `ParentScope`. Older XAMLs serialized as `ActivityAction<GraphServiceClient>` are upgraded transparently to `ActivityAction<Object>` by the `Body` setter.
- The internal `IClientServices` (the runtime payload passed to children — wraps an `IGraphServiceClientProxy` and `OAuthDataOptions`) is not part of the design-time contract and is not exposed via XAML.
