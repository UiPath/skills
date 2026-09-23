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

| The user says | Use |
|---|---|
| "create an entity", "add a field to X" with no solution in play | tenant — [`entity-schema.md`](entity-schema.md) |
| "add an entity to this solution", "my flow needs a table" | **`--local`**, this file |
| "the flow reads Orders" and Orders is already in Data Fabric | tenant entity, referenced — see [Referenced entities](#referenced-entities-are-not-yours-to-edit) |

When it is genuinely ambiguous, ask. Creating a live tenant entity when the
user wanted one that ships with their solution leaves an orphan on the tenant
that the solution will not manage.

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

Nine types. This is narrower than the tenant surface, and the limit is real —
the authored document format has no representation for the rest.

| `type` | Stored as |
|---|---|
| `STRING` | NVARCHAR — `lengthLimit` |
| `MULTILINE_TEXT` | MULTILINE — `lengthLimit` |
| `MULTILINE_MAX` | MULTILINE_MAX — `lengthLimit` is a **byte** budget |
| `DECIMAL` | DECIMAL — `decimalPrecision`, `minValue`, `maxValue` |
| `BOOLEAN` | BIT |
| `DATE` | DATE |
| `DATETIME_WITH_TZ` | DATETIMEOFFSET |
| `AUTO_NUMBER` | DECIMAL, auto-assigned |
| `FILE` | attachment column |

**Not authorable locally:** `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`,
`RELATIONSHIP`. No authored type pair exists for them in any host, including
Studio Web and the VS Code modeller. Model those in Data Fabric on a live
entity instead — do not substitute `STRING` for a relationship.

**Never authorable anywhere:** `INTEGER`, `BIG_INTEGER`, `FLOAT`, `DOUBLE`,
`UUID`, `DATETIME` — the six UI-broken types from
[Rule 12b](data-fabric.md). The command refuses them and names the
substitution (`INTEGER` → `DECIMAL` with `decimalPrecision: 0`, `DATETIME` →
`DATETIME_WITH_TZ`, `UUID` → `STRING`).

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

A `core.datafabric.*` node needs more than the entity name, and the extra
attributes are **not** something to hand-write:

1. Author the node with `entityConfig.entityName` set to the entity.
2. Run `uip maestro flow format <Project>.flow`.

Format fills in `_resourceKey`, `_folderKey` and the two `bindings[]` rows —
the same thing the Studio Web / VS Code entity picker writes. It reports
`EntitiesBound` (nodes wired), `EntityBindingRowsRemoved` (stale rows dropped
when a node is repointed, renamed or deleted), and regenerates
`bindings_v2.json`. A `BindingsFileError` in the output means the `.flow` was
written but that artifact is stale until the command succeeds again.

**Why this matters, and why a missing binding is hard to diagnose:** a node
carrying only `entityName` serializes to a bare tenant-scoped
`=datafabric.<Name>` literal. A locally authored entity is provisioned into the
debug or deployment folder, not at tenant level, so the literal resolves to
nothing and the run fails with:

```
[300205] Error executing query expansion in Data Fabric
         Data Fabric returned: Entity <Name> does not exist
```

That error names the entity, so it reads as "the entity wasn't created" when
the entity exists and the binding is missing. `flow validate` passes either
way. If you see it, check the node has `_resourceKey` and run `format`.

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
(`OmittedProjects` / a warning naming each one). The entity still reaches a
debug session through the solution's resources; it just is not editable as a
project in the browser. A `solution download` will not contain it.

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
