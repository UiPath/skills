# UiPath Web Activities

`UiPath.WebAPI.Activities`

Activities for making HTTP/REST requests and working with JSON and XML data. Includes modern HTTP Request with retry policies, authentication, and proxy support, plus JSON/XML serialization and parsing utilities.

## Identity & References (read this first)

> **The NuGet package name is _not_ the assembly name or the namespace.** This is the single most common source of compile/load errors. Do not write `assembly=UiPath.WebAPI.Activities` or `using UiPath.WebAPI.Activities` — neither exists.

| Concept | Correct value | Used in |
|---------|---------------|---------|
| NuGet **package** | `UiPath.WebAPI.Activities` | `project.json` dependency, `uip rpa install-or-update-packages` |
| **Assembly** (activities) | `UiPath.Web.Activities` | XAML `xmlns` `assembly=` segment |
| **Assembly** (coded interfaces/extensions) | `UiPath.Web.Activities.API` | coded workflow references |

Note `Web.Activities` (assembly/namespace) vs `WebAPI.Activities` (package) differ by only the two letters `AP`. Always reference the **assembly/namespace** form (`UiPath.Web.Activities`) in code; only `project.json` uses the **package** form.

`project.json` dependency (package form):

```json
"dependencies": { "UiPath.WebAPI.Activities": "[2.5.0,)" }
```

> To install or update the dependency from the CLI, use `uip rpa install-or-update-packages` (pass the package id and version). If a command name ever differs in your CLI build, confirm the exact subcommand with `uip rpa --help`.

### XAML workflows — copy these `xmlns` declarations

```xml
xmlns:uwah="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
xmlns:uwahm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"
xmlns:json="clr-namespace:UiPath.Web.Activities.JSON;assembly=UiPath.Web.Activities"
xmlns:jn="clr-namespace:Newtonsoft.Json.Linq;assembly=Newtonsoft.Json"
```

| Activity | Class | `xmlns` prefix to use |
|----------|-------|------------------------|
| HTTP Request | `UiPath.Web.Activities.Http.NetHttpRequest` | `uwah:` |
| HTTP Request (legacy) | `UiPath.Web.Activities.HttpClient` | `web:` |
| Deserialize JSON | `UiPath.Web.Activities.DeserializeJson` | `web:` |
| Deserialize JSON Array | `UiPath.Web.Activities.DeserializeJsonArray` | `web:` |
| Serialize JSON | `UiPath.Web.Activities.JSON.SerializeJson` | `json:` |
| Deserialize XML | `UiPath.Web.Activities.DeserializeXml` | `web:` |
| Execute XPath | `UiPath.Web.Activities.ExecuteXPath` | `web:` |
| Get XML Nodes | `UiPath.Web.Activities.GetNodes` | `web:` |
| Get XML Node Attributes | `UiPath.Web.Activities.GetXMLNodeAttributes` | `web:` |

### Model & result types (variable types, multipart parts)

These are the types **returned or consumed** by the activities — not the activities themselves. They live in a **different namespace** from the activities (`...Http.Models`, not `...Http`), which is the most common cause of the "unknown type `HttpResponseSummary`" validation error and the Studio `BC30002: type FormDataPart is not defined` error. In XAML they use the `uwahm:` prefix:

```xml
xmlns:uwahm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
```

| Type | Used as | Namespace | XAML prefix |
|------|---------|-----------|-------------|
| `HttpResponseSummary` | `NetHttpRequest.Result` variable type | `UiPath.Web.Activities.Http.Models` | `uwahm:` |
| `FormDataPart`, `TextFormDataPart`, `FileFormDataPart`, `BinaryFormDataPart` | items of `FormDataParts` (multipart upload) | `UiPath.Web.Activities.Http.Models` | `uwahm:` |
| `HttpMethod`, `AuthenticationType`, `HttpRequestBodyType`, `RetryPolicyType` (enums; the matching activity properties are `Method`, `AuthenticationType`, `RequestBodyType`, `RetryPolicyType`) | activity property values | `UiPath.Web.Activities.Http.Models` | set as bare strings in XAML (e.g. `Method="POST"`) — no prefix needed |
| `HttpRequestOptions`, `RetryPolicyOptions`, `AuthenticationOptions`, `ClientOptions`, `ResponseOptions` | coded `http.SendRequestAsync` config | `UiPath.Web.Activities.API.Models` | coded only (not used in XAML) |
| `HttpResponseSummaryExtensions` | coded response helpers (`IsSuccessStatusCode()`, …) | `UiPath.Web.Activities.API` | coded only |

