# Document (DOM)

**Namespace:** `UiPath.DocumentProcessing.Contracts.Dom`
**Source:** `UiPath.DocumentProcessing.Contracts/Dom/Document.cs`
**Kind:** plain data class (POCO). Mutable. JSON-serializable.

`Document` is the **Document Object Model** produced by digitization. It is the normalized, OCR-/parser-independent representation of a single physical document (PDF, image, email, plain text, …). Every downstream stage — classification, extraction, validation, training — takes the `Document` as input alongside any stage-specific result.

## When to use it

- You are writing a **digitizer**: build and return a `Document`.
- You are writing a **classifier** or **extractor**: receive `Document` as input; use it to locate text / boxes / pages referenced by your result.
- You need to **resolve a `ResultsContentReference`** back to page coordinates or raw text: the reference indexes into this `Document`.
- You need the **raw text** of the document: reconstruct it from `Pages[*].Sections[*].WordGroups[*].Words[*].Text`, in order. `Word.IndexInText` points into that text.

## Shape

```
Document
 ├─ DocumentId : string                     // unique id
 ├─ ContentType : string                    // MIME, e.g. "application/pdf", "image/jpeg"
 ├─ Length : int                            // character length of the raw text
 ├─ Pages : Page[]
 │   ├─ PageIndex : int
 │   ├─ Size : Box                          // page bounds (Top/Left usually 0)
 │   ├─ Sections : PageSection[]
 │   │   ├─ IndexInText : int, Length : int
 │   │   ├─ Language : string
 │   │   ├─ Rotation : Rotation             // None | 90 | 180 | 270 | Other
 │   │   ├─ SkewAngle : float
 │   │   ├─ Type : SectionType              // Vertical | Paragraph | Header | Footer | Table
 │   │   └─ WordGroups : WordGroup[]
 │   │       ├─ IndexInText : int, Length : int
 │   │       ├─ Type : WordGroupType        // Sentence | TableCell | TableRowEnd | Heading | Other
 │   │       └─ Words : Word[]
 │   │           ├─ Box : Box               // axis-aligned bounds
 │   │           ├─ Polygon : Polygon       // tight polygon, clockwise, first point = top-left of the word
 │   │           ├─ IndexInText : int       // offset into the document's raw text
 │   │           ├─ Text : string
 │   │           ├─ OcrConfidence : float
 │   │           ├─ VisualLineNumber : int  // -1 if unknown
 │   │           ├─ TextType : TextType     // Text | Handwriting | Checkbox | Barcode | QRcode | Stamp | Logo | Circle | Underline | Cut | Unknown
 │   │           └─ MarkupType : MarkupType[]
 │   ├─ PageMarkups : PageMarkup[]          // circles / underlines / strikethroughs spanning multiple words
 │   ├─ ProcessingSource : ProcessingSource // Unknown | Ocr | Pdf | PlainText | PdfAndOcr
 │   ├─ IndexInText : int, TextLength : int
 │   ├─ SkewAngle : float
 │   ├─ Rotation : Rotation?
 │   └─ PageMetadata : List<Metadata>       // Key/Value pairs
 └─ DocumentMetadata : List<Metadata>
```

`Box` holds `Top`, `Left`, `Width`, `Height` (`double`, rounded to 4 decimals) plus derived `Right`, `Bottom`, `HorizontalCenter`, `VerticalCenter`, `Area`, `IsEmpty`. Construct via `Box.CreateChecked`, `Box.CreateUnchecked`, `Box.CreateSize`. `Box.None` is the zero box.

`IndexInText` fields form a consistent **global text offset space** across the whole document. The document's raw text is implicit — rebuild it by concatenating `Word.Text` in order, separated by whitespace / newlines, so that each word lands at its `IndexInText`.

## API

```csharp
// Serialization (round-trippable JSON)
string Serialize();
string Serialize(SerializationSettings serializationSettings);
static Document Deserialize(string jsonString);

// Query
bool IsTextTypeInDocument(TextType textType);

// Factory — build a Document from plain text. Produces a single page; sections
// are split on blank lines, word groups on consecutive whitespace, words on
// single whitespace. Useful for tests or text-only inputs.
static Document GenerateFromText(string text, string documentId);
```

