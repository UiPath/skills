# Testing — Document & Text Comparison

PDF document and text comparison APIs on the `testing` service (`ITestingService`). For general info see [testing.md](testing.md).

---

## ComparePdfDocuments

Compares two PDF documents and verifies if they are equivalent.

```csharp
ComparisonResult ComparePdfDocuments(
    string baselinePath,
    string targetPath,
    ComparisonType comparisonType = ComparisonType.Line,
    CompareDocumentsOptions options = null
);
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `baselinePath` | `string` | — | Path of the base document (reference) |
| `targetPath` | `string` | — | Path of the document to compare against the base |
| `comparisonType` | `ComparisonType` | `ComparisonType.Line` | Granularity of comparison |
| `options` | `CompareDocumentsOptions` | `null` | Comparison options (built via `TestingOptions.CompareDocuments()`) |

### Usage

```csharp
// Simple comparison
ComparisonResult result = testing.ComparePdfDocuments(
    @"C:\Docs\baseline.pdf",
    @"C:\Docs\target.pdf"
);

if (result.AreEquivalent)
{
    Log("Documents match.");
}

// With options
ComparisonResult result = testing.ComparePdfDocuments(
    @"C:\Docs\baseline.pdf",
    @"C:\Docs\target.pdf",
    ComparisonType.Word,
    TestingOptions.CompareDocuments()
        .WithIgnoreRegexRule("dates", @"\d{2}/\d{2}/\d{4}")
        .WithIgnoreIdenticalItems(true)
        .WithIncludeWidgets(true)
        .WithGenerateHtml(@"C:\Output\diff.html")
        .WithContinueOnError(true)
);
```

---

## CompareText

Compares two text strings and verifies if they are equivalent.

```csharp
ComparisonResult CompareText(
    string baselineText,
    string targetText,
    ComparisonType comparisonType = ComparisonType.Line,
    CompareTextOptions opts = null
);
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `baselineText` | `string` | — | The reference text |
| `targetText` | `string` | — | The text to compare against the reference |
| `comparisonType` | `ComparisonType` | `ComparisonType.Line` | Granularity of comparison |
| `opts` | `CompareTextOptions` | `null` | Comparison options (built via `TestingOptions.CompareText()`) |

### Usage

```csharp
// Simple comparison
ComparisonResult result = testing.CompareText(expectedText, actualText);

// With options
ComparisonResult result = testing.CompareText(
    expectedText,
    actualText,
    ComparisonType.Word,
    TestingOptions.CompareText()
        .WithWordSeparators(".,!?:\n ")
        .WithIgnoreWildcardRule("timestamps", "*:*:*")
        .WithGenerateSemanticResult(true)
        .WithGenerateHtml(@"C:\Output\text-diff.html")
);

if (!result.AreEquivalent)
{
    foreach (var diff in result.Differences)
    {
        if (diff.Operation != Operation.Equal)
        {
            Log($"{diff.Operation}: {diff.Text}");
        }
    }
}
```

---

## ComparisonType Enum

Determines the granularity of comparison.

| Value | Description |
|---|---|
| `ComparisonType.Line` | Compare line by line |
| `ComparisonType.Word` | Compare word by word |
| `ComparisonType.Character` | Compare character by character |

---

## ComparisonResult

Returned by both `ComparePdfDocuments` and `CompareText`.

| Property | Type | Description |
|---|---|---|
| `AreEquivalent` | `bool` | `true` if no differences found (all differences have `Operation.Equal`) |
| `Differences` | `List<Difference>` | List of individual differences |
| `SemanticDifferences` | `SemanticDifferences` | Semantic analysis result (only populated when `GenerateSemanticResult` is enabled) |

### Difference

| Property | Type | Description |
|---|---|---|
| `Operation` | `Operation` | `Inserted`, `Deleted`, or `Equal` |
| `Text` | `string` | The text of this difference segment |

### SemanticDifferences

