# Data Fabric — Traps & Server Behavior

Signatures/params/examples: `dist/entities/index.d.ts` (trigger-event behavior differs per method — the JSDoc on each insert/update/delete method documents it). Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope pairing warning:** schema introspection (`entities.getAll()` / `getById()`) and record I/O sit in different scope pairs — `DataFabric.Schema.Read` vs `DataFabric.Data.Read` / `DataFabric.Data.Write`. This file mandates schema introspection before writes and filters, so an app with only Data scopes 403s on the introspection step. Check the shipped table per method.

## Anti-shapes & gotchas (read first)

Data Fabric does NOT behave like a typical RDBMS. These server behaviors are invisible to both the types and the JSDoc. Before writing analytics, filters, or update logic, call `entities.getById(id)` and inspect `fields[].name` + `fieldDataType.name`. Pick your data strategy from what's actually there — do NOT assume.

1. **Choice values come back as `numberId` integers on every read path.** Including ungrouped `getRecordById` / `queryRecordsById` items AND `groupBy` result keys. The SDK does NOT convert to string names. Code like `record.Priority.toLowerCase()` throws or produces `"5"`; `if (record.Status === "Resolved")` is always false because `record.Status` is `5`. Build `numberId → name` maps via `choiceSets.getById(<choiceSetId>)` (get `<choiceSetId>` from `entities.getById(id).fields[].choiceSetId`) and translate every read.
2. **Choice-set writes and filters take the integer `numberId`, not the value name.** Writes: sending `status: "Open"` fails with `Single choiceset value Open is not integer`. Filters: `{ fieldName: 'Status', operator: Equals, value: 'Resolved' }` matches nothing — use `value: String(numberIdForResolved)` (applies to **every** operator touching a choice field, including `NotEquals`, `In`, `NotIn`). Failure is silent: 0 rows or all rows depending on operator.
3. **Record keys must match the schema's exact casing.** The SDK does NOT pascalize keys. If the entity field is `Subject` (PascalCase, the DF UI default), sending `{ subject: … }` fails with `Required field "Subject" is not provided` — DF's required-field check is case-sensitive. Use `field.name` verbatim as the record key.
4. **Unknown keys on insert/update are silently dropped.** A typo'd field name in `insertRecordsById` does NOT error — the value is discarded without warning. Introspect the schema and validate keys before bulk operations.
5. **DF auto-creates audit fields that look like domain fields but aren't.** Every entity has `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`, `Id`, `RecordOwner` — **row metadata** (when DF wrote the row), not the business event the row represents. They appear in the schema but are not writable. Need a domain-level "created at" / "owner"? Look for a custom field with a domain-specific name; if none exists, flag it to the user rather than silently using the audit column. Seeding historical timestamps: add a custom `DATETIME_WITH_TZ` field (e.g., `OriginalCreatedTime`) — do NOT name it `CreateTime` / `CreatedTime`, the audit name conflict causes silent drops or schema rejection.
6. **No `IsNull` filter operator.** The server can't ask "where field is null" (`QueryFilterOperator` has no such member). Filter client-side after fetching, or design with explicit non-null sentinels.
7. **Aggregates require server-side `aggregates` + `groupBy`.** Don't fetch raw rows and `.length` / `.reduce` client-side — every list call returns one page (see [pagination.md](pagination.md)), so `result.items.length` after `queryRecordsById({ filter })` returns at most one page's worth, no matter how many rows match. Use `totalCount` for cardinality, `aggregates: [{ function: 'COUNT', field: 'Id' }]` (with `groupBy` for per-bucket counts) for chart data.
8. **File-type fields (`fieldDisplayType === 'File'`) aren't strings.** The record carries only metadata (`{ id, name, size, contentType }`); stringifying gives `"[object Object]"`. To display, call `entities.downloadAttachment(entityId, recordId, fieldName)` → `Blob` → `URL.createObjectURL` for an `<img src>`. **Neither `contentType` nor filename extension is reliable for detecting kind** — DF often returns `application/octet-stream`, and the stored `name` is frequently a bare UUID with no extension. To decide inline render vs download link, either (a) sniff the blob's magic bytes after download (PNG starts `89 50 4E 47`, JPEG `FF D8 FF`, GIF `47 49 46 38`, PDF `25 50 44 46`), or (b) optimistically attempt `<img src={objectUrl}>` and swap to a download link in `onError`. Writes go through `uploadAttachment(...)`, not `insertRecordById` / `updateRecordById`.

## Three paths require choice-value translation — don't miss any

| Path | Direction | What to do |
|---|---|---|
| Writes (`insertRecordsById`, `updateRecordById`, `updateRecordsById`) | name → `numberId` | translate before sending |
| Filter values (any `queryRecordsById` filter on a choice field) | name → `numberId` (as a string) | translate before sending |
| Read results (`groupBy` keys AND ungrouped record items) | `numberId` → name | translate after receiving |

Best practice: on app load, fetch each choice set once (`choiceSets.getById` returns values carrying `name` + `numberId`) and build **both** maps (`byName` and `byNumberId`). Reuse across all paths.
