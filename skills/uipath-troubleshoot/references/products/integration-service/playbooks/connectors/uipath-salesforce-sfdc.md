---
confidence: medium
---

# Salesforce Connector Diagnostics

Use for connector key `uipath-salesforce-sfdc`.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the Salesforce-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- Salesforce blocked or has not propagated the connected/external app, client, or selected OAuth grant.
- The Salesforce token was revoked or refresh policy, audience, environment, instance, or Run As identity is wrong.
- The Salesforce edition or connected principal lacks API, object, field, record, or file access.
- The workflow supplied a business identifier where a Salesforce record `Id` is required.
- The generated SOQL, selected fields, projection, date predicate, or pagination contract is invalid.
- The workflow and connector disagree about Salesforce Files, `ContentVersion`, classic `Attachment`, or bulk-job state.
- The generated activity is incompatible with the selected UiPath project type.
- The polling SOQL, watermark, paging, event identity, or dedupe logic omitted the expected record event.

## Investigation

### Fast Symptom Router

| Symptom | Leading diagnosis | First check |
|---|---|---|
| `OAUTH_APPROVAL_ERROR_GENERIC` / app blocked | Salesforce connected/external app policy | Install/approve the app or use an authorized BYOA app |
| `invalid_client_id` | Wrong/unpropagated client or app policy | Wait for app propagation, then recheck key, secret, and policies |
| Connection later expires unexpectedly | Refresh policy or five-token-per-user/app limit | Inspect active OAuth approvals and refresh-token policy |
| `API not enabled for this organization or partner` | Edition/profile lacks API access | Confirm edition and `API Enabled` permission |
| Object absent | Object permission or unsupported object operations | Test describe API as connection user and force-refresh metadata |
| Field absent | Field-level security | Test object describe and field permission as connection user |
| Record ID like Case Number fails | Activity expects Salesforce `Id` | Search by business key, then pass returned `Id` |
| Search returns only 200 rows per page | `FIELDS(ALL)` behavior | Select explicit fields or follow `nextRecordsUrl` |
| File visible in UI but cannot download | API-level file permission/storage type | Distinguish `ContentVersion` from classic `Attachment` |
| Advanced trigger rejects query | SOQL parser or date-filter contract | Remove customer date predicate and ensure valid `SELECT ... FROM` |

### Authentication

#### Supported methods

| Connector value | User-facing method | Required inputs and gotchas |
|---|---|---|
| `oauth2` | OAuth 2.0 authorization code | Production/Sandbox, Salesforce login. Public app normally requests `full refresh_token`. Salesforce admin can block uninstalled apps. |
| `oauth2Password` | OAuth 2.0 password | Client key/secret, username, password, optional security token. The connector supports either the token field or password+token convention. This grant is deprecated/blocked by default for new orgs and is scheduled for Salesforce Winter '27 retirement. |
| `jwtOauth` | JWT bearer / PAT | Base64-encoded private key, audience, issuer/client ID, subject/username, app credentials, environment. Audience must match production vs sandbox login host. |
| `byoa` | Bring your own OAuth 2.0 app | External Client App client ID/secret and exact callback URL. Current source keeps BYOA scope behavior revision-sensitive; verify selected scopes instead of assuming a default. |
| `oauth2ClientCredentials` | OAuth 2.0 client credentials | Salesforce org domain plus app key/secret. The External Client App must enable this flow and specify the Run As user. |

The connector resolves the Salesforce instance host and API version during
connection provisioning. Record both from the affected connection; a source default
or newer connection does not prove what an existing connection uses.

#### Common exact branches

#### App blocked / `OAUTH_APPROVAL_ERROR_GENERIC`

For the public UiPath app, a Salesforce admin must install/approve it under Connected
Apps OAuth Usage or grant the applicable bypass permission. For BYOA, configure the
External Client App policies and assigned users.

#### `invalid_client_id` / `client identifier invalid`

Check:

1. Consumer Key copied from the correct External Client App;
2. Consumer Secret paired with that key;
3. Production versus Sandbox;
4. callback URL exact match;
5. permitted-user and IP-relaxation policies;
6. up to ten minutes of Salesforce propagation after app changes.

#### Connection disconnects after working

Salesforce allows a limited number of active tokens for a user/app; UiPath public
guidance calls out five. New approvals can revoke older tokens without warning.
Also verify:

- `Perform requests at any time` / refresh-token scope;
- refresh policy set to valid until revoked where appropriate;
- password/security-token changes for the legacy password flow;
- connected app/session security policy.

Create a new connection only after capturing the prior connection's refresh failure
and app policy; otherwise the recurrence remains unexplained.

#### `API not enabled for this organization or partner`

The Salesforce edition must support API access and the acting user/Run As user needs
`API Enabled`. Authentication success does not prove either.

#### Permission model

The connection inherits the Salesforce principal's:

- object CRUD permission;
- field-level security;
- sharing/record visibility;
- file API access;
- approval/transition rights;
- API request limits.

