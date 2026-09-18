# Publish a Process to Automation Hub — `uip ah` CLI flow

Creates one process from a schema-driven payload and attaches its documents (PDD/SDD), using `uip ah` commands. Auth is handled by the CLI (Delegate env-auth or `uip login`) — you never touch a token.

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The domain contract (required fields, wrapping rules, document types) is the same one [`api-endpoints.md`](api-endpoints.md) documents — the CLI only changes the transport.

## Step 1: Verify connectivity (and fetch the idea flows)

```bash
uip ah idea-flows list --output json
```

- `Result: Success` → keep `Data` (flow names + ids) and tell the user "Connected to Automation Hub."
- Auth failure → tell the user to run `uip login` (or, in Delegate, to sign in). Never ask for a raw token.
- `Failure` mentioning the tenant/enablement → AH is not available on this tenant. Report the message for the matching case, verbatim, from [`cli-commands.md`](cli-commands.md) → **Automation Hub not available on this tenant** — then **stop**; nothing later in this flow can succeed.

## Step 2: Pick the idea flow

Default to the entry whose `Name` contains "Business Process" (case-insensitive); take its `Id`. If the caller named a different flow, use that. Several candidates → ask. None → say Business Process flows may not be enabled and stop. Store `IDEA_FLOW_ID`.

## Step 3: Fetch the schema

```bash
uip ah automations schema get --idea-flow-id $IDEA_FLOW_ID --destination ./ah-schema.json --output json
```

> 📁 **Working files (`ah-schema.json`, `ah-answers.json`, and any document files you generate for upload) go in the current working directory — never `/tmp`.** Hosted runtimes (e.g. the Delegate) sandbox their file tools to the session workspace: a file written to `/tmp` is readable by the CLI but every file-tool access to it fails with an access-denied error.

Read `./ah-schema.json`: the field catalog is under `properties.schema.properties` (Assessment Type > Section > Question; enums carry `answer_option` codes) and `user_inputs` is the payload template.

> ⚠️ **Do NOT submit `user_inputs` verbatim** — its example values are placeholders the API rejects (category `1`, placeholder answer codes, example emails). Shape only.

## Step 4: Collect the inputs, then assemble the answers file

**Collect every required input BEFORE creating** — same rules as the API flow, with CLI discovery:

First **enumerate the tenant's actual required set from the schema file**: every `required`-flagged question, plus owner + submitter (enforced but never flagged). Tenant admins add required questions (commonly "Applications used"/"Thin applications used") — the baseline table is a minimum, never the whole list. Resolve each: from the caller's material, the recipes below, or `AskUserQuestion` — never by inventing.

| Input | Recipe |
|---|---|
| Process **name** | Ask. Non-empty; duplicates fail with a 409-style error. |
| **Description** | Ask, or derive from the material and confirm. |
| **Category id** | `uip ah categories get` → pick from `Data.Categories` (**`category_is_active: 1` only**); several plausible → ask with names. Never the template's `1`. |
| **Documentation** answer code | The `PROCESS_DOCUMENTS` question's own `enum` in the schema — match by label, send its `answer_option` code. |
| **Owner email** | **`uip ah auth-info get`** → `Data.User.Email` is the signed-in identity and the default owner. That call is the authority; do not substitute an address from any list. |
| **Submitter email** | Same as owner; usually the same person. |
| **Application questions** (when tenant-required) | `uip ah applications list` → match the material's systems. Missing ones: **create them** (below). If creating fails for any reason, pick from the listed entries and record the real systems in the description — never block the publish on applications. |

The discovery commands are independent — run the ones you need (`auth-info get`, `categories get`, `applications list`) **in a single shell invocation** rather than one per turn; each is fast, the round-trips between them are not.

**Never block the publish on an owner lookup.** `uip ah users list` defaults to activated users only, so a user who has only ever used the API or CLI is *absent from it despite existing and being able to own a process*. Looking them up is optional and informational; if you do it, scope it and treat a miss as no signal:

```bash
uip ah users list --search "<owner-email>" --invite-status all
```

`--search` is server-side, so it is not subject to the default page size; `--invite-status all` is required, because without it a not-invited user returns zero rows. **Pass both or the lookup is worse than useless** — search alone reports "no such user" for exactly the users this guidance is about.

Whatever that returns, use the `auth-info` email verbatim, submit, and let the API decide. Only a real `Cannot identify owner by email` from the create is an owner problem (Step 5).

### Creating a missing application

