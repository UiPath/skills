# CLI Conventions (authoring)

This reference covers the **authoring-side** CLI surface only: active-context
checks and read-only discovery commands used to produce a valid, importable
Maestro `.bpmn` file. These commands may update local metadata caches but do not
mutate the discovered cloud resources. Operate and diagnose use different CLI
commands — see
[operate/CAPABILITY.md](operate/CAPABILITY.md) and
[diagnose/CAPABILITY.md](diagnose/CAPABILITY.md).

## Discovery commands (read-only, authoring-safe)

All commands below are discovery/read-only. None mutate cloud state.

| Command | Purpose |
| --- | --- |
| `uip login status [--profile <name>] --output json` | Report the active base URL, organization, and tenant for the selected login context. The response does not report the profile name. |
| `uip maestro bpmn registry pull [--profile <name>] [-f\|--force] --output json` | Sync and cache the registry. Without login, only OOTB extension types are synced; login adds discovered connectors and processes. |
| `uip maestro bpmn registry list [--profile <name>] [--limit <n\|-1>] --output json` | List cached extension types (and discovered connectors/processes). Default 30; use `--limit -1` for all. |
| `uip maestro bpmn registry search <keyword> [--profile <name>] --output json` | Find entries by keyword across extension type, label, connector name, process name. |
| `uip maestro bpmn registry get <extensionType> [--profile <name>] [--connection-id <id>] [--object-name <name>] --output json` | Get the full spec for one extension type: `XmlTemplate`, `ContextFields`, `BindingPattern`, `BindingInfo`, and input/output patterns. `--connection-id`/`--object-name` add live Integration Service field metadata for connector types. |
| `uip or queues list [--profile <name>] [--folder-key <key>\|--folder-path <path>\|--all-folders] --output json` | Resolve queue bindings in an exact supplied folder, or exhaustively when scope is unknown. |
| `uip is connections list <connector-key> [--profile <name>] --all-folders [--refresh] --output json` | Resolve enabled connections for one exact, registry-discovered connector key across every accessible folder. `--refresh` bypasses the connection cache. |
| `uip is activities list <connector-key> [--profile <name>] --output json` | List the connector's curated and generic activity catalog rows. Curated rows carry a concrete `ObjectName`; generic CRUD rows carry an `Operation` and report `ObjectName: N/A`. |
| `uip is resources list <connector-key> [--profile <name>] --connection-id <id> --operation <operation> --output json` | Resolve a concrete object for a generic CRUD activity. Do not use it for a curated row that already supplies `ObjectName`. |
| `uip is resources describe <connector-key> <object-name> [--profile <name>] [--connection-id <id>] [--operation <operation>] [-f <name=value>] --output json` | Resolve the selected object's exact method, path, parameters, request fields, and response fields. Repeat `-f` only for known parent values when the schema is parent-dependent. |

Square brackets mark syntax that is optional only when no named profile was
selected. Once the user selects a profile for live discovery, include
`--profile <name>` on every command in this table.

These are the registry/discovery commands the skill verifies against the CLI
source (`packages/maestro-tool/src/commands/registry.ts`). Do not invent flags.
Validation uses `uip maestro bpmn validate <file>` — see
[Validation](structural-bpmn.md#validation).

`registry list` is a coarse discovery view; `registry get` owns the full binding
contract. Route that contract, resolve exact identity/folder/state, and handle
ambiguity or stale evidence with the bounded workflow in
[live-resource-resolution-guide.md](live-resource-resolution-guide.md#2-select-the-adapter-from-the-full-contract).

## Validation order

For file-based authoring, complete coherent BPMN DI before the first final
`validate` call — see [Validation](structural-bpmn.md#validation). Then run:

```bash
uip maestro bpmn validate <file.bpmn> --output json
```

The `validate` command runs the canvas rules offline. If your CLI reports
`validate` as an unknown command, or it clearly runs only the deploy-readiness
checks and not the structural rules, the installed CLI is too old — update to
the latest:

```bash
npm install -g @uipath/cli@latest   # or: bun add -g @uipath/cli
```

An exit-0 validation result is structural preflight only. It does not execute
the BPMN engine and cannot establish that public input/output bridges or
business outputs produce the intended runtime values. Do not describe `Valid`
as a successful business execution.

> **Don't conclude "it doesn't exist" from truncated discovery output.** A row past a cutoff reads exactly like a missing row. Two cutoffs bite here: `registry list` defaults to **30** — pass `--limit -1` for the full set — and piping `registry search`/`is connections list` through `head`/`tail`/`grep -m`/a pager drops everything past the cap. To check existence, narrow the query (keyword to `registry search`, `--all-folders` to connection lists) rather than capping rows; cap only data already known complete.

## Output parsing

Whenever a CLI result is parsed programmatically, pass `--output json`. If a
command does not support JSON, do not silently scrape human text; keep the step
manual and tell the user.

## Login boundary

Local source authoring and `uip maestro bpmn validate` work without login (the
validator runs fully offline). Registry
discovery of **connectors and processes** (and Integration Service field
enrichment) requires `uip login`. Without login, `registry pull` still returns
the built-in (OOTB) extension types. Before live discovery, read
`uip login status [--profile <name>] --output json`; if authentication is
needed, use interactive login only where browser authentication can complete,
then verify status again. Never infer an environment URL, organization, tenant,
or profile from a task name or a prior session. If the user named a target
context and status reports another one, stop instead of silently switching. For
a named profile, pass the user-provided `--profile <name>` to status and every
dependent registry, queue, and connection command; the status payload identifies
the base URL/organization/tenant but not the profile name. Profile selection is
not sticky: `login status --profile <name>` does not switch the default context
or make later commands inherit that profile.

The bundled validator spec can replace failed CLI evidence only for login-free
built-in templates. It cannot prove the existence or current state of a live
resource; follow the blocked/refresh boundary in
[live-resource-resolution-guide.md](live-resource-resolution-guide.md#4-refresh-once-then-stop).

## Never fabricate an identifier

Connection IDs, `releaseKey`/process keys, queue keys, connector keys, app IDs,
folder IDs/paths — every concrete identifier comes from the active context's
discovery results or from the user. Never invent one. In live mode, ask when a
required identity remains ambiguous; in portable draft mode, leave the
placeholder unresolved and label the node non-runnable.

## Side-effect boundary

Status, registry pull/list/search/get, queue list, and connection list are
authoring-safe discovery. They may update local session or metadata cache state,
but they do not mutate the discovered resource. Connection create/edit/delete
changes tenant configuration, and direct connector operation execution can
change an external system. Those actions require explicit user consent and are
never substitutes for resource or schema discovery.
