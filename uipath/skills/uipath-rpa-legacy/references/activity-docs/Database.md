# UiPath Database Activities - Community Reference

## Overview
Database integration via ADO.NET providers. Supports any database with a .NET data provider (SQL Server, Oracle, MySQL, PostgreSQL, SQLite, ODBC, OleDB). Package: `UiPath.Database.Activities` (from Community.Activities repo).

---

## Activities

### Connection Management
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `DatabaseConnect` | Open database connection | ProviderName (required), ConnectionString OR ConnectionSecureString (overload groups), Output: DatabaseConnection |
| `DatabaseDisconnect` | Close connection | DatabaseConnection |
| `DatabaseTransaction` | Transaction scope with auto-commit/rollback | ProviderName, ConnectionString, ExistingDbConnection, UseTransaction (default true), Body (child activities) |

### Query Execution
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `ExecuteQuery` | Run SELECT statements | Sql (required), CommandType (Text/StoredProcedure/TableDirect), Parameters, TimeoutMS, Output: DataTable |
| `ExecuteNonQuery` | Run INSERT/UPDATE/DELETE | Sql (required), CommandType, Parameters, TimeoutMS, Output: AffectedRecords (int) |

### Data Operations
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `InsertDataTable` | Insert DataTable rows into table | TableName (required), DataTable (required), Output: AffectedRecords (int) |
| `BulkInsert` | High-performance bulk insert | TableName (required), DataTable (required), Output: AffectedRecords (long) |
| `BulkUpdate` | Bulk update existing rows | TableName, DataTable, ColumnNames |

### Common Properties (inherited from DatabaseExecute/DatabaseRowActivity)
- `ExistingDbConnection` (DatabaseConnection) - Reuse existing connection
- `ConnectionString` (string) OR `ConnectionSecureString` (SecureString) - New connection
- `ProviderName` (string) - ADO.NET provider (e.g., "System.Data.SqlClient", "Oracle.ManagedDataAccess.Client")
- `ContinueOnError` (bool) - Suppress exceptions
- `TimeoutMS` (int) - Command timeout in milliseconds
- `Parameters` (Dictionary<string, Argument>) - SQL parameters with direction support

---

## Critical Gotchas

### Connection Management
1. **If ExistingDbConnection is null, a new connection is created and disposed per activity** - each activity opens/closes its own connection unless you pass ExistingDbConnection
2. **ConnectionString OR ConnectionSecureString** - overload groups, cannot provide both
3. **ProviderName is REQUIRED** for new connections - must match installed ADO.NET provider exactly
4. **ConnectionValidation** checks: either ExistingDbConnection OR (ConnectionString + ProviderName) must be provided

### SQL Injection Risk
5. **Use Parameters dictionary for parameterized queries** - never concatenate user input into Sql string
6. **Parameters support direction** (In/Out/InOut) - useful for stored procedures with output parameters
7. **Parameter type inferred from ArgumentType** at runtime

### Timeout
8. **TimeoutMS must be >= 0** - negative values throw ArgumentException
9. **TimeoutMS is COMMAND timeout** (not connection timeout) - affects query execution time
10. **Default is 0** (which means provider default, typically 30 seconds for SQL Server)

### Transaction Handling
11. **DatabaseTransaction UseTransaction=true (default)** - wraps Body in transaction
12. **Auto-rollback on exception** - if Body throws, transaction rolls back
13. **Auto-commit on success** - if Body completes, transaction commits
14. **DatabaseTransaction is hidden in NETSTANDARD** builds (`[Browsable(false)]`)

### BulkInsert
15. **BulkInsert returns long** (not int) - for large datasets
16. **BulkInsert uses SqlBulkCopy** internally for SQL Server - much faster than InsertDataTable
17. **BulkInsert supports logging** via IExecutorRuntime if available

### Data Type Mapping
18. **DataTable column types must match database column types** - type mismatch causes runtime errors
19. **NULL handling** - DBNull.Value vs null in DataTable cells
20. **InsertDataTable uses SqlDataAdapter** internally - generates INSERT statements per row (slower than BulkInsert)

### Provider-Specific Issues
21. **Oracle requires Oracle.ManagedDataAccess.Client** provider (or legacy Oracle.DataAccess.Client)
22. **MySQL requires MySql.Data.MySqlClient** (or MySqlConnector)
23. **PostgreSQL requires Npgsql** provider
24. **ODBC/OleDB** work but with limited parameter support
25. **Provider DLLs must be accessible** to the UiPath Robot process at runtime
