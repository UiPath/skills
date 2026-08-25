---
confidence: high
---

# BYO LLM Call Failing — Underlying IS Connection Dead

## Context

What this looks like:
- Agent / product LLM call was previously working and now fails with auth-shaped errors (401, 403, "invalid credentials", "API key not valid")
- Errors reference the vendor (OpenAI / Azure OpenAI / Bedrock / Vertex / Anthropic) directly, not the UiPath platform
- A BYO LLM product configuration is registered for the failing product / feature
- The configuration's `enabled: true`

What can cause it:
- The Integration Service connection's OAuth token expired and refresh failed
- The connection owner revoked the app in the external service
- The vendor rotated or invalidated the API key
- The IS connection was disabled or deleted in the connections folder

What to look for:
- The BYO config has not been edited since the breakage began
- A time gap between last successful LLM call and first failure
- The IS connection referenced by `connectionId` is not in `Enabled` state when resolved live

## Investigation

1. **Identify the BYO configuration** for the failing (product, feature). If the user gave a trace ID, read `uip traces spans get <trace-id> --output json` first to confirm the model + provider the call was attempting (or attempted to fall back to).

   ```bash
   uip llm-configuration byo-connections list \
     --output json --output-filter "Data[?product=='<product>' && operationGroupName=='<feature>']"
   ```

2. **Re-resolve the underlying IS connection state.** `--force-refresh` bypasses cached connection details and re-queries Integration Service:

   ```bash
   uip llm-configuration byo-connections get <id> --force-refresh --output json
   ```

   Inspect the resolved fields: `connectionState`, `enabled` (on the connection, not the BYO record), and connector identity. Any value other than `Enabled` confirms the hypothesis.

3. **Optional cross-check — ping the IS connection directly.** If you have the `connectionId` from step 2, route to the [Integration Service connection-auth-expired playbook](../../integration-service/playbooks/connection-auth-expired.md) for the re-authentication path. The IS layer owns the OAuth recovery.

## Resolution

- Re-authenticate the IS connection: `uip is connections edit <connection-id>` (or via the Integration Service UI). See [Integration Service playbook](../../integration-service/playbooks/connection-auth-expired.md) for the full re-auth flow.
- Once the IS connection is back to `Enabled`, re-probe the BYO config by issuing an idempotent `update` — this forces a fresh server-side validation:

  ```bash
  uip llm-configuration byo-connections update <id> \
    --llm-name <same> --llm-identifier <same> \
    --connector-type <same> --api-flavor <same> \
    --connection-id <same> --output json
  ```

  Expect `isAvailable: true` / `isCompatible: true` in the validation block.
- If the external service revoked the app, re-authorize it in the vendor's settings before re-authenticating the connection.
- For BYO configs used in production, audit periodically: `uip llm-configuration byo-connections list --include-connection-details --output-filter "Data[?connectionState!='Enabled']"`.
