# Standard Resource Reference

StandardResource (SR) files live in `app/element/standard-resources/*.json` (one per
object). They define the schema, display metadata, and per-method config. element.json
says HOW to call the API; the SR says WHAT the data looks like.

Author SR files with the `activity` verbs — `activity create` (whole resource: SR file +
one element.json entry per method), `activity field create`, `activity method set`,
`activity param create`. Never hand-edit an SR for things a verb can do; reserve raw
`state patch` for fields no flag exposes (see [element-json.md](element-json.md)
§state-patch). Command map + workflows live in SKILL.md — don't re-derive them here.

## Link to element.json
`standardResourceName` on the element.json resource entry is canonical (`"accounts"` →
`accounts.json`). The SR filename is independent of the path. element.json is the source
of truth; on every write the SR's contract params auto-reconcile to it. System resources
have NO SR file and no `standardResourceName` (see [system-resources.md](system-resources.md)).

The SR's `metadata.method.<VERB>.{reference ?? path}` MUST resolve to the element.json
resource `path` — the IS slug `/<object>`, NOT the vendor path — or the method won't
attach and won't show under the object in Studio. `validate` warns "SR linkage broken"
when nothing resolves.

## Top-Level Fields
`name` (matches filename), `path`, `displayName` (also the Studio activity name),
`elementKey`, `type`/`subType` (`"standard"`), `custom` (`"no"`/`"yes"` — string),
`isPriority`, `isHidden`, `executionType` (`sync`/`async`/`hybrid`),
`metadata` (object), `fields` (object — **TOP-LEVEL**, not inside metadata).

## metadata.method — per-method config
Keys are method names: `GET`, `GETBYID`, `POST`, `PATCH`, `PUT`, `DELETE`. Only methods
defined here appear in the CRUD dropdown. Set/replace one with `activity method set
--resource <name> --method <VERB>`. Each entry:

| Property | Description |
|----------|-------------|
| `method` | Same as the key. |
| `operation` | List / Retrieve / Create / Update / Delete (`--operation`). |
| `operationId` | Unique op id (`--operation-id`). |
| `description` | Method description. |
| `hasCEQL` | Supports CEQL filtering (`--has-ceql`; typically true for GET). |
| `isHidden` | Hide this method from the dropdown (`--hidden`). |
| `responseDisplayName` / `responseDescription` | Response var name/desc in Studio. |
| `parameters` | Same schema as element.json resource params. element.json is the source of truth for contract fields; SR-only UI fields are preserved. Runtime-only types (`value`, `body`) are excluded from the SR side. |
| `curated` | If present, this method becomes a standalone curated Studio activity. **Auto-added by default** by `activity create` (pass `--no-curate` to skip). |

Curated block: `{ "name", "displayName", "description", "isHidden" }`. A curated
activity's fields also need field-level `requestCurated`/`responseCurated` visibility —
see **fields** below.

### by-id methods (GETBYID / PATCH / PUT / DELETE)
`activity create` auto-adds the `/{primaryKey}` path param for by-id methods, so a
GETBYID method's path becomes `/<object>/{id}` without extra flags. The suffix is added
ALWAYS for `GETBYID`, and for `PATCH`/`PUT`/`DELETE` only when the activity is CRUD (it also
defines `GET`/`GETBYID`); a write-only activity keeps its base path. A per-method
`--method-vendor-path GETBYID=/foo` override that lacks `{id}` STILL works — the id param
is derived from the canonical resource path. Only model GETBYID for TRUE by-id endpoints,
not a search/list-by-filter endpoint.

### nested / parent-id vendor paths (mid-path `{token}`)
A path variable is bound on TWO sides: element-side `{name}` in the internal `path`, vendor-side
`{vendorName}` in the `vendorPath`. When a `{token}` sits **only in the vendor path** — a
parent-scoped sub-collection like `--vendor-path /issue/{issueId}/comment` whose internal slug is the
flat `/comments` — it CANNOT be `type:"path"`: element-service looks for the segment in the flat
element URL, doesn't find it, and 400s **"required parameter '<name>' not found"** at request time
(reads/writes on comments/transitions/assignee/attachments all fail). `activity create` now emits the
right shape automatically:

