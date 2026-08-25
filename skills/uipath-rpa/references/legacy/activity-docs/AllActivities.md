# UiPath Legacy Activities - Complete Catalog

> **Scope**: Legacy/Classic XAML activities only. No modern "X" suffix, no portable, no coded workflows.

---

## 1. UiPath.System.Activities (v26.2.0) — 93.6% adoption

### Workflow Control (Foundation)
| Activity | Description |
|----------|-------------|
| `Assign` | Assigns a value to a variable or argument |
| `Delay` | Pauses execution for specified TimeSpan |
| `Log Message` | Writes message to Robot execution log (Trace/Info/Warn/Error/Fatal) |
| `Message Box` | Displays message dialog to user |
| `Comment Out` | Disables contained activities (design-time only) |
| `Invoke Workflow File` | Invokes another .xaml workflow with input/output arguments |
| `Invoke Process` | Invokes a published process/package |
| `Invoke Code` | Executes inline VB.NET or C# code |
| `Sequence` | Sequential container for activities |
| `Flowchart` | Flow-based container with decision nodes |
| `State Machine` | State-based workflow container |
| `Try Catch` | Exception handling with catch blocks by exception type |
| `Retry Scope` | Retries child activities on failure (configurable count/interval) |
| `Throw` | Throws a specified exception |
| `Rethrow` | Re-throws caught exception (inside Catch block) |
| `For Each` | Iterates over collection items |
| `For Each Row` | Iterates over DataTable rows |
| `While` | Loops while condition is true |
| `Do While` | Loops at least once, then while condition is true |
| `Switch` | Multi-branch switch on expression value |
| `If` | Conditional branch (Then/Else) |
| `Break` | Exits innermost loop |
| `Continue` | Skips to next iteration of loop |
| `Parallel` | Executes branches in parallel |
| `Parallel For Each` | Iterates collection with parallel execution |
| `Pick` | Waits for one of multiple triggers, executes first |
| `Pick Branch` | Individual branch inside Pick |
| `Interruptible While` | While loop that can be interrupted by triggers |
| `Terminate Workflow` | Terminates workflow execution |

### Orchestrator - Assets & Credentials
| Activity | Description |
|----------|-------------|
| `Get Asset` | Gets Orchestrator asset value (Text/Bool/Int/Credential) |
| `Set Asset` | Sets Orchestrator asset value |
| `Get Credential` | Gets username+password from Orchestrator Credential asset |
| `Set Credential` | Sets Orchestrator Credential asset |

### Orchestrator - Queues
| Activity | Description |
|----------|-------------|
| `Add Queue Item` | Adds item to Orchestrator queue |
| `Add Transaction Item` | Adds item and sets status to InProgress |
| `Get Transaction Item` | Gets next available queue item for processing |
| `Set Transaction Status` | Sets queue item status (Success/Failed/Abandoned) |
| `Set Transaction Progress` | Updates progress info on transaction |
| `Get Queue Items` | Retrieves queue items with filtering |
| `Bulk Add Queue Items` | Adds DataTable rows to queue |
| `Delete Queue Items` | Deletes items from queue |
| `Postpone Transaction Item` | Defers transaction to later time |
| `Wait Queue Item` | Waits for queue item status change |
| `Queue Trigger` | Trigger that fires on new queue items |

### Orchestrator - Jobs & Storage
| Activity | Description |
|----------|-------------|
| `Start Job` | Starts a process job on Orchestrator |
| `Stop Job` | Stops a running job |
| `Get Jobs` | Lists jobs with filtering |
| `Should Stop` | Checks if current job has been requested to stop |
| `Upload Storage File` | Uploads file to Orchestrator Storage Bucket |
| `Download Storage File` | Downloads file from Storage Bucket |
| `Delete Storage File` | Deletes file from Storage Bucket |
| `List Storage Files` | Lists files in Storage Bucket |
| `Read Storage Text` | Reads text content from Storage Bucket |
| `Write Storage Text` | Writes text content to Storage Bucket |
| `Raise Alert` | Raises alert in Orchestrator |

### Compression
| Activity | Description |
|----------|-------------|
| `Compress/Zip Files` | Compresses files into ZIP archive |
| `Extract/Unzip Files` | Extracts files from ZIP archive |

### DataTable
| Activity | Description |
|----------|-------------|
| `Build Data Table` | Creates DataTable with column definitions (wizard) |
| `Add Data Row` | Adds row to DataTable |
| `Remove Data Row` | Removes row from DataTable |
| `Add Data Column` | Adds column to DataTable |
| `Remove Data Column` | Removes column from DataTable |
| `Clear Data Table` | Removes all rows from DataTable |
| `Filter Data Table` | Filters DataTable by column conditions |
| `Sort Data Table` | Sorts DataTable by column |
| `Merge Data Table` | Merges two DataTables |
| `Join Data Tables` | Joins two DataTables (Inner/Left/Full) |
| `Lookup Data Table` | Looks up value in DataTable by key |
| `Output Data Table` | Converts DataTable to formatted string |
| `Generate Data Table` | Creates DataTable from structured text |
| `Remove Duplicate Rows` | Removes duplicate rows from DataTable |
| `For Each Row` | Iterates over DataTable rows |
| `Get Row Item` | Gets cell value by column name/index |

### Collections
| Activity | Description |
|----------|-------------|
| `Append Item To List` | Appends an item to a List and returns the index |
| `Create List` | Creates a new empty List of specified type |
| `Read List Item` | Reads an item from a List at specified index |
| `Update List Item` | Updates an item in a List at specified index |
| `Append Item To Collection` | Appends one or more items to an ICollection |
| `Build Collection` | Builds a new collection from individual items |
| `Exists In Collection` | Checks if item exists in collection, returns bool and index |
| `Filter Collection` | Filters a collection based on criteria |
| `Remove From Collection` | Removes item(s) from collection by item, index, or all |
| `Merge Collections` | Merges two collections into one |

