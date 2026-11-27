# Generate Given Name

Generates a random first name (given name) from a built-in dataset. Useful for creating realistic test data without real personal information.

**Class:** `UiPath.Testing.Activities.TestData.GivenName`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Output

| Property | Type | Description |
|----------|------|-------------|
| `GivenNameResult` | `OutArgument<String>` | A randomly selected first name. |

---

## XAML Example

```xml
<utad:GivenName
  DisplayName="Generate Given Name"
  GivenNameResult="[firstName]" />
```
