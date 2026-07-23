---
confidence: medium
---

# Jira Connector Diagnostics

Use this playbook for the UiPath Jira connector with key
`uipath-atlassian-jira`. It is based on the connector definition, the Jira-specific
Udon runtime hook, and the Periodic dynamic activity-pack generator. It is intended
to answer three questions quickly:

1. Is the behavior expected for this connector and consumer surface?
2. At which boundary did it fail: connection, design-time metadata, activity
   execution, file transfer, or event polling?
3. What evidence and corrective action will unblock the customer?

The connector supports **Jira Software Cloud only**. Do not use this playbook for
Jira Server or Jira Data Center.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the Jira-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The Atlassian grant is revoked, the connected account has no Jira Cloud site, or the configured site URL does not match an accessible site.
- The connected Jira user lacks the required product, project, issue, field, transition, comment, or attachment permission.
- The connector route, HTTP method, project key, issue type, issue key, transition, or attachment identifier is wrong.
- Jira create/edit metadata is unavailable, stale, over the connector field ceiling, or based on a project and issue-type combination with no usable sample.
- The connector injected its default 30-day JQL window or failed to propagate `nextPageToken`.
- The attachment is disabled, too large, unavailable to the user, or transferred with the wrong multipart or binary contract.
- The generated activity is incompatible with or has not propagated to the selected UiPath project type.
- The polling JQL, timezone, watermark, paging, event identity, or dedupe decision omitted the expected issue event.

## Investigation

### Fast Symptom Router

| Symptom | Most likely branch | First decisive check |
|---|---|---|
| Connection creation says `No Jira sites found` | OAuth accessible-resources lookup | Confirm the Atlassian account has Jira Cloud site access and granted the expected site |
| Connection creation says `Jira site <URL> not found` | Exact site URL mismatch | Normalize the configured URL and compare it with the URL returned by Atlassian |
| `The token was globally revoked. Please re-authenticate.` | Atlassian grant revoked | Reauthenticate the connection; do not treat this as a Jira project permission issue |
| `401` or `403` during an activity | Scope, Jira product access, or Jira object permission | Compare provider response, granted scopes, and the connected user's Jira permissions |
| `No API found at that URL for the given token and credentials` | Udon route/method resolution | Confirm connector path and HTTP method before changing credentials |
| Create/Update fields do not load | Dynamic Jira metadata | Select a literal Project and Issue Type and confirm the combination has an existing schema/sample issue |
| Older issues are missing from a list/search | Udon default JQL | Check whether the request omitted JQL; the runtime then adds a 30-day window |
| Search repeats or stops after one page | `/search/jql` paging/version | Capture `nextPageToken` and connector version |
| Add/Download Attachment is absent | Consumer project compatibility | Check the generated activity's `compatibleProjectTypes`, not only Windows/Cross-platform compatibility |
| Attachment upload fails | Jira attachment settings, size, multipart contract, or permission | Read attachment metadata and compare `enabled` and `uploadLimit` with the file |
| Trigger cannot be created | Missing connection timezone or trigger parameter | Check `/myself` result and required Project/Issue Type values |
| Issue exists but no event arrives | Poll JQL, connected-user visibility, watermark, or dedupe | Run the exact poll JQL as the connected user and trace the issue's `created`/`updated` value |
| Comment webhook trigger is absent | Expected behavior | The comment webhook definition is disabled for production; Jira events currently use polling |

### Connector Capabilities

| Capability | Connector behavior |
|---|---|
| Deployment | Jira Software Cloud only; REST API v2 |
| Discovery | Static objects with field discovery; custom fields are resolved at design time |
| CEQL | Only the `issue` object has CEQL support, and supported operators are limited |
| Advanced query | Use Jira's `jql` parameter or **Search Issues by JQL** for complex searches |
| HTTP Request | Supported; use it when no curated/generic activity covers a Jira endpoint |
| Events | Polling for issue created/updated; no production comment webhook |
| Generic activities | Create, Retrieve/Get, List, Replace, Delete, and Download where the resource supports them |
| Curated issue activities | Add Comment, Create Issue, Get Issue, Update Issue, Update Issue Assignee, Update Issue Status, Search Issues, Search Issues by JQL, and attachment activities |
| Other curated activities | Get Comments, Update Comment, Find User by Email Address or Display Name, and Get Instance Details |

