# Deserialize JSON Array

`UiPath.Web.Activities.DeserializeJsonArray`

Deserializes a JSON array string to a `JArray` object.

**Package:** `UiPath.WebAPI.Activities`
**Category:** JSON

## When to use

Use when the response is a JSON array and you need a `JArray` for iteration or querying.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `JsonString` | JSON string | InArgument | `string` | Yes | | | The JSON array string to deserialize |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `JsonArray` | JSON array | OutArgument | `JArray` | The deserialized JSON array |

## XAML Example

```xml
<web:DeserializeJsonArray
  DisplayName="Deserialize JSON Array"
  JsonString="[jsonArrayString]"
  JsonArray="[resultArray]" />
```

## Notes

- Input must be a valid JSON array (starting with `[`). For JSON objects, use **Deserialize JSON** instead.
- Individual elements can be accessed by index on the resulting `JArray` (e.g., `resultArray(0)`).
- Fails if `JsonString` is empty or invalid JSON.
