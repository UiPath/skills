# Local Metadata Regeneration

Use this guide when BPMN source changed and local package metadata must be refreshed or verified before packaging, upload, debug, publish, or deploy.

The BPMN `refresh` command is the authoritative local source-to-derived-state
boundary. It requires exactly one project-root `.bpmn` file
and atomically regenerates the complete package metadata set. The command is
offline and provider-neutral: it does not log in, discover a tenant, invoke a
connector, or resolve an account. It consumes only identities already authored
into the supported BPMN contract.

## Ownership

- `.bpmn` is the source of record for process structure, root variables, root bindings, entry point IDs, mappings, diagrams, and documented non-Integration-Service UiPath XML.
- `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` are derived package metadata unless a CLI contract explicitly marks a field as user-authored.
- Connector-backed or dynamically schematized `Intsvc.*` activity and event payloads are executable only after registry-backed enrichment supplies connector metadata, connection binding references, dynamic schemas, and generated package resources. Confirmed plain connectionless HTTP follows the documented pass-2 authoring recipe instead.

## Current Local Project Contract

For a new local project, reuse the current solution when one is already in
scope; otherwise let the supported generator create and register one:

```bash
uip maestro bpmn init <ProjectName> \
  --output json
```

Use the returned `Data.Path` and preserve its generated metadata. The current
scaffold has these ownership boundaries:

- `project.uiproj` stores exact-cased `Name` and
  `ProjectType: "ProcessOrchestration"`; it does not own the main-file path.
- `operate.json.main` stores
  `/content/<project>.bpmn#<start-event-id>` and `contentType` stores
  `ProcessOrchestration`.
- `entry-points.json` links that start-event fragment to the same UUID carried
  by the start event's serializer-owned `uipath:entryPointId`.
- `package-descriptor.json` contains the CLI-owned `files` map.
- The CLI scaffold omits `bpmn:process@isExecutable`. Preserve that form; if
  existing source includes the equivalent default `isExecutable="false"`,
  preserve it. Do not force `isExecutable="true"`.

Do not translate `project.uiproj`, `operate.json`, entry-point, or package
descriptor fields from another UiPath project type or from a hand-written
synthetic package.

## Regeneration Inputs

Local regeneration reads:

- Root manual `bpmn:startEvent` elements with `uipath:entryPointId`.
- Root `uipath:variables` for entry point input/output schemas.
- Root `uipath:bindings` for package resources.
- Enriched `uipath:activity` and `uipath:event` payloads for `Intsvc.*` context fields, request payloads, output mappings, and schemas.
- The project/start-event path from `operate.json.main` or the selected BPMN
  file and root manual start event.

Do not derive metadata from stale package files first. Use existing generated files only as a drift comparison or as CLI-owned enrichment input when the CLI explicitly supports that workflow.

## Safe Local Workflow

1. Edit `.bpmn` first.
2. Run local validation for XML, diagrams, entry point IDs, variables, mappings, binding references, and package metadata drift.
3. After validation succeeds, regenerate derived metadata:

   ```bash
   uip maestro bpmn \
     refresh <project-path> --output json
   ```

   A successful response reports the BPMN file, main path, project ID, entry
   point count, Connection-resource count, files written, and files unchanged.
   The command derives supported V1 Connection resources from root bindings and
   `Intsvc.*` activity context, and deduplicates activities that intentionally
   share one `resourceKey`. This is connector-provider-neutral; the same source
   contract applies regardless of which provider owns the connection.
4. Verify the project now contains the full local metadata set:
   `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`,
   and `package-descriptor.json`. Run refresh a second time only when checking
   idempotence; unchanged source must leave all four generated files unchanged.
5. Inspect the generated content for:
   - `entry-points.json` entries matching root manual start events and schemas.
   - `bindings_v2.json` resources matching root bindings and enriched connector metadata.
   - `operate.json` pointing at the intended BPMN file with `ProcessOrchestration` content type.
   - `package-descriptor.json` root `files` mappings for the BPMN file and generated JSON.
6. For package-shape verification, run `pack` only after refresh. Pack consumes
   the generated files; it does not synthesize a missing package descriptor:

   ```bash
   uip maestro bpmn pack <project-path> <OutputDir> --output json
   ```

