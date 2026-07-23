---
confidence: medium
---

# ServiceNow Connector Diagnostics

Use this for connector key `uipath-servicenow-servicenow`. The connector uses the
ServiceNow Table API and supports cloud and HTTPS-reachable self-hosted instances.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the ServiceNow-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The ServiceNow site URL, legacy subdomain, OAuth client, credential, or authentication policy is incorrect.
- The ServiceNow instance is hibernating, unreachable, or returned HTML instead of the expected JSON API response.
- The connected user cannot read `sys_db_object`, `sys_dictionary`, the target table, record, field, or attachment.
- The workflow supplied the wrong table, `sys_id`, reference value, `sysparm_query`, limit, or offset.
- The connector normalized or transformed the ServiceNow response, reference field, page, or attachment incorrectly.
- The generated activity is incompatible with the selected UiPath project type.
- The polling query, GMT timestamp window, paging, watermark, or dedupe logic omitted the expected record.

## Investigation

### Fast Symptom Router

| Symptom | Meaning | First check |
|---|---|---|
| `Invalid Domain. Please enter only domain (devxxx), not the full URL` | Legacy subdomain validation received a URL/HTML response | Determine whether the deployed auth screen expects `siteUrl` or legacy `servicenow.subdomain` |
| `Please verify the user has the required permissions` during creation | Provisioning call to `sys_db_object` returned `403` | Grant metadata-table read ACLs |
| `Instance is in Hibernating Mode...` or HTML instead of JSON | ServiceNow developer instance is asleep/unavailable | Wake the instance and retry the same call |
| Connection succeeds but object is missing | Table discovery visibility | Check `sys_db_object`, `sys_dictionary`, table ACL, and `ws_access` |
| Field missing or read-only unexpectedly | Dictionary/ACL-derived metadata | Compare `sys_dictionary` as the connection user |
| Reference input/output shape differs | ServiceNow reference flattening | Use the value field for writes; link fields are read-only |
| List returns empty after large offset | ServiceNow “records matching query not found” normalization | Check `sysparm_query`, `sysparm_offset`, and previous page |
| Attachment upload is too large | Base64 conversion runtime limit | Compare original byte count with deployed Udon `maxFileSize` |
| Trigger misses the newest record | Five-second upper safety window | Wait for the next poll and compare `sys_updated_on` |

### Authentication

#### Supported types

| Authentication | Required input | Gotchas |
|---|---|---|
| OAuth 2.0 authorization code | Full Site URL, Client ID, Client Secret | Callback URL must match the ServiceNow OAuth client exactly. Supported from ServiceNow Istanbul onward; newer releases can use Machine Identity Console configuration. |
| OAuth 2.0 password grant | Site URL, username, password, Client ID, Client Secret | The ServiceNow user and OAuth application must both be valid. Diagnose token exchange separately from table ACLs. |
| Basic | Full Site URL, username, password | Useful for validation/POCs, but account lock, IP policy, SSO policy, or disabled basic auth can reject it. |

The connector constructs API base URL as:

```text
https://<site>/api/now
```

Use the full canonical Site URL on the current connection screen, for example
`https://dev12345.service-now.com`. Do not append `/api/now`.

Older definitions used a subdomain-only field. The legacy validation hook treats an
HTML response as an invalid domain and emits the exact `Invalid Domain...` error.
When investigating an upgraded connection, capture the configuration field names
and deployed connector version instead of repeatedly changing between full URL and
subdomain.

#### Connection creation validates metadata access

The provisioning resource calls:

```text
/api/now/v1/table/sys_db_object?sysparm_fields=sys_name
```

A `403` is rewritten to `Please verify the user has the required permissions`.
This means valid credentials are insufficient: the connector needs metadata access
to construct its object/activity catalog.

Minimum read access commonly required:

- `sys_db_object`
- `sys_dictionary`
- `sys_choice`
- `sys_user`
- `sys_glide_object`

The connection user also needs CRUD ACLs for every target business table. For
incident use cases, metadata access plus read/write on `incident` is required.

#### Auth decision tree

1. If authorization/token exchange fails before provisioning, verify callback URL,
   client ID/secret, grant type, active account, and ServiceNow OAuth application.
2. If token/login succeeds but provisioning returns `403`, fix metadata ACLs.
3. If the response is HTML or mentions hibernation, wake the instance.
4. If connection succeeds but one table fails, fix that table/field ACL; do not
   reauthorize a healthy token.
