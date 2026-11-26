# Resolution — OrderStatusSync

## Root Cause

Job `4fa9cfe0-3a24-4502-a498-cf8672b1f3d8` (process `OrderStatusSync`, entry point `Main.xaml`) faulted in **Deserialize XML (DeserializeXml)** "Deserialize order status" with:

```
System.Xml.XmlException: Root element is missing.
```

The upstream HTTP Request "Get order status" (`NetHttpRequest`, GET `https://httpbin.org/status/204`, `ContinueOnError = True`) returned `204 No Content` — a success status with an empty body (job log: `Order status HTTP 204, body length 0`). The workflow passes `response.TextContent` (an empty string, not null) straight into Deserialize XML with no status/body check, and `XDocument.Parse("")` throws `Root element is missing.` The parser fault is a symptom of the empty HTTP response.

Matches `activity-packages/web-activities/playbooks/deserialize-xml-malformed.md` (branch B — empty input).

## Fix

Point "Get order status" at an endpoint that returns the order-status XML, and guard the parse: only run Deserialize XML when the status is 2xx and `!String.IsNullOrWhiteSpace(response.TextContent)`; otherwise log/throw a clear business error with the status code.

## Must NOT attribute

Do not attribute this to: malformed / non-XML / HTML / truncated input (the body was empty, 0 chars); a null input (`ArgumentNullException`); an HTTP connection failure, timeout, DNS, SSL or proxy problem (the request completed with 204); a JSON deserializer error; a namespace/prefix problem.
