# Invoking PowerShell from RPA Workflows

## Default: Use a Coded Workflow Instead

When the impulse is "drop into PowerShell," reach for a coded workflow (`[Workflow]` in a `.cs` file) first. A coded workflow runs in-process, surfaces real exceptions, and lives in one file with the rest of the project.

Reach for PowerShell only when:

1. The script needs Windows-admin cmdlets (`Get-ADUser`, `Mount-*`, etc.) awkward to call from .NET.
2. The project already has `.ps1` scripts you must edit (don't rewrite for its own sake).
3. Logic is genuinely PS-shaped (modules, pipeline-style data flow).

For SharePoint REST, HTTP uploads, JSON parsing, file mangling — write a coded workflow. See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md).

## When You Need PowerShell — Use the `InvokePowerShell` Activity

`UiPath.Core.Activities.InvokePowerShell<T>` (`UiPath.System.Activities`) is the supported path. **Do not shell out via `Invoke Process` + `powershell.exe`** — that path requires manual quote escaping, exit-code parsing, and a status-file dance. `InvokePowerShell` handles parameter binding and output collection directly, and exceptions propagate as activity faults.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| `CommandText` | `InArgument<string>` | Required. Script body or single command. |
| `IsScript` | `InArgument<bool>` | `true` → multi-line script. `false` → single cmdlet invocation. |
| `Parameters` | typed collection | Named bindings passed in. Verify the element type via `uip rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.InvokePowerShell\`1"`. |
| `Input` | `InArgument<IEnumerable>` | Pipeline input (`$input` inside the script). |
| `Output` | `OutArgument<IEnumerable<T>>` | Collected results. `T` is the activity's generic type argument (e.g. `PSObject`, `string`). |
| `PowerShellProcess` | enum | `WindowsPowerShell32` / `WindowsPowerShell64` / `PowerShellCore`. Pin the runtime explicitly. |
| `ContinueOnError` | `InArgument<bool>` | Default `false`. PS exceptions propagate as activity faults. |

### Minimal Pattern

```xml
<ui:InvokePowerShell x:TypeArguments="x:String"
    CommandText="[scriptBody]"
    IsScript="True"
    PowerShellProcess="WindowsPowerShell64"
    Output="[psOutput]" />
```

For typed parameter bindings, use the `Parameters` collection instead of building a command line — no string concatenation, no quote escaping. Look up the element type with `get-default-activity-xaml` before authoring.

### Choosing `PowerShellProcess`

| Value | Runtime | When to use |
|-------|---------|-------------|
| `WindowsPowerShell64` | Windows PowerShell 5.1, 64-bit | Default for Windows robots; broadest cmdlet compatibility. |
| `WindowsPowerShell32` | Windows PowerShell 5.1, 32-bit | Legacy 32-bit modules only. |
| `PowerShellCore` | PowerShell 7+ | Cross-platform. Requires `pwsh` installed on the robot. Needed for 7+-only features (`Invoke-WebRequest -InFile`, `ConvertFrom-Json -AsHashtable`, ternary, null-conditional, `&&`/`\|\|`). |

Always set `PowerShellProcess` explicitly so a robot upgrade does not silently change the runtime.

## Last-Resort `Invoke Process`

Some scenarios force a direct shellout — a vendor script with exact-CLI requirements, or an interactive session. In that case:

1. **Pin the executable.** `FileName="powershell.exe"` for 5.1, `FileName="pwsh.exe"` for 7+. Do not rely on PATH.
2. **Escape quotes in every value** embedded in `Arguments`. A single `"` or `'` in a path silently shifts every later positional arg.
   - VB: `value.Replace("""", """""")`
   - C#: `value.Replace("\"", "\"\"")`
3. **Status by file, not stdout.** `Invoke Process` returns the exit code only. Wrap the script body in `try { … } catch { Out-File -FilePath $statusFile -InputObject ("ERROR: " + $_.Exception.Message); exit 1 }` so failures are never silent. Read the file after, then delete it.

## Anti-Patterns

1. **Defaulting to PowerShell when a coded workflow would do.** See § Default.
2. **Using `Invoke Process` when `InvokePowerShell` works.** Skipping the typed activity for no reason triples the gotcha surface.
3. **Driving UI from PowerShell.** Use UiPath UIAutomation activities — see [ui-automation-guide.md](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code).
4. **Omitting `PowerShellProcess`.** A robot upgrade can silently land your script on a different runtime.
