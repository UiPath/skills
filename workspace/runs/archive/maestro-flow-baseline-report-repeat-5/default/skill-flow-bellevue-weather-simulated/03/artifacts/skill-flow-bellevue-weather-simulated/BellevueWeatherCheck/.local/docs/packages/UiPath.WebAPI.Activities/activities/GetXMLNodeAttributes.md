# Get XML Node Attributes

`UiPath.Web.Activities.GetXMLNodeAttributes`

Gets the attributes of an XML node.

**Package:** `UiPath.WebAPI.Activities`
**Category:** XML

## When to use

Use when you already have a node and need its attribute list.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `ExistingXMLNode` | ExistingXMLNode | InArgument | `XNode` | Yes | | | The XML node to extract attributes from |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Attributes` | Attributes | OutArgument | `IEnumerable<XAttribute>` | The collection of attributes on the node |

## XAML Example

```xml
<web:GetXMLNodeAttributes
  DisplayName="Get Node Attributes"
  ExistingXMLNode="[xmlNode]"
  Attributes="[nodeAttributes]" />
```

## Notes

- The input `XNode` is typically obtained from the **Get XML Nodes** activity or by navigating an `XDocument`.
- Each `XAttribute` in the output has `Name` and `Value` properties.
- If the node has no attributes, the output collection is empty.
- Only elements have attributes; other node types return none.
