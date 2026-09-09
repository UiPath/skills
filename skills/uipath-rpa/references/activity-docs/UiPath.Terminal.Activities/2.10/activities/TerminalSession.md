# Terminal Session

`UiPath.Terminal.Activities.TerminalSession`

Container scope activity that establishes a terminal connection and provides it to all child activities. All other terminal activities must be placed inside a Terminal Session. Supports creating new connections (via connection string), reusing an existing open connection, and SSH authentication. Supported providers include BlueZone, IBM PCOMM, Attachmate, direct TCP/SSH (UiPathNew), EHLLAPI (Generic), and Tandem/NonStop via THLLAPI (TandemHLL).

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals  

## Quickstart

Connect to a Telnet host, wait for the prompt, type a command, read a row, log it. The skeleton below is a complete, paste-ready workflow body — swap `Host`/`Port` in the connection string and replace the four child activities to fit your scenario.

```xml
<Activity xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:ui="http://schemas.uipath.com/workflow/activities"
          xmlns:uit="http://schemas.uipath.com/workflow/activities/terminal"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <Sequence>
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="screenText" />
    </Sequence.Variables>
    <uit:TerminalSession DisplayName="Telnet"
                         ConnectionString="{}{'AttachExisting':false,'ConnectionProtocol':0,'ConnectionType':1,'EhllBasicMode':false,'EhllDll':null,'EhllEnhanced':true,'EhllFunction':'hllapi','EhllSession':'A','EnableSSL':false,'Host':'myhost.com','InProcessMode':false,'InternalEncoding':'ASCII','Mode':1,'Port':23,'Profile':null,'ProviderType':9,'ProxyHost':null,'ProxyPassword':null,'ProxyPort':0,'ProxyType':0,'ProxyUser':null,'ShowTerminal':true,'TerminalModel':3,'TerminalType':2}"
                         TimeoutMS="60000" DelayMS="2000" CloseConnection="True">
      <uit:TerminalSession.Body>
        <ActivityAction x:TypeArguments="uit:TerminalConnection">
          <ActivityAction.Argument>
            <DelegateInArgument x:TypeArguments="uit:TerminalConnection" Name="terminalSession" />
          </ActivityAction.Argument>
          <Sequence DisplayName="Interaction">
            <uit:TerminalWaitScreenText Text="[&quot;login:&quot;]" />
            <uit:TerminalSendKeys Keys="[&quot;help&quot;]" />
            <uit:TerminalSendControlKey Key="Return" />
            <uit:TerminalGetTextAtPosition Row="[3]" Column="[1]" Text="[screenText]" />
          </Sequence>
        </ActivityAction>
      </uit:TerminalSession.Body>
    </uit:TerminalSession>
    <ui:LogMessage Level="Info" Message="[screenText]" />
  </Sequence>
</Activity>
```

What to change for your scenario:

