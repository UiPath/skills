---
confidence: medium
---

# SAP Concur Connector Diagnostics

Use this playbook for the UiPath SAP Concur connector with key
`uipath-sap-concur`. The important boundaries are the OAuth application,
token-derived regional host, connected Concur user, Expense API version,
runtime custom-field transformation, and activity-specific file contract.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the SAP Concur-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The Concur OAuth application, required scopes, company SSO policy, grant, or connected user is invalid.
- Token provisioning or refresh did not return and persist the correct regional `geolocation` host.
- The connected Concur user or company lacks the scope, app permission, profile mapping, or resource access required by the operation.
- The emitted Concur host, API version, identifier, report filter, or request transformation is wrong.
- Report form or custom-field metadata is stale, inaccessible, or mapped incorrectly.
- The file type, byte count, MIME type, multipart transport, or activity-specific 5 MB/10 MB limit is violated.
- The polling query, LastModifiedDate window, paging, mapping, watermark, or visibility omitted the expected report event.

## Investigation

### Fast Symptom Router

| Symptom | Most likely branch | First decisive check |
|---|---|---|
| Connection cannot be created and mentions scope | Concur app scope allow-list | Compare every requested scope with the OAuth client's allowed scopes; `openid` is mandatory |
| Authorization fails only for an SSO-enabled company | Known Concur authentication limitation | Test against the documented SSO limitation before changing the connector |
| Token succeeds but every API call uses an empty/wrong host | Missing token `geolocation` | Inspect the token response and stored `base.url` |
| Token refresh succeeds but requests move to another region | Refresh response geolocation | Confirm refresh returned and persisted the correct `geolocation` |
| Connection identity or user-specific activity is empty | `/profile/v1/me` mapping | Confirm response contains both profile `id` and Concur `cteUsername` |
| `401` | Expired/revoked token or wrong OAuth app | Inspect token/refresh phase and reauthorize only after confirming |
| `403` | Missing scope, app permission, or Concur user/company access | Retain provider body and compare the exact operation with granted scopes |
| `404` | Wrong geolocation host, API version, or identifier | Prove the emitted hostname/path and provider response |
| Create Report fields are missing/stale | Report form/custom-field cache | Check the default RPTINFO form, field access, and Refresh Metadata |
| Report search filter behaves unexpectedly | Udon filter translation | Capture final query parameters, especially date and reimbursement fields |
| `File type not supported...` | Connector-side extension validation | Route by the exact message and activity; supported types differ slightly |
| `File size should not be greater than 5MB` | Add Quick Expense with Receipt | Reduce below 5,000,000 bytes |
| `File size should not be greater than 10MB` | Report/expense attachment or receipt upload | Reduce below 10,000,000 bytes |
| `Unable to upload file` | Udon upload transport failure | Inspect nested runtime/provider evidence; this is not a size/type message |
| Report trigger delayed/missing | Five-minute poll, LastModifiedDate, pages, or visibility | Run the exact report poll with the same connection |

### Connector Capabilities

| Capability | Connector behavior |
|---|---|
| API family | SAP Concur REST/OData, primarily Expense V3 plus Quick Expense V4 and profile endpoints |
| Discovery | Static resources; report custom fields are dynamically obtained/cached by Udon |
| HTTP Request | Supported |
| Curated operations | Add Quick Expense; Add Quick Expense with Receipt; Upload Receipt Image; Create/Submit Report and supporting lookups |
| Generic resources | Reports, expense entries, attendee types, group configurations, and attachment/receipt upload resources |
| Events | Polling for Report Created and Report Updated |
| Files | Multipart/raw streaming with connector-specific validation; limits vary by activity |

### Authentication and Regional Provisioning

#### Supported authentication type

The connector supports **OAuth 2.0 Authorization Code** with a customer SAP Concur
OAuth application. The connection asks for Client ID, Client Secret, and scopes.
The source's default scope string is:

```text
openid EXPRPT IMAGE user.read CONFIG quickexpense.writeonly
```

