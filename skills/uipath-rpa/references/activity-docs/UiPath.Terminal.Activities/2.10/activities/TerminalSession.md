# Terminal Session

`UiPath.Terminal.Activities.TerminalSession`

Container scope activity that establishes a terminal connection and provides it to all child activities. All other terminal activities must be placed inside a Terminal Session. Supports creating new connections (via connection string), reusing an existing open connection, and SSH authentication. Supported providers include BlueZone, IBM PCOMM, Attachmate, direct TCP/SSH (UiPathNew), EHLLAPI (Generic), and Tandem/NonStop via THLLAPI (TandemHLL).

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  

## Properties

### New Session

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionString` | Connection String | `InArgument` | `string` | | | Serialized connection string describing the terminal provider, host, port, and protocol. Use the **Connection Settings** button in the designer to build this value visually. |
| `OutputConnection` | Output Connection | `OutArgument` | `TerminalConnection` | | | Stores the opened connection object so it can be reused in a later Terminal Session (via `ExistingConnection`). If not set, the connection is closed automatically when the scope ends. |

### Use Existing Connection

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ExistingConnection` | Existing Connection | `InArgument` | `TerminalConnection` | | | A previously opened `TerminalConnection` object to reuse. When set, `ConnectionString` must not be set. |
| `CloseConnection` | Close Connection | `Property` | `bool` | | `true` | When using an existing connection, controls whether the connection is closed when the scope exits. Automatically set to `false` if `OutputConnection` is provided. |

### SSH Connection Properties

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SSHUserName` | SSH UserId | `InArgument` | `string` | | | SSH username for authentication. Only applies when the connection string specifies SSH protocol. |
| `SSHPassword` | SSH Password | `InArgument` | `SecureString` | | | SSH password for authentication. Use a `SecureString` variable to avoid storing credentials as plain text. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `50000` | Milliseconds to wait for the terminal connection to be established. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `1000` | Milliseconds to wait after the connection is established before scheduling child activities. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | `false` | When `true`, the workflow continues execution even if this activity throws an error. |

## Valid Configurations

This activity supports two mutually exclusive connection modes. `ConnectionString` and `ExistingConnection` cannot both be set — a validation error is raised at design time.

**Mode A — New Connection**: Set `ConnectionString`. The session opens a new connection. Optionally set `OutputConnection` to keep the connection alive after the scope exits.

**Mode B — Existing Connection**: Set `ExistingConnection` with a previously opened `TerminalConnection` variable. Optionally set `CloseConnection = false` to leave it open after the scope.

## Notes

- All other terminal activities must be placed inside this scope.
- If `OutputConnection` is set, `CloseConnection` is automatically forced to `false`.
- The connection string must not reference the deprecated `UiPathInternal` provider type (validation error is raised).
- For Tandem/NonStop sessions, use the `TandemHLL` provider type with `ConnectionType.LowLevel`. The connection uses the same EHLLAPI-style fields (`EhllDll`, `EhllSession`, etc.) but targets `THLLW3.DLL` or `THLLW6.DLL` (Attachmate Reflection 6530). Color information is not available for this provider.
- SSH credentials are only used when the connection string's protocol is SSH. For non-SSH connections, `SSHUserName` and `SSHPassword` are ignored.
- Use the **Connection Settings** button in the UiPath Studio designer to build the connection string visually (not available in Studio Web).
- Use the **Run Wizard** button to launch the Terminal Recorder (not available in Studio Web, requires a literal connection string).

## XAML Example

**Mode A — New connection:**

```xml
<uit:TerminalSession DisplayName="Terminal Session"
                   ConnectionString="[connStr]"
                   TimeoutMS="50000"
                   CloseConnection="True"
                   DelayMS="1000">
  <uit:TerminalSession.Body>
    <ActivityAction x:TypeArguments="uit:TerminalConnection">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="uit:TerminalConnection" Name="terminalSession" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- child terminal activities here -->
      </Sequence>
    </ActivityAction>
  </uit:TerminalSession.Body>
</uit:TerminalSession>
```

**Mode B — Existing connection:**

```xml
<uit:TerminalSession DisplayName="Terminal Session (Reuse)"
                   ExistingConnection="[existingConn]"
                   CloseConnection="False"
                   TimeoutMS="50000"
                   DelayMS="1000">
  <uit:TerminalSession.Body>
    <ActivityAction x:TypeArguments="uit:TerminalConnection">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="uit:TerminalConnection" Name="terminalSession" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- child terminal activities here -->
      </Sequence>
    </ActivityAction>
  </uit:TerminalSession.Body>
</uit:TerminalSession>
```
