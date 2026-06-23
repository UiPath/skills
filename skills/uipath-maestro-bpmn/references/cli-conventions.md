# CLI Conventions (authoring)

This reference covers the **authoring-side** CLI surface only: the read-only
registry discovery commands used to produce a valid, importable Maestro `.bpmn`
file. The registry commands below never mutate cloud state. Operate and diagnose
use different CLI commands — see
[operate/CAPABILITY.md](operate/CAPABILITY.md) and
[diagnose/CAPABILITY.md](diagnose/CAPABILITY.md).

## Discovery commands (read-only, authoring-safe)

All commands below are discovery/read-only. None mutate cloud state.

| Command | Purpose |
| --- | --- |
| `uip maestro bpmn registry pull [-f\|--force]` | Sync and cache the registry. Without login, only OOTB extension types are synced; login adds discovered connectors and processes. |
| `uip maestro bpmn registry list [--limit <n\|-1>]` | List cached extension types (and discovered connectors/processes). Default 30; use `--limit -1` for all. |
| `uip maestro bpmn registry search <keyword>` | Find entries by keyword across extension type, label, connector name, process name. |
| `uip maestro bpmn registry get <extensionType> [--connection-id <id>] [--object-name <name>]` | Get the full spec for one extension type: `xmlTemplate`, `contextFields`, `bindingInfo`, input/output patterns. `--connection-id`/`--object-name` add live Integration Service field metadata for `Intsvc.*` connector types. |
| `uip is connections list --all-folders` | List live Integration Service connections (id + state) across all folders. Always pass `--all-folders`; a folder-scoped list silently misses connections. |

These are the **only** commands the skill verifies against the CLI source
(`packages/maestro-tool/src/commands/registry.ts`). Do not invent flags. In
particular, there is **no** `uip maestro bpmn validate` command — see
[Validation](structural-bpmn.md#validation). Validation is done with the bundled
offline validator, not a CLI.

## Output parsing

Whenever a CLI result is parsed programmatically, pass `--output json`. If a
command does not support JSON, do not silently scrape human text; keep the step
manual and tell the user.

## Login boundary

Local source authoring and the bundled validator work without login. Registry
discovery of **connectors and processes** (and Integration Service field
enrichment) requires `uip login`. Without login, `registry pull` still returns
the built-in (OOTB) extension types.

## Never fabricate an identifier

Connection IDs, `releaseKey`/process keys, queue keys, connector keys, app IDs,
folder IDs/paths — every concrete identifier comes from discovery
(`registry get`, `registry search`, `uip is connections list`) or from the user.
Never invent one. When a required identifier is unknown, leave the placeholder
in place, flag it as a draft binding, and ask the user.
