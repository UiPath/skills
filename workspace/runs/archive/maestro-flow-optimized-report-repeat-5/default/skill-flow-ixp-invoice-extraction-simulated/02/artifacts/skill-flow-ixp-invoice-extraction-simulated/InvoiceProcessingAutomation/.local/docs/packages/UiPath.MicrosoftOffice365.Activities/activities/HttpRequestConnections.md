# HTTP Request

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.General.HttpRequestConnections`

Sends an HTTP request to the Microsoft Graph API.

**Connector:** `uipath-microsoft-365`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `RequestMethod` | Request Method | `InArgument` | `RequestMethod` | Yes | | The HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. |
| `RequestUrl` | Request URL | `InArgument` | `String` | Yes | | The Graph API endpoint path (e.g., "/me/messages"). |
| `ParametersVariable` | Parameters | `InArgument` | `Dictionary<String, String>` | No | | Query parameters as a dictionary. |
| `HeadersVariable` | Headers | `InArgument` | `Dictionary<String, String>` | No | | HTTP headers as a dictionary. |
| `Body` | Body | `InArgument` | `String` | No | | The request body (for POST, PUT, PATCH). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ResponseContent` | Response Content | `OutArgument` | `String` | The response body as a string. |
| `ResponseStatus` | Response Status Code | `OutArgument` | `Int32` | The HTTP status code. |
| `ResponseHeaders` | Response Headers | `OutArgument` | `Dictionary<String, String>` | The response headers. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umag="clr-namespace:UiPath.MicrosoftOffice365.Activities.General;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umage="clr-namespace:UiPath.MicrosoftOffice365.Activities.General.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umag:HttpRequestConnections ConnectionId="{x:Null}"
    RequestUrl="/me/messages"
    ResponseContent="[responseBody]"
    ResponseStatus="[statusCode]"
    DisplayName="HTTP Request">
  <umag:HttpRequestConnections.RequestMethod>
    <InArgument x:TypeArguments="umage:RequestMethod">GET</InArgument>
  </umag:HttpRequestConnections.RequestMethod>
</umag:HttpRequestConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
