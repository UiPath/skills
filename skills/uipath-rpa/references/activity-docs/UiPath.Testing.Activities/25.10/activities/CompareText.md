# Compare Text

Compares two text strings (baseline vs. target) and returns whether they are equivalent, along with a list of differences. Supports line-by-line, word-by-word, or character-by-character comparison. Accepts comparison rules (created via **Create Comparison Rule**) to exclude dynamic sections. Optionally uses Autopilot AI to interpret differences semantically.

**Class:** `UiPath.Testing.Activities.CompareText`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `BaselineText` | `InArgument<String>` | Yes | — | The reference text (the expected / golden content). |
| `TargetText` | `InArgument<String>` | Yes | — | The text to compare against the baseline (the actual content). |
| `ComparisonType` | `ComparisonType` | Yes* | — | Granularity of comparison: `Line`, `Word`, or `Character`. *Hidden when `InterpretDifferencesWithAutopilot` is `true`. |
| `InterpretDifferencesWithAutopilot` | `Boolean` | No | `false` | If `true`, uses Autopilot AI to semantically interpret differences. When enabled, `ComparisonType` is hidden and `SemanticDifferences` is populated instead of `Differences`. |
| `ContinueOnFailure` | `InArgument<Boolean>` | No | `true` | If `true`, the workflow continues even if the comparison finds differences (test case is still marked failed). |
| `Rules` | `List<InArgument<ComparisonRule>>` | No | — | *(Legacy)* Individual comparison rules added via the designer. |
| `RulesList` | `InArgument<List<ComparisonRule>>` | No | — | A list of `ComparisonRule` objects (from **Create Comparison Rule**) to exclude dynamic sections. Prefer this over `Rules` when building rules programmatically. |
| `WordSeparators` | `InArgument<String>` | No | `".,!?:\n "` | Characters treated as word separators. Only visible when `ComparisonType` is `Word`. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Result` | `OutArgument<Boolean>` | `true` if texts are equivalent (no differences), `false` if differences were found. |
| `OutputFilePath` | `InArgument<String>` | Path where the HTML diff output file is saved. Default: `"differences.html"`. |
| `Differences` | `OutArgument<IEnumerable<Difference>>` | List of differences. Each `Difference` has `Operation` (`Equal`, `Inserted`, `Deleted`) and `Text`. Populated when `InterpretDifferencesWithAutopilot` is `false`. |
| `SemanticDifferences` | `OutArgument<SemanticDifferences>` | Semantic interpretation of differences from Autopilot. Only populated when `InterpretDifferencesWithAutopilot` is `true`. |

---

## Valid Configurations

**Standard comparison** (`InterpretDifferencesWithAutopilot = false`):
- Set `ComparisonType` to `Line`, `Word`, or `Character`.
- `WordSeparators` is only available when `ComparisonType = Word`.
- `Differences` output is populated; `SemanticDifferences` is not.

**Autopilot-interpreted comparison** (`InterpretDifferencesWithAutopilot = true`):
- `ComparisonType` is hidden and ignored.
- `SemanticDifferences` output is populated; `Differences` is not.

These two modes are mutually exclusive.

---

## Enum: `ComparisonType`

| Value | Description |
|-------|-------------|
| `Line` | Compares text line by line. |
| `Word` | Compares text word by word (uses `WordSeparators` to tokenize). |
| `Character` | Compares text character by character. |

---

## XAML Example

```xml
<!-- Standard line-by-line comparison with a rule to ignore dates -->
<uta:CompareText
  DisplayName="Compare Invoice Text"
  BaselineText="[baselineContent]"
  TargetText="[actualContent]"
  ComparisonType="Line"
  ContinueOnFailure="True"
  RulesList="[New List(Of ComparisonRule) From {dateRule}]"
  OutputFilePath="&quot;Output\diff.html&quot;"
  Result="[compareResult]"
  Differences="[diffs]" />

<!-- Word comparison with custom separators -->
<uta:CompareText
  DisplayName="Compare Text (Word)"
  BaselineText="[baseline]"
  TargetText="[target]"
  ComparisonType="Word"
  WordSeparators="&quot; ,.\n&quot;"
  OutputFilePath="&quot;Output\diff.html&quot;"
  Result="[compareResult]" />

<!-- Autopilot semantic interpretation -->
<uta:CompareText
  DisplayName="Compare Text (Autopilot)"
  BaselineText="[baseline]"
  TargetText="[target]"
  InterpretDifferencesWithAutopilot="True"
  OutputFilePath="&quot;Output\diff.html&quot;"
  Result="[compareResult]"
  SemanticDifferences="[semanticResult]" />
```