5. If OAuth uses the wrong browser identity because of SSO, retry in a private window
   and authenticate as the intended integration user.

The connector uses subdomain as OAuth connection identity, and
`<username>-<subdomain>` for Basic/password-grant identities.

### Metadata and Permissions

#### How objects are discovered

The connector reads `sys_db_object`, including table name, label, parent table,
`sys_id`, and `ws_access`. Udon:

- skips views that do not support the metadata API;
- resolves parent-table metadata;
- caches table/parent details on the connection instance;
- queries `sys_dictionary` to generate fields;
- marks custom tables/fields by the `u_` prefix;
- derives required/read-only/createable/updateable properties from ServiceNow
  dictionary metadata.

If an object is missing:

1. Query `sys_db_object` as the connected principal.
2. Confirm the table has web-service access (`ws_access`) and is not an unsupported
   view.
3. Confirm read access to `sys_dictionary` for the table and its parents.
4. Refresh connector metadata after ACL/table changes.
5. Compare the generated standard resource with the raw table/dictionary response.

#### Required and read-only fields can differ from the ServiceNow form

ServiceNow maintains form/UI policy separately from API dictionary/ACL behavior.
Udon deliberately lets ServiceNow validate some write permissions at execution time.
Therefore:

- a field mandatory in the form is not automatically mandatory in the Table API;
- UI Policy/Client Script behavior is not proof of REST API behavior;
- a field visible in a browser can be hidden from the integration principal;
- a field in generated metadata can still be rejected by a field ACL.

Use the same user, table, operation, and raw REST request when comparing.

#### Reference fields

ServiceNow responses can return reference fields as:

```json
{
  "link": "https://instance.service-now.com/api/now/table/sys_user/...",
  "value": "sys_id"
}
```

Udon flattens/normalizes complex fields for stable activity types. Link fields are
read-only; the value is the writable identifier. If an activity writes the whole
reference object and ServiceNow says a string/sys_id is expected, map only the value.

#### Hibernating instances

Developer instances can return HTML instead of JSON. Udon maps this to a `502` with
messages such as:

- `Instance is in Hibernating Mode, Please wake up your ServiceNow Instance.`
- `Service Unavailable, be sure to wake up your ServiceNow Instance.`

Wake the instance and prove the metadata endpoint returns JSON before changing
schema or authentication.

### Activities and UiPath Surfaces

Curated activities include:

- Create, List, and Update Incident
- Search Incidents by Incident Number
- Create, Get, List, and Update Incident Task
- Search Users by Email or Name
- Add, Delete, Download, Get, and List Attachments

Generic CRUD activities are generated for discovered tables allowed by the connected
user.

#### Surface compatibility

ServiceNow has no connector-wide project override. Apply the common rules in
[connector.md](./connector.md): **Add Attachment**, **Download Attachment**, and
event waits follow the required-upload, download, and persistence exclusions.

The connector hides the superseded Incident Task list variant and exposes the
curated activity on the generic incident-task object. Duplicate JSON definitions do
not mean duplicate activities should appear.

### Attachments

#### Add Attachment

The Udon Jira/ServiceNow-style upload path converts the UiPath file to a Base64 value
inside a JSON payload before calling ServiceNow. This matters:

- the file expands by roughly one third during Base64 encoding;
- the operation is subject to Udon's configured `maxFileSize`;
- it is also subject to Integration Service's 8 MB JSON processing limit and
  ServiceNow attachment properties;
- the source comment describes an intended 5 MB guard, but the implementation uses
  the deployed runtime setting. Capture the exact limit/error rather than assuming
  five MB.

Exact runtime errors include:

- `Required file upload items are empty`
- `The given file exceeds the size limit of <n> MB`
- `Please provide valid request body`

The generic legacy path posts to `ecc_queue`, then searches `sys_attachment` by
table sys_id, creation time, and filename to return attachment metadata. If the file
exists in ServiceNow but the activity output is wrong, capture both the `ecc_queue`
response and follow-up `sys_attachment` query/result.

#### Download Attachment

The download flow can make an additional call to `sys_attachment` to recover the
true content type, Base64-decodes the payload, and sets binary response headers.

For corrupted or empty downloads, capture:

- attachment `sys_id`;
- source table and record `sys_id`;
- `sys_attachment` metadata and content type;
- pre-decode provider body length;
- post-decode content length and magic bytes;
- connector/activity version and consumer surface.

