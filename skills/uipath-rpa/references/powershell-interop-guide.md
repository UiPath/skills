# Invoking PowerShell from RPA Workflows

## Default: Use a Coded Workflow Instead

When the impulse is "drop into PowerShell," reach for a coded workflow (`[Workflow]` in a `.cs` file) first. A coded workflow:

- Runs in-process — no quote escaping, no exit code translation, no status-file dance.
- Targets a fixed .NET runtime — no PS 5.1 vs 7+ feature gap.
- Surfaces real exceptions with stack traces, debuggable in Studio.
- Lives in one file with the rest of the project.

Reach for PowerShell **only** when:

1. The project already has `.ps1` scripts you must edit (don't rewrite for its own sake).
2. The script needs Windows-admin cmdlets (`Get-ADUser`, `Mount-*`, etc.) awkward to call from .NET.
3. The robot machine blocks adding NuGet packages.

For SharePoint REST, HTTP uploads, JSON parsing, file mangling — write a coded workflow. See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md).

The rest of this guide covers the failure modes when PowerShell is unavoidable.

## Failure Modes Specific to `Invoke Process` + PowerShell

Two issues account for most incidents. Both fail at runtime, not `build`:

1. **Wrong PowerShell version.** `powershell.exe` = Windows PowerShell 5.1. `pwsh.exe` = PowerShell 7+ (only if installed separately).
2. **Argument string corruption.** Quotes in any value silently shift positional args.

### Which PowerShell Runs

| Executable | Version | Default install state |
|-----------|---------|------------------------|
| `powershell.exe` | Windows PowerShell **5.1** | Always present |
| `pwsh.exe`       | PowerShell **7+** | Only if installed |

If `Invoke Process` uses `FileName="powershell.exe"`, assume 5.1.

### PS 5.1 vs 7+ Feature Gap

These features need PS 6.0+. Using them under `powershell.exe` (5.1) fails at runtime:

| Feature | 5.1 | 7+ | Symptom in 5.1 |
|---------|-----|----|----------------|
| `Invoke-WebRequest -InFile` | no | yes | `A parameter cannot be found that matches parameter name 'InFile'` |
| `ConvertFrom-Json -AsHashtable` | no | yes | parameter not recognized |
| Ternary `cond ? a : b` | no | yes | `Unexpected token '?'` |
| Null-conditional `?.`, `?[]` | no | yes | parse error |
| `ForEach-Object -Parallel` | no | yes | parameter not recognized |
| Pipeline chain `&&` / `\|\|` | no | yes | parse error |

#### 5.1-Compatible Migrations

| 7+ | 5.1 |
|----|-----|
| `Invoke-WebRequest -InFile $p -Method Put -Uri $u` | `Invoke-RestMethod -Method Put -Uri $u -Body ([System.IO.File]::ReadAllBytes($p)) -ContentType 'application/octet-stream'` |
| `ConvertFrom-Json -AsHashtable` | `$obj = $json \| ConvertFrom-Json; $h = @{}; $obj.PSObject.Properties \| ForEach-Object { $h[$_.Name] = $_.Value }` |
| `$x ?? $default` | `if ($null -ne $x) { $x } else { $default }` |
| `cond ? a : b` | `if (cond) { a } else { b }` |
| `$obj?.Prop` | `if ($null -ne $obj) { $obj.Prop }` |

If you cannot control the target machine, refuse early:

```powershell
if ($PSVersionTable.PSVersion.Major -lt 7) {
    # fall back, or fail loudly
}
```

### Building `PSArguments` From a XAML Expression

Quotes inside any value close the surrounding `""…""` and shift every later positional arg. `build` does not catch this. Escape every value.

#### VB

```xml
<ui:InvokeProcess
    FileName="powershell.exe"
    Arguments='[String.Format(
        "-NoProfile -ExecutionPolicy Bypass -File ""{0}"" -SiteUrl ""{1}"" -RootFolder ""{2}"" -FilePath ""{3}""",
        ScriptPath.Replace("""", """"""),
        in_SPSiteUrl.Replace("""", """"""),
        in_RootFolder.Replace("""", """"""),
        in_FilePath.Replace("""", """"""))]' />
```

`""""` in VB inside `[…]` = one literal `"`; `""""""` = `""` (PS reads as one literal `"` inside double quotes).

#### C#

```xml
<InArgument x:TypeArguments="x:String">
  <CSharpValue x:TypeArguments="x:String">
    string.Format(
      "-NoProfile -ExecutionPolicy Bypass -File \"{0}\" -SiteUrl \"{1}\" -RootFolder \"{2}\" -FilePath \"{3}\"",
      ScriptPath.Replace("\"", "\"\""),
      in_SPSiteUrl.Replace("\"", "\"\""),
      in_RootFolder.Replace("\"", "\"\""),
      in_FilePath.Replace("\"", "\"\""))
  </CSharpValue>
</InArgument>
```

Default to escaping even when the value looks safe — cost is negligible, regression cost is high.

### Returning Status

`Invoke Process` returns the exit code, not stdout. Two patterns:

#### Status File (recommended)

The script writes one text file with `OK` or a one-line error. Workflow reads it after `Invoke Process`.

Two correctness rules:

1. **Always write the file, even on crash.** Wrap the body in `try { … } catch { Out-File -FilePath $statusFile -InputObject ("ERROR: " + $_.Exception.Message) -Encoding UTF8; exit 1 }`. Otherwise the workflow reads stale content from a previous run, or hits a generic "file not found" that hides the real failure.
2. **Delete after read, not before write.** Cleanup tied to "after read" makes status files self-cleaning. "Before write" leaves a window where a crashed prior run's file gets read by the next.

XAML layout after `Invoke Process`:

```text
Invoke Process (powershell.exe -File <script> …)
└── If (Not File.Exists(StatusFilePath))
    ├── Then: Throw BusinessRuleException("Script produced no status file at " + StatusFilePath)
    └── Else: Read Text File → status
              If (status starts with "ERROR")
              ├── Then: Throw BusinessRuleException(status)
              └── Else: continue
              Delete (Path = StatusFilePath)
```

`Throw` uses `s:Exception`-derived types — see [xaml/common-pitfalls.md § Invalid Use of `x:` Prefix](xaml/common-pitfalls.md#invalid-use-of-x-prefix-for-non-builtin-clr-types).

#### Exit Code Only

Use when the outcome is binary. `exit 0` on success, non-zero on failure; check `Invoke Process`'s `Result` output. If you mix both, document which is authoritative — usually the status file.

## Anti-Patterns

1. **Defaulting to PowerShell when a coded workflow would do.** See § Default above.
2. **Assuming `pwsh.exe` is available.** Default to `powershell.exe`; gate any 7+ feature behind a version check.
3. **Concatenating paths into `PSArguments` without escaping.** A single `"` or `'` shifts every positional arg.
4. **Driving UI from PowerShell.** Use UiPath UIAutomation activities — see [ui-automation-guide.md](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code).
5. **Capturing status via stdout.** Fragile across PS versions and locales. Use a status file or exit code.
