---
confidence: medium
---

# Workday REST Connector Diagnostics

UiPath has two different Workday connectors. Identify the connector key before
diagnosing:

| Connector | Key | Contract |
|---|---|---|
| Workday | `uipath-workday-workday` | SOAP/WSDL; employee onboarding plus limited supplier/purchase objects |
| Workday REST | `uipath-workday-workdayrest` | OAuth 2.0, Workday REST APIs, absence management, WQL, HTTP Request, and polling |

This playbook focuses on **Workday REST**. Do not apply its OAuth URLs, WQL behavior,
or JSON schema rules to the SOAP connector.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the Workday REST-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The workflow selected the Workday REST connector when it requires the Workday SOAP connector, or vice versa.
- The Workday OAuth callback, authorization URL, token URL, REST endpoint, tenant, client, scope, or grant is incorrect.
- Connection provisioning failed to resolve the current worker or persisted the wrong Workday worker identity.
- The connected Workday identity lacks the security-group, domain, functional-area, data-source, field, or file permission required by the operation.
- The WQL data source, projection, filter, date format, limit, offset, ordering, or metadata sample is invalid.
- The generated activity is incompatible with the selected project type or file-download contract.
- The polling date/window, worker identity, paging, watermark, event mapping, or dedupe logic omitted the expected worker event.

## Investigation

### Fast Symptom Router

| Symptom | Leading diagnosis | First check |
|---|---|---|
| User configured WSDL URL/username/password | Wrong connector playbook | Confirm SOAP connector key |
| OAuth redirects to Workday home page | Redirect URI mismatch | Compare exact registered and displayed callback URI |
| Connection appears created but current-worker activities fail | `/workers/me` provisioning error was swallowed | Inspect `workerID`, connection identity, and original `/workers/me` response |
| WQL activity returns max 1,000 | Connector adds default `LIMIT 1000` | Add an intentional LIMIT/paging strategy |
| Discovered object returns only `workdayID` | Field cache missing/empty | Refresh object metadata and inspect data-source field API |
| Expected custom/calculated field absent | Projection safety filter | Request the field explicitly and inspect skip/max-field config |
| Records repeat/skip by page | Offset math | Verify `(page - 1) * pageSize` and total |
| Download Invoice PDF absent in Agent/API | Periodic file-download exclusion | Inspect live compatibility metadata |
| Worker hired/terminated trigger misses event | Date-equality polling | Compare Workday date and GMT poll day, not `updated` time |

### Authentication

Workday REST supports OAuth 2.0 authorization code. Required connection values are:

- REST API endpoint;
- Authorization URL;
- Token URL;
- Client ID;
- Client Secret;
- Tenant name.

Example shapes:

```text
REST API endpoint:
https://<host>/ccx/api/v1/<tenant>

Token URL:
https://<host>/ccx/oauth2/<tenant>/token
```

The Workday API client must:

- use Authorization Code Grant;
- issue Bearer tokens;
- register the callback shown by UiPath exactly;
- use the provider-supported refresh-token lifetime and rotation policy appropriate
  for unattended automation, with revocation available and tokens stored only in
  the connection secret store;
- include every functional-area scope used by the workflow;
- include **System - Workday Query Language** for WQL.

#### Redirect to Workday home page

This is the documented symptom of a redirect URI mismatch. Compare scheme, host,
path, region, and trailing slash. The current Automation Cloud shape is:

```text
https://<UiPath base URL>/provisioning_/callback
```

Do not troubleshoot tenant permissions until Workday returns an authorization code.

#### Endpoint parsing

The connector derives:

- tenant name from the final path segment of `apiEndpoint`;
- host from the endpoint URL;
- API base as `<scheme>://<hostname>/ccx/api`;
- refresh URL from the configured token URL.

Therefore an endpoint with an extra trailing slash, query string, wrong final path
segment, or non-canonical hostname can produce the wrong tenant/base URL even if the
OAuth client itself is valid.

Capture all three configured URLs and the derived host/tenant/base URL.

#### Provisioning can hide `/workers/me` failure

During provisioning the connector calls:

