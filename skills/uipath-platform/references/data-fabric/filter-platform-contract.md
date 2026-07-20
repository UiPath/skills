# Filter Platform Contract

Filter body shape (`filterGroup` / `queryFilters` / `logicalOperator`), operator token list, and the operator × field-type matrix all live in the CLI docs: [Data Fabric CLI docs → `records query` filter body](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#records-query--filter-operator--field-type-matrix). The CLI validates body shape and token names from `@uipath/data-fabric-tool` `1.199.0+`; the operator × field-type matrix is not yet CLI-enforced.

## Agent behavior

- **Out-of-matrix combo (❌ cell)** — don't silently run it. Ask the user to either (a) drop the filter, (b) supply a supported operator/type combo, or (c) accept a composition (`BETWEEN` → `>=` + `<=`; regex → `contains`/`startswith`/`endswith`). Apply only their choice (Rule 17).
- **`MULTILINE_MAX` in a filter or `sortOptions`** — refuse; surface the 400 verbatim (Rule 18). Fetch full values via `records get` and evaluate client-side only if the user asks.
- **Missing value or unknown operator** — the CLI rejects with a specific message. Surface verbatim; propose a valid operator or composition keyed to the error.
