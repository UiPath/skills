# Tenant Library Search

Discover libraries already deployed to the tenant feed. Use whenever the user wants to "leverage", "reuse", "find", or "use existing" libraries — and as Step 2.5 of SDD generation for any RPA-bearing scope.

## Default search target: tenant feed, not local filesystem

The tenant feed is authoritative for org-published libraries. Do NOT search the local filesystem, project folder, NuGet.org, or `git grep` for "shared library" candidates — those surfaces do not represent what the org has deployed.

## CLI surface

One command, one global filter:

```bash
uip resource libraries list --limit 500 --output json
```

Returns `Data: [{ Key, Title, Version, Authors }]`. `Key` is `PackageId:Version` and is always populated. `Title` can be `null`.

| Flag | Purpose |
|------|---------|
| `--limit <N>` | Items per call (default 50). Use 500 to cover most tenants in one call. |
| `--offset <N>` | Pagination offset. Use only if `Data.length == --limit`. |
| `--order-by "<field> <asc\|desc>"` | Sort. Default `Id desc`. |
| `--output-filter "<JMESPath>"` | Global filter, evaluated client-side after the API returns. |
| `-t, --tenant <name>` | Override default tenant. |

There is **no `--search` flag** and **no `--feed-id` flag** on `libraries list`. Filter via `--output-filter`.

## JMESPath filter recipe

`Title` can be `null`, so `contains(Title, 'X')` errors out unless guarded. Always use:

```bash
# Single keyword
uip resource libraries list --limit 500 \
  --output-filter "[?Title != null && contains(Title, 'Excel')]" \
  --output json

# Multi-keyword OR
uip resource libraries list --limit 500 \
  --output-filter "[?Title != null && (contains(Title, 'Common') || contains(Title, 'Shared'))]" \
  --output json
```

For case-insensitive matching, lowercase the keyword in the filter and the field: `contains(to_string(Title), 'common') || contains(to_string(Title), 'Common')` — or run unfiltered and rank in-agent.

### Authors-field filter

For orgs that publish libraries with cryptic Titles but a stable `Authors` value, filter on `Authors` instead of `Title`:

```bash
uip resource libraries list --limit 500 \
  --output-filter "[?Authors != null && contains(Authors, '<OrgName>')]" \
  --output json
```

Combine `Title` and `Authors` filters with `||` when the org uses both conventions inconsistently.

## Procedure

1. **Auth preflight.** Run a benign call once: `uip resource libraries list --limit 1 --output json`. If `Result == "Failure"` with an auth-related message, surface it and switch to the manual fallback (below). Do NOT retry silently.
2. **Extract keywords** from the source (PDD Application Inventory, user prompt, project intent). Cap at 6:
   - Org-prefix terms: `Common`, `Shared`, `Utils`, `Helpers`, `<Company>` if known
   - Capability terms: `Excel`, `SAP`, `ServiceNow`, `Salesforce`, `Email`, `PDF`, `SharePoint`, `Outlook`, `Citrix`, etc. — drawn from the in-scope applications
   - Domain terms: `Invoice`, `Vendor`, `Banking`, `Order` — drawn from the process name

   If you have more than 6 candidate keywords, **skip the OR-filter** and run unfiltered (`--limit 500`, paginate via `--offset` until `Data.length < limit`); rank in-agent. Splitting a long keyword set across multiple OR-filtered calls is an anti-pattern (#7 below).
3. **Run one filtered call covering all keywords** with the OR pattern above. Single call, not one per keyword. Branch on the result: ≥1 candidate after ranking → step 5a. 0 candidates → step 5b. Do not loop back to step 2 with new keyword permutations.
4. **Rank candidates in-agent.**
   - Org-prefix match in `Title` or `Key` (starts with `Common`, `Shared`, `<Company>`) → rank highest
   - Capability/domain match in `Title` → rank next
   - Authors equal to the user's org → boost
   - De-duplicate by `Title` keeping the latest `Version`
5a. **If ≥1 candidate — present top 5 via `AskUserQuestion` with `multiSelect: true`.** Each option label: `<PackageId> <Version> — <Title>`. Always include "None / skip" as a non-multiSelect-exclusive option (or describe it as "leave all unchecked").
5b. **If 0 candidates — present a single-select numbered fallback.** Do not run more filtered calls with new keywords:

   > No org-published libraries matched the search. How would you like to proceed?
   >
   > 1. **Proceed without shared libraries** *(recommended)* — §14 will list only public NuGet dependencies; the reuse mandate becomes a forward note in §16
   > 2. **Search a specific name or prefix** — re-run with the team's actual library naming convention
   > 3. **Provide names manually** — name libraries to include even if not yet deployed; flag as `[VERIFY DEPLOYMENT]`
   > 4. **Pause and re-authenticate to a different tenant** — if libraries live elsewhere

6. **Record the user's selection.** For SDD usage: write each selected library into every sub-project's §14 Packages table and into §16 → "Shared libraries referenced". For RPA usage: pass to `install-or-update-packages` after project scaffold.

## Manual fallback (auth preflight failed)

If `uip` is unauthenticated, ask the legacy question:

> Tenant library search is unavailable (not authenticated to a UiPath tenant). Provide shared libraries manually?
>
> 1. **Skip — no shared libraries** *(recommended)*
> 2. **Yes — `CommonLibrary`** (the conventional default)
> 3. **Yes — other** (you name them)
> 4. **Authenticate first** — run `uip auth login`, then re-invoke the skill

## Anti-patterns

1. **Searching the local filesystem first.** Tenant is authoritative; local matches do not indicate org adoption.
2. **Using `--search`.** That flag does not exist on `uip resource libraries list`. Filter via `--output-filter`.
3. **Using `--feed-id`.** That flag does not exist on `uip resource libraries list` (it does on `uip or packages list` — different command). The libraries command always targets the default tenant feed.
4. **Calling `contains(Title, ...)` without `Title != null` guard.** Tenants commonly hold packages with null Title — the call fails fast with `Invalid type: contains() expected ... received type null`.
5. **Listing all libraries with no `--limit` bump, or paginating past the end.** Default 50 truncates large tenants and silently misses candidates. Use `--limit 500` for a one-shot scan; paginate via `--offset` only if `Data.length == 500`. If `Data.length < --limit` on a paginated call, you have seen the entire feed — stop searching, do not run more filtered queries hoping for hidden matches.
6. **Auto-selecting a candidate.** Library selection drives §14 Packages and project compilability — always confirm via `AskUserQuestion`.
7. **One CLI call per keyword, or running more keyword permutations after a zero-result filtered call.** Combine keywords into one OR-filtered call. On zero results, escalate to step 5b — do not loop back with new keyword sets hoping for hidden matches.
8. **Repeating the search per sub-project in a Solution.** Run once per SDD generation; reuse the result across all sub-projects.
