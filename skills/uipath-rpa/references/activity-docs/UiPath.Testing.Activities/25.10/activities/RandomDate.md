# Generate Random Date

Generates a random `DateTime` value within a specified range. The lower bound (`MinDate`) is inclusive; the upper bound (`MaxDate`) is exclusive.

**Class:** `UiPath.Testing.Activities.TestData.RandomDate`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `MinDate` | `InArgument<DateTime>` | Yes | The inclusive lower bound of the date range. |
| `MaxDate` | `InArgument<DateTime>` | Yes | The exclusive upper bound of the date range. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Output` | `OutArgument<DateTime>` | The randomly generated date within `[MinDate, MaxDate)`. |

---

## XAML Example

```xml
<utad:RandomDate
  DisplayName="Generate Random Date"
  MinDate="[New DateTime(2020, 1, 1)]"
  MaxDate="[New DateTime(2025, 1, 1)]"
  Output="[randomDate]" />
```
