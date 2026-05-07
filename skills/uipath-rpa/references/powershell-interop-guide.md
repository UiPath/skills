# Invoking PowerShell from RPA Workflows

When an RPA workflow shells out to PowerShell — typically via `Invoke Process` (`UiPath.System.Activities`) or the legacy `InvokeCode`/`Start Process` patterns — two failure modes account for almost all incidents:

1. **Targeting the wrong PowerShell version.** `powershell.exe` is Windows PowerShell 5.1 and ships preinstalled; `pwsh.exe` is PowerShell 7+ and only exists if installed separately. Most LTS-class robot machines have only 5.1.
2. **Argument string corruption** when the XAML expression that builds `PSArguments` does not escape embedded double-quotes.

Both fail at runtime, not at `build`. Plan for them at design time.

## Which PowerShell Runs?

| Executable | Version | Install state on a default Windows robot |
|-----------|---------|------------------------------------------|
| `powershell.exe` | Windows PowerShell **5.1** | Always present |
| `pwsh.exe`       | PowerShell **7+** (cross-platform) | Only if PS 7 was installed; not present by default |

If the workflow does not pin a version and uses `Invoke Process` with `FileName="powershell.exe"`, **assume 5.1**. Audit the script against the PS 5.1 vs 7+ feature gap below before shipping.

## PS 5.1 vs 7+ Cheat Sheet (common gotchas)

The features below were added in PowerShell 6.0+. Using them in a script that runs under `powershell.exe` (5.1) fails at runtime with parse or parameter errors:

| Feature | PS 5.1 | PS 7+ | Symptom in 5.1 |
|---------|--------|-------|----------------|
| `Invoke-WebRequest -InFile <path>` (request body from file) | not supported | supported | `A parameter cannot be found that matches parameter name 'InFile'` |
| `ConvertFrom-Json -AsHashtable` | not supported | supported | Same — parameter not recognized |
| Ternary expression `condition ? a : b` | parse error | supported | `Unexpected token '?' in expression` |
| Null-conditional `?.` and `?[]` | parse error | supported | Same |
| `ForEach-Object -Parallel` | not supported | supported | Parameter not recognized |
| `Where-Object` chained property accessors with `?.` | parse error | supported | Parse error |
| Pipeline chain operators `&&` / `||` | parse error | supported | Parse error |
| `Test-Json` | available | available | OK in both |

### Migration patterns when stuck on 5.1

| You wanted (PS 7+) | Use instead (PS 5.1-compatible) |
|--------------------|---------------------------------|
| `Invoke-WebRequest -InFile $path -Method Put -Uri $u` | `Invoke-RestMethod -Method Put -Uri $u -Body ([System.IO.File]::ReadAllBytes($path)) -ContentType 'application/octet-stream'` |
| `ConvertFrom-Json -AsHashtable` | `$obj = $json \| ConvertFrom-Json; $hash = @{}; $obj.PSObject.Properties \| ForEach-Object { $hash[$_.Name] = $_.Value }` |
| `$x ?? $default` | `if ($null -ne $x) { $x } else { $default }` |
| `condition ? a : b` | `if (condition) { a } else { b }` |
| `$obj?.Prop` | `if ($null -ne $obj) { $obj.Prop }` |

### Detection

If you do not control the target machine, ask the script to refuse early:

```powershell
if ($PSVersionTable.PSVersion.Major -lt 7) {
    # … fall back to the 5.1 path, or fail loudly with a clear message
}
```

Do not silently degrade — surface the version mismatch so the workflow's status file (see below) carries the reason.

## Building `PSArguments` from a XAML Expression

`Invoke Process` passes `Arguments` to the started process verbatim. When the workflow assembles a command line containing user-controlled paths or values, double-quotes inside any value will close the surrounding `""…""` string and corrupt the argument list. `build` does not catch this — it surfaces only when a runtime path contains a `"` or `'`.

**Rule:** for every value embedded in `PSArguments`, escape both XAML and shell-level quoting.

### VB expression (default for VB XAML projects)

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

`""""` in VB inside a `[…]` expression is a single literal `"`; `""""""` becomes a double-`"` (the escape sequence PowerShell parses as one literal `"` inside a double-quoted string).

### C# expression

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

### When the value is known to be path-safe

If the value is a constant or a value the workflow itself produced (no user input, no Orchestrator asset, no file picker output), the escape is unnecessary. **Default to escaping anyway** — the cost is negligible and the regression cost is high.

## Returning Status from a Script

`Invoke Process` returns the process exit code, not stdout. Two common patterns to surface meaningful status:

### Pattern A — Status file (recommended for short messages)

The script writes a single text file with either `OK` or a one-line error message. The workflow reads it after `Invoke Process` returns and acts on the contents.

**Two non-obvious correctness rules — both required:**

1. **Always write the file, even on crash.** Wrap the script body in `try { … } catch { Out-File -FilePath $statusFile -InputObject ("ERROR: " + $_.Exception.Message) -Encoding UTF8; exit 1 }`. Without this, an unhandled exception leaves the previous run's file in place and the workflow reads stale content — or no file exists and the workflow throws a generic "file not found" error that masks the real failure.
2. **Delete the status file at the end of the workflow run, not at the start of the next one.** Tying cleanup to "after read" makes status files self-cleaning regardless of whether the next run starts; tying it to "before write" leaves a window where a crashed previous run's file is read by the next.

Layout in XAML after the `Invoke Process`:

```text
Invoke Process (powershell.exe with -File <script> …)
└── If (Not File.Exists(StatusFilePath))
    ├── Then: Throw BusinessRuleException("Script produced no status file at " + StatusFilePath)
    └── Else: Read Text File → status
              If (status starts with "ERROR")
              ├── Then: Throw BusinessRuleException(status)
              └── Else: continue
              Delete (Path = StatusFilePath)
```

The `Throw` activity uses `s:Exception`-derived types — see [xaml/common-pitfalls.md § Invalid Use of `x:` Prefix](xaml/common-pitfalls.md#invalid-use-of-x-prefix-for-non-builtin-clr-types).

### Pattern B — Exit code only

Use when the script's outcome is binary (success/failure) and no message is needed. Have the script `exit 0` on success and `exit <non-zero>` on failure; check the `Result` output of `Invoke Process` (the exit code).

Mixing the two patterns (status file *and* exit code) is fine, but document which is authoritative — typically the status file, since exit codes can be hidden by intermediate process wrappers.

## Anti-Patterns

1. **Do not assume `pwsh.exe` is available** unless your provisioning bakes it in. Default to `powershell.exe` and gate any 7+ feature behind a version check.
2. **Do not concatenate paths into `PSArguments` without quote escaping.** A single `"` or `'` in any value silently shifts every subsequent positional argument.
3. **Do not use PowerShell to drive the UI** of a desktop or browser application. UiPath UIAutomation activities are the only sanctioned path — see [ui-automation-guide.md § Mandatory: Generate Targets Before Writing Any UI Code](ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code).
4. **Do not redirect script stdout to capture status.** It is fragile across PS versions and locales. Use a status file or exit code.
