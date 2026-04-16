# Scope Selection

**Default: ALL clauses in the pack are in scope.** Do not ask the user to pick a scenario. Only narrow scope if the user's prompt explicitly signals it.

## Signal detection (text match on the user's prompt)

| Signal in prompt | Resulting `inScopeClauseIds` |
|---|---|
| (none) | Every clause in `clause-map.json`. Default. |
| "mandatory", "required" | Clauses where `obligationLevel ∈ {Mandatory, ConditionalMandatory}`. Legacy `mandatory: true` counts as `Mandatory`. |
| "mandatory + recommended", "recommended" (with "mandatory") | `{Mandatory, ConditionalMandatory, Recommended}` |
| "all including optional", "everything" | All four levels (same as default) |
| Clause ID mentioned ("A.8.11", "A.5.23 and A.8.15") | Exactly those IDs. Validate each exists; unknown IDs halt. |
| Descriptive phrase ("data masking", "encryption controls") | NL match across `clause.name + clause.description`. Surface matches, require user confirmation before proceeding. |

## Confirmation rules

1. **Scope itself** — never ask. Derive from signals above and show a one-line preview at the pre-flight gate.
2. **NL match** — always confirm the matched clause list before proceeding (fuzzy matching is unreliable).
3. **`ConditionalMandatory` clauses** — for each one in scope, show the `condition` string and require explicit user approval before including it.
4. **Pre-flight** — one final "proceed?" before any CLI side effects. That's the only global confirmation.

## Filter to policy files

Only policy files with at least one in-scope contributing clause are passed to Phase 1. A file whose every contributor is out of scope is **skipped** and recorded as `status: "skipped"` in the deploy record.

```python
inScopePolicyFiles = { contrib.uipolicyFile
                       for clause in clauses if clause.id in inScopeClauseIds
                       for contrib in clause.contributions }
```
