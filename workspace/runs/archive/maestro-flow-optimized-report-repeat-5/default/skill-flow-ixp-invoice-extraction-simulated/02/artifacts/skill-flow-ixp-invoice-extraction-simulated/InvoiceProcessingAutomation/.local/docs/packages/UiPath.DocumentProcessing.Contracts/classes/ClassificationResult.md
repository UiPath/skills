# ClassificationResult

**Namespace:** `UiPath.DocumentProcessing.Contracts.Results`
**Source:** `UiPath.DocumentProcessing.Contracts/Results/ClassificationResult.cs`
**Kind:** plain data class. Mutable. JSON-serializable.

`ClassificationResult` is the **typed output of classification**. It carries the document type the classifier picked, the confidence around that pick, the page range the classification applies to, and an optional `ResultsContentReference` that points back into the `Document` DOM (the words / boxes that justified the choice).

A typical pipeline produces a `ClassificationResult` per logical document and uses it as the input to extraction. The class also provides **`AsExtractionResult(DocumentTaxonomy)`** — the bridge from classification output into a starting `ExtractionResult` for the downstream extractor.

## When to use it

- You are writing a **classifier** activity — return a `ClassificationResult`.
- You are wiring **classification → extraction** — call `AsExtractionResult(taxonomy)` to seed the `ExtractionResult` with the picked document type, then hand that to your extractor.
- You are writing a **classification validation / review** flow — the validator displays / edits a `ClassificationResult` (or its `AsExtractionResult` projection inside Action Center).

## Shape

```
ClassificationResult
 ├─ DocumentTypeId   : string                    // taxonomy id of the chosen document type
 │                                                //   throws if set to "" (null is allowed for ML splitter outputs)
 ├─ DocumentId       : string                    // throws if null or empty
 ├─ Confidence       : float                     // classifier confidence; not unified across classifiers
 ├─ OcrConfidence    : float                     // OCR confidence over the words backing the reference
 ├─ Reference        : ResultsContentReference   // words / boxes in the Document that justified the pick
 ├─ DocumentBounds   : ResultsDocumentBounds     // PageRange ("1-5") + PageCount; throws if set to null
 └─ ClassifierName   : string                    // identifier of the classifier that produced the result
```

`DocumentTypeId` accepts `null` — the ML splitter activity emits classification results with `null` `DocumentTypeId` when it can't make a call. It rejects the empty string.

## API

```csharp
// Constructors
ClassificationResult(string documentTypeId,
                     string documentId,
                     ResultsDocumentBounds documentBounds);                           // minimal; confidences default to Unknown, no Reference

ClassificationResult(string documentTypeId,
                     string documentId,
                     float confidence,
                     float ocrConfidence,
                     ResultsContentReference reference,
                     ResultsDocumentBounds documentBounds);

[JsonConstructor]
ClassificationResult(string documentTypeId,
                     string documentId,
                     float confidence,
                     float ocrConfidence,
                     ResultsContentReference reference,
                     ResultsDocumentBounds documentBounds,
                     string classifierName);

// Bridge to extraction — seeds an ExtractionResult with the classified document type
ExtractionResult AsExtractionResult(DocumentTaxonomy taxonomy);
ExtractionResult AsExtractionResult(DocumentTaxonomy taxonomy, Document dom);

// Serialization (round-trippable JSON)
string Serialize();
string Serialize(SerializationSettings serializationSettings);
static ClassificationResult Deserialize(string jsonString);
```

`AsExtractionResult` throws `ArgumentException` if `DocumentTypeId` is not present in the supplied `DocumentTaxonomy`.

The `(taxonomy, dom)` overload also walks the supplied DOM to compute the `TextType` for the document-type evidencing words (e.g. `Handwriting`, `Checkbox`) and stamps it onto `ResultsDocument.DocumentTypeField.TextType`. Use it when you have the digitized `Document` in hand; the taxonomy-only overload is fine when you don't (the DocumentTypeField stays `Text`/`Unknown`).

## Typical code

### Build a ClassificationResult from a custom classifier

```csharp
using UiPath.DocumentProcessing.Contracts.Results;

var bounds = new ResultsDocumentBounds(pageRange: "1-3", pageCount: 3);

var result = new ClassificationResult(
    documentTypeId: "Invoice",
    documentId:     document.DocumentId,
    confidence:     0.92f,
    ocrConfidence:  0.99f,
    reference:      reference,             // optional ResultsContentReference into `document`
    documentBounds: bounds);

result.ClassifierName = "MyCustomClassifier";
```

### Hand off classification to extraction

```csharp
using UiPath.DocumentProcessing.Contracts.Results;
using UiPath.DocumentProcessing.Contracts.Taxonomy;

DocumentTaxonomy taxonomy = DocumentTaxonomy.Deserialize(File.ReadAllText("taxonomy.json"));

// Seed an ExtractionResult that the extractor can populate
ExtractionResult seed = classification.AsExtractionResult(taxonomy, document);

// …pass `seed` (and `document`) to your extractor…
ExtractionResult populated = MyExtractor.Run(document, seed);
```

`seed.ResultsDocument` already has `DocumentTypeId`, `DocumentTypeName`, `DocumentGroup`, `DocumentCategory`, `DocumentTypeField`, and `Bounds` filled in. `Fields` starts as an empty array — it's the extractor's job to populate it.

### Round-trip through JSON (queue boundary)

```csharp
string json = classification.Serialize();
// …enqueue / persist / send over the wire…
ClassificationResult copy = ClassificationResult.Deserialize(json);
```

### Project an `ExtractionResult` back to a `ClassificationResult`

When you already have an `ExtractionResult` (e.g. after extraction) and need the classification view, use `ExtractionResult.AsClassificationResult()` — see [ExtractionResult](ExtractionResult.md). The two helpers are inverse projections: `AsClassificationResult` reads `ResultsDocument.DocumentTypeField`; `AsExtractionResult(taxonomy)` writes it.

## Don't

- **Don't** set `DocumentTypeId` to the empty string — the setter throws. `null` is allowed (used by ML Splitter), but downstream consumers usually treat it as "unclassified".
- **Don't** set `DocumentBounds` to `null` — the setter throws. Use `new ResultsDocumentBounds(pageRange, pageCount)` even for single-page documents.
- **Don't** call `AsExtractionResult(taxonomy)` with a taxonomy that doesn't include `DocumentTypeId` — it throws `ArgumentException`. Validate the taxonomy first if you accept user-supplied input.
- **Don't** compare `Confidence` values across different classifiers — scales are not unified. Use classifier-specific thresholds or calibrate.

## See also

- [ExtractionResult](ExtractionResult.md) — the structured extraction output. `ExtractionResult.AsClassificationResult()` is the reverse projection.
- [Document](Document.md) — the DOM that `Reference` points into and that `AsExtractionResult(taxonomy, dom)` reads to compute the document-type evidencing `TextType`.
- [DocumentTaxonomy](Taxonomy.md) — required input to `AsExtractionResult`. The `DocumentType` it resolves drives the `Group`, `Category`, and `Name` fields of the seeded `ResultsDocument`.
