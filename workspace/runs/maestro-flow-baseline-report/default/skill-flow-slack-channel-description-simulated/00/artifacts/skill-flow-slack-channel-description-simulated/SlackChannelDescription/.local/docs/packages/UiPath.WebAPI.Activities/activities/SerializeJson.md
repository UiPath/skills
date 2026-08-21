# Serialize JSON

`UiPath.Web.Activities.JSON.SerializeJson`

Serializes the given object to a JSON string, optionally using custom serializer settings.

**Package:** `UiPath.WebAPI.Activities`
**Category:** JSON

## When to use

Use when you need to send or store JSON derived from an object.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `InputObject` | Input object | InArgument | `object` | Yes | | | The object to serialize to JSON |
| `Settings` | Serializer settings | InArgument | `JsonSerializationSettings` | | | | Custom serialization settings (date format, null handling, etc.) |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `string` | The serialized JSON string |

## XAML Example

```xml
<json:SerializeJson
  DisplayName="Serialize Object to JSON"
  InputObject="[myObject]"
  Result="[jsonString]" />
```

## Notes

- Uses Newtonsoft.Json internally. Accepts any .NET object including `DataTable`, `JObject`, `Dictionary`, custom types, etc.
- Custom `JsonSerializationSettings` can control indentation, null value handling, date formatting, and other serialization behaviors.
- Fails if `InputObject` is null.
