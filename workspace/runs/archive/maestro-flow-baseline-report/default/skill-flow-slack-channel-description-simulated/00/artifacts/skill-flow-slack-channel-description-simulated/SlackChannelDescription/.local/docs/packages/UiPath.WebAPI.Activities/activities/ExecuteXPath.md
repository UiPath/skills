# Execute XPath

`UiPath.Web.Activities.ExecuteXPath`

Evaluates an XPath expression against an XML document or string and returns the result.

**Package:** `UiPath.WebAPI.Activities`
**Category:** XML

## When to use

Use when you need to query or extract data from XML via XPath.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `XPathExpression` | XPath Expression | InArgument | `string` | Yes | | | The XPath expression to evaluate |
| `ExistingXML` | Existing XML | InArgument | `XDocument` | Yes* | | | An existing XML document to query. *Required if `XMLString` is not set (OverloadGroup: ExistingXML) |
| `XMLString` | XML String | InArgument | `string` | Yes* | | | An XML string to query. *Required if `ExistingXML` is not set (OverloadGroup: XMLString) |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `object` | The XPath evaluation result. Type depends on the expression (string, number, boolean, or node set) |

## Valid Configurations

Provide XML input in one of two ways (mutually exclusive):

**Mode A — Existing XML Document**: Set `ExistingXML` to a pre-parsed `XDocument` (e.g., from Deserialize XML).

**Mode B — XML String**: Set `XMLString` to a raw XML string. The activity parses it internally.

## XAML Examples

Query using an existing `XDocument`:

```xml
<web:ExecuteXPath
  DisplayName="Execute XPath on Document"
  ExistingXML="[xmlDoc]"
  XPathExpression="[&quot;//book[@category='fiction']/title&quot;]"
  Result="[xpathResult]" />
```

Query using a raw XML string:

```xml
<web:ExecuteXPath
  DisplayName="Execute XPath on String"
  XMLString="[xmlString]"
  XPathExpression="[&quot;count(//item)&quot;]"
  Result="[itemCount]" />
```

## Notes

- `ExistingXML` and `XMLString` are mutually exclusive (`[OverloadGroup]`). Set only one.
- The result type depends on the XPath expression: string expressions return `string`, `count()` returns a number, boolean expressions return `bool`, and node selections return node sets.
- Provide either `ExistingXML` or `XMLString`.
- Fails if the XML is invalid or the expression is invalid.
