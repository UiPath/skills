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

## metadata.events
`{ "eventMode": ["polling"] }` — `trigger create` sets this. Full `eventMode` value set:
[events.md](events.md) §"SR-level event metadata".

## fields — definitions (top-level object)
Each key = field name and MUST equal `field.name`. Add/update with `activity field
create --resource <name> --name <field> [--type <t>]`. Re-running MERGES: top-level keys
you pass win, unspecified keys are kept, and per-method visibility is deep-merged.
`--type` is required only for a NEW field, optional on a merge.

Core: `name`, `type` (string/integer/number/boolean/date/date-time/object/array),
`displayName`, `nativeType`, `format`, `description`, `sampleValue`, `primaryKey`
(`--primary-key`), `sortOrder` (`--sort-order`), `enum` (`--enum '[{"value":"active"}]'`),
`mask` (`--mask`), `custom`. **`enum` MUST be the object form `[{"value":"x"}]`** — the server
SR marshaller rejects a bare string array `["x"]` at PUBLISH time even though `validate` passes.
The CLI auto-normalizes a bare `--enum '["a","b"]'` to the object form, but hand-edited SR/`state
patch` enums must use `[{"value":…}]`.

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
both. Properties: `response`, `request`, `required`, `requestCurated`, `responseCurated`,
`designOverrides`. `requestCurated`/`responseCurated` gate a field's visibility INSIDE a
curated activity (plain `request`/`response` is not enough); auto-curation sets them from
the field's request/response side.

**Searchable**: `searchable` (`--searchable`), `searchableOperators`
(`--searchable-operators '=,!=,like,>,<,>=,<=,in'`), `searchableNames`.

**design** object (`--design-position primary|secondary|none`, `--component`, `--hidden`):
`position`, `component` (FolderPicker, Button, Connectors, Resources, Fields, Processes,
Queues), `hidden` (what `--hidden` writes — the field-level key is `design.hidden`, NOT
`isHidden`), `loadByDefault`, `isMultiSelect`, `enableUserOverride`, `dictionaryWidget`,
`solutionResourceKind`, `fieldActions` (cascading show/hide based on another field's value).

**reference** object (lookup dropdown): `{ "lookupNames": ["name"], "lookupValue": "id",
"path": "/accounts" }` — set via `state patch` (no field flag).

## Rules
1. Field dict key MUST equal `field.name`. 2. `fields` is top-level. 3. Only methods in
   `metadata.method` appear in dropdowns. 4. Primary-key field needs `"primaryKey": true`.
5. SR linkage (above) must resolve to the IS slug `/<object>`, not the vendor path.

## See also
- [element-json.md](element-json.md), [events.md](events.md), [system-resources.md](system-resources.md)
