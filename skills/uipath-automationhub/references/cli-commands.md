# Automation Hub via the `uip ah` CLI — Command Catalog

> **Preflight (run once per session):** `uip ah --help`. If it errors with `unknown command 'ah'`, the installed CLI predates the Automation Hub surface — tell the user to update `uip` (or follow the raw-API flows in [`api-endpoints.md`](api-endpoints.md) instead). Never mix the two paths in one run.

The CLI wraps the same Open API endpoints as [`api-endpoints.md`](api-endpoints.md) — every domain fact there (required fields, wrapping rules, document-type ids, tenant-required questions) still applies. What the CLI adds: auth is handled for you, every response is one uniform JSON envelope, and windowing/projection quirks are absorbed.

## Auth — nothing to do

`uip` resolves credentials itself, in this order:
1. **Delegate runtime env-auth**: the Delegate injects `UIPATH_CLI_AUTH_TOKEN` + org/tenant vars; `uip` consumes them natively. No setup.
2. **`uip login` session** (`~/.uipath/.auth`).

If a command fails with an authentication error, tell the user to run `uip login` — never ask for or handle a raw token yourself.

## Automation Hub not available on this tenant

The CLI already classifies this for you — read its `Instructions` field:

- `Instructions` mentioning **"not provisioned on this tenant"** → AH is not enabled. Report: *"Please contact your administrator to enable Automation Hub on this tenant."*
- `Instructions` mentioning **"no tenant record of its own yet"** → reachable but not onboarded. Report: *"Automation Hub is reachable for this tenant but has not finished setup. Open Automation Hub in the browser once to complete it, then retry."*

Either way **stop** — don't retry and don't try another tenant unless asked. Full detail (and the raw signals behind each) in [`api-endpoints.md`](api-endpoints.md) → **Automation Hub not available on this tenant**.

## Output envelope (every command)

Always pass `--output json`. Success:

```json
{ "Result": "Success", "Code": "Ah<Group><Verb>", "Data": … }
```

Failure: `Result` is `Failure`/`ValidationError` with a `Message` and usually an `Instructions` hint — surface both to the user. Exit codes: `0` success, `1` failure, `3` validation.

> ⚠️ **`--output-filter` requires an explicit `--limit`.** List commands default to `--limit 20`, and the CLI rejects an output filter on an implicit page (validation error, exit `3`) because it would silently filter only the first 20 records. Whenever you pass `--output-filter`, also pass a `--limit` sized to cover the full result set (the option's `--help` text states the command's maximum).

## Commands used by the flows

| Command | Purpose | Data shape notes |
|---|---|---|
| `uip ah auth-info get` | connectivity + who/where am I | `Data.Tenant.Url`, `Data.User` |
| `uip ah idea-flows list` | flow names → ids | entries carry `Id`, `Name`, `Phases` |
| `uip ah automations schema get --idea-flow-id <id> --destination <file>` | write the flow's schema + `user_inputs` template to a file | same document as the raw `/idea-schema` |
| `uip ah categories get` | category tree | `Data.Levels` + `Data.Categories` (nested `subcategories`; pick `category_is_active: 1` only) |
| `uip ah users list --limit 50` | owner/submitter discovery | entries carry `Email`, `IsActive` |
| `uip ah applications list` | app inventory (tenant-required application questions) | entries carry `Id`, `Name` |
| `uip ah automations create --from-schema --idea-flow-id <id> --file <answers.json>` | **create the process** | `Data.Id` is the new process id |
| `uip ah documents create <automation-id> --title <t> --description <d> --document-type-id <n> --file <path>` | **upload a document's bytes** | `Data.Id` (document id) + `Data.FileId`; use `--embed-link <url>` *instead of* `--file` for link-only docs (exactly one of the two) |
| `uip ah documents list <automation-id>` | verify attachments | entries carry `Id`, `Title`, `FileId` (file-backed) or `EmbedLink` (link-backed) |
| `uip ah documents download <file-id> --destination <path>` | **download a document's bytes** | takes the `FileId` from `documents list`, **not** the document `Id` |
| `uip ah automations update <id> --file <answers.json>` | edit assessment answers post-create (e.g. set the Studio Web link) | same `user_inputs` document shape as create |
| `uip ah automations list --search <text> --limit 20` | name → process id | projected records with `Id`, `Name`, `Phase` |
| `uip ah automations get <id> [--all-fields]` | one process record | default projection has `Id`/`Name`/`Phase`/`Tags`; `--all-fields` for the raw record (needed for `process_slug`) |
| `uip ah components list --automation-id <id>` | linked components (optional, get flow) | same record shape as the tenant-wide catalogue |

**Version note:** the `ah` surface first appears in `uip` **1.201.0** (as of 2026-08-21 no public release ships it — the latest release is 1.199.0; the Step-0 preflight routes older installs to the raw-API flows). `documents create --file` and `automations create --idea-flow-id` additionally come from CLI PR #3720 — if either flag is rejected as unknown, the installed `uip` has the `ah` surface but predates those flags: tell the user to upgrade `uip` and **stop**. Never switch to the raw-API path mid-run — the transport was already selected at preflight.
