# Terminal Activities

`UiPath.Terminal.Activities`

Terminal emulation activities for automating interactions with IBM 3270/5250, VT, HP, and other legacy terminal systems. Supports BlueZone, IBM PCOMM, Attachmate, and direct TCP/SSH connections.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/coded-api.md) — Service API for coded C# workflows
- [Machine-readable activity index](activities.json) — JSON listing of every activity's class name, required properties, output properties, and doc path. For code generators and agents that need the activity surface without parsing markdown.

## If you want to ...

Quick task → activity lookup. Each row points at the activity that does the thing with the fewest assumptions.

| Task | Use |
|------|-----|
| Open a session and run a few activities | [`TerminalSession`](activities/TerminalSession.md) (start here) |
| **Synchronize before any read or write** | [`WaitScreenText`](activities/WaitScreenText.md) (most reliable), [`WaitScreenReady`](activities/WaitScreenReady.md) (after a control key), [`WaitTextAtPosition`](activities/WaitTextAtPosition.md), or [`WaitFieldText`](activities/WaitFieldText.md). Reading without a preceding wait returns stale data on real hosts. |
| Type a literal string into the terminal | [`SendKeys`](activities/SendKeys.md) |
| Type a password without logging it | [`SendKeysSecure`](activities/SendKeysSecure.md) |
| Press Enter, Tab, F-keys, or any control key | [`SendControlKey`](activities/SendControlKey.md) (use `Transmit` for 3270 enter, `Return` for VT enter) |
| Wait for the keyboard to unlock after sending a key | [`WaitScreenReady`](activities/WaitScreenReady.md) |
| Wait for specific text to appear anywhere | [`WaitScreenText`](activities/WaitScreenText.md) |
| Wait for specific text at known coordinates | [`WaitTextAtPosition`](activities/WaitTextAtPosition.md) |
| Wait for a named input field to contain text | [`WaitFieldText`](activities/WaitFieldText.md) |
| Read the entire visible screen | [`GetText`](activities/GetText.md) |
| Read a rectangular region | [`GetScreenArea`](activities/GetScreenArea.md) |
| **Extract tabular data into a `DataTable`** | [`GetScreenArea`](activities/GetScreenArea.md) → `Generate Data Table` (from `UiPath.System.Activities`). See [GetScreenArea.md § Extracting tabular data as a DataTable](activities/GetScreenArea.md#extracting-tabular-data-as-a-datatable) |
| Read N characters starting at a row/col | [`GetTextAtPosition`](activities/GetTextAtPosition.md) (cross-provider safe) |
| Read the field at a row/col (provider-agnostic) | [`GetFieldAtPosition`](activities/GetFieldAtPosition.md) |
| Read a labeled input field (single-provider) | [`GetField`](activities/GetField.md) — see the [provider portability caveat](activities/GetField.md#prefer-position-based-reads-when-portability-matters); prefer position-based reads above if the workflow must run against multiple providers |
| Write to the field at a row/col (provider-agnostic) | [`SetFieldAtPosition`](activities/SetFieldAtPosition.md) |
| Write to a labeled input field (single-provider) | [`SetField`](activities/SetField.md) — see the [provider portability caveat](activities/SetField.md#prefer-position-based-writes-when-portability-matters); prefer [`MoveCursor`](activities/MoveCursor.md) + [`SendKeys`](activities/SendKeys.md) or `SetFieldAtPosition` for cross-provider work |
| Find where a string appears on screen | [`FindText`](activities/FindText.md) (returns Row/Column) |
| Move the cursor to coordinates | [`MoveCursor`](activities/MoveCursor.md) |
| Find a string and move the cursor there | [`MoveCursorToText`](activities/MoveCursorToText.md) |
| Read the current cursor location | [`GetCursorPosition`](activities/GetCursorPosition.md) |
| Detect a highlighted / error-colored character | [`GetColorAtPosition`](activities/GetColorAtPosition.md) |
| **Close a session you kept open via `OutputConnection`** | A second [`TerminalSession`](activities/TerminalSession.md#closing-a-saved-connection) with empty body and `CloseConnection="True"` |

## XAML Setup

All terminal activity XAML snippets in this documentation use the `uit:` prefix. The required namespace declaration on the root `<Activity>` element is:

```
xmlns:uit="http://schemas.uipath.com/workflow/activities/terminal"
```

Do **not** infer this URL from the package name — `clr-namespace:UiPath.Terminal.Activities;assembly=UiPath.Terminal.Activities` is plausible but incorrect; using it causes silent activity-resolution failures (`validate` passes, `build` fails with unknown element / member errors).

## Known Authoring Pitfalls

These trip both XAML and coded authors regularly. Read once before authoring; they do not surface as friendly error messages.

### `validate` clean ≠ buildable

`uip rpa validate` (and Studio's lightweight Validate button) checks XAML structure, references, expression syntax, and analyzer rules. It does **not** execute the WF activity-constraint runner for this package. Constraints — including the parent-scope check that ensures every child activity sits inside a `TerminalSession` — only run at **pack / build** time (`uip rpa build`, Studio's Pack/Publish). Consequences:

- A file that passes `validate` can still fail `build` with a constraint error.
- Iterating on `validate` alone is not sufficient verification. After every edit, also run `uip rpa build` (or pack from Studio) and treat that as the truthful check.
- A `validate` run can inherit the cached state of a prior `build`. If a previous `build` populated `.local/install/`, a subsequent `validate` may *also* surface the constraint runner's verdict — i.e. validate is not always stateless. If you see `validate` flip from clean to red after a build attempt, that is why.

### `String.Format(format, arg1, arg2, …)` in WF expressions can crash the interpreter

On newer .NET SDK toolchains (.NET 8+ Roslyn / BCL), the C# / VB compiler resolves `String.Format` calls with multiple arguments to overloads whose argument set involves `ReadOnlySpan<string>` (introduced in .NET 8). The WF expression *interpreter*, used by the activity-constraint runner at pack time, then tries to construct `Func<…, ReadOnlySpan<string>>` and fails with `TypeLoadException` — `ReadOnlySpan<T>` is a `ref struct` and cannot be a generic type argument. The full stack ends in `System.RuntimeType.MakeGenericType`.

Symptom (during `uip rpa build` or Studio Pack):

```
Internal constraint exception while running constraint with name 'Constraint<TerminalActivity<String>>'
  System.ArgumentException: GenericArguments[1], 'System.ReadOnlySpan`1[System.String]',
  on 'System.Linq.Expressions.Interpreter.FuncCallInstruction`2[T0,TRet]'
  violates the constraint of type 'TRet'.
  ---> System.TypeLoadException: …
```

Mitigations, any one of them:

- **Use `&` (VB) or `+` (C#) concatenation** to compose the string. Overload resolution stays on `String.Concat(string, string, …)`, no span overload involved.
- **For `ConnectionString` specifically, avoid string composition altogether** — build a typed `ConnectionData` and serialize it (see [authoring-paths.md § Option B](activities/TerminalSession/authoring-paths.md#option-b--xaml-build-a-connectiondata-and-serialize-with-connectionstringhelperserialize)).
- **Force the legacy `String.Format` overload** by passing an explicit `object[]`: `String.Format(format, New Object() { arg1, arg2, arg3 })`. The compiler binds to `String.Format(String, params Object[])` rather than the span family.
- **Pre-format outside the expression**: assemble the string in a coded helper or a sequence of `&` concatenations, then pass the result into the activity argument.

Note: this is not specific to Terminal Activities — any package whose constraints use the WF expression interpreter is affected. It surfaces here because most child activities in this package carry a parent-scope constraint that runs at pack time.

## Activities

### App Integration.Terminals

| Activity | Description |
|----------|-------------|
| [Terminal Session](activities/TerminalSession.md) | Container scope that establishes and manages a terminal connection for all child activities. |
| [Get Text](activities/GetText.md) | Reads the entire visible text content of the terminal screen. |
| [Get Field](activities/GetField.md) | Reads the text of a specific input field, identified by label, index, or adjacent label. |
| [Set Field](activities/SetField.md) | Writes text into a specific input field, identified by label, index, or adjacent label. |
| [Get Cursor Position](activities/GetCursorPosition.md) | Returns the current row and column of the terminal cursor. |
| [Send Control Key](activities/SendControlKey.md) | Sends a control key (Tab, F1–F24, Enter, etc.) to the terminal. |
| [Wait Screen Text](activities/WaitScreenText.md) | Waits until a specified text string appears anywhere on the terminal screen. |
| [Wait Field Text](activities/WaitFieldText.md) | Waits until a specific input field contains the expected text. |

### App Integration.Terminals.Advanced

| Activity | Description |
|----------|-------------|
| [Move Cursor](activities/MoveCursor.md) | Moves the terminal cursor to an exact row/column position. |
| [Send Keys](activities/SendKeys.md) | Sends a raw text string or key sequence directly to the terminal. |
| [Send Keys Secure](activities/SendKeysSecure.md) | Sends a `SecureString` (e.g., a password) to the terminal without exposing it as plain text. |
| [Wait Screen Ready](activities/WaitScreenReady.md) | Waits until the terminal keyboard is unlocked and the screen is ready for input. |
| [Get Screen Area](activities/GetScreenArea.md) | Reads the text from a rectangular region of the terminal screen defined by start and end coordinates. |
| [Get Text at Position](activities/GetTextAtPosition.md) | Reads text starting at a specific row/column, optionally limited to a given length. |
| [Get Field at Position](activities/GetFieldAtPosition.md) | Reads the content of the field that starts at the specified row/column position. |
| [Get Color at Position](activities/GetColorAtPosition.md) | Returns the foreground color of the character at the specified row/column. |
| [Set Field at Position](activities/SetFieldAtPosition.md) | Writes text into the field at a specific row/column position. |
| [Wait Text at Position](activities/WaitTextAtPosition.md) | Waits until a specific row/column position contains the expected text. |
| [Find Text](activities/FindText.md) | Searches the screen for a text string, starting from an optional position, and returns the coordinates where it was found. |
| [Move Cursor to Text](activities/MoveCursorToText.md) | Searches the screen for a text string and moves the terminal cursor to the location where it was found. |
