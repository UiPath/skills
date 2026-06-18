---
name: uipath-connector-builder
description: "UiPath Integration Service connector authoring (REST+JSON). Always invoke for `element.json`, `element-metadata.json`, `standard-resources/*.json`, or a `periodic-uipath-*` connector repo. Build on disk via `uip is connectors builder`: scaffold a connector, configure auth (any of 14 types), add resources/fields/params/methods, write JS pre/post hooks, add polling events, manage config and system resources, validate, and pull/push to a tenant. For operating a published connector (connections, ping, run an activity)→uipath-platform. For .flow connector nodes→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Connector Builder

Author UiPath Integration Service connectors on disk with the `uip is connectors builder` CLI. A connector is a `periodic-*` repo (`periodic-uipath-{vendor}-{product}` for official, `periodic-design-{org}-{slug}` for custom/design — `scaffold --organization <ORG>` produces the `design-{org}-{slug}` element key) whose core is `app/element/element.json` plus `standard-resources/*.json` and JavaScript `hooks/`. Connectors wrap **REST APIs that return JSON only** — no SOAP, GraphQL, or XML.

## When to Use This Skill

- Creating a new connector from a vendor's API docs (scaffold → auth → resources → validate).
- Editing an existing connector: adding endpoints/resources, fields, parameters, or methods.
- Configuring or switching authentication (OAuth2, PKCE, client credentials, API key, basic, JWT, AWS v4, etc.).
- Writing or fixing JavaScript request/response hooks.
- Adding polling events to a resource.
- Debugging a connection, resource, hook, or polling problem in `element.json` / a standard-resource file.
- Validating a connector before release, or pulling/pushing a design connector to a tenant.

## Critical Rules

1. **Inspect before editing.** On any existing connector, run `connector inspect` first to map auth, config, resources, hooks, and events. Never edit blind.
2. **Validate before you finish.** Run `connector validate` at the end of every workflow, and after each fix while debugging. It runs the full periodic check set and exits non-zero on failure. On failure, read the reported field, fix that specific entry, re-validate. After 3 failed attempts on the same error, stop and surface the `validate` output to the user — do not keep guessing.
3. **`auth set` owns all authentication.** It writes the config entries, `authentication.type` / `typeOauth` / `authenticationTypes`, and — for refresh-token OAuth types (not client credentials) — the `oauthOnTokenRefresh` resource, in one call. Never hand-roll auth via `config create`.
4. **`resource create` writes both sides in one call** — the standard-resource file AND the `element.json` resource entries. Pass `--skip-sr` (or use `resource system create`) only for system resources that need no SR file.
5. **To edit one config field, `state query` the entry then `state patch` the COMPLETE object back with that field changed.** `state patch` REPLACES the whole node at the pointer (it does not merge), so any field you omit is dropped. Do NOT use `config create --force` to edit — it resets omitted fields to their defaults (e.g. `internal`, `hide`, `displayOrder`). Use orchestrator verbs (`resource create`, `auth set`, ...) for creation. Resource paths in `state` pointers are URL-encoded: `/contacts` → `%2Fcontacts`.
6. **Never invent config keys, resource paths, or IDs.** Read the current state first (`connector inspect`, `state query`, `config list`, `resource list`) before writing.
7. **Connector targeting.** Run builder commands from inside the connector directory — the CLI walks up from the cwd, then scans immediate subdirectories (this is why the examples omit the flag). Pass `--connector-dir <PATH>` to target one explicitly; required when multiple connectors are nearby or you run from elsewhere.
8. **Output is the `{Result, Code, Data}` envelope.** Add `--output json` when you need to parse output. Never suppress stderr.
9. **`remote import` / `remote get` need `uip login`.** Authenticate before any tenant pull/push.
10. **One hook file per resource+method+phase.** Duplicate logic rather than sharing a file. Prefer a `type:"value"` parameter with `${configuration.<key>}` interpolation over a hook for static header/auth injection.

## Workflow

Each workflow is an ordered sequence of copy-paste-ready commands.