### Text Handling
| Activity | Description |
|----------|-------------|
| `Change Case` | Changes text case (Lower, Upper, Sentence, Title) |
| `Combine Text` | Concatenates text strings with separator |
| `Extract Text` | Extracts text between strings, emails, URLs, or from HTML |
| `Find And Replace` | Finds and replaces text in a string |
| `Split Text` | Splits text by separator (comma, newline, space, tab, etc.) |
| `Extract Date Time` | Parses date/time from text with culture support |

### Date/Time
| Activity | Description |
|----------|-------------|
| `Add Or Subtract From Date` | Adds/subtracts seconds/minutes/hours/days/weeks/months/years |
| `Format Date As Text` | Formats DateTime to string with culture |
| `Get Next Or Previous Date` | Gets next/previous occurrence of a day |

### Dialog/Input
| Activity | Description |
|----------|-------------|
| `Input Dialog` | Displays input dialog box, returns user-typed value |
| `Custom Input` | Shows custom HTML form dialog, returns string result |
| `Select File` | File picker dialog |
| `Select Folder` | Folder picker dialog |
| `Ask When Run` | Prompts user for a value at runtime |

### File System
| Activity | Description |
|----------|-------------|
| `Delete File` | Deletes a file from disk |
| `File Exists` | Checks if file exists, returns bool |
| `Get File Info` | Returns FileInfo for a file path |
| `Delete Folder` | Deletes a folder from disk |
| `Folder Exists` | Checks if folder exists, returns bool |
| `Get Folder Info` | Returns folder information |
| `Rename File` | Renames a file |
| `Rename Folder` | Renames a folder |
| `Copy Folder` | Copies a folder recursively |
| `Move Folder` | Moves a folder |
| `Get Last Downloaded File` | Monitors download folder for newest file |

### Process/Code
| Activity | Description |
|----------|-------------|
| `Execute PowerShell` | Executes PowerShell commands/scripts with parameters |
| `Invoke Power Shell` | Alternative PowerShell invocation |
| `Invoke VBScript` | Executes VBScript code |
| `Invoke Code` | Executes inline VB.NET or C# code |
| `Invoke COM Method` | Calls a method on a COM object by ProgID or CLSID |

### Workflow Control
| Activity | Description |
|----------|-------------|
| `Multiple Assign` | Assigns multiple variables in a single activity |
| `If Else If` | Multi-branch conditional (if/else if/else) |

### Credentials
| Activity | Description |
|----------|-------------|
| `Get Username Password` | Gets credentials from Windows Credential Manager or Orchestrator |

### Triggers
| Activity | Description |
|----------|-------------|
| `Trigger Scope` | Container for event-driven triggers with scheduling modes |
| `File Change Trigger` | Fires when file system changes detected |
| `Process Start Trigger` | Fires when a process starts |
| `Process End Trigger` | Fires when a process ends |
| `Notify Global Variable Changed` | Notifies when global variable changes |

### Regex
| Activity | Description |
|----------|-------------|
| `Is Match` | Tests if string matches regex pattern |
| `Matches` | Returns all regex matches from string |
| `Replace` | Regex-based find and replace |

---

## 2. UiPath.UIAutomation.Activities (v26.1.0) — 92.6% adoption

### Mouse
| Activity | Description |
|----------|-------------|
| `Click` | Clicks UI element (single/double/down/up, left/right/middle) |
| `Double Click` | Double-clicks a UI element |
| `Hover` | Hovers mouse over a UI element |
| `Click Image` | Clicks on image match found in UI |
| `Hover Image` | Hovers over image match in UI |
| `Click Text` | Clicks on OCR-recognized text in UI |
| `Click OCR Text` | Clicks text found by OCR engine |
| `Mouse Scroll` | Scrolls mouse wheel on element |

### Keyboard
| Activity | Description |
|----------|-------------|
| `Type Into` | Types text into a UI element with special key support |
| `Type Secure Text` | Types SecureString into element (passwords) |
| `Send Hotkey` | Sends keyboard shortcut (Ctrl+C, Alt+F4, etc.) |
| `Set Text` | Sets text value of element via attribute |

### Element Search
| Activity | Description |
|----------|-------------|
| `Find Element` | Finds a UI element by selector, returns UiElement |
| `Element Exists` | Checks if element exists, returns bool (no exception on timeout) |
| `Find Children` | Finds child elements matching filter criteria |
| `Find Relative Element` | Finds element at relative offset from target |
| `Get Ancestor` | Navigates up N levels in element hierarchy |
| `Wait Element Appear` | Waits until element appears (adaptive polling) |
| `Wait Element Vanish` | Waits until element disappears |
| `On Element Appear` | Trigger: fires when element appears |
| `On Element Vanish` | Trigger: fires when element vanishes |
| `Element Scope` | Container that finds element once for child activities |
| `Indicate On Screen` | Highlights element for user to see |
| `Find Image Matches` | Finds all occurrences of template image in screen |

### Element Attributes
| Activity | Description |
|----------|-------------|
| `Get Text` | Gets text content of UI element |
| `Get Full Text` | Gets full text using FullText method |
| `Get Visible Text` | Gets visible/rendered text using Native method |
| `Get Value` | Gets value attribute of element |
| `Set Value` | Sets value attribute of element |
| `Get Attribute` | Gets any named attribute of element |
| `Set Attribute` | Sets any named attribute of element |
| `Select Item` | Selects item from dropdown/listbox by text |
| `Select Multiple Items` | Selects multiple items from multi-select control |
| `Check` | Checks/unchecks checkbox or radio button |
| `Wait Attribute` | Waits until element attribute matches value (wildcards) |
| `Get Position` | Gets element screen coordinates as Rectangle |

### Actions
| Activity | Description |
|----------|-------------|
| `Activate` | Brings window to foreground |
| `Set Focus` | Sets keyboard focus to element |
| `Highlight` | Draws colored box around element for debugging |
| `Take Screenshot` | Captures element or region as Image |
| `Save Image` | Saves Image object to file |
| `Load Image` | Loads image from file |
| `Set Clipping Region` | Sets visible region of element |
| `Block User Input` | Blocks keyboard/mouse input during execution |

