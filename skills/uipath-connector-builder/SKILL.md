---
name: uipath-connector-builder
description: "UiPath Integration Service connector authoring (REST+JSON) on disk via `uip is connectors builder`. Triggers on `element.json`, `element-metadata.json`, `standard-resources/*.json`, a `periodic-uipath-*`/`periodic-design-*` connector repo, or any request to build/edit an IS connector: init the connector shell, configure auth (14 types via `auth set`), add activities with fields/params/methods/hooks, wire polling/webhook triggers, add auth-system resources, inspect, validate, and surgically read/write files via state. Import + publish live on the parent `uip is connectors` (need `uip login`). NOT for operating a published connector — connections, ping, run an activity→uipath-platform; NOT for `.flow` connector nodes→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Connector Builder

Author UiPath Integration Service connectors on disk with `uip is connectors builder`, then `import` + `publish` them through the parent `uip is connectors`. A connector is a `periodic-*` repo (`periodic-uipath-{vendor}-{product}` for official; `periodic-design-{org}-{slug}` for custom — `init` derives the `design-{org}-{slug}` element key from `--name` + `--organization`) whose core is `app/element/element.json` plus `standard-resources/*.json` and JavaScript `hooks/`. Connectors wrap **REST APIs that return JSON only** — no SOAP, GraphQL, or XML. Terminology: the authoring noun is **activity** (it maps to an element.json resource + a standard-resource file).

## When to Use This Skill

- Creating a new connector from a vendor's API docs (init → auth → activities → validate → import → publish).
- Editing an existing connector: adding activities, fields, parameters, methods, or hooks.
- Configuring or switching authentication (OAuth2, PKCE, client credentials, API key, basic, JWT, AWS v4, etc.).
- Writing or fixing JavaScript request/response hooks.
- Wiring a polling or webhook trigger on an existing activity.
- Debugging a connector, activity, hook, or trigger problem in `element.json` / a standard-resource file.
- Validating before release, or pulling/pushing a design connector to a tenant.

## Critical Rules

