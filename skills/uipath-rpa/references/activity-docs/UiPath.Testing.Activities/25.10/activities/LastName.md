# Generate Last Name

Generates a random surname (last name / family name) from a built-in dataset. Useful for creating realistic test data without real personal information.

**Class:** `UiPath.Testing.Activities.TestData.LastName`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Output

| Property | Type | Description |
|----------|------|-------------|
| `LastNameResult` | `OutArgument<String>` | A randomly selected last name. |

---

## XAML Example

```xml
<utad:LastName
  DisplayName="Generate Last Name"
  LastNameResult="[lastName]" />
```
