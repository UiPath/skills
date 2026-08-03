# Resolution — ParseResponse: Deserialize JSON malformed input

## Root Cause

The `ParseResponse` job (entry point `Wf_ParseResponse.xaml`, folder Shared, job `febd892d-787b-4008-a573-4af66cf710cf`) faulted in a **Deserialize JSON** activity with:

```
Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: <. Path '', line 0, position 0.
```

The input string handed to `DeserializeJson` is **not valid JSON** — it begins with `<`, the hallmark of an HTML/XML body fed into a JSON parser. The `.NET` stack confirms the activity is `UiPath.Web.Activities.DeserializeJson` 1 calling `JsonConvert.DeserializeObject`.

## What the evidence shows

- **Exception class + activity:** `Newtonsoft.Json.JsonReaderException` raised by `DeserializeJson` "Deserialize JSON" inside the `Parse Response` sequence (from `jobs get … Info` and `jobs logs --level Error`). This is the verbatim signature of `activity-packages/web-activities/playbooks/deserialize-malformed-input.md`.
- **Leading character:** the message says `parsing value: <` at `line 0, position 0` — the input's first character is `<`, i.e. an HTML/markup document, not JSON.
- **Input wiring (decisive):** `Wf_ParseResponse.xaml` is a single-activity Sequence whose only activity is `DeserializeJson<JObject>` with a **hardcoded string literal** `JsonString = "<html><body>503 Service Unavailable</body></html>"`. There is **no `HttpClient` or `NetHttpRequest`** anywhere in the workflow.
- This resolves the playbook to its **literal-input branch**, not the upstream-HTTP-output branch. No HTTP activity to pivot to.

## Correct conclusion

The Deserialize JSON activity is being given a non-JSON, HTML-shaped string (`<html>…503 Service Unavailable…</html>`). In production this exact failure almost always means an **upstream HTTP call returned an error page / non-2xx / empty body** that was passed into the parser without a success check — here it is reproduced directly as a literal.

## Fix

1. Ensure the string passed to `Deserialize JSON` is the **JSON payload**, not an HTML error page. If it comes from an HTTP activity, check that activity's `StatusCode` is 2xx and inspect the body before deserializing.
2. Guard the deserialize: only parse when the response is a success and the content type is JSON; on a non-2xx/HTML body, branch to error handling instead of parsing.
3. If the input is genuinely static config, correct the literal to valid JSON.

## Must NOT attribute

- Do **not** attribute this to an HTTP connection failure, timeout, DNS, or SSL problem — there is no HTTP activity in the workflow.
- Do **not** attribute it to a null/empty input (`ArgumentNullException`) — the input is a non-empty, non-JSON string, so the parser reached and rejected the first character.
- Do **not** invent an endpoint, connection, or upstream activity that the source does not contain.
