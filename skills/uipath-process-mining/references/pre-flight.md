# Pre-flight data checks + the minimal data mapping

Cheap local checks before any upload — each one saves a multi-minute ingest
round-trip.

## Inspect the file first

1. **Encoding / BOM** — non-UTF-8 (Windows-1252 / ISO-8859-1) must be declared via
   `ingestions create --encoding` (or the mapping's `SourceSettings.Encoding`), or
   the load mangles/fails.
2. **Delimiter + field regularity** — stream the file and assert every line splits
   into the same field count (catches embedded-delimiter / quoting issues). CSVs
   here are often `;`-delimited.
3. **Junk rows** — strip fully-empty trailing rows (`;;;;…`). Combined with a
   NotNull-error on the key column they cause the whole table to
   `Failed to load datasources`.
4. **Date format** — inspect token ranges to tell `dd-mm` from `mm-dd` (token1 max
   > 12 ⇒ day-first). Feeds `DateTimeFormatString`. Formats vary **per file** in
   the same dataset — check each.
5. **Cardinality** — distinct case ids and activities, to sanity-check the mapping.

## Minimal `mapping.json`

```json
{ "Tables": [ {
  "SourceName": "Event_log", "TargetName": "Event_log", "Source": "blob",
  "SourceSettings": { "Encoding": "utf-8", "FieldDelimiter": ";", "QuoteCharacter": "\"" },
  "IsMandatory": true, "ValidationType": "specificationOnly",
  "Fields": [
    { "DataType": "text",     "SourceName": "Incident ID",          "TargetName": "Case_ID",   "IsMandatory": true,  "ValidationType": "specificationOnly" },
    { "DataType": "text",     "SourceName": "IncidentActivity_Type","TargetName": "Activity",  "IsMandatory": true,  "ValidationType": "specificationOnly" },
    { "DataType": "datetime", "DataTypeSettings": { "DateTimeFormatString": "dd-mm-yyyy hh:mm:ss" },
      "SourceName": "DateStamp", "TargetName": "Event_end", "IsMandatory": true, "ValidationType": "specificationOnly" }
  ] } ] }
```

Rules:

- Core `uipath.custom` event-log targets: **`Case_ID`**, **`Activity`**,
  **`Event_end`** (datetime). Optional: `Event_start`, `User`.
- `DateTimeFormatString` is lowercase, non-strftime: `dd-mm-yyyy hh:mm:ss`
  (`.nnn` for milliseconds).
- **`IsNotNull` / `IsUnique` now default** per field (the CLI fills
  `{ Enabled: false, Severity: "warning" }` when omitted) — you no longer need to
  hand-write them on every field. `data-mapping update` applies the same defaults,
  so one mapping file works in both commands. Set them explicitly
  (`{ Enabled: true, Severity: "error" }`) on `Case_ID`/`Activity`/`Event_end` when
  you want a null there to fail the load rather than warn.
- **Map risky columns as `text` and parse in SQL** (dates with odd formats,
  decimal-comma numbers). Only `Event_end` must be a real `datetime`. Unmapped
  columns still load under their raw source names and are usable as attributes.
- **Multi-table apps**: add more `Tables[]` entries (Incidents, Interactions,
  Changes, …). All load; the template models only reference `Event_log`; your
  custom models `source('sources', '<Table>')` the rest and join on a shared key.

## Fixing the mapping after the app exists

A mapping mistake is **not** a reason to delete the app and start over. `apps
data-mapping` reads and replaces the mapping of an existing app:

```bash
uip pm apps data-mapping get <app> --destination ./mapping.json   # download the mapping + note Data.ETag
#   ...edit: fix the DateTimeFormatString, move a column to the right TargetName, map one more column...
uip pm apps data-mapping update <app> --file ./mapping.json --etag 'W/"639…"'   # --etag REQUIRED
uip pm files upload <app> ./data.csv --input-table Event_log      # ONLY if the source columns changed
uip pm ingestions create <app> --wait                             # the mapping applies to the NEXT ingestion
```

`get` without `--destination` inlines the mapping in the envelope as `Data.Mapping`
(useful with `--output-filter`, e.g.
`--output-filter "Mapping.Tables[0].Fields[].{Src:SourceName,Tgt:TargetName}"`).

Facts worth not re-learning:

- **A mapping change needs a re-ingest, not `transformations apply`.** `apply`
  re-runs SQL over already-parsed data; the mapping governs *parsing*. Editing the
  mapping and then running `apply` looks successful and changes nothing.
- **`dev` only.** The backend allows `PUT` on the dev stage; `published` is
  read-only, and the CLI restricts `update --stage` to `dev` up front.
- **`--etag` is REQUIRED on `update`, and it must be the one *your* `get` returned.**
  You edited the file locally, so only that ETag proves the edit was based on the
  version you read; the CLI deliberately does not fetch a fresh one before the `PUT`
  (which would make the `If-Match` pass no matter who wrote in between). A concurrent
  edit (someone in the UI's mapping editor) is therefore rejected `409
  UserError_ETagFileConflict` — recover by re-running `get` for the latest version
  **and its new ETag**, re-applying your change on top of that, then updating with the
  new `--etag`. Re-running the same `update` unchanged just fails again.
- `update` reports `Tables` (the mapped table names) and `IngestionNeeded: true`, not
  an ETag; to confirm a write landed, `get` again and diff — the `get` ETag is a
  **content checksum**, so re-pushing an identical mapping leaves it unchanged.
- **A table-less mapping is refused locally.** `{ "Tables": [] }` (or any file with
  no usable table) fails `No tables found in …` before any API call, so a bad file
  cannot overwrite and wipe the stored mapping.
- **Either key casing works** — PascalCase (`{"Tables":[…]}`, what the recipe above
  and `apps create --data-mapping` use) and the camelCase the API returns. Note
  `get --destination` writes the API's response **verbatim**, so the downloaded file
  is camelCase (`{"tables":[…]}`) while the envelope's `Data.Mapping` is PascalCased
  like every other envelope — same document, two casings. Either can be fed back to
  `update --file` or to `apps create --data-mapping` on another app.
- **A structurally invalid mapping fails safe**: `400
  UserError_DatapipelineBadRequest` / `INVALID_DATASOURCE_ARGUMENT`, and the stored
  mapping is left untouched.
- **An app id you can't see answers `403 UserError_NotAuthorized`, not `404`** —
  don't read that as a permissions problem on the mapping itself; check the id with
  `apps list`.
- Reading the `published` stage of an app that was **never published** still
  succeeds — you get the *template's* mapping with `ETag: W/"0"` and
  `UseInLoad: false`. Don't mistake it for the app's real mapping.

## Other app types

The mapping above targets the `uipath.custom` `Event_log`. For a **source-system
template** (`uipath.p2p.sap`, `uipath.im.servicenow`, …) the same `mapping.json`
shape applies, but you map your extract to the **template's expected input
tables** instead — create the app, then read `models/schema/sources.yml`
(`transformations get <app> models/schema/sources.yml`) to see the exact input
tables and columns the template's transformations consume, and match your
`Tables[]`/`Fields[]` to them. The pre-flight checks (encoding, delimiter, dates,
empty rows) are the same. See [`app-types.md`](app-types.md).
