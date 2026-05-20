# Local Metadata Regeneration

Use this guide when BPMN source changed and local package metadata must be refreshed or verified before packaging, upload, debug, publish, or deploy.

## Ownership

- `.bpmn` is the source of record for process structure, root variables, root bindings, entry point IDs, mappings, diagrams, and documented non-Integration-Service UiPath XML.
- `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` are derived package metadata unless a CLI contract explicitly marks a field as user-authored.
- Connector-backed or dynamically schematized `Intsvc.*` activity and event payloads are executable only after registry-backed enrichment supplies connector metadata, connection binding references, dynamic schemas, and generated package resources. Confirmed plain connectionless HTTP follows the documented pass-2 authoring recipe instead.
- Local-only work may use a standalone project directory. Before upload, debug, publish, or run, wrap or register the project in a solution directory.

## Regeneration Inputs

Local regeneration reads:

- Root-level `bpmn:startEvent` elements with `uipath:entryPointId`.
- Root `uipath:variables` for entry point input/output schemas.
- Root `uipath:bindings` for package resources.
- Enriched `uipath:activity` and `uipath:event` payloads for `Intsvc.*` context fields, request payloads, output mappings, and schemas.
- The selected BPMN file and project metadata.

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
   uip maestro bpmn pack <ProjectDir> <OutputDir> --name <ProjectName> --output json
   ```

5. Inspect the package or generated content for:
   - `entry-points.json` entries matching root start events and schemas.
   - `bindings_v2.json` resources matching root bindings and enriched connector metadata.
   - `operate.json` carrying Process Orchestration runtime metadata.
   - `package-descriptor.json` `files` mappings for the BPMN file and generated JSON.
6. If the installed CLI cannot regenerate a needed file in place, keep the generated file stale only as a known blocker and report the exact unsupported step.

Packaging is local and authoring-safe. Upload, publish, deploy, debug, and run are cloud or runtime actions and still require explicit user consent.

## Minimal Local Metadata Shape

When a local-only synthetic project needs package files and the CLI cannot
regenerate them in place, use this placeholder-safe shape before running
`uip maestro bpmn pack`. This shape matches the current local `uip maestro bpmn init`
metadata contract. Replace only the BPMN file name, start event id, display
name, and public-safe project name.

`project.uiproj`:

```json
{
  "Name": "SyntheticProject",
  "ProjectType": "ProcessOrchestration"
}
```

`operate.json`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/operate",
  "projectId": "00000000-0000-0000-0000-000000000000",
  "contentType": "processOrchestration",
  "targetFramework": "Portable",
  "runtimeOptions": {
    "requiresUserInteraction": false,
    "isAttended": false
  }
}
```

`entry-points.json`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "/content/SyntheticProject.bpmn#Start_Manual",
      "uniqueId": "Entry_ManualStart",
      "type": "processorchestration",
      "input": {
        "type": "object",
        "properties": {}
      },
      "output": {
        "type": "object",
        "properties": {}
      },
      "displayName": "Manual trigger"
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

`package-descriptor.json`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/package-descriptor",
  "files": {
    "operate.json": "operate.json",
    "entry-points.json": "entry-points.json",
    "bindings.json": "bindings_v2.json",
    "SyntheticProject.bpmn": "SyntheticProject.bpmn"
  }
}
```

## Entry Point Rules

For each root start event with `uipath:entryPointId`, generated `entry-points.json` must include:

- `uniqueId` equal to the `uipath:entryPointId` value.
- `filePath` equal to `/content/<bpmn-file>#<start-event-id>`.
- `input` from root input variables whose `elementId` matches the start event.
- `output` from root output variables.

JSON schema variables use their CDATA body as the property schema. Strip `$schema` from generated package schemas. Other primitive variables map by type, such as `string`, `integer`, `number`, `boolean`, `array`, `object`, or `json`.

## Binding Rules

Generated `bindings_v2.json` must include one resource for each root binding that is not only a folder helper attribute. The resource should preserve:

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
- If `package-descriptor.json` points at the wrong BPMN file or `operate.json` has stale runtime metadata, refresh package metadata through the CLI path.
- Do not commit private IDs, tenant URLs, connection IDs, folder keys, or copied customer payloads while resolving drift.
