---
confidence: medium
---

# Oracle NetSuite Connector Diagnostics

Use for connector key `uipath-oracle-netsuite`.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the NetSuite-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- A NetSuite consumer key, consumer secret, token ID, token secret, account ID, application, user, or role binding is incorrect.
- The token role lacks the required SuiteTalk, record, subsidiary, SuiteAnalytics, or file permission.
- The integration exceeded its allocated NetSuite concurrency.
- The workflow supplied a display value instead of a NetSuite internal ID.
- The SuiteQL query, literal schema sample, limit, offset, ordering, or custom-field contract is invalid.
- The generated activity is incompatible with the selected project type or the file operation exceeds a provider/platform contract.
- The poll query, role visibility, timestamp, timezone, paging, or dedupe logic omitted the expected record.

## Investigation

### Fast Symptom Router

| Symptom | Leading diagnosis | First check |
|---|---|---|
| `At least one of the Consumer credentials, Token credentials, or Account ID is incorrect...` | Connector mapped NetSuite `Invalid login attempt.` | Validate all five TBA values and their application/user/role relationship |
| Token works as admin but not integration role | Wrong/insufficient token role | Confirm the token was generated for the intended single role |
| Intermittent failures under parallel load | NetSuite concurrency allocation | Check the integration record; connector default is five concurrent sessions |
| Object activity needs an “ID” not visible in UI | NetSuite internal ID | Enable Show Internal IDs and pass `internalId` |
| Update Customer says ID contains space | Connector pre-hook validation | Pass the internal ID without whitespace |
| SuiteQL schema button disabled/fails | Query is variable/expression or invalid | Use a literal SELECT query to generate schema |
| SuiteQL page rejected | Offset not divisible by limit | Use aligned offset/limit pairs |
| File upload/download absent in Agent/API | Periodic file compatibility rules | Inspect live `compatibleProjectTypes` |
| Trigger misses record | Role visibility, `lastModifiedDate`, timezone, paging | Run exact query with same token role |

### Authentication and Permissions

#### Supported authentication

The connector exposes one type:

```text
Token Based Authentication
```

Required values:

- Consumer Key
- Consumer Secret
- Access Token ID
- Access Token Secret
- Account ID

Legacy username/password properties remain in the connector configuration, but the
current public connector does not expose Basic authentication. Do not recommend
Basic based only on those dormant properties.

The connector maps NetSuite provider message `Invalid login attempt.` to HTTP `401`
with:

```text
At least one of the Consumer credentials, Token credentials, or Account ID is
incorrect. Click 'Help' below to review the prerequisites for creating a connection
successfully.
```

This message intentionally cannot identify which secret is wrong. Validate the
credential chain rather than rotating values randomly.

#### Required NetSuite setup

1. Enable Token-Based Authentication.
2. Create an integration record.
3. Enable Token-Based Authentication and TBA Issue Token Endpoint on that record.
4. Create a dedicated role with User Access Tokens and SOAP Web Services plus
   permissions for the required records/files/searches.
5. Assign the role to a dedicated integration employee/user.
6. Generate the access token for that exact application, user, and role.
7. Retrieve the canonical Account ID.
8. Enable Show Internal IDs.

UiPath guidance specifically recommends a new user linked to a single role. An
existing user with several roles can cause the web-service role to differ from the
role assumed during setup.

#### Account ID gotcha

Use the NetSuite Account ID, not the company name or URL. Public guidance states
that hostname-compatible account names cannot contain underscores. Preserve any
sandbox/account suffix exactly as NetSuite shows it.

#### `401` versus `403`

| Evidence | Diagnosis |
|---|---|
| Mapped `Invalid login attempt.` | Consumer key/secret, token ID/secret, Account ID, token/application/user/role binding, or TBA feature |
| Authentication succeeds but one record type/field/file is denied | Role permission, subsidiary restriction, employee restriction, or feature permission |
| Admin succeeds but integration token fails | Role/visibility difference, not connector-wide outage |

Do not test with an Administrator browser session as final proof. Use the same token
role.

#### Concurrency

NetSuite applies account/integration concurrency limits. UiPath documentation states
that the connector defaults to five concurrent sessions, configurable on the
NetSuite integration record.

If failures correlate with parallel jobs:

1. capture start/end time of every overlapping call;
2. capture NetSuite concurrency/rate error and request ID;
3. inspect the integration record's concurrency allocation;
4. ensure no other workflow shares the same credentials unexpectedly;
5. serialize/reduce concurrency or allocate more capacity within account limits.

Reauthentication does not fix a concurrency limit.

### Activities and UiPath Surfaces

Important curated activities include:

- Create/Update Customer and Vendor;
- Create/Update Contact;
- Create/Update Support Case;
- basic company/individual customer and vendor variants;
- Search Customers;
- Search Items;
- Execute SuiteQL Query;
- Upload File, Download File, Attach File, and Detach File.

Generic activities cover many NetSuite record types. Most use `internalId` as the
primary key.

#### Basic versus full curated customer/vendor activities

Several “Basic” activity variants explicitly omit address-book details. If a user
expects address creation/update from **Create Basic Company Customer** or similar,
the absence is by contract. Use the full Customer/Vendor activity or a supported
generic/HTTP operation.

#### Internal IDs

Customer-facing numbers/names are not NetSuite `internalId`. Enable Show Internal
IDs and use the value expected by the resource. The current Update Customer hook
returns:

```text
Customer ID cannot contain space
```

when the path ID includes whitespace.

#### Surface compatibility

