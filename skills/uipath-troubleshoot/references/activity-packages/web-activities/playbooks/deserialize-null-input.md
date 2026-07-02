---
confidence: high
signatures:
  - kind: exception
    value: "System.ArgumentNullException"
    note: "on DeserializeJson — input guard for null/empty JsonString; parameter name 'JSON string'"
  - kind: message
    value: "Value cannot be null. (Parameter 'JSON string')"
  - kind: exception
    value: "System.NullReferenceException"
    note: "on DeserializeJsonArray — no null-input guard, a null JsonString hits JArray.Parse directly"
---

# Deserialize — Null / Empty Input

## Context

What this looks like:
- A deserialize activity faults because its input string is null or empty. The exception type depends on the activity:
  - **`DeserializeJson`** (`DeserializeJson<T>`) guards the input and throws `System.ArgumentNullException` with the parameter name `JSON string` — message `Value cannot be null. (Parameter 'JSON string')` (on .NET Framework: `... Parameter name: JSON string`). The guard fires on null **or** empty input.
  - **`DeserializeJsonArray`** has **no guard** (it calls `JArray.Parse` directly), so the same null input surfaces as `System.NullReferenceException: Object reference not set to an instance of an object.`
- The `JSON string` parameter name and the `DeserializeJson` vs `DeserializeJsonArray` activity identity together confirm this branch (vs a malformed-payload `JsonReaderException`, where a non-null but invalid string parsed and failed).

What can cause it:
- **Unassigned / null input variable** — the `JsonString` argument is wired to a variable that is `Nothing` (never assigned, or assigned only on a path not taken) at runtime.
- **Empty input** (`DeserializeJson` only) — the variable is `""`; the guard treats empty the same as null.
- **Null upstream value** — the input came from a prior activity that returned nothing: an HTTP call whose body was empty / never set, an asset/config read that returned null, or a no-match lookup.

What to look for:
- **The parameter name `JSON string`** in an `ArgumentNullException` → confirms `DeserializeJson` received null/empty.
- **A bare `NullReferenceException` on `DeserializeJsonArray`** → same root cause (null input) without the friendly guard.
- **The source of `JsonString`** — which variable, and where it is assigned; the upstream activity that should have produced it.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info`. `ArgumentNullException (Parameter 'JSON string')` on `DeserializeJson`, or `NullReferenceException` on `DeserializeJsonArray`; `JobError.ActivityName` names the activity.
2. **Trace `JsonString` to its assignment** in the workflow source. Identify the variable and every place it is (or is not) set on the failing path.
3. **Check the upstream producer.** If the input comes from an HTTP activity or a lookup/asset read, confirm whether that step returned an empty/null value — that is the real fault to fix.

## Resolution

- **Null/unset variable:** ensure `JsonString` is assigned a non-null, non-empty value before the deserialize activity on every path that reaches it; add a guard/default if a branch can legitimately leave it unset.
- **Null from upstream:** fix the producing activity so it returns the expected payload (e.g., an HTTP call that returned an empty body — see [deserialize-malformed-input.md](./deserialize-malformed-input.md) and the HTTP playbooks), or handle the empty result explicitly before deserializing.
- **`DeserializeJsonArray` null-input hardening:** because `DeserializeJsonArray` does not guard null input (unlike `DeserializeJson`), validate the string is non-empty before the activity so the failure is an explicit check rather than a bare `NullReferenceException`.
