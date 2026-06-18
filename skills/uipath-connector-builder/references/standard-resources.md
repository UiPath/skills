# Standard Resource Reference

SR files live in `app/element/standard-resources/*.json` (one per object). They define
the schema, display metadata, and method config; element.json says HOW to call the API,
the SR says WHAT the data looks like.

**Link:** `standardResourceName` on the element.json resource entry is canonical
(`"accounts"` → `accounts.json`). The SR filename is independent of the path. Older
connectors match on SR `path`. System resources have no SR file (see
[system-resources.md](system-resources.md)).

## Top-Level Fields
`name` (matches filename), `path`, `displayName` (also the Studio activity name),
`elementKey`, `type`/`subType` (`"standard"`), `custom` ("no"/"yes" — string),
`isPriority`, `isHidden`, `executionType` (`sync`/`async`/`hybrid`),
`metadata` (object), `fields` (object — **TOP-LEVEL**, not inside metadata).

## metadata.method — per-method config
Keys are method names: `GET`, `GETBYID`, `POST`, `PATCH`, `PUT`, `DELETE`. Only methods
defined here appear in the CRUD dropdown. Each entry:

| Property | Description |
|----------|-------------|
| `method` | Same as the key. |
| `operation` | List / Retrieve / Create / Update / Delete. |
| `operationId` | Unique op id. |
| `description` | Method description. |
| `hasCEQL` | Supports CEQL filtering (typically true for GET). |
| `isHidden` | Hide this method from the dropdown. |
| `responseDisplayName` / `responseDescription` | Response var name/desc in Studio. |
| `parameters` | Same schema as element.json resource params. element.json is the source of truth for contract fields; SR-only UI fields preserved. Runtime-only types (`value`, `body`) are excluded from the SR side. |
| `curated` | If present, this method becomes a standalone curated activity. **Auto-added by default** by `resource create` and `resource sync-from-cache` (pass `--no-curate` to skip). |

Curated block: `{ "name", "displayName", "description", "isHidden" }`. The activity's fields also need field-level `requestCurated`/`responseCurated` visibility — see **fields** below.

## metadata.events
`{ "eventMode": ["polling"] }` — see [events.md](events.md) §"Event types" for the full
`eventMode` value set.

## Cache-sync normalization
`resource sync-from-cache` normalizes each cached SR before writing it to `standard-resources/`:
- `metadata.method.<VERB>.{path,reference}` and the top-level `path` are rewritten to the IS
  slug `/<object>` so periodic links the method to its element.json resource. Cache SRs carry
  the VENDOR path; left as-is, the object shows in Studio with its name but NO methods.
- Each method is auto-curated into a standalone Studio activity (curated block + the
  field-level visibility described under **fields**). Pass `--no-curate` to opt out.

## fields — definitions (top-level object)
Each key = field name and MUST equal `field.name`.

Core: `name`, `type` (string/integer/number/boolean/date/date-time/object/array),
`displayName`, `nativeType`, `format`, `description`, `sampleValue`,
`primaryKey`, `sortOrder`, `enum` (`[{"value":"active"}]`), `mask`, `custom`.

**Method visibility** (`field.method` object) controls request/response per method:
```json
"method": {
  "GET": {"name": "GET", "response": true},
  "POST": {"name": "POST", "request": true, "response": true, "required": true}
}
```
Properties: `response`, `request`, `required`, `requestCurated`, `responseCurated`,
`designOverrides`. `requestCurated`/`responseCurated` gate a field's visibility **inside a curated
activity** (plain `request`/`response` is not enough); the auto-curation step sets them from the
field's request/response side.

**Searchable**: `searchable`, `searchableOperators` (`["=","!=","like",">","<",">=","<=","in"]`),
`searchableNames`.

**design** object: `position` (`primary`/`secondary`/`none`), `component`
(FolderPicker, Button, Connectors, Resources, Fields, Processes, Queues), `isHidden`,
`loadByDefault`, `isMultiSelect`, `enableUserOverride`, `dictionaryWidget`,
`solutionResourceKind`, and `fieldActions` (cascading show/hide based on another
field's value).

**reference** object (lookup dropdown): `{ "lookupNames": ["name"], "lookupValue": "id", "path": "/accounts" }`.

## Rules
1. Field dict key MUST equal `field.name`. 2. `fields` is top-level. 3. Only methods in
`metadata.method` appear in dropdowns. 4. Primary key field needs `"primaryKey": true`.
5. `standardResourceName` links a resource entry to its SR; the SR's `metadata.method.<VERB>.{reference ?? path}` must also resolve to the element.json resource `path` (the IS slug `/<object>`, **NOT** the vendor path) for the method to attach and show under the object in Studio. periodic matches on that value; `connector validate` warns "SR linkage broken" when nothing resolves.

## See also
- [element-json.md](element-json.md), [events.md](events.md)