| Property | Type | Description |
|---|---|---|
| `AreSemanticallyEquivalent` | `bool` | Whether the texts are semantically equivalent despite textual differences |
| `Explanation` | `string` | Overall explanation of semantic differences |
| `Differences` | `List<SemanticDifference>` | List of individual semantic differences |

### SemanticDifference

| Property | Type | Description |
|---|---|---|
| `Explanation` | `string` | Description of this specific semantic difference |

---

## CompareTextOptions

Created via `TestingOptions.CompareText()`. Configured using fluent extension methods.

| Property | Type | Default | Description |
|---|---|---|---|
| `WordSeparators` | `string` | `".,!?:\n "` | Characters considered as word separators |
| `GenerateSemanticResult` | `bool` | `false` | Also generate semantic analysis |
| `OutputDiffType` | `DocumentOutputDiffType` | `None` | Diff output format |
| `OutputFilePath` | `string` | `null` | Path for the output diff file |
| `ContinueOnError` | `bool` | `false` | Continue execution if comparison throws an error |
| `Rules` | `List<ComparisonRule>` | `[]` | Comparison rules (regex or wildcard) |

### Fluent Methods

| Method | Description |
|---|---|
| `.WithWordSeparators(string separators)` | Set word separator characters |
| `.WithGenerateSemanticResult(bool generate)` | Enable/disable semantic analysis |
| `.WithGenerateHtml(string filePath)` | Generate HTML diff output at the given path |
| `.WithIgnoreRegexRule(string name, string pattern, bool usePlaceholder = true)` | Add a regex-based ignore rule |
| `.WithIgnoreWildcardRule(string name, string pattern, bool usePlaceholder = true)` | Add a wildcard-based ignore rule |
| `.WithContinueOnError(bool continueOnError)` | Continue on error |

---

## CompareDocumentsOptions

Created via `TestingOptions.CompareDocuments()`. Extends `CompareTextOptions` with additional properties.

| Property | Type | Default | Description |
|---|---|---|---|
| `IgnoreIdenticalItems` | `bool` | `true` | Ignore identical lines during comparison |
| `IncludeWidgets` | `bool` | `true` | Include images and URIs in comparison |
| `IgnoreWidgetsLocation` | `bool` | `false` | Ignore page and position of widgets |
| *(inherits all CompareTextOptions properties)* | | | |

### Additional Fluent Methods

| Method | Description |
|---|---|
| `.WithIgnoreIdenticalItems(bool ignore)` | Set whether to ignore identical items |
| `.WithIncludeWidgets(bool include)` | Set whether to include widgets |
| `.WithIgnoreWidgetsPageAndPosition(bool ignore)` | Set whether to ignore widget location |
| `.WithGeneratePdf(string baselinePath, string targetPath)` | Generate PDF diff output |

---

## Comparison Rules

Rules allow ignoring dynamic content (dates, IDs, timestamps) during comparison.

### RegexRule

Ignores text matching a regex pattern.

```csharp
new RegexRule(string name, string pattern, bool usePlaceholder = true)
```

### WildcardRule

Ignores text matching a wildcard pattern (`*` matches any characters, `?` matches a single character).

```csharp
new WildcardRule(string name, string pattern, bool usePlaceholder = true)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | — | Rule name (used in placeholder: `<<excluded_by_{name}>>`) |
| `pattern` | `string` | — | Regex or wildcard pattern to match |
| `usePlaceholder` | `bool` | `true` | Replace matched text with a placeholder instead of removing it |

### Usage with Fluent API

```csharp
var options = TestingOptions.CompareDocuments()
    .WithIgnoreRegexRule("dates", @"\d{2}/\d{2}/\d{4}")
    .WithIgnoreRegexRule("guids", @"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    .WithIgnoreWildcardRule("timestamps", "*:*:* *M");
```

---

## DocumentOutputDiffType Enum

| Value | Description |
|---|---|
| `None` | No diff output |
| `Html` | Generate HTML diff file |
| `Pdf` | Generate PDF diff files (documents only) |
| `Unidiff` | Generate unified diff format |