### New connector
```bash
uip is connectors builder connector scaffold --name 'Acme Widgets' --description 'Acme Widgets connector'
uip is connectors builder auth set --auth-type oauth2 \
  --authorization-url https://acme.com/oauth/authorize \
  --token-url https://acme.com/oauth/token \
  --scope 'read write' \
  --scope-options '[{"value":"read"},{"value":"write"}]' \
  --validation-vendor-path /me                            # seeds a provisionAuthValidation probe (recommended)
uip is connectors builder global set --accept-type application/json --content-type application/json --paginator-version 2
uip is connectors builder resource create --name accounts --methods GET,POST,PATCH,DELETE \
  --vendor-path /v1/accounts --primary-key id
uip is connectors builder metadata set --categories 'CRM,Sales and marketing'   # values must be from the approved list
# Fill the vendor base URL (base.url exists empty after scaffold) so validate doesn't warn:
uip is connectors builder config create --key base.url --name 'Base URL' \
  --type TEXTFIELD_1000 --default-value https://api.acme.com --force
uip is connectors builder connector validate   # run LAST — must be Errors:0
# validate reports Errors (block release) AND Warnings (recommended, non-blocking). The only
# Warning left here is oauth.scope — set its default to the vendor's scopes. Warnings don't fail.
```

### Add a resource
```bash
uip is connectors builder connector inspect --output json
# research the vendor API, then:
uip is connectors builder resource create --name contacts --methods GET,GETBYID,POST \
  --vendor-path /v1/contacts --primary-key id --fields-file ./contacts-fields.json
uip is connectors builder hook create --resource-name contacts --method GET --hook-type postRequest \
  --custom-code-file ./unwrap.js                                   # optional
uip is connectors builder connector validate
```

### Pull resources from the SR cache
Cache holds StandardResource artifacts for this connector (authored by `uip is resources
standardize`). `sync-from-cache` writes ONLY `app/element/standard-resources/*.json` (NOT
element.json) and normalizes each SR — path rewrite to the IS slug + auto-curation
([references/standard-resources.md](references/standard-resources.md) §Cache-sync normalization).

**Triage before mutating.** If a connector with this key already exists on the tenant, pull it and compare against the cached SRs so the user can pick add / rename / replace per activity:
```bash
uip login --output json                                  # all remote get/import/publish calls need it (Rule 9)
uip is connectors builder remote get <ELEMENT_KEY> --output json
#   404 → net-new connector. Run scaffold + the pipeline below.
#   200 → existing connector. Pull files and inspect before any mutation:
uip is connectors builder remote get <ELEMENT_KEY> --include files --output json
uip is connectors builder resource list --output json    # activities already on it
# For each cached object that matches one on the connector, ask the user (AskUserQuestion):
# keep both (rename to <NAME>_v2) / replace / skip. If unsure, ask — see Anti-patterns.
```

Then run the pipeline:
```bash
uip is connectors builder connector inspect --output json        # confirm scaffold + element.json:key
uip is connectors builder resource sync-from-cache --output json
#   --connection-id <ID> | --object-name <OBJECT> to scope; --dry-run to preview
#   --overwrite ONLY when the user confirmed Replace in triage; --no-curate for the generic shape
# resource create each NEW object only (<OBJECT> from sync output, <VENDOR_PATH> from the SR).
# It is an idempotent upsert that OVERWRITES — never run it for keep-both/skip objects (Anti-patterns):
uip is connectors builder resource create --name <OBJECT> --methods <VERBS> \
  --vendor-path <VENDOR_PATH>                                     # auto-curates; --no-curate to opt out
uip is connectors builder connector validate
# Push design-state, then promote to a tenant-wide CUSTOM connector:
uip is connectors builder remote import --output json
uip is connectors builder remote publish --output json           # fire-and-forget; returns { PublishId }
#   add --wait to poll, or check later: remote publish-status <PUBLISH_ID>
#   Studio Web shows the connector ~5-10 min later.
```

### Add or customize a curated activity (a method shown as a standalone Studio activity)
`resource create` and `resource sync-from-cache` auto-curate every method by default (see
[references/standard-resources.md](references/standard-resources.md) §`curated`). Use `method curate`
below only to override the auto-generated activity name/displayName, or to curate a method created
with `--no-curate`:
```bash
uip is connectors builder connector inspect --output json
uip is connectors builder resource method curate --resource cases --method GET \
  --display-name 'Get Support Request'
uip is connectors builder resource field create --resource cases --name subject --type string \
  --method GET --response --response-curated --design-position primary   # base --response + the curated flag
uip is connectors builder connector validate
```

### Debug
```bash
uip is connectors builder connector inspect --output json
# Read the WHOLE entry, change ONLY the field at fault, then patch the COMPLETE object back —
# state patch REPLACES the node (omitted fields are dropped), so copy every field from the query.
# (Do NOT use config create --force here: it resets omitted fields like internal/hide/displayOrder.)
uip is connectors builder state query element.json/configuration/oauth.token.url --output json
uip is connectors builder state patch element.json/configuration/oauth.token.url \
  --value '<the full entry from the query above, with defaultValue set to the correct token URL>'
uip is connectors builder connector validate
# If validate keeps failing, follow Critical Rule 2: fix the reported field, re-validate, stop after 3 attempts.
```

