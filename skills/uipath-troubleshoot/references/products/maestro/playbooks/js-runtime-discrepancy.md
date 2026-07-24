---
confidence: high
---

# JS Runtime Discrepancy

## Context

What this looks like:
- JavaScript expression passes in JS Editor but fails at runtime
- `ReferenceError: btoa is not defined`, `ReferenceError: atob is not defined`, `TextEncoder is not defined`, or another `<api> is not defined` runtime JS error naming a browser API
- Browser-specific APIs (TextEncoder, atob, btoa) fail at runtime

What can cause it:
- The design-time JS Editor runs in the browser (supports btoa, TextEncoder, etc.) but runtime uses Jint (.NET JS interpreter) which lacks browser-specific APIs

Not this playbook:
- `Property 'X' not found against object of type ExpressionDictionary` or engine code `400300`/`400301`/`400302` with no undefined-API mention → [expression-evaluation-errors](expression-evaluation-errors.md)
- `InvalidCastException: System.Object[] to ExpressionList` on a multi-instance marker (code `400008`) → [marker-invalid-cast](marker-invalid-cast.md)

Discriminator: message names a JS API as not defined AND the same expression passes in the JS Editor - that combination is this playbook.

## Investigation

1. Identify which JS API the expression uses
2. Check if that API is a browser-specific API not supported by Jint

## Resolution

- Use Jint-compatible alternatives. For base64 encoding use: `new Uint8Array(Array.from("test", c => c.charCodeAt(0))).toBase64()`
- Reference the Jint GitHub repo for supported features
- Validate the expression works in both the JS Editor and at runtime
