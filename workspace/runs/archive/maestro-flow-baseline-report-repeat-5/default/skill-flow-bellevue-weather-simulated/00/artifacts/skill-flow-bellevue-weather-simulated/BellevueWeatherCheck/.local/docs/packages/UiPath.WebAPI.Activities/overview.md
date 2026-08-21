# UiPath Web Activities

`UiPath.WebAPI.Activities`

Activities for making HTTP/REST requests and working with JSON and XML data. Includes modern HTTP Request with retry policies, authentication, and proxy support, plus JSON/XML serialization and parsing utilities.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### Web

| Activity | Description |
|----------|-------------|
| [HTTP Request](activities/NetHttpRequest.md) | Send HTTP requests with configurable authentication, retry policies, proxy, and SSL options. Returns a structured `HttpResponseSummary` |
| [HTTP Request (legacy)](activities/HttpClient.md) | Legacy HTTP request activity using RestSharp. Prefer the newer HTTP Request for new workflows |

### JSON

| Activity | Description |
|----------|-------------|
| [Deserialize JSON](activities/DeserializeJson.md) | Deserialize a JSON string to a .NET object (`JObject` by default, or a custom type via generic parameter) |
| [Deserialize JSON Array](activities/DeserializeJsonArray.md) | Deserialize a JSON array string to a `JArray` object |
| [Serialize JSON](activities/SerializeJson.md) | Serialize a .NET object to a JSON string with optional custom settings |

### XML

| Activity | Description |
|----------|-------------|
| [Deserialize XML](activities/DeserializeXml.md) | Parse an XML string into an `XDocument` object |
| [Execute XPath](activities/ExecuteXPath.md) | Evaluate an XPath expression against an XML document or string |
| [Get XML Nodes](activities/GetXMLNodes.md) | Extract all XML nodes from a document or string |
| [Get XML Node Attributes](activities/GetXMLNodeAttributes.md) | Get the attributes of an XML node |
