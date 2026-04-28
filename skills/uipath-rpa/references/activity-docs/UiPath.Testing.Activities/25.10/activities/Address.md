# Generate Address

Generates a random postal address and returns it as a `Dictionary<String, String>`. The dictionary contains keys: `Country`, `City`, `State`, `StreetNumber`, `StreetName`, `PostalCode`.

**Class:** `UiPath.Testing.Activities.TestData.Address`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Data

```xml
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Output

| Property | Type | Description |
|----------|------|-------------|
| `AddressResult` | `OutArgument<Dictionary<String, String>>` | A dictionary containing address fields. Supported keys: `Country`, `City`, `State`, `StreetNumber`, `StreetName`, `PostalCode`. |

---

## Notes

- The `Country` and `City` filter inputs are available in the designer via dropdowns, but they are not directly configurable as XAML expression arguments (they use non-browsable dropdown widgets).
- The activity generates random addresses from a built-in dataset. Data is not fetched from any external API.

---

## XAML Example

```xml
<utad:Address
  DisplayName="Generate Address"
  AddressResult="[addressDict]" />
```

After execution, access individual fields:
```vb
addressDict("City")        ' e.g. "Chicago"
addressDict("PostalCode")  ' e.g. "60601"
```
