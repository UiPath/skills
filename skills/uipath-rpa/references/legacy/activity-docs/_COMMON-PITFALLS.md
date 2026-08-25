# UiPath Legacy Activities - Common Real-World Pitfalls

## Purpose
Gotchas reported by the community and discovered in source code that go beyond typical documentation. These are the issues developers hit in production.

---

## Excel (Classic - ExcelApplicationScope)

### Zombie Excel Processes
- **Problem**: Invisible `EXCEL.EXE` processes accumulate, especially after exceptions mid-workflow
- **Root cause**: COM objects not released when workflow crashes before Dispose runs
- **Fix**: Use Kill Process for `EXCEL.EXE` in a Finally block. The codebase has 207+ `DisposeWithReleaseComObject` calls showing this is a known hard problem

### Dates Read as Serial Numbers (45678 instead of date)
- **Problem**: Read Range returns OLE Automation doubles instead of dates
- **Root cause**: Excel stores dates internally as doubles since 1900. `PreserveFormat=false` returns raw numbers
- **Fix**: Set `PreserveFormat=true`, or convert with `DateTime.FromOADate(doubleValue)`

### Read Range Returns Empty DataTable
- **Problem**: Activity succeeds but DataTable is empty
- **Root cause**: Sheet name mismatch (case/whitespace), malformed range, or file locked by open Excel
- **Fix**: Verify sheet name with Get Workbook Sheets first. Use `""` for range to read entire used range. Close Excel before running

### Write Range Overwrites Formatting
- **Problem**: Cell formatting (colors, fonts, borders) lost after Write Range
- **Root cause**: Classic Write Range strips formatting by default
- **Fix**: Use Write Cell in loop for small updates, or use Interop-based writing with Visible=true

### ClosedXML Formula Evaluation is Limited (Portable)
- **Problem**: Formulas return stale/wrong values in Portable mode
- **Root cause**: ClosedXML cannot evaluate all Excel formulas; falls back to cached values via GetRichText()
- **Fix**: Use Interop mode (ExcelApplicationScope) for formula-dependent workflows

---

## UIAutomation (Classic - Click, TypeInto, Selectors)

### TypeInto Missing or Wrong Characters
- **Problem**: Characters dropped, wrong, or special chars interpreted as modifiers
- **Root cause**: `{`, `}`, `[`, `]`, `+`, `^`, `%`, `~` are SendKeys modifier chars. SimulateType may be too fast.
- **Fix**: Escape special chars: `{{}`, `{}}`, `{+}`. Add `DelayBetweenKeys` (50ms). For passwords use Type Secure Text

### TypeInto at Wrong Cursor Position
- **Problem**: Text inserted in middle of existing content instead of replacing
- **Root cause**: EmptyField may not work on all controls. Cursor position unpredictable.
- **Fix**: Set `EmptyField=true` AND prepend `[k(ctrl+a)]` to select all before typing

### EmptyField Silently Ignored with SimulateType
- **Problem**: Field not cleared despite EmptyField=true
- **Root cause**: Source code only runs EmptyField sequence for hardware events and SendWindowMessages, NOT for SimulateType/API mode
- **Fix**: Use hardware events (default) or SendWindowMessages when EmptyField is needed