```text
/absenceManagement/v1/<tenant>/workers/me
```

If Workday returns an error, the post-hook currently converts it to HTTP `200` with
an empty body so that some Integration System User scenarios can still provision.
That means a connection can appear valid while:

- `workerID` is missing;
- connection identity falls back to `Workday`;
- “current logged-in worker” and personal time-off activities fail later.

If those activities fail, inspect connection configuration for `workerID` and replay
`workers/me`. The likely causes are tenant endpoint, current user not mapped to a
worker, or insufficient absence-management scope/security—not a generic activity
mapping problem.

The connector's `/ping` hook returns a synthetic success and does not call Workday.
A successful ping alone does not prove token, tenant, scope, or worker identity.

### WQL Discovery and Queries

#### Object/field discovery path

Current Udon supports Workday WQL data-source and field metadata even though older
top-level metadata flags can appear static. It:

1. reads Workday WQL data sources;
2. limits discovery to configured allowed primary business objects;
3. fetches field metadata 100 fields per request;
4. fetches remaining field pages in parallel;
5. builds standard resources and caches safe selectable fields.

If Workday returns `404`/empty metadata for a data source, the hook returns an empty
successful metadata response so Periodic can fall back to static metadata. This can
look like “object exists but has no dynamic fields.”

Capture the data-source ID, all field-metadata pages, and whether the response was a
fallback.

#### Safe projection rules

To avoid oversized/unsafe Workday responses, the runtime:

- defaults to at most 20 safe fields per object (`workday.default.max.fields`);
- falls back to `workdayID` if no cached safe fields exist;
- removes `[*]` from multi-instance field names before WQL;
- collapses complex fields such as `manager.id`/`manager.descriptor` to a base
  projection;
- limits a generated projection to at most 100 base fields;
- drops excess `cf_` custom fields first, then excess currency base fields;
- maintains a configured calculated-field skip list.

This is an intentional diagnosis branch for “field is visible in Workday metadata
but not returned by List Records.” Request the field explicitly with the operation's
fields parameter, confirm it is WQL-selectable, and keep the response below platform
limits.

#### Query construction

For generated object list operations, Udon constructs WQL with selected fields and
optional WHERE, then sends pagination as URL parameters:

```text
limit=<pageSize>
offset=(pageNumber - 1) * pageSize
```

For the curated **Execute WQL Query** activity, a JavaScript hook adds:

```text
LIMIT 1000
```

when the customer query has no LIMIT. It removes a trailing semicolon before
appending the clause.

Recurring branches:

| Evidence | Diagnosis | Unblock |
|---|---|---|
| Exactly 1,000 rows from Execute WQL | Default limit | Add deliberate LIMIT/filter and paging/query partitioning |
| Page 1 correct, page 2 repeats | Page number not advanced or offset lost | Capture emitted limit/offset |
| Only `workdayID` projected | Empty/corrupt field cache | Refresh metadata and inspect cache/data source |
| Custom/calculated field absent | Safety filtering | Request explicitly and confirm Workday allows projection |
| `Failed to fetch payload during metadata generation...` | Sample WQL metadata call failed | Fix WQL scope, data source, field security, or tenant |

Do not add every field to work around metadata issues; Workday and Integration
Service response-size/time limits make that unreliable.

### Activities and UiPath Surfaces

Curated Workday REST activities include:

- Search Workers by Name or ID
- List Inbox Tasks for a Worker
- List All Tasks in Your Inbox
- Approve or Reject Inbox Task
- Create Personal Time-off Request
- Execute WQL Query
- Get Instance Details
- Download Invoice PDFs

The connector also exposes supported absence-management and dynamically discovered
WQL object activities plus HTTP Request.

#### Current-worker versus specified-worker activities

Activities under `me` require successful `/workers/me` resolution and connection
`workerID`. Activities accepting a Worker ID can work for an integration principal
even when “me” resolution is unavailable. Use the correct family; do not substitute
the integration user's username for Workday worker ID.

#### Hidden resources

Repository history intentionally hides generic variants of:

- `me/inboxTasks`;
- worker eligible absence types;
- some underlying endpoints replaced by curated activities.