### Clipboard
| Activity | Description |
|----------|-------------|
| `Get From Clipboard` | Gets text from system clipboard |
| `Set To Clipboard` | Sets text to system clipboard |
| `Copy Selected Text` | Copies currently selected text (Ctrl+C) |

### Data Scraping
| Activity | Description |
|----------|-------------|
| `Extract Structured Data` | Scrapes structured/tabular data from UI into DataTable |
| `Extract Data` | Legacy data extraction |

### Window/Process
| Activity | Description |
|----------|-------------|
| `Close Window` | Closes a window |
| `Close Tab` | Closes a browser tab |
| `Start Process` | Starts an executable |
| `Get Active Window` | Gets the currently active/foreground window |

### Scope Activities
| Activity | Description |
|----------|-------------|
| `Open Browser` | Opens browser (IE/Chrome/Firefox/Edge) and provides scope |
| `Open Application` | Launches application and provides window scope |
| `Attach Browser` | Attaches to existing browser window |
| `Attach Window` | Attaches to existing application window |
| `Browser Scope` | Targets browser by selector or browser variable |
| `Window Scope` | Targets window by selector or window variable |

### OCR/Image
| Activity | Description |
|----------|-------------|
| `Get OCR Text` | Extracts text from element using OCR engine |
| `Find OCR Text Position` | Finds position of OCR text in element |
| `Wait Image Appear` | Waits for image to appear on screen |
| `Wait Image Vanish` | Waits for image to disappear |

### SAP
| Activity | Description |
|----------|-------------|
| `Click SAP` | Clicks SAP GUI element |
| `Select SAP Item` | Selects item in SAP control |
| `Expand Tree` | Expands SAP tree node |
| `Collapse Tree` | Collapses SAP tree node |
| `Select SAP Date` | Selects date in SAP calendar control |

### Citrix
| Activity | Description |
|----------|-------------|
| `Click Text` | Clicks OCR-recognized text (Citrix/RDP) |
| `Type Into (image)` | Types into image-based target |

---

## 3. UiPath.Excel.Activities (v3.5.0) — 90.2% adoption

### Scope
| Activity | Description |
|----------|-------------|
| `Excel Application Scope` | Opens workbook via COM Interop, provides scope for child activities |

### Interop Activities (require Excel Application Scope)
| Activity | Description |
|----------|-------------|
| `Read Range` | Reads cell range into DataTable |
| `Write Range` | Writes DataTable to cell range |
| `Read Cell` | Reads single cell value |
| `Write Cell` | Writes value to single cell |
| `Read Cell Formula` | Gets formula text from cell |
| `Read Row` | Reads entire row as IEnumerable |
| `Read Column` | Reads entire column as IEnumerable |
| `Append Range` | Appends DataTable after last row |
| `Select Range` | Selects/highlights a cell range |
| `Get Selected Range` | Returns currently selected range address |
| `Get Table Range` | Gets range address of named table |
| `Auto Fill Range` | Auto-fills pattern in range |
| `Copy Paste Range` | Copies and pastes cell range |
| `Create Table` | Creates formatted table from range |
| `Create Pivot Table` | Creates pivot table from data |
| `Refresh Pivot Table` | Refreshes pivot table data |
| `Filter Table` | Applies filter to table |
| `Sort Table` | Sorts table data |
| `Delete Range` | Deletes cells in range |
| `Delete Column` | Deletes column(s) |
| `Insert Column` | Inserts column(s) |
| `Insert/Delete Rows` | Inserts or deletes rows |
| `Insert/Delete Columns` | Inserts or deletes columns |
| `Remove Duplicates Range` | Removes duplicate rows from range |
| `Lookup Range` | VLOOKUP-style lookup in range |
| `Copy Sheet` | Copies worksheet within/between workbooks |
| `Get Workbook Sheets` | Lists all sheet names |
| `Get Cell Color` | Gets cell background color |
| `Set Range Color` | Sets cell background color |
| `Execute Macro` | Executes VBA macro by name |
| `Invoke VBA` | Invokes VBA code from .bas file |

### Portable Activities (no Excel required)
| Activity | Description |
|----------|-------------|
| `Read Range (Workbook)` | Reads range from .xlsx file using ClosedXML |
| `Write Range (Workbook)` | Writes to .xlsx file using ClosedXML |
| `Read Cell (Workbook)` | Reads single cell from file |
| `Write Cell (Workbook)` | Writes single cell to file |
| `Read Cell Formula (Workbook)` | Gets formula from cell in file |
| `Read Row (Workbook)` | Reads row from file |
| `Read Column (Workbook)` | Reads column from file |
| `Append Range (Workbook)` | Appends data to file |
| `Create Table (Workbook)` | Creates table in file |
| `Create Pivot Table (Workbook)` | Creates pivot table in file |
| `Get Table Range (Workbook)` | Gets table range from file |
| `Get Sheets (Workbook)` | Lists sheets in file |
| `Set Range Color (Workbook)` | Sets cell color in file |
| `Get Cell Color (Workbook)` | Gets cell color from file |
| `Create New Workbook` | Creates new .xlsx file |

### CSV Activities
| Activity | Description |
|----------|-------------|
| `Read CSV` | Reads CSV file into DataTable |
| `Write CSV` | Writes DataTable to CSV file |
| `Append To CSV` | Appends DataTable rows to existing CSV |

---

## 4. UiPath.Mail.Activities (v2.8.0) — 77.7% adoption

### SMTP
| Activity | Description |
|----------|-------------|
| `Send SMTP Mail Message` | Sends email via SMTP with attachments, HTML body |

### IMAP
| Activity | Description |
|----------|-------------|
| `Get IMAP Mail Messages` | Retrieves emails from IMAP server with filtering |
| `Delete IMAP Mail Message` | Deletes email from IMAP server |
| `Move IMAP Mail Message` | Moves email between IMAP folders |

