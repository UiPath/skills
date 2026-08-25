# Resolution — ParseList

## Root Cause

Job `1150d469-f4dc-44fc-b39e-c89aaa5db3f9` (process `ParseList`, entry point `Wf_ParseList.xaml`, folder Shared) faulted in **Deserialize JSON Array (DeserializeJsonArray)** with:

```
Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: n. Path '', line 0, position 0.
```

The DeserializeJsonArray activity's JsonString is a hardcoded non-array, non-JSON literal ("not a json array"); JArray.Parse rejects the first character. No upstream HttpClient/NetHttpRequest in the workflow.

Matches `activity-packages/web-activities/playbooks/deserialize-malformed-input.md`.

## Fix

Ensure the input is a valid JSON array ([...]). If it comes from an HTTP response, verify a 2xx status and JSON content before parsing.

## Must NOT attribute

Do not attribute this to: an HTTP connection failure/timeout/DNS/SSL (no HTTP activity exists); a null/empty input (the input is a non-empty non-JSON string, not an ArgumentNullException/NullReferenceException); an invented endpoint.