The connector repository contains several hidden or superseded resource definitions.
Do not infer customer-visible activities merely from a JSON filename. Periodic uses
method-level `curated`, `isHidden`, lifecycle, and compatible-project metadata to
construct the activity package.

### Authentication and Connection Provisioning

#### Supported authentication types

| UI option | Required customer input | Runtime base URL | Use and gotchas |
|---|---|---|---|
| **Basic authentication** | Jira account email/username, API token, and Jira site URL | `<SITE_URL>/rest/api/2` | The password field is an Atlassian API token, not the Atlassian password. The provisioning hook adds `https://` if absent, but does not remove a trailing slash. Enter `https://tenant.atlassian.net` with no trailing `/`. |
| **OAuth 2.0** | Jira site URL, consented Atlassian user, and requested scopes | `https://api.atlassian.com/ex/jira/<CLOUD_ID>/rest/api/2` | Atlassian must return the configured site from `accessible-resources`. Select the same Jira site during consent that was entered in the connection form. |
| **Bring your own OAuth 2.0 app (BYOA)** | Jira site URL, OAuth client ID/secret, consented user, and scopes | Same cloud-ID route as OAuth 2.0 | The Atlassian app must be configured for 3LO and authorized for every requested scope. A successful token does not prove the site or Jira permissions are correct. |

OAuth and BYOA use:

- authorization endpoint `https://auth.atlassian.com/authorize`;
- token and refresh endpoint `https://auth.atlassian.com/oauth/token`;
- the Atlassian `accessible-resources` endpoint to resolve the Jira `cloudId`.

The connector's required scope options are:

- `offline_access`
- `read:jira-user`
- `write:jira-work`
- `manage:jira-project`
- `read:jira-work`

The configuration also offers `manage:jira-configuration` and
`manage:jira-data-provider`. Diagnose the actual operation: a token can be valid
while the connected Atlassian user lacks Jira product access, Browse Projects,
issue-security visibility, transition permission, comment permission, or attachment
permission.

### Exact Connection Errors

#### `No Jira sites found`

This comes from the connector's post-provision hook when Atlassian returns no entries
from `oauth/token/accessible-resources`.

Unblock:

1. Confirm the login is for the intended Atlassian organization.
2. Open the target Jira Cloud site as that user and prove Jira product access.
3. Reauthorize and select the target Jira site during the grant.
4. For BYOA, confirm the OAuth app has the required Jira scopes and the consent was
   granted again after scope changes.

#### `Jira site <SITE_URL> not found`

The hook compares the returned site URL with
`https://<CONFIGURED_SUBDOMAIN>.atlassian.net` exactly.

Unblock:

1. Configure the canonical site URL, including `https://` and excluding a trailing
   slash or path.
2. Confirm Atlassian returned that exact site for the connected user.
3. If the site was renamed, create or reauthenticate the connection with the current
   canonical URL.

Do not work around this error by manually supplying a cloud ID; the connector owns
the cloud-ID-to-base-URL construction.

#### `The token was globally revoked. Please re-authenticate.`

The connector explicitly maps an Atlassian `error_description` containing
`Token was globally revoked` to a `401` with this message. Reauthenticate. If it
recurs immediately, inspect Atlassian app/user security policy and BYOA refresh-token
configuration.

#### `No API found at that URL for the given token and credentials`

This is Udon's no-handler `404`. It means no connector resource matched the incoming
path and HTTP method. It is not proof that Jira rejected the credentials.

Check, in order:

1. connector key and selected connection;
2. exact resource path;
3. HTTP method;
4. whether `/rest/api/2` was incorrectly duplicated;
5. whether an old activity still targets Jira's deprecated `/search` endpoint;
6. Udon route-resolution logs and whether any outbound Jira request exists.

Only investigate Jira credentials if the trace shows Jira received and rejected the
request.

#### Connection identity and timezone

After provisioning, the connector calls `/myself`. It stores Jira's `timeZone` as
`event.user.account.timezone`; polling URLs interpolate this value. The connection
identity may use the Jira email address, but Atlassian privacy settings can make
`emailAddress` null. A missing email alone is not a broken connection.

