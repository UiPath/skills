---
confidence: high
---

# Deserialize XML — Malformed XML Input

## Context

What this looks like:
- `DeserializeXml` (`XDocument.Parse`) faults with `System.Xml.XmlException`. Message selects branch:
  - `'soapenv' is an undeclared prefix. Line 1, position 2.` — any `'<prefix>' is an undeclared prefix` (`soap`, `s`, `ns0`, …)
  - `Root element is missing.` — no line/position
  - `The 'hr' start tag on line 5 position 2 does not match the end tag of 'body'.` — any `start tag ... does not match the end tag of`
  - `'en' is an unexpected token. The expected token is '"' or '''.`
  - `'alt' is a duplicate attribute name.`
  - `Data at the root level is invalid. Line 1, position 1.`
  - `There is an unclosed literal string.`
- Stack top: `System.Xml.XmlTextReaderImpl.Throw` → `System.Xml.Linq.XDocument.Parse(String text, LoadOptions options)`. Parser exception propagates raw; no package wrapper.
- NOT for null input (`System.ArgumentNullException: Value cannot be null. (Parameter 's')`) → [deserialize-null-input.md](./deserialize-null-input.md).
- NOT for JSON (`Newtonsoft.Json.JsonReaderException` on `DeserializeJson` / `DeserializeJsonArray`) → [deserialize-malformed-input.md](./deserialize-malformed-input.md).
- NOT for `XmlException` from other activities (`BuildDataTable`, Excel `AppendRange` / `WriteCell`, Exchange `ServiceRequestException`) — different domain; route by faulted activity.

What can cause it:
- **A. Namespace prefix never declared** (`is an undeclared prefix`, typically `Line 1, position 2`) — input is a fragment of a SOAP/namespaced document: `<soapenv:Body>` or an inner element cut out by `Substring` / `Split` / regex, or XML built by string concatenation. The `xmlns:soapenv="..."` declaration lives on the `<soapenv:Envelope>` element that was not kept. Most frequent `DeserializeXml` fault.
- **B. Empty input** (`Root element is missing.`) — string is `""` or whitespace only. Upstream HTTP returned an empty body (`204`, or non-2xx with `ContinueOnError`), file read returned an empty file, or a variable was initialized to `""` and never filled. Distinct from null → [deserialize-null-input.md](./deserialize-null-input.md).
- **C. HTML page instead of XML** (`start tag ... does not match the end tag of`, `is an unexpected token. The expected token is '"' or '''`, `is a duplicate attribute name`) — HTML parses as XML until it breaks an XML rule: void tags (`<hr>`, `<br>`, `<img>`) never closed, unquoted attributes (`<html lang=en>`), duplicate attributes. `'hr' ... 'body'` at line 5–6 = default nginx error page (`<center><h1>404 Not Found</h1></center><hr><center>nginx</center>`). Upstream HTTP call failed; the parser fault is a symptom.
- **D. Not XML at all** (`Data at the root level is invalid. Line 1, position 1.`) — plain text, JSON, an error string, or a leading BOM / non-XML byte before `<`. Also an HTML page that starts with text before the first tag.
- **E. Truncated / hand-built XML** (`There is an unclosed literal string.`, `Unexpected end of file`) — payload cut off (size limit, partial read, timeout) or attribute quote never closed in a concatenated string.

What to look for:
- **Message text** → branch A–E above.
- **`Line`/`position`** — `Line 1, position 2` on a prefix error = first element is the undeclared one (fragment). Line 5–6 tag mismatch = nginx error page.
- **Source of `XMLString`** — literal, variable, file read, or upstream `HttpClient` / `NetHttpRequest` `Result` / body. Decisive for B, C, D.
- **String manipulation between source and parse** — `Substring`, `Split`, `Regex`, `Replace`, `String.Format` / `+` concatenation on the XML. Decisive for A and E.

## Investigation

1. **Confirm signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.Xml.XmlException` and `XDocument.Parse` frame; `JobError.ActivityName` / workflow stack names `DeserializeXml`. Read verbatim message → branch.
2. **Open faulted workflow, trace `XMLString` to its source** (literal, variable assignment, file read, HTTP output). Record every transform applied in between.
3. **Branch A (undeclared prefix):** find where the string was cut from a larger document or concatenated. Confirm the root element of the parsed string uses a prefix with no matching `xmlns:<prefix>` attribute.
4. **Branch B / C / D (empty, HTML, not XML):** if input is an HTTP output, check that activity's `StatusCode` and body — `uip traces spans get --job-key <job-key> --output json` or job logs. Non-2xx, empty body, or `text/html` body = HTTP call is the real fault → pivot to [http-request-connection-failure.md](./http-request-connection-failure.md), [net-http-request-aggregate-failure.md](./net-http-request-aggregate-failure.md), [http-request-proxy-blocked.md](./http-request-proxy-blocked.md). If input is a file, check file exists, is non-empty, and holds XML.
5. **Branch E (truncated):** compare input length against expected payload; check the producing step for size limits, partial reads, or unbalanced quotes in concatenation.

## Resolution

- **A. Undeclared prefix:** parse the complete document (full `<soapenv:Envelope>`), then select the needed element with LINQ to XML and an `XNamespace` (`xDoc.Descendants(XNamespace.Get("http://schemas.xmlsoap.org/soap/envelope/") + "Body")`). Do not cut XML with `Substring` / `Split` / regex. If a fragment is unavoidable, re-add the declaration on its root (`xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"`, or the namespace URI the source envelope declares). Build XML with `XElement` / `XDocument`, not string concatenation.
- **B. Empty input:** fix the producer so it returns a payload; guard the parse with `!String.IsNullOrWhiteSpace(<XML_STRING>)` (C#) / `Not String.IsNullOrWhiteSpace(<XML_STRING>)` (VB) and handle the empty case explicitly. For HTTP, check `StatusCode` is 2xx and body non-empty before deserializing.
- **C. HTML page:** fix the upstream HTTP call (endpoint, auth, gateway/proxy, server outage — the page title names the status, e.g. `404 Not Found`, `502 Bad Gateway`). Check `StatusCode` and response `Content-Type` before parsing; log the body on non-2xx instead of deserializing it.
- **D. Not XML:** correct the data at its source; strip a leading BOM / whitespace (C#: `<XML_STRING>.Trim().TrimStart('\uFEFF')`; VB: `<XML_STRING>.Trim().TrimStart(ChrW(&HFEFF))`); use `DeserializeJson` if the data is JSON.
- **E. Truncated / hand-built:** fix the producer (raise size/timeout limits, read the whole stream); replace string concatenation with `XElement` construction so quoting and escaping are generated.
