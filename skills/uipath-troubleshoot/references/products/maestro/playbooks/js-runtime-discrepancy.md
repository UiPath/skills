---
confidence: high
---

# JS Runtime Discrepancy

## Context

What this looks like:
- JavaScript expression passes in JS Editor but fails at runtime
- "btoa is not defined" or other runtime JS errors
- Browser-specific APIs (TextEncoder, atob, btoa) fail at runtime

What can cause it:
- The design-time JS Editor runs in the browser (supports btoa, TextEncoder, etc.) but runtime uses Jint (.NET JS interpreter) which lacks browser-specific APIs

## Investigation

1. Identify which JS API the expression uses
2. Check if that API is a browser-specific API not supported by Jint

## Resolution

- Use Jint-compatible alternatives. For base64 encoding use: `new Uint8Array(Array.from("test", c => c.charCodeAt(0))).toBase64()`
- Reference the Jint GitHub repo for supported features
- Validate the expression works in both the JS Editor and at runtime
