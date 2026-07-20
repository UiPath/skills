# Runtime Exceptions Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — scope check, data correlation rules, local log paths, and source code analysis for runtime exception investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Null Reference Exception | Medium | `System.NullReferenceException` in workflow code — uninitialized variable, null activity output, missing data, or unguarded conditional path | [null-reference-exception.md](./playbooks/null-reference-exception.md) |
| Argument Null Exception | Medium | `System.ArgumentNullException` in workflow code — null value passed to activity or method that requires non-null | [argument-null-exception.md](./playbooks/argument-null-exception.md) |
| Assign — Type Mismatch (Design-Time) | High | `Cannot assign from type '<X>' to '<Y>'` (e.g. `System.Object`→`System.String`, `System.String`→`System.String[]`) — Studio Error List validation error on an `Assign`; RHS expression type ≠ target variable type | [assign-type-mismatch.md](./playbooks/assign-type-mismatch.md) |
| Assign — Source Contains No Data Rows | High | `System.InvalidOperationException: The source contains no data rows` — LINQ `.CopyToDataTable()` in an `Assign` when the `.Where`/`.Select` matched zero rows | [assign-linq-no-data-rows.md](./playbooks/assign-linq-no-data-rows.md) |