All of these are in assembly `UiPath.Web.Activities` **except** the `...API` / `...API.Models` namespaces, which are in assembly `UiPath.Web.Activities.API`.

### Coded workflows — copy these `using` directives

```csharp
using UiPath.CodedWorkflows;              // CodedWorkflow base class, [Workflow]
using UiPath.Web.Activities.API;          // http/soap/curl accessors + HttpResponseSummaryExtensions
using UiPath.Web.Activities.API.Models;   // HttpRequestOptions, RetryPolicyOptions, AuthenticationOptions
using UiPath.Web.Activities.Http.Models;  // HttpResponseSummary, FormDataPart, HttpMethod
using Newtonsoft.Json;                    // JsonConvert
using Newtonsoft.Json.Linq;               // JObject, JArray
```

The `http` (`IHttpService`), `soap` (`ISoapService`), and `curl` (`ICurlImportService`) accessors are **inherited members of `CodedWorkflow`** — call them directly (e.g. `http.GetAsync(...)`). Do **not** resolve them with `GetRequiredService<IHttpService>()`, and do **not** use `System.Net.Http.HttpClient`. See [coded/coded-api.md](coded/coded-api.md) for the full skeleton and anti-patterns.

## Expression language (XAML): VB vs C#

UiPath XAML projects use one of two expression languages, and **how you bind a value to an activity property depends on which one**. Getting this wrong fails validation even when the activity, namespace, and types are all correct.

**How to tell which a project uses:** look at the root `<Activity>` element. A C# project carries `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"`. If that attribute is absent or set to `VB`, it is a VB project.

| Binding | VB project | C# project |
|---------|-----------|-----------|
| **Literal scalar** (URL, method, content-type) | plain attribute: `RequestUrl="https://api.example.com/data"` | identical — a plain attribute works in both |
| **In-argument expression** (variable, concatenation, `new Dictionary<…>`) | attribute bracket shorthand: `JsonString="[httpResponse.TextContent]"` | child element with `CSharpValue` (see below) |
| **Out-argument** (bind a result into a variable) | attribute bracket shorthand: `Result="[httpResponse]"` | child element with `CSharpReference` (see below) |

The bracket shorthand `[ … ]` is **VB-only**. Putting it in a C# project (e.g. `Result="[httpResponse]"` or `RequestUrl="[&quot;https://…&quot;]"`) causes a validation/type-binding error — the brackets and embedded quotes are taken literally.

### C# expression form (child elements)

In-argument expression:

```xml
<uwah:NetHttpRequest.RequestUrl>
  <InArgument x:TypeArguments="x:String">
    <CSharpValue x:TypeArguments="x:String">"https://jsonplaceholder.typicode.com/todos/1"</CSharpValue>
  </InArgument>
</uwah:NetHttpRequest.RequestUrl>
```

Out-argument (bind into a variable):

```xml
<uwah:NetHttpRequest.Result>
  <OutArgument x:TypeArguments="uwahm:HttpResponseSummary">
    <CSharpReference x:TypeArguments="uwahm:HttpResponseSummary">httpResponse</CSharpReference>
  </OutArgument>
</uwah:NetHttpRequest.Result>
```

The `x:TypeArguments` on `CSharpValue`/`CSharpReference` must match the property's argument type (`x:String` for `RequestUrl`, `uwahm:HttpResponseSummary` for `Result`, etc.). For a **literal scalar** you can skip the child element entirely and use a plain attribute (`RequestUrl="https://…"`), which is valid in both project types.

> **`CSharpValue` / `CSharpReference` need no extra `xmlns`.** They are part of the default activities namespace (`xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"`), so the unqualified form above is what Studio emits and loads. If you ever see them written with a prefix (`mca:CSharpValue`), that prefix maps `clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities` — functionally identical; do **not** use `assembly=UiPath.Workflow`, which is the DLL file name, not the XAML assembly identity.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API](coded/coded-api.md) — `IHttpService`/`ISoapService`/`ICurlImportService` reference and skeleton

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