NetSuite has no connector-wide project override. Apply the common rules in
[connector.md](./connector.md): **Upload File**, **Download File**, and event waits
follow the required-upload, download, and persistence exclusions.

Attach/Detach File operate on existing NetSuite file IDs and record IDs and are not
the same as transferring file bytes.

### SuiteQL

#### Design-time schema generation

**Execute SuiteQL Query** requires a SELECT query and offers **Generate output
schema**. The button is enabled for a literal query, not an unresolved workflow
expression.

Correct sequence:

1. enter a valid literal SELECT query without variables;
2. generate output schema;
3. only then replace values with variables if the projected columns/types remain
   unchanged;
4. regenerate schema whenever selected columns or aliases change.

Exact design-time message on failure:

```text
Could not generate custom fields schema. Provider message: <ERROR>.
Please validate Query field input and try again
```

The failure may be query syntax, table/column permission, SuiteAnalytics feature,
role visibility, or response schema—not connection authentication.

#### Limit/offset rule

The activity guidance states:

```text
offset must be divisible by limit
```

Valid examples:

- Offset `0`, Limit `5`
- Offset `20`, Limit `10`

Invalid example:

- Offset `15`, Limit `10`

For missing rows:

1. capture literal query and generated schema;
2. record limit/offset for every page;
3. use deterministic ORDER BY;
4. compare NetSuite `items`, count, offset, totalResults, and links;
5. check role visibility and SuiteAnalytics Workbook permission;
6. keep the response below Integration Service's 8 MB JSON limit.

Without deterministic ordering, offset pagination can shift while records change.

#### Custom fields

If a custom field is absent:

1. confirm the role can read it;
2. use its internal/script ID, not display label;
3. regenerate schema with a literal query that projects it;
4. refresh connector/activity metadata;
5. compare the provider field with the generated activity schema.

### Files

#### Upload File

The connector resource accepts:

- required file;
- required `folderId`.

It uploads to the NetSuite file cabinet and returns `internalId`. If upload fails:

1. verify the role has Documents and Files permissions;
2. verify the destination folder internal ID and folder restrictions;
3. capture original filename, size, MIME type, and multipart handling;
4. distinguish Periodic surface exclusion from provider `403`;
5. inspect Integration Service/runtime upload limit and NetSuite limit.

#### Download File

Download uses `/files/{id}` and returns `application/octet-stream`. Pass file
`internalId`, not path/name.

For corrupt/empty downloads, capture provider content type/length, content
disposition, first bytes, and relay/proxy behavior.

#### Attach and Detach

These operations use:

```text
/{objectName}/{recordId}/files/{fileId}
```

All three identifiers are required. Recurring errors come from:

- singular/plural or wrong object API name;
- customer-facing record number instead of internal ID;
- file ID not visible to the role;
- record type does not support that attachment relationship.

Uploading a file to the cabinet does not automatically attach it to a record.

### Triggers

NetSuite exposes polling-based Created/Updated events for many record types. The
common contract is:

```text
lastModifiedDate > <LAST_POLL_DATE>
```

with:

- five-minute interval;
- `internalId` identity;
- record-specific list resource;
- File using `modified` rather than `lastModifiedDate`.

Curated event families include Customer, Vendor, and Support Case created/updated.

For a missed event:

1. use the same token role to retrieve the record;
2. record `internalId` and `lastModifiedDate`/`modified`;
3. run the exact connector query;
4. capture all pages and ordering;
5. compare poll watermark/timezone and event classification;
6. trace dedupe and downstream delivery.

The curated Customer/Vendor/Support Case polls route through internal transformed
resources with `includeRaw=true`; capture both raw and transformed records if an
event is returned by NetSuite but not emitted.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching action-map row. If the evidence does not isolate one cause, stop at the
missing discriminator.

Correct the smallest proven NetSuite branch: TBA credential chain, role/access,
account ID, concurrency allocation, internal ID, SuiteQL contract, file operation,
or poll query. Verify with the same token role and record.

### Diagnosis-to-Action Map

| Proven finding | Owner and unblock | Healing decision |
|---|---|---|
| Consumer/token/account/role chain is inconsistent or the account ID format is wrong | NetSuite connection owner/admin: correct the exact TBA relationship and reauthorize/test the same role | Human action; never disclose or regenerate credentials in diagnosis |
| Valid token role lacks record, subsidiary, SuiteAnalytics, or file access | NetSuite admin: grant the minimum required permission to that role | Human approval; do not switch to an administrator role as a workaround |
| Concurrency limit is proven by overlapping calls and NetSuite response | NetSuite admin/workflow owner: reduce parallelism or allocate concurrency | Policy-controlled backoff only when the operation is safe to retry |
| SuiteQL text, internal ID, limit/offset, or stable ordering is wrong | Workflow developer: correct the query/input and verify against the same record | Source-change recommendation only |
| Provider page/file/record is correct but generated schema or transformed output is not | Connector team: fix schema, mapping, pagination, or file handling | Escalate with raw and transformed evidence |

### Escalation Bundle

Include:

- tenant/region, UTC time, trace/request ID, connector/activity version, UiPath
  surface/project type;
- Account ID, integration record ID/name, token user and role IDs, enabled feature
  names—never consumer/token secrets;
- concurrency allocation and overlapping call timeline;
- record type, `internalId`, subsidiary/restriction context, operation;
- SuiteQL text, generated schema, limit/offset/order, every provider page;
- raw provider response and connector-transformed response;
- for files: folder ID, file ID, record/object IDs, byte size, MIME type, content
  length/magic bytes;
- for triggers: record internal ID, modified timestamp, exact query, watermark,
  pages, and dedupe result.
