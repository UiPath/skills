---
name: uipath-connector-builder
description: "Always invoke for `element.json`, `element-metadata.json`, `standard-resources/*.json`, or a `periodic-uipath-*` connector repo. Authors UiPath Integration Service connectors (REST+JSON) on disk via `uip is connectors builder`: scaffold a connector, configure auth (any of 14 types), add resources/fields/params/methods, write JS pre/post hooks, add polling events, manage config and system resources, validate, and pull/push to a tenant. For operating a published connector (connections, ping, run an activity)→uipath-platform. For .flow connector nodes→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Connector Builder

Author UiPath Integration Service connectors on disk with the `uip is connectors builder` CLI. A connector is a `periodic-uipath-{vendor}-{product}/` repo whose core is `app/element/element.json` plus `standard-resources/*.json` and JavaScript `hooks/`. Connectors wrap **REST APIs that return JSON only** — no SOAP, GraphQL, or XML.

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
2. **Validate after every change.** Run `connector validate` after each mutation. It runs the full periodic check set and exits non-zero on failure.
3. **`auth set` owns all authentication.** It writes the config entries, `authentication.type` / `typeOauth` / `authenticationTypes`, and the OAuth refresh resource in one call. Never hand-roll auth via `config create`.
4. **`resource create` writes both sides in one call** — the standard-resource file AND the `element.json` resource entries. Pass `--skip-sr` (or use `resource system create`) only for system resources that need no SR file.
5. **Use `state query` / `state patch` for surgical single-field edits**, the orchestrator verbs (`resource create`, `auth set`, ...) for creation. Resource paths in `state` pointers are URL-encoded: `/contacts` → `%2Fcontacts`.
6. **Never invent config keys, resource paths, or IDs.** Read the current state first (`connector inspect`, `state query`, `config list`, `resource list`) before writing.
7. **Target a specific connector with `--connector-dir <path>`.** Without it, the CLI walks up from the cwd, then scans immediate subdirectories.
8. **Output is the `{Result, Code, Data}` envelope.** Add `--output json` when you need to parse output. Never suppress stderr.
9. **`remote import` / `remote get` need `uip login`.** Authenticate before any tenant pull/push.
10. **One hook file per resource+method+phase.** Duplicate logic rather than sharing a file. Prefer a `type:"value"` parameter with `${configuration.<key>}` interpolation over a hook for static header/auth injection.

## Workflow

Each workflow is an ordered sequence of copy-paste-ready commands.

### New connector
```bash
uip is connectors builder connector scaffold --name 'Acme Widgets'
uip is connectors builder auth set --auth-type oauth2 \
  --authorization-url https://acme.com/oauth/authorize \
  --token-url https://acme.com/oauth/token --scope 'read write'
uip is connectors builder auth scope set --options '[{"value":"read"},{"value":"write"}]'   # OAuth scopes, if any
uip is connectors builder global set --accept-type application/json --content-type application/json --paginator-version 2
uip is connectors builder resource create --name accounts --methods GET,POST,PATCH,DELETE \
  --vendor-path /v1/accounts --primary-key id
uip is connectors builder metadata set --categories 'CRM,Sales'
uip is connectors builder connector validate
```

### Add a resource
```bash
uip is connectors builder connector inspect
# research the vendor API, then:
uip is connectors builder resource create --name contacts --methods GET,GETBYID,POST \
  --vendor-path /v1/contacts --primary-key id --fields-file ./contacts-fields.json
uip is connectors builder hook create --resource-name contacts --method GET --hook-type postRequest \
  --custom-code-file ./unwrap.js                                   # optional
uip is connectors builder connector validate
```

### Pull resources from the SR cache
When the cache already holds StandardResource artifacts for this connector (authored by `uip is resources standardize`, or seeded from a flow via `uip maestro flow extract-http-nodes`), pull them onto disk in one call instead of rebuilding by hand.

> **Standard entry point for HTTP-node-derived connectors** is the maestro-flow background-publish loop — fire-and-forget after the user picks their primary destination (Studio Web / Orchestrator). It runs the triage + scaffold + sync + publish in one shot without touching the .flow file. The steps below are the underlying primitives — invoke them directly only when authoring a connector that isn't being seeded from a flow.

