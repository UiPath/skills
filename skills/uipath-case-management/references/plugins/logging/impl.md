# Logging — Implementation

Unified issue log for the implementation phase. Initialized by `implementation.md`, written to by any plugin, dumped to markdown after build.

## Setup

Initialize before Step 6:

```python
issues = []
```

## Entry Format

```python
issues.append({
    "severity": "ERROR",       # "ERROR" | "WARNING" | "SKIPPED"
    "step": "9",               # implementation step number
    "plugin": "io-binding",    # plugin name — used for grouping in the output file
    "message": "human-readable description"
})
```

| Severity | Meaning | Build effect |
|---|---|---|
| `ERROR` | Required element missing — operation skipped | Binding/wiring incomplete |
| `WARNING` | Possible problem — operation proceeded | May cause runtime issues |
| `SKIPPED` | Intentionally deferred — skeleton/unresolved | User must complete manually |

## Dump

After Step 12 (validate), group issues by `plugin` and write to `tasks/build-issues.md`:

```markdown
# Build Issues — <CaseName>

**Case file:** caseplan.json | **Timestamp:** <ISO>

| Category | Errors | Warnings | Skipped |
|---|---|---|---|
| [io-binding](#io-binding) | 3 | 1 | 2 |
| [global-vars](#global-vars) | 1 | 0 | 0 |
| **Total** | **4** | **1** | **2** |

---

## io-binding

### Errors

| Step | Issue |
|---|---|
| 9 | Input `amount` not found on task "Validate Expense Data" |

### Skipped

| Step | Task | Reason |
|---|---|---|
| 9 | Run Compliance Check | No inputs — skeleton task |
```

- Omit severity subsections with zero entries
- Plugins with zero issues: write `No issues.` under the heading
- Write the file even if zero total issues — confirms a clean build
- The completion report (Step 13) reads this file directly
