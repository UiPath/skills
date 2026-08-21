# Classification Details — uipath-process-mining

**Classification: Strong**

---

## What the Skill Teaches

UiPath Process Mining via `uip pm` covering the full pipeline from raw CSV to queryable process app: template selection, data mapping, upload, ingest, dbt transformation layer, publishing, querying, and data model editing.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Template selection** | **Yes — LOOKUP/REFERENCE-TABLE** | Rule 2: map data shape (single log → `uipath.custom`; multi-table extract → `<process>.<system>`) to template key |
| 2 | **CSV pre-flight checks** | **Yes — VALIDATE/CHECK** | `references/pre-flight.md` specifies encoding/delimiter/date-format/empty-row checks before upload |
| 3 | **Data mapping creation** | **Yes — FORMAT-CONVERT** | Produces `mapping.json` from CSV column names; minimal recipe in `references/pre-flight.md` |
| 4 | **App creation + upload + ingest pipeline** | **Yes — TRANSFORM-PIPELINE** | `app-types list` → `apps create` → `files upload` → `ingestions create --wait` |
| 5 | dbt SQL authoring (Cases.sql patch, custom tables) | No | Writing/fixing SQL requires judgment about schema and business logic |
| 6 | **Data model registration (add-table)** | **Yes — TRANSFORM-PIPELINE** | Rule 1: `add-table` with DataModelDto JSON → `ingestions create`; shape and FK rules fully specified |
| 7 | **ETag get-modify-put for mapping/SQL updates** | **Yes — VALIDATE/CHECK** | Rule 5 and Anti-pattern: get with ETag → edit → update with ETag; 409 → re-get + re-apply |
| 8 | **Querying (aggregate + metrics)** | **Yes — AGGREGATE/STATS + EXTRACT** | `query run` with `--group-by/--metric` sugar; field-id discovery via `query info` |

---

## Codifiable Procedures (not yet scripted)

### 1. Template Selection — LOOKUP/REFERENCE-TABLE

**Source:** `skills/uipath-process-mining/SKILL.md` §Critical Rules, Rule 2

**What it does:** Maps the shape of the input data to the correct `uip pm` template key. A single denormalized event log (Case, Activity, Timestamp + attributes) → `uipath.custom`; a multi-table extract from a specific source system and process → `<process>.<system>` (e.g., `uipath.p2p.sap`). Line 38: `"A single denormalized log (Case, Activity, Timestamp [+ attributes]) ⇒ uipath.custom ('Event log'). Otherwise pick the <process>.<system> template matching your source system AND process... but only when you actually have that system's full multi-table extract."` Discovery: `uip pm app-types list`, inspection: `uip pm app-types get`.

**Why it's mechanical:** The decision rule is a binary: single-log shape → custom; multi-table + known system → specific template. No judgment on process design.

**Turn savings:** Agents currently read Rule 2 and the app-types list to resolve template on every task; a lookup script takes data shape + system as inputs and returns the template key in one call.

---

### 2. CSV → Queryable App Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-process-mining/SKILL.md` §App lifecycle, §Quick Start

**What it does:** Executes the fixed end-to-end pipeline: select template → create app with mapping → upload CSV → ingest (with `--wait`) → patch `Cases.sql` if `uipath.custom` → apply → query. Line 32: `"An app moves through: create (from a template + data mapping) → load (upload + ingest) → transform on the dev stage (the ELT/dbt layer) → publish to the published stage → query / build dashboards."` Each step has a specific `uip pm` command; `--wait` prevents polling loops.

**Why it's mechanical:** The command sequence is fully specified; branch points (re-ingest vs. re-apply) are rule-governed (Rule 4: transform-only failure → apply; mapping change → ingest).

**Turn savings:** Agents currently execute the pipeline step-by-step across 4–8 turns; an orchestrator script runs the full sequence and pauses only when SQL authoring is needed.

---

### 3. ETag Get-Modify-Put for Mapping and SQL — VALIDATE/CHECK

**Source:** `skills/uipath-process-mining/SKILL.md` §Critical Rules, Rules 4–5

**What it does:** For mapping updates: `apps data-mapping get <app> --destination ./mapping.json` → edit `mapping.json` → `apps data-mapping update <app> --file ./mapping.json --etag '<etag>'`. For SQL updates: `transformations get <path> --output json` → edit → `transformations update <path> --file <edited> --etag '<etag>'`. A 409 `UserError_ETagFileConflict` means re-get (new document + new ETag) then re-apply edits and retry. Line 44: `"--etag is required — pass the Data.ETag that your get returned, which is what proves the edit was based on the version you read; a lost race is refused 409 UserError_ETagFileConflict (re-get for the new version AND ETag, re-apply, retry)."` 

**Why it's mechanical:** The get → edit → put-with-etag → retry-on-409 loop is fully specified; the anti-pattern (re-getting ETag without re-getting document) is explicitly prohibited.

**Turn savings:** Agents re-read this loop on every update; a reusable update function with built-in ETag handling and 409 retry collapses 3–4 turns to 1.

---

### 4. Aggregate Query — AGGREGATE/STATS

**Source:** `skills/uipath-process-mining/SKILL.md` §Critical Rules, Rule 7

**What it does:** Runs `query run <app> --group-by <col> --metric <col>:<fn>` where `fn` ∈ `average|count|sum|min|max`. For raw query bodies, fetches hashed field IDs from `query info` first, then constructs the AST. Line 48: `"Query field ids come from query info, not column names. query run/percentile bodies take the hashed F__<Table>__<Col>__<hash> ids. Prefer the sugar: query run <app> --group-by <col> --metric <col>:<fn> resolves human names for you."` Inputs: app id + column names + aggregation function; output: grouped metric result.

**Why it's mechanical:** The field-id resolution and aggregation function enum are fully specified; the sugar syntax handles name→id resolution automatically.

**Turn savings:** Agents currently discover field IDs and construct query bodies across 2–3 turns; a query helper takes human column names and emits results in one call.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Six of eight teaching areas are codifiable: template selection (LOOKUP/REFERENCE-TABLE), CSV pre-flight (VALIDATE/CHECK), data mapping (FORMAT-CONVERT), the full ELT pipeline (TRANSFORM-PIPELINE), data model registration (TRANSFORM-PIPELINE), ETag concurrency (VALIDATE/CHECK), and querying (AGGREGATE/STATS + EXTRACT). The only non-codifiable area is dbt SQL authoring, which requires domain knowledge about the data and business process. The pipeline and validation mechanics dominate the skill's content.

**Why not None:** Four independent codifiable procedures exist across template selection, the ELT pipeline, ETag concurrency control, and aggregate querying.

**Evidence locations:**
- LOOKUP/REFERENCE-TABLE template: `SKILL.md` Rule 2 (line 38)
- TRANSFORM-PIPELINE pipeline: `SKILL.md` §App lifecycle (line 32)
- VALIDATE/CHECK ETag: `SKILL.md` Rule 5 (line 44)
- AGGREGATE/STATS query: `SKILL.md` Rule 7 (line 48)
- TRANSFORM-PIPELINE add-table: `SKILL.md` Rule 1 (line 36)
