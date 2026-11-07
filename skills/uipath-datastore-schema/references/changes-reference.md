# Schema Changes Reference

What Data Service accepts inside `spec.changesets`. Property names and change names match without regard to case; give each property once. An unknown property anywhere is refused with `{path} has unknown property '{x}'.`

## Contents

- [Changeset](#changeset)
- [Preconditions](#preconditions)
- [Changes](#changes)
- [Columns](#columns)
- [Column types](#column-types)
- [Values](#values)
- [where and sqlCheck SQL](#where-and-sqlcheck-sql)
- [Foreign keys](#foreign-keys)
- [Names and limits](#names-and-limits)
- [Full example](#full-example)

## Changeset

```json
{ "changeset": 2, "preConditions": [ ... ], "changes": [ { "<change>": { ... } } ] }
```

| Property | Rule |
|---|---|
| `changeset` | Required. A JSON integer from 1 to 999999999 (not `"1"`, not `1.0`). Unique in the resource. Runs in ascending number order; gaps are allowed. A new number below the highest installed one is refused. |
| `changes` | Required, at least one item. Each item is an object with exactly one property, the change name. |
| `preConditions` | Optional. See [Preconditions](#preconditions). |

Anything else (`id`, `author`, `name`, `comment`, `labels`, `context`) is refused. `upSql` / `downSql` are refused with `'upSql' cannot be used in a Schema whose changesets use changes.`

## Preconditions

A list of single-property objects: at most one `onFail`, and at least one `sqlCheck`.

```json
"preConditions": [
  { "onFail": "MARK_RAN" },
  { "sqlCheck": { "expectedResult": "0", "sql": "SELECT COUNT(*) FROM Region" } }
]
```

- `onFail`: `HALT` (default) fails the deploy; `MARK_RAN` skips the changeset's changes and records it as installed, never to run again.
- `sqlCheck.sql`: one `SELECT` of one value from one of this schema's tables ([rules](#where-and-sqlcheck-sql)).
- `sqlCheck.expectedResult`: a string or a JSON integer. It is compared as text, case-sensitively, with the first column of the first row (no row or NULL is `""`; a bit is `1`/`0`; a date with no time also matches `yyyy-MM-dd`). Every check must hold.
- Other Liquibase preconditions (`tableExists`, `columnExists`, `and`, `or`, `not`, `onError`, `changeSetExecuted`, `dbms`) are not supported.

Typical use: seed rows only into an empty table (`MARK_RAN` + `SELECT COUNT(*) … = "0"`).

## Changes

Supported: `createTable`, `addColumn`, `dropColumn`, `modifyDataType`, `createIndex`, `dropIndex`, `addForeignKeyConstraint`, `dropForeignKeyConstraint`, `insert`, `update`, `delete`. `setColumnRemarks` is accepted and ignored. Everything else is refused, including `sql`, `dropTable`, `renameTable`, `renameColumn`, `addPrimaryKey`, `addUniqueConstraint`, `addNotNullConstraint`, `addDefaultValue`, `createView`, `loadData` (write rows as `insert`).

Every change except `createTable` must name a table this schema created earlier: in an earlier changeset, or earlier in the same changeset.

| Change | Attributes (required in **bold**) | Notes |
|---|---|---|
| `createTable` | **`tableName`**, **`columns`**, `remarks` | Columns per [Columns](#columns). Several `primaryKey` columns form one composite key, in column order. A table may have no primary key. `schemaName`, `catalogName`, `tablespace`, `ifNotExists` are refused. |
| `addColumn` | **`tableName`**, **`columns`** | No `primaryKey` column. A `nullable: false` column needs a non-null default. |
| `dropColumn` | **`tableName`**, **`columnName`** | One column. Its own default and unique constraints are dropped with it. Refused while a foreign key uses it. |
| `modifyDataType` | **`tableName`**, **`columnName`**, **`newDataType`** | Keeps the column's nullability, default, unique constraint, and the primary key. Other indexes on the column are not dropped: drop and recreate them around the change. Refused while a foreign key uses it. |
| `createIndex` | **`tableName`**, **`indexName`**, **`columns`**, `unique` (default false) | `columns`: `[{ "column": { "name": "C" } }]`, at most 16, no repeats. No `descending`, `clustered`, `where`. An index on a `(MAX)` column fails at deploy. |
| `dropIndex` | **`tableName`**, **`indexName`** | `tableName` is required. |
| `addForeignKeyConstraint` | **`baseTableName`**, **`baseColumnNames`**, **`constraintName`**, **`referencedTableName`**, **`referencedColumnNames`**, `onDelete`, `onUpdate`, `validate` (default true) | See [Foreign keys](#foreign-keys). |
| `dropForeignKeyConstraint` | **`baseTableName`**, **`constraintName`** | |
| `insert` | **`tableName`**, **`columns`** | Each column: `name` and exactly one value field ([Values](#values)). |
| `update` | **`tableName`**, **`columns`**, `where` | No `where` updates every row. |
| `delete` | **`tableName`**, `where` | No `where` deletes every row. |

## Columns

Used by `createTable` and `addColumn`. Always wrapped: `{ "column": { ... } }`.

| Property | Rule |
|---|---|
| `name` | Required. See [Names](#names-and-limits). |
| `type` | Required. See [Column types](#column-types). |
| `constraints` | Optional object: `primaryKey`, `nullable`, `unique`, `foreignKeyName`, `referencedTableName`, `referencedColumnNames`, `deleteCascade`. Nothing else (`primaryKeyName`, `checkConstraint`, `references` are refused). |
| `defaultValue`, `defaultValueNumeric`, `defaultValueBoolean`, `defaultValueDate` | At most one. JSON `null` means `DEFAULT NULL`. |
| `remarks` | Ignored. |

- `nullable` defaults to true, except for a `primaryKey` column, which is never nullable.
- A `primaryKey` or `unique` column cannot have a `(MAX)` type (or `TEXT`, `CLOB`, `BLOB`, …).
- A column foreign key needs all three of `foreignKeyName`, `referencedTableName`, `referencedColumnNames`, references exactly one column, and may add `"deleteCascade": true`. Use `addForeignKeyConstraint` for several columns, `onUpdate`, or `validate`.
- Not supported: `autoIncrement` / identity, `startWith`, `incrementBy`, `defaultValueComputed`, `defaultValueSequenceNext`, computed columns, `afterColumn`/`position`. For generated keys, use `UNIQUEIDENTIFIER` keys the app supplies, or a key the app computes.

## Column types

Case-insensitive; written to SQL Server in canonical form. Anything else (including `NOT NULL`, `COLLATE`, user types) is refused: `'{type}' is not a supported column type.`

| Type | Parameters |
|---|---|
| `BIGINT`, `INT`, `SMALLINT`, `TINYINT`, `BIT`, `MONEY`, `SMALLMONEY`, `REAL`, `DATE`, `DATETIME`, `SMALLDATETIME`, `UNIQUEIDENTIFIER` | none (`INT(4)` is refused) |
| `DECIMAL`, `NUMERIC` | optional `(p)` or `(p,s)`: 1 ≤ p ≤ 38, s ≤ p |
| `FLOAT` | optional `(n)`: 1–53 |
| `TIME`, `DATETIME2`, `DATETIMEOFFSET` | optional `(n)`: 0–7 |
| `CHAR`, `BINARY` | optional `(n)`: 1–8000 |
| `VARCHAR`, `VARBINARY` | optional `(n)`: 1–8000, or `(MAX)` |
| `NCHAR` | optional `(n)`: 1–4000 |
| `NVARCHAR` | optional `(n)`: 1–4000, or `(MAX)` |

Liquibase aliases: `BOOLEAN`→`BIT`, `INTEGER`→`INT`, `DOUBLE`→`FLOAT`, `CURRENCY`→`MONEY`, `UUID`→`UNIQUEIDENTIFIER`, `TIMESTAMP[(n)]`→`DATETIME2[(n)]`, `CLOB`/`NCLOB`/`TEXT`/`NTEXT`→`NVARCHAR(MAX)`, `BLOB`/`IMAGE`→`VARBINARY(MAX)` (no parameters on these). Always give a length for `NVARCHAR`/`VARCHAR`/`CHAR`: without one SQL Server makes it 1 character. Not supported: `XML`, `SQL_VARIANT`, `GEOGRAPHY`, `GEOMETRY`, `HIERARCHYID`, `ROWVERSION`, `JSON`.

## Values

`insert` / `update` columns take exactly one of `value`, `valueNumeric`, `valueBoolean`, `valueDate`; defaults use the `defaultValue…` forms with the same rules. JSON `null` is SQL `NULL`. Not supported: `valueComputed`, `valueBlobFile`, `valueClobFile`, `valueSequenceNext`.

| Field | Accepts |
|---|---|
| `value` | text (a JSON integer or boolean is taken as text) |
| `valueNumeric` | a JSON integer, or a numeric **string** such as `"12.5"`, `"-0.75"`, `"1.5E1"` (at most 38 digits). A JSON number with a fraction or exponent is refused: `12.5 cannot be kept exactly in SQL Server. Write it as a string`. |
| `valueBoolean` | `true` / `false` (or the strings `"true"` / `"false"`); not `1` / `0` |
| `valueDate` | an ISO 8601 string: `2026-11-03`, `2026-11-03T10:15:00`, `2026-11-03T10:15:00.123Z`, `2026-11-03T10:15:00+02:00`. No functions (`NOW()`), and an offset needs a time. |

## where and sqlCheck SQL

At most 4000 characters, 32 levels of parentheses, 200 operators. Validated, then regenerated from its parse tree.

**`where`** (update, delete) is a condition using only: comparisons `= <> != < > <= >=`, `AND`/`OR`/`NOT`, parentheses, `IS [NOT] NULL`, `[NOT] BETWEEN`, `[NOT] LIKE`, `IN (` literal list `)`, one-part column names (brackets allowed), and number, string (`'…'`, `N'…'`) and `NULL` literals. Not allowed: functions, arithmetic, `@variables`, subqueries, `EXISTS`, `CASE`, `CAST`, `alias.column`.

```json
"where": "Status IN ('Open', 'New') AND Amount >= 1000.00 AND RegionId IS NOT NULL"
```

**`sqlCheck.sql`** is `SELECT <one value> FROM <one of this schema's tables> [WHERE <condition as above>]`. The value is one column, one literal, or one aggregate (`COUNT`, `COUNT_BIG`, `SUM`, `MIN`, `MAX`, `AVG`, `COUNT(DISTINCT x)`). No joins, `SELECT *`, `TOP`, `GROUP BY`, `ORDER BY`, `UNION`, CTEs, hints, or two-part names (`sys.tables` is refused). Avoid reserved words as table names (`Order`, `User`): they fail to parse here.

## Foreign keys

- Both tables must belong to the same Schema resource; a key to another resource's table, or to a tenant schema's table from a folder schema, is refused.
- `baseColumnNames` / `referencedColumnNames`: comma-separated, same count, at most 16 each. Referenced columns must be a primary key or unique in SQL Server.
- `onDelete` / `onUpdate`: `CASCADE`, `SET NULL`, `SET DEFAULT`, `NO ACTION`, `RESTRICT` (installed as `NO ACTION`).
- `validate: false` adds the key without checking existing rows.
- Refused: `baseTableCatalogName`, `baseTableSchemaName`, `referencedTableCatalogName`, `referencedTableSchemaName` (when set), `deferrable: true`, `initiallyDeferred: true`.
- A key named `x` cannot be on a table named `FK_x`.
- SQL Server refuses some combinations at deploy, such as two cascade paths to one table.

**Retyping or dropping a key column.** `dropColumn` and `modifyDataType` are refused while a foreign key uses the column, on either side. Both sides of a key must keep one type, so write one changeset:

```json
{ "changeset": 7, "changes": [
  { "dropForeignKeyConstraint": { "baseTableName": "SalesOrder", "constraintName": "SalesOrder_Customer" } },
  { "modifyDataType": { "tableName": "Customer", "columnName": "Id", "newDataType": "BIGINT" } },
  { "modifyDataType": { "tableName": "SalesOrder", "columnName": "CustomerId", "newDataType": "BIGINT" } },
  { "addForeignKeyConstraint": { "baseTableName": "SalesOrder", "baseColumnNames": "CustomerId", "constraintName": "SalesOrder_Customer",
    "referencedTableName": "Customer", "referencedColumnNames": "Id" } }
] }
```

## Names and limits

- Table, column, index, and key names: letters, digits, and underscores, starting with a letter or underscore. Maximum length: table 95, column 92, foreign key 92, index 128.
- A table cannot be named `PK` or start with `DF_` or `UQ_`.
- Names keep their case, but two tables or two columns differing only in case are the same name.
- Table names are unique per folder (folder scope) or per tenant (tenant scope) across all Schema resources: two resources cannot create the same table in the same place.
- At most 16 columns in an index or foreign key; numeric literals at most 38 digits; changeset numbers up to 999999999.

## Full example

```json
"changesets": [
  { "changeset": 1, "changes": [
    { "createTable": { "tableName": "Customer", "columns": [
      { "column": { "name": "Id", "type": "BIGINT", "constraints": { "primaryKey": true } } },
      { "column": { "name": "Email", "type": "NVARCHAR(320)", "constraints": { "nullable": false, "unique": true } } },
      { "column": { "name": "IsActive", "type": "BOOLEAN", "defaultValueBoolean": true, "constraints": { "nullable": false } } }
    ] } },
    { "createTable": { "tableName": "SalesOrder", "columns": [
      { "column": { "name": "Id", "type": "BIGINT", "constraints": { "primaryKey": true } } },
      { "column": { "name": "CustomerId", "type": "BIGINT", "constraints": { "nullable": false,
          "foreignKeyName": "SalesOrder_Customer", "referencedTableName": "Customer", "referencedColumnNames": "Id", "deleteCascade": true } } },
      { "column": { "name": "Amount", "type": "DECIMAL(18,2)", "defaultValueNumeric": "0", "constraints": { "nullable": false } } },
      { "column": { "name": "Status", "type": "NVARCHAR(20)", "defaultValue": "Open" } }
    ] } }
  ] },
  { "changeset": 2, "changes": [
    { "addColumn": { "tableName": "SalesOrder", "columns": [
      { "column": { "name": "Priority", "type": "INT", "defaultValueNumeric": 0, "constraints": { "nullable": false } } }
    ] } },
    { "createIndex": { "tableName": "SalesOrder", "indexName": "IX_SalesOrder_Status", "columns": [ { "column": { "name": "Status" } } ] } }
  ] },
  { "changeset": 3,
    "preConditions": [ { "onFail": "MARK_RAN" }, { "sqlCheck": { "expectedResult": "0", "sql": "SELECT COUNT(*) FROM Customer" } } ],
    "changes": [
      { "insert": { "tableName": "Customer", "columns": [
        { "column": { "name": "Id", "valueNumeric": 1 } },
        { "column": { "name": "Email", "value": "first@example.com" } }
      ] } }
  ] },
  { "changeset": 4, "changes": [
    { "update": { "tableName": "SalesOrder", "columns": [ { "column": { "name": "Priority", "valueNumeric": 1 } } ],
      "where": "Status = 'Open' AND Amount >= 1000.00" } },
    { "delete": { "tableName": "Customer", "where": "IsActive = 0" } }
  ] }
]
```
