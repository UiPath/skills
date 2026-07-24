---
confidence: medium
---

# Custom Connector Request and Response Contract

## Context

Use when the provider receives a request different from the connector design, the provider
response is visible but the connector output is empty, a field/type mapping fails, pagination
stops, or a pre/post hook changes the contract.

If the provider returned a non-success HTTP status, first classify it with
[request-failed.md](../request-failed.md). If the published route never matched, use
[route-path-mapping.md](./route-path-mapping.md).

Required anchors: connector/published version, connection ID, resource/operation/method,
request/trace ID and timestamp, redacted emitted request, redacted provider response and content
type, expected input/output schema, page number/token, and involved hook names.

### What can cause it

- The connector emitted the wrong base URL, vendor path, HTTP method, parameter, header, body wrapper, or serialization.
- A pre-request hook changed or omitted required request data.
- The provider response content type, root/data envelope, array/object shape, or field type differs from the declared connector schema.
- A post-response hook dropped or transformed provider data incorrectly.
- Pagination root, token, offset, next URL, page size, or termination logic is incorrect.
- The inspected local definition is not the imported/published revision used by the failed runtime call.

## Investigation

1. **Build a phase-by-phase diff:** activity inputs → declared connector resource → pre-request
   hook output → emitted provider request → provider response → post-response hook output →
   declared standard-resource/output.
2. **Inspect and validate the exact connector revision:**

   ```bash
   uip is connectors builder inspect --output json
   uip is connectors builder validate --output json
   ```

3. **Request branch:** compare base URL, `vendorPath`, HTTP method, path/query parameters,
   headers (`Content-Type`, `Accept`, authorization placement), body wrapper, field names,
   serialization, and the pre-request hook. Check actual traffic; a correct draft is not proof.
4. **Empty response branch:** confirm the provider returned a body, then compare content type,
   response root key/data envelope, standard-resource method linkage, hidden/curated fields, and
   post-response hook behavior. A missing/wrong response root key is a deterministic cause when
   the payload exists below that root.
5. **Schema branch:** identify the precise field and actual versus declared type. Compare
   nullable fields, arrays versus objects, dynamic/polymorphic values, and nested structures.
6. **Pagination branch:** inspect provider next-page link/token/offset, configured root,
   termination condition, and any hook that derives the next request. Distinguish a provider
   with one page from a connector that ignores the next-page marker.
7. **Hook branch:** verify reference/filename/case, phase, resource/method scope, supported
   runtime modules, error handling, and that every path calls `done()`. Prefer a declarative
   mapping when it can express the contract.

### Diagnosis

| Evidence | Diagnosis |
|---|---|
| Emitted request differs before any hook | Resource/configuration or activity-input mapping |
| Pre-request hook introduces the difference | Hook defect |
| Provider body exists below an unconfigured/wrong root | Response root-key defect |
| Provider body reaches post hook but output becomes empty/changed | Post-response hook defect |
| Provider success has a field shape incompatible with declared output | Connector schema drift/design limitation |
| Provider exposes a next-page marker that is not followed | Pagination configuration/hook defect |
| Static source is correct but runtime uses another revision | Import/publish lifecycle issue |

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that request/response branch. If evidence does not isolate one cause, stop at the
missing discriminator.

Diagnosis is read-only. Obtain explicit approval before editing hooks/resources,
importing, publishing, or remapping a consumer.

- Correct the smallest proven layer: resource method/path/parameters, header/body mapping, root
  key, field schema, pagination, or hook.
- For connector schema drift, update the declared standard resource and activity output, bump
  the version, validate, import, publish, and re-map consumers if the public type changed.
- Do not force an unstable/dynamic response into a fixed schema without a documented transform
  and representative payload coverage.
- After a source fix:

  ```bash
  uip is connectors builder validate --output json
  ```

  Then import and publish before testing the runtime.

### Verification

Replay representative requests through the published connector, including an error payload,
null/optional fields, and at least two pages when pagination applies. Compare the actual emitted
request and final mapped output—not only Builder preview.

### Escalation Bundle

Include anchors, redacted phase-by-phase diff, exact resource and standard-resource entries,
hook names and relevant redacted logic, actual/expected field type or root, pagination markers,
validation output, and imported/published versions.
