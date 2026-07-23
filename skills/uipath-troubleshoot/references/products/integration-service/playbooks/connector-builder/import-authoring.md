---
confidence: medium
---

# Custom Connector Import and Authoring Failures

## Context

Use when OpenAPI import fails or returns `5xx`, an import appears to do nothing, Activity
Designer spins or times out, a resource cannot be saved, or local connector validation reports
structural/linkage errors.

This playbook separates an invalid/unsupported API definition, connector-definition validation
failure, definition-size/rendering issue, and service regression. It does not diagnose runtime
provider calls.

Required anchors: environment, authoring surface and browser/client version, connector key,
definition format and size, path/schema counts, exact action, request/trace ID, timestamp,
HTTP status/body, and whether a minimal definition succeeds.

### What can cause it

- The source OpenAPI or connector definition is syntactically invalid or structurally inconsistent.
- The definition uses an unsupported protocol, content type, schema shape, reference graph, or operation contract.
- Generated connector resources, standard-resource links, operation IDs, or field metadata fail validation.
- Definition size, path count, schema depth, or Activity Designer rendering exceeds the authoring path's practical capacity.
- The tenant import or authoring service regressed even though a minimal supported definition succeeds.

## Investigation

1. **Preserve the original definition and error.** Do not repeatedly resave or manually prune
   the only copy.
2. **Classify the phase:** source parsing, generated connector validation, Activity Designer
   rendering/edit/save, or tenant import.
3. **For a local connector,** inspect and validate:

   ```bash
   uip is connectors builder inspect --output json
   uip is connectors builder validate --output json
   ```

   Fix the reported field/linkage error one at a time. Do not treat `inspect` as validation.
4. **For OpenAPI,** record specification version, external `$ref` usage, circular/deep schemas,
   unsupported content types or operations, duplicate/invalid operation IDs, and path/schema
   cardinality. Connector Builder custom connectors support REST APIs with JSON contracts;
   XML/SOAP/GraphQL/binary-only requirements are a capability mismatch.
5. **Reduce only on a copy.** Test a minimal valid definition and then add path/schema groups to
   identify the smallest failing construct or size threshold. A minimal success plus large-file
   `503`/UI hang is performance/capacity evidence, not proof that the full spec is invalid.
6. **For Activity Designer spinning,** capture the resource's field/parameter/schema size,
   browser console/network failure, server request ID, and whether another small resource in the
   same connector renders.
7. **For tenant import,** verify login/tenant, connector root, generated `element.json`,
   metadata, standard-resource linkage, hook references, and exact import response.
8. **Check service state** when multiple known-good definitions fail in the same environment.

### Diagnosis

| Evidence | Diagnosis |
|---|---|
| Parser identifies a specific invalid construct | Definition syntax/structure |
| Valid spec requires unsupported protocol/content/shape | Product capability limitation |
| Builder validation names a broken field/resource/hook/event link | Connector artifact defect |
| Minimal import works; failure correlates reproducibly with size/cardinality | Import/render performance or service limit |
| Same known-good artifact works elsewhere but repeatedly returns `5xx` here | Environment/service regression |
| Import succeeds but runtime still uses older content | Publishing lifecycle, not import authoring |

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that authoring/import branch. If evidence does not isolate one cause, stop at the
missing discriminator.

Diagnosis is read-only. Obtain explicit approval before changing the definition,
importing, publishing, or altering provider/tenant configuration.

- Correct the minimal invalid construct or connector linkage and rerun validation.
- For unsupported contracts, redesign to a supported REST+JSON representation or document the
  limitation; do not conceal it with a brittle schema.
- Split very large definitions into supported connector boundaries only when that design is
  acceptable; otherwise escalate the reproducible threshold and request IDs.
- For a service regression, preserve the failing and minimal-success artifacts and escalate
  rather than repeatedly importing.
- After a successful local validation, import once, retain the response/revision, then use the
  publishing playbook.

### Verification

Prove the exact previously failing definition/resource parses, validates, imports, and can be
reopened. A successful reduced definition verifies only the reducer hypothesis.

### Escalation Bundle

Include anchors, sanitized failing definition or minimal reproducer, file size and counts,
validation output, browser/network evidence, import response, request IDs, environment
comparison, and exact unsupported construct if identified.
