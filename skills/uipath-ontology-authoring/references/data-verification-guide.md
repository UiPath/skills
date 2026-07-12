# Data verification guide — no literal enters the package unverified

Every value domain, code, format, scale, count, and grain claim is checked
against the **actual data** before it is written into an annotation or policy
line. A single wrong literal (e.g. a truncated `'District Special Education
Consortia Sch'`) produces SQL that filters on wrong values and costs more than
ten missing annotations.

## Sources, in order of preference

1. **The Data Fabric entity records themselves** — query via the `uip df`
   record commands (discover the exact subcommand/flags on the host with
   `uip df --help` / `uip df records --help`; always pass `--folder-key`).
2. **The source database**, when reachable (e.g. the SQLite/SQL Server the
   entities were loaded from) — fastest for aggregates; SQL recipes below.
3. **The dataset's own documentation** (description files shipped with the
   data, e.g. `database_description/*.csv`) — legitimate schema knowledge for
   cryptic-column meanings and code lists.
4. **The author interview** — for domain semantics only (what a code *means*
   when no documentation exists, business rules, relationship names).

**Never** derive a fact from example answers / gold queries / expected results.
If a fact can only be justified by "that's what the expected answer does", it is
leakage — leave it out.

## Recipes per fact type (SQL form; translate to record queries as needed)

```sql
-- 2. VALUE DOMAINS: exact, complete, case-sensitive. NEVER truncate values.
SELECT DISTINCT status FROM loan;
-- keep the domain only if cardinality is small (≤ ~20); otherwise annotate the
-- format instead of the list

-- 4a. SCALE: fraction vs percent
SELECT MAX("Percent (%) Eligible Free (K-12)") FROM frpm;   -- 1.0 → stored fraction

-- 1. GRAIN: rows per business parent
SELECT COUNT(*), COUNT(DISTINCT team_api_id) FROM Team_Attributes;  -- 1458/288 → time series

-- 4b. FORMAT: zero-padding, date shapes
SELECT CharterNum FROM schools WHERE CharterNum IS NOT NULL LIMIT 5;  -- '0728' → zero-padded
SELECT birthday FROM Player LIMIT 2;                                   -- 'YYYY-MM-DD HH:MM:SS'

-- CO-OCCURRENCE claims (before writing "X implies Y"): expect 0
SELECT COUNT(*) FROM frpm
 WHERE "Charter Funding Type" IS NOT NULL AND "Charter School (Y/N)" != 1;

-- NULL RATES (drives the IS-NOT-NULL-for-ascending rule)
SELECT COUNT(*) FROM satscores WHERE AvgScrRead IS NULL;   -- 596 → annotate

-- UNIQUENESS claims (before "lookups return one row")
SELECT team_short_name, COUNT(*) FROM Team
 GROUP BY team_short_name HAVING COUNT(*) > 1 LIMIT 5;      -- duplicates → say so

-- 3. CODE LISTS with names, when the data pairs them
SELECT DISTINCT SOC, SOCType FROM schools ORDER BY CAST(SOC AS INT);

-- 4c. SIGN / RANGE conventions
SELECT MIN(Longitude), MAX(Longitude) FROM schools;          -- all negative → annotate
```

Fact types 5 (cryptic columns) and 7 (domain semantics) come from documentation
and the interview respectively — but any *checkable* part (the value list a code
column actually contains, the fill-rate of "rare" slots) still gets a data check:

```sql
-- slot fill-rates (before "slot 1 is the primary administrator")
SELECT COUNT(AdmFName1), COUNT(AdmFName2) FROM schools;      -- 11700 vs 431
```

## Choice sets (Data Fabric native)

Stored values are integer NumberIds. Pull the real label↔NumberId map — never
guess and never bind by label:

```bash
uip df choice-sets list-values <choice-set-id> --folder-key <key> --output json
```

Record the map in the property's `rdfs:comment` ("NumberId. 1=Pending,
2=Shipped, 3=Delivered").

## Recording rules

- Copy literals **exactly** — case, spacing, diacritics, full length. Beware any
  tooling that truncates sampled values before you read them.
- Note counts approximately ("~600 rows NULL", "~5 rows per team") — precision
  isn't the point; the consequence is.
- Every claim in an annotation should be reproducible by rerunning its recipe.