1. **Inspect before editing.** On any existing connector, run `builder inspect` first to map auth, config, activities, hooks, and triggers. Never edit blind. Never invent config keys, activity paths, or IDs — read state first (`inspect`, `activity list`, `state query`).
2. **Validate before you finish.** Run `builder validate` at the end of every workflow and after each fix — it runs the full periodic check set and exits non-zero on failure. On failure, read the reported field, fix that one entry, re-validate. After 3 failed attempts on the same error, stop and surface the `validate` output — don't keep guessing. **Don't stop at "0 errors": read the WARNINGS too** — they flag real gaps that still ship a half-built connector (a fieldless activity, a broken SR link). Treat them as must-fix unless you can articulate why a given one is acceptable.
3. **`auth set` owns all authentication.** It writes the config entries, `authentication.type` / `typeOauth` / `authenticationTypes`, and the token-refresh resource in one call. Define scopes here too (`--scope`, `--scope-options`, `--required-scopes`, `--preselected-scopes`) — there is no separate scope command. `init --auth oauth2|customApiKey` is inline sugar for the create-time common case; everything else goes through `auth set`. Never hand-roll auth via `state patch`.
4. **`activity create` writes both sides in one call** — the standard-resource file AND one `element.json` entry per method. Re-running on an existing activity appends/merges. Pass `--skip-sr` (or use `auth system create`) only for system resources that need no SR file. Model `GETBYID`/`PATCH`/`PUT`/`DELETE` only for TRUE by-id endpoints — never for search. The `/{primaryKey}` path param is added automatically: ALWAYS for `GETBYID`, and for `PATCH`/`PUT`/`DELETE` only when the activity is CRUD (it also has a `GET`/`GETBYID`); a write-only/action activity keeps its base path.
5. **`state patch` REPLACES the whole node at a pointer (no merge).** To change one field: `state query` the entry, edit it, then `state patch` the COMPLETE object back. `element-metadata.json` has no addressable sub-paths — round-trip the whole file. Activity paths in pointers are URL-encoded: `/contacts` → `%2Fcontacts`. Use the dedicated authoring verbs for creation, not `state patch`.
6. **Connector targeting.** Builder verbs walk up from the cwd, then scan immediate subdirectories — run from inside the connector dir, or pass `--connector-dir <PATH>` to target one explicitly (required when multiple connectors are nearby). `import` reads `--connector-dir` the same way (the connector root holding `app/element/element.json`); on `download` it instead names the OUTPUT directory to write the pulled connector into. **Exception — `init` does NOT scan subdirectories** (it would otherwise resolve a SIBLING connector and silently EDIT/rename it): to CREATE, run `init` from a fresh/empty directory (a dir that merely *contains* connector subdirs — e.g. `/tmp` — creates a new connector, it will not dive into a child to edit it); to EDIT, run from inside the connector or pass `--connector-dir`.
7. **Output is the `{Result, Code, Data}` envelope.** Add `--output json` to parse it. Failures exit non-zero. Never suppress stderr.
8. **`import` / `download` / `publish` — and `init` when CREATING — need `uip login`.** Authenticate before any tenant pull/push. A NEW connector's key `design-{org}-{slug}` takes its org from your logged-in session, so `init` create ERRORS when you're not logged in. Let it derive the org; do NOT pass a guessed `--organization` (a wrong org bakes into the key and only surfaces, mismatched, at import/publish) — `--organization <slug>` is only for offline/CI builds with a known org.
9. **Never echo, log, or hard-code a secret.** Secret config keys (client secret, API key, password, token) are written by `auth set` ENCRYPTED (`encrypt: true`) — most as `PASSWORD` fields, though some (OAuth tokens, a service-account JSON) are encrypted `TEXTFIELD`/`TEXTAREA`. End users supply real credentials at connection time; the connector holds only the auth TYPE + endpoint URLs + scopes. Use placeholders in every example command.
10. **Prefer a built-in over a hook.** Before writing JS, consult the decision table ([references/hooks.md](references/hooks.md) §"Decide first: hook or built-in?") — a hook is only for transforms, orchestration, or derivation no declarative feature expresses. One hook file per activity+method+phase; hooks run in Denali (modern JS + `require('axios')` for secondary calls) and must end every path with `done()`.
11. **Author the field schema for EVERY activity — `activity create` does NOT infer fields.** An activity with no fields renders in Studio Web as a single raw JSON body in and raw JSON out, with zero typed inputs/outputs — a half-built connector that still validates and publishes, so the omission is easy to miss (it's a recurring failure: "got it valid and published" while skipping the schema). After `activity create`, ALWAYS define the request/response fields from the vendor's documented schema — either pass `--fields-file <json>` on `activity create` for the whole schema at once, or add them one at a time with `activity field create`. `validate` emits a WARNING for any fieldless activity — treat it as must-fix. Never report a connector "done" with fieldless activities; if a raw-body passthrough is genuinely intended, say so explicitly.

## Connection design (host, region, discovered values)

Decide how each per-connection value reaches the request BEFORE scaffolding — getting this wrong is the most common rework:

- **One config drives the host — not three URLs.** When the base, token, and authorize hosts share a per-connection part (an instance name, region, datacenter, or workspace), surface ONE config and template it into every URL: `init --base-url 'https://{instance}.../api'` + `auth set --token-url 'https://{instance}.../token' --authorization-url 'https://{instance}.../authorize'`. The CLI auto-seeds a single fillable `{instance}` field that resolves all three ([references/configuration.md](references/configuration.md) §Templated hosts). Do NOT expose `base.url`/`oauth.token.url`/`oauth.authorization.url` as separate connection fields.
- **Open value → TEXTFIELD; fixed set → COMBO.** A free-form instance/workspace/account name is the auto-seeded templated TEXTFIELD — that is a legitimate, common shape, not a smell. Only a genuinely fixed datacenter/environment list becomes a COMBO (`state patch` the seeded entry to `type:COMBO` with `options`, whose `value` can be the host fragment itself).
- **Derive or discover before you ask.** If a per-connection value (the API host, an org/account id) is returned in the token response or is discoverable via an authenticated call, capture it instead of adding a manual field — but ONLY when it is genuinely needed AND obtainable; a single templated config is the simpler default, so don't over-engineer discovery where a plain field suffices. Token-response host → a `postRequest` hook that validates (https + allowlisted host, never log the token) and persists via `done({configuration})` — recipe: [references/hooks.md](references/hooks.md) §"Pattern: base URL …". Discoverable id → an `onProvision` system resource that calls the lookup at connection time ([references/system-resources.md](references/system-resources.md)).
- **Multi-datacenter OAuth:** the accounts/token host itself varies by region — template the region config into `--token-url`/`--authorization-url` too, not just the base URL.

## Workflows

Each workflow is an ordered sequence of copy-paste-ready commands. Use placeholders (`<ORG>`, `https://api.example.com`) — never real secrets.

### New connector (full lifecycle)
```bash
# 0. Log in FIRST. The key `design-{org}-{slug}` takes its org from your logged-in
#    session, so `init` (create) ERRORS if you're not logged in. Let it derive the
#    org — do NOT guess --organization (a wrong org bakes into the key and only
#    surfaces, mismatched, at import). --organization <slug> is for offline/CI only.
uip login status            # check Data.Status == "Logged in" — NOT the envelope
                            # Result/exit, which is "Success" even when the session
                            # is dead (refresh-failed / expired). (`init` create
                            # itself re-checks the live login status and blocks.)

# 1. Scaffold the shell. --name is required when creating; key + folder are derived
#    (the org comes from your login — see step 0).
uip is connectors builder init --name 'Acme Widgets' \
  --description 'Acme Widgets connector' --categories 'CRM,Sales and marketing' \
  --base-url https://api.acme.com --auth oauth2 \
  --authorization-url https://acme.com/oauth/authorize \
  --token-url https://acme.com/oauth/token --scope 'read write'
#   --categories must be approved DISPLAY-NAME values (e.g. 'CRM', 'Sales and marketing',
#   'Collaboration', 'Productivity', 'E-commerce') — NOT lowercase slugs like `crm,sales`.
#   Validated at init AND `validate`: wrong case is canonicalized, an unknown value fails fast
#   and the error lists the approved enum. init seeds element-metadata.json:latestVersion = "1.0.0".

# 2. Add an activity (writes element.json entries + standard-resources/accounts.json).
uip is connectors builder activity create --name accounts --vendor-path /v1/accounts \
  --methods GET,GETBYID,POST,PATCH,DELETE --primary-key id --has-ceql

# 3. Author the field schema — REQUIRED, not optional (Rule 11). `activity create`
#    does NOT infer fields; without this the activity ships as a raw JSON body and
#    `validate` warns. Pass `--fields-file <json>` on `activity create` for the whole
#    schema at once, or add fields one at a time with `field create`
#    (visibility flags apply to every --method listed; re-runs merge):
uip is connectors builder activity field create --resource accounts --name email \
  --type string --method GET --method POST --response

# 4. Validate — must be 0 errors AND no unresolved warnings (fieldless activity,
#    broken SR link) before import.
uip is connectors builder validate

# 5. Import (create-or-update on the tenant) then publish.
uip login
uip is connectors import
uip is connectors publish --wait        # blocks until SUCCESS; live in Studio Web then
                                        # (fire-and-forget without --wait: allow ~5-10 min)
```
Publishing a NEW connector needs no `--version` (init seeded `1.0.0`). **Re-publishing** an existing connector requires a HIGHER version — bump `element-metadata.json:latestVersion` (or pass `--version 1.0.1`); the server rejects an equal version.

### Add an activity to an existing connector
```bash
uip is connectors builder inspect --output json     # map what exists first
# research the vendor API, then:
uip is connectors builder activity create --name contacts --vendor-path /v1/contacts \
  --methods GET,GETBYID,POST --primary-key id --fields-file ./contacts-fields.json
uip is connectors builder activity field create --resource contacts --name status \
  --type string --method GET --response --searchable
uip is connectors builder activity hook create --resource-name contacts --method GET \
  --hook-type postRequest --custom-code-file ./contacts-postRequest.js   # optional response shaping (you write the JS)
uip is connectors builder validate
```

### Add a polling trigger
`trigger create` authors a POLLING trigger. The target activity must already exist and have an SR file (`trigger create` hard-fails otherwise).
```bash
uip is connectors builder activity list --output json    # confirm the activity exists
uip is connectors builder trigger create --resource-name accounts --event-kind polling \
  --updated-date-field LastModifiedDate --id-field Id     # seeds the event config + hasEvents flag
uip is connectors builder validate
```
`--updated-date-field` is REQUIRED for every `--event-kind` — the command always authors a polling loop. `--event-kind polling|webhook|all` (default `polling`) only picks the config bundle; `webhook`/`all` add webhook config keys but don't implement delivery. Webhook delivery, the polling-vs-webhook semantics, and per-flag defaults all live in [references/events.md](references/events.md).

### Customize a curated activity
`activity create` auto-curates every method into a standalone Studio activity by default (opt out with `--no-curate`). Use `method curate` only to override the generated name/displayName, or to curate a `--no-curate` method.
```bash
uip is connectors builder activity method curate --resource cases --method GET \
  --display-name 'Get Support Request'
uip is connectors builder activity field create --resource cases --name subject --type string \
  --method GET --response --response-curated --design-position primary
uip is connectors builder validate
```

### Debug
```bash
uip is connectors builder inspect --output json
# state patch REPLACES the node — query the WHOLE entry, change ONLY the field at fault, patch it ALL back:
uip is connectors builder state query element.json/configuration/oauth.token.url --output json
uip is connectors builder state patch element.json/configuration/oauth.token.url \
  --value '<full entry from the query above, with defaultValue corrected>'
uip is connectors builder validate
```
For a derived base URL (e.g. Salesforce `instance_url` from the token response): a `postRequest` hook VALIDATES the URL (https + allowlisted host) and persists it with `done({configuration})` — NOT `state patch`, which baking-time-edits one org's URL into every connection. Full recipe: [references/hooks.md](references/hooks.md) §"Pattern: base URL …"; investigation checklists: [references/debugging.md](references/debugging.md).

## Command Map

```text
uip is connectors                      # tenant/catalog + design-connector lifecycle (needs `uip login`)
  list | get <key> | swagger <key> | export <key> | audit-logs | event-operations
  download <key> | import | publish | publish-status <id> | probe
  builder                              # author a connector ON DISK
    init                               # create-or-EDIT the connector shell in ONE verb
                                       #   (folds the old scaffold / metadata / global / base+pagination preset)
        preset apply --kind base|pagination
        header delete <vendorName>
    auth     set | get | system (create|list)
    activity create | list | get | delete
             field  (create|list|get|delete)
             method (get|set|curate)
             param  (create|list|get|delete)
             hook   (create|list|get|delete)
    trigger  create                    # --event-kind polling|webhook|all (folds the event preset + polling)
    inspect                            # read-only whole-connector rollup
    validate                           # full check set; exits non-zero on failure
    state    query <pointer> | patch <pointer>
```

`publish` returns a `PublishId`; `--wait` polls to SUCCESS/FAILURE (timeout via `--timeout-seconds`, default 600); check later with `publish-status <id>` (positional). Status enum: `IN_PROGRESS | SUCCESS | FAILURE`.

## Reference Navigation

Depth lives in `references/` — each self-contained. SKILL.md owns the workflows, command map, and rules above; references must not repeat them. The always-current flag source is `uip is connectors builder <noun> <verb> --help`.

| Task → read this | Reference |
|---|---|
| What a connector is, file layout, the CRUD/curated/HTTP activity model | [references/overview.md](references/overview.md) |
| element.json internals: top-level fields, resources[], parameters[], value interpolation, hook order | [references/element-json.md](references/element-json.md) |
| Standard-resource files: linking, metadata.method, curated, fields (visibility/design/searchable) | [references/standard-resources.md](references/standard-resources.md) |
| configuration[] entries: widget types, screen types, per-auth key sets, pagination + event keys | [references/configuration.md](references/configuration.md) |
| Authentication setup: all 14 auth types and the OAuth/JWT scope surface | [references/auth.md](references/auth.md) |
| Auth-system resources: auth-validation, onProvision/onDelete, OAuth token overrides | [references/system-resources.md](references/system-resources.md) |
| When to write a hook vs use a built-in (decision table + good/avoidable patterns), execution order, context vars, done(), naming | [references/hooks.md](references/hooks.md) |
| Polling and webhook triggers: config keys, event.poller.configuration schema | [references/events.md](references/events.md) |
| Debugging auth / activity / hook / trigger / pagination issues (workflow + checklists) | [references/debugging.md](references/debugging.md) |

## Anti-patterns

1. Editing without `builder inspect` first (Rule 1) — you'll invent keys/paths that don't exist.
2. Hand-rolling auth via `state patch` instead of `auth set` (Rule 3) — leaves the auth block inconsistent.
3. Editing a config entry with a partial value (Rule 5) — `state patch` REPLACES the node, dropping omitted fields. Query the whole entry and patch the complete object back.
4. Re-running `activity create` with a name that already exists when you meant a SEPARATE activity — it's an idempotent upsert that MERGES into the same-named activity (appends methods, preserves existing field definitions unless `--overwrite-fields`); it does not error, so a wrong name silently merges instead of warning.
5. Modeling `GETBYID` for a search/list endpoint (Rule 4) — by-id verbs auto-add the `/{primaryKey}` param; reserve them for true single-record reads.
6. Putting a real secret in an example or expecting the connector to store one (Rule 9) — secrets are encrypted fields (usually PASSWORD) supplied at connection time.
7. Re-publishing without bumping the version — the server rejects an equal version; bump `latestVersion` or pass `--version`.
8. Invented `--categories` values — they must come from the approved enum; `validate` reports the list.
9. Writing a hook for a job a built-in does (Rule 10; hooks.md §"Recognizing an avoidable hook"), or omitting the trailing `done()` so the hook never returns.
10. Reaching for a removed command — there is no `connector scaffold/inspect/validate` wrapper (use `init`/`inspect`/`validate` directly), no `global`/`metadata`/`config`/`resource*`/`event polling add`/`auth scope`/`remote*`/`describe`/`reference`.
11. Reporting a connector "done" with fieldless activities (Rule 11) — `activity create` writes endpoints/methods/auth but NOT the field schema; an activity with no `field create` / `--fields-file` shows only a raw JSON body in Studio and trips a `validate` WARNING. Author fields before finishing, and never treat a 0-error/has-warnings validate as a pass.
