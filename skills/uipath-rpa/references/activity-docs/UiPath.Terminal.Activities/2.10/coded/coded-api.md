# Terminal Activities — Coded Workflow API

`UiPath.Terminal.Activities`

Coded workflow API for automating terminal emulation sessions. Provides methods to establish connections to IBM 3270/5250, VT, HP, ANSI, Wyse, and other legacy terminal systems via BlueZone, IBM PCOMM, Attachmate, or direct TCP/SSH connections, then interact with the terminal screen programmatically.

**Service accessor:** `terminal` (type `ITerminalService`)
**Required package:** `"UiPath.Terminal.Activities": "*"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```
UiPath.Terminal
UiPath.Terminal.Data
UiPath.Terminal.Activities.API
UiPath.Terminal.Enums
```

## Service Overview

The `terminal` service provides factory methods that open a terminal connection and return a `TerminalConnection` object. The connection object is the API surface for all terminal operations — screen reads, field access, key sending, and waiting.

This is a **connection-based API**:
1. Call a service method (`GetConnection` / `GetSshConnection`) to open and connect.
2. Use the returned `TerminalConnection` to perform terminal operations.
3. Dispose the connection when done (or use a `using` statement).

In coded workflow mode, all `TerminalConnection` methods **throw `TerminalConnectionException`** on failure instead of returning error codes. This means you do not need to check return values — just handle exceptions.

---

## Connection Methods

### `TerminalConnection GetConnection(string connectionString)`

Opens a terminal connection using a serialized connection string. The connection string encodes the provider type, host, port, protocol, and other settings. Use the **Terminal Session** XAML activity's Connection Settings dialog to generate a valid string.

**Parameters:**
- `connectionString` (`string`) — Serialized connection string. Example: obtained by configuring a Terminal Session activity and copying the `ConnectionString` property value.

**Returns:** `TerminalConnection` — An open, connected terminal session. Implements `IDisposable`; use inside a `using` statement.

**Throws:** `TerminalConnectionException` if the connection cannot be established within the timeout.

---

### `TerminalConnection GetConnection(ConnectionData connectionData)`

Opens a terminal connection using a `ConnectionData` object, allowing programmatic configuration without a serialized connection string.

**Parameters:**
- `connectionData` (`ConnectionData`) — Configuration object specifying provider, host, port, protocol, and emulation settings.

**Returns:** `TerminalConnection` — An open, connected terminal session.

**Throws:** `TerminalConnectionException` if the connection cannot be established.

---

### `TerminalConnection GetSshConnection(ConnectionData connectionData, string sshUser, SecureString sshPassword)`

Opens an SSH terminal connection with explicit credentials. The `connectionData` must specify `ProviderType = UiPathNew` and `ConnectionProtocol = SSH`.

**Parameters:**
- `connectionData` (`ConnectionData`) — Connection configuration. Must have `ProviderType = TerminalProviderType.UiPathNew` and `ConnectionProtocol = CommunicationType.SSH`.
- `sshUser` (`string`) — SSH username.
- `sshPassword` (`SecureString`) — SSH password. Use a `SecureString` variable (e.g., from Get Credential) to avoid plain-text exposure.

**Returns:** `TerminalConnection` — An open, connected SSH terminal session.

**Throws:** `TerminalConnectionException` if the connection fails, or `ArgumentException` if `ProviderType` or `ConnectionProtocol` is invalid.

---

## TerminalConnection

`TerminalConnection` is the handle returned by all service methods. It provides all terminal interaction operations and implements `IDisposable`.

> This type implements `IDisposable`. Always use inside a `using` statement or call `Dispose()` / `Shutdown()` explicitly. Disposing disconnects the session and terminates any host processes.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `Connected` | `bool` | `true` if the session is currently connected to the host. |
| `ConnectionString` | `string` | The serialized connection string used to establish this connection. |
| `DefaultCmdOptions` | `CommandOptions` | Default timeout and wait-mode options applied to all operations when not explicitly overridden. |

### Events

| Event | Description |
|-------|-------------|
| `TerminalScreenChanged` | Raised when the terminal screen content changes. |
| `TerminalFieldChanged` | Raised when a field value changes. |
| `TerminalCursorChanged` | Raised when the cursor position changes. |
| `TerminalConnectionChanged` | Raised when the connection status changes (e.g., connect/disconnect). |
| `TerminalErrorRaised` | Raised when a terminal error occurs asynchronously. |

### Screen Reading Methods

#### `TerminalResultCode GetText(out string text, CommandOptions options = null)`

Reads the entire visible text content of the terminal screen.

**Parameters:**
- `text` (`out string`) — Receives the full screen text.
- `options` (`CommandOptions`, optional) — Timeout and wait mode. Defaults to `DefaultCmdOptions`.

**Returns:** `TerminalResultCode.Success` (or throws `TerminalConnectionException` on failure in coded workflow mode).

---

#### `TerminalResultCode GetTextAtPosition(TerminalField criteria, int? length, out string text, CommandOptions options = null)`

Reads text from the screen starting at the position defined by `criteria`. Optionally limits the number of characters read.

**Parameters:**
- `criteria` (`TerminalField`) — Defines the start position via `RowStart` / `ColStart`.
- `length` (`int?`, optional) — Number of characters to read. `null` reads to end of line.
- `text` (`out string`) — Receives the text read from the position.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode GetScreenArea(TerminalField criteria, out string text, CommandOptions options = null)`