**Triage before mutating.** If a connector with this key already exists on the tenant, pull it first and compare against the cached SRs so the user can pick add / rename / replace per activity:
```bash
uip is connectors builder remote get --key <elementKey> --output json
#   404 → net-new connector. Run scaffold + the pipeline below.
#   200 → existing connector. Pull files and inspect before any mutation:
uip is connectors builder remote get <elementKey> --include files --output json
uip is connectors builder resource list --output json    # the activities already on it
# For each cached object whose name matches one in the list, ask the user
# (AskUserQuestion): keep both (rename to <name>_v2) / replace / skip.
# Replacing risks dropping fields the existing activity had — diff fields first
# and surface the deltas in a follow-up prompt.
```

Then run the pipeline:
```bash
uip is connectors builder connector inspect                      # confirm scaffold + element.json:key
uip is connectors builder resource sync-from-cache --output json
#   add --connection-id <id> | --object-name <obj> to scope
#   --dry-run to preview; --overwrite ONLY when the user confirmed Replace in triage
# sync-from-cache writes ONLY app/element/standard-resources/*.json — it does NOT touch element.json.
# Run resource create for each NEW object (skip ones marked Replace; resource create errors on duplicates):
uip is connectors builder resource create --name <object> --methods <VERBS> \
  --vendor-path <relative-vendor-path-from-the-SR>
uip is connectors builder connector validate
# Push design-state to tenant:
uip is connectors builder remote import --output json
# Background-promote design → tenant-wide CUSTOM (the published-publish step):
uip is connectors builder remote publish --background --output json
#   Returns { PublishId }. Studio Web shows the connector ~5-10 min later.
```

### Add a curated activity (a method shown as a standalone Studio activity)
```bash
uip is connectors builder connector inspect
uip is connectors builder resource method curate --resource cases --method GET \
  --display-name 'Get Support Request'
uip is connectors builder resource field create --resource cases --name subject --type string \
  --method GET --request-curated --response-curated --design-position primary
uip is connectors builder connector validate
```

### Debug
```bash
uip is connectors builder connector inspect
uip is connectors builder state query element.json/configuration                 # auth slice
uip is connectors builder state query element.json/resources/GET/%2Fcontacts     # one resource (path URL-encoded)
# cross-reference references/debugging.md, then patch the fix:
uip is connectors builder state patch element.json/configuration/oauth.token.url \
  --value '{"defaultValue":"https://acme.com/oauth/token"}'
uip is connectors builder connector validate
```

### Review
```bash
uip is connectors builder connector inspect
uip is connectors builder connector validate
# walk the checklist in references/debugging.md (auth, metadata, resources, params, hooks, events), then apply fixes
```

### Add polling events
```bash
uip is connectors builder config preset create --kind event --event-type polling
uip is connectors builder event polling add --resource-name accounts \
  --updated-date-field LastModifiedDate --id-field Id
uip is connectors builder metadata set --has-events
uip is connectors builder connector validate
```

### Publish to a tenant
```bash
uip login --output json                                  # if not already authenticated
uip is connectors builder connector validate
uip is connectors builder remote import                  # create first time, update by key after
# pull a tenant connector for local editing:
uip is connectors builder remote get <connector-key> --include files
```

## Reference Navigation

The depth lives in the `references/` pages below — the skill is self-contained and does not depend on the CLI to supply this content. For live discovery, `uip is connectors builder describe [<noun>]` is the current tool catalog (args, invariants, related topics) and `uip is connectors builder <noun> <verb> --help` is the always-current flag source.

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

```
uip is connectors builder
  connector   scaffold | inspect | validate
  remote      get [key] | import                 # tenant pull/search & push (needs `uip login`)
  metadata    get | set
  global      set | header (create|list|delete)
  auth        set | get | scope (set|add|delete)
  config      list | get | create | delete | preset create
  resource    list | get | create | delete
              field  (list|get|create|delete)
              method (get|set|curate)
              param  (list|get|create|delete)
              system (create|list)
  hook        list | get | create | delete
  event       polling add
  state       query <pointer> | patch <pointer>  # surgical read/write at a structured path
  reference   list | get <topic>
  describe    [<noun>]
```
