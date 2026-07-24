---
confidence: medium
---

# Key Not Found Exception

## Context

`System.Collections.Generic.KeyNotFoundException` in the user's workflow code. A `Dictionary` (or similar keyed collection) was indexed with a key it does not contain. In `Assign` activities this is the classic config lookup — `Config("SomeKey")` or `dict(key)` — where the key is absent.

**Scope:** only applies when the exception originates from the user's workflow logic — a dictionary the user's expression indexed. If the stack trace shows the fault deep inside an activity package namespace with no user code in the call chain, redirect to that package's troubleshooting.

What this looks like:
- Workflow faults with `System.Collections.Generic.KeyNotFoundException`
- Error message: "The given key 'X' was not present in the dictionary." — the missing key is named
- Frequently environment-specific: a config key present in dev is missing in the failing environment

What can cause it:
- A `Config` dictionary lookup whose key is missing for this environment (row absent from `Config.xlsx`, deleted asset, typo)
- Case mismatch — the default `Dictionary` is case-sensitive, so `"apikey"` ≠ `"ApiKey"`
- A key derived from input data that varies between runs
- A dictionary populated from an asset/queue/JSON that lacked the expected entry
- An `If` / `While` **Condition** that indexes a dictionary with an absent key (e.g., `If config["FeatureEnabled"] == "true"`) — the fault occurs while resolving the condition, before either branch runs

What to look for:
- The missing key name in the message — exact, case-sensitive
- The dictionary's source (config sheet, asset, JSON, prior activity output)
- Why the key is absent there (typo, case, environment difference, missing source row)

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code (typically an `Assign` with a dictionary indexer) and read the expression
3. Extract the missing key name from the message; match it to the indexer expression
4. Trace how the dictionary is populated (Read Range of `Config.xlsx`, `Deserialize JSON`, asset read) and check whether that source contains the key — watch for typos and case differences
5. If environment-specific: compare the populating source between the environment where it works and the failing one

The root cause is WHY the key was absent (missing config row, typo, case mismatch, environment gap), not merely which lookup threw.

## Resolution

- **If lookup may miss:** use `TryGetValue(key, out value)` or guard with `If dict.ContainsKey(key)`, and provide a default
- **If missing config/asset entry:** add the key to the source (`Config.xlsx` row, Orchestrator asset) for the failing environment; fix typos and case
- **If case mismatch is expected:** build the dictionary with `StringComparer.OrdinalIgnoreCase` so lookups are case-insensitive
- **If the key is genuinely required:** fail fast with a clear `BusinessException` that names the missing key, instead of a raw `KeyNotFoundException`
