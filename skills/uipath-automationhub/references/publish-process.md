# Publish a Process to Automation Hub

Creates one process in Automation Hub from a schema-driven payload and attaches its documents (PDD/SDD). Authenticates with the **user's cloud token** — the user does **not** need an admin-generated OpenAPI token.

> Auth, base/gateway URL, headers (and the header to **never** send), and every endpoint below are defined in [`api-endpoints.md`](api-endpoints.md). Resolve `$ACCESS_TOKEN` / `$BASE_URL` / `$ORG` / `$TENANT` via the shared **Authentication** section in [`../SKILL.md`](../SKILL.md) before starting.

## Step 1: Verify connectivity (and fetch the idea flows)

Verify the resolved token with a cheap call — this also fetches the idea flows you need next:

```bash
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-flows"
```

- **200** → save the `data` array (reused in Step 2) and tell the user "Connected to Automation Hub."
- **401** → token missing/expired: if it came from `~/.uipath/.auth`, ask the user to run `uip login` again; re-resolve and retry. **Never** add `x-ah-openapi-auth` to "fix" a 401 — that routes to the admin-token path and guarantees failure.
- **403** → the user is authenticated but lacks AH access on this tenant.
- **404 / network** → wrong URL or AH not enabled; confirm the org/tenant.

Do not proceed until you have a 200.

## Step 2: Pick the idea flow

From the saved `/idea-flows` `data` array:
1. Default to the entry whose `Idea flow name` contains "Business Process" (case-insensitive) and take its `Idea flow ID`.
2. If the caller specified a different flow, use that. If neither is found, list the available names + IDs and ask the user which to use. If none exist, tell the user Business Process flows may not be enabled and stop.

Store `idea_flow_id`.

## Step 3: Fetch the schema

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-schema?idea_flow_id=$IDEA_FLOW_ID"
```

Parse `data.properties.schema.properties` for the field catalog (Assessment Type > Section > Question; note types, required flags, enum `answer_option` codes/labels) and keep `data.user_inputs` as the payload template. The process-name question (key contains `OVERVIEW_NAME`) is **required**.

> ⚠️ **Do NOT POST `data.user_inputs` verbatim.** The template ships **example/placeholder values that the API rejects** — e.g. `OVERVIEW_CATEGORY: 1` (→ `Invalid Category Id`), a placeholder `PROCESS_DOCUMENTS` answer-option that triggers a backend `co_question_answer_option_value` crash, and `First.last@example.com` owner/submitter emails. Treat the template as **shape only** and replace every value with a real one (below).

## Step 4: Collect the inputs, then assemble the payload

**Collect every required input BEFORE the first POST** — do not discover gaps one 400 at a time.

First, **enumerate the tenant's actual required set from the live schema** (Step 3): walk `data.properties.schema.properties` and collect every question whose `required` flag is set — tenant admins can mark **additional** questions required (commonly "Applications used" and "Thin applications used"), so the baseline table below is the *minimum*, never the whole list. Add the two questions the backend enforces without flagging (owner + submitter). Then resolve a value for **each** required question: from the caller's supplied data (e.g. a Process Scribe hand-off object), from the discovery recipes below, or via `AskUserQuestion` — never by inventing one.

The six baseline inputs:

| Input | How to resolve when not supplied |
|---|---|
| Process **name** | Ask the user. Non-empty; a duplicate name 409s. |
| **Description** | Ask the user, or derive from the supplied material and confirm. |
| **Category id** | `GET /hierarchy` → pick from `data.categories[]` (`category_id`, `category_name`, nested `subcategories`) — **only nodes with `category_is_active: 1`** (0 = archived). One clear fit → propose it; several plausible → `AskUserQuestion` with the names. **Never send the template's `1`.** (Works on an empty tenant — do not depend on an existing process.) |
| **Documentation** answer code | The `PROCESS_DOCUMENTS` question's own `enum` in the schema — match by **label** (e.g. "Standard Operating Procedure") and send that `answer_option` code. Never reuse the template's placeholder code. |
| **Owner email** | `GET /users` → the list is under `data.users[]`, the field is **`user_email`** (prefer `user_is_active: 1`); a non-listed address 400s (`Cannot identify owner by email`). Default to the signed-in user — confirm which listed email is theirs. |
| **Submitter email** | Same recipe as owner; usually the same person. |

**Tenant-required application questions** ("Applications used", "Thin applications used", and similar): the valid answers are the tenant's application inventory — `GET /appinventory` (paged; entries carry the app id, name, version, language). Match what the caller's material names, but if the documents leave the systems unconfirmed, `AskUserQuestion` with the inventory entries — **never record an application the material does not support**. Follow that question's own schema shape for how the selected entries are encoded in `user_inputs`.

Then build `user_inputs` using the template's **structure** but the **collected values**:
- Place each value in its `AssessmentType > section > question` slot.
- Follow the template's wrapping per field: most are `{ "value": <v> }`; owner/submitter questions take a **direct string** (no `value` wrapper).
- Convert enum labels to their `answer_option` codes taken from that field's own `enum` in the schema — **never** reuse the template's placeholder code. Send integers as numbers.

**Required fields for `idea_flow_id` = Business Process** (verified live — the backend enforces owner + submitter even though the schema's `required` flags do **not** list them):

| Question (key) | Section | Shape | Value |
|---|---|---|---|
| `OVR-OVERVIEW_NAME` | `ah-section-ovr-0-0` | `{"value": "<name>"}` | process name, non-empty |
| `OVR-OVERVIEW_DESCRIPTION` | `ah-section-ovr-0-0` | `{"value": "<desc>"}` | description |
| `OVR-OVERVIEW_CATEGORY` | `ah-section-ovr-0-0` | `{"value": <int>}` | **valid** category id |
| `OVR-PROCESS_DOCUMENTS` | `ah-section-ovr-0-0` | `{"value": ["<answer_option code>"]}` | code from the field's `enum` |
| `OVR-PROCESS_OWNER` | `ah-section-ovr-0-0` | `"<email>"` (direct string) | real AH user |
| `OVR-OVERVIEW_PROCESS_SUBMITTER` | `ah-section-ovr-0-1` | `"<email>"` (direct string) | real AH user |

Include only sections that have at least one populated field. Show the user a concise preview (name + key fields, and "show raw JSON" on request) and get a confirm before writing.

## Step 5: Create the process

```bash
curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-from-schema"
```
where `$PAYLOAD` is `{ "idea_flow_id": <id>, "user_inputs": { … } }`.

- **201** → the envelope is `{ "message": "Resource Created", "statusCode": 201, "data": { … } }` — read **`data.process_id`** (it is nested, NOT top-level). Keep it for Step 6. A 201 means the process WAS created: if a field read comes back undefined, re-read the response — **never re-POST** (that creates a duplicate and 409s).
- **400** → fix and retry. The message shapes seen live:
  - `errorDetails: { "<question>": ["An answer selection is required…"] }` → that required field is missing/empty; add it.
  - `errorDetails: {}` with `"Please fill in all the required information"` → a required field the API **won't name** is missing. Check in order: (1) owner (`OVR-PROCESS_OWNER`) / submitter (`OVR-OVERVIEW_PROCESS_SUBMITTER`) — enforced but never flagged; (2) **diff your payload against every `required`-flagged question in the live schema** — tenant admins add required questions (e.g. "Applications used" / "Thin applications used"), and a payload missing any of them gets this same generic 400. Fill the gaps (Step 4 recipes), then retry once.
  - `"Invalid Category Id."` → `OVERVIEW_CATEGORY` isn't a real category on this tenant (see Step 4).
  - `Cannot set properties of undefined (setting 'co_question_answer_option_value')` → an enum field carries an invalid `answer_option` code (you left a template placeholder in). Use a code from that field's `enum`.
- **401** → re-authenticate. **409** → duplicate name; ask the user for a new name or stop.

## Step 6: Attach documents (PDD/SDD)

Attach each document the caller supplies — **default to all of them**; never silently skip a supplied file. The one exception: if two supplied files appear to be the *same document in different formats*, ask which to attach — as part of the single up-front clarifying round (Step 4), not a separate round. **Upload the bytes** — the endpoint takes a base64 `file` object directly, so nothing needs hosting first. Fall back to `embed_link` only when the caller has a URL instead of bytes.

```bash
curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DOC_PAYLOAD" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```

