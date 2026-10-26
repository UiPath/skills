# BYO Guardrail (BYOG) Configurations

Manage tenant-registered bring-your-own guardrail configurations with `uip guardrails byo-configurations` (`list` / `list-validators` / `probe` / `create` / `update` / `delete`). A BYOG configuration registers an external validator provider (e.g. Databricks AI Guardrails, Azure AI Content Safety) through an Integration Service connection, so agent checks such as PII detection and harmful content use that provider instead of, or as a fallback with, UiPath's built-in implementation. This is the guardrail counterpart of [`uip llm-configuration byo-connections`](../llmgateway/byo-connections.md) and Admin → AI Trust Layer → Guardrails Configurations.

> **No `get <id>` verb.** `update` fetches the current record internally before its PUT, but there is no standalone read-by-id command. To inspect one configuration, run `uip guardrails byo-configurations list --output json` and filter by `Id`.

## Subcommand Surface

| Command | Purpose |
|---|---|
| `list` | List tenant BYOG configurations, including resolved connection details. |
| `list-validators` | List validators exposed by an Integration Service connection; each `Validator` is a valid `--validator-type`. |
| `probe` | Test whether a connection serves a validator without creating anything. Exits 1 when unavailable. |
| `create` | Register a configuration. Requires `--connection-id`, `--validator-name`, `--validator-type`; optionally accepts `--fallback-on-ui-path`, `--disabled`. **Always probes first and aborts if the probe fails.** |
| `update <configuration-id>` | Change connection, fallback, or enabled state with merge semantics. `ValidatorName`/`ValidatorType` are locked at creation; delete and re-create to change them. **Supplying `--connection-id` re-probes and aborts on failure.** |
| `delete <configuration-id> --force` | Permanently delete; `--force` is mandatory. |

**Prerequisites (all verbs):**
- **Log in with a user token, not an application (client-credentials) token.** The endpoint requires an org-admin **user** session and rejects application tokens.
- The user must have an org-admin role for AI Trust Layer in the target tenant. Insufficient permissions return `403` with the backend reason in `Instructions` (for example, `"User is not a member of the Administrators group"`), distinct from the `404`/`ByoGuardrailsUnavailable` case.
- For `create`/`update --connection-id`, an **Integration Service connection** to the provider must already exist. Discover it with `uip is connections list --output json`; pass its UUID as `--connection-id`. See [Connections](../integration-service/connections.md).

## `list`

Run:

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
| `Id` | Configuration id for `update`/`delete`. Agents do not reference it; low-code and coded guardrails use `ValidatorName`. |
| `ConnectionId` | Runtime Integration Service connection GUID. Agents never supply it; the platform resolves it server-side from the validator name. |
| `ValidatorName` | Tenant-chosen alias passed to `ByoValidator(...)` and surfaced as `ByoValidatorName` by `uip agent guardrails list --byo`. **Unique across the whole tenant**; duplicates are rejected. |
| `ValidatorType` | Raw category, such as `pii_detection` or `harmful_content`, matching the built-in `Validator` name for that category. |
| `FallbackOnUiPath` | Whether an external-provider failure falls back to UiPath's built-in validator or hard-fails the check. |
| `Enabled` | Whether enabled. Disabled configurations still appear in `uip agent guardrails list --byo` with `Status: Disabled`. |
| `ValidConnection` | Whether the underlying connection resolves and is healthy; `false` means it was disabled, revoked, or rotated since registration. |
| `ConnectorKey` / `ConnectorName` / `ConnectionName` | Resolved connector/connection display metadata; `null` when unresolved. |

`Data: []` is valid and means the tenant has no registered BYOG configurations.

## `create`

**Run the two discovery calls first — never fabricate either value.**

1. **`uip guardrails byo-configurations list --output json`** — `ValidatorName` is unique across the tenant, so check the name is free before you spend a create on it. A duplicate is rejected by the backend.
2. **`uip is connections list "<connector-key>" --all-folders --output json`** — `--connection-id` takes the connection's `Id`. Pick the connection by its `ConnectorName`/`Name`, not by position; a made-up or placeholder GUID fails the probe (below) and creates nothing.

Optionally run these read-only checks:

```bash
uip guardrails byo-configurations list-validators --connection-id <guid> --output json
uip guardrails byo-configurations probe --connection-id <guid> --validator-type pii_detection --output json
```

Then run:

```bash
uip guardrails byo-configurations create \
  --connection-id <is-connection-uuid> \
  --validator-name my-pii-guardrail \
  --validator-type pii_detection \
  --output json
```

