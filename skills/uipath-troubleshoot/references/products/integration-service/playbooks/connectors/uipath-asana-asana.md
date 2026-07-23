---
confidence: medium
---

# Asana Connector Diagnostics

Use this playbook for the UiPath Asana connector with key
`uipath-asana-asana`. It is based on the deployed connector definition and
Periodic activity-generation rules. It turns the connector's actual OAuth,
resource, pagination, and polling contracts into customer-unblock steps.

## Context

Apply the common evidence, activity-surface, file, and trigger rules in
[connector.md](./connector.md), then use the Asana-specific branches below.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The Asana OAuth redirect, client, PKCE, consent, or BYOA application configuration is incorrect.
- The connected Asana user is not a member of or cannot access the target workspace, team, project, task, or custom field.
- The selected Asana operation requires a paid plan or permission unavailable to the connected user.
- The workflow supplied the wrong GID, resource type, field alias, timestamp, or request-body shape.
- The connector failed to propagate Asana cursor pagination from `next_page.offset`.
- The polling window, parent GID, hydration, permissions, mapping, or dedupe logic omitted an expected event.
- The requested upload or download activity is not implemented or is excluded from the consumer project type.

## Investigation

### Fast Symptom Router

| Symptom | Most likely branch | First decisive check |
|---|---|---|
| OAuth returns to an error page or never creates the connection | Redirect URI, client, PKCE, or consent | Compare the exact redirect URI registered in the Asana developer app |
| UiPath OAuth works but BYOA fails | Customer app configuration | Verify Client ID, secret, exact redirect URI, and that the app is usable by the connected user |
| Connection succeeds but resource dropdown is empty | Connected-user membership | Call `/users/me`, list workspaces, and prove the user belongs to the target workspace/team/project |
| `401` | Expired/revoked grant or wrong app | Reauthenticate, retaining the Asana response and connection version |
| `403` | Membership, resource permission, or premium endpoint | Check the connected user's access and whether **Search Tasks** is available for the Asana plan |
| `404` for a known task/project | Wrong GID/type or invisible resource | Use the numeric/string GID, correct resource type, and same connected user |
| Create/Update rejects otherwise valid-looking inputs | Connector field alias transformation | Check `*Gid` inputs and the final `data` body sent to Asana |
| Search/list returns only the first page | Cursor mapping | Capture `body.next_page.offset` and the next request's `offset` |
| Search Tasks fails while basic task list works | Premium-only search API | Confirm the Asana workspace has the required paid tier |
| Trigger is delayed | Expected polling behavior | Check the five-minute poll schedule before treating it as lost |
| Completed task trigger misses a task | Project, `modified_at`, hydration, or permissions | Run the exact project-task poll as the connected user |
| Project status trigger misses an update | Wrong parent GID or poll window | Check `parent`, `created_since`, `modified_at`, and the returned status-update GID |
| Upload/Download activity is absent | Expected connector catalog | This source revision has no curated file-transfer activity |

### Connector Capabilities

| Capability | Connector behavior |
|---|---|
| API | Asana REST API at `https://app.asana.com/api/1.0` |
| Discovery | Static connector resources; no native object or field discovery |
| HTTP Request | Supported for APIs that are not exposed as curated/generic activities |
| Curated activities | Search Tasks; Create/Get/Update Project; Create/Get/Update Task |
| Generic resources | Workspaces, teams, users, projects, tasks, status updates, project members, task-project links, and custom-field settings |
| Pagination | Cursor pagination; records are below `data`, next cursor is `body.next_page.offset` |
| Events | Polling for task completed and project status updated |
| Files | No curated upload/download method in the verified connector definition |

Do not infer a visible activity from a resource filename. Periodic also evaluates
method lifecycle, `curated`, hidden flags, and compatible project types.

### Authentication and Connection Provisioning

#### Supported authentication types

| UI option | Required input | Runtime behavior | Gotchas |
|---|---|---|---|
| **OAuth 2.0 Authorization Code with PKCE** | Asana sign-in and consent | Authorization code flow with PKCE `S256`; token and refresh calls use Asana's OAuth endpoint | A successful Asana browser session does not prove the user granted the intended account or can see the target workspace |
| **Bring your own OAuth 2.0 app** | Client ID, client secret, registered redirect URI, and consented user | Uses the same PKCE flow with the customer's Asana app | The redirect URI must match the URL shown by UiPath exactly, including scheme, host, path, and trailing slash behavior |

The source connector uses:

- authorization endpoint `https://app.asana.com/-/oauth_authorize`;
- token endpoint `https://app.asana.com/-/oauth_token`;
- revocation endpoint `https://app.asana.com/-/oauth_revoke`;
- PKCE challenge method `S256`;
- default scopes `default openid email profile`.

Connection validation calls `/users/me`. On success the connector stores the
returned email as connection identity. Therefore:

- a failure before `/users/me` is an OAuth/token branch;
- `/users/me` success plus an empty workspace/project dropdown is normally a
  membership or reference-data branch;
- an email mismatch means the wrong Asana account was authorized.

#### OAuth error meanings

| Evidence | Meaning | Unblock |
|---|---|---|
| Provider reports redirect/callback mismatch | BYOA redirect URI differs | Copy the exact UiPath redirect URI into the Asana app and reauthorize |
| Authorization succeeds but token exchange rejects client | Wrong Client ID/secret or app | Correct the BYOA credentials; never attach the secret to the ticket |
| Token exists but `/users/me` is `401` | Invalid, expired, or revoked grant | Reauthenticate; if immediate recurrence, inspect app/user revocation |
| `/users/me` works but operation is `403` | Resource access or product-tier restriction | Check membership/permission and whether the endpoint is premium |
| `/users/me` identifies another email | Wrong browser/account selected | Sign out/select the intended Asana identity and create a new connection |

