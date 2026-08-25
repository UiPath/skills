# UiPath System Activities - Legacy Reference

## Overview
Core system-level activities for collections, text handling, dates, dialogs, file system, processes, workflow control, credentials, and triggers. Package: `UiPath.System.Activities`.

---

## Activity Categories

### Collection/List Activities
| Activity | Returns | Key Gotcha |
|----------|---------|------------|
| `AppendItemToList<T>` | int (index) | Returns 0-based index |
| `CreateList<T>` | IList\<T\> | Creates empty List\<T\> |
| `ReadListItem<T>` | T | **Silent null return on out-of-bounds** - no exception thrown |
| `UpdateListItem<T>` | - | Generic update |
| `AppendItemToCollection<T>` | List\<T\> | Throws `NotSupportedException` for fixed-size collections (arrays) |
| `BuildCollection<T>` | List\<T\> | **Cannot use both `NextItems` and `Items` simultaneously** |
| `ExistsInCollection<T>` | bool + int | Index=-1 if not found; Item must be non-null |
| `FilterCollection<T>` | List\<T\> | If Result not bound, **modifies collection in-place** |
| `RemoveFromCollection<T>` | List\<T\> | Mutually exclusive: RemoveAllElements vs Item vs Index |
| `MergeCollections<T>` | List\<T\> | Reference-checks to decide in-place vs new list |

### Text Handling Activities
| Activity | Returns | Key Gotcha |
|----------|---------|------------|
| `ExtractText` | string + IEnumerable | FirstMatch is `[Browsable(false)]`; Results has all matches |
| `FindAndReplace` | string | Standard find/replace |
| `SplitText` | IEnumerable\<string\> | NewLine uses 3-element array: `\r\n`, `\r`, `\n` |
| `ChangeCase` | string | SentenceCase is culture-dependent (uses regex with Unicode) |
| `CombineText` | string | Concatenation with separator |
| `ExtractDateTime` | DateTime | Multiple culture support |

### Date/Time Activities
| Activity | Returns | Units |
|----------|---------|-------|
| `AddOrSubtractFromDate` | DateTime | Seconds, Minutes, Hours, Days, Weeks, Months, Years |
| `FormatDateAsText` | string | Culture-aware formatting |
| `GetNextOrPreviousDate` | DateTime | Next/previous day/date occurrence |

### Dialog/Input Activities
| Activity | Returns | Key Gotcha |
|----------|---------|------------|
| `InputDialog` | dynamic | **Result type dynamically bound at CacheMetadata** from Result.ArgumentType; type conversion has fallback chain |
| `CustomInput` | string | Default 800x600; uses separate worker process |
| `SelectFile` | string | File dialog |
| `SelectFolder` | string | Folder dialog |
| `AskWhenRun<T>` | T | **Infinite retry loop on conversion failure**; uses reflection to find parent activity |

### File System Activities
| Activity | Key Gotcha |
|----------|------------|
| `DeleteFileX` | Direct File.Delete |
| `GetFileInfoX` | Returns FileInfo |
| `FileExistsX` | Returns bool |
| `GetLastDownloadedFile` | **Creates folder if doesn't exist**; IgnoreFiles is comma-separated extensions; default timeout 300s |

### Process Activities
| Activity | Key Gotcha |
|----------|------------|
| `ExecutePowerShell` | Parameter names prefixed differently from PowerShellVariables ("Global."); InArgument\<bool\> with null = switch parameter |
| `InvokeVBScript` | Windows-only VBScript execution |
| `InvokeCode` | CacheMetadata checks compilation errors |

### Workflow Control
| Activity | Key Gotcha |
|----------|------------|
| `MultipleAssign` | Uses Activity.Implementation pattern (not CodeActivity); validates each assignment's Value/To |
| `IfElseIf` / `IfElseIfV2` | All non-Else blocks must have Condition |

### Credential Activities
| Activity | Key Gotcha |
|----------|------------|
| `GetUsernamePasswordX` | Sources: CredentialsManager or Orchestrator; **timeout passed in milliseconds (value * 1000)**; uses separate CancellationTokenSource |

### Trigger Activities
| Activity | Key Gotcha |
|----------|------------|
| `TriggerScope` | Complex scheduling: Sequential, SequentialCollapse, SequentialDrop, OneTime; event queue filtering |
| `FileChangeTrigger` v1/v2/v3 | Version evolution; v3 is newest |
| `ProcessStartTrigger` v1/v2 | v2 is newer |
| `ProcessEndTrigger` v1/v2 | v2 is newer |

