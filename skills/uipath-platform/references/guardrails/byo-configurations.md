# BYO Guardrail (BYOG) Configurations

Inspect tenant-registered bring-your-own guardrail configurations via `uip guardrails byo-configurations list`. A BYOG configuration registers an external validator provider (e.g. Databricks AI Guardrails, Azure AI Content Safety) against an Integration Service connection, so an agent's guardrail checks (PII detection, harmful content, etc.) run against that external provider instead of — or as a fallback pair with — UiPath's own built-in implementation.

> **List-only today.** There is no `create` / `update` / `delete` / `get` verb yet. Registering, editing, or removing a BYOG configuration is **Admin UI only**: Admin → AI Trust Layer → Guardrails Configurations. This command is read visibility, not lifecycle management.

---

## Command

```bash
uip guardrails byo-configurations list --output json
```

**Prerequisites:**
- **Logged in with a user token, not an application (client-credentials) token.** The endpoint requires an org-admin **user** session and rejects application tokens outright.
- The logged-in user must have an org-admin role for AI Trust Layer in the target tenant. Insufficient permissions surface as a `403` with the backend's reason in `Instructions` (e.g. `"User is not a member of the Administrators group"`) — distinct from the `404`/`ByoGuardrailsUnavailable` case below.
- No other setup — this is a read-only listing of whatever the tenant admin has already registered via the Admin UI.

### Output shape

```json
{
  "Result": "Success",
  "Code": "ByoGuardrailConfigurationsList",
  "Data": [
    {
      "Id": "e5723bb8-fbc2-4317-c7d7-08de803bc010",
      "ConnectionId": "18fb337c-29b7-4162-a9e8-0c05b01cf4df",
      "ValidatorName": "my-pii-guardrail",
      "ValidatorType": "pii_detection",
      "FallbackOnUiPath": true,
      "Enabled": true,
      "CreatedAt": "2026-07-01T10:00:00Z",
      "UpdatedAt": null,
      "ConnectorKey": "uipath-azure-contentsafety",
      "ConnectorName": "Azure AI Content Safety",
      "ConnectionName": "My Content Safety Connection",
      "ValidConnection": true
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `Id` | The BYOG configuration's own id — this is the `ByoConfigurationId` a low-code guardrail includes to pin itself to this exact configuration (see [uipath-agents guardrails](/uipath:uipath-agents)). |
| `ConnectionId` | The Integration Service connection GUID backing this configuration. This is the value a **coded agent** passes as `connection_id` in `ByoValidator(<ValidatorName>, connection_id=<ConnectionId>)` — the backend does no name→id resolution, so it must be the literal GUID. |
| `ValidatorName` | The tenant-chosen alias for this configuration — the first argument a coded agent passes to `ByoValidator(...)`, and the same value surfaced as `ByoValidatorName` by `uip agent guardrails list --byo`. |
| `ValidatorType` | The raw validator category this configuration implements (e.g. `pii_detection`, `harmful_content`) — matches the built-in `Validator` name for the same category. |
| `FallbackOnUiPath` | Whether a failed call to the external provider falls back to UiPath's own built-in validator logic, or hard-fails the guardrail check. |
| `Enabled` | Whether the tenant has switched this configuration on. A disabled configuration still appears in `uip agent guardrails list --byo` output but with `Status: Disabled`. |
| `ValidConnection` | Whether the underlying Integration Service connection currently resolves and is healthy. `false` means the connection was disabled, revoked, or rotated since registration. |
| `ConnectorKey` / `ConnectorName` / `ConnectionName` | Resolved metadata about the underlying IS connector/connection, for display. |

Empty `Data: []` is a valid result — it means the tenant has no BYOG configurations registered.

### Feature not available

A 404 surfaces as:

```json
{
  "Result": "Failure",
  "Code": "ByoGuardrailsUnavailable",
  "Message": "...",
  "Instructions": "Contact UiPath support to enable bring-your-own guardrails for this tenant."
}
```

This means BYOG is not enabled (feature-flagged off) for the tenant — not a transient error. Report it to the user rather than retrying.

### Permission errors (distinct from feature-not-available)

Any other non-2xx status (e.g. `403`) surfaces as `Message: "Failed to list BYO guardrail configurations"` with the backend's response body carried in `Instructions` (truncated to 1000 characters) — e.g. `"403 Forbidden: {\"title\":\"Forbidden\",\"detail\":\"User is not a member of the Administrators group\"}"`. This means the logged-in identity lacks the org-admin role, or is an application token (not a user token) — tell the user to re-authenticate with an admin user account rather than treating it as a feature-availability problem.

---

## How this feeds agent authoring

This command is the **only CLI way to obtain the `ConnectionId`** a coded agent needs. The agent-authoring side (discovery from an agent-design context, not admin) is `uip agent guardrails list --byo` in `uipath-agents` — see:
- [Low-code guardrails](/uipath:uipath-agents) — `builtInValidator` guardrails authored against a specific BYOG configuration via `byoConfigurationId`.
- [Coded guardrails](/uipath:uipath-agents) — `ByoValidator(<ValidatorName>, connection_id=<ConnectionId>)`.

## Diagnostics

**`ValidConnection: false`** — the underlying Integration Service connection is broken. Inspect and repair it directly:

```bash
uip is connections list --output json
uip is connections get <connection-id> --output json
```

See [Connections](../integration-service/connections.md) for connection lifecycle. There is no CLI re-probe for a BYOG configuration itself (unlike BYO LLM connections' `get --force-refresh`) — repairing the underlying IS connection is the fix; the BYOG record's `ConnectionId` doesn't change.

**A guardrail using this configuration behaves unexpectedly at runtime** — check `Enabled` and `FallbackOnUiPath` here first: a disabled configuration or a dead connection with `FallbackOnUiPath: false` fails the guardrail check outright rather than falling back to the built-in validator. See [uipath-troubleshoot § Guardrail Violation](/uipath:uipath-troubleshoot) for full runtime diagnosis via trace spans.
