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
All idea flows (workflow types) on the tenant. Each element has `Idea flow name` (e.g. "Business Process") and `Idea flow ID` (number). Response wrapped as `{ message, statusCode, data: [...] }`. *(Used by the publish flow.)*

### GET `/idea-schema?idea_flow_id={id}`
Full JSON schema for an idea flow + a ready-made `user_inputs` template. Response wrapped as `{ status: "success", data: {...} }`:
- `data.properties.schema.properties` — field definitions, 3-level nested (Assessment Type > Section > Question); enums carry `answer_option` codes + labels in `custom_properties`.
- `data.user_inputs` — the exact POST body template ("fill in the blanks"). Most fields wrap as `{ "value": <v> }`; owner/submitter questions take a direct string (no wrapper); questions with no example are omitted.

*(Used by the publish flow.)*

### POST `/idea-from-schema`
Create a process from the schema. **Use this, not `POST /automations`** (the `/automations` alias 404s in some deployments).

Body:
```json
{ "idea_flow_id": <id>, "user_inputs": { "<AssessmentType>": { "<section-ahid>": { "<question-key>": { "value": "<v>" } } } } }
```
**Do not POST `data.user_inputs` verbatim** — its example values are placeholders that the API rejects. Replace each with a real value; in particular resolve a **valid** `OVERVIEW_CATEGORY` id (the template's `1` → `Invalid Category Id`) and real `answer_option` codes (a placeholder code → backend `co_question_answer_option_value` crash).

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

  Pick by the document's kind: PDD → `1`, SDD → `2`; when unsure, default to `9` (MISC).
- Plus **exactly one** of `file` or `embed_link` — an XOR enforced in the handler, not the schema. Sending both, or neither, 400s with `"One and only one of embed_link or file need to be specified."`
- **`file` — byte upload, the default.** Validated by `EncodedFileValidator`: `file_name`, `mimetype`, `file_content`, `file_encoding` are all required and must be non-empty, and `file_encoding` must be `base64` — the only accepted value. No mimetype allowlist. The JSON body limit is **300mb**, so a PDD-sized `.docx` or `.md` fits with room to spare.
- **`embed_link`** — use only when the document already lives at a URL and the bytes are not available.

Returns the standard envelope with the created id **nested under `data`** — read **`data.document_id`**. *(Used by the publish flow.)*

### POST `/automations/{process_id}/media`  *(not needed for documents)*
A separate byte-upload route taking the same `EncodedFileValidator` shape. Documents do **not** need it — `/documents` accepts `file` directly.

### GET `/hierarchy`
The tenant's category tree (verified live): `data.levels` (level names) + `data.categories[]`, each with `category_id`, `category_name`, `category_is_active`, and nested `subcategories`. **This is how to resolve a valid `OVERVIEW_CATEGORY` id** — it works even on a tenant with zero processes. Only pick nodes with **`category_is_active: 1`** — `0` means archived and the write will be rejected or hidden. *(Used by the publish flow.)*

### GET `/users?limit=<n>`
The Automation Hub users on the tenant (verified live): paged envelope with the list under **`data.users[]`**; each entry carries **`user_email`**, `user_first_name`/`user_last_name`, and `user_is_active`. **This is how to resolve a valid owner/submitter email** — both must be provisioned AH users (prefer `user_is_active: 1`), and this endpoint is the ground truth. *(Used by the publish flow.)*

### GET `/appinventory?limit=<n>`
The tenant's application inventory (paged; entries carry the application id, name, version, language). **This is the valid-answer set for tenant-required application questions** ("Applications used", "Thin applications used") in the publish flow. *(Used by the publish flow when the tenant requires application questions.)*

### GET `/automations?search=<text>&limit=<n>&offset=<n>`
Search/list processes. Returns a paged list (results under a resource key, e.g. `processes`, or a bare array). Use to resolve a name → `process_id`. *(Used by the get flow.)*

### GET `/automations/{id}`
Fetch one process by numeric id (or slug). Returns the full process record (can be ~300 fields; project to the ones you need for display). *(Used by the get flow.)*

### GET `/automations/{process_id}/documents`
List a process's documents (key `documents`). Each entry carries `document_id`, `document_title`, `document_type_id`, and **either** a `file_id` (file-backed — downloadable) **or** an `embed_link` (link-backed — nothing to download; show the URL). *(Used by both flows.)*

### GET `/download/file/{file_id}`
Download a file-backed document's **bytes**. `{file_id}` is the `file_id` from the documents list — **not** the `document_id`. The response body is the raw file — save it with `curl -o <path>`; there is no JSON envelope. Link-backed documents (`file_id` absent) cannot be downloaded — present their `embed_link` instead. *(Used by the get flow.)*

### GET `/automations/{id}/components`  *(optional)*
Linked components for the process.

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Validation — missing required field, invalid enum, empty `user_inputs`, missing `OVERVIEW_NAME` |
| 401 | Unauthorized — token missing/expired, or `x-ah-openapi-auth` was wrongly sent |
| 403 | Forbidden — the user lacks the AH permission (authorization = the user's real AH role) |
| 404 | Wrong URL, or AH not enabled on the tenant |
| 409 | Duplicate process name |
