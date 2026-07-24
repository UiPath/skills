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
  hand-write them on every field.
- **Map risky columns as `text` and parse in SQL** (dates with odd formats,
  decimal-comma numbers). Only `Event_end` must be a real `datetime`. Unmapped
  columns still load under their raw source names and are usable as attributes.
- **Multi-table apps**: add more `Tables[]` entries (Incidents, Interactions,
  Changes, …). All load; the template models only reference `Event_log`; your
  custom models `source('sources', '<Table>')` the rest and join on a shared key.

## Other app types

The mapping above targets the `uipath.custom` `Event_log`. For a **source-system
template** (`uipath.p2p.sap`, `uipath.im.servicenow`, …) the same `mapping.json`
shape applies, but you map your extract to the **template's expected input
tables** instead — create the app, then read `models/schema/sources.yml`
(`transformations get <app> models/schema/sources.yml`) to see the exact input
tables and columns the template's transformations consume, and match your
`Tables[]`/`Fields[]` to them. The pre-flight checks (encoding, delimiter, dates,
empty rows) are the same. See [`app-types.md`](app-types.md).
