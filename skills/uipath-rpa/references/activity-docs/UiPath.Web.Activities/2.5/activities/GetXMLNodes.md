# Get XML Nodes

`UiPath.Web.Activities.GetNodes`

Deserializes XML into a list of XML nodes.

**Package:** `UiPath.WebAPI.Activities`
**Category:** XML

## When to use

Use when you need to enumerate the top-level XML nodes.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `ExistingXML` | Existing XML | InArgument | `XDocument` | Yes* | | | An existing XML document. *Required if `XMLString` is not set (OverloadGroup: Existing XML Document) |
| `XMLString` | XML String | InArgument | `string` | Yes* | | | An XML string. *Required if `ExistingXML` is not set (OverloadGroup: XML Text) |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `XMLNodes` | XMLNodes | OutArgument | `IEnumerable<XNode>` | The collection of XML nodes extracted from the document |

## Valid Configurations

Provide XML input in one of two ways (mutually exclusive):

**Mode A — Existing XML Document**: Set `ExistingXML` to a pre-parsed `XDocument`.

**Mode B — XML String**: Set `XMLString` to a raw XML string.

## XAML Examples

From an existing document:

```xml
<web:GetNodes
  DisplayName="Get XML Nodes from Document"
  ExistingXML="[xmlDoc]"
  XMLNodes="[nodeList]" />
```

From a string:

```xml
<web:GetNodes
  DisplayName="Get XML Nodes from String"
  XMLString="[xmlString]"
  XMLNodes="[nodeList]" />
```

## Notes

- `ExistingXML` and `XMLString` are mutually exclusive (`[OverloadGroup]`). Set only one.
- Output nodes can be iterated with a **For Each** activity and passed to **Get XML Node Attributes** or further XPath queries.
- For element-only enumeration, use the activity that returns element nodes from `Root`.
