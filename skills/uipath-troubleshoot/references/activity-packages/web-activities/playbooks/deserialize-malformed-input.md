---
confidence: high
signatures:
  - kind: exception
    value: "Newtonsoft.Json.JsonReaderException"
    note: "raised by DeserializeJson / DeserializeJsonArray — input string is not valid JSON (most often an upstream HTTP call returned an HTML/error body)"
  - kind: exception
    value: "System.Xml.XmlException"
    note: "raised by DeserializeXml (XDocument.Parse) — input string is not valid XML"
  - kind: message
    value: "Unexpected character encountered while parsing value"
  - kind: message
    value: "Unexpected end of content while loading JArray"
  - kind: message
    value: "Data at the root level is invalid"
---

# Deserialize — Malformed JSON / XML Input

## Context

What this looks like:
- A deserialize activity faults parsing its input string:
  - `DeserializeJson` (`DeserializeJson<T>`, `JsonConvert.DeserializeObject`) or `DeserializeJsonArray` (`JArray.Parse`) → `Newtonsoft.Json.JsonReaderException`, e.g. `Unexpected character encountered while parsing value: <. Path '', line 0, position 0.` or `Unexpected end of content while loading JArray. Path '', line 1, position N.`
  - `DeserializeXml` (`XDocument.Parse`) → `System.Xml.XmlException`, e.g. `Data at the root level is invalid. Line 1, position 1.`
- The message carries a `line`/`position` (and for JSON a `Path`) pointing at where parsing broke. The exception is raised by the parser and propagates raw.

What can cause it:
- **Input is not valid JSON/XML** — the string is HTML, plain text, an error page, a truncated/partial payload, or has a leading BOM / wrong encoding.
- **Upstream HTTP activity returned a non-payload body** — the single most common cause: an `HttpClient` / `NetHttpRequest` whose `Result` / body is wired into this activity returned an HTML error page (`<!DOCTYPE html>...` → the classic `Unexpected character ... <`), an empty body, or a non-JSON error envelope. The deserialize fault is a **symptom** of the HTTP call, not the parser.
- **Wrong deserializer for the data** — XML fed to a JSON activity (or vice versa), or a single JSON object fed to `DeserializeJsonArray` (which requires array `[...]` syntax).

What to look for:
- **The first offending character / `line`/`position`** — `<` at position 0 almost always means HTML where JSON was expected (an upstream error page).
- **The source of the input string** — literal, variable, or the output of an upstream `HttpClient` / `NetHttpRequest`. Decisive: if it's an HTTP output, investigate that call.
- **The upstream HTTP `StatusCode`** — a non-2xx status that the workflow ignored (e.g. `ContinueOnError = True`) explains a non-payload body.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `JsonReaderException` (Deserialize JSON / JSON Array) or `XmlException` (Deserialize XML); `JobError.ActivityName` names the activity.
2. **Trace the input string to its source** in the workflow. Is `JsonString` / `XMLString` a literal, a variable, or an upstream HTTP activity's `Result` / body?
3. **If the input is an HTTP output:** inspect that HTTP activity's `StatusCode` and body (job logs / trace spans). A non-2xx status or an HTML/empty body means the HTTP call is the real fault — pivot to the HTTP playbooks ([http-request-connection-failure.md](./http-request-connection-failure.md), [net-http-request-aggregate-failure.md](./net-http-request-aggregate-failure.md)).
4. **If the input is a literal/variable:** validate it against the expected format; the `line`/`position` in the message localizes the defect (wrong format, truncation, encoding/BOM, or object-vs-array mismatch).

## Resolution

- **Upstream HTTP returned a non-payload body (most common):** fix the HTTP call so it returns the expected payload — check the endpoint/status, and do not deserialize a response without first confirming a success status. Guard the deserialize with a `StatusCode` check (and inspect the body on non-2xx).
- **Malformed/partial/wrong-encoding payload:** correct the data at its source so it is well-formed JSON/XML; strip a leading BOM or fix the encoding if that is what the `line 0/1, position 0/1` indicates.
- **Wrong deserializer:** use the activity that matches the data — `DeserializeXml` for XML, `DeserializeJson` for a JSON object, `DeserializeJsonArray` only for a JSON array (`[...]`).