If trigger creation reports
`Invalid configuration key event.user.account.timezone in event configuration`,
ping or reauthenticate the connection and inspect `/myself`. Repair connection
provisioning before recreating the trigger.

### Activity Availability by UiPath Surface

Jira has no connector-wide project override. Apply the common project-type rules in
[connector.md](./connector.md). Specifically:

- **Add Issue Attachment** follows the required-upload exclusion;
- **Download Issue Attachment** follows the download exclusion;
- **Wait for an Event and Resume** follows the persistence exclusion.

If tenant behavior differs, capture the live `compatibleProjectTypes`; do not
diagnose the Jira connection from activity visibility alone.

### Activity-Specific Gotchas

#### Create Issue

The activity loads its input schema only after **Project** and **Issue Type** are
selected. These values call Jira metadata with the project key and issue-type ID.

Gotchas:

- Use the project **key**, not its display name.
- Use the issue-type **ID**, not its name.
- Literal design-time values are the reliable way to load the schema. Variables can
  replace them at runtime only if the generated fields remain valid for the runtime
  project/type.
- Jira fields vary by project, issue type, screen, field configuration, and connected
  user's permissions.
- If one reusable workflow must target multiple project/type combinations, create a
  dummy Jira project and issue type whose create screen contains the superset of
  fields required by those combinations. Generate the activity schema from that
  superset and validate every runtime target separately.

The exact runtime metadata error
`projectKeys and issuetypeIds are mandatory` means the design-time call did not
receive both selectors. It is not an OAuth error.

#### Update Issue and Get Issue

Update/Get metadata can use an explicit issue ID/key. If only Project and Issue Type
are supplied, Udon searches for a sample issue to derive the field schema.

`Could not fetch JIRA issues with project and issuetype combination` means that
lookup found no usable issue. Unblock by supplying an existing issue key or creating
a representative issue in the selected project/type. Confirm the connected user can
browse it.

For Update Issue:

- at least one editable field must be changed;
- fields absent from Jira edit metadata are not valid merely because they exist on
  the Jira issue;
- transition/status is a separate workflow operation; use **Update Issue Status**;
- a field can be required by Jira even if an old issue already lacks it.

#### Custom fields and stale design-time metadata

Udon fetches `/field`, converts IDs such as `customfield_12345` to customer-readable
names, and stores forward/reverse maps on the element instance. It also remaps Jira
field-error keys back to the readable name.

Use the connector's metadata refresh path when a field was renamed, added, removed,
or changed type. Then remove/re-add or refresh the activity fields in the designer.
Recreating only the workflow does not clear connector-instance metadata.

For field metadata, the Jira hook reads 50 fields per page and stops after 50 pages.
That is a 2,500-field ceiling. If a site has more, prove whether the missing field is
beyond the fetched range before treating it as a Studio rendering issue.

Some custom array fields use an internal `_arrayRemap_` representation. When a
provider request shows the wrong shape, compare the connector-transformed payload
with Jira's expected array-of-values or array-of-objects schema.

#### Search Issues and Search Issues by JQL

If a Jira GET/POST search request has no JQL, the Udon Jira hook injects:

```text
created >= -30d order by created DESC
```

Therefore, “the connector returns recent issues but not old ones” is expected when
JQL was omitted. Supply explicit JQL to widen the period.

Other search rules:

- only `issue` supports CEQL, with limited operators;
- prefer Jira JQL for advanced filters;
- the curated Search Issues activity requires at least one search input and returns
  `At least one search parameter must be provided` otherwise;
- an issue-ID search value cannot contain spaces;
- curated Search Issues joins supplied criteria with `AND` and requests `*all`
  fields;
- Udon clamps general search page size to 100 and project search page size to 50;
- Jira search uses `/search/jql` and continuation field `nextPageToken`.

If the first page works but later pages repeat or disappear, capture the raw Jira
`nextPageToken`, the connector's emitted next-page value, activity Max records, and
connector version.

#### Update Issue Status

Jira transitions are workflow-specific. A status visible on another project or issue
type is not necessarily an allowed transition for this issue.

Unblock:

1. Read the available transitions for the same issue as the connected user.
2. Pass the transition/status identifier offered by that lookup.
3. Confirm required transition-screen fields.
4. Distinguish “transition does not exist” from missing Transition Issues permission.

