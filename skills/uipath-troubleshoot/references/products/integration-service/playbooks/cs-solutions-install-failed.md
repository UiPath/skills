---
confidence: medium
---

# Connection Service — Solutions Package Install / Validation Failed (CNS1050, CNS1055–CNS1075 range, shell connections)

> **Fault bucket: 👤 A for spec/version/authentication issues (the package author or installer fixes the package or the tenant state) · 🛠 B1 for unexpected-error and stuck-publish codes.** These codes surface when a **Solutions package** that carries connections/connectors is validated or installed into a tenant. Unlike the rest of the CNS family, most of them are **not HTTP errors** — they arrive *embedded* in the validation response (`ValidateResourcesResponse`) or the async install job's status as per-resource `ValidationError` entries, each with its own `ErrorCode` and sometimes `AllowedActions`.

## Context

What this looks like:
- Solution install/validate reports per-resource errors; the install job status carries `ValidationError { ErrorCode: "CNS10xx", … }` entries
- A corrupt package upload fails outright with HTTP 400 `CNS1050`

Package/spec validation (fix the package):

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| `CNS1050` | InvalidSolutionArchive | Package zip is corrupt/unreadable (HTTP 400, not embedded) | Rebuild/re-upload the package. ⚠ `CNS1050` is a **duplicated literal** — it is also `EventModeNotSupported` on the make-connection-call API; disambiguate by operation. |
| `CNS1059` | ConnectorKeyRequired | Connector/connection resource spec missing `Key` | Fix package spec |
| `CNS1074` | ConnectorNameRequired | Connector spec missing `Name` | Fix package spec |
| `CNS1055` | InvalidAuthenticationType | Connection spec has an unrecognized authentication type | Fix package spec |
| `CNS1058` | ConnectionNameInvalid | Connection spec name invalid | Fix package spec |
| `CNS1039` | InvalidPollingInterval | Polling interval out of range (also a live-API error) | Fix package spec |

Connector version reconciliation (installer chooses):

| Code | Name | Meaning | AllowedActions |
|------|------|---------|----------------|
| `CNS1064` | ConnectorVersionNotFound | Package links a custom-connector version not present in the tenant | Install the connector first |
| `CNS1066` | LowerConnectorVersionExists | Tenant has a lower version than the package expects | UseExisting / MergeConfiguration |
| `CNS1067` | HigherConnectorVersionExists | Tenant has a higher version | UseExisting |

Shell connections (authenticate-after-deployment):

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| `CNS1068` | ShellConnectionRequired | Spec says authenticate-after-deployment but no shell-connection key supplied | Fix package spec |
| `CNS1069` | ShellConnectionNotFound | Referenced shell connection doesn't exist in the tenant | Create/fix the reference |
| `CNS1072` | ShellConnectionRequiredAuthentication | Shell connection exists but is unauthenticated | Authenticate it, then install |
| `CNS1071` | ShellConnectionWarning | Informational: authentication will be required after deployment | None — expected |
| `CNS1070` | ShellConnectionUnexpectedError | Unexpected failure validating the shell connection | 🛠 escalate |

Service-side install failures (escalate if not transient):

| Code | Name | Meaning |
|------|------|---------|
| `CNS1060` | ConnectorKeyUnexpectedError | Unexpected exception checking connector existence/version (element-service call failure) |
| `CNS1063` | ConnectorImportError | Unexpected exception importing a custom connector, or its publish job failed |
| `CNS1065` | ConnectorImportPublishError | Connector publish job stuck in progress past the polling timeout |
| `CNS1056` | ConnectionCreateError | Unexpected exception creating a connection during install |
| `CNS1057` | ConnectionUpdateError | Unexpected exception updating a connection during install |

## Investigation

1. **Read the per-resource `ValidationError` list from the install/validate response** — each entry names the resource, the code, and (for version conflicts) the `AllowedActions`. The code table above routes each one; most installs fail on the *first* category (spec errors) or the *second* (version reconciliation).
2. **Version conflicts (`CNS1064`/`CNS1066`/`CNS1067`)** are choices, not faults: decide whether the tenant's existing connector version should win (`UseExisting`), merge configuration, or install the packaged version first.
3. **Shell-connection codes:** verify the referenced connection exists and is authenticated in the target tenant *before* re-running the install. `CNS1071` is a warning — the install proceeded; someone must authenticate after deployment (until then, runtime calls will fail with `CNS1008` — see [cs-connection-not-authenticated.md](./cs-connection-not-authenticated.md)).
4. **Service-side codes (`CNS1060`/`CNS1063`/`CNS1065`/`CNS1056`/`CNS1057`):** retry the install once (transient dependency blips are common); a repeat with the same code is an Integration Service escalation with the install job ID and `traceId`. `CNS1065` specifically means the connector publish pipeline is slow/stuck — check for a wider publish backlog before blaming the package.

## Resolution

- **Spec errors:** fix the package definition and rebuild — these never self-resolve.
- **Version reconciliation:** pick an `AllowedAction` deliberately; document which connector version the solution standardizes on to avoid drift across tenants.
- **Shell connections:** create/authenticate the referenced connection, re-run install; plan for post-deployment authentication of `CNS1071`-flagged connections as part of the rollout runbook.
- **Sustained service-side failures:** escalate with install job ID, tenant, package name/version, and `traceId`s.
