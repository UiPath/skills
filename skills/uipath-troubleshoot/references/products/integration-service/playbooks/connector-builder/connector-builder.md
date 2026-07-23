---
confidence: medium
---

# Connector Builder Diagnostics

## Context

Use this router for a custom connector during authoring, import, publish, connection
provisioning, runtime request/response handling, or custom trigger setup.

This is a secondary implementation playbook, not the primary entry point for a
failed workflow. Do not use it merely because a workflow consumes a custom
connector. Stable DAP codes and ordinary connection/runtime errors start in
[Integration Service summary](../../summary.md), then
[Integration Service Connector Diagnostics](../connectors/connector.md). Enter
this folder only after runtime evidence identifies the custom definition, hook,
schema, route, import, publication, or trigger contract as the first failing
boundary.

Collect these anchors before selecting a branch:

- environment, organization, tenant, and region;
- local connector directory and connector key;
- draft/imported/published version or revision;
- phase: authoring, validate, import, publish, connection, operation, or trigger;
- connection ID, operation/resource/method, and trigger ID where applicable;
- request/trace or publish ID, UTC timestamp, full outer error, provider status/body;
- caller: builder test, Studio test/debug, deployed automation, Apps, API Workflow, or Maestro.

Never include secrets, authorization headers, client secrets, passwords, API keys, or tokens in
the evidence bundle.

### What can cause it

- The published exposed route or HTTP method does not match the imported custom connector definition.
- The custom authentication, token, refresh, validation, or provisioning contract is incorrect.
- The provider TLS certificate, chain, hostname, protocol, cipher, or supported trust contract is invalid.
- A request hook, response root, schema, field mapping, pagination, or file-transfer contract is incorrect.
- Activity-generation metadata or project compatibility omitted a method, field, upload, or download activity.
- The OpenAPI definition or generated connector structure is unsupported, invalid, or too large for the authoring path.
- The wrong revision was imported, published, promoted, cached, or bound to the consumer.
- The custom polling or webhook definition cannot represent or deliver the provider event contract.

## Investigation

### Route by First Failing Phase

| Signature | Playbook |
|---|---|
| Builder test succeeds but published operation returns route-level `404`; exposed path and vendor path may differ | [route-path-mapping.md](./route-path-mapping.md) |
| Connection creation/token exchange/refresh fails, auth fields are absent, or grant may be unsupported | [authentication-provisioning.md](./authentication-provisioning.md) |
| `SSLHandshakeException`, `PKIX path building failed`, certificate, hostname, protocol, or cipher error | [tls-pkix.md](./tls-pkix.md) |
| Runtime request differs from design, provider response is empty/mis-shaped, or mapping fails | [request-response-contract.md](./request-response-contract.md) |
| Activity is absent from Studio Web, Studio, Maestro, Apps, Agent Builder, or API Workflows; fields are missing; file upload/download fails or is unavailable | [activity-surfaces-files.md](./activity-surfaces-files.md) |
| OpenAPI import/Activity Designer hangs, fails validation, or returns `5xx` | [import-authoring.md](./import-authoring.md) |
| Local change is absent after publish, publish fails, connector is not visible, or environment promotion breaks identity | [publishing-lifecycle.md](./publishing-lifecycle.md) |
| Custom polling/webhook trigger is absent or never fires | [trigger-contract.md](./trigger-contract.md) |

If more than one signature is present, select the earliest failing phase. For example, an
operation cannot validate a response mapping if the published route never matched.

### Baseline Inspection

When the connector source is available, run from its root:

```bash
uip is connectors builder inspect --output json
uip is connectors builder validate --output json
```

Inspect the matching paths in `app/element/element.json`,
`app/element/element-metadata.json`, `app/element/standard-resources/`, and
`app/element/hooks/`. `inspect` is discovery; `validate` is the static pass/fail gate. Static
success does not prove the imported/published revision or a live provider request is correct.

For a published custom connector, correlate local version, imported definition, publish job,
published catalog identity, connection, and runtime request. Builder preview success proves
only the preview path.

For a workflow failure, require the failed execution ID, faulting activity,
connector/version, connection, operation, UTC window, and provider/connector trace
before attributing the failure to the local connector files. A successful static
validation and a source observation are not runtime causation.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then route to the
matching leaf playbook. If evidence does not isolate one cause, present the missing
discriminator instead of changing the connector.

Correct the earliest proven lifecycle phase using the selected playbook, then
validate, import, publish, and verify the exact affected consumer path as required.

The diagnosis must identify the exact artifact and field that differs from the
observed runtime contract. Changes to connector source, import/publish state,
connections, or provider configuration require explicit approval; otherwise
present the proposed change and verification steps only.

### Escalation Boundary

Escalate when the evidence shows:

- the published definition differs from a successful validated/imported definition;
- route matching fails before a request reaches the provider;
- a supported auth contract is serialized or executed incorrectly;
- a provider-success payload cannot be represented by the declared connector schema;
- a valid connector definition repeatedly fails import/publish;
- a correctly declared event operation is absent or the event path stops inside IS.

Attach the relevant branch's escalation bundle and state which anchors remain unavailable.