If refresh fails, the atomic write contract leaves the prior four-file set
unchanged. Fix the reported source or project precondition and run it again; do
not patch generated JSON around the failure. The current contract requires
exactly one project-root `.bpmn` file, one or more root processes, and at least
one root manual start event overall. Each root manual start event must carry
exactly one valid GUID `uipath:entryPointId`; refresh generates one
`entry-points.json` entry for each such start event. It rejects unsupported
binding-resource kinds instead of silently dropping them. If the installed CLI
does not expose this command, keep any stale generated files only as known
comparison evidence and report package generation as blocked. A source-only
project is not package-ready.

Packaging is local and authoring-safe. Upload, publish, deploy, debug, and run are cloud or runtime actions and still require explicit user consent.

## Entry Point Rules

For each root manual start event, require exactly one valid GUID
`uipath:entryPointId`. Its generated `entry-points.json` entry must include:

- `uniqueId` equal to the `uipath:entryPointId` value.
- `filePath` equal to `/content/<bpmn-file>#<start-event-id>`.
- `type` equal to `ProcessOrchestration`.
- `input` from root input variables whose `elementId` matches the start event.
- `output` from root output variables returned by that entry point.

JSON schema variables use their CDATA body as the property schema. Strip `$schema` from generated package schemas. Other primitive variables map by type, such as `string`, `integer`, `number`, `boolean`, `array`, `object`, or `json`.

## Binding Rules

Generated `bindings_v2.json` must be a top-level object with
`"version": "2.0"` and a `resources` array. Do not use a bare resource array, a
single resource object, or an unversioned `{ "resources": [] }` object; those
shapes are not the package contract consumed by solution resources refresh.

The resource array has two consumers with different tolerance:

- Local/package binding expressions may need id-addressable entries that mirror
  root `uipath:binding` IDs.
- `uip solution resources refresh` reads the same `resources` array and imports
  concrete dependencies only when it contains parseable resource entries.
  Process resources should come from CLI generation or fixture-backed binding
  entries with `id`, `kind`, `name`, `resourceKey`, `metadata`, `resource`,
  `resourceSubType`, and, for name/folder-path binding pairs,
  `propertyAttribute`.

When an executable BPMN depends on remote Orchestrator processes, include
generated process binding resources before refresh so it can import the
process/package resources and write debug overwrites. If resource dependencies
are expected, verify that refresh produced matching generated resource files or
explicitly report that no dependency resources were imported.

Generated id-addressable entries should preserve:

- `id`, `name`, kind/type, and `resourceKey`.
- `metadata.BindingsVersion` for the source binding version.
- `metadata.DisplayLabel` from the binding display name.
- `metadata.SubType` from the binding resource subtype or type.
- Connector metadata, parent resource keys, and solution support fields supplied by Integration Service enrichment.

If multiple BPMN elements share a connector connection binding, regenerate or validate deduplication through the CLI instead of copying a resource entry by hand.

## Integration Service Enrichment

Before a connector element is executable, enrichment must make these fields agree:

- Every `Intsvc.*` `connection`, `trigger`, object/property, or resource context value references an existing root binding with `=bindings.<id>`.
- The referenced package resource exists in `bindings_v2.json`.
- Connector-specific package metadata agrees with the `connectorKey` in the enriched payload.
- Trigger property resources carry the parent trigger resource key when required by the connector shape.
- Activity payloads include required operation context and generated request/input schema data when the selected operation requires it.
- Output mappings target declared variables and dynamic output schemas are generated by the enrichment tool.

If enrichment is unavailable, leave the BPMN element as draft intent. Do not hand-author real connection IDs, tenant resource keys, connector payloads, or dynamic schemas.

## Drift Handling

- If `entry-points.json` differs from root variables or start event IDs, fix the BPMN source first, then regenerate.
- If `bindings_v2.json` differs from root bindings or `Intsvc.*` context references, fix or re-enrich the BPMN source, then run the BPMN refresh command again.
- If `operate.json` or `package-descriptor.json` points at the wrong BPMN file, rerun BPMN refresh instead of editing either file.
- Do not commit private IDs, tenant URLs, connection IDs, folder keys, or copied customer payloads while resolving drift.