`openid` is required to create a connection. Every requested scope must be enabled
for the Concur OAuth client; one unsupported scope can cause the whole grant to
fail. Do not remove a scope merely to make consent succeed without checking which
activities require it.

Source endpoints:

- authorize: `https://www-us.api.concursolutions.com/oauth2/v0/authorize`;
- token/refresh: `https://us.api.concursolutions.com/oauth2/v0/token`.

The fixed token hostname is not the operational API hostname. After token exchange,
the connector stores:

- `access_token`;
- `refresh_token`;
- `expires_in`;
- token time;
- token response `geolocation` as `base.url`.

The refresh hook performs the same update. If the token lacks `geolocation`, the
hook stores an empty base URL. Therefore a successful token exchange followed by
bad/empty request paths is a provisioning defect or unexpected Concur token
response, not an ordinary operation permission error.

#### Connection identity

The connector calls `/profile/v1/me`. Its post-hook requires:

- response `id`, stored as `user.id`; and
- `com:concur:internal:product:Identifiers:1.0.cteUsername`, used as connection
  identity.

If either is absent, the hook completes without setting identity/user ID. This can
leave user-specific Quick Expense paths unusable even though OAuth succeeded.
Capture the redacted profile response shape and connector version.

#### Authentication error meanings

| Evidence | Meaning | Unblock |
|---|---|---|
| Consent/token says a requested scope is not allowed | OAuth client is not approved for all requested scopes | Update the Concur app allow-list or request only the verified operation scopes |
| `openid` absent | Connection identity contract cannot be established | Add `openid` and reauthorize |
| SSO organization cannot complete authorization | Documented Concur SSO limitation | Follow the supported Concur/UiPath authentication path; escalate with company/app context |
| Token succeeds; `base.url` is empty | Token response lacks `geolocation` or hook did not persist it | Capture token keys (not values), hook trace, and stored config presence |
| Initial calls work; refresh fails | Refresh grant/client/revocation issue | Inspect refresh response and rotated token fields |
| Refresh works; calls use wrong region | Refresh `geolocation` persistence issue | Compare old/new geolocation and emitted host |
| Profile call works but identity remains blank | Missing profile `id` or `cteUsername` | Correct account/API access or escalate response-shape drift |

### Activity Availability by UiPath Surface

SAP Concur has no connector-wide project restriction. Apply the common rules in
[connector.md](./connector.md). Required upload activities and event waits follow
the shared Agent/API exclusions. Keep the operation-specific 5 MB and 10 MB limits
below; they are connector behavior, not a common platform rule.

### Activity-Specific Gotchas

#### Add Quick Expense

The source maps customer-friendly payment values before calling Concur:

| Activity value | Provider value |
|---|---|
| `Company Paid` | `CPAID` |
| `Out of Pocket` | `CASHX` |
| `Pending Transaction` | `PENDC` |

If Concur rejects the payment type, capture the structural/redacted post-hook body and connector
version. The activity also depends on provisioned `user.id` and constructs the V4
path under `/quickexpense/v4/users/{user.id}/context/TRAVELER/...`.

#### Create Report and custom fields

Udon retrieves the default report form (`RPTINFO`, named like **Default Report
Information**) and its `/Fields`. It caches field metadata in the connection.
Only custom fields with `Access == RW` and `Custom == Y` are offered. Provider
types map to UiPath types, with `TIMESTAMP` mapped to date and other types generally
mapped to string.

At execution, display labels are transformed back to provider keys such as
`Custom8`; underscores are removed from `Custom_*` and `OrgUnit_*` body keys.

If fields are absent or stale:

1. confirm the connected user can read report forms/fields;
2. confirm the default RPTINFO form exists;
3. check `RW` and custom flags;
4. use **Refresh Metadata** to clear the cache;
5. reopen/remap the activity after refresh.

`metadata not found` means the expected cached form metadata was unavailable. It is
not an OAuth error by itself.

#### Report filtering

Report list/search is not a transparent pass-through:

- friendly reimbursement method values are mapped to Concur enum values;
- CEQL date comparisons `<=` and `>=` are translated to the configured
  before/after provider parameters;