Reads text from a rectangular region of the screen defined by `criteria`.

**Parameters:**
- `criteria` (`TerminalField`) — Defines the region using `RowStart`, `ColStart`, `RowEnd`, `ColEnd`.
- `text` (`out string`) — Receives the text from the region.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode GetColorAtPosition(int row, int column, out Color color, CommandOptions options = null)`

Gets the foreground color of the character at the specified position.

**Parameters:**
- `row` (`int`) — Row (1-based).
- `column` (`int`) — Column (1-based).
- `color` (`out Color`) — Receives the `System.Drawing.Color` value.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `ScreenData GetScreen(CommandOptions options = null)`

Returns the raw screen data object including all field attributes and character data.

**Parameters:**
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

**Returns:** `ScreenData` with screen content and field metadata, or `null` if not connected.

---

### Field Methods

#### `TerminalResultCode GetField(TerminalField field, out string text, CommandOptions options = null)`

Reads the text content of a field identified by its criteria (label, index, or coordinates).

**Parameters:**
- `field` (`TerminalField`) — Field identification. Set `LabeledBy`, `FollowedBy`, `Index`, or coordinate properties.
- `text` (`out string`) — Receives the field text.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode SetField(TerminalField criteria, string text, CommandOptions options = null)`

Writes text into the field matching the criteria.

**Parameters:**
- `criteria` (`TerminalField`) — Field identification. Set `LabeledBy`, `FollowedBy`, `Index`, or coordinate properties.
- `text` (`string`) — Text to write.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

### Cursor Methods

#### `TerminalResultCode GetCursorPosition(out CursorPosition cursorPosition, CommandOptions options = null)`

Gets the current row and column of the terminal cursor.

**Parameters:**
- `cursorPosition` (`out CursorPosition`) — Receives the cursor position (`Row`, `Column`).
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode MoveCursor(int row, int column, CommandOptions options = null)`

Moves the terminal cursor to the specified row and column.

**Parameters:**
- `row` (`int`) — Target row (1-based).
- `column` (`int`) — Target column (1-based).
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode MoveCursor(CursorPosition cursor, CommandOptions options = null)`

Moves the cursor using a `CursorPosition` object.

**Parameters:**
- `cursor` (`CursorPosition`) — Target position.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

### Key Sending Methods

#### `TerminalResultCode SendKeys(string keys, CommandOptions options = null)`

Sends a text string to the terminal at the current cursor position.