- **`Host` and `Port`** in the connection string (the `…'Host':'myhost.com',…'Port':23,…` fields).
- **`EnableSSL`** (set `'EnableSSL':true` and choose the appropriate TLS port — e.g. `992` for TN5250/TN3270 over TLS) if your host requires it.
- **`TerminalType` and `TerminalModel`** for 3270 / 5250 / different VT models — see [Starter literals](#starter-literals) for ready-to-paste alternatives.
- **The four child activities** — they read like a recipe: wait for something, send something, wait for something else, read something. Add as many siblings as you need inside the inner `<Sequence>`.

Need a different provider (BlueZone, IBM PCOMM, Attachmate) or SSH? Hand-deriving the connection-string integers is unsafe — see [authoring-paths.md § Option B](TerminalSession/authoring-paths.md#option-b--xaml-build-a-connectiondata-and-serialize-with-connectionstringhelperserialize) for the helper-based approach that uses real enum names.

For multi-activity sessions, more property detail, the existing-connection mode, and tuning, continue below.

## Properties

### New Session

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionString` | Connection String | `InArgument` | `string` | | | JSON-serialized `UiPath.Terminal.Data.ConnectionData`. See [Connection String Format](#connection-string-format) below — the format has serializer quirks that differ from canonical JSON and the activity validator rejects strings that don't match. Use the **Connection Settings** button in the designer to build this value visually. |

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

Connection-level timing. Defaults work for typical LAN hosts; raise both when connecting over TLS, VPN, or to slow remote hosts.

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `TimeoutMS` | TimeoutMS | `InArgument` | `int` | `50000` | Milliseconds to wait for the terminal connection to be established. |
| `DelayMS` | DelayMS | `InArgument` | `int` | `1000` | Milliseconds to wait after the connection is established before scheduling child activities. **Raise to 3000–5000 ms for TLS hosts** to let TN3270/TN5250 protocol negotiation finish before the first child activity runs — otherwise a leading `WaitScreenReady` can throw `ErrorWaitReady` against an otherwise-healthy connection. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `OutputConnection` | Output Connection | `OutArgument` | `TerminalConnection` | Stores the opened connection object so it can be reused in a later Terminal Session (via `ExistingConnection`). If not set, the connection is closed automatically when the scope ends. Only applies to Mode A (new connection). |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | `false` | When `true`, the workflow continues execution even if this activity throws an error. |

## Valid Configurations

This activity supports two mutually exclusive connection modes. `ConnectionString` and `ExistingConnection` cannot both be set — a validation error is raised at design time.

**Mode A — New Connection**: Set `ConnectionString`. The session opens a new connection. Optionally set `OutputConnection` to keep the connection alive after the scope exits.

**Mode B — Existing Connection**: Set `ExistingConnection` with a previously opened `TerminalConnection` variable. Optionally set `CloseConnection = false` to leave it open after the scope.

### Closing a saved connection

When you keep a connection alive via `OutputConnection`, you are responsible for closing it before the workflow ends — leaving connections open can hurt performance and interfere with subsequent terminal sessions (the provider may refuse new connections or reuse a stale handle).

Pattern: add a final `TerminalSession` with no child activities, point `ExistingConnection` at the saved variable, and set `CloseConnection="True"`:

```xml
<uit:TerminalSession DisplayName="Close session"
                     ExistingConnection="[savedConn]"
                     CloseConnection="True">
  <uit:TerminalSession.Body>
    <ActivityAction x:TypeArguments="uit:TerminalConnection">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="uit:TerminalConnection" Name="terminalSession" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Close" />
    </ActivityAction>
  </uit:TerminalSession.Body>
</uit:TerminalSession>
```

The `Sequence` body is required by the XAML schema even though it has no children — analyzer rule `ST-MRD-008 (Empty Sequence)` will flag it; suppress via an annotation or move the close call into a finally branch of a `TryCatch`. Alternatively, do not use `OutputConnection` in the first place — let the original scope close the connection on exit.

## Notes

- All other terminal activities must be placed inside this scope.
- **Always wait for the screen before reading or writing.** Begin every screen interaction with a `WaitScreenText`, `WaitScreenReady`, `WaitFieldText`, or `WaitTextAtPosition` to confirm the host has finished the previous redraw. Reading too early returns stale data or a partial screen, and the same activity will pass on a fast localhost session and fail intermittently against a real host.
- **Do not nest `TerminalSession` activities.** Placing one `TerminalSession` inside another's `Body` — directly, or indirectly via `Invoke Workflow File` or a library activity that itself opens a session against the same connection — produces undefined behavior (the inner scope may attach to or steal the outer scope's connection). Open exactly one scope per connection; reuse the connection across logical steps via `OutputConnection` + `ExistingConnection` instead of nesting.
- **IBM EHLLAPI provider: skip `OutputConnection` / `ExistingConnection`.** With the `IBM` provider (and `Generic` in `LowLevel` mode), the underlying terminal emulator already persists the session — adding the activity's own persistence layer is redundant and forces an extra explicit-close pattern. Open a fresh `TerminalSession` each time you need to interact; the emulator side stays connected.
- If `OutputConnection` is set, `CloseConnection` is automatically forced to `false`.
- The connection string must not reference the deprecated `UiPathInternal` provider type (validation error is raised).
- For Tandem/NonStop sessions, use the `TandemHLL` provider type with `ConnectionType.LowLevel`. The connection uses the same EHLLAPI-style fields (`EhllDll`, `EhllSession`, etc.) but targets `THLLW3.DLL` or `THLLW6.DLL` (Attachmate Reflection 6530). Color information is not available for this provider.
- SSH credentials are only used when the connection string's protocol is SSH. For non-SSH connections, `SSHUserName` and `SSHPassword` are ignored.
- Use the **Connection Settings** button in the UiPath Studio designer to build the connection string visually (not available in Studio Web).
- Use the **Run Wizard** button to launch the Terminal Recorder (not available in Studio Web, requires a literal connection string).

## Connection String Format

`ConnectionString` is a JSON-serialized `UiPath.Terminal.Data.ConnectionData`. The property surface is documented in [coded-api.md § ConnectionData](../coded/coded-api.md#connectiondata). The serialized form has several quirks that differ from canonical JSON — generating it by hand from those property descriptions will produce strings the validator rejects with `Invalid connection string`.

**Serialization rules:**

- **Single quotes** around property names and string values (not double quotes). This is a deliberate choice that lets the string be embedded in an XAML attribute without `&quot;` escaping.
- **Enums as integer values**, not string names (`'ConnectionProtocol':0`, not `'ConnectionProtocol':'TELNET'`). The integers do NOT match the order the enum members appear in the reference lists in `coded-api.md` — those lists are by display order, not numeric value. **Do not hand-derive the integers** from the docs; copy them from a Studio-generated example or use the helper (see [authoring-paths.md](TerminalSession/authoring-paths.md)).
- **All `ConnectionData` properties must be present**, including ones that are null or default for your scenario (EHLLAPI fields, proxy fields, etc.). The validator rejects partial objects.
- **PascalCase property names**, identical to the C# `ConnectionData` field names.

**XAML attribute encoding:**

When set via attribute form, the value must be **prefixed with `{}`** (the XAML literal-string escape). XAML treats any attribute value starting with `{` as a markup extension (e.g. `{x:Null}`), so a raw JSON string starting with `{` crashes the parser with `XamlParseException: Quote characters ' or " are only allowed at the start of values`. The `{}` prefix tells the parser "this is a literal string". Single quotes in the JSON keep the XAML attribute itself free of `&quot;` escaping.

**Canonical reference:** the connection string produced by Studio's **Connection Settings** dialog is the authoritative source. Copy the generated string and substitute scenario-specific fields (`Host`, `Port`, `EnableSSL`, `Profile`, etc.) — keep all other fields and the integer enum values exactly as Studio emits them.

## Choosing an authoring path

| Your situation | Use |
|----------------|-----|
| You have a known-good literal connection string (Studio-generated, Asset, config) | **Option A — literal `ConnectionString`** (this doc, [Starter literals](#starter-literals) below) |
| Authoring outside Studio Desktop (Studio Web, CLI, PR review) | **Option B — XAML helper** ([authoring-paths.md](TerminalSession/authoring-paths.md#option-b--xaml-build-a-connectiondata-and-serialize-with-connectionstringhelperserialize)) |
| Coded C# workflow | **Option C — `terminal.GetConnection`** ([coded-api.md § Coded Quickstart](../coded/coded-api.md#coded-quickstart)) |
| Need a non-`UiPathNew` provider, SSH protocol, or unusual `TerminalType` | **Option B** — hand-deriving the enum integers is unsafe; the helper uses real enum names |

Option A is the only path that keeps Studio Desktop's **Connection Settings** dialog and **Terminal Recorder** functional, because both need a literal value at design time.

### Starter literals

Pick the closest row, copy the connection string, swap `Host` and `Port`. Substitute it for the `ConnectionString` attribute value in the [XAML Example](#xaml-example) below (remember the `{}` prefix when used as an attribute).

All starter literals below use `ProviderType=9` (`UiPathNew`), `ConnectionType=1` (`Address`), `ConnectionProtocol=0` (`TELNET`). For other providers, SSH, or `ConnectionType.LowLevel`, use [Option B](TerminalSession/authoring-paths.md#option-b--xaml-build-a-connectiondata-and-serialize-with-connectionstringhelperserialize).

| Scenario | `EnableSSL` | `Port` | `TerminalType` | `TerminalModel` | Notes |
|----------|-------------|--------|----------------|------------------|-------|
| DEC VT (VT220 default) over plain Telnet | `false` | `23` | `2` | `3` (VT220) | The general-purpose default for legacy UNIX hosts. |
| DEC VT (VT100) over plain Telnet | `false` | `23` | `2` | `0` (VT100) | Use when the host expects strict VT100 (no VT220 device attrs). |
| IBM 5250 (TN5250) over plain Telnet | `false` | `23` | `1` | `0` (default: `IBM_5250_3477_FC`) | Plain TN5250 — uncommon in production, useful for tests. |
| IBM 5250 over TLS (TN5250s) | `true` | `992` | `1` | `0` (default: `IBM_5250_3477_FC`) | The IBM i / AS/400 standard for secure TN5250. |

For VT model variants other than `0` / `3`, see [`TTVtTermId` in coded-api.md](../coded/coded-api.md#enum-reference) for the full integer table.

**Worked literal 1 — Plain Telnet, VT220 (the Quickstart default):**

```
{'AttachExisting':false,'ConnectionProtocol':0,'ConnectionType':1,'EhllBasicMode':false,'EhllDll':null,'EhllEnhanced':true,'EhllFunction':'hllapi','EhllSession':'A','EnableSSL':false,'Host':'myhost.com','InProcessMode':false,'InternalEncoding':'ASCII','Mode':1,'Port':23,'Profile':null,'ProviderType':9,'ProxyHost':null,'ProxyPassword':null,'ProxyPort':0,'ProxyType':0,'ProxyUser':null,'ShowTerminal':true,'TerminalModel':3,'TerminalType':2}
```

**Worked literal 2 — TN5250 over TLS (IBM i / AS/400), TLS port 992:**

```
{'AttachExisting':false,'ConnectionProtocol':0,'ConnectionType':1,'EhllBasicMode':false,'EhllDll':null,'EhllEnhanced':true,'EhllFunction':'hllapi','EhllSession':'A','EnableSSL':true,'Host':'pub400.com','InProcessMode':false,'InternalEncoding':'ASCII','Mode':1,'Port':992,'Profile':null,'ProviderType':9,'ProxyHost':null,'ProxyPassword':null,'ProxyPort':0,'ProxyType':0,'ProxyUser':null,'ShowTerminal':true,'TerminalModel':0,'TerminalType':1}
```

To derive the other rows in the table, take Worked literal 1 and change only the cells listed for your row — leave every other field at the Studio-emitted default. In an XAML attribute the literal becomes `ConnectionString="{}{...}"` — the `{}` prefix tells the XAML parser the value is a literal string rather than a markup extension.

## XAML Example

The XAML namespace declaration `xmlns:uit="http://schemas.uipath.com/workflow/activities/terminal"` is required on the root `<Activity>` element (see [overview.md § XAML Setup](../overview.md#xaml-setup)).

**Mode A — New connection:**

```xml
<Activity xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:uit="http://schemas.uipath.com/workflow/activities/terminal"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <uit:TerminalSession DisplayName="Terminal Session"
                     ConnectionString="{}{'AttachExisting':false,'ConnectionProtocol':0,'ConnectionType':1,'EhllBasicMode':false,'EhllDll':null,'EhllEnhanced':true,'EhllFunction':'hllapi','EhllSession':'A','EnableSSL':false,'Host':'myhost.com','InProcessMode':false,'InternalEncoding':'ASCII','Mode':1,'Port':23,'Profile':null,'ProviderType':9,'ProxyHost':null,'ProxyPassword':null,'ProxyPort':0,'ProxyType':0,'ProxyUser':null,'ShowTerminal':true,'TerminalModel':3,'TerminalType':2}"
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
</Activity>
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

## Child Activity Skeleton

Every per-activity doc in this package shows its activity element in isolation (just the `<uit:TerminalXxx … />` line). To use them, **nest them all inside a single `TerminalSession.Body` `Sequence`** — do not open one `TerminalSession` per child activity. One scope = one network connection; opening a scope per activity multiplies connect latency and breaks any logical session continuity (cursor position, screen state, locks).

Skeleton showing three child activities (set a field, transmit, read result screen) under one scope:

```xml
<uit:TerminalSession DisplayName="Terminal Session"
                   ConnectionString="{}{...}"
                   TimeoutMS="50000"
                   CloseConnection="True"
                   DelayMS="1000">
  <uit:TerminalSession.Body>
    <ActivityAction x:TypeArguments="uit:TerminalConnection">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="uit:TerminalConnection" Name="terminalSession" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <uit:TerminalSetField DisplayName="Set User ID" Text="myuser" DelayMS="300" TimeoutMS="5000" WaitType="READY">
          <uit:TerminalSetField.Field>
            <InArgument x:TypeArguments="uit:TerminalField">
              <uit:TerminalField LabeledBy="User" />
            </InArgument>
          </uit:TerminalSetField.Field>
        </uit:TerminalSetField>
        <uit:TerminalSendControlKey DisplayName="Transmit" Key="Transmit" DelayMS="1000" TimeoutMS="5000" WaitType="READY" />
        <uit:TerminalGetText DisplayName="Read result screen" Text="[screenText]" DelayMS="300" TimeoutMS="5000" WaitType="READY" />
      </Sequence>
    </ActivityAction>
  </uit:TerminalSession.Body>
</uit:TerminalSession>
```

Composition rules:
- All child activities go into the same inner `<Sequence DisplayName="Do">`. The `Sequence` is required; child activities cannot be direct children of `ActivityAction`.
- Per-activity docs show snippets *without* this wrapper deliberately — copy the activity element only and append it to the inner `Sequence` as a sibling of any existing children. Do not copy a child snippet's surrounding scope; there is no surrounding scope in a child snippet.
- The `DelegateInArgument` Name (`terminalSession` above) is the in-scope handle to the open connection. Child activities pick it up implicitly via the parent-chain validation constraint; you do not need to reference it by name in the child activities' attributes.
- **`DisplayName` uniqueness:** the inner `Sequence`'s `DisplayName="Do"` (and the outer `TerminalSession`'s `DisplayName="Terminal Session"`) collide with workflow analyzer rule `ST-NMG-004 (Display Name Duplication)` if you author more than one session in the same file. Rename one or both per session — e.g. `DisplayName="Mainframe Session"` / `DisplayName="Mainframe Steps"` — to keep the rule clean.

## References

- [Authoring `ConnectionString` Outside Studio Desktop](TerminalSession/authoring-paths.md) — Options B and C for building the connection string without the Studio designer (Studio Web, CLI authoring, coded workflows).
- [Common Options](TerminalSession/_common-options.md) — The shared `TimeoutMS` / `DelayMS` / `WaitType` properties carried by every child activity of this scope.