Older connector definitions had multiple hidden transition variants. Diagnose the
customer-visible activity version, not a hidden standard-resource file.

#### Comments

Add Comment supports an optional Role visibility field in current activity releases.
If a comment is created but not visible to the expected user, inspect Jira comment
visibility and project roles before changing connector response mapping.

Comment create/update activities are ordinary API calls. A production comment
created/updated **trigger** is a separate capability and is not currently enabled.

#### Response too large and timeout

Integration Service has a platform-wide 8 MB JSON response-processing limit and a
120-second activity/trigger working ceiling in current Automation Cloud. Confirm
the affected deployment's current limits before concluding. Files transferred
outside JSON have a separate working ceiling of up to 1 GB, but Jira's own upload
limit can be lower.

For `Response content too large`, lower Max records, add JQL, or request fewer
fields. Do not retry the same unbounded Jira query.

### Attachments

#### Add Issue Attachment

The curated activity sends:

- `POST /issue/{issueIdOrKey}/attachments`;
- a required multipart file;
- `Content-Type: multipart/form-data`;
- `X-Atlassian-Token: no-check`.

The connector selects the first item from Jira's array response as the activity
result.

Before upload, inspect Jira attachment metadata (`attachment_meta` /
`/attachment/meta`):

| Field | Meaning | Corrective action |
|---|---|---|
| `enabled` | Whether Jira attachments are enabled | Enable attachments in Jira or stop; retrying cannot bypass this |
| `uploadLimit` | Maximum attachment size in bytes | Compare the original file byte size and reduce/split it if over the limit |

| Symptom | Diagnosis | Unblock |
|---|---|---|
| Activity absent in Agent/API project | Periodic surface restriction | Use a supported process/orchestration surface or verify a newer tenant feature rollout |
| `413` or provider size error | Jira or gateway size limit | Compare file bytes with `uploadLimit`; capture which hop returned the error |
| `415`, boundary, or empty-file error | Multipart contract lost | Use the file resource input; do not base64-wrap it into JSON or manually override the multipart boundary |
| `403` | Connected user cannot create attachments or view issue | Check Jira Create Attachments and Browse Projects/issue-security permissions |
| `404` | Wrong issue key, hidden issue, or permission-masked not-found | Retrieve the same issue with the same connection |
| Success but no output | Response-root/schema issue | Capture Jira's response array and connector-transformed response |

#### Download Issue Attachment

The curated download uses the attachment content endpoint with `redirect=false` and
returns an octet-stream resource. Use the Jira attachment **ID**, not the filename or
issue key.

If metadata retrieval works but download fails:

1. call the same attachment content endpoint as the connected user;
2. record redirect status, `Content-Type`, content length, and provider request ID;
3. confirm the activity is receiving the attachment ID;
4. distinguish an activity surface restriction from a Jira `403`/`404`;
5. check whether a proxy/relay strips binary content or redirect headers.

### Triggers and Long-Running Workflows

#### Supported event model

Current Jira issue events are polling-based:

- **Issue Created**
- **Issue Updated**
- generic Record Created/Updated for the issue resource

The curated trigger requires Project and Issue Type. It uses the project **key** and
issue-type **ID**, polls every five minutes by default, uses a page size of 20, and
interprets times in `event.user.account.timezone` from `/myself`.

The production connector does not expose the comment webhook definition. Its
candidate definition is under `eventTypes-disabledForProdDeployment`. Do not
repeatedly recreate a comment trigger or ask for Jira Administrator solely to
enable an unsupported production path.

#### Trigger creation errors

| Exact error | Meaning | Fix |
|---|---|---|
| `Invalid configuration key event.user.account.timezone in event configuration` | Connection provisioning did not store Jira timezone | Ping/reauthenticate; inspect `/myself` and connection config |
| `Parameter key <NAME> is required to create the trigger` | Required Project or Issue Type value was absent | Re-select literal lookup values; capture key/ID rather than display text |

#### Trigger does not fire

Trace one issue key end to end:

1. Record trigger creation time, connection ID, Project key, Issue Type ID, event
   type, and tenant region.
2. Confirm the connected user can retrieve the issue.
3. Run the exact generated JQL as that user.
4. Compare `fields.created` or `fields.updated` with the poll watermark in the
   connection timezone.