**Parameters:**
- `keys` (`string`) — Text to send.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode SendKeysSecure(SecureString keys, CommandOptions options = null)`

Sends a `SecureString` to the terminal. The string is decrypted in-memory, sent, then the unmanaged buffer is zeroed. Use for passwords.

**Parameters:**
- `keys` (`SecureString`) — Secure text to send.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode SendControlKey(ControlKey key, CommandOptions options = null)`

Sends a control key (Tab, F1–F24, Transmit/Enter, arrow keys, etc.) to the terminal.

**Parameters:**
- `key` (`ControlKey`) — The control key to send. See `ControlKey` enum.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode SendControlKey(ControlKey key, int delayMS, CommandOptions options = null)`

Sends a control key then waits a specified number of milliseconds before returning. Useful when the host needs processing time after a key.

**Parameters:**
- `key` (`ControlKey`) — The control key to send.
- `delayMS` (`int`) — Milliseconds to sleep after sending the key.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

### Wait Methods

#### `TerminalResultCode WaitScreenReady(CommandOptions options = null)`

Waits until the terminal keyboard is unlocked and the screen is ready for input.

**Parameters:**
- `options` (`CommandOptions`, optional) — Timeout and wait mode. Set `Timeout` to control how long to wait.

---

#### `TerminalResultCode WaitText(string text, TerminalField criteria = null, bool matchCase = true, CommandOptions options = null)`

Waits until the specified text appears on the terminal screen (or in a specific field if `criteria` is provided).

**Parameters:**
- `text` (`string`) — Text to wait for.
- `criteria` (`TerminalField`, optional) — When set, waits for the text in the specific field. When `null`, waits for the text anywhere on the screen.
- `matchCase` (`bool`, optional) — Case-sensitive comparison. Default: `true`.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

#### `TerminalResultCode FindTextInScreen(string text, CursorPosition startPosition, bool ignoreCase, out CursorPosition position, CommandOptions options = null)`

Searches the screen for a text string starting from `startPosition`.

**Parameters:**
- `text` (`string`) — Text to search for.
- `startPosition` (`CursorPosition`) — Starting search position.
- `ignoreCase` (`bool`) — Case-insensitive search.
- `position` (`out CursorPosition`) — Receives the coordinates where text was found.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

**Returns:** `TerminalResultCode.Success` if found; throws (or returns `InvalidCoordinates`) if not found.

---

### Connection Lifecycle

#### `TerminalResultCode Disconnect(CommandOptions options = null)`

Disconnects from the host while keeping the connection object alive (does not dispose). Rarely needed — `Dispose()` handles cleanup.

#### `void Shutdown()`

Alias for `Dispose()`. Disconnects, shuts down host processes, and releases resources.

#### `void Dispose()`

Disconnects the session, terminates any host broker processes (x86/x64), and releases all managed and unmanaged resources.

---

### Advanced

#### `TerminalResultCode OverrideScreenResolution(ScreenSize screenSize, CommandOptions options = null)`

Overrides the terminal screen dimensions. Use when the host requires a non-standard screen size.

**Parameters:**
- `screenSize` (`ScreenSize`) — Target screen dimensions.
- `options` (`CommandOptions`, optional) — Timeout and wait mode.

---

## Options & Configuration Classes

### `CommandOptions`

Controls timeout and screen-wait behavior for individual terminal operations.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Timeout` | `int` | `30000` | Milliseconds to wait before throwing a timeout error. When `0` or negative, falls back to the service default of 30000 ms. |
| `WaitType` | `WaitMode` | `READY` | How to wait for the screen before executing the operation. |

```csharp
// Example: 10-second timeout, wait for screen ready
var opts = new CommandOptions(WaitMode.READY, 10000);
```

### `ConnectionData`

