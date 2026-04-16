# Creation · AOps · AI Trust Layer

Follow [../_shared.md](../_shared.md). This file only lists AITL-specific CLI quirks and error patterns.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `AITrustLayer` (exact case) |
| Default license | `NoLicense` |

## CLI value quirks (will cause 400 if wrong)

| Property | Expected type/values |
|---|---|
| `allow-llm-model-auto-routing` | String `"yes"` or `"no"` (NOT boolean) |
| `traces-ttl`, `traces-ttl-effective` | Duration string `"90d"`, `"30d"`, etc. (NOT seconds) |
| `pii-processing-mode` | Enum: `"DetectionAndMasking"` \| `"DetectionOnly"` \| `"Disabled"` |
| `pii-execution-stage` (and other `*-execution-stage`) | Enum: `"Both"` \| `"InFlight"` \| `"AtRest"` \| `"Disabled"` |
| `container.*`, `harmful-content-container.*`, `prompt-injection-container.*`, `ip-protection-container.*` | Nested booleans — preserve nesting when writing subset |
| `allowed-llm-regions.*` | Nested booleans, keys like `united-states`, `europe`, `japan` |

## Error triage

| Error message fragment | Likely cause | Action |
|---|---|---|
| `container.pii-in-flight-foo` unknown | Template drift — pack declares a leaf the current template no longer has | Halt. Tell user to bump pack version. |
| `allow-llm-model-auto-routing` type mismatch | Passed as boolean | Halt. Bug in pack or upstream synthesis. |
| `traces-ttl` format | Passed as number | Halt. Same — pack/synthesis bug. |
