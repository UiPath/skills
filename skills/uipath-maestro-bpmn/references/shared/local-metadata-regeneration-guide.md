# Local Metadata Regeneration

Use this guide when BPMN source changes and local package metadata must be refreshed or verified, including after binding a connection and before packaging, upload, debug, publish, or deploy. Do not use it for a timer or V1 trigger-start draft: neither has an entry point, so `refresh` fails; skip it ([SKILL.md](../../SKILL.md) step 3). A V2 connector trigger start is an entry point, so a draft containing one runs `refresh`.

**Do NOT apply it to an Integration Service draft or boundary handoff.** For a local BPMN draft whose connector enrichment is handed to the CLI (a request that only asks to validate is not one), keep `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` CLI-owned: do not hand-author or pre-generate them. Author only the `.bpmn` source shape and a `.md` notes file **inside the project directory** naming CLI-owned blockers. This workflow reaches the project only after connector enrichment.

Run `uip maestro bpmn refresh <project-path>` as the authoritative, offline, provider-neutral source-to-derived-state boundary. It requires exactly one project-root `.bpmn`, atomically regenerates the complete package metadata set, and neither logs in, discovers a tenant, invokes a connector, nor resolves an account; it consumes only identities authored in the supported BPMN contract.

## Ownership and project contract

- `.bpmn` is authoritative for process structure, root variables and bindings, entry point IDs, mappings, diagrams, and documented non-Integration-Service UiPath XML.
- `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` are derived unless a CLI contract explicitly marks a field user-authored.
- Connector-backed or dynamically schematized `Intsvc.*` payloads are executable only after registry-backed enrichment supplies connector metadata, connection binding references, dynamic schemas, and generated package resources. Confirmed plain connectionless HTTP follows the documented pass-2 authoring recipe.

**`uip maestro bpmn refresh <project-path>` is the only supported regeneration command.** It rewrites all four derived package files and materializes `Intsvc.*` connection bindings (activities and `Intsvc.EventTrigger` / `Intsvc.WaitForEvent` triggers) in `bindings_v2.json` as `Connection` resources: triggers use `connectionId`; activities use `connection`. `update-metadata` is **deprecated**, never materializes connection bindings, and can make a trigger pass `validate` but fault at runtime with a null connection (error 102010). For V2 connector nodes it also writes each trigger start's `EventTrigger` and `Property` resources and bound picker resources, and makes each V2 trigger start an entry point—see [v2-connector-nodes.md](../v2-connector-nodes.md#3-refresh-validate-debug).

`refresh` writes the shape scaffolded by `uip maestro bpmn init`; `uip maestro bpmn pack` consumes it:

- Preserve initializer `bpmn:process@isExecutable` shape—see [structural-bpmn.md](../structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples).
- `project.uiproj` carries `"Name"` and `"ProjectType": "ProcessOrchestration"`. The CLI does not write `"main"`; preserve a hand-authored one and do not add one expecting it to be required.
- `operate.json` uses `"main"` `/content/<file>.bpmn#<start-event-id>` and `"contentType": "ProcessOrchestration"`; `refresh` rewrites this each run, so a bare filename does not survive.
- `package-descriptor.json` uses top-level `"files"` mapping names to paths, including the BPMN file, `operate.json`, `entry-points.json`, and `"bindings.json": "bindings_v2.json"`; do not use `contentFiles`.

`pack` also accepts a hand-authored top-level `"content"` array of `content/<file>` paths, so existing synthetic metadata in that shape remains valid; prefer the CLI shape for new content.

For a new local project, reuse the current in-scope solution; otherwise run:

```bash
uip maestro bpmn init <ProjectName> --output json
```

Edit the returned `Data.Path`, preserve generated metadata, and do not translate `project.uiproj`, `operate.json`, entry-point, or package-descriptor fields from another UiPath project type. If the CLI is unavailable, use the exact placeholder-safe fallback below, changing only project, file, and start-event names.

## Regeneration inputs and workflow

Local regeneration reads:

- Root manual `bpmn:startEvent` elements with `uipath:entryPointId`.
- Root `uipath:variables` for entry-point input/output schemas.
- Root `uipath:bindings` for package resources.
- Enriched `uipath:activity` and `uipath:event` payloads for `Intsvc.*` context fields, request payloads, output mappings, and schemas.
- The project/start-event path from `operate.json.main` or the selected BPMN and root manual start event.

Do not derive metadata from stale package files; use them only for drift comparison or CLI-supported enrichment input.

