# Database Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and evidence-gathering prerequisites for Database Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Execute Query Failures | Medium | `Execute Query` faults across seven surfaces: null/out-of-scope `DatabaseConnection`, post-migration provider mismatch (`Keyword not supported`), SQL syntax / unsafe concatenation (`A database error occurred`), query text pasted into the connection-string field, `TimeoutMS` exceeded (`Timeout expired`), `0xE0434352` CLR crash (oversized result set / Oracle ref cursor / stale package), and wrong activity for the statement type (Execute Query vs Execute Non Query). Includes anti-patterns and cross-branch prevention. | [execute-query-failures.md](./playbooks/execute-query-failures.md) |