Programmatic configuration object for terminal connections. Used with `GetConnection(ConnectionData)` and `GetSshConnection()`.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ProviderType` | `TerminalProviderType` | `UiPathNew` | Terminal emulator provider. Use `UiPathNew` for direct TCP/SSH connections. |
| `ConnectionType` | `ConnectionType` | `Profile` | How the connection is established: `Address` (host/port — required for `UiPathNew`), `Profile` (provider profile file), `LowLevel` (EHLLAPI). |
| `ConnectionProtocol` | `CommunicationType` | `TELNET` | Protocol: `TELNET`, `SSH`, or `HPVT`. |
| `TerminalType` | `TerminalType` | `Terminal3270` | Terminal emulation type. |
| `Host` | `string` | | Hostname or IP address of the target host. |
| `Port` | `int` | `23` | TCP port. Default is 23 (Telnet); SSH typically uses 22. |
| `ShowTerminal` | `bool` | `true` | Whether to display the terminal window (if supported by provider). |
| `EnableSSL` | `bool` | `false` | Enable SSL/TLS for the connection. |
| `Profile` | `string` | | Path to provider profile file (for profile-based providers: Attachmate, IBM, BlueZone, etc.). |
| `InProcessMode` | `bool` | `false` | Run the terminal provider in-process (Generic/EHLLAPI only). |
| `AttachExisting` | `bool` | `false` | Attach to an already-running terminal session. `true` value only available for the `Attachmate` provider| 
| `ProxyType` | `ProxyType` | `None` | Proxy type (None, HTTP, SOCKS4, SOCKS5). |
| `ProxyHost` | `string` | | Proxy server hostname. |
| `ProxyPort` | `int` | | Proxy server port. |
| `ProxyUser` | `string` | | Proxy authentication username. |
| `ProxyPassword` | `string` | | Proxy authentication password. |
| `InternalEncoding` | `string` | | Character encoding override (e.g., `"IBM037"` for EBCDIC). |
| `EhllDll` | `string` | | Path to EHLLAPI DLL (Generic provider). |
| `EhllFunction` | `string` | `"hllapi"` | EHLLAPI entry-point function name. |
| `EhllSession` | `string` | `"A"` | EHLLAPI session identifier. |
| `EhllEnhanced` | `bool` | `true` | Use enhanced EHLLAPI mode. |
| `EhllEncoding` | `string` | | Character encoding used for EHLLAPI text communication (Generic provider). Defaults to the provider's configured encoding if not set or unrecognized. |
| `EhllBasicMode` | `bool` | `false` | When `true`, disables field parsing on screen retrieval. Screen data is returned as raw text only, with no field metadata. Use for performance when field-level access is not needed (Generic provider). |
| `LuName` | `string` | | For 3270/5250: the SNA Logical Unit (LU) name to request from the host. For VT/Wyse/Linux: the terminal answerback string (use `^M` for carriage return). Has no effect on non-SNA or non-VT connections. |
| `TerminalModel` | `int` | `0` | Terminal model identifier. Use the enum value for the active `TerminalType`: `TerminalModes3270` (3270), `TerminalModes5250` (5250, defaults to `IBM_5250_3477_FC` when `0`), `TTVtTermId` (VT), `TerminalModesHP` (HP), `TerminalModesWyse` (Wyse), `TerminalModesLinux` (Linux). |

### `TerminalField`

Identifies a field or screen region for read/write operations.

| Property | Type | Description |
|----------|------|-------------|
| `RowStart` | `int` | Start row (1-based, or -1 for unset). |
| `ColStart` | `int` | Start column (1-based, or -1 for unset). |
| `RowEnd` | `int` | End row for area operations (-1 for unset). |
| `ColEnd` | `int` | End column for area operations (-1 for unset). |
| `LabeledBy` | `string` | Text of the label that precedes the field. |
| `FollowedBy` | `string` | Text of the label that follows the field. |
| `Index` | `int` | Zero-based field index (-1 for unset). |

### `CursorPosition`

Represents a row/column location on the terminal screen.

| Property | Type | Description |
|----------|------|-------------|
| `Row` | `int` | Row (1-based). Default: `1`. |
| `Column` | `int` | Column (1-based). Default: `1`. |

---

## Enum Reference

**`WaitMode`**: `NONE`, `READY`, `COMPLETE`
- `NONE` — Do not wait; execute immediately.
- `READY` — Wait for keyboard unlock before executing.
- `COMPLETE` — Wait for all screen data to arrive before executing.

**`TerminalProviderType`**: `UiPathNew`, `Attachmate`, `IBM`, `BlueZone`, `Generic`, `AttachmateExtra`, `ReflectionUnix`, `ReflectionIBM`, `Rumba`, `TandemHLL`
- `UiPathNew` — Direct TCP/SSH connection without a third-party emulator. Supports Telnet, SSH, and HPVT.
- `TandemHLL` — Tandem/NonStop host sessions via THLLAPI (`THLLW3.DLL` / `THLLW6.DLL`, Attachmate Reflection 6530). Uses `ConnectionType.LowLevel` and the same `Ehll*` fields as `Generic`. Color attribute data is not supported; `GetColorAtPosition` always returns `Color.LightGreen`.

**`CommunicationType`**: `TELNET`, `SSH`, `HPVT`

**`ConnectionType`**: `Address`, `Profile`, `LowLevel`
- `Address` — Connect by host/port. Required when using `ProviderType.UiPathNew`.
- `Profile` — Connect using a provider-specific profile file (path set via `Profile`).
- `LowLevel` — Connect via EHLLAPI (Generic provider) or THLLAPI (TandemHLL provider).

**`TerminalType`**: `Terminal3270`, `Terminal5250`, `TerminalVT`, `TerminalHP`, `TerminalANSI`, `TerminalT653X`, `TerminalSCOANSI`, `TerminalWYSE`, `TerminalLinux`

**`ControlKey`** (selected values): `Transmit`, `Tab`, `BackTab`, `Return`, `Escape`, `BackSpace`, `Home`, `End`, `Insert`, `Delete`, `PageUp`, `PageDown`, `Up`, `Down`, `Left`, `Right`, `F1`–`F24`, `Shift_F1`–`Shift_F12`, `Ctrl_F1`–`Ctrl_F12`, `Alt_F1`–`Alt_F12`, `PA1`–`PA3`, `Clear`, `Reset`, `Attention`, `EraseEOF`, `EraseInput`, `CursorSelect`, `FieldPlus`, `FieldMinus`, `FieldExit`, `Ctrl_A`–`Ctrl_Z`, `Tandem_Horizontal_Tab`, `Tandem_Vertical_Tab`

**`TerminalModes3270`** (use with `TerminalType.Terminal3270`): `IBM_3270_3278_2` (0), `IBM_3270_3278_3` (1), `IBM_3270_3278_4` (2), `IBM_3270_3278_5` (3), `IBM_3270_3279_2` (4), `IBM_3270_3279_3` (5), `IBM_3270_3279_4` (6), `IBM_3270_3279_5` (7)

**`TerminalModes5250`** (use with `TerminalType.Terminal5250`): `IBM_5250_3179_2` (54), `IBM_5250_3179_220` (60), `IBM_5250_3180_2` (52), `IBM_5250_3196_A1` (53), `IBM_5250_3477_FG` (61), `IBM_5250_3477_FC` (62), `IBM_5250_5251_1` (55), `IBM_5250_5251_11` (56), `IBM_5250_5252` (57), `IBM_5250_5291_1` (58), `IBM_5250_5292_2` (59), `IBM_5250_5555_C01` (64), `IBM_5250_5555_B01` (65), `IBM_5250_Printer` (63)

**`TTVtTermId`** (use with `TerminalType.TerminalVT`): `VT100` (0), `VT101` (1), `VT102` (2), `VT220` (3), `VT240` (4), `VT320` (5), `VT340` (6), `VT420` (7), `VT100W` (10), `VT101W` (11), `VT102W` (12), `VT220w` (13), `VT240W` (14), `VT320W` (15), `VT340W` (16), `VT420W` (17), `VT100M` (20), `VT101M` (21), `VT102M` (22), `VT220M` (23), `VT240M` (24), `VT320M` (25), `VT340M` (26), `VT420M` (27)

**`TerminalModesHP`** (use with `TerminalType.TerminalHP`): `HP_2372A` (0), `HP_70092` (1), `HP_70094` (2)

**`TerminalModesWyse`** (use with `TerminalType.TerminalWYSE`): `WYSE_50_24_80` (0), `WYSE_50_24_132` (10), `WYSE_60_24_80` (1), `WYSE_60_24_132` (11), `WYSE_60_42_80` (41), `WYSE_60_42_132` (51), `WYSE_60_43_80` (61), `WYSE_60_43_132` (71), `WYSE_350_24_80` (2), `WYSE_350_24_132` (12)

**`TerminalModesLinux`** (use with `TerminalType.TerminalLinux`): `Linux_24_80` (0), `Linux_24_132` (1), `Linux_36_80` (2), `Linux_36_132` (3), `Linux_48_80` (4), `Linux_48_132` (5)

---

## Common Patterns

### Login to a 3270 host and read a field

```csharp
[Workflow]
public void Execute()
{
    var connData = new ConnectionData
    {
        Host = "mainframe.corp.com",
        Port = 23,
        TerminalType = TerminalType.Terminal3270,
        ProviderType = TerminalProviderType.UiPathNew,
        ConnectionType = ConnectionType.Address,
        ConnectionProtocol = CommunicationType.TELNET
    };

    using var conn = terminal.GetConnection(connData);

    // Wait for login screen, then type credentials
    conn.WaitText("ENTER USERID", options: new CommandOptions(WaitMode.READY, 30000));
    conn.SetField(new TerminalField { LabeledBy = "USERID" }, "myuser");
    conn.SetField(new TerminalField { LabeledBy = "PASSWORD" }, "mypassword");
    conn.SendControlKey(ControlKey.Transmit);

    // Wait for main menu
    conn.WaitScreenReady(new CommandOptions(WaitMode.READY, 15000));

    // Read data
    conn.GetText(out string screen);
    Log(screen);
}
```

---

### SSH connection with secure credentials

```csharp
[Workflow]
public void Execute()
{
    var controlKeyDelayMS = 1000;
    var connData = new ConnectionData
    {
        Host = "unix-server.corp.com",
        Port = 22,
        TerminalType = TerminalType.TerminalVT,
        ProviderType = TerminalProviderType.UiPathNew,
        ConnectionType = ConnectionType.Address,
        ConnectionProtocol = CommunicationType.SSH
    };

    // sshPwd is a SecureString variable, e.g., from Get Credential activity
    using var conn = terminal.GetSshConnection(connData, sshUser: "deploy", sshPassword: sshPwd);

    conn.WaitText("$", options: new CommandOptions(WaitMode.NONE, 10000));
    conn.SendKeys("ls -la /var/log");
    conn.SendControlKey(ControlKey.Transmit, controlKeyDelayMS);

    conn.GetText(out string output);
    Log(output);
}
```

---

### Navigate a menu by field position (EHLLAPI / Generic provider)

Use when automating a terminal session managed by a third-party emulator that exposes an EHLLAPI interface (e.g., a running IBM PCOMM or BlueZone session accessed via its EHLLAPI DLL).

```csharp
[Workflow]
public void Execute()
{
    var connData = new ConnectionData
    {
        ProviderType = TerminalProviderType.Generic,
        ConnectionType = ConnectionType.LowLevel,
        EhllDll = @"C:\Program Files\IBM\Personal Communications\PCSHLL32.DLL",
        EhllFunction = "hllapi",
        EhllSession = "A",
        EhllEnhanced = true
    };

    using var conn = terminal.GetConnection(connData);

    // Move cursor to the Option field and type a menu choice
    conn.MoveCursor(row: 4, column: 14);
    conn.SendKeys("2");
    conn.SendControlKey(ControlKey.Transmit);
    conn.WaitScreenReady(new CommandOptions(WaitMode.READY, 20000));

    // Read a region of the response screen (rows 5-20, full width)
    var region = new TerminalField { RowStart = 5, ColStart = 1, RowEnd = 20, ColEnd = 80 };
    conn.GetScreenArea(region, out string result);
    Log(result);
}
```

---

### Wait for processing and read a result field (IBM Personal Communications / saved profile)

Use when the connection is pre-configured in an IBM PCOMM workspace file (`.ws`). PCOMM must be installed on the robot machine.

```csharp
[Workflow]
public void Execute()
{
    var connData = new ConnectionData
    {
        ProviderType = TerminalProviderType.IBM,
        ConnectionType = ConnectionType.Profile,
        Mode = ConnectionMode.Play,
        ShowTerminal = true,
        Profile = @"C:\PComm\Profiles\MainframeSession.ws"
    };

    using var conn = terminal.GetConnection(connData);

    // Submit a transaction
    conn.SetField(new TerminalField { LabeledBy = "TRAN CODE" }, "INQ01");
    conn.SetField(new TerminalField { LabeledBy = "ACCOUNT  " }, accountNumber);
    conn.SendControlKey(ControlKey.Transmit);

    // Wait for either success or error indicator
    var opts = new CommandOptions(WaitMode.READY, 30000);
    conn.WaitScreenReady(opts);

    // Check status field
    conn.GetField(new TerminalField { LabeledBy = "STATUS   " }, out string status);
    if (status.Trim() == "00")
    {
        conn.GetField(new TerminalField { LabeledBy = "BALANCE  " }, out string balance);
        Log($"Balance: {balance}");
    }
    else
    {
        conn.GetText(out string screen);
        throw new Exception($"Transaction failed. Status: {status}. Screen: {screen}");
    }
}
```

---

### Detect a field color for conditional logic

```csharp
[Workflow]
public void Execute()
{
    var conn = terminal.GetConnection(connectionString);
    try
    {
        conn.WaitScreenReady(new CommandOptions(WaitMode.READY, 10000));

        // Check if the status indicator at row 24, col 1 is red (error)
        conn.GetColorAtPosition(24, 1, out Color statusColor);

        if (statusColor == Color.Red)
        {
            conn.GetText(out string errorScreen);
            Log($"Error screen detected: {errorScreen}");
        }
        else
        {
            conn.GetField(new TerminalField { Index = 0 }, out string firstField);
            Log($"First field: {firstField}");
        }
    }
    finally
    {
        conn.Dispose();
    }
}
```


---

### Connect to a Tandem/NonStop host via THLLAPI

Use when automating a Tandem/NonStop session running through Attachmate Reflection 6530. The `EhllFunction` entry point for THLLAPI is `"thllapi"` (not `"hllapi"`). Color attribute data is not available for this provider.

```csharp
[Workflow]
public void Execute()
{
    var connData = new ConnectionData
    {
        ProviderType = TerminalProviderType.TandemHLL,
        ConnectionType = ConnectionType.LowLevel,
        EhllDll = @"C:\Program Files\Attachmate\Reflection\THLLW6.DLL",
        EhllFunction = "thllapi",
        EhllSession = "A"
    };

    using var conn = terminal.GetConnection(connData);

    conn.WaitScreenReady(new CommandOptions(WaitMode.READY, 15000));

    // Type a command and submit with Horizontal Tab to move between fields
    conn.SetField(new TerminalField { LabeledBy = "LOGON:" }, "myuser");
    conn.SendControlKey(ControlKey.Tandem_Horizontal_Tab);
    conn.SetField(new TerminalField { LabeledBy = "PASSWORD:" }, "mypassword");
    conn.SendControlKey(ControlKey.Return);

    conn.WaitScreenReady(new CommandOptions(WaitMode.READY, 15000));
    conn.GetText(out string screen);
    Log(screen);
}
```
