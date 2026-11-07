# Querying Schema Tables

Apps, agents, and processes read and write a Schema resource's tables with one SQL statement per request to Data Service. The statement names tables by their logical names (`Customer`), never their physical names.

Requires the `solution-entity-sql` feature on the tenant; with it off, the endpoint returns 404.

## Request

```http
POST https://<cloud-host>/<org>/<tenant>/dataservice_/api/v3/QueryExecutor
Authorization: Bearer <token>
Content-Type: application/json
X-UiPath-FolderKey: <folder GUID>      # folder-scoped schema only; or X-UiPath-FolderPath: Finance/Invoices

{
  "sql": "SELECT Id, Email FROM Customer WHERE IsActive = @active ORDER BY Id",
  "parameters": { "active": true }
}
```

- **Scope:** with a folder header the statement sees that folder's tables; without one, the tenant's tables. A folder header that does not resolve is a 400, never a fall-back to the tenant.
- **Parameters:** every `@name` in the SQL needs a value, by name with or without `@`. Values are a string, number, boolean, or null; send dates as ISO strings. Strings bind as `nvarchar`.

## Response

```json
{
  "columns": [ { "name": "Id", "type": "bigint" }, { "name": "Email", "type": "nvarchar" } ],
  "rows": [ { "Id": 1, "Email": "first@example.com" } ],
  "truncated": false,
  "rowsAffected": null
}
```

- Rows are keyed by column name, so every result column needs a unique name: alias expressions (`COUNT(*) AS Total`).
- A `SELECT` returns at most 1,000 rows; `truncated` is true when there were more. Page with `ORDER BY … OFFSET … FETCH`.
- `INSERT`/`UPDATE`/`DELETE` return `rowsAffected`, plus rows when the statement has an `OUTPUT` clause.

## Permissions

| Scope | Read (any table the statement reads) | Insert | Update | Delete |
|---|---|---|---|---|
| Folder | `EntityRecords.View` | `EntityRecords.Create` | `EntityRecords.Edit` | `EntityRecords.Delete` |
| Tenant | `ReadData` | `CreateData` | `UpdateData` | `DeleteData` |

Every table in joins, subqueries, and `INSERT … SELECT` needs read; a statement naming no table still needs read. Writes also need a token scope that allows writing data (`DataService.Data.Write` or `DataFabric.Data.Write`, or the user-access / default scopes); a read scope alone runs only `SELECT`.

## Allowed SQL

One statement: `SELECT`, `INSERT`, `UPDATE`, or `DELETE`, with joins, subqueries, `APPLY`, CTEs (`WITH`), `GROUP BY`/`HAVING`, `ORDER BY`/`OFFSET`, `UNION`, `CASE`, `CAST`, and `OUTPUT` (without `INTO`).

Functions allowed: dates (`GETDATE`, `GETUTCDATE`, `SYSDATETIME`, `SYSUTCDATETIME`, `SYSDATETIMEOFFSET`, `DATEADD`, `DATEDIFF`, `DATEDIFF_BIG`, `DATEPART`, `DATENAME`, `DATETRUNC`, `EOMONTH`, `YEAR`, `MONTH`, `DAY`, the `…FROMPARTS` family, `SWITCHOFFSET`, `TODATETIMEOFFSET`, `ISDATE`), ids (`NEWID`, `NEWSEQUENTIALID`), strings (`LEN`, `DATALENGTH`, `UPPER`, `LOWER`, `LTRIM`, `RTRIM`, `TRIM`, `SUBSTRING`, `REPLACE`, `TRANSLATE`, `CONCAT`, `CONCAT_WS`, `CHARINDEX`, `PATINDEX`, `REVERSE`, `STUFF`, `REPLICATE`, `SPACE`, `STR`, `FORMAT`, `ASCII`, `CHAR`, `NCHAR`, `UNICODE`), numbers (`ABS`, `CEILING`, `FLOOR`, `ROUND`, `POWER`, `SQRT`, `SQUARE`, `SIGN`, `EXP`, `LOG`, `LOG10`, `PI`), and `ISNULL`, `ISNUMERIC`, `CHOOSE`, `GREATEST`, `LEAST`, `ISJSON`, `JSON_VALUE`, `JSON_QUERY`, `HASHBYTES`, `CHECKSUM`, plus the aggregates.

Refused (400, with the reason in `problems`): more than one statement; two-, three-, or four-part names (`dbo.Customer`, `sys.tables`); `#temp` tables and table variables; `SELECT INTO`, `OUTPUT INTO`, `EXEC`; table and query hints, `OPTION`; `FOR XML`/`FOR JSON`; `OPENROWSET`, `OPENQUERY`, table-valued functions; `@@` variables and functions outside the list above.

A table name the folder or tenant does not have is a 403 naming it.

## Limits

| Limit | Value |
|---|---|
| SQL length | 64 KB, 10,000 tokens, parentheses 32 deep |
| Rows returned | 1,000 (`truncated` when cut) |
| Result size | 16 MB |
| Statement time | 30 s (then 400 "did not finish in time") |
| Busy service | 429: send again shortly |

## Errors

| Status | Meaning |
|---|---|
| 400 | The SQL does not parse or breaks a rule, a parameter is missing or extra, SQL Server refused it (constraint, type), it timed out, or it was a deadlock victim ("changed nothing; send it again"). `problems` lists each reason; SQL Server's text comes back with logical table names. |
| 403 | A permission or write scope is missing, or a table is not the folder's or tenant's. |
| 404 | The feature is off for the tenant. |
| 429 | Too many queries being parsed at once; retry. |

Each statement runs in its own transaction: a write that fails changes nothing.
