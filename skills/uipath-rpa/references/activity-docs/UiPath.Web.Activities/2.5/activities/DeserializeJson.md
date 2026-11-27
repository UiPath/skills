# Deserialize JSON

`UiPath.Web.Activities.DeserializeJson<T>`

Deserializes a JSON string to a .NET object of the specified type `T`. By default, deserializes to `JObject`.

**Package:** `UiPath.WebAPI.Activities`
**Category:** JSON

## When to use

Use when you need a typed object from a JSON string for downstream activities.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `JsonString` | JSON string | InArgument | `string` | Yes | | | The JSON string to deserialize |
| `JsonSample` | JSON sample | Property | `string` | | | | Optional sample JSON used at design time for custom type inference when supported by Studio features |
| `Settings` | Serializer settings | InArgument | `JsonDeserializationSettings` | | | | Custom deserialization settings |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `JsonObject` | JSON object | OutArgument | `T` | The deserialized object. Type depends on the generic parameter (default: `JObject`) |

## XAML Examples

Deserialize to `JObject` (default):

```xml
<web:DeserializeJson x:TypeArguments="jn:JObject"
  DisplayName="Deserialize JSON"
  JsonString="[jsonString]"
  JsonObject="[jsonResult]" />
```

Deserialize to a custom type:

```xml
<web:DeserializeJson x:TypeArguments="local:MyDataClass"
  DisplayName="Deserialize to MyDataClass"
  JsonString="[jsonString]"
  JsonObject="[myDataObject]" />
```

## Notes

- The generic type parameter `T` determines the output type. When used in XAML, specify the type via `x:TypeArguments`.
- `JsonSample` is a design-time helper and may be hidden when type-inference features are not available.
- Uses Newtonsoft.Json internally. Custom settings can control date handling, null value handling, etc.
- Fails if `JsonString` is empty or invalid JSON.
- The output type is determined by the activity's generic type argument.
