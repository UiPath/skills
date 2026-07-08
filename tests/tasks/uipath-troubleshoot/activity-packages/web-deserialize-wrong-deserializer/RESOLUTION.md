# Resolution — ParseList: wrong deserializer (JSON object fed to Deserialize JSON Array)

## Root Cause

Job `1150d469-f4dc-44fc-b39e-c89aaa5db3f9` (process `ParseList`, entry point `Wf_ParseList.xaml`, folder Shared) faulted in **Deserialize JSON Array (DeserializeJsonArray)** with:

```
Newtonsoft.Json.JsonReaderException: Error reading JArray from JsonReader. Current JsonReader item is not an array: StartObject. Path '', line 1, position 1.
```

The `JsonString` handed to `DeserializeJsonArray` is **valid JSON, but a JSON object (`{...}`), not a JSON array (`[...]`)**. `DeserializeJsonArray` calls `JArray.Parse`, which requires the top-level token to be an array; given an object it rejects it at the very first token (`StartObject`). This is a **wrong-deserializer** fault — the payload parses fine, it is simply the wrong container shape for this activity.

## What the evidence shows

- **Exception class + activity:** `Newtonsoft.Json.JsonReaderException` — *"…not an array: StartObject"* — raised by `DeserializeJsonArray` "Deserialize JSON Array" inside the `Parse List` sequence (from `jobs get … Info` and `jobs logs --level Error`). This is the verbatim signature of the **wrong-deserializer** branch of `activity-packages/web-activities/playbooks/deserialize-malformed-input.md`.
- **What the message says (decisive):** *"not an array: **StartObject**"* at `line 1, position 1` — the parser read a well-formed `{`, i.e. a JSON **object**, and refused only because `JArray` requires `[`. There is **no** *"Unexpected character"* — the input is not garbage.
- **Input wiring:** `Wf_ParseList.xaml` is a single-activity Sequence whose only activity is `DeserializeJsonArray` with a **hardcoded valid JSON object literal** `{"orderId":1044,"customer":"Contoso Ltd","status":"open"}`. There is **no `HttpClient` / `NetHttpRequest`** anywhere in the workflow.
- **Stack:** `JArray.Load → JArray.Parse → UiPath.Web.Activities.DeserializeJsonArray.Execute` — the fault is the array loader rejecting a non-array token, not a text-parse failure.

## Correct conclusion

`DeserializeJsonArray` was used to parse a JSON **object**. `JArray.Parse` only accepts arrays (`[...]`); a `{...}` object is valid JSON but the wrong container type, so the activity throws *"not an array: StartObject"*. The activity does not match the data shape — this is deserializer selection, not content validity.

## Fix

1. Parse a JSON **object** with **Deserialize JSON** (`DeserializeJson` → `JObject`), not Deserialize JSON Array.
2. If a JSON **array** was actually expected here, fix the upstream producer so it emits an array (`[ { … } ]`) and keep Deserialize JSON Array.
3. Rule of thumb — choose the deserializer by data shape: `DeserializeJson` for a JSON object, `DeserializeJsonArray` only for a JSON array (`[...]`), `DeserializeXml` for XML.

## Must NOT attribute

- Do **not** attribute this to malformed / non-JSON / garbage input — the input is **valid JSON**; the parser reached `StartObject`, it did not hit an *"Unexpected character."*
- Do **not** attribute it to a null/empty input (`ArgumentNullException`).
- Do **not** attribute it to an HTTP connection failure, timeout, DNS, or SSL problem — there is no HTTP activity in the workflow.
- Do **not** invent an endpoint, connection, or upstream activity that the source does not contain.
