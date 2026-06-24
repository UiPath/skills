# Connector Overview — the mental model

A connector wraps a vendor's REST API into UiPath Studio activities and triggers.
**Udon** (the Integration Service runtime) sits between Studio and the vendor API,
standardising pagination, authentication, parameter mapping, and error handling.
For the commands that build all of this, see [SKILL.md](../SKILL.md) — this file is
depth only (no command map, no workflows).

**Glossary** (used throughout these references): **Udon** = the runtime executor that
renders the connection form, runs the auth flow, calls the vendor, and applies hooks at
request time. **periodic** = the build/template tooling that validates and packages the
connector on disk. **IS** = Integration Service (the UiPath product); an **IS slug** is the
IS-side resource path `/<object>` (vs the vendor path). When a doc says "the server", read it
as Udon at runtime. The CLI noun for an endpoint is **activity** (an element.json resource
entry + its standard-resource file).

## The 5 CRUD activities + curated + HTTP Request

Every connector automatically gets 5 CRUD activities, each a dropdown listing every
standard resource that implements that method:

| Activity | Method   | Description                              |
|----------|----------|------------------------------------------|
| List     | GET      | Filtered list. Supports CEQL query.      |
| Get      | GETBYID  | Retrieve a single record by ID.          |
| Create   | POST     | Insert a new record.                     |
| Update   | PATCH/PUT| Modify an existing record.               |
| Delete   | DELETE   | Remove a record by ID.                   |

A **curated activity** is a standalone activity shown alongside the 5 CRUDs (e.g.
"Get Support Request"), produced from a `metadata.method.{METHOD}.curated` block in the
SR file. `activity create` auto-curates every method by default. Field visibility
(`requestCurated`/`responseCurated`) and `design.position`:
[standard-resources.md](standard-resources.md). Every connector also gets a free
**HTTP Request** activity (hide it via `hasHttpRequest` in element-metadata.json).

## File layout (periodic-{elementKey}/)

```text
app/element/
├── element.json              # Core definition: auth, configuration[], resources[], parameters[], hooks[]
├── element-metadata.json     # Catalog entry: name, categories, capability flags, latestVersion
├── image.svg                 # Icon
├── hooks/*.js                # JS pre/post request transformers (extracted from element.json by scripts/build)
├── standard-resources/*.json # Per-object metadata: fields, methods, curated, events
└── event-hook/               # Event/polling hook definitions
```

## How the files link

element.json tells Udon HOW to call the vendor (vendorPath, parameters, hooks).
Standard resources tell Udon WHAT the data looks like (fields, types, method config).

1. **resource entry → SR file**: `standardResourceName` is the canonical link
   (`"accounts"` → `standard-resources/accounts.json`). Linkage rule + the older path-match
   fallback: [standard-resources.md](standard-resources.md).
2. **resource entry → hook files**: each `resources[].hooks[].ref` names a file in `hooks/`.
3. **global hooks**: top-level `hooks[]`, same `ref` field; always run for every request.
4. **system resources**: element.json resource entries with NO SR file and no
   `standardResourceName` → never appear as activities. Internal only (onProvision,
   oauthOnTokenRefresh, provisionAuthValidation). Override a built-in by matching its path.

## Connector key format

- Official UiPath: `uipath-{vendor}-{product}` (e.g. `uipath-salesforce-sfdc`).
- Custom / design: `design-{org}-{slug}` — `init --organization <ORG>` derives it from the
  org slug + `--name`. Repo name = `periodic-` + key (e.g. `periodic-design-myorg-acme`).

## Scope

In scope: RESTful JSON APIs, a single base URL, polling/webhook triggers, JS hooks. Out of
scope: GraphQL, SOAP/XML, SDKs, multiple base URLs. The builder authors connectors by hand
from the vendor's API docs; it has no OpenAPI/Postman import command.

## See also
- [element-json.md](element-json.md) — element.json internals
- [configuration.md](configuration.md) — config + auth keys
- [standard-resources.md](standard-resources.md) — SR / field shape