If an expected generic CRUD activity is absent but the curated activity exists, this
is intentional. Inspect `isHidden` and deployed version.

#### Surface compatibility

Workday REST has no connector-wide project override. Apply the common rules in
[connector.md](./connector.md): **Download Invoice PDFs** follows the download
exclusion, and event waits follow the persistence exclusion.

No file-upload curated activity is present in this Workday REST connector.

### Files and Date Formats

#### Download Invoice PDFs

This is a binary `application/octet-stream` download by Workday resource ID. If the
activity is absent, inspect surface compatibility. If it executes but returns bad
content:

1. call the same invoice endpoint as the connected principal;
2. record response content type, length, disposition, and first bytes;
3. confirm the input is the Workday resource ID;
4. check whether a relay/proxy transforms the binary body;
5. distinguish Workday `403` data security from connector mapping.

#### Date/time gotchas

If Workday rejects a date, capture the final serialized JSON and compare it with the
specific resource schema. Do not globally convert every Workday date to the same
format; date-only and datetime fields have different contracts.

The leave-of-absence endpoint supports comma-separated `leaveType` values.

### Triggers

Workday REST exposes two polling events:

| Event | Query rule | Identity |
|---|---|---|
| Worker Hired | WQL `hireDate = <current GMT date>` | `worker.id` |
| Worker Terminated | WQL `terminationDate = <current GMT date>` | `worker.id` |

Both poll every five minutes. These are **date-equality** queries, not generic
LastModifiedDate polling.

For a missed event:

1. capture the Workday hire/termination date and tenant timezone;
2. run the exact WQL for the GMT date used by the poll;
3. confirm the integration principal can read `allWorkers` and every selected field;
4. inspect result `worker.id`;
5. trace poll pages, identity, and dedupe;
6. confirm downstream job creation.

A worker backdated to yesterday or future-dated will not match today's query.
Timezone boundaries can also move an expected event to a different poll date.

Wait for Event compatibility is separately restricted in Agent/API projects by
Periodic defaults.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching action-map row. If the evidence does not isolate one cause, stop at the
missing discriminator.

Correct the smallest proven Workday REST branch: callback/endpoint, OAuth scope,
worker provisioning, WQL metadata/projection, pagination, date format, file
download, or polling. Verify with the same Workday identity and tenant.

### Diagnosis-to-Action Map

| Proven finding | Owner and unblock | Healing decision |
|---|---|---|
| Callback, authorization/token endpoint, tenant, or derived base URL is wrong | Workday connection owner/admin: correct the exact endpoint/tenant contract and reauthorize | Human action; do not redirect token exchange to an unverified host |
| `/workers/me` or the target resource is rejected by scope/security domains | Workday admin: correct API client scopes and security-group/domain access | Human approval; do not automatically broaden Workday security |
| WQL data source, projection, filter, date format, limit, or offset is invalid | Workflow developer: correct the activity/query input using provider metadata | Source-change recommendation only |
| Workday returns the worker/field/page/file but connector discovery or output drops it | Connector team: correct WQL discovery, schema, pagination, or binary mapping | Escalate with raw Workday and transformed output |
| Poll query returns the worker event inside the GMT window but no event is emitted | Connector team after watermark, identity, paging, and dedupe are proved | Escalate; do not move the watermark without evidence |

### Escalation Bundle

Include:

- connector key proving SOAP versus REST;
- tenant/region, UTC time, trace ID, connector/activity version, UiPath surface;
- REST endpoint, authorization URL, token URL, derived host/tenant/base URL;
- connection ID, OAuth scope names, Workday API client and acting user/ISU (no
  secrets/tokens);
- `/workers/me` provider response and stored `workerID`/identity;
- Workday security groups/domains/functional scopes for the exact resource;
- final WQL, data-source ID, selected fields, limit, offset, all pages, and total;
- raw Workday response and connector-transformed response;
- for downloads: invoice ID, content type/length/magic bytes;
- for triggers: worker ID, hire/termination date, GMT poll date/query, pages,
  identity, and dedupe result.