### Selector Works in Studio, Fails on Robot/Orchestrator
- **Problem**: Element not found in production despite working in development
- **Root cause**: Different resolution, DPI scaling, user session (interactive vs service), window state. RDP disconnect loses UI.
- **Fix**: Use SimulateClick/SimulateType (don't depend on screen). Keep RDP alive. Use consistent resolution. Avoid `idx` attribute.

### Dynamic Selectors Break Over Time
- **Problem**: Selectors with timestamps, session IDs, or changing indices fail
- **Root cause**: Dynamic attributes like `aaname` containing runtime values, `idx` being position-dependent
- **Fix**: Use wildcards (`*`) for dynamic parts. Prefer `AutomationId` or `name`. Use Anchor Base for relative positioning. Avoid `idx`.

### OpenBrowser Defaults to Internet Explorer
- **Problem**: Workflows default to IE which is deprecated
- **Root cause**: `BrowserType` default is `BrowserType.IE` in source code
- **Fix**: Always explicitly set BrowserType to Chrome, Firefox, or Edge

---

## Mail (Classic - SMTP/IMAP/POP3/Exchange/Outlook)

### SMTP Authentication Fails with Gmail/Microsoft 365
- **Problem**: Login rejected despite correct credentials
- **Root cause**: Google/Microsoft disabled "Less Secure Apps". OAuth2 now required.
- **Fix**: Use App Passwords (Gmail) or configure Azure AD App Registration with SMTP.Send permission (M365). Set UseOAuth=true and pass OAuth token as Password.

### SMTP SSL/TLS Port Mismatch
- **Problem**: Connection fails with SSL errors
- **Root cause**: Port 587 requires STARTTLS (`SecureConnection=StartTls`). Port 465 requires implicit SSL. Port 25 is unencrypted.
- **Fix**: Use Port 587 + StartTls for most SMTP servers. Classic SMTP activity may not support implicit SSL on port 465.

### Attachment Paths Not Found on Robot
- **Problem**: Attachment path valid in Studio but not on production Robot
- **Root cause**: Relative paths resolve differently on Robot vs Studio
- **Fix**: Always use absolute paths. Use `Path.Combine(Environment.CurrentDirectory, filename)`

### Addresses Must Use Semicolons (Not Commas)
- **Problem**: Multiple recipients not receiving emails
- **Root cause**: Address separator is `;` not `,` for all protocols EXCEPT Lotus Notes (which uses commas)
- **Fix**: `"user1@mail.com;user2@mail.com"` - semicolons only

---

## Web (Classic - HTTP Request, SOAP)

### HTTP Request Returns Error Despite Correct Setup
- **Problem**: 403/401 errors with valid credentials
- **Root cause**: Missing required headers (`User-Agent`, `Accept`), expired token, or wrong `Content-Type`
- **Fix**: Add `User-Agent` header. Match `Content-Type` exactly. Verify with Postman first, replicate exact headers.

### HTTP Request ContinueOnError Defaults to TRUE
- **Problem**: HTTP errors silently swallowed; workflow continues with null/empty response
- **Root cause**: `NetHttpRequest.ContinueOnError = true` by default in source code
- **Fix**: Explicitly set `ContinueOnError=false` to get exceptions on 4xx/5xx responses

### Legacy HttpClient Very Short Timeout (6 seconds)
- **Problem**: Requests timeout on slow APIs
- **Root cause**: Default timeout is only 6,000ms. NetHttpRequest default is 10,000ms. Both often too low.
- **Fix**: Increase TimeoutMS to 30,000-60,000ms for production APIs

### SOAP Client Timeout Not Configurable
- **Problem**: SOAP requests timeout at 60 seconds with no way to increase
- **Root cause**: Hardcoded `60,000ms` constant in HttpSoapRequestLogic, no exposed property
- **Fix**: No workaround via activity properties. For long-running SOAP calls, consider using HTTP Request with manual SOAP envelope construction.

---

## PDF (Classic)

### Read PDF Text Returns Empty String
- **Problem**: Activity returns `""` for a PDF that clearly has content
- **Root cause**: PDF contains scanned images, not text layer. `ReadPDFText` only extracts native text.
- **Fix**: Use `Read PDF With OCR` with an OCR engine (Tesseract, UiPath Document OCR). Check if text is selectable in Adobe Reader.

### Read PDF Text Returns Garbled/Out-of-Order Text
- **Problem**: Text is present but columns are mixed, lines out of order
- **Root cause**: PDF internal text stream doesn't match visual layout. Multi-column layouts especially problematic.
- **Fix**: Set `PreserveFormatting=true` (off by default!). Or use Read PDF With OCR for better layout handling.

---

## Database (Community)

### "Unable to find requested .NET Framework Data Provider"
- **Problem**: Connection fails with provider not found error
- **Root cause**: Missing database driver, or 32-bit vs 64-bit mismatch with UiPath Robot
- **Fix**: Install correct bitness driver (64-bit for modern UiPath). For Oracle use `Oracle.ManagedDataAccess` NuGet. Check `machine.config` for provider registration.

### Connection Works in Studio, Fails on Robot
- **Problem**: Same connection string fails in production
- **Root cause**: Different ODBC/OLE DB drivers installed, Windows credentials differ (Integrated Security)
- **Fix**: Use explicit credentials, not `Integrated Security=true`. Ensure drivers installed on Robot machine.

### Execute Query vs Execute Non Query Confusion
- **Problem**: SELECT returns no data, or INSERT returns DataTable
- **Root cause**: Using wrong activity for the SQL operation type
- **Fix**: `Execute Query` for SELECT (returns DataTable). `Execute Non Query` for INSERT/UPDATE/DELETE (returns row count).

---

## Credentials

### Get Credential Fails on Robot Server
- **Problem**: Works on developer machine but fails on production Robot
- **Root cause**: Windows Credential Manager is per-user. Robot service account doesn't have the stored credential.
- **Fix**: Use Orchestrator Assets (Credential type) instead. If must use Windows CM, log in as Robot service account and store credential there.

---

## Python (Community - PythonScope)

### Python Scope Fails to Find Installation
- **Problem**: "Python not found" error
- **Root cause**: Wrong Path or Version. 32-bit vs 64-bit mismatch. TargetPlatform must match Python installation.
- **Fix**: Set full path to `python.exe`. Match Version exactly. Set TargetPlatform to x64 for 64-bit Python.

### Python Script Works Locally but Fails in UiPath
- **Problem**: Script runs fine in command line but errors in PythonScope
- **Root cause**: Virtual environment not activated, working directory different, packages not installed globally
- **Fix**: Point Path to virtualenv's `python.exe`. Use absolute paths in scripts. Install packages globally or in the specific env.

---

## FTP (Community)

### Download/Upload Hangs or Timeouts
- **Problem**: Connection established but transfers hang
- **Root cause**: Passive vs Active mode mismatch; firewall blocking data channel ports
- **Fix**: Toggle UsePassiveMode. Ensure firewall allows passive port range (1024-65535). Use SFTP (port 22) when possible.

---

## GenericValue Traps (System)

### String Comparison Instead of Numeric
- **Problem**: `"10" > "9"` returns False
- **Root cause**: GenericValue does string comparison (lexicographic), not numeric
- **Fix**: Explicitly convert: `CInt(genericValue)`, `CDbl(genericValue)`. Avoid GenericValue in new projects; use strongly-typed variables.

### DataTable Column Name Issues
- **Problem**: "Column X does not belong to table" after reading data
- **Root cause**: Column names have trailing/leading whitespace, or case mismatch in filter expressions
- **Fix**: Trim column names: `col.ColumnName = col.ColumnName.Trim()`. Use column index `row(0)` when names unreliable. Use bracket notation for spaces: `[Column Name]`.

### GenericValue Boolean Conversion Trap (DANGEROUS)
- **Problem**: `new GenericValue("hello")` converted to bool returns `True`. ANY non-null, non-empty, non-boolean string → `True`
- **Root cause**: Source code `GenericValue.cs` line 89: if `Convert.ToBoolean` fails, the catch block returns `true` (not false!)
- **Fix**: NEVER rely on implicit GenericValue-to-bool conversion. Always explicitly compare: `If myVar.ToString() = "True"`. Better yet, avoid GenericValue entirely and use strongly-typed variables.

### GenericValue Null Conversion Traps
- **Problem**: Silent data loss on null values
- **Root cause**: `GenericValue(null)` → int returns `0`, → DateTime returns `DateTime.MinValue` (Jan 1, 0001), → double returns `0.0`. No errors thrown.
- **Fix**: Always check for null/empty before converting: `If Not String.IsNullOrEmpty(myGenericValue.ToString())`

---

## HIDDEN DANGEROUS DEFAULTS (Source Code Verified)

### Activities That Default ContinueOnError=TRUE (silent failures)
These activities SWALLOW all errors by default. Your workflow will continue as if they succeeded:

| Activity | Package | Impact |
|----------|---------|--------|
| `NetHttpRequest` (HTTP Request) | Web | HTTP 500/timeout → empty response, no error |
| `Data Scraping` wizard output | UIAutomation | Extraction failure → empty DataTable |
| `ShowCallout` | Forms | Callout display failure → silently ignored |

**Fix**: Always explicitly set `ContinueOnError=False` on HTTP Request activities unless you're checking status codes manually.

### Excel AutoSave=TRUE Causes Performance Disasters in Loops
- **Problem**: 1000 Write Cell operations = 1000 disk writes
- **Root cause**: `AutoSave=true` by default on ExcelApplicationScope. Every single activity triggers `Document.Save()`
- **Fix**: Set `AutoSave=false` on ExcelApplicationScope, then add a single Save Workbook at the end. The `ExcelForEachRowX` activity internally disables AutoSave during iteration for this exact reason.

### Excel DisplayAlerts/ScreenUpdating Left in Bad State After Crash
- **Problem**: After workflow crash, Excel stays in "frozen" state or silently overwrites files
- **Root cause**: Operations temporarily set `DisplayAlerts=false` and `ScreenUpdating=false` on the COM app. Crash before restore leaves Excel broken.
- **Fix**: Use Try-Finally to ensure Excel state is restored. Consider Kill Process as cleanup.

### CSV Encoding Varies by Platform (Encoding.Default trap)
- **Problem**: Same CSV file produces different results on different machines
- **Root cause**: `Encoding.Default` returns system ANSI code page on .NET Framework but UTF-8 on .NET Core. Locale-dependent.
- **Fix**: Always explicitly specify encoding: `"UTF-8"` in CSV activities. Never rely on defaults.

### CSV Delimiter Depends on System Culture
- **Problem**: CSV activities produce different delimiters on different machines
- **Root cause**: `CultureInfo.CurrentUICulture` used for CSV configuration internally
- **Fix**: Always explicitly set the `Delimitator` (note spelling) property. Don't rely on system defaults.

---

## DATE/LOCALE TRAPS

### Date Formats Cached from Windows Registry for Entire Process
- **Problem**: Date parsing/formatting uses stale format if Windows settings change
- **Root cause**: Short/long date formats read from `HKCU\Control Panel\International` and cached in static fields for process lifetime (never refreshed)
- **Fix**: Don't change date format settings during Robot execution. If needed, restart Robot process.

### Outlook Mail Filter Depends on Windows Date Format
- **Problem**: Outlook date filters silently return no results
- **Root cause**: Filter reads `sShortDate` from registry. If your filter date format doesn't match Windows-configured short date format, Outlook filtering fails silently.
- **Fix**: Format dates in Outlook filter expressions to match the system's short date format.

---

## PROCESS/MEMORY SAFETY

### COM Singleton Reference Counting (Excel, Word, PowerPoint)
- **Problem**: One crashed activity corrupts COM state for all subsequent activities in same process
- **Root cause**: All three Office apps use process-wide singleton `ComAppReferenceCountManager`. Delayed cleanup via `Task.Factory.StartNew` can race with new scope creation. Falls back to `Process.Kill()` as last resort.
- **Fix**: Wrap all Office scope activities in Try-Finally. Use Kill Process as safety net. Don't run multiple Excel/Word/PowerPoint scopes concurrently.

### Mail Session Server Orphan Processes
- **Problem**: `UiPath.Mail.MainSessionServer.exe` runs forever after Robot disconnects
- **Root cause**: Server uses `await Task.Delay(int.MaxValue)` in infinite loop. Only terminates if parent PID argument is passed correctly.
- **Fix**: Monitor for orphaned MainSessionServer.exe processes. Kill after workflow completion if needed.

### Regex with Infinite Timeout
- **Problem**: Complex regex patterns can hang workflow indefinitely
- **Root cause**: `System.Activities` Regex Replace uses `Regex.InfiniteMatchTimeout` when TimeoutMS not specified
- **Fix**: Always set TimeoutMS on Regex activities. Test regex patterns for catastrophic backtracking.

### Terminal Infinite Wait on Unresponsive Server
- **Problem**: Workflow hangs forever waiting for terminal response
- **Root cause**: Terminal operations use `Timeout.Infinite` when no timeout specified in 3 code paths
- **Fix**: Always set explicit TimeoutMS on all terminal activities. Never rely on defaults.

---

## SILENT ERROR SWALLOWING (Design-Time)

### HTTP Request Designer Hides Configuration Errors
- **Problem**: Incorrectly configured HTTP requests show no warnings at design time
- **Root cause**: Four separate empty `catch { }` blocks in HttpRequestWindow.xaml.cs silently eat configuration errors
- **Fix**: Always test HTTP requests manually (e.g., in Postman) before relying on the designer configuration.

### Connection Service Resolution Silently Fails
- **Problem**: Mail connection falls back to null ConnectionId without warning
- **Root cause**: Empty `catch (Exception) { }` in BaseMailConnectionServiceActivities when resolving connection bindings
- **Fix**: Test connection resolution explicitly in a separate workflow step before using in production.

### Office365 Token Storage Silently Fails
- **Problem**: Token refresh/storage operations fail without any indication
- **Root cause**: OrchestratorGlobalAssetStore catches and ignores HttpClientFramework.ApiServiceException on delete, get, list, and folder operations
- **Fix**: Monitor Orchestrator logs for token-related errors. Test auth flow end-to-end.