---

## Critical Gotchas

1. **ReadListItem\<T\> silent failure** - Returns null/default on out-of-bounds instead of throwing
2. **InputDialog dynamic typing** - Result type determined at design time from ArgumentType, not runtime
3. **FilterCollection in-place mutation** - Without Result bound, modifies original collection
4. **RemoveFromCollection bitwise AND bug** - Uses `&` instead of `&&` on line 49 (works but technically incorrect)
5. **AskWhenRun reflection fragility** - Searches parent activity by expression Id matching
6. **ExecutePowerShell version detection** - Registry-based; parameter/variable name prefixing prevents collisions
7. **TriggerScope queue modes** - SequentialCollapse removes all but last from same trigger; OneTime cancels all triggers after first event

## Platform Constraints
- `#if !NETPORTABLE_UIPATH`: InputDialog, CustomInput, InvokeComMethod, File activities
- `#if NET6_0_OR_GREATER`: Text/Date standard activities
- `#if NET6WINDOWS`: IfElseIf marked `[Browsable(false)]`

## Orchestrator Activities (MISSING FROM MANY REFERENCES - CRITICAL)

### Assets & Credentials
| Activity | Key Arguments | Gotcha |
|----------|---------------|--------|
| `Get Asset` | AssetName -> Value (object) | Returns object type; cast to String/Int/Bool as needed |
| `Set Asset` | AssetName, Value | Asset must exist and type must match |
| `Get Credential` | AssetName -> Username, Password (SecureString) | Orchestrator credential assets only |
| `Set Credential` | AssetName, Username, Password | |

### Queues
| Activity | Key Arguments | Gotcha |
|----------|---------------|--------|
| `Add Queue Item` | QueueName, ItemInformation (Dictionary), Priority, DeferDate, DueDate | ItemInformation values must be serializable |
| `Get Transaction Item` | QueueName -> TransactionItem | Returns null if queue empty (check for Nothing!) |
| `Set Transaction Status` | TransactionItem, Status (Success/Failed/Abandoned), Reason | Must be called for every transaction |
| `Add Transaction Item` | QueueName, ItemInformation -> TransactionItem | Combines Add + Get in one call |
| `Bulk Add Queue Items` | QueueName, DataTable | Column names become field names |
| `Should Stop` | -> bool | Check periodically in loops for graceful stop |

### Storage Buckets
| Activity | Key Arguments | Gotcha |
|----------|---------------|--------|
| `Upload Storage File` | BucketName, FilePath, BlobFilePath | BlobFilePath is the remote key/path |
| `Download Storage File` | BucketName, BlobFilePath, LocalPath | |
| `List Storage Files` | BucketName, Directory -> IEnumerable | |
| `Read/Write Storage Text` | BucketName, BlobFilePath, Content | UTF-8 encoding |

### Jobs
| Activity | Key Arguments | Gotcha |
|----------|---------------|--------|
| `Start Job` | ProcessName, RobotName -> JobId | Requires Orchestrator connection |
| `Should Stop` | -> bool | Returns true if stop requested from Orchestrator |

## GenericValue Conversion Traps (CRITICAL)
- **To bool**: null/empty → `false`; ANY other non-boolean string → `true` (not false!). `new GenericValue("hello")` → `true`
- **To int/double/decimal**: null → `0` (silent, no error)
- **To DateTime**: null → `DateTime.MinValue` (Jan 1, 0001)
- **Comparison**: `"10" > "9"` → `False` (string/lexicographic comparison)
- **Fix**: Avoid GenericValue. Use strongly-typed variables. Always explicitly convert.

## Date Format Registry Caching
- Short/long date formats read from `HKCU\Control Panel\International` and cached for entire process lifetime
- Changing Windows date settings during execution has NO effect until Robot restart

## Regex Infinite Timeout
- Regex Replace activity uses `Regex.InfiniteMatchTimeout` when TimeoutMS not set
- Complex patterns with catastrophic backtracking will hang forever

## Common Patterns
- **[RequiredArgument]** - Must be provided at design time
- **ContinueOnError** - Suppresses exceptions (InvokeComMethod returns null, TriggerScope calls HandleFault)
- **Telemetry** - All activities have conditional telemetry with `ENABLE_DEFAULT_TELEMETRY` preprocessor
