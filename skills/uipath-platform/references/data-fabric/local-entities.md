# Local Entities — authoring a schema into a solution

`uip df entities <verb> --local` authors a Data Fabric entity **into a solution
on disk**. Nothing exists on the platform until the solution deploys, so these
commands need no login and touch no tenant.

The same verbs without `--local` are the other half: they operate on live
entities over the API. One noun, two targets — the flag is what says which.

```
uip df entities create Product                    → a live entity, now, on the tenant
uip df entities create Product --local            → files on disk; an entity at deploy
```

Everything else changes with it. Without `--local`, `get` / `update` / `delete`
take an entity **id**; with `--local` they take the entity **name**, because
nothing has an id until deploy.

---

## Which one does the request want?

A local entity is part of a solution. Tenant is the default; use `--local` only
when the user explicitly asks for the entity to live in, or ship with, a
solution.

| The user says | Use |
|---|---|
| "create an entity", "add a field to X" | tenant — [`entity-schema.md`](entity-schema.md) |
| "add an entity to this solution", "the entity should ship with the solution" | **`--local`**, this file |
| "my flow needs a table", or a solution is open but nothing says where the entity lives | ambiguous — ask |
| "the flow reads Orders" and Orders is already in Data Fabric | tenant entity, referenced — see [Referenced entities](#referenced-entities-are-not-yours-to-edit) |

Ask rather than guess either way: a tenant entity the user wanted in the
solution is an orphan the solution will not manage, and a local entity the user
wanted on the tenant does not exist until a deploy.

---

## Commands

All are filesystem-only. Run them from the solution directory.

```bash
uip df entities create   <Name> --local [--project-name <project>]
uip df entities list            --local [--project-name <project>]
uip df entities get      <Name> --local [--project-name <project>]
uip df entities update   <Name> --local [--project-name <project>] --body '<json>'
uip df entities validate [<Name>] --local [--project-name <project>]
uip df entities delete   <Name> --local [--project-name <project>] --yes [--force]
```

`validate` is local-only — it has no tenant counterpart (the server is the
judge there) and refuses to run without `--local`.

### `--project-name` is optional

An Entity *project* is a folder that holds many entities; it is a different
thing from the entity, and it has looser name rules. Most of the time you do
not need to name it:

| Verb | `--project-name` omitted |
|---|---|
| `create` | a new Entity project named after the entity |
| `get` / `update` / `delete` | the owning project is found by entity name — entity names are solution-wide unique, so one name resolves to one project |
| `list` / `validate` | the whole solution |

Pass it when you mean something narrower: adding a **second** entity to an
existing project, or scoping `list` / `validate` to one project. An existing
`--project-name` must be a project of type Entity — `pack` only ships entities
from those.

```bash
# One entity, one project of the same name — the common case.
uip df entities create Product --local

# A second entity into the project the first one made.
uip df entities create Supplier --local --project-name Product

# Several entities under a name of your choosing.
uip df entities create Product --local --project-name Catalog
uip df entities create Supplier --local --project-name Catalog
```

### Name rules differ by level

| | Allowed |
|---|---|
| Project name | letters, digits, `_` and `-` |
| Entity name | `^[a-zA-Z][a-zA-Z0-9_]{2,99}$` — underscores legal, hyphens not |
| **Field** name | `^[a-zA-Z][a-zA-Z0-9]{2,99}$` — **no underscores** |

Field names are the strict ones. This trips agents that mirror a column name
from a CSV.

### `update` takes the tenant body

Same payload shape as `uip df entities update` — `addFields` / `updateFields` /
`removeFields`, plus `displayName` and `description`. One body, two targets.

```bash
uip df entities update Product --local --body '{
  "addFields": [
    {"name":"Sku","type":"STRING","lengthLimit":64,"isRequired":true,"isUnique":true},
    {"name":"UnitPrice","type":"DECIMAL","decimalPrecision":2,"defaultValue":"0"},
    {"name":"InStock","type":"BOOLEAN"}
  ]}'
```

`defaultValue` is **text for every field type** — a `DECIMAL` default is
`"0"`, not `0`.

### Response envelopes still say "inline"

The `Code` on every local response is `InlineEntityCreated`,
`InlineEntityList`, `InlineEntitySchema`, `InlineEntityUpdated`,
`InlineEntityValidated` or `InlineEntityDeleted` — a naming holdover from
before the flag was `--local`. Filter on those, not on a `Local…` prefix.

---

## Authorable field types

Field types, options, and the mapping from user words ("number", "text") to a
type are shared with tenant entities — use
[`entity-schema.md` → Supported Field Types](entity-schema.md#supported-field-types)
and its [UI-broken types](entity-schema.md#ui-broken-types--do-not-use) table.
A local entity accepts that table with one difference:

**Not authorable locally:** `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`,
`RELATIONSHIP`. No authored type pair exists for them in any host, including
Studio Web and the VS Code modeller. Model those in Data Fabric on a live
entity instead — do not substitute `STRING` for a relationship.

The UI-broken types (`INTEGER`, `FLOAT`, `UUID`, `DATETIME`, …) that the tenant
API accepts are **refused** by `--local`, with the substitution named in the
error (`INTEGER` → `DECIMAL` with `decimalPrecision: 0`).

The error tells the caller which case they hit and where to go, so surface it
verbatim rather than guessing a replacement.

---

## Referenced entities are not yours to edit

A solution can also **reference** a live platform entity
(`uip solution resources add --source remote --kind Entity`). On disk the two
look almost identical — same resource envelope, same `kind`, same `type`. One
field separates them:

```
FolderId: 99999999-9999-9999-9999-999999999999   → authored locally, yours
FolderId: <any real GUID>                        → a live platform entity
```

`entities list --local` reports this as `LocallyAuthored`. `update --local` and
`delete --local` refuse a referenced entity, because editing its local copy
would land an unreviewed schema change on a shared object at deploy —
bypassing the `--yes --reason` gate the tenant path requires for exactly that
reason.

To change a referenced entity: `uip df entities update <id>` or Data Fabric.

---

## Broken pairs

An authored entity is two files that have to agree: a `<Name>.entity` stub in
the project and the definition resource under
`resources/solution_folder/entity/native/<Name>.json`. Hand-editing, a bad
merge or a half-finished rename can leave them disagreeing.

`entities list --local` reports each of those rows with a `Problem` (the pair
does not verify) or a `ProjectProblem` (the project directory itself cannot be
read). The ordinary `delete` refuses them, because it cannot read what it is
being asked to remove — which left the one state that most needs cleaning up
reachable only by hand. `--force` is the way out:

```bash
uip df entities delete Product --local --yes --force
```

It removes whichever half is on disk without reading it, and reports
`Forced: true`. Use it only on a row `list` flagged.

---

## Using a local entity from a flow

A `core.datafabric.*` node needs more than the entity name: the entity's
resource key, and the placeholder folder `99999999-9999-9999-9999-999999999999`
that deploy and debug replace. Without them the node is tenant-scoped and fails
at runtime (below). Which way you supply them depends on how the flow is
authored.

<!--skill-flavor:flow-sdk-local-entity-keys:start-->
**Builder SDK (`.flow.ts`, the Flow skill's default).** Pass both keys to the
`dataFabric*` factory — `folderKey` from `FolderId` in
`uip df entities get <Name> --local`, `resourceKey` from the `Source: Local` row
of `uip solution resources list --kind Entity`. Do not look the entity up on the
tenant: it is not there until deploy. Leaving the keys out — the Flow skill's
fallback for a tenant entity — makes the node look for a tenant entity that
does not exist, so the run fails. See
[/uipath:uipath-maestro-flow — data-fabric.md](../../../uipath-maestro-flow/references/data-fabric.md#an-entity-the-solution-authors-itself).

<!--skill-flavor:flow-sdk-local-entity-keys:end-->
**Hand-written `.flow` JSON:**

1. Author the node with `entityConfig.entityName` set to the entity.
2. Run `uip maestro flow node configure <Project>.flow <node-id> --detail '{"entityName":"<Name>"}'`.

`node configure` fills in `_resourceKey`, `_folderKey` and the two `bindings[]`
rows — the same thing the Studio Web / VS Code entity picker writes — reports
them as `BindingsCreated`, and regenerates `bindings_v2.json`. It is idempotent,
so a second run reports `BindingsCreated: 0` and changes nothing.

Two zero counts that are **not** failures: a second node naming the same entity
adds no rows because `bindings[]` is flow-wide, and re-running the command on an
already-wired node is a no-op. A genuine miss is never silent — naming an entity
this solution does not author succeeds with `BindingsCreated: 0` **and** a
`Warnings` entry saying so.

Adding the node with the CLI instead needs no follow-up — `node add` resolves
the keys on the spot:

```bash
uip maestro flow node add <Project>.flow core.datafabric.read \
  --input '{"entityConfig":{"entityName":"Product","resultMode":"multiple"}}'
```

**Why this matters, and why a missing binding is hard to diagnose:** a node
carrying only `entityName` serializes to a bare tenant-scoped
`=datafabric.<Name>` literal. A locally authored entity is provisioned into the
debug or deployment folder, not at tenant level, so the literal resolves to
nothing and the run fails with:

```
[300205] Error executing query expansion in Data Fabric
         Data Fabric returned: Entity <Name> does not exist
```

That error names the entity, so it reads as "the entity wasn't created" when the
entity exists and the binding is missing. You should never reach it: `flow
validate` reports the node as an error (`INLINE_ENTITY_UNBOUND`) naming the exact `node configure` to run — in a builder-SDK project, fix the `.flow.ts` instead, or the next `compile` reverts it —
`flow pack` and `uip solution pack` run the same rule, and `flow debug` and `flow eval` raise the
same message before packaging. Entities this solution only references, and
tenant entities resolved at runtime, are not reported — they have no local
resource to bind to.

---

## Shipping

```bash
uip solution pack <solution> --dry-run     # validates entity projects, emits no package
uip solution pack <solution> ./out
uip solution publish ./out/<pkg>.zip
uip solution deploy run --name <n> --package-name <p> --package-version <v> …
```

The entity becomes a real table at **deploy**, in the deployment's folder.
Verify with `uip df entities list --folder-key <new-folder> --output json`.

An entity project emits no package of its own — its definition resource under
`resources/solution_folder/entity/native/` is the deployable payload, so pack
validates the project rather than building it.

**Studio Web cannot import Entity projects.** `uip solution upload` and
`uip maestro flow debug` omit them from the package and say so
(`OmittedProjects` / a warning naming each one). The browser never holds the
Entity project, so it is not editable there, and a `solution download` will not
contain it.

**`flow debug` works once per solution, then fails.** The first
`uip maestro flow debug` creates the cloud solution and provisions the entity
into a `Debug_<project>` folder, so that run reads and writes records normally.
Every later run overwrites that same cloud solution, which Studio Web does not
support for a solution with an Entity project — from the second run on, the
debug fails. Tell the user before they rely on it:

- **To debug repeatedly, use the UiPath extension for VS Code**, which debugs
  the local solution and handles Entity projects.
- Use `uip maestro flow debug` only for a single check of a fresh solution.
- To ship, `uip solution pack` / `publish` / `deploy run` is unaffected — the
  entity is created in the deployment's folder and the flow binds to it.

Two consequences worth knowing before you reach for `upload`:

- **An Entity-only solution has nothing to upload.** Omitting every project
  would leave an empty cloud solution reported as a success, so `upload`
  fails instead. That is a real shape — `entities create Product --local`
  with no other project scaffolds exactly it. Ship it with
  `uip solution pack` / `publish`, which is the path that deploys the
  entity anyway.
- **Upload the directory, not a prebuilt `.uis`.** The `.uis` bytes pass
  through untouched, so nothing can omit a project from one; an archive
  that already holds an Entity project is refused up front rather than sent
  to fail with a bare `20039`. `uip solution upload <solution-dir>` is the
  form that omits and reports.

---

## Validate is the loop

`entities validate --local` runs the same stub↔resource pairing and schema
checks `solution pack` runs, without packing — so a clean result means the
project will not fail pack on its entities. It exits non-zero on findings, and
without `--project-name` it gates the whole solution, failing on the first
project it cannot read or validate.

Run it after every edit. It is the only check between an authored document and
a deploy; `flow validate` does not look at entities, and the CLI's other
commands cannot see a schema problem until pack.

Diagnostics it raises: `ENTITY_NAME_INVALID`, `ENTITY_NAME_NOT_UNIQUE`,
`FIELD_NAME_INVALID`, `DUPLICATE_FIELD_NAME`, `FIELD_TYPE_NOT_ALLOWED`,
`NAME_RESERVED`, `SYSTEM_FIELD_MISSING`, `SYSTEM_FIELD_MODIFIED`,
`FIELDS_MALFORMED`, `TOO_MANY_MULTILINE_MAX`.

`SYSTEM_FIELD_MODIFIED` is the one worth recognising: the five system fields
(`Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`) must match their
canonical shape exactly, and an entity that has round-tripped through the
service carries extra per-field metadata that is **not** an edit. Do not
"tidy" system fields.

---

## Rules

1. **Drive this through the commands, not the files.** The schema lives
   JSON-escaped inside `spec.resourceJson` in the definition resource; the
   commands own both halves of the pair and keep them in step. Hand-editing is
   how a `Problem` row gets made.
2. **Entity names are solution-wide unique**, not per project. That is what
   lets `--project-name` be optional.
3. **System fields cannot be removed or changed** — the commands refuse.
4. **`delete --local` takes `--yes` but no `--reason`.** Nothing is deployed
   and git is the audit trail; the tenant delete's reason has nowhere to go.
5. **Removing a local field is not destructive** — no rows exist yet. The
   tenant's `removeFields` gate does not apply.
6. **No `--folder-key`.** A locally authored entity has no folder until deploy.
7. **Only on an explicit ask.** A local entity is part of a solution; create
   one only when the user asks for the entity to live in, or ship with, the
   solution. Otherwise the tenant path is the default.
