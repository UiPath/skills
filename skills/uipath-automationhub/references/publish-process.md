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

## Step 4: Assemble the process payload

Gather the process fields — from the caller's supplied data (e.g. a Process Scribe hand-off object) or by asking the user. Then build `user_inputs` using the template's **structure** but **real values**:
- Place each value in its `AssessmentType > section > question` slot.
- Follow the template's wrapping per field: most are `{ "value": <v> }`; owner/submitter questions take a **direct string** (no `value` wrapper).
- Convert enum labels to their `answer_option` codes taken from that field's own `enum` in the schema — **never** reuse the template's placeholder code. Send integers as numbers.
- **Category** (`OVERVIEW_CATEGORY`) must be a **valid category id on this tenant**, not the template's `1`. Resolve one by reading `categories[].category_id` (and `subcategories`) from an existing process (`GET /automations/{anyId}`), or ask the user.
- **Owner/submitter emails must be real, provisioned AH users** on this tenant (a bad address 400s).

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

- **201** → read `process_id` from the **top level** of the response (not nested in `data`). Keep it for Step 6.
- **400** → fix and retry. The message shapes seen live:
  - `errorDetails: { "<question>": ["An answer selection is required…"] }` → that required field is missing/empty; add it.
  - `errorDetails: {}` with `"Please fill in all the required information"` → a required field the API **won't name** is missing — almost always **owner** (`OVR-PROCESS_OWNER`) or **submitter** (`OVR-OVERVIEW_PROCESS_SUBMITTER`). Send the full required set from Step 4.
  - `"Invalid Category Id."` → `OVERVIEW_CATEGORY` isn't a real category on this tenant (see Step 4).
  - `Cannot set properties of undefined (setting 'co_question_answer_option_value')` → an enum field carries an invalid `answer_option` code (you left a template placeholder in). Use a code from that field's `enum`.
- **401** → re-authenticate. **409** → duplicate name; ask the user for a new name or stop.

## Step 6: Attach documents (PDD/SDD)

For each document the caller wants attached (link-based — an embed/link URL + metadata, per the reference):

```bash
curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DOC_PAYLOAD" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```

Build `$DOC_PAYLOAD` per `ProcessDocumentValidator` — verified-live required fields:

```json
{ "document_title": "PDD - <name>", "document_description": "<desc>", "document_type_id": <int>, "embed_link": "https://…" }
```

- `document_title`, `document_description`, `document_type_id` are all required (note the field is `document_title`, **not** `document_name`).
- You **must** also supply **exactly one** of `embed_link` or `file` — this is enforced in the handler, not the JSON schema, so it 400s with `"One and only one of embed_link or file need to be specified."` if omitted. This skill uses `embed_link` (link-based); byte upload via `file` is not usable yet.

Record each returned `document_id`. On 400, surface the validation message and continue with the remaining documents.

> Raw file-byte upload is not supported here (the `media` endpoint is not usable yet). Attach documents by link/URL. If the caller only has bytes, host them first and pass the link.

## Step 7: Report

Summarize: the created `process_id`, the attached document ids (and any that failed), and a link to view it:

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12), SDD ✓ (doc 13)
  View: {baseUrl}/{org}/{tenant}/automationhub_/process-repository
```

## Notes

- **Cloud token only** — never send `x-ah-openapi-auth` / `x-ah-openapi-app-key`. Authorization is the user's real AH permissions.
- **Always** `POST /idea-from-schema` (not `/automations`) and **always** include `idea_flow_id`.
- The schema is fetched live, so the flow adapts automatically if fields change on the tenant.
- Idempotency: AH is the system of record for the *approved* process — publish once after approval. A duplicate name returns 409; decide up front whether to update-in-place (out of scope here) or treat as an error.
- To read a process back, use the [`get-process.md`](get-process.md) flow.