- `--connection-id`, `--validator-name`, and `--validator-type` are required.
- The pair is probed server-side before saving, with no skip flag. See [Validation](#validation-mandatory-before-save).
- `--fallback-on-ui-path` defaults to **false**. Configurations are enabled by default; pass `--disabled` to disable.
- `--validator-name` must be tenant-unique; duplicates are rejected.
- Success returns `Code: ByoGuardrailConfigurationCreated`; `Data` is the created configuration. Use `Data.Id` for `update`/`delete`.

## `update`

```bash
uip guardrails byo-configurations update <configuration-id> --connection-id <new-uuid> --output json
uip guardrails byo-configurations update <configuration-id> --disabled --output json   # switch off
uip guardrails byo-configurations update <configuration-id> --enabled --output json    # switch back on
```

- **Merge semantics**: fetches the current record internally, then PUTs it with only supplied fields changed; omitted fields retain their values.
- Updatable flags: `--connection-id`, `--fallback-on-ui-path`/`--no-fallback-on-ui-path`, and `--enabled`/`--disabled` (mutually exclusive).
- Supplying `--connection-id` **re-probes the new pair and aborts on failure**; changing only enabled/fallback does not probe. This permits `update <id> --disabled` even when the provider is down.
- **`ValidatorName` and `ValidatorType` are locked after creation** and have no flags. Rename or retype by `delete --force` then `create`.
- Passing no updatable field is refused client-side before any API call.
- Success returns `Code: ByoGuardrailConfigurationUpdated`.

## `delete`

```bash
uip guardrails byo-configurations delete <configuration-id> --force --output json
```

- Without `--force` the command refuses: `"Refusing to delete without --force. Deletion is permanent."`
- Success returns `Code: ByoGuardrailConfigurationDeleted`, `Data: { Id: <id> }`.
- Deletion is permanent; a low-code or coded guardrail referencing the configuration by `ByoValidatorName` fails at runtime.

## Error paths

### Feature not available

Any verb can return:

```json
{
  "Result": "Failure",
  "Code": "ByoGuardrailsUnavailable",
  "Message": "...",
  "Instructions": "Contact UiPath support to enable bring-your-own guardrails for this tenant."
}
```

This `404` means BYOG is feature-flagged off for the tenant, not transient; report it rather than retrying.

### Configuration not found (update/delete only)

For `update`/`delete`, a `404` can instead mean the id does not exist. The CLI uses the backend error body and reports `Code: ByoGuardrailConfigurationNotFound` for a bad id. Do not treat it as feature unavailability; run `uip guardrails byo-configurations list --output json` for valid ids.

### Permission errors

Any other non-2xx status, such as `403`, returns `Message: "Failed to <verb> BYO guardrail configuration(s)"` and the backend body in `Instructions` (truncated to 1000 characters), for example `"403 Forbidden: {\"title\":\"Forbidden\",\"detail\":\"User is not a member of the Administrators group\"}"`. This indicates a missing org-admin role or an application token; tell the user to re-authenticate with an admin user account, not to treat it as feature unavailability.

## How this feeds agent authoring

Agents reference BYOG configurations **by `ValidatorName` alone**; the platform resolves the stored connection server-side and agents never pass a connection id. Discover authoring choices with `uip agent guardrails list --byo` in `uipath-agents`:
- [Low-code guardrails](/uipath:uipath-agents) — `builtInValidator` guardrails target a BYOG configuration through `byoValidatorName`.
- [Coded guardrails](/uipath:uipath-agents) — `ByoValidator(<ValidatorName>)`.

## Validation: mandatory before save

Like [BYO LLM connections](../llmgateway/byo-connections.md), the pair is **always probed server-side before saving, with no skip flag**:

- `create` always probes; failure aborts the create and persists nothing.
- `update` probes when `--connection-id` is supplied and aborts on failure. Changing only `--enabled`/`--disabled` or the fallback flag does not re-probe.

The probe asks the connector for its validators, then evaluates benign input with the validator's default parameters. It verifies reachability and that the service serves the requested `--validator-type`; wrong connection ids, wrong service types, and providers without the guardrail contract fail here rather than at runtime.

On failure the command exits 1 with `Code: ByoGuardrailProbeFailed` and a `Data` block carrying the diagnosis:

```json
{
  "Result": "Failure",
  "Code": "ByoGuardrailProbeFailed",
  "Message": "Probe failed for validator 'pii_detection' on connection '…' — REACHABILITY_FAILED: Connection […] is invalid or you do not have access to it",
  "Data": {
    "ConnectionId": "…",
    "ValidatorType": "pii_detection",
    "IsAvailable": false,
    "Error": { "Code": "REACHABILITY_FAILED", "Message": "…" }
  }
}
```

### Check the pair before you commit to it

Run these read-only verbs after a failed `create` or to discover supported validators:

```bash
# Does this connection serve this validator? (probes, creates nothing)
uip guardrails byo-configurations probe --connection-id <guid> --validator-type pii_detection --output json

# Which validators does this connection expose? Each Validator is a valid --validator-type.
uip guardrails byo-configurations list-validators --connection-id <guid> --output json
```

> **Important: no file support for BYO guardrails.** A BYO validator receives text only; attachments are never forwarded, and BYO entries in `uip agent guardrails list` have no `detectionScope` parameter. A guardrail using `byoValidatorName` with `detectionScope: "Files"` / `"Both"` evaluates no file content.

`probe` exits 1 when unavailable. `list-validators` returns the exact accepted ids, each one's `AllowedScopes` and `Parameters` schema, and is the fastest fix for `VALIDATOR_NOT_SUPPORTED`.

## Diagnostics

**`ValidConnection: false`** means the underlying Integration Service connection is broken. Inspect it directly:

```bash
uip is connections list --output json
uip is connections ping <connection-id> --output json
```

See [Connections](../integration-service/connections.md). To re-probe without changing anything, run `uip guardrails byo-configurations probe --connection-id <id> --validator-type <type>`; it reports the current verdict. Repair the IS connection or run `update <id> --connection-id <new-uuid>` with a healthy connection; update probes before saving.

**A guardrail using this configuration behaves unexpectedly at runtime** — check `Enabled` and `FallbackOnUiPath`: a disabled configuration, or a dead connection with `FallbackOnUiPath: false`, fails outright instead of falling back. Re-enable with `update <id> --enabled` after understanding the cause. See [uipath-troubleshoot § Guardrail Violation](/uipath:uipath-troubleshoot) for trace-span diagnosis.