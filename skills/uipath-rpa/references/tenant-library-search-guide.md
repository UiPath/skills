# Tenant Library Search

Discover libraries already deployed to the tenant feed. Use whenever the user wants to "leverage", "reuse", "find", or "use existing" libraries — typically before adding NuGet dependencies to a new RPA project, or when planning which utilities a project should consume.

## Default search target: tenant feed, not local filesystem

The tenant feed is authoritative for org-published libraries. Do NOT search the local filesystem, project folder, NuGet.org, or `git grep` for "shared library" candidates — those surfaces do not represent what the org has deployed.

## CLI surface

`uip or libraries list`. Returns a curated `Data: [{ Key, Title, Version, Authors }]` (pass `--all-fields` for the full DTO). `Key` is `PackageId:Version` and is always populated. `Title` can be `null`.

```bash
# Server-side name search (contains-match), single keyword:
uip or libraries list --search Excel --output json

# Full scan, then filter/rank client-side:
uip or libraries list --limit 500 --output json
```

| Flag | Purpose |
|------|---------|
| `-s, --search <term>` | Server-side name contains-match. Single term only — for multi-keyword OR or `Authors` matching, use `--output-filter`. |
| `--feed-id <id>` | Target a specific feed by ID. Defaults to the tenant feed. |
| `--limit <N>` | Items per call (default 50). Use 500 to cover most tenants in one call. |
| `--offset <N>` | Pagination offset. Use only if `Data.length == --limit`. |
| `--sort-by "<field> <asc\|desc>"` | Sort. Default `Id desc`. |
| `--all-fields` | Return the full library DTO instead of the curated subset. |
| `--output-filter "<JMESPath>"` | Client-side filter, evaluated after the API returns. Use for multi-keyword OR, `Authors` matching, or null-`Title` guarding. |

`--search` is the simplest path for a single name keyword. Use `--output-filter` (below) when you need multi-keyword OR, `Authors`-field matching, or a null-`Title` guard.

## JMESPath filter recipe

`Title` can be `null`, so `contains(Title, 'X')` errors out unless guarded. Always use:

```bash
# Single keyword
uip or libraries list --limit 500 \
  --output-filter "[?Title != null && contains(Title, 'Excel')]" \
  --output json

# Multi-keyword OR
uip or libraries list --limit 500 \
  --output-filter "[?Title != null && (contains(Title, 'Common') || contains(Title, 'Shared'))]" \
  --output json
```

For case-insensitive matching, lowercase the keyword in the filter and the field: `contains(to_string(Title), 'common') || contains(to_string(Title), 'Common')` — or run unfiltered and rank in-agent.

### Authors-field filter

For orgs that publish libraries with cryptic Titles but a stable `Authors` value, filter on `Authors` instead of `Title`:

```bash
uip or libraries list --limit 500 \
  --output-filter "[?Authors != null && contains(Authors, '<OrgName>')]" \
  --output json
```

Combine `Title` and `Authors` filters with `||` when the org uses both conventions inconsistently.

## Procedure

1. **Auth preflight.** Run a benign call once: `uip or libraries list --limit 1 --output json`. If `Result == "Failure"` with an auth-related message, surface it and switch to the manual fallback (below). Do NOT retry silently.
2. **Extract keywords** from the source (user prompt, plan tasks, surrounding workflow names). Cap at 6:
   - Org-prefix terms: `Common`, `Shared`, `Utils`, `Helpers`, `<Company>` if known
   - Capability terms: `Excel`, `SAP`, `ServiceNow`, `Salesforce`, `Email`, `PDF`, `SharePoint`, `Outlook`, `Citrix`, etc. — drawn from the activities the project will use
   - Domain terms: `Invoice`, `Vendor`, `Banking`, `Order` — drawn from the project name and request

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
   > 1. **Proceed without shared libraries** *(recommended)* — install only public NuGet dependencies
   > 2. **Search a specific name or prefix** — re-run with the team's actual library naming convention
   > 3. **Provide names manually** — name libraries to install even if not yet deployed; flag as `[VERIFY DEPLOYMENT]`
   > 4. **Pause and re-authenticate to a different tenant** — if libraries live elsewhere

6. **Record the user's selection.** For each accepted library, run `uip rpa packages install --packages '[{"id": "<PackageId>", "version": "<Version>"}]' --output json` to add it to `project.json`. Verify after install with `uip rpa validate --output json`.

## Skip when

- An SDD already records "Shared libraries referenced" in §16 — those have been confirmed and the package list flows from the SDD. Do not re-prompt.
- The user has explicitly said "no shared libraries" earlier in the session.
- The task is pure UI capture / authoring with no new dependencies.

## Manual fallback (auth preflight failed)

If `uip` is unauthenticated, ask the legacy question:

> Tenant library search is unavailable (not authenticated to a UiPath tenant). Provide shared libraries manually?
>
> 1. **Skip — no shared libraries** *(recommended)*
> 2. **Yes — `CommonLibrary`** (the conventional default)
> 3. **Yes — other** (you name them)
> 4. **Authenticate first** — run `uip login`, then re-invoke the skill

## Anti-patterns

1. **Searching the local filesystem first.** Tenant is authoritative; local matches do not indicate org adoption.
2. **Using `--search` for multi-keyword OR or `Authors` matching.** `--search` is a single-term server-side name contains-match only. For OR across keywords or matching on `Authors`, use `--output-filter`.
3. **Passing `--feed-id` without a reason.** It defaults to the tenant feed — only set it to target a non-default feed.
4. **Calling `contains(Title, ...)` without `Title != null` guard.** Tenants commonly hold packages with null Title — the call fails fast with `Invalid type: contains() expected ... received type null`.
5. **Listing all libraries with no `--limit` bump, or paginating past the end.** Default 50 truncates large tenants and silently misses candidates. Use `--limit 500` for a one-shot scan; paginate via `--offset` only if `Data.length == 500`. If `Data.length < --limit` on a paginated call, you have seen the entire feed — stop searching, do not run more filtered queries hoping for hidden matches.
6. **Auto-installing a candidate.** Library installation modifies `project.json` and project compilability — always confirm via `AskUserQuestion` before invoking `packages install`.
7. **One CLI call per keyword, or running more keyword permutations after a zero-result filtered call.** Combine keywords into one OR-filtered call. On zero results, escalate to step 5b — do not loop back with new keyword sets hoping for hidden matches.