### Activity Availability by UiPath Surface

Asana has no connector-wide project restriction. Apply the common rules in
[connector.md](./connector.md). Event waits follow the persistence exclusion; their
absence in Agent Builder/API Workflows is not an Asana authorization failure.

### Activity-Specific Gotchas

#### GIDs, membership, and reference dropdowns

Asana resources use globally unique identifiers (`gid`). Use the GID, not the
display name. Dropdowns are resolved using the connection:

- workspaces from `/workspaces`;
- projects filtered by selected workspace;
- users/teams through their corresponding workspace or team resource.

A resource visible to the reporter can be absent for the connected user. Prove
membership using the connection identity, not a separate browser account.

#### Create/Update Task

The curated request exposes friendly GID fields, but the pre-request hook rewrites:

| Activity field | Asana request field |
|---|---|
| `workspaceGid` | `data.workspace` |
| `followerGids` | `data.followers` |
| `projectGids` | `data.projects` |
| `tagGids` | `data.tags` |
| `assigneeGid` | `data.assignee` |

If Asana reports an invalid relationship, capture the post-hook body. Confirm it
has one `data` wrapper and that each GID belongs to the intended workspace. Do not
add a second wrapper or send both the friendly and provider field.

#### Create/Update Project

The project hook rewrites:

| Activity field | Asana request field |
|---|---|
| `teamGid` | `data.team` |
| `ownerGid` | `data.owner` |
| `followerGids` | `data.followers` |

An owner/follower can be a valid Asana user but invalid for the selected
workspace/team. Test the smallest body (name plus required workspace/team), then
add owner/followers.

#### Search Tasks

The curated operation calls
`/workspaces/{workspaceId}/tasks/search`. This Asana API is available only to
premium workspaces. A `403` or plan-related provider error on Search Tasks while
ordinary task listing works is a plan/endpoint capability branch, not a broken
connection.

If the caller does not choose fields, the connector adds:
`name,resource_type,resource_subtype,modified_at,created_at,completed`.

#### Pagination

List/search responses use the Asana envelope:

```text
body.data                 -> current records
body.next_page.offset     -> next cursor
offset=<CURSOR>           -> next request
```

The connector uses cursor pagination with a safe provider maximum of 100.
Treat 100 as the per-request limit unless the exact resource declares less
(the task-completed poll uses 20). When records are missing, capture every offset;
do not fabricate numeric page numbers.

#### Custom fields

Custom fields are static connector shapes plus GID-based values, not full native
field discovery. Confirm the field GID and type (enum, number, text, people, and so
on) in Asana. A valid value for one workspace's custom field is not portable to
another field with the same display name.

### Files and Attachments

The verified connector definition exposes no curated upload or download activity,
even though Asana's API has attachment endpoints. Therefore an absent file activity
is expected for this connector version.

Use **HTTP Request** only if its supported request/response modes can represent the
target Asana attachment API. Establish the actual multipart/binary contract and
provider file limit before recommending it. Do not claim a generic UiPath or Asana
size limit without a trace because this connector source supplies no file method,
file tag, or connector-specific file-size validation.

If file support is required as a first-class activity, capture the provider
contract and raise a connector capability request rather than diagnosing a CRUD
activity as defective.

### Triggers

#### Task completed

This is a five-minute poller on:

```text
/projects/{projectId}/tasks
  ?completed_since=<LAST_POLL_GMT>
  &opt_fields=name,resource_type,resource_subtype,modified_at,created_at,completed
```

Contract:

- required inputs: Workspace ID and Project ID;
- ID field: `gid`;
- updated field: `modified_at` in GMT;
- page size: 20;
- the post-poll mapping emits `TASK_COMPLETED` only when `completed == true`;
- hydration retrieves `/tasks/{gid}`.

Unblock by running the exact URL as the connected user and proving the task is in
the selected project, returned in all pages, completed, and hydratable.

#### Project status updated

This is a five-minute poller on:

```text
/status_updates
  ?opt_fields=status_type,modified_at
  &created_since=<LAST_POLL_GMT>
  &parent=<PROJECT_GID>
```

Contract:

- required inputs resolve workspace then project/parent GID;
- ID field: `gid`;
- page size: 100;
- updated field: `modified_at`;
- curated mapping emits `PROJECT_STATUS_UPDATED`.

If a status is missing, compare the literal parent GID and poll window. Status
updates on another project, portfolio, or goal are not part of this trigger.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching unblock branch. If the evidence does not isolate one cause, stop at the
missing discriminator.

### Unblock Runbooks

#### Connection works but dropdown is empty

1. Capture `/users/me` identity.
2. List `/workspaces` through the same connection.
3. Confirm the user is a member of the intended workspace/team/project.
4. Reopen the activity and select workspace before dependent project fields.
5. Escalate only if the provider returns the record but reference mapping drops it.

#### Create/Update fails

1. Capture redacted activity inputs and the structural/redacted post-hook provider body.
2. Confirm a single `data` wrapper.
3. Verify every GID and its workspace relationship.
4. Retry with the minimum required fields.
5. Add optional followers/projects/tags/custom fields one group at a time.

#### List/search misses records

1. Prove the record is visible to the connected user.
2. Capture `data`, `next_page.offset`, and every subsequent request.
3. For Search Tasks, confirm a premium workspace.
4. Confirm filters use GIDs and correct timestamps.
5. Escalate with the first dropped cursor/page.

### Escalation Bundle

Include connector/activity version, tenant and surface/project type, connection
identity, workspace/team/project/task GIDs, operation, trace/request ID and UTC
timestamp, redacted post-hook request/provider response, pagination offsets,
provider request/rate-limit headers, and for triggers the exact poll window,
returned pages, GID, mapping, hydration, and downstream job ID.
