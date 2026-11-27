# Generate Random Value

Picks a random line from a single-column `.txt` or `.csv` file and returns it as a string. The file can contain up to ~2 billion lines. Useful for selecting random test values from a predefined list (e.g., product codes, user IDs, test inputs).

**Class:** `UiPath.Testing.Activities.TestData.RandomValue`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `FilePath` | `InArgument<String>` | Yes | The absolute or relative path to the `.txt` or `.csv` file. The file must contain one value per line. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Value` | `OutArgument<String>` | The string from the randomly selected line in the file. |

---

## Notes

- The file must be a single-column text file (one entry per line).
- Both `.txt` and `.csv` formats are supported.
- The random selection is uniformly distributed across all lines.

---

## XAML Example

```xml
<utad:RandomValue
  DisplayName="Generate Random Value"
  FilePath="&quot;Data\TestValues.txt&quot;"
  Value="[randomVal]" />
```