1. Edit `.bpmn` first.
2. Check the source itself for well-formed XML, entry-point IDs, variables, mappings, and binding references—not the diagram; step 3 generates it. Do not run `uip maestro bpmn validate` yet: it cross-checks `entry-points.json` and reports the pre-refresh error if a start event was renamed. Run it in step 5, after refresh.
3. Lay out the diagram after the last source edit: run `uip maestro bpmn format <file.bpmn>`. `refresh` validates before writing, so a newly added node fails step 4 with `MISSING_DI_SHAPE`. On a file that already had a diagram, follow [Keep the user's diagram](../../SKILL.md#keep-the-users-diagram) instead of running `format`.
4. Regenerate from source by running:

   ```bash
   uip maestro bpmn refresh <project-path> --output json    # regenerate + materialize IS connection bindings
   ```

   `refresh` validates before writing and materializes `Intsvc.*` connection bindings, including triggers. It requires a root entry point (manual or V2 connector trigger start); a timer or V1 connector start alone fails and never reaches this step. It also requires `project.uiproj`; without one it exits `BpmnRefreshFailed` / `RetryWillNotFix`, so for a bare `.bpmn` write the two-key `project.uiproj` first. `Data.WrittenFiles` identifies stale files and `Data.UnchangedFiles` already-current files; no separate drift command is needed. Never use deprecated `update-metadata`. If the CLI is unavailable for a local-only synthetic project, write the fallback shape below before continuing.
5. Run `uip maestro bpmn validate <file.bpmn> --output json`; verify the directory contains `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, and `package-descriptor.json`. Run refresh again only for idempotence; unchanged source must leave all four generated files unchanged.
6. Inspect that `entry-points.json` matches root manual starts and schemas; `bindings_v2.json` matches root bindings and enriched connector metadata; `operate.json` targets the intended BPMN with `ProcessOrchestration`; and `package-descriptor.json` maps the BPMN and generated JSON under root `files`.
7. For package-shape verification, run `pack` only after refresh:

   ```bash
   uip maestro bpmn pack <project-path> <OutputDir> --output json
   ```

   `pack` consumes generated files; it does not synthesize a missing package descriptor.

If refresh fails, atomic writing leaves the prior four-file set unchanged. Fix the reported source or project precondition and rerun; do not patch generated JSON around failure.

Refresh checks project preconditions before reading BPMN: the path is a directory, it contains exactly one root `.bpmn`, and `project.uiproj` sets `ProjectType` to `ProcessOrchestration`. A missing item reports `Required file is missing: <path>`; a wrong type reports `project.uiproj must set "ProjectType" to "ProcessOrchestration".`. Neither is a BPMN defect; do not look for one in the BPMN.

The source requires one or more root processes and at least one root manual start event overall. Every root manual start must carry exactly one valid GUID `uipath:entryPointId`; refresh creates one `entry-points.json` entry per such start. Refresh rejects with its reported message:

- A public `uipath:input`/`uipath:output` type outside `string`, `boolean`, `integer`, `number`, `array`, `object`, `json`: `Unsupported process input/output type "<type>"`. Canvas `double` and `float` are common node-scoped types but are rejected here; use `number` or an inline JSON-schema CDATA body, which bypasses the vocabulary.
- A root `uipath:output` whose `elementId` is not a root end event: `Process output "<name>" must target a root end event.`
- A repeated public name: `Duplicate process input/output "<name>".`
- A declaration with neither `type` nor inline schema.
- A connector `connection` that is not a `=bindings.<id>` reference; a missing referenced binding; a connection binding `default` that is not a GUID; or a `resourceKey` reused across connectors or connections.

Root `uipath:binding` nodes are silently dropped unless `resource` is `Connection` and `propertyAttribute` is `ConnectionId`. A connection binding with any other `propertyAttribute` therefore vanishes and surfaces as `Activity "<name>" references missing Connection binding "<id>".`; interpret this as checking binding attributes, not the activity. If the installed CLI lacks the command, retain stale generated files only as comparison evidence and report package generation blocked; a source-only project is not package-ready.

Packaging is local and authoring-safe. Upload, publish, deploy, debug, and run are cloud or runtime actions requiring explicit user consent.

## Source-only fallback

When a local-only synthetic project needs package files and the CLI cannot regenerate them in place, mirror `refresh`; replace only the BPMN filename and start-event ID.

`project.uiproj`:

```json
{"Name":"SyntheticProject","ProjectType":"ProcessOrchestration"}
```

`operate.json`:

```json
{"main":"/content/SyntheticProject.bpmn#Start_Manual","contentType":"ProcessOrchestration"}
```

`entry-points.json`:

```json
{"entryPoints":[{"filePath":"/content/SyntheticProject.bpmn#Start_Manual","uniqueId":"00000000-0000-0000-0000-000000000000","type":"ProcessOrchestration","input":{"type":"object","properties":{}},"output":{"type":"object","properties":{}}}]}
```

Set each `uniqueId` to the start event's own `uipath:entryPointId`, not the placeholder.

`bindings_v2.json`:

```json
{"version":"2.0","resources":[]}
```

This is only a package-shape placeholder for projects with no generated resource dependencies; it does not prove dependency refresh imported an external process, queue, connector, or agent.

`package-descriptor.json`:

```json
{"files":{"operate.json":"operate.json","entry-points.json":"entry-points.json","bindings.json":"bindings_v2.json","SyntheticProject.bpmn":"SyntheticProject.bpmn"}}
```

## Entry Point Rules

For every root **manual** start event with `<uipath:entryPointId value="<uuid>" />` in `extensionElements`, `entry-points.json` must contain:

- `filePath`: `/content/<bpmn-file>#<start-event-id>`.
- `uniqueId`: the `uipath:entryPointId` value.
- `type`: `ProcessOrchestration`.
- `input`: root input variables whose `elementId` matches the start event; unmatched inputs are silently dropped.
- `output`: root output variables, each with `elementId` naming a root end event; a missing or non-end-event ID fails with `Process output "<name>" must target a root end event.`

A start without that element has no entry point and `refresh` refuses the project rather than inventing one. For a bare manual start, the message is `Expected one uipath:entryPointId on root manual start event "<id>", found 0.`; when none exists because every root start carries an event definition, it is `BPMN file must contain a root manual start event with a uipath:entryPointId.`

Use JSON-schema variable CDATA as the property schema and strip `$schema` from generated package schemas. Map other primitive variables by `string`, `integer`, `number`, `boolean`, `array`, `object`, or `json`.

## Binding Rules

`bindings_v2.json` must be a top-level object with `"version": "2.0"` and a `resources` array. Do not use a bare array, single resource object, or unversioned `{ "resources": [] }`; these are not the package contract consumed by solution resources refresh.

The array serves two consumers: local/package expressions may need ID-addressable entries mirroring root `uipath:binding` IDs; `uip solution resources refresh` imports concrete dependencies only from parseable entries. Process resources should come from CLI generation or fixture-backed entries containing `id`, `kind`, `name`, `resourceKey`, `metadata`, `resource`, `resourceSubType`, and, for name/folder-path binding pairs, `propertyAttribute`.

For executable BPMN depending on remote Orchestrator processes, include generated process binding resources before refresh so it can import process/package resources and write debug overwrites. If dependencies are expected, verify matching generated resource files or explicitly report that none were imported.

Generated ID-addressable entries preserve `id`, `name`, kind/type, `resourceKey`, `metadata.BindingsVersion` from the source binding version, `metadata.DisplayLabel` from the binding display name, `metadata.SubType` from resource subtype or type, plus connector metadata, parent resource keys, and solution support fields supplied by Integration Service enrichment. If multiple BPMN elements share a connector connection binding, regenerate or validate CLI deduplication; do not copy a resource entry by hand.

## Integration Service Enrichment

Before a connector element is executable, enrichment must make these fields agree:

- Every `Intsvc.*` connection, `trigger`, object/property, or resource context references an existing root binding via `=bindings.<id>`. Activities use `connection`; triggers/waits (`Intsvc.EventTrigger`, `Intsvc.WaitForEvent`) use `connectionId`.
- The referenced package resource exists in `bindings_v2.json`; `uip maestro bpmn refresh` (and `pack`) materializes connection `Connection` resources, including triggers. Missing resources pass `validate` but fault at runtime with a null connection (error 102010).
- Connector package metadata agrees with enriched `connectorKey`; trigger property resources carry the parent trigger resource key when required by the connector shape; activity payloads include required operation context and generated request/input schemas when the selected operation requires it; output mappings target declared variables and enrichment generates dynamic output schemas.

If enrichment is unavailable, leave the BPMN element as draft intent. Do not hand-author real connection IDs, tenant resource keys, connector payloads, or dynamic schemas.

## Drift Handling

- For `entry-points.json` drift from root variables or start IDs, fix BPMN first and regenerate.
- For `bindings_v2.json` drift from root bindings or `Intsvc.*` references, fix or re-enrich BPMN, then run the BPMN refresh command again.
- For `operate.json` or `package-descriptor.json` targeting the wrong BPMN, rerun BPMN refresh; do not edit either file.
- Do not commit private IDs, tenant URLs, connection IDs, folder keys, or copied customer payloads while resolving drift.