- **query→path (default for a vendor-only token):** internal `/comments`, param
  `{ name:"issueId", type:"query", vendorName:"issueId", vendorType:"path" }`. Element-service takes the
  value as a query param and interpolates it into the vendor template. This is how shipped connectors
  (e.g. Jira `curated_add_comment`) declare parent ids. Callers pass it at run time via
  `uip is resources run … --query issueId=<id>`.
- **path→path (token in the internal path):** pass `--resource-path /comments/{id}` so `{id}` is a real
  element URL segment → `type:"path"`. If the internal and vendor tokens differ in name, the param is
  `{ name:"id", vendorName:"issueId", type:"path", vendorType:"path" }` (name↔internal, vendorName↔vendor);
  the CLI can't auto-derive a differing pair, so author it with `activity param create`.

`validate` now flags both failure modes: a `type:"path"` param whose `{name}` is missing from the
internal path, and a `{token}` in the vendorPath with no param sending it (unbound → 404).

## metadata.events
`{ "eventMode": ["polling"] }` — `trigger create` sets this. Full `eventMode` value set:
[events.md](events.md) §"SR-level event metadata".

## fields — definitions (top-level object)
Each key = field name and MUST equal `field.name`. Add/update with `activity field
create --resource <name> --name <field> [--type <t>]`. Re-running MERGES: top-level keys
you pass win, unspecified keys are kept, and per-method visibility is deep-merged.
`--type` is required only for a NEW field, optional on a merge.

Core: `name`, `type` (string/integer/number/boolean/date/date-time/object/array),
`displayName`, `nativeType` (`--native-type`), `format`, `description`, `sampleValue`,
`defaultValue` (`--default-value`, scalar or JSON), `primaryKey` (`--primary-key`),
`sortOrder` (`--sort-order`), `enum` (`--enum`), `enhancedEnum` (`--enhanced-enum`),
`custom`. **`mask` is a date/number FORMAT PATTERN string** (e.g. `yyyy-MM-dd'T'HH:mm:ssZ`),
NOT a boolean — set it with `--mask <pattern>`. **`enum` MUST end up as the object form `[{"value":"x"}]`** — the
server SR marshaller rejects a bare string array `["x"]` at PUBLISH time. Both `--enum` and
`--fields-file` auto-normalize a bare `["a","b"]` to the object form; and `validate` now FLAGS a
bare/`!{value}` enum still sitting in an SR (e.g. from a hand `state patch`), so it no longer
slips through to a publish failure. `--enhanced-enum '[{"name":"Label","value":"V"}]'` writes
labelled options.

**Method visibility** (`field.method` object) controls request/response per method:
```json
"method": {
  "GET":  {"name": "GET",  "response": true},
  "POST": {"name": "POST", "request": true, "response": true, "required": true}
}
```
Set it with the visibility flags. `--method` is REPEATABLE and the flags
(`--request`/`--response`/`--required`/`--request-curated`/`--response-curated`) apply to
EVERY listed method: `--method GET --method POST --response` makes the field a response on
both. For DIFFERENT visibility per method in one call, use the inline form —
`--method 'GET=response,response-curated' --method 'POST=request,required'` — and prefix a
flag with `!` to UNSET it on a merge (`--method 'GET=!request'` writes `request: false`
over an accidental `true`; no `state patch` needed). Bare and inline `--method` forms mix.
Properties: `response`, `request`, `required`, `requestCurated`, `responseCurated`,
`designOverrides`. `requestCurated`/`responseCurated` gate a field's visibility INSIDE a
curated activity (plain `request`/`response` is not enough); auto-curation sets them from
the field's request/response side.

**Searchable**: `searchable` (`--searchable`), `searchableOperators`
(`--searchable-operators '=,!=,like,>,<,>=,<=,in'`), `searchableNames` (`--searchable-names`).