There is no constructor that validates structure — the class is a data container. If you construct one by hand, ensure `IndexInText` / `Length` values are consistent across pages / sections / word groups / words or downstream consumers will misalign.

## Typical code

### Load / save

```csharp
using UiPath.DocumentProcessing.Contracts.Dom;

var json = File.ReadAllText("digitized.json");
Document document = Document.Deserialize(json);

// …mutate or inspect…

File.WriteAllText("digitized.json", document.Serialize());
```

### Build from plain text (tests, fallbacks)

```csharp
Document doc = Document.GenerateFromText("Invoice\nTotal: 42.00 USD", documentId: "doc-1");
```

### Reconstruct the raw document text

```csharp
static string GetDocumentText(Document document)
{
    var sb = new StringBuilder(document.Length);
    foreach (var page in document.Pages)
        foreach (var section in page.Sections)
            foreach (var group in section.WordGroups)
                foreach (var word in group.Words)
                {
                    // Pad with spaces so that sb.Length == word.IndexInText
                    while (sb.Length < word.IndexInText) sb.Append(' ');
                    sb.Append(word.Text);
                }
    return sb.ToString();
}
```

### Find all words inside a bounding box on a page

```csharp
using UiPath.DocumentProcessing.Contracts;
using UiPath.DocumentProcessing.Contracts.Dom;

static IEnumerable<Word> WordsInsideBox(Document document, int pageIndex, Box area)
{
    var page = document.Pages[pageIndex];
    return page.Sections
        .SelectMany(s => s.WordGroups)
        .SelectMany(g => g.Words)
        .Where(w =>
            w.Box.Left >= area.Left &&
            w.Box.Top >= area.Top &&
            w.Box.Right <= area.Right &&
            w.Box.Bottom <= area.Bottom);
}
```

### Detect handwriting / checkboxes anywhere

```csharp
bool hasHandwriting = document.IsTextTypeInDocument(TextType.Handwriting);
bool hasCheckboxes  = document.IsTextTypeInDocument(TextType.Checkbox);
```

### Attach a `ResultsValue` to a specific area on a page

```csharp
using UiPath.DocumentProcessing.Contracts.Results;

ResultsValue value = ResultsValue.CreateWithWordsReference(
    newValue: "ACME Inc.",
    pageIndex: 0,
    area: Box.CreateChecked(top: 100, left: 50, width: 200, height: 30),
    confidence: 0.95f,
    ocrConfidence: 0.99f,
    document: document); // required: the factory walks the DOM to collect the covered words
```

`ResultsValue.CreateWithWordsReference` / `CreateWithCustomAreaReference` both take the `Document` so they can index the covered words and produce a valid `ResultsContentReference` back into the DOM. (Both delegate to an internal `ResultsValueFactory`; only the static methods on `ResultsValue` are public.)

## Enums — quick reference

- `TextType`: `Unknown`, `Text`, `Checkbox`, `Handwriting`, `Barcode`, `QRcode`, `Stamp`, `Logo`, `Circle`, `Underline`, `Cut`.
- `SectionType`: `Vertical`, `Paragraph`, `Header`, `Footer`, `Table`.
- `WordGroupType`: `Sentence`, `TableCell`, `TableRowEnd`, `Heading`, `Other`.
- `Rotation`: `None`, `Rotated90`, `Rotated180`, `Rotated270`, `Other`.
- `ProcessingSource`: `Unknown`, `Ocr`, `Pdf`, `PlainText`, `PdfAndOcr`.
- `MarkupType` — see `Dom/MarkupType.cs`.

## Don't

- **Don't** assume a specific origin for `Box`. The DOM uses page-local coordinates with `Top`/`Left` as the origin, but the origin may be the top-left (default) or differ per processing source — trust the values, not an assumption.
- **Don't** trust `Box` alone for rotated words — use `Polygon` when you need the tight outline. `Polygon` enforces exactly 4 points in clockwise order and throws `ArgumentException` otherwise.
- **Don't** build a `Document` with missing `WordGroups.Words` just to carry metadata; downstream code assumes non-null arrays.
- **Don't** reuse a `Document` instance across threads while a mutator (e.g. validation) is running — there is no concurrency protection.