### POP3
| Activity | Description |
|----------|-------------|
| `Get POP3 Mail Messages` | Retrieves emails from POP3 server (inbox only) |

### Exchange
| Activity | Description |
|----------|-------------|
| `Send Exchange Mail Message` | Sends email via Exchange Web Services |
| `Get Exchange Mail Messages` | Retrieves emails from Exchange with filtering |
| `Delete Mail` | Deletes email from Exchange |
| `Move Message To Folder` | Moves email between Exchange folders |
| `Save Exchange Attachments` | Saves email attachments to disk |
| `Exchange Scope` | Connection container for Exchange activities |

### Outlook
| Activity | Description |
|----------|-------------|
| `Send Outlook Mail Message` | Sends email via Outlook COM with importance/sensitivity |
| `Get Outlook Mail Messages` | Retrieves emails from Outlook folders |
| `Delete Outlook Mail Message` | Deletes Outlook email |
| `Move Outlook Message` | Moves Outlook email between folders |
| `Mark Outlook Mail As Read` | Toggles read/unread status |
| `Reply To Outlook Mail Message` | Sends reply via Outlook |
| `Save Attachments` | Saves Outlook email attachments |
| `Save Outlook Mail Message` | Saves email as .msg file |
| `Set Outlook Mail Categories` | Assigns categories/flags to email |
| `Outlook Mail Message Trigger` | Trigger for incoming Outlook emails |

### Lotus Notes
| Activity | Description |
|----------|-------------|
| `Send Lotus Notes Mail Message` | Sends email via Lotus Notes COM |
| `Get Lotus Notes Mail Messages` | Retrieves emails from Lotus Notes |
| `Delete Lotus Notes Mail Message` | Deletes Lotus Notes email |
| `Move Lotus Notes Mail Message` | Moves Lotus Notes email |

---

## 5. UiPath.Web.Activities (v2.4.0) — 33.9% adoption

### HTTP
| Activity | Description |
|----------|-------------|
| `HTTP Request` | Modern HTTP client with auth, retry, proxy, SSL config |
| `HTTP Client` | Legacy REST client (RestSharp-based) with OAuth1 support |
| `SOAP Request` | SOAP 1.1/1.2 web service client from WSDL |

### JSON
| Activity | Description |
|----------|-------------|
| `Deserialize JSON` | Parses JSON string to typed object |
| `Deserialize JSON Array` | Parses JSON string to JArray |
| `Serialize JSON` | Serializes object to JSON string |

### XML
| Activity | Description |
|----------|-------------|
| `Deserialize XML` | Parses XML string to XDocument |
| `Get XML Nodes` | Extracts all nodes from XML document |
| `Get Nodes` | Extracts root element's child nodes |
| `Execute XPath` | Executes XPath query on XML document |
| `Get XML Node Attributes` | Gets attributes from XML node |

---

## 6. UiPath.Database.Activities (v1.8.1) — 22.7% adoption

| Activity | Description |
|----------|-------------|
| `Connect` | Opens ADO.NET database connection |
| `Disconnect` | Closes database connection |
| `Execute Query` | Runs SELECT SQL, returns DataTable |
| `Execute Non Query` | Runs INSERT/UPDATE/DELETE, returns affected row count |
| `Insert Data Table` | Inserts DataTable rows into database table |
| `Bulk Insert` | High-performance bulk insert using SqlBulkCopy |
| `Bulk Update` | Bulk update existing rows |
| `Start Transaction` | Transaction scope with auto-commit/rollback |

---

## 7. UiPath.Credentials.Activities (v1.5.0) — 22.3% adoption

| Activity | Description |
|----------|-------------|
| `Get Secure Credential` | Gets username + SecureString password from Windows Credential Manager |
| `Get Credential` | Gets username + plain string password from Credential Manager |
| `Add Credential` | Stores credential in Windows Credential Manager |
| `Delete Credential` | Removes credential from Credential Manager |
| `Request Credential` | Shows Windows credential prompt dialog |

---

## 8. UiPath.MicrosoftOffice365.Activities (v3.8.0) — 17.5% adoption

### Scope
| Activity | Description |
|----------|-------------|
| `Microsoft Office 365 Scope` | OAuth2 authentication container for all O365 activities |

### Mail
| Activity | Description |
|----------|-------------|
| `Send Mail` | Sends email via Microsoft Graph API |
| `Delete Mail` | Deletes email |
| `Forward Mail` | Forwards email |
| `Reply To Mail` | Replies to email |
| `Move Mail` | Moves email between folders |
| `Set Mail Categories` | Assigns categories to email |

### Calendar
| Activity | Description |
|----------|-------------|
| `Create Event` | Creates calendar event with attendees |
| `Modify Event` | Updates calendar event |
| `Delete Event` | Deletes calendar event |
| `Add Attendee` | Adds attendee to event |
| `Add Location` | Adds location to event |
| `Add Attachment` | Adds attachment to event |
| `Search Events` | Queries calendar events |
| `Get Calendars` | Lists available calendars |
| `Find Meeting Times` | Finds optimal meeting times |
| `RSVP` | Responds to meeting invitation |

### Excel Online
| Activity | Description |
|----------|-------------|
| `Read Range` | Reads from Excel Online worksheet |
| `Write Range` | Writes to Excel Online worksheet |
| `Read Cell` | Reads single cell from online workbook |
| `Write Cell` | Writes single cell to online workbook |
| `Read Row` | Reads row from online workbook |
| `Read Column` | Reads column from online workbook |
| `Append Range` | Appends data to online worksheet |
| `Paste Range` | Pastes data with method (values/formulas) |
| `Clear Range` | Clears range contents |
| `Copy Range` | Copies range within workbook |
| `Copy Sheet` | Copies worksheet |
| `Delete Rows` | Deletes rows |
| `Delete Column` | Deletes column |
| `Insert Rows` | Inserts rows |
| `Insert Column` | Inserts column |
| `Create Table` | Creates formatted table |
| `Get Table Range` | Gets table data range |
| `Create Workbook` | Creates new online workbook |
| `Delete Sheet` | Deletes worksheet |
| `Rename Sheet` | Renames worksheet |
| `Add Sheet` | Adds new worksheet |
| `Get Sheets` | Lists worksheets |
| `Get Cell Color` | Gets cell background color |
| `Set Range Color` | Sets cell background color |
| `VLookup Range` | VLOOKUP operation |