### Review
```bash
uip is connectors builder connector inspect --output json
uip is connectors builder connector validate
# walk the checklist in references/debugging.md (auth, metadata, resources, params, hooks, events), then apply fixes
```

### Add polling events
```bash
uip is connectors builder resource list --output json    # the target resource (e.g. accounts) must already exist
uip is connectors builder config preset create --kind event --event-type polling
uip is connectors builder event polling add --resource-name accounts \
  --updated-date-field LastModifiedDate --id-field Id   # also wires the hasEvents flag
uip is connectors builder connector validate
```

### Publish to a tenant
```bash
uip login --output json                                  # if not already authenticated
uip is connectors builder connector validate
uip is connectors builder remote import --output json    # create first time, update by key after
uip is connectors builder remote publish --output json   # promote to tenant-wide CUSTOM; returns { PublishId }
#   add --wait to poll, or check later: remote publish-status <PUBLISH_ID>
# pull a tenant connector for local editing:
uip is connectors builder remote get <CONNECTOR_KEY> --include files --output json
```

## Reference Navigation

Depth lives in `references/` below — self-contained, no dependency on the CLI to supply it. For live discovery: `uip is connectors builder describe [<NOUN>]` lists the tool catalog (args, invariants, related topics); `uip is connectors builder <NOUN> <VERB> --help` is the always-current flag source.

| Task → read this | Reference |
|---|---|
| Understand what a connector is, file layout, the CRUD/curated/HTTP activities | [references/overview.md](references/overview.md) |
| element.json internals: top-level fields, resources[], parameters[], value interpolation, hook order | [references/element-json.md](references/element-json.md) |
| Standard-resource files: linking, metadata.method, curated, fields (visibility/design/searchable) | [references/standard-resources.md](references/standard-resources.md) |
| configuration[] entries: widget types, screen types, per-auth key sets, pagination + event keys | [references/configuration.md](references/configuration.md) |
| System resources: auth-validation, onProvision/onDelete, OAuth token overrides, webhook hooks | [references/system-resources.md](references/system-resources.md) |
| Writing JS hooks: execution order, context vars, done(), naming, common patterns | [references/hooks.md](references/hooks.md) |
| Polling and webhook events: config keys, event.poller.configuration schema | [references/events.md](references/events.md) |
| Debugging auth / resource / hook / event / pagination issues (investigation workflow + checklists) | [references/debugging.md](references/debugging.md) |
| Authentication setup: all 14 auth types and the OAuth scope surface | [references/auth.md](references/auth.md) |

### Command map

```text
uip is connectors builder
  connector   scaffold | inspect | validate
  remote      get [key] | import | publish | publish-status   # tenant pull/search, push, promote (needs `uip login`)
  metadata    get | set
  global      set | header (create|list|delete)
  auth        set | get | scope (set|add|delete)
  config      list | get | create | delete | preset create
  resource    list | get | create | delete | sync-from-cache
              field  (list|get|create|delete)
              method (get|set|curate)
              param  (list|get|create|delete)
              system (create|list)
  hook        list | get | create | delete
  event       polling add
  state       query <POINTER> | patch <POINTER>  # surgical read/write at a structured path
  reference   list | get <TOPIC>
  describe    [<NOUN>]
```

## Anti-patterns

Highest-cost mistakes (each maps to a Critical Rule above):

1. Editing without `connector inspect` first (Rule 1) — you'll invent keys/paths that don't exist.
2. Hand-rolling auth with `config create` instead of `auth set` (Rule 3) — leaves the auth block inconsistent.
3. Editing a config entry with a partial value (Rule 5) — `state patch` REPLACES the whole node (drops omitted fields), and `config create --force` RESETS omitted fields to defaults. To change one field, `state query` the entry and `state patch` the complete object back with only that field changed.
4. Running `resource create` for an object marked keep-both/skip in triage — it is an idempotent upsert that OVERWRITES (it does NOT error), clobbering the existing activity.
5. `sync-from-cache --overwrite` without explicit user confirmation — silently replaces SR files.
6. Wrong auth flags: `--options` (use `--scope-options`), `remote get --key` (positional `[key]`), `remote publish --background` (it's fire-and-forget; use `--wait`).
7. Non-ES5 hook syntax (optional chaining `?.`, etc.) — the Denali engine is ES5/ES6.
8. Invented `--categories` values — they must come from the approved enum; `validate` reports the list.
9. One hook file shared across resource+method+phase (Rule 10) — duplicate the file instead.