**design** object (`--design-position primary|secondary|none`, `--component`, `--hidden`):
`position`, `component` (FolderPicker, Button, Connectors, Resources, Fields, Processes,
Queues), `isHidden` (what `--hidden` writes — the key shipped connectors use; a dependent
dropdown's `--depends-on` writes the same key), `loadByDefault`, `isMultiSelect`,
`enableUserOverride`, `dictionaryWidget`, `solutionResourceKind`, `fieldActions` (cascading
show/hide based on another field's value).

### Dropdowns (reference / lookup)
A dropdown lists rows from a **List resource in this connector** — you choose which field is
DISPLAYED and which is SENT. A dropdown can live on a **field, a path param, or a query param**, so
the same flags exist on both `activity field create` and `activity param create`:

```
--reference-object <name>   target List resource's object name (e.g. teams)
--reference-path <path>     its list path (e.g. /teams); use {parent} for a dependent dropdown
--lookup-value <field>      the ONE field sent as the value (e.g. id)
--lookup-names <csv>        display-candidate fields (e.g. id,displayName)
--display-pattern <p>       visible label, e.g. "{displayName}" or "{name} - {id}" (combines lookupNames)
--filter-pattern <p>        server-side type-ahead template with {filter} (optional)
--load-by-default           populate the list on open;  --multi-select;  --enable-user-override
```

The reference points at a resource whose GET is `operation:"List"`; `lookupValue`/`lookupNames`
name fields in that resource's returned records. Raw `--reference '<json>'` (`{objectName,path,
lookupValue,lookupNames}`) is still accepted as an escape hatch. `objectName`+`path`+`lookupValue`
are expected; `validate` warns if `lookupValue` is missing.

**Dependent dropdowns** (child list scoped by a parent — e.g. Teams channel depends on team): put
`{<parentName>}` in the child's `--reference-path` (must equal the parent field/param's name) and
pass `--depends-on <parentName>`. That injects `design.isHidden` + a show/hide `fieldActions` pair,
so the child appears only after the parent has a value and its list is filtered by the parent:

```
activity field create --resource messages --name team_id --reference-object teams \
  --reference-path /teams --lookup-value id --lookup-names id,displayName \
  --display-pattern "{displayName}" --load-by-default --method "POST=request,required"
activity field create --resource messages --name channel_id --depends-on team_id \
  --reference-object "teams::channels" --reference-path "/teams/{team_id}/channels" \
  --lookup-value id --lookup-names id,displayName --display-pattern "{displayName}" \
  --method "POST=request,required"
```

The parent (`team_id`) must exist as a sibling field/param on the same resource — `validate` warns
if a dependent path's `{token}` or a rule's `refFieldName` names nothing on the resource.

**Show/hide on a value** (conditional field, not a lookup): `--field-actions '<json>'` is the
escape hatch — an array of `{ actionType: show|hide|required|optional, rules: [{ type:"field",
refFieldName:"<other>", refFieldValues:["card"], isCleared:false }] }`. Use `refFieldValues:["*"]`
for "any value", `isCleared:true` to fire when the ref field is empty; multiple rules in one action
are ANDed. **`--depends-on` vs `--field-actions`:** use `--depends-on` for a dependent dropdown
(show once the parent has ANY value — it hard-codes `["*"]`); use `--field-actions` when the child
should appear only for a SPECIFIC parent value (e.g. `refFieldValues:["task"]`).

**Dropdowns on path / query params** work identically — the same flags exist on `activity param
create`. For a **path variable** just pass `--type path`: the CLI auto-encodes it as `type:"query"`
+ `vendorType:"path"` when the variable isn't a segment of the flat internal path (element-service
interpolates it into the vendor path — a literal `type:"path"` there would 400). Example — a `boardId`
path-param dependent dropdown scoped by `projectId`:

```
activity param create --resource cards --method POST --name boardId --type path \
  --reference-object boards --reference-path "/projects/{projectId}/boards" \
  --lookup-value id --lookup-names id,name --display-pattern "{name}" --depends-on projectId
```

## Authoring for catalogue parity — the curation layer
Wiring dropdowns is necessary but NOT sufficient to match a catalogue connector's Studio Web UX.
Benchmarking generated connectors vs catalogue (Gmail/Outlook/OneDrive) showed the dropdown plumbing
reaches parity, but four things a blind build usually MISSES — do these to close the gap:

1. **Static / enum-backed pickers.** Not every dropdown is backed by a live vendor list — some are a
   fixed set of literal choices. Two cases:
   - **Small closed choice** (writeMode, valueInputOption, operation, role/type) → use
     `--enum '["A","B"]'` or `--enhanced-enum '[{"name":"Label","value":"V"}]'` on **`field create`
     OR `param create`** (both support it). This renders a static combo directly — do NOT stand up a
     helper List resource for these. (Catalogue puts `enum`/`enhancedEnum` right on the field/param.)
   - **Large / shared / vendor-fetched set** (timezones, currencies) → author a small helper List
     resource holding that set and point a dropdown at it (`--reference-object timezones
     --reference-path /timezones`). The catalogue adds a `timezones` picker on every calendar /
     send-mail activity this way.
2. **Curated responses, not raw vendor JSON.** Don't leave an activity's output as raw vendor field
   names. Curate it — friendly output field names + a curated subset — via per-field `responseCurated`
   + `displayName` (e.g. `EventTitle`/`StartDateTime` instead of `subject`/`start`). Set curated
   visibility in the `--fields-file` method map; both `responseCurated` and the kebab
   `response-curated` spelling are accepted (normalized).
3. **Scope pickers on list / read verbs.** A list activity should offer the folder / calendar /
   parent **scope** as a dropdown, not just a generic `where` / `pageSize`. e.g. Get Email List →
   an email-folder picker; Get Event List → a calendar picker.
4. **Field completeness.** Cover the catalogue's fields, not just the obvious ones (e.g. `Importance`
   / `ReplyTo` on send-email, `ListColumns` on SharePoint list items).

**Known CLI limits (catalogue-only for now — can't reach 100% here):** there is no hierarchical
**tree-picker** reference type (the OneDrive drive→folder→file browser) and no **merged/combined**
picker (sheets+tables+named-ranges in one dropdown); the SR-level `type:"curated"` + `section` /
`category` grouping isn't settable (activities still surface as standalone via
`metadata.method.<VERB>.curated`). Don't try to hand-fake these — note them as gaps.

## Bulk field authoring — `--fields` / `--fields-file`
`activity create --fields '<json-array>'` (inline) or `--fields-file <path>` seeds the whole
field schema in one shot. Two shapes are accepted: an ARRAY of field objects
(`[{ "name": "email", ... }]`), OR a name→spec OBJECT map (`{ "email": { ... } }`) where the KEY
is the field name — the exact shape a standard-resource stores `fields` under, so you can paste a
real connector's `fields: {…}` object VERBATIM. Each field object uses the SAME keys as above
(`name` required in the array form; `type` optional — defaults to `string`). This path is **validated and
normalized before anything is written** (same engine as `field create`): a bad shape fails
fast with a `ValidationError` listing EVERY problem, rather than silently authoring a broken
SR that only fails at publish. Specifically it:
- normalizes a bare `enum: ["a","b"]` → `[{"value":"a"},…]`;
- accepts per-method visibility under `method` (canonical) OR `methods` (alias) — but not both;
- requires `objectName`+`path` on a `reference`; requires `name`+`value` on each `enhancedEnum`;
- checks `design.position` ∈ {primary,secondary,none} and that boolean flags are booleans;
- REJECTS unknown top-level keys (typo guard) and duplicate field names.
Example element: `{ "name": "status", "type": "string", "enum": ["open","closed"],
"searchable": true, "method": { "GET": { "response": true } } }`. `--fields`/`--fields-file`
carry the full property set (enum, enhancedEnum, reference, searchable*, primaryKey,
sortOrder, defaultValue, design, …) — none are dropped.

The schema is OPEN: recognized keys are listed by `activity field schema`, but connectors
carry a vendor long tail (`refName`, `searchableDisplayName`, `isHidden`, …) — those pass
through with a WARNING, not an error, so real fields are never blocked. Only true
publish‑breakers hard‑fail: missing `name`, duplicate names, both `method`+`methods`, a
non‑object `method` map.

Don't guess the shape: `activity field schema` prints the exact accepted keys, types,
visibility methods, and a copy‑pasteable **valid** example (no connector needed). To
bulk‑add fields to an EXISTING activity, re‑run `activity create --name <same>
--fields-file <path>` — it MERGES fields into the existing SR (existing fields kept).

## Rules
1. Field dict key MUST equal `field.name`. 2. `fields` is top-level. 3. Only methods in
   `metadata.method` appear in dropdowns. 4. Primary-key field needs `"primaryKey": true`.
5. SR linkage (above) must resolve to the IS slug `/<object>`, not the vendor path.

## See also
- [element-json.md](element-json.md), [events.md](events.md), [system-resources.md](system-resources.md)
