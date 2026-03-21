# Test Data Creation Guide

How to create test data files and UiPath types for legacy workflow testing.

---

## Excel Test Data (COM-Compliant)

### Using ExcelApplicationScope (Interop — .xls/.xlsx)

Create a DataTable in code, then write it via Excel Interop:

```xml
<!-- Step 1: Build DataTable with InvokeCode -->
<ui:InvokeCode Code="
Dim dt As New DataTable()
dt.Columns.Add(&quot;Name&quot;, GetType(String))
dt.Columns.Add(&quot;Amount&quot;, GetType(Double))
dt.Columns.Add(&quot;Date&quot;, GetType(String))
dt.Columns.Add(&quot;Status&quot;, GetType(String))
dt.Rows.Add(&quot;Invoice-001&quot;, 1500.50, &quot;2024-01-15&quot;, &quot;Active&quot;)
dt.Rows.Add(&quot;Invoice-002&quot;, 2300.00, &quot;2024-02-20&quot;, &quot;Pending&quot;)
dt.Rows.Add(&quot;Invoice-003&quot;, 890.25, &quot;2024-03-10&quot;, &quot;Closed&quot;)
dt.Rows.Add(&quot;Invoice-004&quot;, 0, &quot;&quot;, &quot;Active&quot;)
dt.Rows.Add(&quot;Invoice-005&quot;, -100.00, &quot;2024-12-31&quot;, &quot;Error&quot;)
testData = dt" Language="VBNet">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <OutArgument x:TypeArguments="sd:DataTable" x:Key="testData">[dtTestData]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>

<!-- Step 2: Write to Excel via ExcelApplicationScope -->
<!-- Use ExcelApplicationScope + ExcelWriteRange (Interop) for .xls/.xlsx -->
```

### Test data design principles
- Include edge cases: empty strings, zero values, negative numbers, special characters
- Include null/DBNull values to test null handling
- Mix data types per column to test type coercion
- Include dates in multiple formats to test parsing
- Include at least 5-10 rows for meaningful iteration testing

### Using WriteCsvFile (Portable — no Excel needed)

```xml
<!-- Write CSV then optionally convert to Excel -->
<ui:WriteCsvFile FilePath="[Path.Combine(Environment.CurrentDirectory, &quot;Data&quot;, &quot;test.csv&quot;)]"
  DataTable="[dtTestData]" />
```

---

## Top 10 File Types

| File Type | How to Create | Key Activity | Notes |
|-----------|--------------|-------------|-------|
| **Excel (.xls/.xlsx)** | `ExcelApplicationScope` + `ExcelWriteRange` | COM Interop | Use `.xls` for max legacy compat; `.xlsx` for modern |
| **CSV (.csv)** | `WriteCsvFile` or `Write Text File` | Portable | Set `Delimitator` explicitly; specify `"UTF-8"` encoding |
| **Text (.txt)** | `Write Text File` activity | System.IO | Use `Encoding="UTF-8"` for portability |
| **JSON (.json)** | `Serialize JSON` + `Write Text File` | WebAPI package | Build JObject/JArray in InvokeCode, serialize, write |
| **XML (.xml)** | Build XDocument in InvokeCode + `Write Text File` | System.Xml.Linq | Or use `Serialize XML` if available |
| **PDF (.pdf)** | Export from Excel/Word scope, or HTML string + wkhtmltopdf | Requires source app | No native PDF creation activity in legacy |
| **Word (.docx)** | `WordApplicationScope` + `Word Write Text` | COM Interop | Requires Word installed |
| **HTML (.html)** | `Write Text File` with HTML string content | String building | Build HTML in InvokeCode or Assign |
| **Email (.eml/.msg)** | `Save Mail Message` from mail activities | Mail package | Create MailMessage object first |
| **Config (.xlsx)** | REFramework pattern: Config.xlsx with Settings/Constants/Assets sheets | Excel Interop | See `_REFRAMEWORK.md` for sheet structure |

### Creating JSON test data

```vb
' InvokeCode — build JSON string
Dim json As String = "{" & vbCrLf &
  "  ""name"": ""Test User""," & vbCrLf &
  "  ""amount"": 1500.50," & vbCrLf &
  "  ""items"": [""A"", ""B"", ""C""]" & vbCrLf &
  "}"
output = json
```

### Creating XML test data

```vb
' InvokeCode — build XML string
Dim xml As String = "<?xml version=""1.0"" encoding=""UTF-8""?>" & vbCrLf &
  "<Invoices>" & vbCrLf &
  "  <Invoice Id=""001"" Amount=""1500.50"" />" & vbCrLf &
  "  <Invoice Id=""002"" Amount=""2300.00"" />" & vbCrLf &
  "</Invoices>"
output = xml
```

---

## Top 10 UiPath Types

| Type | How to Create | Common Test Values | VB.NET Expression |
|------|--------------|-------------------|-------------------|
| **DataTable** | `Build Data Table` activity or InvokeCode | Headers + 5-10 rows, mixed types, nulls | `New DataTable()` |
| **String** | `Assign` / literal | `"test"`, `""`, `Nothing`, special chars `<>&"` | `"value"` |
| **Int32** | `Assign` / `CInt()` | `0`, `-1`, `Integer.MaxValue`, `Integer.MinValue` | `CInt("42")` |
| **Boolean** | `Assign` | `True`, `False` | `True` |
| **DateTime** | `Assign` / `DateTime.Parse()` | Today, epoch, future, `DateTime.MinValue` | `DateTime.Now` |
| **Dictionary(Of String, Object)** | InvokeCode or `Assign` | Config-style key-value pairs, nested objects | `New Dictionary(Of String, Object)` |
| **String()** (array) | `Assign` / `Split()` | Empty `{}`, single item, many items | `New String() {"a","b","c"}` |
| **SecureString** | `Get Credential` or InvokeCode | Test password strings | `New NetworkCredential("","pass").SecurePassword` |
| **MailMessage** | `Get Outlook Mail Messages` or InvokeCode | Email with To/Subject/Body/Attachments | `New System.Net.Mail.MailMessage()` |
| **QueueItem** | `Get Transaction Item` from Orchestrator | SpecificContent dictionary, Priority, Deadline | Requires Orchestrator queue |

### Creating a test Dictionary (Config-style)

```vb
' InvokeCode
Dim config As New Dictionary(Of String, Object)
config("MaxRetryNumber") = 3
config("logF_BusinessProcessName") = "TestProcess"
config("OrchestratorQueueName") = "TestQueue"
config("ExcelFilePath") = "Data\Input\test.xlsx"
output = config
```

### Creating a test DataTable with edge cases

```vb
' InvokeCode
Dim dt As New DataTable()
dt.Columns.Add("Name", GetType(String))
dt.Columns.Add("Amount", GetType(Double))
dt.Columns.Add("IsActive", GetType(Boolean))

' Normal rows
dt.Rows.Add("Alice", 100.50, True)
dt.Rows.Add("Bob", 0, False)

' Edge cases
dt.Rows.Add("", -999.99, True)           ' Empty name
dt.Rows.Add(DBNull.Value, DBNull.Value, DBNull.Value)  ' All nulls
dt.Rows.Add("Special <>&""chars", 1E+15, True)  ' Special chars, large number

testData = dt
```
