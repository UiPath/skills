# Word — Portable API

Lightweight cross-platform API using `word.UseDocument(...)` returning `IWordDocumentHandle`. Works without COM interop (uses Xceed). For general info see [word.md](word.md).

---

## Opening Documents

### `word.UseDocument(string documentPath, bool createNew = true)`

Opens or creates a Word document.
Returns `IWordDocumentHandle` (disposable — use with `using`).

```csharp
using var doc = word.UseDocument("report.docx");
using var newDoc = word.UseDocument("new-report.docx", createNew: true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `documentPath` | `string` | — | Path of the document |
| `createNew` | `bool` | `true` | Create a new document if it does not exist |

---

## Operations

### AppendText

Appends text to a document.

```csharp
// With newLine control
void AppendText(this IWordDocumentHandle wordDocument, string text, bool newLine);

// Default: appends on a new line
void AppendText(this IWordDocumentHandle wordDocument, string text);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `string` | — | Text to append |
| `newLine` | `bool` | `true` | If `true`, appends on a new line; if `false`, appends directly after existing text |

```csharp
doc.AppendText("First line.");
doc.AppendText("Second line on new line.");
doc.AppendText(" Continued on same line.", false);
```

### ReadText

Reads all text from the document.

```csharp
string ReadText(this IWordDocumentHandle wordDocument);
```

Returns the full text content.

```csharp
string content = doc.ReadText();
Log($"Document text: {content}");
```

### ReplaceText

Searches and replaces a text string with another.

```csharp
bool ReplaceText(this IWordDocumentHandle wordDocument, string search, string replace);
```

| Parameter | Type | Description |
|---|---|---|
| `search` | `string` | Text to search for |
| `replace` | `string` | Replacement text |

Returns `true` if the searched text was found.

```csharp
bool found = doc.ReplaceText("{{Placeholder}}", "Actual Value");
```
