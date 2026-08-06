# BYO Guardrail (BYOG) Configurations

Manage tenant-registered bring-your-own guardrail configurations via `uip guardrails byo-configurations` (`list` / `create` / `update` / `delete`). A BYOG configuration registers an external validator provider (e.g. Databricks AI Guardrails, Azure AI Content Safety) against an Integration Service connection, so an agent's guardrail checks (PII detection, harmful content, etc.) run against that external provider instead of — or as a fallback pair with — UiPath's own built-in implementation. This is the guardrail analog of the BYO LLM configurations managed by [`uip llm-configuration byo-connections`](../llmgateway/byo-connections.md), and the CLI counterpart of Admin → AI Trust Layer → Guardrails Configurations.

> **No `get <id>` verb.** `update` fetches the current record internally before its PUT, but there is no standalone read-by-id command — to inspect one configuration, `list` and filter by `Id`.

---

## Subcommand Surface

| Command | Purpose |
|---------|---------|
| `list` | List BYOG configurations for the tenant, including resolved connection details. |
| `create` | Register a new configuration. `--connection-id`, `--validator-name`, `--validator-type` required; optional `--fallback-on-ui-path`, `--disabled`. |
| `update <configuration-id>` | Change a configuration's connection, fallback, or enabled state. Merge semantics — only supplied fields change. `ValidatorName`/`ValidatorType` are locked at creation (delete + re-create to change them). |
| `delete <configuration-id> --force` | Permanently delete. `--force` is mandatory — the command refuses without it. |

**Prerequisites (all verbs):**
- **Logged in with a user token, not an application (client-credentials) token.** The endpoint requires an org-admin **user** session and rejects application tokens outright.
- The logged-in user must have an org-admin role for AI Trust Layer in the target tenant. Insufficient permissions surface as a `403` with the backend's reason in `Instructions` (e.g. `"User is not a member of the Administrators group"`) — distinct from the `404`/`ByoGuardrailsUnavailable` case below.
- For `create`/`update --connection-id`: an **Integration Service connection** to the guardrail provider must already exist. Discover with `uip is connections list --output json`; its UUID is what `--connection-id` takes. See [Connections](../integration-service/connections.md).

## `list`

```bash
uip guardrails byo-configurations list --output json
```

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
| `Id` | The BYOG configuration's own id — this is the `ByoConfigurationId` a low-code guardrail includes to pin itself to this exact configuration (see [uipath-agents guardrails](/uipath:uipath-agents)), and the id `update`/`delete` take. |
| `ConnectionId` | The Integration Service connection GUID this configuration calls through at runtime. Set here via `create`/`update` — **agents never supply it**; the platform resolves the connection server-side purely from the validator name. |
| `ValidatorName` | The tenant-chosen alias for this configuration — the only value a coded agent passes to `ByoValidator(...)`, and the same value surfaced as `ByoValidatorName` by `uip agent guardrails list --byo`. **Unique across the whole tenant** — the backend rejects a duplicate name outright. |
| `ValidatorType` | The raw validator category this configuration implements (e.g. `pii_detection`, `harmful_content`) — matches the built-in `Validator` name for the same category. |
| `FallbackOnUiPath` | Whether a failed call to the external provider falls back to UiPath's own built-in validator logic, or hard-fails the guardrail check. |
| `Enabled` | Whether this configuration is switched on. A disabled configuration still appears in `uip agent guardrails list --byo` output but with `Status: Disabled`. |
| `ValidConnection` | Whether the underlying Integration Service connection currently resolves and is healthy. `false` means the connection was disabled, revoked, or rotated since registration. |
| `ConnectorKey` / `ConnectorName` / `ConnectionName` | Resolved metadata about the underlying IS connector/connection, for display. `null` when unresolved. |

Empty `Data: []` is a valid result — it means the tenant has no BYOG configurations registered.

## `create`

```bash
uip guardrails byo-configurations create \
  --connection-id <is-connection-uuid> \
  --validator-name my-pii-guardrail \
  --validator-type pii_detection \
  --output json
```

- `--connection-id`, `--validator-name`, `--validator-type` are required.
- `--fallback-on-ui-path` defaults to **false**. Configurations are created **enabled** by default; pass `--disabled` to save it switched off.
- `--validator-name` must be unique across the tenant — a duplicate is rejected by the backend.
- Success: `Code: ByoGuardrailConfigurationCreated`, `Data` is the created configuration (use `Data.Id` for later `update`/`delete`).

