# Web Activities

Activities from the `UiPath.Web.Activities` package for HTTP calls and payload deserialization. Two families:

- **HTTP request** — `HttpClient` (legacy, RestSharp-based) and `NetHttpRequest` (modern, `System.Net.Http.HttpClient` + retry/connection pipeline). Issue an outbound HTTP request and return status, headers, and body.
- **Deserialize** — `DeserializeJson<T>` (Newtonsoft `JsonConvert.DeserializeObject`), `DeserializeJsonArray` (Newtonsoft `JArray.Parse`), `DeserializeXml` (`System.Xml.Linq.XDocument.Parse`). Parse a string into a typed object / `JArray` / `XDocument`.

## Exceptions propagate raw

Unlike connection-based packages (O365's `Office365Exception`, Integration Service's `GeneralException`), these activities do **NOT** wrap failures in a package-specific exception type. After tracking telemetry, the original `catch`/`rethrow` lets the raw .NET / Newtonsoft / RestSharp exception propagate to the job. So the **faulted activity class plus the exception class** — not a unique message string — is the primary discriminator. Two activities throwing `System.NullReferenceException` are different investigations.

## Key activity types

### HTTP request

- **HTTP Client** (`HttpClient`) — legacy REST activity. `EndPoint` is `[RequiredArgument]`. Default `TimeoutMS = 6000`. On a request-build error it rethrows unless `ContinueOnError = true` (then returns an empty response). A RestSharp timeout surfaces as an explicit `System.TimeoutException`; transport/HTTP errors surface as the raw `System.Net.WebException` unwrapped from the faulted task.
- **HTTP Request** (`NetHttpRequest`) — modern activity over `HttpClient.SendAsync` with a retry policy. Default `TimeoutInMiliseconds = 10000`, `ContinueOnError = true` (so it returns a response summary for HTTP error statuses rather than faulting). When it does fault, the async pipeline surfaces a `System.AggregateException` wrapping the real cause (`HttpRequestException`, `TaskCanceledException`, …).

### Deserialize

- **Deserialize JSON** (`DeserializeJson<T>`) — guards null/empty input with an explicit `ArgumentNullException`, then `JsonConvert.DeserializeObject<T>`. Malformed text → `JsonReaderException`; well-formed JSON whose shape does not fit `T` → `JsonSerializationException`.
- **Deserialize JSON Array** (`DeserializeJsonArray`) — `JArray.Parse`. **No null guard** (contrast with `DeserializeJson`): null/unset input → `NullReferenceException`; malformed or non-array text → `JsonReaderException`.
- **Deserialize XML** (`DeserializeXml`) — `XDocument.Parse`. Malformed XML → `System.Xml.XmlException`.

## Common failure patterns

- **HTTP call failed** — `HttpClient` throws `System.Net.WebException` (non-success status, DNS failure, connection refused, SSL/TLS). `NetHttpRequest` surfaces the same causes wrapped in `System.AggregateException`.
- **HTTP timeout** — `HttpClient` throws `System.TimeoutException` when the request exceeds `TimeoutMS`. `NetHttpRequest` timeouts arrive as `AggregateException` → inner `TaskCanceledException`.
- **HTTP null reference** — `HttpClient` throws `System.NullReferenceException` when a request input (endpoint, header, cookie, parameter) resolves to null and is dereferenced during request building.
- **Malformed payload** — `DeserializeJson` / `DeserializeJsonArray` throw `JsonReaderException`, `DeserializeXml` throws `XmlException`, when the input string is not valid JSON/XML. Frequently a **symptom of an upstream HTTP activity** that returned an HTML error page, an empty body, or a non-JSON error envelope.
- **Type mismatch** — `DeserializeJson` throws `JsonSerializationException` when well-formed JSON does not match the target type `T`.
- **Null/empty payload** — `DeserializeJson` throws `ArgumentNullException` (param `JSON string`); `DeserializeJsonArray` throws `NullReferenceException` for the same null input.

## Package

NuGet: `UiPath.Web.Activities`