### OneDrive/SharePoint
| Activity | Description |
|----------|-------------|
| `Upload File` | Uploads file to OneDrive/SharePoint |
| `Download File` | Downloads file from OneDrive/SharePoint |
| `Delete Item` | Deletes file or folder |
| `Create Folder` | Creates new folder |
| `Find Files And Folders` | Searches by name or query |
| `Get Item` | Gets file metadata |
| `Copy Item` | Copies file or folder |
| `Move Item` | Moves file or folder |
| `Share Item` | Creates sharing link |
| `Export As PDF` | Exports document to PDF |

### SharePoint Lists
| Activity | Description |
|----------|-------------|
| `Get List Info` | Gets list metadata |
| `Get List Items` | Gets list items as DataTable |
| `Add List Items` | Adds items to list |
| `Update List Item` | Updates list item properties |
| `Delete List Item` | Deletes list item |

### Planner
| Activity | Description |
|----------|-------------|
| `Create Plan` | Creates Planner plan |
| `Get Plan` | Gets plan details |
| `List Plans` | Lists group plans |
| `Create Task` | Creates Planner task |
| `Get Task` | Gets task details |
| `List Tasks` | Lists tasks |
| `Update Task` | Modifies task |
| `Delete Task` | Deletes task |
| `Create Bucket` | Creates bucket in plan |
| `Delete Bucket` | Deletes bucket |
| `List Buckets` | Lists buckets |

### Groups
| Activity | Description |
|----------|-------------|
| `Create Group` | Creates Microsoft 365 group |
| `Delete Group` | Deletes group |
| `Get Group` | Gets group details |
| `List Groups` | Lists all groups |

---

## 9. UiPath.Testing.Activities (v25.10.0) — 16.1% adoption

### Assertions
| Activity | Description |
|----------|-------------|
| `Verify Expression` | Asserts boolean expression is true |
| `Verify Expression With Operator` | Compares two values with operator (=, <>, >, <, Contains, RegexMatch) |
| `Verify Range` | Verifies value is within or outside a numeric range |
| `Verify Control Attribute` | Verifies output attribute of an activity |

### Document Comparison
| Activity | Description |
|----------|-------------|
| `Compare PDF Documents` | Compares two PDFs, generates visual diff |
| `Compare Text` | Compares two strings, generates HTML diff report |
| `Create Comparison Rule` | Creates regex/wildcard rule for ignoring dynamic content |

### Test Data Queues
| Activity | Description |
|----------|-------------|
| `Get Test Data Queue Item` | Gets next item from Orchestrator test data queue |
| `Get Test Data Queue Items` | Batch retrieves items with filtering |
| `Add Test Data Queue Item` | Adds item to test data queue |
| `Bulk Add Test Data Queue` | Adds DataTable rows to queue |
| `Delete Test Data Queue Items` | Deletes items from queue |

### Test Data Generation
| Activity | Description |
|----------|-------------|
| `Random String` | Generates random string (lower/upper/camel/mixed) |
| `Random Number` | Generates random number in range with decimals |
| `Random Date` | Generates random date in range |
| `Random Value` | Selects random line from text file |
| `Given Name` | Generates random first name |
| `Last Name` | Generates random last name |
| `Address` | Generates random address |

### Other
| Activity | Description |
|----------|-------------|
| `Attach Document` | Attaches file as test evidence in Orchestrator |

---

## 10. UiPath.PDF.Activities (v4.0.1) — 15.5% adoption

| Activity | Description |
|----------|-------------|
| `Read PDF Text` | Extracts native text layer from PDF |
| `Read PDF With OCR` | Extracts text from scanned PDF using OCR engine |
| `Export PDF Page As Image` | Converts single PDF page to image (PNG/JPG/BMP/GIF/TIFF) |
| `Extract Images From PDF` | Extracts all embedded images from PDF |
| `Extract PDF Page Range` | Extracts page range into new PDF |
| `Join PDF` | Merges multiple PDF files into one |
| `Manage PDF Password` | Sets/removes user and owner passwords |
| `Get PDF Page Count` | Returns number of pages in PDF |
| `Convert Text To PDF` | Converts plain text to PDF |
| `Convert HTML To PDF` | Converts HTML to PDF with headers/footers |
| `Convert Email To PDF` | Converts MailMessage to PDF |
| `Read XPS Text` | Extracts text from XPS document (desktop only) |
| `Read XPS With OCR` | OCR text extraction from XPS (desktop only) |

---

## 11. UiPath.Word.Activities (v2.5.0) — 10.1% adoption

### Scope
| Activity | Description |
|----------|-------------|
| `Word Application Scope` | Opens Word document via COM, provides scope |

### COM Activities (require Word Application Scope)
| Activity | Description |
|----------|-------------|
| `Append Text` | Appends text to document with optional newline |
| `Read Text` | Reads entire document text |
| `Replace Text` | Finds and replaces text (max 256 chars) |
| `Add Image` | Inserts image at position (relative to document/bookmark/text) |
| `Insert Data Table` | Inserts DataTable as Word table |
| `Insert Hyperlink` | Inserts clickable hyperlink |
| `Set Bookmark Content` | Replaces bookmark text |
| `Export To PDF` | Exports document as PDF |
| `Save As` | Saves in different format (docx/docm/doc/html/rtf/txt) |
| `Replace Picture` | Replaces image by alt text |
| `Paste From Clipboard` | Pastes clipboard content at position |
| `Get Sensitivity Label` | Gets document sensitivity/classification label |
| `Add Sensitivity Label` | Sets document sensitivity label |