## `update`

```bash
uip guardrails byo-configurations update <configuration-id> --connection-id <new-uuid> --output json
uip guardrails byo-configurations update <configuration-id> --disabled --output json   # switch off
uip guardrails byo-configurations update <configuration-id> --enabled --output json    # switch back on
```

- **Merge semantics**: the command fetches the current record internally, then PUTs it back with only the supplied fields changed. Fields you don't pass keep their current values.
- Updatable: `--connection-id`, `--fallback-on-ui-path`/`--no-fallback-on-ui-path`, `--enabled`/`--disabled` (mutually exclusive).
- **`ValidatorName` and `ValidatorType` are locked after creation** — there are no flags for them. To rename or retype, `delete --force` and `create` again.
- Passing no updatable field at all is refused client-side before any API call.
- Success: `Code: ByoGuardrailConfigurationUpdated`.

## `delete`

```bash
uip guardrails byo-configurations delete <configuration-id> --force --output json
```

- Without `--force` the command refuses: `"Refusing to delete without --force. Deletion is permanent."`
- Success: `Code: ByoGuardrailConfigurationDeleted`, `Data: { Id: <id> }`.
- Deletion is permanent; a guardrail (low-code `byoConfigurationId`, or coded `ByoValidator` by name) pointing at a deleted configuration fails at runtime.

## Error paths

### Feature not available

A "feature disabled" 404 surfaces on any verb as:

```json
{
  "Result": "Failure",
  "Code": "ByoGuardrailsUnavailable",
  "Message": "...",
  "Instructions": "Contact UiPath support to enable bring-your-own guardrails for this tenant."
}
```

This means BYOG is not enabled (feature-flagged off) for the tenant — not a transient error. Report it to the user rather than retrying.

### Configuration not found (update/delete only)

For `update`/`delete`, a 404 can also mean the configuration id doesn't exist. The CLI disambiguates the two by the backend's error body and reports `Code: ByoGuardrailConfigurationNotFound` for a bad id — don't treat it as the feature being off. Re-run `list` to get valid ids.

### Permission errors

Any other non-2xx status (e.g. `403`) surfaces as `Message: "Failed to <verb> BYO guardrail configuration(s)"` with the backend's response body carried in `Instructions` (truncated to 1000 characters) — e.g. `"403 Forbidden: {\"title\":\"Forbidden\",\"detail\":\"User is not a member of the Administrators group\"}"`. This means the logged-in identity lacks the org-admin role, or is an application token (not a user token) — tell the user to re-authenticate with an admin user account rather than treating it as a feature-availability problem.

---

## How this feeds agent authoring

Agents reference a BYOG configuration **by `ValidatorName` alone** — the platform resolves the connection server-side from the stored configuration; agents never pass a connection id. The agent-authoring side (discovery from an agent-design context, not admin) is `uip agent guardrails list --byo` in `uipath-agents` — see:
- [Low-code guardrails](/uipath:uipath-agents) — `builtInValidator` guardrails authored against a specific BYOG configuration via `byoConfigurationId`.
- [Coded guardrails](/uipath:uipath-agents) — `ByoValidator(<ValidatorName>)`.

## Diagnostics

**`ValidConnection: false`** — the underlying Integration Service connection is broken. Inspect and repair it directly:

```bash
uip is connections list --output json
uip is connections get <connection-id> --output json
```

See [Connections](../integration-service/connections.md) for connection lifecycle. There is no CLI re-probe for a BYOG configuration itself (unlike BYO LLM connections' `get --force-refresh`) — repair the underlying IS connection, or point the configuration at a healthy one with `update <id> --connection-id <new-uuid>`.

**A guardrail using this configuration behaves unexpectedly at runtime** — check `Enabled` and `FallbackOnUiPath` here first: a disabled configuration or a dead connection with `FallbackOnUiPath: false` fails the guardrail check outright rather than falling back to the built-in validator. Re-enable with `update <id> --enabled` once the cause is understood. See [uipath-troubleshoot § Guardrail Violation](/uipath:uipath-troubleshoot) for full runtime diagnosis via trace spans.
