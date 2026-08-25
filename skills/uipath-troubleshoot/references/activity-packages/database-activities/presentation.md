# Database Activities Presentation Rules

- **Activities** — use the display name (e.g., "Execute Query", "Execute Non Query", "Connect to Database", "Start Transaction", "Run Command"), not the fully qualified class name (e.g., `UiPath.Database.Activities.ExecuteQuery`)
- **Databases / connections** — refer to the database by its server + database name from the connection string (e.g., "the `SALES` database on `db-prod-01`"), not by the variable holding the `DatabaseConnection`
- **SQL statements** — refer to the statement by what it does (e.g., "the `SELECT` against `Orders`"), and quote the relevant SQL fragment; do not refer to it by the variable holding the query text
- **Parameters** — refer to query parameters by their named placeholder as written in the SQL (e.g., "`@customerId`"), and recommend the `Parameters` collection over string concatenation
- **Providers** — name the ADO.NET provider exactly as configured (e.g., `Microsoft.Data.SqlClient`, `System.Data.SqlClient`, `System.Data.Odbc`), since connection-string syntax and error text depend on it
- **Timeouts** — state timeout values in **milliseconds** with the second-equivalent in parentheses (e.g., "`TimeoutMS` 60000 (60 s)"), because the property is `TimeoutMS`, not a seconds-based field
- **Project compatibility** — refer to project type as **Windows** or **Windows - Legacy** (the exact Studio labels), since the distinction drives provider/driver behaviour
- **Errors** — quote the **inner** provider error (e.g., `Incorrect syntax near ')'`, `ORA-00900`, `Keyword not supported: 'Provider'`), not only the UiPath wrapper `Execute Query: A database error occurred`
