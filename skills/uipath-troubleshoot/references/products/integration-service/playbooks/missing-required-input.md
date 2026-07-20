---
confidence: high
---

# Missing Required Input (DAP-RT-1003 / DAP-RT-1007)

> **Fault bucket: 👤 A — Customer-resolvable.** A required input value the activity needs was not supplied. The customer fixes it by providing the value. Lead with: "This is an input/configuration issue on your side — provide the missing field." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — IS rejected the call before reaching the provider because a required input was empty:

| Code | Name | Specific cause |
|---|---|---|
| `DAP-RT-1003` | ArgumentIsRequired | A required input argument is missing |
| `DAP-RT-1007` | PropertyIsRequired | A required property is empty |

What can cause it:
- A required activity input was left unbound or bound to an empty/null variable
- An upstream step produced no value, leaving the required input empty at runtime
- The activity was published with a required field unset

What to look for:
- No `ProviderErrorCode` / provider status — the failure is input validation, before any provider call
- `ErrorMessage` naming the specific argument/property that is required
- Whether the input is bound to an expression that can resolve to empty/null

## Investigation

1. **Read `ErrorMessage` from the customEvent** — it names the missing argument or property. That is the field to fix.
2. **Read the workflow source** — open the failing activity and check the named input: is it unbound, bound to an empty literal, or bound to a variable that can be null/empty at runtime?
3. **Trace the value upstream** — if the input is bound to a variable, confirm the step that sets it actually produces a value on every path.

## Resolution

- **Unbound / empty literal:** provide the required field value on the activity, then republish.
- **Bound to a variable that resolves empty:** fix the upstream step so the variable is always populated, or add a guard that supplies a default before the activity runs.
- After the fix, re-run to confirm the input-validation error clears.
