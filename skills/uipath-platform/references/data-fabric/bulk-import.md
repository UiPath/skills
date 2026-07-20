# Bulk Import

CLI syntax, flags, and response shape: [Data Fabric CLI docs → `records import`](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#records-import--csv-bulk-load).

## Agent behavior — required before invoking `records import`

1. **If the entity does NOT exist yet** and the user wants one built from the CSV: that's `entities create`, not `records import`. Field types must be **confirmed, not silently inferred** — see [`data-fabric.md` Rule 14](data-fabric.md#critical-rules). Then run `records import`.
2. **If the entity has any complex-type field** (`CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER`), `records import` will silently drop those columns — no error, no `ErrorFileLink` entry. Run `entities get <entity-id>` first; list the columns that will be dropped; ask the user whether to (a) accept the silent drop and re-seed those columns via `records insert` + `files upload` afterwards, or (b) switch to `records insert --file <json>` upfront ([`records-query.md` → Writing choice-set and relationship values](records-query.md#writing-choice-set-and-relationship-values)). Do not invoke import without an answer (Rule 20).
3. **CSV header must exactly match field names (case-sensitive)** and must NOT include system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`). Full CSV rules in the CLI docs above.
4. **Partial success is possible.** After `records import`, compare `Data.InsertedRecords` vs `Data.TotalRecords`; download `Data.ErrorFileLink` for the failed rows and surface the CSV verbatim (Rule 18).
