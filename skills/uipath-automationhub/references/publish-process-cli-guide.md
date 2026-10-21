# Publish a Process to Automation Hub — `uip ah` CLI flow

Creates one process from a schema-driven payload and attaches its documents (PDD/SDD), using `uip ah` commands. Auth is handled by the CLI (Delegate env-auth or `uip login`) — you never touch a token.

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The domain contract (required fields, wrapping rules, document types) is the same one [`api-endpoints.md`](api-endpoints.md) documents — the CLI only changes the transport.

**Expect about 12–15 commands end to end** (more for a large document set or a clarifying round). That covers preflight, flows, schema, one batched discovery call, reading the material, writing the answers, the create, one upload per document and one verification call. A run that wanders well past that tends to run out of turns before the create. This is a pace, not a cap: never skip the preflight check, an upload or the Step 7 verification to save commands. Everything the answers need comes from the caller's material, this tenant's schema and the discovery calls below:
- **Don't study other automations on the tenant** to copy how they were filled, unless the caller asks you to base the process on one. On a shared tenant they're someone else's data, and `automations schema get <id>` returns the template's placeholders, not that automation's answers.
- **Read each supplied document once, front to back, in as few reads as your tools show in full.** Don't page through it in many small slices or re-read sections already read. A large PDD runs to 2,000 lines, more than one tool output shows, so use a few large ranges (e.g. `sed -n '1,700p'`) rather than one `cat` whose output gets cut.
- **Resolve the category with the one-call recipe** in Step 4, not by walking the tree by hand.

## Step 1: Verify connectivity (and fetch the idea flows)

```bash
uip ah idea-flows list --limit 1000 --output json --output-filter "[].{Id: Id, Name: Name, Type: Type}"
```

Keep the projection, and run this as its own command, not chained with other reads. Unprojected, each entry carries its flow's whole phase/status tree, about 20k tokens of output on a default tenant. Agents whose shell truncated that have lost the last entries, which is where Business Process sits, and published to the wrong flow. Publishing needs only `Id`, `Name` and `Type`; a `Type` of `null` means the CLI or server predates it (Step 2).

- `Result: Success` → keep `Data` (flow names + ids) and tell the user "Connected to Automation Hub."
- Auth failure → tell the user to run `uip login` (or, in Delegate, to sign in). Never ask for a raw token.
- `Failure` mentioning the tenant/enablement → AH is not available on this tenant. Report the message for the matching case, verbatim, from [`cli-commands.md`](cli-commands.md) → **Automation Hub not available on this tenant** — then **stop**; nothing later in this flow can succeed.

## Step 2: Pick the idea flow

Default to the Business Process flow, picked by **type**: take the `Id` of the entry whose `Type` is `business-process` — names are tenant-editable and ids differ per tenant. If the caller named a different flow, use that. Several candidates → ask. None → say Business Process flows may not be enabled and stop. Only when no entry carries `Type` (older server or CLI), fall back to the entry whose `Name` contains "Business Process" (case-insensitive). Store `IDEA_FLOW_ID` and the expected type.

## Step 3: Fetch the schema

```bash
uip ah automations schema get --idea-flow-id $IDEA_FLOW_ID --destination ./ah-schema.json --output json
```

> 📁 **Working files (`ah-schema.json`, `ah-answers.json`, and any document files you generate for upload) go in the current working directory — never `/tmp`.** Hosted runtimes (e.g. the Delegate) sandbox their file tools to the session workspace: a file written to `/tmp` is readable by the CLI but every file-tool access to it fails with an access-denied error.

Read `./ah-schema.json`: the field catalog is under `properties.schema.properties` (Assessment Type > Section > Question; enums carry `answer_option` codes) and `user_inputs` is the payload template.

> ⚠️ **Do NOT submit `user_inputs` verbatim** — its example values are placeholders the API rejects (category `1`, placeholder answer codes, example emails). Shape only.

## Step 4: Collect the inputs, then assemble the answers file

**Collect every required input BEFORE creating** — same rules as the API flow, with CLI discovery:

