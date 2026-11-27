# Excel Process Scope

`UiPath.Excel.Activities.Business.ExcelProcessScopeX`

Manages the lifecycle of an Excel process instance. All `ExcelApplicationCard` activities placed inside this scope share the same Excel process, providing fine-grained control over how Excel is started, reused, and closed.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** None (this is a scope activity itself)

## Properties

### Options
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessMode` | Process mode | Property | `ExcelProcessMode?` | No | `null` (Same as project) | Controls whether the Excel process scope creates a new process, reuses an existing process if available, or ensures a unique process for attended users. |
| `LaunchMethod` | Launch method | Property | `ExcelStartMethod?` | No | `null` (Same as project) | Controls how the Excel process will be launched. Either via COM, or as a full process. |
| `LaunchTimeout` | Launch timeout | Property | `int?` | No | `null` (Same as project) | Time to wait for Excel to start if launched as a full process. The default is 20 seconds. |
| `FileConflictResolution` | File conflict resolution | Property | `ExcelFileConflictResolution?` | No | `null` (Same as project) | Action to be executed if Excel document conflicts are detected between Excel processes. |
| `ExistingProcessAction` | Existing processes action | Property | `ExistingExcelProcessAction?` | No | `null` (Same as project) | Action to be executed if other Excel processes are running. |
| `DisplayAlerts` | Display alerts | Property | `bool?` | No | `null` (Same as project) | If true, Microsoft Excel can display alerts and messages. The default is False. |
| `ShowExcelWindow` | Show Excel window | Property | `bool?` | No | `null` (Same as project) | If true, Excel windows will appear during automation. The default is True. |
| `MacroSettings` | Macro settings | Property | `MacroSetting?` | No | `null` (Same as project) | Enable or disable Macros. Default is Enable all. |

## Enum Reference

#### `ExcelProcessMode`
| Value | Display Name |
|-------|-------------|
| `AlwaysCreateNew` | Always create new |
| `AttendedUser` | Attended user |
| `ReuseIfExists` | Reuse if exists |
| `OnlyIfExists` | Only if exists |

#### `ExcelStartMethod`
| Value | Display Name |
|-------|-------------|
| `Automation` | Automation (COM) |
| `Application` | Application (full process) |

#### `ExcelFileConflictResolution`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `CloseWithoutSaving` | Close without saving |
| `PromptUser` | Prompt user |
| `ThrowException` | Throw exception |

#### `ExistingExcelProcessAction`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `ForceKill` | Force kill |

#### `MacroSetting`
| Value | Display Name |
|-------|-------------|
| `EnableAll` | Enable all |
| `DisableAll` | Disable all |
| `ReadFromExcelSettings` | Read from Excel settings |

## XAML Example
```xml
<excel:ExcelProcessScopeX
  ProcessMode="{x:Null}"
  LaunchMethod="{x:Null}"
  DisplayName="Excel Process Scope">
  <excel:ExcelProcessScopeX.Body>
    <ActivityAction x:TypeArguments="excel:IExcelProcess">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="excel:IExcelProcess" Name="ExcelProcessScopeTag" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- ExcelApplicationCard activities here -->
      </Sequence>
    </ActivityAction>
  </excel:ExcelProcessScopeX.Body>
</excel:ExcelProcessScopeX>
```

## Notes
- All nullable properties default to project-level settings when left unset (`null`).
- The `Body` property is hidden in the designer.
- When the scope completes or faults, it automatically quits the Excel process it manages.
- The `ProcessMode` controls whether existing Excel processes are reused or new ones are created.
- If `ProcessMode` is set to `AttendedUser`, the `FileConflictResolution` value is ignored and treated as `PromptUser`.
