# Generic Investigation Guide

Always apply these rules. If a product-specific `investigation_guide.md` exists, apply it **in addition** to these.

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Timestamp** — data falls within the time window the user described (or is recent enough to be relevant if no time was specified)
- **Entity identity** — the entity in the data (job, queue item, process, asset, etc.) is the one the user asked about, not a different one with a similar name
- **Environment** — data comes from the correct tenant, folder, or environment the user is working in
- **Causal relevance** — the data is about the problem itself, not about a side effect or unrelated event that happened around the same time

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Output Capture

Every `uip` data-gathering command follows two patterns — lean context AND an audit trail:

1. **Filter at the source with `--output-filter`** — pull only the fields you need. Do NOT fetch the full response and slice it (`[:3000]` etc.); that silently drops information.
2. **Save AND inspect in one call with `| tee`** — pipe the filtered response through `tee` to `.local/investigations/raw/<command>.json`: it stays visible in the tool result for immediate use AND is saved to disk to re-read during TEST. `raw/` must already exist (created at Startup with the Write tool); `tee` does not create it. Prefer `tee` over a bare `>` redirect — `>` hides stdout (extra turn to inspect) and a standalone write to `raw/` is denied in some sandboxes.

**Filter-failure fallback.** If `--output-filter` returns empty, an error, or an uninterpretable shape (usually a field name that drifted from the current CLI schema), retry the SAME command ONCE without `--output-filter` to see the actual shape. Use that unfiltered response for the current call and note the stale filter in your evidence summary. Do NOT silently swallow filter errors.

**Anti-patterns:** bare `> file.json` (hides stdout); `| head -c N` or byte/character slicing (drops required fields); fetching the unfiltered full response when 2–3 fields suffice (bloats context); inventing JSONpath field names (use only documented filters; on failure apply the fallback above).

## Locating Project Source & Resource Files

A UiPath project ships in one of two layouts, and a named source or resource file (workflow, code, manifest, or a connection/asset/queue/bucket resource) may sit in either. Resolve BOTH before concluding a file is absent — this applies to every product, not just the one that named the file:

- **Standalone** — resources inline under the project dir (e.g. `<project>/connection/<connector>/*.json`).
- **Solution** — the project sits under a subdir and resources are hoisted into a solution wrapper at the **solution root**: the working directory, which is the *parent* of the named project dir — NOT inside it. E.g. from the working directory `resources/solution_folder/connection/<connector>/*.json`; likewise `resources/solution_folder/{package,process,asset,queue,bucket}/...`.

**Search from the working-directory root, not only under a named project subdir.** When the user points you at a project dir (e.g. `./MyProject/`), the solution resources live beside it — one level up — at `./resources/solution_folder/...`. So look both **inside the named project** (standalone layout) AND **in the working-directory root / one level up from the project** (solution layout).

When a playbook names a file at one layout's path and it is not there, check the other layout — including the solution root above the project dir — before treating it as missing. If neither resolves: data gap — ask the user for the correct path. Absence from one layout is NOT absence.

## Testing Prerequisites

Gather and verify these before drawing conclusions on any hypothesis:

1. **Reproduce the scope** — confirm you're looking at the same entity, environment, and time window the user reported
2. **Execution path** — trace what actually happened step by step (don't infer from final status alone)
3. **Error message** — read the full error, not just the type; details in the message often point to the root cause
4. **Configuration state** — check relevant settings/configuration at the time of failure; don't assume defaults
5. **Recent changes** — ask whether anything changed recently (deployments, config updates, infrastructure) that correlates with when the issue started
6. **Dependencies** — check upstream and downstream systems; a failure in one layer often manifests as symptoms in another

## Expected Outcome — Establish Before Investigating

Before starting any investigation, establish what the user expects from the troubleshooting — do they want to understand the root cause, get a fix, confirm a suspicion, or something else?

1. **Try to infer** the expected outcome from the user's problem description and how they framed the request
2. **If you cannot infer**, present the user with the options you identified (e.g., "Are you looking for the root cause, a quick fix, or help understanding why this happens intermittently?") and let them choose
3. **If you have no options**, ask the user directly what outcome they need from this investigation

Do NOT begin triage or hypothesis generation until the expected outcome is clear. It determines what depth of investigation is appropriate and what a useful resolution looks like.

## Tool Boundary — uip CLI Only

All platform interaction MUST go through `uip` CLI commands. Do NOT work around CLI limitations by:

- Calling Orchestrator REST APIs directly (e.g., via `curl` or any HTTP client)
- Reading auth tokens from `%APPDATA%/uipath-cli/.auth` or any other credential store
- Using undocumented or internal API endpoints
- Constructing OData URLs manually

If the `uip` CLI does not provide a command for the data you need, that data is **unavailable**. Report the gap to the user and continue the investigation with what you have. Do NOT attempt to bypass the CLI, and do NOT suggest or mention internal API endpoints, OData URLs, auth token locations, or any other workaround to the user — even as a "for your information" or "if you want to do it yourself" suggestion.

## Scope Boundary — Internal Platform Issues

This troubleshooting tool operates from the **client perspective**. Do NOT attempt to investigate internal platform issues (implementation bugs, server-side defects, infrastructure internals). You have no visibility into them and testing hypotheses about them wastes the user's time.

- If evidence points to a **known limitation or platform bug**: present it to the user as a known issue, link to documentation if available, and suggest workarounds or contacting UiPath support
- If evidence rules out all client-side causes and the remaining explanation is an internal platform issue: **stop testing** and tell the user the problem appears to be on the platform side, recommend they open a support ticket with the evidence gathered so far
- Do NOT fabricate hypotheses about internal platform behavior you cannot observe or verify
- Do NOT ask the user to investigate server logs, database state, or infrastructure they don't control