First **enumerate the tenant's actual required set from the schema file**: every `required`-flagged question, plus owner + submitter (enforced but never flagged). Tenant admins add required questions (commonly "Applications used"/"Thin applications used"; a required thin-apps question still takes `[]` when the material names no thin client, see [Applications](#applications)) — the baseline table is a minimum, never the whole list. Resolve each: from the caller's material, the recipes below, or `AskUserQuestion` — never by inventing.

| Input | Recipe |
|---|---|
| Process **name** | Ask. Non-empty; duplicates fail with a 409-style error. |
| **Description** | Ask, or derive from the material and confirm. |
| **Category id** | `uip ah categories get` → pick from `Data.Categories` (**`category_is_active: 1` only**, and never an Idea-only node: `CategoryScope` 1 is Idea, 2 Process, 3 Both, and a Business Process needs 2 or 3; the recipe below applies both filters): the most specific one that fits the material, and **"Other" only when nothing fits**. "Other" is any node with `CategoryIsOther: 1`, and each branch can carry its own (e.g. *Finance & Accounting › Other*), so skip those too; several plausible → ask with names. Never the template's `1`. |
| **Documentation** answer code | The `PROCESS_DOCUMENTS` question's own `enum` in the schema — match by label, send its `answer_option` code. |
| **Owner email** | **`uip ah auth-info get`** → `Data.User.Email` is the signed-in identity and the default owner. That call is the authority; do not substitute an address from any list. |
| **Submitter email** | Same as owner; usually the same person. |
| **Application questions** | Driven by **what the material names** — see [Applications](#applications) below. `uip ah applications list` → select the systems that exist; send the ones that don't as `new_applications`. None named and the question not required → leave it out. Never block the publish on applications. |

The discovery commands are independent — run the ones you need (`auth-info get`, `categories get`, `applications list`) **in a single shell invocation** rather than one per turn; each is fast, the round-trips between them are not.

**Category in one call.** The tree is several hundred nodes on a real tenant, too long to read in full. Flatten it to `id<TAB>path` rows of usable nodes (active, not "Other", not Idea-only), then grep for two or three words from the material:

```bash
uip ah categories get --output json | jq -r 'def nodes(p): .[] | (p + (if p == "" then "" else " > " end) + .CategoryName) as $path | (select(.CategoryIsActive == 1 and (.CategoryIsOther // 0) != 1 and (.CategoryScope // 3) != 1) | "\(.CategoryId)\t\($path)"), ((.Subcategories // []) | nodes($path)); .Data.Categories | nodes("")' > ./ah-categories.tsv
grep -i -E '<word>|<word>|<word>' ./ah-categories.tsv
```

Use words from the material (its department, function or subject), not the placeholders. If `./ah-categories.tsv` is **empty**, this CLI names the fields differently: read the tree instead, don't conclude nothing fits. If the grep finds no match, list the branches once (`cut -f2 ./ah-categories.tsv | cut -d'>' -f1-2 | sort -u`) and pick the closest node under the best branch. Use "Other" only when nothing there fits, as the table says. Without `jq`, do the same walk in one Python call.

**Never block the publish on an owner lookup.** If you look the owner up at all, do a targeted search and treat a miss as no signal:

```bash
uip ah users list --search "<owner-email>" --invite-status all
```

Both flags: `--search` keeps it server-side and off the page limit; `--invite-status all` is required because the default filter hides users who can still own a process. Whatever it returns, use the `auth-info` email verbatim, submit, and let the API decide — only a real `Cannot identify owner by email` from the create is an owner problem (Step 5).

### Applications

**Answer from the material, one PDD at a time.** Record exactly the systems the PDD/SDD names — no more, no fewer:

- **Named and in the inventory** → put their ids in the question's `value` array. Take each id from the `Id` of its `uip ah applications list` record (`--search "<name>"` per system keeps it exact), **never by counting positions** in the schema's `enum`/`enumNames` arrays: the inventory runs past 100 entries, and an off-by-one there attaches a neighbouring application (asking for `eTrail/Salesforce` and getting `Excel`).
- **Named but not in the inventory** → add them in the same answer (below). A missing system is never a reason to stop, to ask the user, or to pick a look-alike.
- **Nothing named** → if the schema does **not** flag the application question `required`, **omit it entirely** — a process with no applications is valid. Never pad the answer with inventory entries to "fill it in". Only when the tenant flags it `required` and the material names no system, ask the user with `AskUserQuestion` (inventory entries as options, plus free text for a system not in the list).
- **"Thin applications used" is never padded, even when the schema flags it `required`.** It only marks which of the answered applications are thin clients, so its answer is the systems the material explicitly calls thin, Citrix or virtual-desktop clients, and nothing else. When the material calls none of them that, send `{ "value": [] }` if the question is flagged `required` (an empty answer is accepted) and omit it otherwise. Never copy the "Applications used" ids into it to satisfy the flag.

**UiPath itself is never one of them.** The automation is what the process becomes, not a system it uses, so leave out "UiPath" and its own components (Orchestrator, Action Center, robots, Maestro, Case Management, Document Understanding, Integration Service…) even when the PDD or SDD lists them as systems or future-state steps.

#### Adding systems that are not in the inventory — `new_applications`

Check the schema first: if the application question (`<ASSESSMENT>-COUNT_APPS`, "Applications used") has a **`new_applications`** property next to `value`, the submission itself can create applications — **no admin permission, no separate call, no `categoryIds`**. Send the new systems alongside any existing ids:

```json
"OVR-COUNT_APPS": {
  "value": [12],
  "new_applications": [
    { "application_name": "Kinaxis RapidResponse", "application_version": "2026.2", "application_language": "English" },
    { "application_name": "SUNAT Portal" }
  ]
}
```

- `application_name` is required (1–50 chars); `application_version` (≤20), `application_language` (≤50), `application_comments` (≤512), `application_is_citrix_client` (boolean) are optional. At most **20** per submission. No other fields are accepted.
- Each entry is **matched by name + version, ignoring case and surrounding spaces**: an entry that matches an existing application reuses it, so sending a system that turns out to be in the inventory is harmless — it never creates a duplicate. Keep the version the material gives; a different version is a different application.
- Created applications land in the tenant's application inventory (the same as a user typing one in the web form), and are selectable by id on every later submission.
- `new_applications` exists only on "Applications used". "Thin applications used" (`…-COUNT_THIN_APPS`) takes inventory ids only and just flags applications already answered in "Applications used" — an id that is not in "Applications used" has no effect, and an id not in the inventory is rejected. A newly added application has no id until the create returns, so flag it as thin **inline** instead: `application_is_citrix_client: true` on its `new_applications` entry. Don't answer the application questions in a later `automations update` unless the caller asked to change applications. Updates replace the whole list and clear thin flags and comments (see [`api-endpoints.md`](api-endpoints.md), `new_applications`).

A `400` whose message starts `Invalid Application Data.` names the problem — fix it locally and retry once:

| Message tail | Fix |
|---|---|
| `Unknown application id(s): …` | An id in `value` is not in `applications list` — drop it or move that system to `new_applications`. |
| `Adding new applications is disabled for this assessment…` | The tenant admin turned off adding applications for this section. Fall back to [the admin upsert](#fallback-no-new_applications-in-the-schema), then to substitution. |
| `…requires a non-empty application_name` / `…exceeds 50 characters` / `…invalid version, language, comments, or citrix flag` | Fix that entry's field. |
| `…has unknown field(s): …` | Drop the named key — usually a typo, or an `application_id` (ids go in `value`). |
| `At most 20 new applications…` | Keep the 20 most material systems; name the rest in the description. |

#### Fallback: no `new_applications` in the schema

The property is absent on Automation Hub builds that predate it, and whenever the admin has disabled adding applications for that section. Then, and only then, create through the inventory API. `uip ah applications` has no `create` verb — **creation happens through `update`**, by sending an element whose `application_id` is `null`. The service upserts: an element with a real id updates that application, an element with `null` inserts a new one. (The CLI's own `update --help` claims it cannot add one; that is wrong, and it is why agents give up here.)

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

**If creating fails for any reason — 403, a validation error, a bad category id, anything — fall through; never retry it and never stop.** Answer with the systems that *are* in the inventory; if that leaves a **required** "Applications used" empty, pick the closest entries from `applications list` to satisfy it (an optional one stays empty; "Thin applications used" is never filled this way, see [Applications](#applications)). Either way, name the real systems in `OVERVIEW_DESCRIPTION` (e.g. "Systems per PDD: Salesforce, CREDILEX, SUNAT Portal — not in tenant inventory"). The process record is what matters; applications are editable afterwards. **Never abandon a publish because an application is missing or uncreatable, and never silently pass off an unrelated application as the real one — say what you substituted.**

Write the answers to `./ah-answers.json` as the filled `user_inputs` structure (the CLI accepts the whole schema-get document or just the answers map). Wrapping rules unchanged: every field is `{ "value": <v> }` except **user questions**: owner, submitter, and any user picker the tenant adds (the schema marks them `format: email`). Those take the email as a **direct string**; the server also accepts `{ "value": <email> }` for them (a bare string on any other question reads as empty); enum codes from that field's own `enum`; integers as numbers. Show the user a concise preview and get a confirm before writing.

### Preflight: check the answers against the schema

`ah-schema.json` is the same document the service validates against, so check `ah-answers.json` against it locally **before** creating:

1. **Required answers present** — every question the schema flags `required`, plus owner and submitter (enforced but never flagged), has a non-empty value. Take requiredness from *this tenant's* schema, never from a fixed list: the same Business Process flow requires `COUNT_APPS` on one tenant and rejects it on another.
2. **Every answer wrapped** — each answer except user questions (owner, submitter, any `format: email` user picker) is an object with a `value` key. A bare string is read as empty: on `OVR-OVERVIEW_NAME` that fails as `Automation name cannot be empty.`, elsewhere as a missing answer.
3. **Enum codes verbatim** — every enum answer (Documentation, application questions, any select) is a code that appears exactly in that question's own `enum`. Copy it; never retype it. A code with a dropped segment (`…-ovrbp-0-3-5` instead of `…-ovrbp-0-3-0-5`) is never selected. Newer builds reject it with a `400` that names the question and lists its codes; older builds fail a `required` question with `Please fill in all the required information` and **silently drop** an optional one, so run this check on every build.
4. **No placeholders left** — no `Sample input`, no `First.last@example.com`, no template category `1` unless the tenant's tree really has it.
5. **Applications match the material** — every system the PDD names is either an id in `value` or an entry in `new_applications` (only if the schema has that property); nothing the PDD doesn't name; no application question at all when the PDD names none and it isn't `required`. Check the ids by **name**, not by count: map every id in `value` back to its `Name` in `applications list` and compare that list with the PDD's systems. An id whose name is not one of them is a wrong pick, even when the count matches. "Thin applications used" holds only the systems the material calls thin clients, or `[]`.

Fix anything found locally, then create. This costs nothing on a correct payload and catches most of the `400`s below before they happen.

## Step 5: Create the process

```bash
uip ah automations create --from-schema --idea-flow-id $IDEA_FLOW_ID --file ./ah-answers.json --output json > ./ah-create.json; cat ./ah-create.json
```

The create can take 20–30 s, longer for a large process. Run it as its own command, not chained behind the preflight checks, and wait for its envelope. Its envelope also lands in `./ah-create.json` when the command finishes, so a shell that hands back early has not lost it: wait, then read that file. Once it holds `Result: Success`, its `Data.Id` is the process. Never start a second create, and never read the silence or an empty file as a failure.

**Run `automations create` once per process, whatever happens next.** If you lost its envelope, find the record instead: `uip ah automations list --search "<reference code or 2–3 distinctive words>" --limit 20 --output json`. Don't search on the full title: a search term containing `:` never matches anything, even a record that exists, and a record created seconds ago may not be listed yet. An empty result is not proof the create failed. Search again with a shorter term after a few seconds; if the record still doesn't show, tell the user the create's outcome is unknown rather than creating again.

- `Result: Success` → **`Data.Id`** is the new process id. A success means it WAS created — never re-run on a confusing field read (that duplicates).
- `ValidationError`/`Failure` → the `Message`/`Instructions` carry the service's validation text; the same causes as the API flow apply (unnamed `Please fill in all the required information` → re-run the preflight: a missing required answer or an enum code that is not verbatim from the schema; `Invalid Category Id`; `Automation name cannot be empty.` → `OVR-OVERVIEW_NAME` is missing, empty, or a bare string instead of `{ "value": … }`; `errorDetails` with `An answer selection is required for submission` on a field → that field's enum code isn't copied verbatim from its `enum`; on newer builds `Question "<key>" has no answer option matching "<value>". Allowed values: …` → replace exactly that answer with the matching code from that field's own `enum` in `ah-schema.json` (the message lists at most 25), and `… expects an array of answer option values` → wrap the multiple-choice answer as `{"value": ["<code>"]}`). Fix and retry **once**.
- `Cannot set properties of undefined (setting 'co_question_answer_option_value')`, or `Question "<key>" can't be answered on this tenant: it has no answer slot to hold a value…` → **a server-side defect: this tenant has nowhere to store one of your free-text answers** (an answer whose schema `value` is a plain `string` or `number` with no `enum`). Your values aren't wrong, so don't rewrite them. Newer builds return `Question "<key>" can't be answered on this tenant: it has no answer slot to hold a value…` instead, naming the question: drop exactly that key. The older message names nothing: drop every **optional** free-text answer. In both cases keep every `required` answer and owner/submitter, retry **once**, and tell the user which answers were left out. If it still fails, or the named question is `required`, stop and report it with the tenant and `--idea-flow-id`.
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

- `--document-type-id` from the fixed platform table in [`api-endpoints.md`](api-endpoints.md) — read it there; do not guess ids. **A `.bpmn` process map is always `6`**: under any other type AH shows it download-only, with no editor. The CLI does not infer the type from the extension, so pass it every time. A case plan (`caseplan.json`) is download-only whatever its type — the same table entry says how to handle it.
- `--file` uploads the bytes (the CLI base64s it; any file type; 200 MB cap). Use `--embed-link <url>` *instead* only when the caller has a URL and no bytes — exactly one of the two, and never invent a URL.
- Record `Data.Id` (document id) and `Data.FileId` from each response. On a validation error, surface the message and continue with the remaining documents. A `409 Duplicate document with title found` means a document with the same type **and file name** is already attached; the title is not checked (see [`api-endpoints.md`](api-endpoints.md)). Report it with that document and continue with the remaining documents. Never rename or retitle and retry on your own. Re-uploading a `.bpmn` that is already attached as `9` with `--document-type-id 6` succeeds and leaves both copies. Tell the caller the old download-only copy should be deleted in the AH web UI.

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

**Check the process landed in the intended flow:** the `--all-fields` record's `process_submission_type` must match the flow type you chose in Step 2 (`business-process` = `8`; mapping in [`api-endpoints.md`](api-endpoints.md) → **Idea flow types**). A Business Process that came back as `1`/`2` (Employee-/CoE-driven idea) is a known failure mode — the agent picked the flow by name instead of by type, which Step 2 now prevents at the source; this check is the backstop. **Don't re-create it**; tell the user and fix it with [`change-idea-flow-cli-guide.md`](change-idea-flow-cli-guide.md). The payload was built from the wrong flow's schema, so after the move re-fetch the schema for the process (`uip ah automations schema get $PROCESS_ID --destination ./ah-schema-moved.json --output json`; its `user_inputs` holds the current answers) and check the required questions are answered: answer the missing ones from the source with `automations update`, or tell the user which are still empty. Only then report the corrected flow.

The report **MUST end with both View deep links** — the URL segment is `process_slug` from the `--all-fields` record.

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12, file 42), SDD ✓ (doc 13, file 43)
  View process:   {Data.Tenant.Url}/automation-profile/{process_slug}
  View documents: {Data.Tenant.Url}/automation-profile/{process_slug}/documentation
```

Build the links from the tenant the write went to: `uip ah auth-info get` → `Data.Tenant.Url` is **already the full AH tenant base** (`…/{org}/{tenant}/automationhub_`) — append only `/automation-profile/{process_slug}` (+ `/documentation`), never re-append org/tenant segments.