5. Capture every page and `nextPageToken`.
6. Inspect Gallup/poller ingestion, event identity, filter, and dedupe decision.
7. Confirm downstream job creation only after the event is proven emitted.

Special characters and spaces in Project/Issue Type previously caused trigger
failures. Current definitions use project keys and issue-type IDs. If display names
appear in a poller URL or identity, verify the deployed connector version.

#### Duplicate issue events

Do not add an `updated < now` upper bound as a customer workaround without proving
that it matches the deployed poll contract. First capture watermark, page tokens,
event identity, and the Gallup dedupe decision.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching unblock branch. If the evidence does not isolate one cause, stop at the
missing discriminator.

Correct the smallest proven Jira branch: site/grant, Jira permission, metadata
selection, JQL/pagination, issue transition, attachment contract, or poll window.
Verify with the same Atlassian user, Jira site, project, and issue.

### Unblock Runbooks

#### Connection will not create

1. Confirm Jira Software Cloud and canonical site URL.
2. Identify Basic, OAuth 2.0, or BYOA.
3. Match the exact error to the provisioning branches above.
4. For OAuth/BYOA, capture redacted `accessible-resources` output: site URL and cloud
   ID, never tokens.
5. Ping `/myself`; record account ID and timezone.
6. Verify by retrieving one visible issue with the new connection.

#### Activity is missing from a UiPath surface

1. Record the exact project type and surface.
2. Confirm the activity is present for the same tenant in a Windows/Cross-platform
   process.
3. Inspect `compatibleProjectTypes`, activity tags, `isHidden`, and lifecycle.
4. For upload, download, or Wait for Event in Agent/API projects, treat Periodic's
   default exclusion as the leading diagnosis.
5. Escalate publication only if generated metadata says compatible but the consumer
   does not display it.

#### Create/Update fields are missing or wrong

1. Use a literal Project key, Issue Type ID, and representative existing issue.
2. Compare Jira create/edit metadata as the connected user.
3. Refresh connector metadata and then refresh the activity design.
4. Check the 2,500-field ceiling and custom-field remapping.
5. Capture generated activity schema and Jira metadata for one missing field.

#### Search misses issues or pagination fails

1. Capture final JQL after connector transformation.
2. If absent, account for the injected 30-day default.
3. Confirm `/search/jql`, connector version, page size, Max records, and each
   `nextPageToken`.
4. Reduce requested fields if the response approaches 8 MB.
5. Escalate only with raw provider pages and transformed connector pages.

#### Attachment fails

1. Retrieve the issue with the same connection.
2. Read `enabled` and `uploadLimit`.
3. Record original byte size and transfer representation.
4. Confirm multipart plus `X-Atlassian-Token: no-check` for upload, or attachment ID
   plus binary response for download.
5. Check consumer-surface compatibility.
6. Preserve provider and connector status plus structural/redacted bodies separately.

#### Trigger does not create or fire

1. Resolve exact creation errors first.
2. Confirm connection timezone and required key/ID selectors.
3. Run exact poll JQL as connected user.
4. Trace paging, watermark, identity, and dedupe.
5. Do not route comment events to the disabled webhook definition.
6. Verify with a newly created/updated issue and record the observed poll cycle.

### Escalation Bundle

Include:

- tenant/organization, region, UTC time window, trace/request ID;
- connector key and deployed connector/activity version;
- UiPath surface and exact project type;
- connection ID and authentication type, with all credentials/tokens redacted;
- canonical Jira site URL, cloud ID for OAuth/BYOA, connected Jira account ID, and
  timezone;
- activity/trigger name and generated `compatibleProjectTypes`;
- Project key, Issue Type ID, issue/attachment ID, and operation;
- final transformed path, method, query/JQL, headers with secrets removed, and
  structural/redacted body;
- provider response separately from connector-transformed response;
- for metadata: Jira create/edit metadata, generated activity schema, and refresh
  result;
- for files: `enabled`, `uploadLimit`, byte size, MIME type, and transfer form;
- for polling: exact JQL, watermark, page tokens, issue timestamps, event identity,
  and dedupe decision.

Never include API tokens, OAuth client secrets, access tokens, refresh tokens,
authorization headers, or complete customer issue/comment content.
