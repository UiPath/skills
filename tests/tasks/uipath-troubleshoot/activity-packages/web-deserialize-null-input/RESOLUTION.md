# Resolution — ReadConfig

## Root Cause

Job `1dc1992a-7f84-40bf-b61d-75b50f861170` (process `ReadConfig`, entry point `Wf_ReadConfig.xaml`, folder Shared) faulted in **Deserialize JSON (DeserializeJson)** with:

```
System.ArgumentNullException: Value cannot be null. (Parameter 'JSON string')
```

The DeserializeJson activity received a null/empty JsonString; the activity's guard throws ArgumentNullException with parameter name 'JSON string'. The input is empty, not malformed.

Matches `activity-packages/web-activities/playbooks/deserialize-null-input.md`.

## Fix

Ensure JsonString is assigned a non-null, non-empty value before the activity on every path; if it comes from an upstream step that can return nothing, guard/branch on empty before deserializing.

## Must NOT attribute

Do not attribute this to: a malformed-JSON parse error (JsonReaderException) -- this is an empty/null input (ArgumentNullException), the parser never saw a character; an HTTP failure; an invented endpoint.
