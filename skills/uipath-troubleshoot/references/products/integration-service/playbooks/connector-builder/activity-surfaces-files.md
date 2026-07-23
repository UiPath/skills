---
confidence: medium
---

# Custom Connector Activity Surfaces and File Handling

Use when a custom connector is published but an object, method, field, trigger wait,
upload, or download activity is absent from a UiPath authoring surface, or when a
file activity fails due to its representation or size.

Do not start by recreating the connection. Activity generation depends on connector
metadata and project compatibility; authentication usually does not decide whether
an activity is listed.

## Context

This playbook covers the generated-activity boundary:

```text
connector definition → standard-resource linkage → generated activity metadata
→ consumer project compatibility → runtime file contract
```

Use [connector-builder.md](./connector-builder.md) when the first failure occurred
during import, authentication, request execution, publishing, or trigger authoring.

For a deployed workflow failure, require the failed run, faulting activity,
published connector/activity version, consumer project type, and generated
metadata before blaming the custom definition. A local source observation alone
does not prove why the runtime activity failed or disappeared.

### What can cause it

- The standard-resource method path/reference does not link to the Integration Service resource slug.
- The method, curated block, field visibility, lifecycle, or hidden metadata suppresses the generated activity or field.
- The generated `compatibleProjectTypes`, file/wait tags, tenant flags, Studio version, or package runtime excludes the consumer surface.
- The imported/published connector revision differs from the local definition or has not propagated to generated activity metadata.
- The connector models Base64 JSON, binary, multipart, chunked, or URL-source file transfer differently from the provider.
- The provider, connector, platform, or caller size/timeout ceiling is smaller than the attempted transfer.
- A hook loses multipart context, filename, MIME type, boundary, binary stream, or response content type.

## Investigation

### Fast Symptom Router

| Symptom | Most likely cause | First decisive check |
|---|---|---|
| Connector exists but object has no methods | Broken standard-resource linkage | Compare SR method path/reference with the Integration Service slug, not vendor path |
| Generic method exists but standalone curated activity does not | Missing/hidden `curated` block | Inspect `metadata.method.<VERB>.curated` |
| Curated activity exists but an input/output field is missing | Field visibility | Check `requestCurated`/`responseCurated`, method visibility, and `design.hidden` |
| Activity exists in Studio but not Agent Builder/API Workflows | Project-type filtering | Inspect live `compatibleProjectTypes` and file/wait tags |
| Activity exists in Studio Web but not older Studio | Studio/package version | Use Studio Desktop 2023.10+ and the unified dynamic package |
| Windows-Legacy project cannot find activity | Expected package compatibility | Unified package supports Windows and Cross-platform, not Windows-Legacy |
| Upload activity absent only from Agent/API project | Required file-upload filtering | Check `API.File.Upload.Required` |
| Download activity absent only from Agent/API project | File-download filtering | Check `API.File.Download` |
| `Response content too large` | JSON/Base64 payload exceeds 8 MB | Identify representation; reduce fields/records or use binary transfer |
| Binary transfer exceeds limit | Outside-JSON file exceeds 1 GB or provider is smaller | Compare exact byte count with both platform and provider limit |
| Activity times out around two minutes in Automation Cloud | Platform timeout/provider latency | Current Automation Cloud limit is 120 seconds |
| Builder test works but published activity is stale | Import/publish lifecycle | Compare local, imported, published, and generated activity versions |

### How Connector Methods Become Activities

A normal custom activity spans both definitions:

```text
app/element/element.json resource/method
        ↕ standardResourceName and method path/reference
app/element/standard-resources/<RESOURCE>.json
        ↕ Periodic activity generation
UiPath.IntegrationService.Activities in the consumer project
```

Inspect and validate from the connector root:

```bash
uip is connectors builder inspect --output json
uip is connectors builder validate --output json
```

The standard-resource (SR) method's `path` or `reference` must resolve to the
Integration Service resource slug such as `/contacts`, not a provider path such as
`/v3/accounts/{accountId}/contacts`. A broken link commonly produces an object in
Studio with no methods.

For a standalone curated activity:

- `metadata.method.<VERB>.curated` must exist and not be hidden;
- the method itself must not be hidden/deleted or outside its lifecycle;
- request/response fields need curated visibility;
- the imported/published revision must contain the same metadata.