### Portable Activities (no Word required, Xceed-based)
| Activity | Description |
|----------|-------------|
| `Create New Document` | Creates blank .docx/.docm file |
| `Read Text (Document)` | Reads entire document text without COM |
| `Append Text (Document)` | Appends text to document |
| `Replace Text (Document)` | Finds and replaces text |
| `Add Image (Document)` | Inserts image at position |
| `Insert Data Table (Document)` | Inserts DataTable as table |
| `Insert Hyperlink (Document)` | Inserts hyperlink |
| `Set Bookmark Content (Document)` | Replaces bookmark text |

---

## 12. UiPath.Terminal.Activities (v2.9.1) — 4.8% adoption

### Session
| Activity | Description |
|----------|-------------|
| `Terminal Session` | Connection scope for all terminal activities (3270/5250/VT) |

### Basic Operations
| Activity | Description |
|----------|-------------|
| `Get Text` | Gets full terminal screen text |
| `Get Cursor Position` | Returns current cursor row/column (1-based) |
| `Send Control Key` | Sends function/control key (F1-F24, Enter, Tab, PA1-3, etc.) |

### Field-Based
| Activity | Description |
|----------|-------------|
| `Get Field` | Gets field text by index, label, or following text |
| `Set Field` | Sets field text by index, label, or following text |
| `Wait Field Text` | Waits until field contains specified text |
| `Wait Screen Text` | Waits until screen contains specified text |

### Coordinate-Based
| Activity | Description |
|----------|-------------|
| `Get Text At Position` | Gets text at row/column with optional length |
| `Get Field At Position` | Gets field text at row/column |
| `Set Field At Position` | Sets field at row/column |
| `Get Screen Area` | Gets text from rectangular region |
| `Get Color At Position` | Gets display color at row/column |
| `Move Cursor` | Moves cursor to row/column |
| `Move Cursor To Text` | Finds text and moves cursor to it |
| `Find Text In Screen` | Searches screen for text, returns position |
| `Wait Text At Position` | Waits for text at specific row/column |
| `Wait Screen Ready` | Waits for terminal ready state |

### Advanced
| Activity | Description |
|----------|-------------|
| `Send Keys` | Sends text/key sequence to terminal |
| `Send Keys Secure` | Sends SecureString to terminal (passwords) |

---

## 13. UiPath.FTP.Activities (v1.5.0) — 4.5% adoption

### Scope
| Activity | Description |
|----------|-------------|
| `FTP Session` (WithFtpSession) | Connection scope for FTP/FTPS/SFTP |

### Operations
| Activity | Description |
|----------|-------------|
| `Download Files` | Downloads files from FTP server |
| `Upload Files` | Uploads files to FTP server |
| `Delete` | Deletes remote file or folder |
| `Move Item` | Moves/renames remote file |
| `Directory Exists` | Checks if remote directory exists |
| `File Exists` | Checks if remote file exists |
| `Enumerate Objects` | Lists remote directory contents |

---

## 14. UiPath.GSuite.Activities (v3.8.0) — 3.9% adoption

### Gmail
| Activity | Description |
|----------|-------------|
| `Send Email` | Sends email via Gmail API |
| `Get Email List` | Retrieves emails with filtering |
| `Get Newest Email` | Gets latest unread email |
| `Get Email By ID` | Retrieves specific email |
| `Get Email Thread` | Gets entire email thread |
| `Download Email` | Downloads email as attachment |
| `Download Attachments` | Extracts email attachments |
| `Reply To Email` | Sends reply |
| `Forward Email` | Forwards email |
| `Delete Email` | Permanently deletes email |
| `Archive Email` | Archives email |
| `Mark As Read/Unread` | Changes read status |
| `Apply Email Labels` | Tags email with labels |
| `Remove Email Labels` | Removes labels from email |
| `Get Label` | Gets label details |
| `Get Labels List` | Lists all labels |
| `Turn On/Off Automatic Replies` | Out-of-office management |

### Google Drive
| Activity | Description |
|----------|-------------|
| `Get File List` | Lists files/folders with filtering |
| `Upload Files` | Uploads files to Drive |
| `Create Folder` | Creates new folder |
| `Create Document` | Creates Google Doc |
| `Create Spreadsheet` | Creates Google Sheet |
| `Get File/Folder` | Gets item details |
| `Download File` | Downloads file |
| `Copy File` | Duplicates file |
| `Rename File/Folder` | Renames item |
| `Move File` | Moves to different folder |
| `Delete File/Folder` | Deletes item |
| `Share File/Folder` | Shares with users/groups |
| `Get Permissions` | Lists sharing permissions |
| `Update Permission` | Modifies access level |
| `Delete Permission` | Removes sharing |

### Google Sheets
| Activity | Description |
|----------|-------------|
| `Read Range` | Reads range into DataTable |
| `Write Range` | Writes DataTable to range |
| `Read Cell` | Reads single cell |
| `Write Cell` | Writes single cell |
| `Read Row` | Reads entire row |
| `Write Row` | Writes to row |
| `Read Column` | Reads column |
| `Write Column` | Writes to column |
| `Get Cell Color` | Gets cell background color |
| `Set Range Color` | Sets cell background color |
| `Copy Paste Range` | Copies range |
| `Auto Fill Range` | Auto-fills pattern |
| `Delete Range` | Deletes range |
| `Delete Rows` | Deletes rows |
| `Delete Column` | Deletes column |
| `Delete Sheet` | Deletes sheet |
| `Add Sheet` | Adds new sheet |
| `Rename Sheet` | Renames sheet |
| `For Each Row` | Iterates rows |
| `For Each Sheet` | Iterates sheets |

### Google Docs
| Activity | Description |
|----------|-------------|
| `Get Document` | Gets document structure |
| `Read Text` | Reads document text |
| `Write Text` | Inserts text |
| `Find And Replace Text` | Find/replace with regex support |
| `Delete Text` | Removes text |
| `Insert Image` | Embeds image |
| `Fill Template` | Template variable substitution |