If a client-credentials connection behaves differently from an interactive one,
compare the configured **Run As** user.

### Objects, Fields, and Activities

#### Discovery contract

Salesforce has both object and field discovery, but not every API operation appears
in the discovery API. The connector therefore combines dynamic discovery with
static resources for operations such as SOQL, parameterized search, approvals, file
operations, and bulk jobs.

Repository guarantees:

- every Salesforce object's primary key is `Id`;
- standard and custom objects can support SOQL and file-related operations;
- whether an object supports child operations cannot always be inferred from the
  first-level describe response;
- generic Search uses Salesforce `/query`, not a per-object list endpoint.

If an object/field was recently added or access changed:

1. run the Salesforce describe API as the connected user;
2. force-refresh the object lookup in the UiPath designer;
3. refresh/re-add the activity if necessary;
4. compare generated schema with object and field permissions.

Some history/share/system objects are intentionally filtered because they lack
required operations or system fields. “Visible in Object Manager” is not sufficient;
prove the API operation is supported.

#### Curated activities

Important curated families include:

- Create/Get/Update Account, Contact, Lead, and Opportunity;
- Search Records and Search using SOQL;
- Search using String (parameterized SOSL);
- Get Report;
- approval submit/approve/reject;
- Upload File, Add File to Record, Download File, and Download Attachment;
- Salesforce Bulk API job create/start/abort/status/result operations.

Hidden method definitions and current activity visibility differ. Use the generated
activity `isHidden`/lifecycle metadata, not the JSON filename.

#### Surface compatibility

Apply the common project-type and file/wait exclusions in
[connector.md](./connector.md).

One explicit exception exists in the connector source:

- **Record Created/Updated by Query [PREVIEW]** uses object
  `poll_records_by_query` and declares only `ProcessOrchestration`.

If that advanced trigger is missing outside an orchestration project, this is
expected. Inspect live `compatibleProjectTypes` when tenant behavior differs.

### Queries and Pagination

#### Search Records

The curated Search Records operation generates SOQL from:

- selected object;
- selected fields;
- condition;
- optional GROUP BY/HAVING;
- optional ORDER BY.

When no explicit field list is supplied, it uses `FIELDS(ALL)`. Salesforce then
limits the page to 200 records. With explicit fields, the connector requests up to
2,000 records per page.

This explains a recurring issue:

| Evidence | Diagnosis | Unblock |
|---|---|---|
| Exactly 200 rows and `FIELDS(ALL)` | Salesforce query page behavior | Select only needed fields and follow pagination |
| `nextRecordsUrl` present but no next activity page | Connector/activity pagination | Capture raw and mapped continuation URL |
| Field missing from results | SOQL projection or field-level security | Add field explicitly and verify describe/FLS |
| `MALFORMED_QUERY` | Generated or customer SOQL invalid | Capture final SOQL, including appended clauses |

Do not infer “all records” from a successful first page.

#### Business identifiers are not record IDs

Get/Update/Delete activities expect the Salesforce `Id`, not fields such as
`CaseNumber`, lead email, account name, or external ID unless the specific activity
says otherwise. Search by the business key first, then pass the returned `Id`.

#### Response-size and API limits

- Integration Service limits JSON response processing to 8 MB.
- Current Automation Cloud Integration Service activities time out after 120 seconds.
  Other deployments/versions can differ, so record the affected deployment.
- Salesforce enforces per-org API allocations and returns
  `REQUEST_LIMIT_EXCEEDED`.

Use field projection, selective SOQL, pagination, and Bulk API. Do not retry an
unbounded query or `REQUEST_LIMIT_EXCEEDED` aggressively.

### Files and Bulk Jobs

#### Salesforce Files versus classic Attachments

These are separate storage models:

| Activity | Salesforce object/content |
|---|---|
| Upload File | Creates `ContentVersion` |
| Add File to Record | Creates `ContentDocumentLink` |
| Download File | Downloads `ContentVersion.VersionData` |
| Download Attachment | Downloads classic `Attachment.Body` |

If **Download Attachment** is missing, inspect the generated activity metadata and
tenant rollout before using **Download File** with a classic Attachment ID; the two
activities target different Salesforce objects.

A file visible in the Salesforce UI can still be inaccessible through the API due to
record sharing, content/file permissions, library membership, or storage-model
mismatch.

#### Upload File

Udon converts the UiPath file into Base64 JSON:

```json
{
  "Title": "<original filename>",
  "VersionData": "<base64>"
}
```

Consequences:

- the file expands during Base64 encoding;
- it is subject to Udon's configured Base64 conversion limit;
- the JSON response/request path can hit the Integration Service 8 MB limit;
- a missing file emits `Required file upload items are empty`;
- a too-large file emits `The given file exceeds the size limit of <n> MB`.

Do not manually Base64-encode an `IResource`; that produces a double-transformation.

#### Download errors

The download hooks first need metadata:

- modern file needs `Title` and `FileExtension`;
- classic attachment needs `Name`.

If metadata is missing, the connector cannot set a stable filename/content type.
Capture the metadata response, binary response, content length, and file magic bytes.

`failed to retrieve content_version id` is raised when the connector cannot resolve
the `ContentVersion` behind the selected content document. Check content-document ID,
version visibility, and API permission.

#### Bulk upload/query jobs

Bulk upload is asynchronous:

1. Create Bulk Upload Job with object, operation, delimiter, line ending, and CSV.
2. Upload job data.
3. Start the job.
4. Poll Get Bulk Job Info.
5. Download failed/unprocessed rows if needed.

CSV column headers must be Salesforce field API names. The connector contains exact
pre-hook errors:

- `Unable to create bulk job: ...`
- `Bulk Job ID not present in response: ...`

Bulk file upload is binary at the job-data step; ordinary Upload File is Base64 JSON.
Do not apply the ContentVersion troubleshooting path to a Bulk API job.

### Triggers

Current supported public trigger families are polling-based:

- Account Created
- Contact Created
- Lead Created
- Opportunity Created
- Opportunity Closed/Won
- generic Record Created/Updated
- preview Record Created/Updated by Query

The static object triggers poll every five minutes using:

```text
LastModifiedDate > <last poll time>
```

Identity is `Id`; created/updated fields are `CreatedDate` and `LastModifiedDate` in
GMT.

#### Advanced trigger by SOQL

The query parameter must contain a valid SOQL `SELECT ... FROM ...` query **without a
date predicate**. The hook:

1. parses SELECT/FROM/WHERE and trailing GROUP BY/ORDER BY/LIMIT/HAVING;
2. adds `Id`, `CreatedDate`, and `LastModifiedDate` if not projected;
3. injects the poll date condition unless the WHERE already mentions CreatedDate or
   LastModifiedDate;
4. removes quotes around the generated ISO poll timestamp.

Exact parser error:

```text
Invalid SOQL: Missing SELECT clause.
```

If the user includes their own CreatedDate/LastModifiedDate condition, the hook skips
injection. That can cause repeats or missed records if the customer's fixed date
window does not track the poll watermark. The activity guidance explicitly says to
omit date filters.

The advanced trigger has:

- five-minute poll;
- page size 20;
- batch size 1;
- created-check tolerance 10;
- required query and Generate output parameters;
- PREVIEW lifecycle;
- `ProcessOrchestration` compatibility.

For a missed record, capture final transformed SOQL, all `nextRecordsUrl` values,
record timestamps, watermark, event classification, and dedupe.

Diagnose Salesforce events as polling unless the deployed event definition proves
otherwise; static webhook-looking metadata is not evidence of webhook delivery.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching action-map row. If the evidence does not isolate one cause, stop at the
missing discriminator.

Correct the smallest proven Salesforce branch: app policy/auth grant, instance/API
version, Salesforce permission, SOQL/projection, pagination, file model, bulk job,
or poll query. Verify with the same Salesforce principal and record ID.

### Diagnosis-to-Action Map

| Proven finding | Owner and unblock | Healing decision |
|---|---|---|
| Connected/external app blocked, client invalid, grant revoked, or audience/environment wrong | Salesforce connection owner/admin: approve the app or correct the exact auth configuration, then reauthorize | Human action; never expose or replace secrets in the diagnostic output |
| API disabled, object/field permission missing, or record invisible to the connected principal | Salesforce admin: grant only the required API/object/field/record access | Human approval; do not automatically broaden profiles or permission sets |
| Final SOQL is malformed, uses a business identifier as `Id`, or requests an invalid projection | Workflow developer: correct the activity input/query and validate the upstream value | Source-change recommendation only |
| Salesforce returns a continuation URL but the activity drops records | Connector team: fix pagination mapping using the first dropped `nextRecordsUrl` | Escalate; retrying page one does not heal data loss |
| Salesforce accepts the file/bulk request but connector output or job state is wrong | Connector team after the provider job/file ID and transformed output are correlated | Escalate with provider and connector states separately |

### Escalation Bundle

Include:

- tenant/region, UTC time, trace/request ID;
- connector/activity version, UiPath surface/project type;
- auth type, Production/Sandbox, resolved instance hostname, API version,
  connection ID, and acting/Run As username;
- external/connected app policy and granted scope names, never tokens or keys;
- Salesforce object API name, record `Id`, operation, final SOQL/path/method;
- object describe and field-level security result for missing metadata;
- every page's `nextRecordsUrl`, row count, and selected fields;
- redacted Salesforce error/payload and redacted connector-transformed payload;
- for files: ContentVersion versus Attachment, IDs, byte count, permitted hash or
  minimal magic-byte prefix, Base64/binary path, metadata, and content type; never
  attach raw customer file bytes;
- for triggers: final SOQL, record Id/CreatedDate/LastModifiedDate, watermark,
  pages, event classification, and dedupe result.