Do not infer visibility from `element.json` alone or from a successful raw HTTP
request.

### Surface and Project Compatibility

There are three different questions:

1. **Connector catalog visibility**: can the tenant see the published connector?
2. **Activity project type**: did generation expose this method to the consumer
   surface?
3. **Runtime compatibility**: can the activity package run in the project runtime?

Periodic's default project names map approximately as follows:

| Generated project type | UiPath consumer surface |
|---|---|
| `Process` | Studio desktop/RPA process |
| `ProcessLibrary` | Studio desktop/RPA library |
| `TestAutomationProcess` | Test Automation project |
| `BusinessProcess`, `BusinessProcessLibrary` | Studio Web business process/library |
| `ProcessOrchestration`, `BusinessProcessOrchestration` | Maestro/process orchestration |
| `WebApp`, `BusinessWebApp` | UiPath Apps |
| `Agent` | Agent Builder |
| `Api` | API Workflows |

This mapping is a diagnosis aid. The live generated activity's
`compatibleProjectTypes`, tenant feature flags, connector/activity version, and
surface release are authoritative.

The unified `UiPath.IntegrationService.Activities` package is Windows and
Cross-platform compatible, not Windows-Legacy. Studio Desktop 2023.10 or later can
consume custom connectors through the unified package. An older Studio/package
case is a client compatibility branch, not an activity-definition defect.

#### Default Agent/API exclusions

Default activity-generation rules exclude these from `Agent` and `Api` projects:

| Activity family/tag | Effect |
|---|---|
| Generic Persistence **Wait for Event** | Wait activity is not generated for Agent Builder or API Workflows |
| Curated `API.File.Download` | Download activity is not generated for those project types |
| Curated `API.File.Upload.Required` | Required-upload activity is not generated for those project types |

An optional upload that can also accept a URL may have a different compatibility
contract. Inspect its actual tags and generated metadata rather than applying the
required-upload rule by name.

### Why Fields or Methods Are Absent

#### Method linkage

Check:

- `standardResourceName` points to the intended SR file;
- SR top-level resource name/path is consistent;
- `metadata.method.<VERB>.path` or `reference` resolves to the IS slug;
- method and SR verb agree;
- by-ID methods include the real primary-key contract;
- no `isHidden`, deleted, or lifecycle flag suppresses the method.

#### Curated field visibility

An SR field's plain `request`/`response` visibility is not enough for a curated
activity. It also needs `requestCurated` and/or `responseCurated` for that method.
Check:

- field dictionary key equals `field.name`;
- field is top-level under `fields`;
- method visibility includes the affected verb;
- required fields have correct `required`;
- `design.hidden` and field-action rules;
- reference/dropdown dependencies and `loadByDefault`.

If a field appears only after another literal selection, verify the field action.
A variable value can intentionally prevent a design-time reference lookup.

#### Stale generated activity

Trace:

```text
local revision → import response → published version/job → catalog connector
→ generated activity metadata → consumer project
```

Publishing promotes the imported definition; it does not upload later local edits.
After a publish reaches success, allow normal catalog/package propagation and
refresh the consumer. Repeated republishing obscures which version was tested.

### File Upload and Download Contracts

First classify the provider's wire contract:

| Representation | Connector implication |
|---|---|
| Base64 field inside JSON | Counts toward the 8 MB JSON limit; Base64 expansion makes the source file limit lower |
| Raw binary request/response | File is outside JSON; platform file ceiling applies |
| `multipart/form-data` | Must preserve boundary/content disposition, file field name, optional form fields, and MIME type |
| Upload session/chunking | Requires create-session, part/chunk requests, offsets, completion, and retry/idempotency behavior |
| URL source | Provider fetches the URL; allow-list the destination scheme/host and validate reachability, expiry, and authentication; never fetch an arbitrary workflow-supplied URL |

Capture the emitted request, not only the Builder activity design. Common failures:

- file parameter declared as body/string instead of file or multipart;
- activity body is wrapped in the wrong root;
- hook loses `multipart_hook_context_items` or boundary/content type;
- provider expects raw bytes but receives Base64 text;
- filename, content disposition, file field name, or MIME type is missing;
- response advertises JSON while returning bytes, or vice versa;
- download maps a binary stream into a fixed JSON schema;
- provider's own extension/size limit is smaller than UiPath's.

