# Deserialize XML

`UiPath.Web.Activities.DeserializeXml`

Deserializes an XML string to an `XDocument` object.

**Package:** `UiPath.WebAPI.Activities`
**Category:** XML

## When to use

Use when you need an `XDocument` for XPath queries or node inspection.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `XMLString` | XML String | InArgument | `string` | Yes | | | The XML string to deserialize |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `XMLDocument` | XMLDocument | OutArgument | `XDocument` | The parsed XML document |

## XAML Example

> **XAML reference.** Class `UiPath.Web.Activities.DeserializeXml`. Assembly **and** namespace are `UiPath.Web.Activities` — the `UiPath.WebAPI.Activities` package name does **not** go in `assembly=`/`clr-namespace:`. Declare `xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"`.

```xml
<web:DeserializeXml
  DisplayName="Deserialize XML"
  XMLString="[xmlString]"
  XMLDocument="[xmlDoc]" />
```

## Notes

- The output `XDocument` (from `System.Xml.Linq`) can be queried using LINQ to XML or passed to **Execute XPath** and **Get XML Nodes** activities.
- Fails if `XMLString` is empty or invalid XML.
