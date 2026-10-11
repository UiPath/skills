# Pre-flight data checks + the minimal data mapping

Cheap local checks before any upload — each one saves a multi-minute ingest round-trip.

## Inspect the file first

1. **Encoding / BOM** — For non-UTF-8 (Windows-1252 / ISO-8859-1), declare the encoding with `ingestions create --encoding` or the mapping's `SourceSettings.Encoding`, or loading may mangle/fail.
2. **Delimiter + field regularity** — Stream the file and assert every line has the same field count to catch embedded-delimiter / quoting issues; CSVs here are often `;`-delimited.
3. **Junk rows** — Strip fully-empty trailing rows (`;;;;…`); with a NotNull-error on the key column, they cause the whole table to `Failed to load datasources`.
4. **Date format** — Inspect token ranges to distinguish `dd-mm` from `mm-dd` (token1 max > 12 ⇒ day-first). Set `DateTimeFormatString`; formats vary **per file** in the same dataset, so check each.
5. **Cardinality** — Count distinct case ids and activities to sanity-check the mapping.

## Minimal `mapping.json`

```json
{"Tables":[{"SourceName":"Event_log","TargetName":"Event_log","Source":"blob","SourceSettings":{"Encoding":"utf-8","FieldDelimiter":";","QuoteCharacter":"\""},"IsMandatory":true,"ValidationType":"specificationOnly","Fields":[{"DataType":"text","SourceName":"Incident ID","TargetName":"Case_ID","IsMandatory":true,"ValidationType":"specificationOnly"},{"DataType":"text","SourceName":"IncidentActivity_Type","TargetName":"Activity","IsMandatory":true,"ValidationType":"specificationOnly"},{"DataType":"datetime","DataTypeSettings":{"DateTimeFormatString":"dd-mm-yyyy hh:mm:ss"},"SourceName":"DateStamp","TargetName":"Event_end","IsMandatory":true,"ValidationType":"specificationOnly"}]}]}
```

Rules:

- Core `uipath.custom` event-log targets: **`Case_ID`**, **`Activity`**, **`Event_end`** (datetime); optional: `Event_start`, `User`.
- `DateTimeFormatString` is lowercase, non-strftime: `dd-mm-yyyy hh:mm:ss` (`.nnn` for milliseconds).
- Omitted `IsNotNull` / `IsUnique` default per field to `{ Enabled: false, Severity: "warning" }`. `data-mapping update` applies these defaults too, so one mapping works for both commands. To fail loading on nulls, set them explicitly to `{ Enabled: true, Severity: "error" }` on `Case_ID`/`Activity`/`Event_end`.
- Map risky columns as `text` and parse in SQL (e.g., odd-format dates, decimal-comma numbers); only `Event_end` must be a real `datetime`. Unmapped columns load under their raw source names and remain usable as attributes.
- **Multi-table apps**: Add `Tables[]` entries (Incidents, Interactions, Changes, …); all load, but template models reference only `Event_log`. Custom models `source('sources', '<Table>')` the rest and join on a shared key.

## Fixing the mapping after the app exists

A mapping mistake does **not** require deleting and recreating the app. `apps data-mapping` reads and replaces an existing app's mapping. Run:

```bash
uip pm apps data-mapping get <app> --destination ./mapping.json   # download mapping + note Data.ETag
# ...edit: fix DateTimeFormatString, move a column to the right TargetName, or map another column...
uip pm apps data-mapping update <app> --file ./mapping.json --etag 'W/"639…"'   # --etag REQUIRED
uip pm files upload <app> ./data.csv --input-table Event_log      # ONLY if source columns changed
uip pm ingestions create <app> --wait                             # mapping applies to the NEXT ingestion
```

`get` without `--destination` inlines the mapping as `Data.Mapping` (useful with `--output-filter`, e.g. `--output-filter "Mapping.Tables[0].Fields[].{Src:SourceName,Tgt:TargetName}"`).

Facts worth not re-learning:

- A mapping change needs a re-ingest, not `transformations apply`: `apply` reruns SQL over parsed data; mapping governs parsing. Editing the mapping then running `apply` appears successful but changes nothing.
- **`dev` only.** The backend allows `PUT` on `dev`; `published` is read-only, and the CLI restricts `update --stage` to `dev` up front.
- **`--etag` is REQUIRED on `update` and must be the ETag returned by your `get`.** It proves the local edit was based on the version read. The CLI deliberately does not fetch a fresh ETag before `PUT`, which would make `If-Match` pass regardless of intervening writes. A concurrent UI mapping-editor edit is rejected with `409 UserError_ETagFileConflict`: rerun `get` for the latest version and its new ETag, reapply your change, then update with that `--etag`. Repeating the unchanged update fails again.
- `update` reports `Tables` (mapped table names) and `IngestionNeeded: true`, not an ETag. Confirm the write by rerunning `get` and diffing: its ETag is a **content checksum**, unchanged by re-pushing an identical mapping.
- A table-less mapping is refused locally: `{ "Tables": [] }` (or any file with no usable table) fails `No tables found in …` before an API call, so it cannot wipe the stored mapping.
- Either key casing works: PascalCase (`{"Tables":[…]}`, used by this recipe and `apps create --data-mapping`) or API camelCase. `get --destination` writes the API response verbatim in camelCase (`{"tables":[…]}`), while envelope `Data.Mapping` is PascalCased like other envelope fields. Both represent the same document and can be passed to `update --file` or `apps create --data-mapping` on another app.
- Structurally invalid mappings fail safe with `400 UserError_DatapipelineBadRequest` / `INVALID_DATASOURCE_ARGUMENT`; the stored mapping remains untouched.
- An inaccessible app id returns `403 UserError_NotAuthorized`, not `404`; check the id with `apps list` rather than treating this as a mapping-permissions problem.
- Reading `published` for an app never published succeeds with the *template's* mapping, `ETag: W/"0"`, and `UseInLoad: false`; this is not the app's real mapping.

## Other app types

The mapping above targets `uipath.custom` `Event_log`. For source-system templates (`uipath.p2p.sap`, `uipath.im.servicenow`, …), use the same `mapping.json` shape but map extracts to the template's expected input tables. Create the app, then run `transformations get <app> models/schema/sources.yml` to find the exact input tables and columns consumed by its transformations; match `Tables[]`/`Fields[]` to them. The same pre-flight checks (encoding, delimiter, dates, empty rows) apply. See [`app-types.md`](app-types.md).