### Calendar
| Activity | Description |
|----------|-------------|
| `Create Event` | Creates calendar event |
| `Get Event List` | Lists events in date range |
| `Get Event By ID` | Gets event details |
| `Modify Event` | Updates event |
| `Delete Event` | Removes event |
| `RSVP` | Responds to invitation |
| `Forward Event` | Shares event |
| `Get Calendars` | Lists accessible calendars |

### Tasks
| Activity | Description |
|----------|-------------|
| `Create Task` | Creates task |
| `Get Tasks` | Lists tasks |
| `Update Task` | Modifies task |
| `Complete Task` | Marks task complete |
| `Delete Task` | Removes task |
| `Create Task List` | Creates task list |
| `Get Task Lists` | Lists task lists |
| `Rename Task List` | Renames list |

### Apps Script
| Activity | Description |
|----------|-------------|
| `Run Script` | Executes Google Apps Script function |

---

## 15. UiPath.Cognitive.Activities (v1.8.0) — 3.8% adoption

| Activity | Description |
|----------|-------------|
| `Google Text Analysis` | Sentiment/entity extraction via Google Cloud NLP |
| `Google Text Translate` | Text translation via Google Translate |
| `Microsoft Text Analysis` | Sentiment/key phrases via Azure Text Analytics |
| `IBM Watson Text Analysis` | Text analysis via IBM Watson NLU |
| `IBM Watson NLU Text Analysis` | Enhanced Watson NLU analysis |
| `Stanford CoreNLP Text Analysis` | Local Stanford NLP analysis |
| `Stanford CoreNLP Get Components` | Parsed component extraction |
| `Stanford CoreNLP Get OpenIE` | Open Information Extraction triples |
| `Stanford CoreNLP Get Sentence Sentiment` | Per-sentence sentiment |

---

## 16. UiPath.Presentations.Activities (v2.5.0) — 3.3% adoption

### Scope
| Activity | Description |
|----------|-------------|
| `PowerPoint Application Scope` | Opens presentation via COM, provides scope |

### COM Activities (require scope)
| Activity | Description |
|----------|-------------|
| `Insert Slide` | Inserts new slide (beginning/end/specific position) |
| `Delete Slide` | Deletes slide at position |
| `Copy Paste Slide` | Copies/moves slide between presentations |
| `Insert Text` | Inserts text into shape on slide |
| `Find And Replace Text` | Find/replace across presentation |
| `Replace Shape With Data Table` | Replaces shape with DataTable as table |
| `Replace Shape With Media` | Replaces shape with audio/video |
| `Paste Into Slide` | Pastes clipboard content into slide |
| `Insert File` | Embeds file as object in slide |
| `Format Slide Content` | Modifies shape z-index, font size, name |
| `Run Macro` | Executes VBA macro |
| `Save As PDF` | Exports presentation as PDF |
| `Save As` | Saves in different format (pptx/pptm/ppt) |
| `Add Sensitivity Label` | Sets document sensitivity label |
| `Get Sensitivity Label` | Gets document sensitivity label |

### Portable (no PowerPoint required)
| Activity | Description |
|----------|-------------|
| `Create New Presentation` | Creates blank .pptx file |
| `Add Text To Slide` | Adds text to shape in slide |
| `Insert Slide (Document)` | Inserts slide in file |
| `Delete Slide (Document)` | Deletes slide from file |
| `Find And Replace (Document)` | Find/replace in file |
| `Replace Shape With Data Table (Document)` | Inserts table in file |
| `Replace Shape With Media (Document)` | Inserts media in file |
| `Format Slide Content (Document)` | Formats content in file |

---

## 17. UiPath.IntelligentOCR.Activities (v7.0.1) — 3.0% adoption

### Digitization
| Activity | Description |
|----------|-------------|
| `Digitize Document` | Converts document to DOM with OCR text extraction |
| `Load Taxonomy` | Loads document taxonomy definition from file |

### Classification
| Activity | Description |
|----------|-------------|
| `Classify Document Scope` | Container for classification child activities |
| `Intelligent Keyword Classifier` | Cloud keyword-vector classification |
| `Keyword Based Classifier` | Local keyword classification (deprecated) |
| `DU App Classifier` | ML-based classification via DU App |
| `Present Classification Station` | Human validation UI for classification |

### Extraction
| Activity | Description |
|----------|-------------|
| `Data Extraction Scope` | Container for extraction child activities |
| `DU App Extractor` | ML-based field extraction via DU App |
| `Form Extractor` | Template-based position extraction |
| `Intelligent Form Extractor` | Enhanced form extraction for handwriting |
| `Regex Based Extractor` | Rule-based extraction with regex patterns |
| `Export Extraction Results` | Converts ExtractionResult to DataSet |

### Validation
| Activity | Description |
|----------|-------------|
| `Present Validation Station` | Human validation UI for extraction results |

### Training
| Activity | Description |
|----------|-------------|
| `Train Classifiers Scope` | Container for training classifier children |
| `Train Extractors Scope` | Container for training extractor children |
| `Keyword Based Classifier Trainer` | Trains keyword classifier |
| `Intelligent Keyword Classifier Trainer` | Trains vector keyword classifier |
| `DU App Extractor Trainer` | Trains DU App extraction model |

### Orchestrator / Redaction
| Activity | Description |
|----------|-------------|
| `Create Document Validation Artifacts` | Uploads for external validation |
| `Retrieve Document Validation Artifacts` | Downloads validated results |
| `Redact Document` | Redacts sensitive data from documents |

---

## 18. UiPath.Form.Activities (v26.0.0) — 2.5% adoption

