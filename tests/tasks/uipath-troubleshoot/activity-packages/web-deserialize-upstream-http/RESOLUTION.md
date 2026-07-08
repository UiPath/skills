# Resolution — ParseDocument: upstream HTTP returned a non-payload (error page) body

## Root Cause

Job `9937b232-5a94-44ab-8aee-ce6ea52d3bb4` (process `ParseDocument`, entry point `Wf_ParseDocument.xaml`, folder Shared) faulted in **Deserialize JSON (DeserializeJson)** with:

```
Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: <. Path '', line 0, position 0.
```

The `DeserializeJson` input is **not a literal** — it is wired from the `Result` of an upstream `HttpClient` GET (`https://api.internal.example/v1/orders`). The leading `<` at position 0 means the endpoint returned an **HTML/markup body — an error page (5xx / gateway / auth page), not JSON**. The workflow captured the HTTP `StatusCode` into a variable but **never checked it** before deserializing, so a non-2xx / HTML response flowed straight into the parser and faulted. The Deserialize error is a **symptom**; the real fault is the upstream HTTP call returning a non-payload body.

## What the evidence shows

- **Exception + activity:** `Newtonsoft.Json.JsonReaderException`, leading char `<` at `line 0, position 0`, in `DeserializeJson` — the canonical "HTML where JSON was expected" signature.
- **Input source (decisive):** `Wf_ParseDocument.xaml` wires `DeserializeJson.JsonString = [responseBody]`, and `responseBody` is the `Result` of the `HTTP Request` (`HttpClient` GET). The input is an **HTTP output, not a hardcoded literal** → this is the **upstream-HTTP branch**, not the literal-input branch.
- **No status guard:** the `HttpClient` writes `StatusCode` into a variable that is never inspected; the workflow deserializes unconditionally, so a non-2xx / HTML body reaches the parser.
- Matches the **"Upstream HTTP returned a non-payload body"** branch of `activity-packages/web-activities/playbooks/deserialize-malformed-input.md` — pivot to the HTTP call.

## Fix

1. **Guard the deserialize on the HTTP outcome:** only `DeserializeJson` when the `HttpClient` `StatusCode` is 2xx (and the content type is JSON). On a non-2xx / HTML body, branch to error handling — do not parse.
2. **Investigate the endpoint:** the `<` body is an HTML error page, so the endpoint returned a 5xx / gateway / auth error. Check the endpoint health, URL, and authentication; treat the HTTP call as the real fault (see the HTTP-request playbooks).
3. Do **not** "fix the input string" — it is not a literal; it is whatever the endpoint returns at runtime.

## Must NOT attribute

- Do **not** attribute this to a malformed hardcoded literal — the `JsonString` is the `HttpClient` Result, not a literal; editing a literal would not help.
- Do **not** attribute it to a wrong deserializer (object-vs-array) — the payload is HTML, not a valid JSON object/array.
- Do **not** attribute it to a null/empty input (`ArgumentNullException`) — the body is a non-empty HTML string.
- Do **not** attribute it to an HTTP connection failure / timeout / DNS / SSL — the `HttpClient` **did** connect and returned a response (an HTML error page); transport succeeded, the payload was wrong.
