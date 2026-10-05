# App types — the pipeline is template-agnostic

Everything in this skill — data mapping, `files upload`, `ingestions create`,
the `transformations` (ELT) layer, the data model + **add-table**, dev/published
stages, and `query` — works for **every** app type, not just `uipath.custom`.
What changes between templates is only **what the data mapping / extract must
contain**. The machinery around it is identical.

## The two families

| Family | Examples | What you feed it |
|--------|----------|------------------|
| **Custom event log** | `uipath.custom` ("Event log") | ONE flat log you build: Case_ID, Activity, Event_end (+ attributes). You construct the event log. |
| **Source-system templates** | `uipath.p2p.sap`, `uipath.o2c.oraclecloud`, `uipath.im.servicenow`, `uipath.im.salesforce`, `uipath.ap.sap`, `uipath.q2c.netsuite`, … (P2P / O2C / IM / AP / Q2C / … across SAP, Oracle EBS/JDE/Cloud, NetSuite, ServiceNow, Salesforce, Coupa, Ariba) | The source system's **full multi-table extract**, mapped to the template's expected input tables. The template already contains the extraction + event-log construction as dbt models. |

Discover the full list per tenant:

```bash
uip pm app-types list --output-filter "[].{Key:AppTypeKey,Version:Version,Name:DefaultName}"
```

## Same model shape everywhere

Every template's `model` has the same top-level shape — `Processes`, `Metrics`,
**`Tables`**, `Automations`, `DefaultObject` — only the contents differ. The
semantic entities (`model.Tables[]`) are template-specific: `uipath.custom` ships
`Cases`/`Event_log`/`Tags`/`Due_dates`; `uipath.im.servicenow` ships
`Incidents`/`Tags`/`Due_dates`/`__Incident_process_Events`; a P2P template ships
its purchase-order entities. Inspect a template's model + metrics with:

```bash
uip pm app-types get <key> <version>
```

Because the shape is uniform, **the data-model rules generalize**: `query info`
exposes whatever is in `Tables[]`, and you expose a custom analytical table on
**any** app type by adding a `Tables[]` entry (see [`data-model.md`](data-model.md)) —
add-table is not custom-only.

## Choosing and targeting a template

1. **Pick the template.** A single denormalized event log ⇒ `uipath.custom`.
   Otherwise pick the `<process>.<system>` template that matches your source
   system AND process (e.g. Purchase-to-Pay on SAP ⇒ `uipath.p2p.sap`). Use a
   source template only when you actually have that system's expected multi-table
   extract — not a single log you happened to export from it.
2. **Learn the expected input.** For a source template, the expected **input
   tables** (what your extract must provide) are defined by the template's
   transformation layer, not the `model` object. Create the app, then read the
   generated sources with `transformations list`/`get` (look at
   `models/schema/sources.yml`), or follow the template's extractor docs. Build
   the `--data-mapping` to match those input tables + fields.
3. **Everything else is identical.** `files upload --input-table <name>` per
   table, `ingestions create --wait`, fix transforms with `apply` (not re-ingest),
   extend with custom models + add-table, develop on `dev` (subset) and publish
   the full dataset, and `query` with the `--group-by/--metric` sugar.

## Sample data — a demo app without your own data

Some templates ship sample data — the UI's "Use sample data" option when creating
an app. Use it when the user wants a demo / sandbox app or asks for sample data;
do not write a synthetic CSV instead.

1. **Find a template that ships sample data.** `SampleDataAvailable` is per
   template version:

   ```bash
   uip pm app-types list --output-filter "[?SampleDataAvailable].{Key:AppTypeKey,Version:Version,Name:DefaultName}"
   ```

   Empty result ⇒ no template on this tenant ships sample data. Tell the user and
   fall back to their own data (mapping → upload → ingest).
2. **Create the app without `--data-mapping`.** The sample files fit the
   template's default mapping; a custom mapping can make them fail to parse.

   ```bash
   uip pm apps create "<APP_NAME>" --type <APP_TYPE_KEY> --output json
   ```

3. **Ingest the sample data.** No `files upload` first — the backend copies the
   template's sample files into the app.

   ```bash
   uip pm ingestions create <APP_ID> --sample-data --wait --output json
   ```

   The ingestion runs the template's transformations like any other run, so the
   app is queryable when `--wait` returns `Success`.

| Outcome | Meaning | Do |
|---------|---------|-----|
| `Failure`, *"has no sample data"* | Template ships none (`SampleDataAvailable: false`), or the app was imported | Pick a template from step 1, or use the user's own data |
| non-zero exit, *"cannot be used with"* | `--sample-data` combined with `--file-format` / `--field-delimiter` / `--quote-character` / `--encoding` | Drop the file-format flags — sample data needs none |
| *"unknown option '--sample-data'"* | Installed `uip` predates the flag | `npm install -g @uipath/cli@latest`, then retry; do not call the REST API by hand |
| `--wait` ends `FAILED` | Loader/transform error, printed by `--wait` | Treat as any failed ingestion — read the printed error; `ingestions logs` for more |

After loading, everything else is unchanged: transform, extend with add-table,
publish, query. To swap in real data later, set the mapping with `apps
data-mapping update`, `files upload`, and `ingestions create` without
`--sample-data`.

## What is template-specific

- **The `Cases.sql` optional-column gotcha** ([`transformations.md`](transformations.md))
  is a **`uipath.custom`** issue. Source templates ship their own (already-correct)
  transformations — you don't patch their event-log construction; you feed the
  expected extract and, if needed, **extend** with extra models + data-model tables.
- The set of shipped `Metrics` and semantic entities differs per template — always
  `query info` (on a built app) or `app-types get` (on the template) to see what's
  available before writing query bodies.
