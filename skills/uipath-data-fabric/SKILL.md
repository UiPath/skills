---
name: uipath-data-fabric
description: "UiPath Data Fabric entity/record CRUD via `uip df`. Create entities, insert/query/update/delete records, CSV import, file attachments. For Flow connector nodes (query/create/update/delete/get-by-id inside a `.flow`)→uipath-maestro-flow. For Orchestrator→uipath-platform. For Integration Service→uipath-platform."
---

# UiPath Data Fabric — Agent Skill

Data Fabric is UiPath's structured data store. Entities are typed schemas;
records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

---

## When to Use

- Creating or modifying entity schemas (add fields, update metadata)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Computing aggregate metrics for dashboards / KPIs (counts, sums, averages, group-by) — see [references/records-query.md](references/records-query.md#aggregates-server-side)
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

## When NOT to Use — Hand Off to Another Skill

Embedding Data Fabric reads/writes **inside a `.flow` file** as connector activity nodes (Query / Create / Update / Delete / Get Entity Record by ID) is owned by `uipath-maestro-flow`. That skill knows the node JSON, `bindings_v2.json`, connection-resource layout, and `node configure` mechanics.

Use this skill (`uipath-data-fabric`) for entity discovery and record seeding from the CLI; hand off to `uipath-maestro-flow` for in-flow node authoring.

| Task | Skill |
|------|-------|
| Discover entities, list/describe fields before authoring a flow node | `uipath-data-fabric` (`uip df entities list`/`get`) |
| Seed test records the flow will read | `uipath-data-fabric` (`uip df records insert` / `import`) |
| Add a Query/Create/Update/Delete/GetById node to a `.flow` | `uipath-maestro-flow` |
| Resolve the IS `uipath-uipath-dataservice` connection for binding | `uipath-maestro-flow` (in-flow binding) or `uipath-platform` (general IS connection management) |

---

## Not Supported — Never Attempt These

Respond that the operation is not supported. Do not try to work around it.

| Operation | Response |
|-----------|----------|
| Change a field's data type | Not supported; type is fixed at creation |
| Create a federated entity | Not supported via CLI or UiPath portal |
| Write records to a federated entity | Federated entities are read-only |
| Name a field with a C# / VB language keyword (`class`, `for`, `static`, `Sub`, `Dim`, …) | API rejects with `RESERVED_LANGUAGE_KEYWORDS` — pick a domain-specific name (see Rule 4). SQL reserved words like `Status` / `Order` / `Key` / `Type` are NOT in the check and are accepted. |
| **Upload a file to a `FILE` field via `uip df files upload`** | The CLI insists on `referenceEntityId` / `referenceFieldId` on `FILE` field create and then uploads fail with *"Relationship violation"* against arbitrary or placeholder targets. No public attachment-storage entity is documented for FILE fields. **FILE field upload is currently unusable via CLI** — surface this gap to the user; do not attempt without a confirmed target-entity contract. |

---

## Critical Rules

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool`. See *Tool Version Requirements* below for the floor needed per feature.

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. For full login/environment setup, see the `uipath-platform` skill.

3. **Always resolve entity ID first.** Use `entities list` before any operation. Never assume an entity ID.

4. **Entity, field, choice-set, and choice-value names share one validation rule.** Names must:
    - Match `^[a-zA-Z][a-zA-Z0-9_]*$` — start with a letter, then any mix of letters / digits / underscores. **Underscores are allowed** even though the error message confusingly says *"must only contain alphanumeric characters"*; `my_field` is valid.
    - Be 3–100 characters long (entity / field / choice-set names; choice-value names have no documented length cap).

    Two name-collision rejections:

    - **System column names are reserved as field names.** The exact list is: `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy`, `RecordOwner`. Note these are **not** `CreatedOn` / `UpdatedOn` — the system columns are spelled with `Time`, not `On`. `TenantId` is **not** reserved. Pick a different name: `Id` → `RecordId`, `CreatedBy` → `Author`, `CreateTime` → `CreatedDate`, `RecordOwner` → `Owner`.
    - **C# / VB language keywords are rejected.** The check is literally `CodeDomProvider.CreateProvider("C#").IsValidIdentifier(name)` plus the VisualBasic variant. That covers actual language keywords: `class`, `for`, `static`, `void`, `namespace`, `return`, `if`, `else`, `null`, `true`, `false`, `Sub`, `Dim`, `Case`, `Do`, `While`, `End`, `Me`, etc. The error string is `RESERVED_LANGUAGE_KEYWORDS` / *"cannot be a reserved word in C# or VB"*. Pick a domain-specific name: `Class` → `Category`, `Case` → `WorkItem`, `Return` → `ReturnReason`.

    **SQL reserved words are NOT in the check.** Names like `Status`, `Order`, `Group`, `Key`, `Type`, `Select`, `From`, `Where`, `Table`, `Index`, `User`, `Role` are accepted — the platform brackets column identifiers in generated SQL so they don't collide. Prefer domain-specific names anyway for read-clarity (`OrderStatus` over `Status`), but the API will not block them.

    If a `RESERVED_LANGUAGE_KEYWORDS` error comes back, surface the rejected name to the user and offer a domain-specific rename — never silently substitute.

5. **All updates require `Id` in the body.** The CLI routes single vs batch by whether the body is a JSON object (1 record) or array (multiple). Both require `"Id"` in the record. Use `records list` or `records query` to retrieve record IDs before updating.

6. **File fields cannot be written through `records insert` or `records update` — they require a separate `files upload` call.** The two-step flow:
    1. **Insert / update the record without the file field** in the body. Putting a file path, URL, or base64 blob under a FILE-typed field key in `records insert/update` is rejected or silently ignored; the FILE field value is managed by the attachment service, not the record-data service.
    2. **Upload the file** to the FILE field on that record: `uip df files upload <entity-id> <record-id> <field-name> --file <path>`. Use `files download` to retrieve, `files delete` to remove. See [`references/file-attachments.md`](references/file-attachments.md).

    The same applies to `records import` (CSV) — FILE columns are silently dropped on import. Load complex records via `records insert --file <json>` for everything else, then `files upload` per row for any attachments.

    Image / binary upload over the CLI is currently unusable for general FILE-field targets — see *Not Supported* below for the workaround (upload from the UiPath Data Fabric web UI).

7. **`records import` (CSV) handles Basic field types only — inspect the schema before choosing it.** Run `entities get` first and look at every field's `type`. If ANY field on the entity is `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, or `AUTO_NUMBER`, do NOT use `records import` — use `records insert --file <json>` instead. CSV accepts the header for those columns but silently drops the row value: no error, nothing in `ErrorFileLink`, just `null` on every imported row (or row failure if the field is `isRequired` without a `defaultValue`). When CSV is the right path: headers must match exact field names (case-sensitive); system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`) must NOT appear in the CSV — they're populated server-side. Surface the schema inspection result to the user before deciding. See [`references/bulk-import.md`](references/bulk-import.md).

8. **Never create duplicate entities.** Always `entities list` first; reuse if it already exists.

9. **Only work with native entities.** When listing entities before a write, use `entities list --native-only` to filter out federated entities. Never write to federated entities.

10. **Entity delete is irreversible — surface dependents first.** `entities delete <id> --confirm --reason "<why>"` deletes the entity and every record in it. Before invoking, scan for dependents and list them to the user one by one: (a) other entities that reference this one (run `entities list --output json` and pull every entry whose `Fields[].ReferenceEntity.Id == <id>` — these will have broken FKs after the delete); (b) choice sets used by this entity's fields (`Fields[].ChoiceSetId` from `entities get`) — those choice sets are shared and may still be in use elsewhere. Ask the user explicitly for each dependent: delete it too, leave it, or stop. Apply only the choices the user confirms — never cascade silently.

11. **Field delete is irreversible — surface impact first.** `entities update <id> --body '{"removeFields":[{"fieldName":"<name>"}]}' --confirm --reason "<why>"` drops the field and every record's value in it. Note `removeFields` takes `{"fieldName": "..."}` (NOT `{"id": "..."}` like `updateFields`). Before invoking: (a) if it's a RELATIONSHIP / FILE field, identify any code or flows that read its value; (b) if it's a CHOICE_SET field, note the choice set itself is unaffected (still shared). Ask the user explicitly: confirm the field name, confirm the loss is intentional, supply a reason for the audit log. Apply only after explicit confirmation.

12. **Complex field types need extra config and lookups, just like `DECIMAL` needs `decimalPrecision`.** `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` require `choiceSetId` (UUID, from `choice-sets list`); `RELATIONSHIP` and `FILE` require `referenceEntityId` (target entity UUID — from `entities list`) + `referenceFieldId` (target field UUID — from `entities get <target-id>`). The target entity must exist first. When the user describes a link to another row ("each order has a Customer", "each report has a Supplier"), the field type is `RELATIONSHIP` — never substitute `STRING` or `UUID` for it. **The four scalar constraint keys are also strictly per-type** — passing one to an unsupported type fails with *"Field '<name>' of type <TYPE> does not accept <option>"*: `lengthLimit` accepted only on `STRING` / `MULTILINE_TEXT`; `decimalPrecision` only on `DECIMAL` / `FLOAT` / `DOUBLE`; `maxValue` and `minValue` only on the numeric family (`INTEGER`, `BIG_INTEGER`, `DECIMAL`, `FLOAT`, `DOUBLE`). Full shape and the per-type allow-list in [`references/entity-schema.md`](references/entity-schema.md#advanced-field-constraints).

13. **Pick-or-create flow for choice sets and relationship targets.** When the user's request needs a choice set or a relationship target entity that they didn't name (or the name they gave doesn't exist), do NOT auto-create and do NOT fall back to `STRING`. Run `choice-sets list` / `entities list --native-only`, present the matching candidates by `Name` / `DisplayName`, and ask: *pick from these, or create new?* Create only with explicit user approval, using their chosen name and values. Choice-set authoring uses `choice-sets create` / `update` / `delete` + `choice-set-values create` / `update` / `delete`; surface in [`references/choice-sets.md`](references/choice-sets.md).

14. **Preview the proposed schema and get explicit approval before any create or schema-altering update.** Applies to `entities create`, `entities update` with `addFields` / `updateFields` / `removeFields`, `choice-sets create`, and `choice-set-values create`. Sequence: (1) compose the full proposal — entity / choice-set name, `displayName`, `description`, and every field with its `fieldName`, normalized UPPERCASE `type`, and all extras (`isRequired`, `isUnique`, `lengthLimit`, `maxValue` / `minValue`, `decimalPrecision`, `defaultValue`, `choiceSetId`, `referenceEntityId` / `referenceFieldId`); (2) render it as a readable table or formatted JSON block (NOT a raw CLI command); (3) ask the user to confirm or revise — wait for an explicit *yes / approved / proceed* before invoking the CLI; (4) apply revisions exactly as requested — never silently add, drop, rename, or retype fields the user didn't approve; re-show the revised proposal and ask again. Show the proposal **once per round** — don't re-show an unchanged schema after every minor question.

15. **Choice / relationship record values use lookup tokens, not labels.** Choice value → integer `NumberId` (single) or array of `NumberId`s (multi), from `choice-sets list-values`. Relationship value → target record's UUID `Id` regardless of which field was bound as `referenceFieldId`. Filter / `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` filtering has special operator semantics — see [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields).

16. **Answer with `records query`, not from memory.** Counts, sums, filters, lookups — issue a fresh `records query` (or `records list`) and use the server's response. Do not reuse cached insert responses, IDs you generated earlier, or values from previous tool results. Exception: the `Id` returned by the same `records insert` you just made.

17. **`records query` filters.** Body shape, operators, per-type support, response, and unsupported-operator handling are in the [filter contract](references/filter-platform-contract.md). Symbol-form operators only (`==`/`Equals`/`like` → 400). On an unsupported operator/type or a missing value, don't run it — ask the user (Rule 18). **Return all fields by default** — omit `selectedFields` unless a subset is requested.

18. **When a request isn't supported OR the upstream system returns an error, stop and confirm with the user — never silently substitute.** Triggers (not exhaustive): a filter operator unsupported for the field type / not in the symbol list / missing a value (see [filter contract → Unsupported operator](references/filter-platform-contract.md#unsupported-operator-or-missing-value)); an unknown `fieldName`; a nonexistent or federated entity; a missing CLI verb (`removeFields`, … — see *Not Supported*); cross-entity joins or value forms the API can't serve; ANY 4xx/5xx, validation error, `RESERVED_LANGUAGE_KEYWORDS`, constraint-violation, or quota response from the API.
    Sequence: (1) surface the full upstream message verbatim — never swallow it; (2) state precisely what isn't supported or what failed (cite the rule / schema / error code); (3) propose a concrete next step keyed to the error — e.g. unknown `fieldName` → list the entity's real same-type fields from `entities get` and ask which; `RESERVED_LANGUAGE_KEYWORDS` → suggest a domain-specific rename; constraint violation → show the allowed range; missing dependency → list candidates via `entities list` / `choice-sets list` and offer pick-or-create (Rule 13); (4) apply **only** what the user approves, never your own fallback. If nothing works, error out and recommend the right sibling skill (`uipath-maestro-flow` / `uipath-platform` / `uipath-rpa` / `uipath-agents` / `uipath-test`) — don't fabricate or return a degraded result.

---

## Tool Version Requirements

| Feature | Required `@uipath/data-fabric-tool` |
|---------|--------------------------------------|
| `entities` / `records` CRUD, `query` with filters/sort, `records import`, `files` | `0.9.0+` |
| Server-side `aggregates` and `groupBy` on `records query` | `1.0.1+` |

Upgrade with `uip tools install @uipath/data-fabric-tool@latest` when a feature appears to silently no-op (e.g. aggregate body keys returning raw record lists).

---

## Quick Start

```bash
# List entities (use --native-only before any write)
uip df entities list --native-only --output json

# Get entity schema (field names and types)
uip df entities get <entity-id> --output json

# List records (first page)
uip df records list <entity-id> --limit 50 --output json

# Insert one record
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json

# Query with a filter
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json

# Aggregate query — count of records per Status (server-side groupBy)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

For Complex types  field shapes and value formats, see [`references/entity-schema.md`](references/entity-schema.md#supported-field-types) and [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields).

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist | `entities list` → `entities get <id>` |
| Explore only native entities | `entities list --native-only` |
| Manage choice sets | `choice-sets list` / `list-values <id>` / `create` / `update` / `delete`; values via `choice-set-values create` / `update` / `delete` — full surface in [`references/choice-sets.md`](references/choice-sets.md) |
| Create a new entity | `entities create <name> --body '{"fields":[{"fieldName":"Title","type":"STRING"}]}'` — for complex field types (`CHOICE_SET_*`, `RELATIONSHIP`) and their required extras, see [`references/entity-schema.md`](references/entity-schema.md#supported-field-types) |
| Update entity / add fields | `entities update <id> --body '{"addFields":[{"fieldName":"NewField","type":"STRING"}]}'` |
| Update existing field metadata | `entities update <id> --body '{"updateFields":[{"id":"<field-uuid>","displayName":"New Label","isRequired":true}]}'` — `id` is the field UUID from `entities get Fields[].ID` |
| Update entity metadata | `entities update <id> --body '{"displayName":"New Name","description":"desc"}'` |
| Delete an entity (irreversible — list dependents first) | `entities delete <id> --confirm --reason "<why>"` — see Rule 10 for the dependent-discovery flow |
| Delete a field (irreversible — confirm impact first) | `entities update <id> --body '{"removeFields":[{"fieldName":"<name>"}]}' --confirm --reason "<why>"` — note `removeFields` uses `fieldName`, NOT `id` like `updateFields`. See Rule 11 |
| Read records (first page) | `records list <entity-id> --limit 50` |
| Read records (next page) | `records list <entity-id> --cursor <NextCursor>` |
| Get one record | `records get <entity-id> <record-id>` |
| Insert one record | `records insert <entity-id> --body '{...}'` (or `--file`). **Do NOT include FILE-typed field keys in the body** — file content uploads via a separate `files upload` call after the record is created (Rule 6). Choice / relationship value formats: see [`references/records-query.md`](references/records-query.md#writing-choice-set-and-relationship-values) |
| Batch insert | `records insert <entity-id> --body '[{...},{...}]'` |
| Update one record | `records update <entity-id> --body '{"Id":"<record-id>","field":"val"}'` |
| Batch update | `records update <entity-id> --body '[{"Id":"<id1>","field":"val"},{"Id":"<id2>","field":"val"}]'` |
| Delete records | `records delete <entity-id> <id1> <id2>` |
| Filter/search records | `records query <entity-id> --body '{...}'`. Choice / relationship filter operators: see [`references/records-query.md`](references/records-query.md#filtering-on-choice-set-fields) |
| Aggregate / group-by metrics | `records query <entity-id> --body '{"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}],"groupBy":["FieldName"]}'` |
| Bulk import from CSV (Basic field types only — `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER` are silently dropped) | `records import <entity-id> --file data.csv` |
| Bulk seed records that include complex fields | `records insert <entity-id> --file records.json` with a JSON array body |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file path` |
| Download file | `files download <entity-id> <record-id> <field-name> --destination path` |
| Delete file | `files delete <entity-id> <record-id> <field-name>` |

---

## Field Types

Pass the exact `EntityFieldDataType` string — the CLI is case-sensitive. Common types: `STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `UUID`, `FILE`, plus `AUTO_NUMBER` and the complex types (`CHOICE_SET_*` / `RELATIONSHIP` / `FILE`) whose required extras are covered in Rule 12. Full table with SQL backing types and value semantics in [`references/entity-schema.md`](references/entity-schema.md).

**Normalize user input to UPPERCASE before invoking.** Users typically say `boolean`, `string`, `decimal`, `datetime` in their prompts. The CLI rejects lowercase / mixed-case variants with `Cannot read properties of undefined (reading 'sqlTypeName')`. Case-fold to the enum value: `boolean` → `BOOLEAN`, `String` → `STRING`, `Decimal` → `DECIMAL`, etc. Synonyms that don't map 1:1 (e.g. `number` → `INTEGER` or `DECIMAL`; `text` → `STRING` or `MULTILINE_TEXT`) need disambiguation — see [`references/entity-schema.md` → Normalizing user-facing type names](references/entity-schema.md#normalizing-user-facing-type-names).

### Advanced Field Constraints

Optional per-type constraints on create/update — `lengthLimit` (STRING, MULTILINE_TEXT), `maxValue` / `minValue` (INTEGER, BIG_INTEGER, DECIMAL, FLOAT, DOUBLE), `decimalPrecision` (DECIMAL, FLOAT, DOUBLE). See `references/entity-schema.md` for ranges and examples.

---

## Workflow: Discover → Act → Verify

1. **Discover** — list entities, get schema, check existing records
2. **Act** — create/insert/update
3. **Verify** — re-read to confirm the operation succeeded

```bash
uip df entities list --native-only --output json
uip df entities get <entity-id> --output json
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json
uip df records list <entity-id> --limit 50 --output json
# Use HasNextPage + NextCursor to page through results
uip df records list <entity-id> --cursor <NextCursor> --output json
```

---

## Query Request Format

Pass the query body via `--body` or `--file`; pagination uses `--limit` / `--cursor` / `--offset` CLI flags, never body keys (see [Pagination](#pagination) below). The body shape, operators, per-type support, and response shape live in [`references/filter-platform-contract.md`](references/filter-platform-contract.md); query-only extras (`selectedFields`, `sortOptions`) are documented in [`references/records-query.md`](references/records-query.md).

## Pagination

`records list` / `records query` paginate via `--limit`, `--cursor`, `--offset`. See [`references/records-query.md`](references/records-query.md).

---

## Troubleshooting

> **Any error not in this table → Rule 18.** (Surface verbatim, propose options keyed to the error, apply only what the user confirms.)

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown command: df` | Tool not installed | `uip tools install @uipath/data-fabric-tool` |
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| `Record must include 'Id'` | Update body missing Id | Every record passed to `records update` must include `"Id": "<record-id>"` — both single and batch |
| `Each field must include a 'fieldName' string` | Invalid field in `entities create` | Use `{"fieldName":"myfield"}` not `{"name":"myfield"}` |
| `Entity name resolution failed` | Query/import with bad ID | Verify entity exists with `entities list` |
| Import errors in CSV | Header mismatch | Run `entities get` and check exact field names (case-sensitive) |
| `records import` succeeded but choice / relationship / file column is `null` on every row | `records import` silently drops complex field types (Basic only) | Re-seed via `records insert` with a JSON body — see [`references/bulk-import.md`](references/bulk-import.md) |
| Write to federated entity | Entity is read-only | Use `--native-only`; federated entities cannot be written to |
| `cannot be a reserved word in C# or VB` (alias: `RESERVED_LANGUAGE_KEYWORDS`) | Entity or field name is a C# or VB language keyword (e.g. `Class`, `Case`, `For`, `Sub`, `Dim`, `Return`). SQL keywords (`Status`, `Order`, `Key`, etc.) are NOT in the check — if one of those is the rejected name, look for another cause. | Surface the rejected name + the error to the user. Offer concrete renames: `Class` → `Category`; `Case` → `WorkItem` / `Matter`; `Return` → `ReturnReason`. Apply only the user-confirmed rename. See Rule 4. |
| `Choiceset member name must only contain alphanumeric characters, start with alphabetic characters and not be C# keyword` | Choice-set value `Name` violates the keyword rule that also gates entity / field names (Rule 4) | Namespace the system `Name` and keep `DisplayName` unchanged. Full rule + the related `NumberId`-ordering caveat for batch creates: [`references/choice-sets.md` → Value `Name` validation](references/choice-sets.md#value-name-validation). |
| Constraint violation (`"outside of allowed range"`, `"exceeds lengthLimit"`, etc.) | Write value broke `minValue` / `maxValue` / `lengthLimit` / `decimalPrecision` | Surface the full error to the user, show the allowed range from `entities get`, and ask what value to use — never silently clamp. See Rule 18. |
| `referenceEntityId` missing on RELATIONSHIP/FILE field | Field defined with names instead of UUIDs | Pass `referenceEntityId` + `referenceFieldId` (UUIDs from `entities list` / `entities get`). See Rule 12. |
| `Cannot read properties of undefined (reading 'sqlTypeName')` | Field `type` value didn't match a known `EntityFieldDataType` enum — almost always lowercase / mixed-case (e.g. `"boolean"` instead of `"BOOLEAN"`) | Case-fold to the UPPERCASE enum from the type table — see [`references/entity-schema.md` → Normalizing user-facing type names](references/entity-schema.md#normalizing-user-facing-type-names) |
| `Update entity data failed. Relationship violation` (on `files upload`) | The `FILE` field was created with `referenceEntityId`/`referenceFieldId` pointing at an unrelated entity; the server enforces it as a real FK and the file's UUID isn't a record of that entity | FILE upload via CLI is currently unusable for general targets — see Not Supported table. Tell the user: the FILE field exists, but uploads fail until the right target-entity contract is known. |
| FILE field shows as `null` after `records insert` even though the body included a value for it | The record-data service does not accept content for FILE-typed columns (Rule 6). Whatever was put under the FILE key was ignored. | Insert the record without the FILE key, then attach the file separately: `uip df files upload <entity-id> <record-id> <field-name> --file <path>`. CSV `records import` has the same drop behavior. |
| `Each field in removeFields must include a non-empty 'fieldName' string` | `removeFields` was called with `{"id": "..."}` (the shape `updateFields` uses) instead of `{"fieldName": "..."}` | Re-emit with `{"fieldName": "<exact field name>"}` — see Rule 11 |

---

## References

- `references/entity-schema.md` — Field definitions, supported types, schema update patterns, choice-set + relationship field shapes
- `references/choice-sets.md` — Full choice-set CRUD (`list`/`list-values`/`create`/`update`/`delete` plus `choice-set-values create`/`update`/`delete`), look up `NumberId`s, add CHOICE_SET fields to entities, write choice values on records
- `references/records-query.md` — Query filter syntax, pagination, sorting, choice/relationship semantics on read & write
- `references/filter-platform-contract.md` — Filter body structure, per-type operator support matrix, and what to do when a request needs an unsupported operator
- `references/file-attachments.md` — File field upload/download/delete file
- `references/bulk-import.md` — CSV format requirements and the Basic-fields-only limitation (complex types are silently dropped — use `records insert` with a JSON body instead)