Treat filenames, paths, extensions, MIME types, URLs, and file content as untrusted:

- discard directory components, canonicalize the resulting basename, and reject
  path traversal, control characters, and reserved names;
- do not trust extension or caller-supplied MIME type as proof of content;
- for URL sources, revalidate every redirect and DNS result and reject loopback,
  link-local, private-network, and metadata-service destinations;
- never execute, render, or deserialize a diagnostic upload merely to identify it;
- record a redacted filename, byte count, permitted hash, MIME claim, and only a
  minimal magic-byte prefix when safe—never place customer file bytes in the
  evidence bundle.

Use a hook only when the declarative resource cannot express the transformation.
Every hook path must complete, and multipart context must be explicitly available
where required.

### Size and Timeout Limits

The following are current Automation Cloud working ceilings. Confirm them against
the affected deployment's current product documentation before selecting a limit
as the cause:

| Contract | Platform limit | Diagnostic meaning |
|---|---:|---|
| JSON data, including Base64 file content inside JSON | 8 MB | `Response content too large`; reduce records/fields or avoid JSON/Base64 |
| File handled outside JSON | 1 GB | Provider or connector may enforce a smaller limit |
| Integration Service activity/trigger execution | 120 seconds | Slow provider/upload can time out even below size limit |
| Trigger event payload | 8 MB | Large hydrated event can fail independently of poll success |

These are platform ceilings, not promises that a connector/provider accepts the
same size. Always apply the smallest of:

1. provider endpoint limit;
2. connector/activity validation;
3. current deployment's Integration Service limit;
4. caller/surface/runtime limit.

Base64 increases byte size by roughly one third before JSON overhead. Do not use an
8 MB source file in a Base64 JSON field. Measure the serialized payload or use a
small controlled file to establish the boundary.

Automation Suite/Public Sector/version-specific timeouts can differ. Record
deployment and version instead of copying the current Automation Cloud value into
every case.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that generation/file-contract branch. If evidence does not isolate one cause, stop
at the missing discriminator.

Correct the smallest proven layer: method/SR linkage, curation/field visibility,
generated project compatibility, publish propagation, transfer representation, or
provider/platform limit. Verify through the published connector on the same
consumer surface.

Do not silently publish, rebind a workflow, or change file handling. Present the
exact artifact field and proposed change, require approval, and verify against the
same runtime case. Retrying cannot heal an expected surface exclusion or a
provider/platform size ceiling.

### Activity or field absent

1. Record consumer surface, project type, Studio/package version, connector key,
   and published version.
2. Confirm the connector and activity are visible in another supported surface.
3. Inspect method linkage, curated block, field curated visibility, hidden flags,
   and generated `compatibleProjectTypes`.
4. For file/wait activities, apply the Agent/API exclusions.
5. Compare imported/published definition with local source.
6. Refresh the dynamic package after successful publish propagation.

### Upload fails

1. Record exact byte size, filename/extension, MIME type, and activity.
2. Classify JSON/Base64, raw, multipart, session/chunk, or URL-source transfer.
3. Compare provider, connector, platform, and caller limits.
4. Capture post-hook request metadata and provider response.
5. Test a small known-good file with the same type and connection.
6. Escalate the first layer where the request deviates.

### Download/response too large

1. Determine whether the provider returns JSON/Base64 or binary.
2. For JSON list responses, lower max records and filter/select fields.
3. For Base64 files, use an outside-JSON download contract if supported.
4. Check connector root/content-type mapping and the provider's content length.
5. Correlate elapsed time with the deployment timeout.

### Escalation Bundle

Include tenant/deployment, connector key and local/imported/published versions,
publish ID, consumer surface/project type, Studio and unified-package version,
generated `compatibleProjectTypes`, relevant element resource/SR method/field
metadata, validation output, connection ID, operation, trace ID/timestamp, and
redacted request/provider response. For files include representation, redacted
filename/extension, exact byte count, permitted hash, MIME claim,
boundary/field name or session/chunk metadata, provider limit, elapsed time, and
exact error—never include the file payload.
