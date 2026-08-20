# Publish a Process to Automation Hub — `uip ah` CLI flow

Creates one process from a schema-driven payload and attaches its documents (PDD/SDD), using `uip ah` commands. Auth is handled by the CLI (Delegate env-auth or `uip login`) — you never touch a token.

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The domain contract (required fields, wrapping rules, document types) is the same one [`api-endpoints.md`](api-endpoints.md) documents — the CLI only changes the transport.

## Step 1: Verify connectivity (and fetch the idea flows)

```bash
uip ah idea-flows list --output json
```

- `Result: Success` → keep `Data` (flow names + ids) and tell the user "Connected to Automation Hub."
- Auth failure → tell the user to run `uip login` (or, in Delegate, to sign in). Never ask for a raw token.
- `Failure` mentioning the tenant/enablement → AH is not enabled on this tenant; stop.

## Step 2: Pick the idea flow

Default to the entry whose `Name` contains "Business Process" (case-insensitive); take its `Id`. If the caller named a different flow, use that. Several candidates → ask. None → say Business Process flows may not be enabled and stop. Store `IDEA_FLOW_ID`.

## Step 3: Fetch the schema

```bash
uip ah automations schema get --idea-flow-id $IDEA_FLOW_ID --destination ./ah-schema.json --output json
```

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
| **Owner email** | `uip ah users list` → must be a listed `Email` (prefer `IsActive: 1`). Default to the signed-in user; confirm. |
| **Submitter email** | Same as owner; usually the same person. |
| **Application questions** (when tenant-required) | `uip ah applications list` → valid entries; if the material leaves systems unconfirmed, ask — never record an app the material does not support. Follow the question's own schema shape. |

Write the answers to `./ah-answers.json` as the filled `user_inputs` structure (the CLI accepts the whole schema-get document or just the answers map). Wrapping rules unchanged: most fields `{ "value": <v> }`; owner/submitter are **direct strings**; enum codes from that field's own `enum`; integers as numbers. Show the user a concise preview and get a confirm before writing.

## Step 5: Create the process

```bash
uip ah automations create --from-schema --idea-flow-id $IDEA_FLOW_ID --file ./ah-answers.json --output json
```

- `Result: Success` → **`Data.Id`** is the new process id. A success means it WAS created — never re-run on a confusing field read (that duplicates).
- `ValidationError`/`Failure` → the `Message`/`Instructions` carry the service's validation text; the same causes as the API flow apply (unnamed required field → owner/submitter first, then diff against the schema's required set; `Invalid Category Id`; placeholder answer codes). Fix and retry **once**.

## Step 6: Attach documents (PDD/SDD)

Attach every supplied document — default to all; ask only when two files look like the same document in different formats (in the Step 4 round). Per document:

```bash
uip ah documents create $PROCESS_ID \
  --title "PDD - <name>" --description "<desc>" \
  --document-type-id <n> --file "<path>" --output json
```

- `--document-type-id` from the fixed table in [`api-endpoints.md`](api-endpoints.md): PDD → `1`, SDD → `2`, else `9` (MISC).
- `--file` uploads the bytes (the CLI base64s it; any file type; 200 MB cap). Use `--embed-link <url>` *instead* only when the caller has a URL and no bytes — exactly one of the two, and never invent a URL.
- Record `Data.Id` (document id) and `Data.FileId` from each response. On a validation error, surface the message and continue with the remaining documents.

## Step 7: Verify, then report

```bash
uip ah documents list $PROCESS_ID --output json
```

Every attached document id must appear (file-backed ones with a `FileId`). Missing → report it failed; never claim an attach you didn't see in this list.

The report **MUST end with both View deep links**. The URL segment is `process_slug` — fetch it:

```bash
uip ah automations get $PROCESS_ID --all-fields --output json   # read process_slug from Data
```

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12, file 42), SDD ✓ (doc 13, file 43)
  View process:   {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}
  View documents: {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}/documentation
```

Build the links from the tenant the write went to (`uip ah auth-info get` → `Data.Tenant.Url` is the AH base for it).
