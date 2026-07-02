---
confidence: medium
signatures:
  - kind: exception
    value: "Newtonsoft.Json.JsonSerializationException"
    note: "on DeserializeJson<T> — well-formed JSON whose shape does not fit the target type T"
  - kind: message
    value: "Cannot deserialize the current JSON object"
  - kind: message
    value: "Cannot deserialize the current JSON array"
  - kind: message
    value: "Error converting value"
  - kind: message
    value: "Could not cast or convert from System.String"
exclusions:
  - "JsonReaderException (input itself is not valid JSON) → deserialize-malformed-input.md"
---

# Deserialize JSON — Type Mismatch (JsonSerializationException)

## Context

What this looks like:
- A `UiPath.Web.Activities.DeserializeJson<T>` activity faults with `Newtonsoft.Json.JsonSerializationException`. The input is **well-formed JSON** (it parsed), but its shape does not fit the target type `T`. Typical messages:
  - `Cannot deserialize the current JSON object (e.g. {"name":"value"}) into type '<T>' because the type requires a JSON array (e.g. [1,2,3]) to deserialize correctly.`
  - `Cannot deserialize the current JSON array (e.g. [1,2,3]) into type '<T>' because the type requires a JSON object ...`
  - `Error converting value "<x>" to type '<member type>'. Path '<member>', line N, position M.`
  - `Could not cast or convert from System.String to <type>.`
- Contrast with `JsonReaderException` (the JSON itself is invalid) — see [deserialize-malformed-input.md](./deserialize-malformed-input.md). Here the JSON is valid; the **target type** is the mismatch.

What can cause it:
- **Object/array shape mismatch** — `T` expects an array but the JSON is an object (or vice versa).
- **Member type mismatch** — a field is a string where `T` expects a number/bool/date, or null where `T` expects a non-nullable value.
- **Schema drift** — the API response shape changed (renamed/removed/retyped fields) while `T` (often generated from a `JsonSample`) stayed on the old shape.
- **Wrong `T` chosen** — the `JsonObject` output type does not match the actual response contract.

What to look for:
- **The message's `Path` and member name** — pinpoints which field mismatched.
- **`T` vs the actual JSON** — compare the target type (and the `JsonSample` it may have been generated from) against a current sample of the real response.
- **Whether the response shape changed recently** — schema drift if earlier runs succeeded with the same `T`.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `JsonSerializationException` and `JobError.ActivityName` = the `DeserializeJson` activity. Confirm it is a serialization (type) error, not a `JsonReaderException` (malformed).
2. **Read `T` and `JsonSample` from source** — the declared output type and the sample it was modeled on.
3. **Get a current sample of the real input JSON** (the literal, the variable, or the upstream HTTP body) and compare it to `T` at the `Path` named in the message.
4. **Decide object-vs-array, member-type, or drift** from the comparison.

## Resolution

- **Object/array mismatch:** change `T` to match the JSON shape (e.g., `List<...>` for an array, a single type for an object), or select the correct deserialize activity.
- **Member type mismatch:** align the member type in `T` with the JSON (string vs number/bool/date; make it nullable if the field can be null), or fix the producer so the field's type is stable.
- **Schema drift:** regenerate `T` from a current `JsonSample` of the real response and update downstream usages.
- **Wrong `T`:** point `JsonObject` at the type that matches the actual response contract.
