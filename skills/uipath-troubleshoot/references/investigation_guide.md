# Generic Investigation Guide

Always apply these rules. If a product-specific `investigation_guide.md` exists, apply it **in addition to** these.

## Data Correlation

Before using fetched data, verify its **timestamp** (within the user's window, or recent enough if none was specified), **entity identity** (requested job, queue item, process, asset, etc., not a different one with a similar name), **environment** (correct tenant, folder, or environment), and **causal relevance** (about the problem, not an unrelated side effect). If any check fails, **discard it**, report the mismatch, and ask for clarification; do NOT use unrelated data as a proxy.

## Output Capture

For every `uip` data-gathering command:

1. Filter at the source with `--output-filter` to retrieve only needed fields. Do NOT fetch the full response and slice it (`[:3000]` etc.); that silently drops information.
2. Run `mkdir -p .local/investigations/raw` once before the first fetch. `tee` and `>` do not create the directory — otherwise the file is silently dropped.
3. Capture a **small / filtered result** with `| tee .local/investigations/raw/<command>.json` to save and echo the already-small result. Capture a **heavy or unfilterable result** (dense traces, full logs/stacks, `errorDetails`, or the fallback below) with `> .local/investigations/raw/<command>.json`, then read back only needed fields/lines. Do NOT `tee` a full unfiltered response — it loads the whole body into context.

**Filter-failure fallback.** If `--output-filter` returns empty, an error, or an uninterpretable shape (usually a field name drifted from the current CLI schema), retry the SAME command ONCE without `--output-filter`. Capture that unfiltered retry with `>` (not `tee`), read back only needed fields, and note the stale filter in the evidence summary. Do NOT silently swallow filter errors.

**Anti-patterns:** Do NOT `tee` full unfiltered responses, use `| head -c N` or byte/character slicing, fetch unfiltered responses when 2–3 fields suffice, or invent JSONpath field names. Use only documented filters and the fallback above on failure.

## Signal-Extraction Cheatsheet

Fetch each signal per the domain's `investigation_guide.md`; exact commands are documented there and in playbook `## Investigation` sections.

| Signal kind | Where to find it |
|---|---|
| exception (class/FQN) | Job record `Info`; error-level job logs; trace span error attributes; Maestro incident body. Unwrap `System.AggregateException` / `--->` chains—the INNER exception is the routable signal. |
| message / message-key | Verbatim friendly message in job `Info` / logs; localization resource keys quoted in UIA exception details. |
| error-code | Message text (`DAP-*`, `#NNNN`, `AADSTS*`, HRESULTs like `0x8004027D`); Maestro incident code (e.g. `170002`); job `PendingReasons.ErrorCodes`. |
| http-status | Message text ("Bad Gateway", "429"); trace span attributes. |
| state | Job `State` + `PendingReasons`; Maestro instance status + incident open/closed; connection status. |
| faulting activity + package | `[Name]` prefix in error log message bodies; span names; exception FQN prefix maps to the owning package (see `references/summary.md` domain namespaces). |
| package versions | `project.json` dependencies (source-required); job record package version fields. |

## Locating Project Source & Resource Files

A UiPath project may use either layout; any named source or resource file (workflow, code, manifest, or connection/asset/queue/bucket resource) may be in either. Resolve BOTH before concluding a file is absent — this applies to every product, not just the one that named the file:

- **Standalone:** resources inline under the project dir (e.g. `<project>/connection/<connector>/*.json`).
- **Solution:** the project is under a subdir and resources are hoisted into a solution wrapper at the **solution root**, the working directory and *parent* of the named project dir—not inside it. E.g. from the working directory `resources/solution_folder/connection/<connector>/*.json`; likewise `resources/solution_folder/{package,process,asset,queue,bucket}/...`.

Search from the working-directory root, not only the named project subdir. If the user points to `./MyProject/`, search inside it and the working-directory root / one level up (`./resources/solution_folder/...`). When a playbook path is absent, check the other layout, including the solution root above the project, before treating the file as missing. If neither resolves, report a data gap and ask for the correct path. Absence from one layout is NOT absence.

## Interpreting Query Results

- **Empty results or 404:** before concluding an entity does not exist, verify the container (folder, tenant, instance) remains accessible. If deleted or returning 404, scoped queries are unreliable. Widen the search (different folder, broader time window, different state filters) or flag a data gap and ask the user. Never treat empty results from an inaccessible container as proof of absence.
- **Live infrastructure data:** machine connectivity, license counts, connection health, and robot availability show current state, not historical state. For incidents older than 24 hours, use them only as context; current state may differ from six months ago. Never use current infrastructure snapshots as causal evidence for past incidents.

## Testing Prerequisites

Gather and verify these before drawing conclusions on any hypothesis:

1. **Reproduce the scope** — confirm the same entity, environment, and time window.
2. **Execution path** — trace what actually happened step by step; do not infer from final status alone.
3. **Error message** — read the full error, not only its type; message details may identify the root cause.
4. **Configuration state** — check relevant settings at failure time; do not assume defaults.
5. **Recent changes** — ask whether deployments, configuration, infrastructure, or other changes correlate with issue onset.
6. **Dependencies** — check upstream and downstream systems; failures in one layer may appear as symptoms in another.

## Expected Outcome — Establish Before Investigating

Before investigating, establish what the user expects: root cause, fix, confirmation of a suspicion, or another outcome.

1. **Try to infer** it from the problem description and framing.
2. If you cannot infer it, present the identified options (e.g., "Are you looking for the root cause, a quick fix, or help understanding why this happens intermittently?") and let the user choose.
3. If you have no options, ask directly what outcome they need.

Do NOT begin until the expected outcome is clear; it determines investigation depth and a useful resolution.

## Tool Boundary — uip CLI Only

All platform interaction MUST go through `uip` CLI commands. Do NOT work around CLI limitations by:

- Calling Orchestrator REST APIs directly (e.g., via `curl` or any HTTP client)
- Reading auth tokens from `%APPDATA%/uipath-cli/.auth` or any other credential store
- Using undocumented or internal API endpoints
- Constructing OData URLs manually

If `uip` lacks a command for needed data, that data is **unavailable**. Report the gap and continue with available evidence. Do NOT bypass the CLI or suggest or mention internal API endpoints, OData URLs, auth token locations, or other workarounds to the user, even as "for your information" or "if you want to do it yourself" advice.

## Scope Boundary — Internal Platform Issues

This tool operates from the **client perspective**. Do NOT investigate internal platform issues (implementation bugs, server-side defects, infrastructure internals); they are not visible and testing them wastes the user's time.

- If evidence indicates a **known limitation or platform bug**, present it as a known issue, link documentation if available, and suggest workarounds or contacting UiPath support.
- If all client-side causes are ruled out and an internal platform issue remains, **stop testing**; tell the user it appears platform-side and recommend a support ticket with the evidence gathered.
- Do NOT fabricate unverifiable internal-platform hypotheses or ask the user to investigate server logs, database state, or infrastructure they do not control.