- additional friendly fields are mapped to actual provider parameter names.

When filtering is wrong, compare the expression with final emitted query
parameters. A valid unfiltered call does not prove the translation is correct.

### File Upload Limits

There are two distinct file contracts. Route by activity and exact error.

| Activity family | Accepted extensions | Maximum check | Exact connector errors |
|---|---|---|---|
| **Add Quick Expense with Receipt** | PNG, PDF, TIFF, JPEG | `fileSize / 1,000,000 <= 5` | `File type not supported. Supported types are (PNG, PDF, TIFF, JPEG)`; `File size should not be greater than 5MB` |
| **Upload Report Attachment**, **Upload Expense Attachment**, **Upload Receipt Image** | `.jpg`, `.jpeg`, `.png`, `.pdf` | `fileSize / 1,000,000 <= 10` | `File type not supported`; `File size should not be greater than 10MB`; transport failure: `Unable to upload file` |

These are decimal limits: 5,000,000 and 10,000,000 bytes. A file that is “5 MB”
or “10 MB” in a desktop UI can be slightly over the enforced boundary.

Additional distinctions:

- Quick Expense with Receipt allows TIFF; Udon attachment/receipt uploads do not.
- Udon validates the filename extension, then sends the raw file stream with the
  file item's content type.
- A renamed extension does not make incompatible content valid; retain the Concur
  provider response if it rejects the media.
- `Unable to upload file` is a catch-all for exceptions during relay/HTTP upload.
  Inspect the nested exception, emitted URL, content type, trace, and whether
  Concur returned a response. Do not ask the customer to shrink the file unless the
  size error occurred.

### Triggers

Report Created and Report Updated use a five-minute poll:

```text
/reports?where=LastModifiedDate>='<last poll in GMT>'
```

Contract:

- ID field: `ID`;
- created field: `CreateDate`;
- updated field: `LastModifiedDate`;
- timestamp format: `yyyy-MM-dd'T'HH:mm:ss.SSS`, GMT;
- page size: 20;
- curated mapping emits `REPORT_CREATED` or `REPORT_UPDATED`;
- watermark uses the last poll date.

For a missing report:

1. record report `ID`, `CreateDate`, and `LastModifiedDate`;
2. run the literal poll query as the connected user on the stored geolocation host;
3. capture every page;
4. compare timestamp parsing and event classification;
5. trace dedupe/watermark, emitted event, and downstream job.

Do not assume webhook delivery or instantaneous firing; this connector uses
polling.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching unblock branch. If the evidence does not isolate one cause, stop at the
missing discriminator.

### Unblock Runbooks

#### OAuth succeeds but operations fail

1. Confirm token response contained `geolocation`.
2. Confirm stored `base.url` equals that host after initial grant and refresh.
3. Call `/profile/v1/me` and verify `id` plus `cteUsername`.
4. Compare the operation with granted scopes and Concur company/user permissions.
5. Capture the emitted provider hostname/path and response.

#### Report fields missing

1. Call the default report form and Fields endpoints through the connection.
2. Verify the form name/ID and field `Access`/`Custom` values.
3. Run Refresh Metadata.
4. Reopen the activity and remap fields.
5. Escalate only if provider metadata is present but the regenerated fields omit it.

#### File upload fails

1. Identify the exact activity.
2. Record filename, extension, exact byte size, and MIME type.
3. Apply the correct 5 MB or 10 MB matrix.
4. For `Unable to upload file`, inspect relay/runtime/provider evidence.
5. Retry a small known-good supported file through the same connection and path.

### Escalation Bundle

Include connector/activity version, tenant and consumer project type, connection
ID/identity, Concur company/app context and scope names (no secrets), presence of
token fields and redacted `geolocation`, profile response shape, operation and API
version, emitted hostname/path, trace/request ID and UTC timestamp, redacted
request/provider response, report form/cache evidence, and for files filename,
extension, byte size, MIME type, exact error, and provider/relay evidence. For
triggers include report ID, dates, poll query/pages, mapping, watermark, event, and
downstream job ID.