Build `$DOC_PAYLOAD` per `ProcessDocumentValidator`:

```json
{
  "document_title": "PDD - <name>",
  "document_description": "<desc>",
  "document_type_id": <int>,
  "file": {
    "file_name": "<name>.docx",
    "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_content": "<base64 of the file bytes>",
    "file_encoding": "base64"
  }
}
```

- `document_title`, `document_description`, `document_type_id` are all required (the field is `document_title`, **not** `document_name`).
- **`document_type_id` comes from the fixed platform table in [`api-endpoints.md`](api-endpoints.md)** — PDD → `1`, SDD → `2`, otherwise `9` (MISC). Never guess other ids.
- Supply **exactly one** of `file` or `embed_link` — an XOR enforced in the handler, not the JSON schema. Both, or neither, 400s with `"One and only one of embed_link or file need to be specified."`
- **`file` (default).** Base64-encode the file and send `file_name`, `mimetype`, `file_content`, `file_encoding`. `file_encoding` must be the literal `base64` — any other value fails with `"Invalid file."`, as does an empty `file_name`, `mimetype`, or `file_content`. Body limit is 300mb.
- Common mimetypes: `.docx` → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `.md` → `text/markdown`, `.pdf` → `application/pdf`.
- Generate the base64 without loading the file into the conversation:

```bash
base64 -i "<FILE_PATH>" | tr -d '\n'   # macOS/Linux; use `base64 -w0 "<FILE_PATH>"` on GNU coreutils
```

- **`embed_link` (alternative).** Use only when the caller has a URL and no bytes: replace the `file` object with `"embed_link": "https://…"`. Never invent a URL.

Record each returned id — it is nested: read **`data.document_id`** from the response envelope. On 400, surface the validation message and continue with the remaining documents.

## Step 7: Verify, then report

**Verify before claiming success** — read the process back and confirm the documents landed:

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```

Check every attached `document_id` appears (file-backed entries also carry a `file_id`). If one is missing, report it as failed — never report a document as attached without seeing it in this list.

Then summarize with **deep links straight to the created process and its documents** — the 201 response's `data.process_slug` is the URL segment (URL-encode it). Emit these links only after the verification read-back above succeeded:

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12, file 42), SDD ✓ (doc 13, file 43)
  View process:   {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}
  View documents: {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}/documentation
```

Always build the links from the **same org/tenant** the process was created on — never another tenant's segments.

## Notes

- **Cloud token only** — never send `x-ah-openapi-auth` / `x-ah-openapi-app-key`. Authorization is the user's real AH permissions.
- **Always** `POST /idea-from-schema` (not `/automations`) and **always** include `idea_flow_id`.
- The schema is fetched live, so the flow adapts automatically if fields change on the tenant.
- Idempotency: AH is the system of record for the *approved* process — publish once after approval. A duplicate name returns 409; decide up front whether to update-in-place (out of scope here) or treat as an error.
- To read a process back, use the [`get-process.md`](get-process.md) flow.
