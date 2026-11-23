# Automation Hub Open API — Reference (cloud-token auth)

> This skill authenticates with the **user's UiPath cloud access token** — **not** an admin-generated OpenAPI token. This is the AH Open API's `automation-cloud` mode: send the bearer token and **do not** send `x-ah-openapi-auth`.

This is the shared auth + endpoint catalog for both flows — [`publish-process.md`](publish-process.md) (write) and [`get-process.md`](get-process.md) (read).

## Authentication

### Getting the cloud token + org/tenant (in priority order)

1. **Runtime env-auth (preferred — this is how UiPath Delegate provides it).** The runtime runs `uip` in a virtual shell with `UIPATH_CLI_ENABLE_ENV_AUTH=true` and sets `UIPATH_CLI_AUTH_TOKEN` (the user's cloud bearer token) plus `UIPATH_CLI_ORGANIZATION_NAME` / `UIPATH_CLI_TENANT_NAME` (and `..._ID` variants). If `UIPATH_CLI_AUTH_TOKEN` is set, use it as the bearer and take org/tenant from those vars. Base URL defaults to `https://cloud.uipath.com` unless the environment specifies another. *(If a parent `uip` process instead exported `UIPATH_ACCESS_TOKEN` + `UIPATH_URL` — the `{base}/{org}/{tenant}` shape — use those.)*
2. **Logged-in `uip` session.** Otherwise, if the user has run `uip login`, read `~/.uipath/.auth` (JSON). Use its `accessToken`, `baseUrl`, `organizationName`, `tenantName`. If the file is missing or has no `accessToken`, tell the user to run `uip login` (and `uip login tenant set <name>` to pick the tenant).
3. **User-provided (last resort).** Ask the user to paste a cloud bearer token plus their **org** and **tenant** slugs (the two path segments after the host in their AH URL).

Never fall back to an admin OpenAPI token. If none of the above yields a token, stop and explain that the skill needs the user's cloud session (`uip login`) or a host-provided token.

### Base URL

```
{baseUrl}/{org}/{tenant}/automationhub_/api/v1/openapi
```

e.g. `https://cloud.uipath.com/acme/prod/automationhub_/api/v1/openapi`. Always use this **gateway** URL — the platform injects the tenant-routing headers from the `{org}/{tenant}` segments. (Local dev: base `http://localhost:3002`, path `/api/v1/openapi`, and you must confirm how org/tenant are supplied locally.)

### Headers (every request)

| Header | Value | When |
|--------|-------|------|
| `Authorization` | `Bearer <cloud access token>` | always |
| `Content-Type` | `application/json` | POST only |

**Do NOT send** `x-ah-openapi-auth` or `x-ah-openapi-app-key`. Sending `x-ah-openapi-auth: openapi-token` routes to the admin-token path and rejects a cloud token with **401**.

### Token expiry

Cloud access tokens are short-lived. If any call returns **401** and the token came from `~/.uipath/.auth`, tell the user to run `uip login` again (or re-provide a token) and retry.

## Endpoints used by this skill

### GET `/idea-flows`
All idea flows (workflow types) on the tenant. Each element has `Idea flow name` (e.g. "Business Process"), `Idea flow ID` (number), on servers with RPANAV-19226 `Idea flow type` (see **Idea flow types** below), and one key per phase whose statuses carry `phase_variable` / `status_variable`. Response wrapped as `{ message, statusCode, data: [...] }`. *(Used by the publish and change-idea-flow flows.)*

#### Idea flow types

Select a flow by `Idea flow type`, never by name (tenant-editable) or a remembered id (differs per tenant — Business Process is `7` on one tenant, `8` on another). The type comes from the flow's root `workflow_level_variable`, and every flow an admin creates (duplicate a default, copy, upload) is a deep copy that keeps it — so a tenant's copy of Business Process also reports `business-process`, and **several flows sharing a type is normal**. An automation record's `process_submission_type` (CLI: `SubmissionType`) identifies the flow **type** it is in, not which flow of that type:

| `Idea flow type` | `process_submission_type` |
|---|---|
| `idea` (Employee-driven) | `1` |
| `top-down` (CoE-driven) | `2` |
| `automation` (Citizen developer) | `3` |
| `process-mining` | `4` |
| `task-mining` | `5` |
| `change-request` | `6` |
| `agentic-ai-idea` | `7` |
| `business-process` | `8` |
| `custom` (unknown or legacy root variable — rare) | `-1` on create; **not reliable after a move** (see PATCH below) |

Phases differ between tenants even for the same type (an older tenant's Business Process flow has `IDEA`/`ASSESSMENT`/… phases, newer ones start at `DOCUMENTATION`/`NOT_STARTED`) — always read them from the flow's own entry.

### GET `/idea-schema?idea_flow_id={id}`
Full JSON schema for an idea flow + a ready-made `user_inputs` template. Response wrapped as `{ status: "success", data: {...} }`:
- `data.properties.schema.properties` — field definitions, 3-level nested (Assessment Type > Section > Question); enums carry `answer_option` codes + labels in `custom_properties`.
- `data.user_inputs` — the exact POST body template ("fill in the blanks"). Every field wraps as `{ "value": <v> }` except **user questions**: owner, submitter, and any user picker the tenant adds (the schema marks them `format: email`). Those take the email as a **direct string**; the server also accepts `{ "value": <email> }` for them. A bare string on any other question reads as empty; questions with no example are omitted.

*(Used by the publish flow.)*

### POST `/idea-from-schema`
Create a process from the schema. **Use this, not `POST /automations`** (the `/automations` alias 404s in some deployments).

Body:
```json
{ "idea_flow_id": <id>, "user_inputs": { "<AssessmentType>": { "<section-ahid>": { "<question-key>": { "value": "<v>" } } } } }
```
**Do not POST `data.user_inputs` verbatim** — its example values are placeholders that the API rejects. Replace each with a real value; in particular resolve a **valid** `OVERVIEW_CATEGORY` id (the template's `1` → `Invalid Category Id`) and real `answer_option` codes. A single- or multiple-choice value not in that field's `enum` (a label, a slug, a retyped code) is never selected. Newer builds reject it on create and update, required or optional, with a `400` naming the field: `Question "<key>" has no answer option matching "<value>". Allowed values: …`, the same text in `errorDetails["<key>"]`, and the stored answer left untouched; a multiple-choice answer sent as a bare string gets `Question "<key>" expects an array of answer option values`. Older builds fail a `required` question with `Please fill in all the required information` (`errorDetails` names the field: `An answer selection is required for submission`), and on an optional question the create **succeeds and the answer is silently dropped**, so run the preflight on every build.

**Required fields (Business Process, `idea_flow_id`=7), verified live** — note the backend enforces owner + submitter even though the schema's `required` flags omit them:

| Key | Section | Shape |
|---|---|---|
| `OVR-OVERVIEW_NAME` | `ah-section-ovr-0-0` | `{"value":"…"}` |
| `OVR-OVERVIEW_DESCRIPTION` | `ah-section-ovr-0-0` | `{"value":"…"}` |
| `OVR-OVERVIEW_CATEGORY` | `ah-section-ovr-0-0` | `{"value":<valid id>}` |
| `OVR-PROCESS_DOCUMENTS` | `ah-section-ovr-0-0` | `{"value":["<answer_option code>"]}` |
| `OVR-PROCESS_OWNER` | `ah-section-ovr-0-0` | `"<email>"` (direct string) |
| `OVR-OVERVIEW_PROCESS_SUBMITTER` | `ah-section-ovr-0-1` | `"<email>"` (direct string) |

**Studio Web link** (optional): the schema's `OVR-OVERVIEW_STUDIO_WEB_LINK` question links the process to a Studio Web solution. Its `value` is a JSON **string** — `{"url": "<{baseUrl}/{org}/studio_/designer/{projectId}?solutionId={id}>", "name": "<solution name>", "hasProcessMap": <bool>}` (`url` required; `hasProcessMap: true` only when the solution's orchestration project has a `.bpmn` — it drives AH's Maestro diagram preview). Settable at create or via the update path; empty string unlinks.

**Applications used** (`<ASSESSMENT>-COUNT_APPS`; optional unless the tenant flags it `required`): `value` is an array of `/appinventory` ids. When the schema shows a **`new_applications`** property beside `value`, the same answer can also create applications the inventory lacks — any submitter, no `MANAGE_APP_INVENTORY`, no `categoryIds`:

```json
{ "value": [12], "new_applications": [ { "application_name": "…", "application_version": "…", "application_language": "…" } ] }
```

Each entry: `application_name` required (1–50), optional `application_version` (≤20), `application_language` (≤50), `application_comments` (≤512), `application_is_citrix_client` (boolean); no other keys; ≤20 entries. Matched on name + version (case/space-insensitive) — a match reuses the existing inventory row, otherwise a new row is created and linked. Either key alone is fine at create. Set a new app's thin flag and comments **inline**, on its entry (`application_is_citrix_client: true`, `application_comments`), so the create needs no follow-up update. **Updates** (`PATCH /automations/{id}` with body `{ "user_inputs": { … } }`; working example in [`publish-process.md`](publish-process.md) Step 6b): `value` and `new_applications` together **replace** the process's whole application list. Ids in `value` resolve to bare inventory rows, so any update that answers "Applications used" also clears every existing thin flag and per-application comment. Leave both application questions out of an update unless the caller asked to change applications. If they did, send the complete list and the "Thin applications used" answer in the same update, and tell the user that per-application comments were reset. An answer with an empty `value` and no `new_applications` leaves the list unchanged: the Open API can't empty it, so a `200` there is not a removal. The property is absent on builds that predate it and when the admin disabled adding applications for the section. Rejections are `400` with message `Invalid Application Data. <reason>`: `Unknown application id(s): …`, `Adding new applications is disabled for this assessment…`, `…requires a non-empty application_name`, `…exceeds 50 characters`, `…invalid version, language, comments, or citrix flag`, `…has unknown field(s): …`, `new_applications must be an array…`, `At most 20 new applications…`. "Thin applications used" (`…-COUNT_THIN_APPS`) accepts inventory ids only.

When a required field is missing the API may return `errorDetails: {}` (no field named) with `"Please fill in all the required information"` — usually the un-flagged owner/submitter, but **tenant admins can mark additional questions required** (commonly "Applications used"/"Thin applications used"); diff the payload against every `required`-flagged question in the live schema.

**Response 201** — the standard envelope with the created process **nested under `data`**: `{ "message": "Resource Created", "statusCode": 201, "data": { "process_id": …, "process_uuid": …, "process_name": … } }`. Read **`data.process_id`** — it is NOT at the top level. If you received a 201 the process WAS created — never re-POST because a field read came back undefined; re-read the response instead. *(Used by the publish flow.)*

### POST `/automations/{process_id}/documents`
Attach a document to a process — **by uploaded bytes (`file`) or by link (`embed_link`)**. Governed by `open-api-service` `ProcessDocumentValidator` (`src/api/v1/services/processDocumentValidator.class.ts`; schema `src/models/schema/processDocumentRequest.schema.ts`). **Required fields, verified against the validator source:**

```json
{
  "document_title": "…",
  "document_description": "…",
  "document_type_id": 1,
  "file": { "file_name": "…", "mimetype": "…", "file_content": "<base64>", "file_encoding": "base64" }
}
```

- `document_title` (**not** `document_name`), `document_description`, `document_type_id` are all required by the schema.
- **`document_type_id` values are fixed platform-wide** (from `tenant-service` `file.constants.js` — never guess):

  | id | Type | id | Type |
  |---|---|---|---|
  | 1 | PDD (Process Definition Document) | 7 | INF (Input File) |
  | 2 | SDD (Solution Design Document) | 8 | OUF (Output File) |
  | 3 | DSD (Development Specification Document) | 9 | MISC ("Misc." — anything else) |
  | 4 | SOP (Standard Operating Procedure) | 10 | TCD (Task Capture Document — **special**: accepts only `zip`/`ssp` uploads, **no embed_link**) |
  | 5 | DWI (Detailed Work Instructions) | 11 | ASC (Automation Source Code) |
  | 6 | PM (Process Map) | | |

  Pick by the document's kind: PDD → `1`, SDD → `2`, a `.bpmn` process map → `6`; when unsure, default to `9` (MISC).
- **A `.bpmn` file is always `6` (PM) — this overrides the MISC fallback.** AH opens a document in its process-model editor (the canvas) only when it is type `6` **and** its `file_name` ends in `.bpmn`; the same file under `9` or any other type is download-only, with no Edit (verified on alpha, 2026-10-13). Type `6` + `.bpmn` is necessary, not sufficient: the map must also be a file upload (not `embed_link`), and the editor must be available on the tenant (older AH builds gate it behind a feature flag, and it is off on gov). So tell the caller the map *should* open in the editor; do not promise it will. The AH web UI pre-selects Process Map for a `.bpmn`; the API does not infer it — send `6` yourself. Keep the `.bpmn` extension on `file_name`: the editor keys on it, not on `mimetype`.
- **A Maestro case plan (`caseplan.json` / `.case`) is not BPMN.** The API accepts it under any type, but AH has no viewer or editor for it — it is download-only (and the web UI does not allow `.json` uploads at all). Upload it as `6` only when the caller asks for it as the process model, and tell them it will be a download, not an editable map.
- Plus **exactly one** of `file` or `embed_link` — an XOR enforced in the handler, not the schema. Sending both, or neither, 400s with `"One and only one of embed_link or file need to be specified."`
- **`file` — byte upload, the default.** Validated by `EncodedFileValidator`: `file_name`, `mimetype`, `file_content`, `file_encoding` are all required and must be non-empty, and `file_encoding` must be `base64` — the only accepted value. No mimetype allowlist. The JSON body limit is **300mb**, so a PDD-sized `.docx` or `.md` fits with room to spare.
- **`embed_link`** — use only when the document already lives at a URL and the bytes are not available.

Returns the standard envelope with the created id **nested under `data`** — read **`data.document_id`**. *(Used by the publish flow.)*

A **409 `Duplicate document with title found`** is **not** about the title, despite its message. The server returns it when a non-deleted document on the same process already has the same **`document_type_id` and the same `file_name`** (matched against the stored original file name). The title is never checked: a duplicate title with a different file name succeeds, and so does the same file name under a different type. To surface it, find the existing document in the documents list by `document_type_id` + `file.originalname`, and report it to the caller. Never silently rename the file or retitle and retry.

**Re-typing an existing upload creates a second copy.** The type is part of the duplicate check, so re-uploading a `.bpmn` that is already attached as `9` with type `6` succeeds and leaves **two** documents with the same file name: one editable, one download-only. The Open API has no update or delete route for documents, so tell the caller the old type-`9` copy is still on the process and that they should delete it in the AH web UI.

### POST `/automations/{process_id}/media`  *(not needed for documents)*
A separate byte-upload route taking the same `EncodedFileValidator` shape. Documents do **not** need it — `/documents` accepts `file` directly.

### GET `/hierarchy`
The tenant's category tree (verified live): `data.levels` (level names) + `data.categories[]`, each with `category_id`, `category_name`, `category_is_active`, and nested `subcategories`. **This is how to resolve a valid `OVERVIEW_CATEGORY` id** — it works even on a tenant with zero processes. Only pick nodes with **`category_is_active: 1`** — `0` means archived and the write will be rejected or hidden. *(Used by the publish flow.)*

### GET `/users?limit=<n>`
The Automation Hub users on the tenant (verified live): paged envelope with the list under **`data.users[]`**; each entry carries **`user_email`**, `user_first_name`/`user_last_name`, and `user_is_active`.

**It is not the ground truth for who can own a process, and must never gate a publish.** Two defaults make it under-report: `invite` defaults to **activated users only**, so a user who has only ever used the API or CLI is missing from it while being perfectly able to own a process; and results are paged (default 20) under an ordering that is not deterministic when no search text is given, so a user can be absent from one page and present in another. Pass **`?s=<email>&invite=all`** for a scoped, server-side lookup — both parameters, since search alone still hides a not-invited user. The authority for the signed-in identity is the auth/identity call, and the authority for whether an owner is acceptable is the create response. *(Optional in the publish flow.)*

### GET `/appinventory?limit=<n>`
The tenant's application inventory (paged; entries carry the application id, name, version, language). **These ids are the `value` answers for the application questions** ("Applications used", "Thin applications used"; thin-apps holds only the answered systems the material calls thin/Citrix clients, so `[]` when none, even when the schema flags it `required`); systems not listed go in `new_applications` (see `POST /idea-from-schema`). *(Used by the publish flow whenever the material names systems.)*

### GET `/automations?search=<text>&limit=<n>&offset=<n>`
Search/list processes. Returns a paged list (results under a resource key, e.g. `processes`, or a bare array). Use to resolve a name → `process_id`. *(Used by the get flow.)*

### GET `/automations/{id}`
Fetch one process by numeric id (or slug). Returns the full process record (can be ~300 fields; project to the ones you need for display). *(Used by the get flow.)*

### GET `/automations/{process_id}/documents`
List a process's documents (key `documents`). Each entry carries `document_id`, `document_title`, `document_type_id`, a nested `file` (with `originalname`, the uploaded file name, and `mimetype`) for file-backed documents, and **either** a `file_id` (file-backed — downloadable) **or** an `embed_link` (link-backed — nothing to download; show the URL). *(Used by both flows.)*

### GET `/download/file/{file_id}`
Download a file-backed document's **bytes**. `{file_id}` is the `file_id` from the documents list — **not** the `document_id`. The response body is the raw file — save it with `curl -o <path>`; there is no JSON envelope. Link-backed documents (`file_id` absent) cannot be downloaded — present their `embed_link` instead. *(Used by the get flow.)*

### GET `/automations/{id}/components`  *(optional)*
Linked components for the process.

### PATCH `/idea-flows/automations/{automationId}/idea-flow`  *(RPANAV-19226)*
Move an automation into another idea flow (e.g. convert an idea into a Business Process) — the same server logic as the profile page's **Change Idea Flow** action. Body: `{ "idea_flow_id": <id>, "phase_variable": "<P>", "status_variable": "<S>" }`, all three from the target's `/idea-flows` entry. *(Used by the change-idea-flow flow.)*

- **400** — a phase/status not in the target flow, a `change-request` target (a Change Request needs a parent automation), or the automation's *current* status no longer exists in its flow (UI-only fix). **403** — the **Change idea flow** action is missing at the automation's current phase/status (configurable per status) or the user's role lacks it (default: account owner, system admin, program manager), no permission to submit into the target flow, or a user with no tenant roles; don't retry. **404** — unknown automation or `idea_flow_id`, or (for the route itself) a server without the capability (such a server also sends no `Idea flow type`).
- Slow (~20 s+): it re-saves the whole automation. Never retry on a slow response, a timeout or a 5xx — re-read the automation first. The new flow id is committed **before** the full re-save, so a failure can leave it half moved (new flow, old phase/type).
- **A 200 is not proof:** a failed re-save can still answer 200 (an AH bug, to be fixed). Confirm with a read-back: `process_submission_type` matches the target type, `phase_key` / `phase_status_key` (`<PHASE>_<STATUS>`) match what was sent. `process_submission_type` is re-written from the Overview assessment's "Idea source (legacy)" answer (options 1–8 only), so a move into a `custom` flow most likely keeps the old value — check the phase keys instead.
- No same-flow guard: moving into the flow the automation is already in re-saves it and returns 200. Check first; changing phase within a flow is a different operation, not this one.
- Side effects: when the `phase_status_key` changes it counts as a phase change (followers/upvoters get the usual emails/notifications; user tasks are created); history shows the changed overview answers (no dedicated "flow changed" entry); collaborators and roles are not touched.
- Data: answers carry over for assessment types both flows share, migrated to the target flow's version only when the saved version is the source flow's default (manually changed versions are left alone); assessments the target doesn't use are hidden, not deleted; a parent-automation link is cleared.

### GET `/automations/{id}/comments?page=<n>&limit=<n>`  *(RPANAV-19227)*
The comments on an idea or Business Process, as they appear in its Comments section. Paged by **top-level** comment, newest first; each carries all its replies (one level deep). `page` is 1-based (default 1). `limit` is up to 100 (default 20) — a valid `limit` of **5 or less is served as 20**, and `page` ≤ 0, `limit` ≤ 0, a non-integer, or `limit` > 100 is a **400** `error_invalid_pagination`. Response `data`: `{ page, pageIndex, pageSize, totalItems, totalPages, comments: [...] }`. `pageSize` is the number of comments **on this page**, not the requested limit. Each comment: `comment_id`, `parent_comment_id` (null at top level), `text` (plain), `text_draftjs` (stored rich text), `author` `{ user_id, email, first_name, last_name }`, `created_epoch` / `updated_epoch` (ms), `num_replies`, `replies`. With a user token, the user must be able to view the automation (else **403**). A token with no associated user can read any automation in the tenant. An unknown id is **404**. *(Used by the comments flow.)*

### POST `/automations/{id}/comments`  *(RPANAV-19227)*
Post a comment or a reply. Body: `{ "text": "<plain text>", "parent_comment_id": <top-level comment id, optional>, "submitter": "<email, optional>" }`. `text` must contain a non-whitespace character and be at most **2000** characters. Line breaks (LF or CRLF) are kept, and Markdown is not rendered. A `parent_comment_id` that is a reply, or belongs to another automation, is a **400**. The author is the token's user. Only a token with **no** associated user uses `submitter`, which must be an active AH user who can view the automation. It notifies followers exactly as a UI comment does. Not idempotent: re-read before re-posting after a timeout. Returns the created comment (same shape as above). *(Used by the comments flow.)*

### PUT `/automations/{id}/comments/{commentId}`  *(RPANAV-19248)*
Replace the text of a comment or reply. Body: `{ "text": "<plain text>", "submitter": "<email, optional>" }`, with the same text rules as POST. The new text replaces the whole comment, including any mentions or formatting made in the UI. Only the comment's **author** may edit it: the token's user, or — for a token with no associated user — the active user named by `submitter`; anyone else gets a **403** `error_non_poster_attempting_edit`. The author must also be able to view the automation (**403**). A comment that doesn't exist on that automation, is already deleted, or isn't in its Comments section (a question or document comment) is a **404** `error_comment_not_found`. Newly mentioned users are notified as for a UI edit. Idempotent. Returns the edited comment (same shape as above). *(Used by the comments flow.)*

### DELETE `/automations/{id}/comments/{commentId}`  *(RPANAV-19248)*
Soft-delete a comment or reply. `submitter` (token with no user only) goes in the **query** (`?submitter=<email>`) or a JSON body; the body wins when both are sent. Same author-only rule, 403s and 404s as PUT; a repeated delete is a 404. Deleting a reply updates its parent's reply count; deleting a top-level comment hides its replies too. Also updates the automation's comment count and last-updated date. Returns `{ "comment_id": <id>, "deleted": true }`. *(Used by the comments flow.)*

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Validation — missing required field, invalid enum, empty `user_inputs`, missing `OVERVIEW_NAME` |
| 401 | Unauthorized — token missing/expired, or `x-ah-openapi-auth` was wrongly sent |
| 403 | Forbidden — the user lacks the AH permission (authorization = the user's real AH role) |
| 404 | Wrong URL, or AH not available on the tenant — see **Automation Hub not available on this tenant** below |
| 409 | Duplicate process name; on a document attach, a duplicate document (see `POST /automations/{process_id}/documents`) |

### Automation Hub not available on this tenant

Two distinct cases, with **different remedies** — don't collapse them, the advice differs:

**1. AH is not enabled for the tenant.** The tenant has no Automation Hub service at all. Signals: a **404** whose body says `not found in organization`, or a **3xx redirect** to `portal_/unregistered` (following it would surface an HTML portal page as a JSON parse error). The user cannot fix this themselves — report exactly:

> Please contact your administrator to enable Automation Hub on this tenant.

**2. AH is reachable but the tenant was never onboarded into it.** The service answers **422 Tenant Lookup Error** on every call. This one *is* self-service — report exactly:

> Automation Hub is reachable for this tenant but has not finished setup. Open Automation Hub in the browser once to complete it, then retry.

In both cases: **stop after reporting** — do not retry, do not fall back to an admin OpenAPI token, and do not attempt the write against another tenant unless the user asks. Quote the message verbatim; don't paraphrase it.

**Making the signals observable from `curl`.** `curl` reports the status but not *where* a 3xx points, so the first call each flow makes against the tenant asks for both:

```bash
curl -s -w "\n%{http_code} %{redirect_url}" …
```

The last line is then `<status> <redirect target>`: `%{redirect_url}` is empty on any non-3xx and carries the resolved `Location` on a 3xx — which is what makes the `portal_/unregistered` case above distinguishable from an ordinary redirect. **Never add `-L`.** Following the redirect throws away the one diagnosable signal and hands you an HTML portal page, which then fails as a JSON parse error — exactly the generic failure this section exists to prevent.
