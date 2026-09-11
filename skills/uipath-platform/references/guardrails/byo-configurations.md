# BYO Guardrail (BYOG) Configurations

Manage tenant-registered bring-your-own guardrail configurations with `uip guardrails byo-configurations` (`list`, `list-validators`, `probe`, `create`, `update`, `delete`). A BYOG configuration registers an external validator provider through an Integration Service connection. Agent guardrail checks can use that provider instead of, or as a fallback pair with, UiPath's built-in implementation. This is analogous to BYO LLM configurations managed by [`uip llm-configuration byo-connections`](../llmgateway/byo-connections.md) and the CLI counterpart of Admin → AI Trust Layer → Guardrails Configurations.

> **No `get <id>` verb.** `update` fetches the current record internally before its PUT. To inspect one configuration, run `uip guardrails byo-configurations list --output json` and filter by `Id`.

## Subcommand surface

| Command | Purpose |
|---|---|
| `list` | List tenant BYOG configurations with resolved connection details. |
| `list-validators` | List validators exposed by an Integration Service connection. Each `Validator` is a valid `--validator-type`. |
| `probe` | Test a connection/validator pair without creating anything; exits 1 when unavailable. |
| `create` | Register a configuration. Requires `--connection-id`, `--validator-name`, and `--validator-type`; supports `--fallback-on-ui-path` and `--disabled`; always probes first and aborts on failure. |
| `update <configuration-id>` | Merge-update connection, fallback, or enabled state. `ValidatorName` and `ValidatorType` are locked after creation. Supplying `--connection-id` re-probes and aborts on failure. |
| `delete <configuration-id> --force` | Permanently delete; `--force` is mandatory. |

### Prerequisites

All verbs require a logged-in **user token**, not an application (client-credentials) token, and an org-admin role for AI Trust Layer in the target tenant. The endpoint rejects application tokens. Insufficient permissions return `403` with the backend reason in `Instructions`, such as `"User is not a member of the Administrators group"`; distinguish this from the `404`/`ByoGuardrailsUnavailable` case.

For `create` and `update --connection-id`, an Integration Service connection must already exist. Run `uip is connections list --output json` and pass its UUID as `--connection-id`. See [Connections](../integration-service/connections.md).

## `list`

Run:

```bash
uip guardrails byo-configurations list --output json
```

A successful response has `Result: "Success"`, `Code: "ByoGuardrailConfigurationsList"`, and `Data`. `Data: []` means no registered configurations. Records can contain:

```json
{
  "Id": "…",
  "ConnectionId": "…",
  "ValidatorName": "…",
  "ValidatorType": "…",
  "FallbackOnUiPath": true,
  "Enabled": true,
  "CreatedAt": "…",
  "UpdatedAt": null,
  "ConnectorKey": "…",
  "ConnectorName": "…",
  "ConnectionName": "…",
  "ValidConnection": true
}
```

- `Id`: configuration id for `update` and `delete`.
- `ConnectionId`: Integration Service connection GUID used at runtime; agents never supply it.
- `ValidatorName`: tenant-chosen alias, unique across the tenant; agents pass it to `ByoValidator(...)`, and `uip agent guardrails list --byo` shows it as `ByoValidatorName`.
- `ValidatorType`: raw validator category, such as `pii_detection` or `harmful_content`; matches the built-in `Validator` name.
- `FallbackOnUiPath`: whether external-provider failure falls back to UiPath's built-in validator or hard-fails the check.
- `Enabled`: whether the configuration is active. Disabled configurations remain in `uip agent guardrails list --byo` with `Status: Disabled`.
- `ValidConnection`: whether the underlying connection resolves and is healthy; `false` can mean disabled, revoked, or rotated.
- `ConnectorKey` / `ConnectorName` / `ConnectionName`: resolved display metadata; `null` when unresolved.

## `create`

**Run the following discovery calls first; never fabricate either value.**

1. Run `uip guardrails byo-configurations list --output json` and verify that `ValidatorName` is unused; duplicate names are rejected across the tenant.
2. Run `uip is connections list "<connector-key>" --all-folders --output json`. Select by `ConnectorName`/`Name`, not position, and pass the selected connection's `Id` as `--connection-id`. A fabricated or placeholder GUID fails the probe and creates nothing.

Run these optional read-only checks when needed:

```bash
uip guardrails byo-configurations list-validators --connection-id <guid> --output json
uip guardrails byo-configurations probe --connection-id <guid> --validator-type pii_detection --output json
```

Run:

```bash
uip guardrails byo-configurations create \
  --connection-id <is-connection-uuid> \
  --validator-name my-pii-guardrail \
  --validator-type pii_detection \
  --output json
```

Require `--connection-id`, `--validator-name`, and `--validator-type`. The pair is always probed server-side before saving; there is no skip flag. `--fallback-on-ui-path` defaults to `false`; configurations are enabled by default, and `--disabled` saves one disabled. Success returns `Code: ByoGuardrailConfigurationCreated` and the created configuration in `Data`; use `Data.Id` for `update` or `delete`.

