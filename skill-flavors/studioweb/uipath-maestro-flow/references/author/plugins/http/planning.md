<!--skill-flavor:http-prerequisites:start-->
- Auth is host-provided (for both modes — the node type comes from the registry); a 401/403 means the signed-in user lacks rights
- For connector mode: connector must support the HTTP request activity — verify the `HasHttpRequest` flag via `uip is connectors get "<connector-key>"`. If false, fall back to manual mode — confirm the switch with the user before finalizing. See [impl-connector.md Step 2](impl-connector.md#step-2--identify-target-connection).
- For connector mode: a healthy IS connection must exist for the **target connector**. If none exists, auto-fall-through to manual mode is the recommended fallback — but confirm the mode switch with the user before finalizing. See [impl-connector.md Step 2 — HTTP-specific recovery](impl-connector.md#step-2--identify-target-connection) for the user-confirmation flow (switch-to-manual / create-now / skip).
- `uip maestro flow registry pull` to cache the `core.action.http.v2` definition
<!--skill-flavor:http-prerequisites:end-->
