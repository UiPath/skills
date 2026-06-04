# Database Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and evidence-gathering prerequisites for Database Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Execute Query Failures | Medium | `Execute Query` faults across seven surfaces: null/out-of-scope `DatabaseConnection`, post-migration provider mismatch (`Keyword not supported`), SQL syntax / unsafe concatenation (`A database error occurred`), query text pasted into the connection-string field, `TimeoutMS` exceeded (`Timeout expired`), `0xE0434352` CLR crash (oversized result set / Oracle ref cursor / stale package), and wrong activity for the statement type (Execute Query vs Execute Non Query). Includes anti-patterns and cross-branch prevention. | [execute-query-failures.md](./playbooks/execute-query-failures.md) |
| Connect to Database Failures (Excel / Access via OLE DB / ODBC) | Medium | `Connect to Database` faults across four surfaces: malformed connection string (`Invalid connection string` / `ArgumentException`), ACE/Jet provider not registered or 32-vs-64-bit mismatch (`provider is not registered on the local machine`), file lock (`used by another process`), and provider init / wrong `ProviderName` after Windows-Legacy → Windows migration (`type initializer for 'Microsoft.Data.SqlClient.SqlConnection'`). Centered on the Excel-as-a-database pattern. | [connect-to-database-failures.md](./playbooks/connect-to-database-failures.md) |