## `update`

Run, for example:

```bash
uip guardrails byo-configurations update <configuration-id> --connection-id <new-uuid> --output json
uip guardrails byo-configurations update <configuration-id> --disabled --output json
uip guardrails byo-configurations update <configuration-id> --enabled --output json
```

- Update has merge semantics: it fetches the current record and PUTs it with only supplied fields changed.
- Updatable fields are `--connection-id`, `--fallback-on-ui-path`/`--no-fallback-on-ui-path`, and `--enabled`/`--disabled` (mutually exclusive).
- Supplying `--connection-id` re-probes the new pair and aborts on failure. Changing only enabled or fallback state does not probe, so `update <id> --disabled` works when the provider is unavailable.
- `ValidatorName` and `ValidatorType` are locked after creation; delete with `--force` and create again to rename or retype.
- Supplying no updatable field is refused client-side before any API call.
- Success returns `Code: ByoGuardrailConfigurationUpdated`.

## `delete`

Run:

```bash
uip guardrails byo-configurations delete <configuration-id> --force --output json
```

Without `--force`, the command refuses with `"Refusing to delete without --force. Deletion is permanent."` Success returns `Code: ByoGuardrailConfigurationDeleted` and `Data: { Id: <id> }`. A guardrail referencing the deleted configuration by `ByoValidatorName` fails at runtime.

## Validation and diagnostics

The connection/validator pair is always probed server-side before saving, with no skip flag. `create` persists nothing on failure; `update` probes only when `--connection-id` is supplied. Changing only `--enabled`/`--disabled` or the fallback flag does not re-probe.

The probe asks the connector for its validators and evaluates a benign test input using default parameters. It verifies reachability and that the service serves the requested `--validator-type`; wrong connection ids, incompatible services, and providers that do not implement the guardrail contract fail before runtime.

Run these read-only commands when discovering or troubleshooting a pairing:

```bash
# Does this connection serve this validator? (probes, creates nothing)
uip guardrails byo-configurations probe --connection-id <guid> --validator-type pii_detection --output json

# Which validators does this connection expose? Each Validator is a valid --validator-type.
uip guardrails byo-configurations list-validators --connection-id <guid> --output json
```

`probe` exits 1 when unavailable. `list-validators` returns the exact accepted ids, plus each validator's `AllowedScopes` and `Parameters` schema, and is the fastest way to correct `VALIDATOR_NOT_SUPPORTED`.

On failure, the command exits 1 with `Code: ByoGuardrailProbeFailed` and a diagnostic `Data` block:

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

For `ValidConnection: false`, inspect and repair the Integration Service connection. Run:

```bash
uip is connections list --output json
uip is connections ping <connection-id> --output json
```

See [Connections](../integration-service/connections.md). Run `uip guardrails byo-configurations probe --connection-id <id> --validator-type <type>` to re-probe without changing anything. Repair the connection or run `update <id> --connection-id <new-uuid>` to select a healthy one; the update probes before saving.

If a guardrail behaves unexpectedly, check `Enabled` and `FallbackOnUiPath`. A disabled configuration, or a dead connection with `FallbackOnUiPath: false`, fails the guardrail check instead of falling back. Run `update <id> --enabled` after resolving the cause. See [uipath-troubleshoot § Guardrail Violation](/uipath:uipath-troubleshoot) for runtime diagnosis through trace spans.

## Error paths

### Feature not available

Any verb can return:

```json
{
  "Result": "Failure",
  "Code": "ByoGuardrailsUnavailable",
  "Message": "…",
  "Instructions": "Contact UiPath support to enable bring-your-own guardrails for this tenant."
}
```

This `404` means BYOG is feature-flagged off for the tenant; report it and do not retry.

### Configuration not found

For `update` or `delete`, a nonexistent id is reported as `Code: ByoGuardrailConfigurationNotFound`, distinct from `ByoGuardrailsUnavailable`. Run `uip guardrails byo-configurations list --output json` to obtain valid ids.

### Permission errors

Other non-2xx responses, including `403`, surface as `Message: "Failed to <verb> BYO guardrail configuration(s)"` with the backend body in `Instructions`, truncated to 1000 characters; for example: `"403 Forbidden: {\"title\":\"Forbidden\",\"detail\":\"User is not a member of the Administrators group\"}"`. The identity lacks the org-admin role or is using an application token. Tell the user to re-authenticate with an admin user account; do not treat this as feature unavailability.

## How this feeds agent authoring

Agents reference a BYOG configuration by `ValidatorName` alone. The platform resolves the connection server-side; agents never pass a connection id. From an agent-design context, run `uip agent guardrails list --byo` in `uipath-agents`. See:

- [Low-code guardrails](/uipath:uipath-agents) — `builtInValidator` guardrails use `byoValidatorName`.
- [Coded guardrails](/uipath:uipath-agents) — `ByoValidator(<ValidatorName>)`.