| Activity | Description |
|----------|-------------|
| `Show Form` | Displays form (async or modal) with field bindings |
| `Close Form` | Closes an open form |
| `Hide Form` | Minimizes/hides form without closing |
| `Bring Form To Front` | Restores hidden form |
| `Get Form Fields` | Reads current field values from form |
| `Set Form Fields` | Sets field values in form |
| `Change Form Properties` | Modifies form size, position, title at runtime |
| `Execute Script` | Runs JavaScript in form context |
| `Form Trigger` | Listens for form events (click, change, message) |
| `Show Callout` | Displays popup near UI element |

---

## 19. UiPath.Cryptography.Activities (v1.5.0) — 3.2% adoption

| Activity | Description |
|----------|-------------|
| `Encrypt File` | Encrypts file with symmetric key (AES/DES/3DES/RC2/Rijndael) |
| `Decrypt File` | Decrypts file with symmetric key |
| `Encrypt Text` | Encrypts text string |
| `Decrypt Text` | Decrypts text string |
| `Keyed Hash File` | HMAC hash of file (SHA256/SHA384/SHA512/MD5) |
| `Keyed Hash Text` | HMAC hash of text |
| `PGP Sign File` | Signs file with PGP private key |
| `PGP Clear Sign File` | Clear-signs file (readable + signature) |
| `PGP Verify` | Verifies PGP signature |
| `PGP Generate Key Pair` | Generates PGP public/private key pair |

---

## 20. UiPath.Python.Activities (v1.5.0) — 3.0% adoption

| Activity | Description |
|----------|-------------|
| `Python Scope` | Initializes Python runtime (path, version, x86/x64) |
| `Load Script` | Loads .py file as Python module |
| `Run Script` | Executes Python code string |
| `Invoke Method` | Calls method on Python object |
| `Get Object` | Converts PythonObject to .NET type |

---

## 21. UiPath.OmniPage.Activities (v2.0.1) — 1.1% adoption

| Activity | Description |
|----------|-------------|
| `OmniPage OCR` | OCR text extraction using OmniPage engine (Language, Profile, DPI, Handwriting) |

---

## 22. UiPath.Java.Activities (v1.3.0) — <3% adoption

| Activity | Description |
|----------|-------------|
| `Java Scope` | Initializes JVM (JRE/JDK path) |
| `Load Jar` | Loads JAR file into classpath |
| `Invoke Java Method` | Calls static or instance Java method |
| `Create Java Object` | Instantiates Java class |
| `Convert Java Object` | Converts JavaObject to .NET type |
| `Get Java Field` | Reads field from Java object |

---

## 23. UiPath.SAP.BAPI.Activities (v2.2.2) — <3% adoption

| Activity | Description |
|----------|-------------|
| `SAP Application Scope` | SAP connection container (AppServer, SystemNumber, Client) |
| `Open Connection` | Explicit connection establishment |
| `Close Connection` | Connection cleanup |
| `Invoke SAP BAPI` | Executes SAP BAPI/RFC function with dynamic parameters |

---

## 24. UiPath.Persistence.Activities (v1.4.0) — 1.1% adoption

| Activity | Description |
|----------|-------------|
| `Create Form Task` | Creates human task in Action Center with form |
| `Wait For Form Task And Resume` | SUSPENDS workflow until form completed |
| `Create External Task` | Creates task for external system |
| `Wait For External Task And Resume` | SUSPENDS until external completion |
| `Create App Task` | Creates app-level task |
| `Wait For App Task And Resume` | SUSPENDS until app task done |
| `Start Job And Get Reference` | Starts job with tracking reference |
| `Wait For Job And Resume` | SUSPENDS until job completes |
| `Add Queue Item And Get Reference` | Adds queue item with reference |
| `Wait For Queue Item And Resume` | SUSPENDS until queue item processed |
| `Resume After Delay` | SUSPENDS for duration, releases robot |
| `Assign Tasks` | Assigns tasks to users/groups |
| `Complete Task` | Marks task finished |
| `Forward Task` | Routes task to another user |
| `Get Form Tasks` | Retrieves form tasks |
| `Get Task Data` | Gets task details |
| `Get App Tasks` | Retrieves app tasks |
| `Add Task Comment` | Appends notes to task |
| `Update Task Labels` | Modifies task tags |
| `Configure Task Timer` | Sets time constraints |

---

## 25. Other UiPath Packages (< 2% adoption)

### UiPath.Vision.Activities (v4.0.1)
| Activity | Description |
|----------|-------------|
| `Microsoft OCR` | OCR via Azure Computer Vision |
| `Google OCR` | OCR via Google Cloud Vision |
| `ABBYY OCR` | OCR via local ABBYY FineReader |
| `Tesseract OCR` | OCR via open-source Tesseract |

### UiPath.ImageProcessing (v24.10.1)
| Activity | Description |
|----------|-------------|
| `Find All` | Locates all template matches in image |
| `Find First` | Locates first template match |
| `Compare` | Computes image similarity score |
| `Are Different` | Boolean image difference check |

### UiPath.CommunicationsMining.Activities (v1.7.0)
| Activity | Description |
|----------|-------------|
| `Create CM Validation Action` | Creates Action Center task for CM |
| `Create CM Validation Artifacts` | Uploads training data |
| `Retrieve CM Validation Artifacts` | Downloads validated data |
| `Wait For CM Validation Action` | Waits for human review |

### UiPath.WorkflowEvents.Activities (v3.33.0)
| Activity | Description |
|----------|-------------|
| `App Request Trigger` | Listens for app workflow invocation requests |
| `Handle App Request` | Executes and responds to request |
| `Send Interim Result` | Pushes intermediate status |

### UiPath.MobileAutomation.Activities (v25.10.0)
| Activity | Description |
|----------|-------------|
| `Connect` | Connects to mobile device via Appium |
| `Disconnect` | Disconnects from device |
| `Get Devices` | Lists configured devices |
| `Get Applications` | Lists configured apps |
| *(UI actions via MobileTarget selectors)* | Tap, swipe, type, get text, etc. |

### UiPath.ComplexScenarios (v1.5.2)
| Activity | Description |
|----------|-------------|
| *(18 StudioX scenario templates)* | Pre-built file/email/Excel workflow patterns |
