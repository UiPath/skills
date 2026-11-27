# Generate Random String

Generates a random string of a specified length and casing. Useful for creating unique identifiers, test inputs, or password-like strings.

**Class:** `UiPath.Testing.Activities.TestData.RandomString`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `Length` | `InArgument<Int32>` | Yes | — | The number of characters in the generated string. |
| `Case` | `Case` | Yes | `LowerCase` | The casing style of the generated string. See enum values below. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Output` | `OutArgument<String>` | The randomly generated string. |

---

## Enum: `Case`

| Value | Description |
|-------|-------------|
| `LowerCase` | All characters are lowercase (e.g., `abcdef`). |
| `UpperCase` | All characters are uppercase (e.g., `ABCDEF`). |
| `CamelCase` | CamelCase style (first letter of each word capitalized). |
| `Mixed` | Random mix of upper and lowercase characters. |

---

## XAML Example

```xml
<!-- 8-character lowercase string -->
<utad:RandomString
  DisplayName="Generate Random String"
  Length="[8]"
  Case="LowerCase"
  Output="[randomStr]" />

<!-- 12-character mixed-case string -->
<utad:RandomString
  DisplayName="Generate Mixed String"
  Length="[12]"
  Case="Mixed"
  Output="[randomStr]" />
```