`uip ah applications` has no `create` verb — **creation happens through `update`**, by sending an element whose `application_id` is `null`. The service upserts: an element with a real id updates that application, an element with `null` inserts a new one. (The CLI's own `update --help` claims it cannot add one; that is wrong, and it is why agents give up here.)

All five fields are required by the request schema, and `categoryIds` needs at least one valid id from `uip ah categories get`:

```bash
cat > ./new-apps.json <<'JSON'
[{ "application_id": null,
   "application_name": "SUNAT Portal",
   "application_version": "1.0",
   "application_language": "English",
   "categoryIds": [1] }]
JSON

uip ah applications update --file ./new-apps.json --output json
```

Then re-read `uip ah applications list` and use the new ids in the answer.

**This requires the `MANAGE_APP_INVENTORY` permission**, which ordinary roles (`ah-standard-user`, `ah-authorized-user`) do not hold. A non-admin gets:

```
{"Result":"Failure","Message":"This user is not permitted to perform this action based on their role. (403 Forbidden)"}
```

**If creating fails for any reason — 403, a validation error, a bad category id, anything — fall through; never retry it and never stop.** Pick the closest entries from `applications list` to satisfy the required field, and name the real systems in `OVERVIEW_DESCRIPTION` (e.g. "Systems per PDD: Salesforce, CREDILEX, SUNAT Portal — not in tenant inventory"). The process record is what matters; applications are editable afterwards. **Never abandon a publish because an application is missing or uncreatable, and never silently pass off an unrelated application as the real one — say what you substituted.**

Write the answers to `./ah-answers.json` as the filled `user_inputs` structure (the CLI accepts the whole schema-get document or just the answers map). Wrapping rules unchanged: most fields `{ "value": <v> }`; owner/submitter are **direct strings**; enum codes from that field's own `enum`; integers as numbers. Show the user a concise preview and get a confirm before writing.

## Step 5: Create the process

```bash
uip ah automations create --from-schema --idea-flow-id $IDEA_FLOW_ID --file ./ah-answers.json --output json
```

- `Result: Success` → **`Data.Id`** is the new process id. A success means it WAS created — never re-run on a confusing field read (that duplicates).
- `ValidationError`/`Failure` → the `Message`/`Instructions` carry the service's validation text; the same causes as the API flow apply (unnamed required field → owner/submitter first, then diff against the schema's required set; `Invalid Category Id`; placeholder answer codes). Fix and retry **once**.
- `Cannot identify owner by email` → **not a typo'd address; do not retry with a different email.** The account is authenticated but has never been activated on this tenant. Confirm with `uip ah auth-info get` — `IsActive: 1` plus a role list proves the identity is real — then tell them to open Automation Hub in a browser once and sign in, and retry unchanged:

  ```
  https://cloud.uipath.com/<org>/<tenant>/automationhub_
  ```

  Build that URL from the org/tenant already in the authenticated CLI context, never from the error output. Nothing was created, so the retry is safe. Newer Automation Hub versions accept these users with no sign-in at all, so on an up-to-date tenant this error should not appear.

## Step 6: Attach documents (PDD/SDD)

Attach every supplied document — default to all; ask only when two files look like the same document in different formats (in the Step 4 round). Per document:

```bash
uip ah documents create $PROCESS_ID \
  --title "PDD - <name>" --description "<desc>" \
  --document-type-id <n> --file "<path>" --output json
```

- `--document-type-id` from the fixed platform table in [`api-endpoints.md`](api-endpoints.md) — read it there; do not guess ids.
- `--file` uploads the bytes (the CLI base64s it; any file type; 200 MB cap). Use `--embed-link <url>` *instead* only when the caller has a URL and no bytes — exactly one of the two, and never invent a URL.
- Record `Data.Id` (document id) and `Data.FileId` from each response. On a validation error, surface the message and continue with the remaining documents.

## Step 6b (optional): Link a Studio Web solution

When the caller wants the process linked to a Studio Web solution (or supplies one), set the `OVR-OVERVIEW_STUDIO_WEB_LINK` question — at create time inside `user_inputs`, or afterwards via `uip ah automations update $PROCESS_ID --file <answers.json>`. The answer's exact value format (JSON-string `value` with a required `url`, `hasProcessMap` semantics, empty string to unlink) is a domain fact — read it in [`api-endpoints.md`](api-endpoints.md) (**Studio Web link**), don't restate it.

- **Resolve the solution from the caller — no CLI discovery exists.** No stable `uip` command lists Studio Web solutions today, so ask the user (`AskUserQuestion`) for the solution's **designer URL** — they can copy it from the browser address bar with the solution open in Studio Web. If they instead supply a solution id + project id, build the URL per the catalog's designer-URL shape (`projectId` = the solution's ProcessOrchestration project). **Never invent, guess, or search for a solution id or URL.**
- If the caller doesn't know whether the solution has a `.bpmn` (the `hasProcessMap` condition), omit that field rather than guessing.

## Step 7: Verify, then report

Both verification reads are independent — run them in **one shell invocation**:

```bash
uip ah documents list $PROCESS_ID --output json
uip ah automations get $PROCESS_ID --all-fields --output json   # read process_slug from Data
```

Every attached document id must appear in the documents list (file-backed ones with a `FileId`). Missing → report it failed; never claim an attach you didn't see in this list.

The report **MUST end with both View deep links** — the URL segment is `process_slug` from the `--all-fields` record.

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12, file 42), SDD ✓ (doc 13, file 43)
  View process:   {Data.Tenant.Url}/automation-profile/{process_slug}
  View documents: {Data.Tenant.Url}/automation-profile/{process_slug}/documentation
```

Build the links from the tenant the write went to: `uip ah auth-info get` → `Data.Tenant.Url` is **already the full AH tenant base** (`…/{org}/{tenant}/automationhub_`) — append only `/automation-profile/{process_slug}` (+ `/documentation`), never re-append org/tenant segments.
