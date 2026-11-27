# Generate Random Number

Generates a random numeric value between an optional minimum and maximum, with an optional number of decimal places. Returns a `Decimal`.

**Class:** `UiPath.Testing.Activities.TestData.RandomNumber`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `Min` | `InArgument<Int64>` | No | `0` | The minimum value (inclusive). Default is `0`. |
| `Max` | `InArgument<Int64>` | No | `Int64.MaxValue` | The maximum value (exclusive). Default is `long.MaxValue`. |
| `Decimals` | `InArgument<Int32>` | No | `0` | Number of decimal places in the result. Default is `0` (integer). |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Output` | `OutArgument<Decimal>` | The randomly generated number. |

---

## XAML Example

```xml
<!-- Integer between 1 and 100 -->
<utad:RandomNumber
  DisplayName="Generate Random Number"
  Min="[1]"
  Max="[100]"
  Decimals="[0]"
  Output="[randomNum]" />

<!-- Float with 2 decimal places between 0 and 1 -->
<utad:RandomNumber
  DisplayName="Generate Random Float"
  Min="[0]"
  Max="[1]"
  Decimals="[2]"
  Output="[randomFloat]" />
```