Do not treat Base64 JSON and binary-stream limits as the same limit.

### Queries and Response Transformations

#### Query/filter behavior

ServiceNow uses `sysparm_query`, `sysparm_limit`, and `sysparm_offset`. The connector
can construct encoded queries from the activity filter builder.

When data is missing:

1. Capture the final `sysparm_query`, not only the designer filter.
2. Confirm carets, ORDERBY clauses, and URL encoding were not double encoded.
3. Record every `sysparm_offset` and `sysparm_limit`.
4. Run the same Table API request as the connection user.
5. Compare `X-Total-Count`/returned-count metadata where available.

ServiceNow's “Records matching query not found. Check query parameter or offset
parameter” error can be normalized to an empty list. An empty page after a large
offset can therefore be expected end-of-data rather than a mapping defect.

Connector `1.4.0` routes supported query behavior through the unified `/v1/query`
engine. For regressions, compare whether the tenant is before or after that version
and capture the generated query.

#### Response cleanup

Udon flattens complex reference values and converts some string values to numeric
types to keep activity request/response metadata consistent. If a successful
provider response fails mapping:

1. identify the exact field and raw ServiceNow type;
2. capture raw provider JSON and transformed connector JSON;
3. check whether it is a reference, choice, currency, number, date, or custom field;
4. compare dictionary metadata and activity output schema;
5. refresh metadata before escalating.

### Triggers

The verified connector exposes polling for:

- Incident Created/Updated
- Incident Task Created/Updated
- generic Record Created/Updated on those resources

Both use:

- five-minute polling;
- `sys_id` as identity;
- GMT timestamps;
- a lower bound on `sys_updated_on`;
- an upper safety bound five seconds before “now”.

The effective filter is structurally:

```text
sys_updated_on > <last poll>
AND sys_updated_on < <now minus 5 seconds>
```

The five-second upper bound prevents racing records that are still being committed.
A record updated inside that safety window should be picked up by the next poll.

For a missed event:

1. retrieve the exact `sys_id` as the connected user;
2. record `sys_created_on` and `sys_updated_on` in GMT;
3. run the exact encoded poll query;
4. check every page/offset;
5. compare watermark, event operation, identity, and dedupe;
6. then trace downstream job creation.

If a record is updated repeatedly with the same `sys_id`, distinguish provider
return from poller deduplication. A UI timestamp displayed in local time is not the
poll comparison value.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching action-map row. If the evidence does not isolate one cause, stop at the
missing discriminator.

Correct the smallest proven ServiceNow branch: instance state, authentication,
metadata ACL, table/field access, query translation, attachment contract, or poll
window. Verify using the same ServiceNow user and table.

### Diagnosis-to-Action Map

| Proven finding | Owner and unblock | Healing decision |
|---|---|---|
| Developer instance returns hibernation/HTML instead of the expected JSON API | ServiceNow instance owner: wake or restore the instance, then repeat the same metadata/API call | Bounded retry only after the instance is confirmed available |
| Provisioning cannot read `sys_db_object`, or record/field ACL rejects the connected user | ServiceNow admin: grant only the metadata/table/field access required by the operation | Human approval; never automatically add broad roles |
| Emitted `sysparm_query`, table, `sys_id`, limit, or offset differs from workflow intent | Workflow developer: correct the activity input/filter using the same connection | Source-change recommendation only |
| Provider JSON contains the field/page/attachment but the transformed connector output drops it | Connector team: correct response, pagination, or attachment mapping | Escalate with redacted provider and transformed payloads |
| Poll query returns the record inside the window but no event is emitted | Connector team after watermark, mapping, and dedupe evidence are pinned | Escalate; do not reset the watermark blindly |

### Escalation Bundle

Include:

- tenant, region, UTC time, request/trace ID;
- connector/activity version and exact UiPath project/surface;
- authentication type, ServiceNow release, canonical instance host, connection ID,
  and connected username (no password/tokens);
- raw provisioning response from `sys_db_object`;
- relevant roles and record/field ACL result;
- table name, parent table, `sys_id`, operation, final path, method,
  `sysparm_query`, limit, and offset;
- raw ServiceNow JSON and transformed connector JSON;
- dictionary metadata for the exact failing field;
- for files: original size, Base64/binary representation, runtime size limit,
  attachment metadata, and content type;
- for triggers: exact `sys_id`, GMT timestamps, poll bounds, pages, watermark, and
  dedupe result.
