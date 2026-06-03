# Local Metadata Regeneration

Use this guide when BPMN source changed and local package metadata must be refreshed or verified before packaging, upload, debug, publish, or deploy.

## Ownership

- `.bpmn` is the source of record for process structure, root variables, root bindings, entry point IDs, mappings, diagrams, and documented non-Integration-Service UiPath XML.
- `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` are derived package metadata unless a CLI contract explicitly marks a field as user-authored.
- Connector-backed or dynamically schematized `Intsvc.*` activity and event payloads are executable only after registry-backed enrichment supplies connector metadata, connection binding references, dynamic schemas, and generated package resources. Confirmed plain connectionless HTTP follows the documented pass-2 authoring recipe instead.

## Regeneration Inputs

Local regeneration reads:

- Root-level `bpmn:startEvent` elements with `uipath:entryPointId`.
- Root `uipath:variables` for entry point input/output schemas.
- Root `uipath:bindings` for package resources.
- Enriched `uipath:activity` and `uipath:event` payloads for `Intsvc.*` context fields, request payloads, output mappings, and schemas.
- The project main file from `project.uiproj` or the selected BPMN file.

Do not derive metadata from stale package files first. Use existing generated files only as a drift comparison or as CLI-owned enrichment input when the CLI explicitly supports that workflow.

## Safe Local Workflow

1. Edit `.bpmn` first.
2. Run local validation for XML, diagrams, entry point IDs, variables, mappings, binding references, and package metadata drift.
3. Before running `pack`, verify the project directory contains the full local
   metadata set: `project.uiproj`, `operate.json`, `entry-points.json`,
   `bindings_v2.json`, and `package-descriptor.json`. The pack command
   consumes these files; it does not synthesize a missing package descriptor.
4. If generated package JSON is stale, regenerate it with the supported local
   CLI path. If no generator is available for a local-only synthetic project,
   write the minimal placeholder-safe shape below before packing. For
   package-shape verification, use the local pack command and request JSON
   output when parsing command results:

   ```bash
   uip maestro bpmn pack <project-path> <OutputDir> --output json
   ```

5. Inspect the package or generated content for:
   - `entry-points.json` entries matching root start events and schemas.
   - `bindings_v2.json` resources matching root bindings and enriched connector metadata.
   - `operate.json` pointing at the intended BPMN file with `ProcessOrchestration` content type.
   - `package-descriptor.json` entries for the BPMN file and generated JSON under `content/`.
6. If the installed CLI cannot regenerate a needed file in place, keep the generated file stale only as a known blocker and report the exact unsupported step.

Packaging is local and authoring-safe. Upload, publish, deploy, debug, and run are cloud or runtime actions and still require explicit user consent.

## Minimal Local Metadata Shape

When a local-only synthetic project needs package files and the CLI cannot
regenerate them in place, use this placeholder-safe shape before running
`uip maestro bpmn pack`. Replace only the BPMN file name and start event id;
do not invent `contentFiles` as a substitute for `content`.

`project.uiproj`:

```json
{
  "projectVersion": "1.0.0",
  "ProjectType": "ProcessOrchestration",
  "Name": "SyntheticProject",
  "main": "SyntheticProject.bpmn"
}
```

`operate.json`:

```json
{
  "main": "SyntheticProject.bpmn",
  "contentType": "ProcessOrchestration"
}
```

`entry-points.json`:

```json
{
  "entryPoints": [
    {
      "id": "Entry_ManualStart",
      "filePath": "/content/SyntheticProject.bpmn#Start_Manual",
      "inputSchema": { "type": "object", "properties": {} },
      "outputSchema": { "type": "object", "properties": {} }
    }
  ]
}
```

`bindings_v2.json`:

```json
{
  "version": "2.0",
  "resources": []
}
```

This empty resource file is only a package-shape placeholder for projects with
no generated resource dependencies. It does not prove that process, queue,
connector, or agent dependencies were imported.

`package-descriptor.json`:

```json
{
  "content": [
    "content/SyntheticProject.bpmn",
    "content/bindings_v2.json",
    "content/entry-points.json",
    "content/operate.json"
  ]
}
```

## Entry Point Rules

For each root start event with `uipath:entryPointId`, generated `entry-points.json` must include:

- `id` equal to the `uipath:entryPointId` value.
- `filePath` equal to `/content/<bpmn-file>#<start-event-id>`.
- `inputSchema` from root input variables whose `elementId` matches the start event.
- `outputSchema` from root output variables.

JSON schema variables use their CDATA body as the property schema. Strip `$schema` from generated package schemas. Other primitive variables map by type, such as `string`, `integer`, `number`, `boolean`, `array`, `object`, or `json`.

## Binding Rules

Generated `bindings_v2.json` must be a top-level object with
`"version": "2.0"` and a `resources` array. Do not use a bare resource array, a
single resource object, or an unversioned `{ "resources": [] }` object; those
shapes are not the package contract consumed by solution resource refresh.

The `resources` array serves both local binding references and solution
resource refresh. Entries referenced as `=bindings.<id>` must be id-addressable.
Entries expected to import remote resources must be parseable concrete
resources.

For remote Orchestrator process dependencies, prefer CLI-generated entries. If
using fixture-backed public-safe entries, preserve `id`, `kind`, `name`,
`resourceKey`, `metadata`, `resource`, `resourceSubType`, and any
`propertyAttribute` used for name/folder-path pairs. If dependency resources are
expected, verify that refresh produced matching generated resources or report
that no dependency resources were imported.

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
- If `bindings_v2.json` differs from root bindings or `Intsvc.*` context references, rerun enrichment/generation.
- If `operate.json` or `package-descriptor.json` points at the wrong BPMN file, refresh package metadata through the CLI path.
- Do not commit private IDs, tenant URLs, connection IDs, folder keys, or copied customer payloads while resolving drift.
