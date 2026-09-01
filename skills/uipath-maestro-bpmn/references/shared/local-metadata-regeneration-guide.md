# Local Metadata Regeneration

Use this guide when BPMN source changed and local package metadata must be refreshed or verified before packaging, upload, debug, publish, or deploy.

## Ownership

- `.bpmn` is the source of record for process structure, root variables, root bindings, entry point IDs, mappings, diagrams, and documented non-Integration-Service UiPath XML.
- `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` are derived package metadata unless a CLI contract explicitly marks a field as user-authored.
- Connector-backed or dynamically schematized `Intsvc.*` activity and event payloads are executable only after registry-backed enrichment supplies connector metadata, connection binding references, dynamic schemas, and generated package resources. Confirmed plain connectionless HTTP follows the documented pass-2 authoring recipe instead.

## Local Synthetic Project Contract

> **Use `uip maestro bpmn refresh <project-path>` for any project with an
> Integration Service connector node.** `refresh` regenerates all four package
> files *and* materializes `Intsvc.*` connection bindings (activities, and
> `Intsvc.EventTrigger` / `Intsvc.WaitForEvent` triggers) into `bindings_v2.json`
> `Connection` resources — the trigger connection field is `connectionId`
> (activities use `connection`). `update-metadata` is **deprecated** and never
> materializes connection bindings, so a trigger regenerated with it passes
> `validate` but faults at runtime with a null connection (error 102010). The
> file-shape contract below is identical for both commands.

`uip maestro bpmn update-metadata <file.bpmn>` writes the
same shape `uip maestro bpmn init` scaffolds, and `uip maestro bpmn pack`
consumes it as written:

- The root process must be `<bpmn:process ... isExecutable="true">`.
- `project.uiproj` carries `"Name"` and `"ProjectType":
  "ProcessOrchestration"`. The CLI does not write `"main"` here; it preserves a
  hand-authored one, so do not add one expecting it to be required.
- `operate.json` uses `"main"` with the entry-point path
  `/content/<file>.bpmn#<start-event-id>` plus `"contentType":
  "ProcessOrchestration"`. `update-metadata` rewrites this field every run — a
  bare filename does not survive.
- `package-descriptor.json` uses a top-level `"files"` map of name to path,
  including the BPMN file, `operate.json`, `entry-points.json`, and
  `"bindings.json": "bindings_v2.json"`. Do not use `contentFiles`.

`pack` also accepts a hand-authored top-level `"content"` array of
`content/<file>` paths, so pre-existing synthetic metadata in that shape stays
valid. Prefer the CLI shape for anything new.

The placeholder-safe JSON shape for a CLI-unavailable fallback is shown below;
keep it exact apart from project, file, and start event names.

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
3. Regenerate package metadata from the BPMN source:

   ```bash
   uip maestro bpmn refresh <project-path>                  # regenerate + materialize IS connection bindings
   ```

   Use `refresh` — it materializes `Intsvc.*` connection bindings (including
   triggers) and validates before writing. The deprecated
   `uip maestro bpmn update-metadata <file.bpmn>` (with `--dry-run` for a
   drift check) only rewrites the BPMN-derived fields and does **not** materialize
   connection bindings.

   If CLI unavailable for a local-only synthetic project, write the minimal
   placeholder-safe shape (see below) before continuing.

4. Verify the project directory now contains the full metadata set:
   `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`,
   and `package-descriptor.json`. The pack command consumes these files; it does
   not synthesize a missing package descriptor.

5. For package-shape verification, use the local pack command:

   ```bash
   uip maestro bpmn pack <project-path> <OutputDir> --output json
   ```

6. Inspect the package or generated content for:
   - `entry-points.json` entries matching root start events and schemas.
   - `bindings_v2.json` resources matching root bindings and enriched connector metadata.
   - `operate.json` pointing at the intended BPMN file with `ProcessOrchestration` content type.
   - `package-descriptor.json` entries for the BPMN file and generated JSON under `content/`.
7. If the installed CLI cannot regenerate a needed file in place, keep the generated file stale only as a known blocker and report the exact unsupported step.

Packaging is local and authoring-safe. Upload, publish, deploy, debug, and run are cloud or runtime actions and still require explicit user consent.

## Minimal Local Metadata Shape

When a local-only synthetic project needs package files and the CLI cannot
regenerate them in place, mirror what `update-metadata` would have written.
Replace only the BPMN file name and start event id.

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
  "main": "/content/SyntheticProject.bpmn#Start_Manual",
  "contentType": "ProcessOrchestration"
}
```

`entry-points.json`:

```json
{
  "entryPoints": [
    {
      "filePath": "/content/SyntheticProject.bpmn#Start_Manual",
      "uniqueId": "00000000-0000-0000-0000-000000000000",
      "type": "ProcessOrchestration",
      "input": { "type": "object", "properties": {} },
      "output": { "type": "object", "properties": {} }
    }
  ]
}
```

Set each `uniqueId` to the start event's own `uipath:entryPointId` value, not to
the placeholder above.

`bindings_v2.json`:

```json
{
  "version": "2.0",
  "resources": []
}
```

This empty resource file is a package-shape placeholder only for projects with
no generated resource dependencies. It is not evidence that dependency refresh
imported an external process, queue, connector, or agent.

`package-descriptor.json`:

```json
{
  "files": {
    "operate.json": "operate.json",
    "entry-points.json": "entry-points.json",
    "bindings.json": "bindings_v2.json",
    "SyntheticProject.bpmn": "SyntheticProject.bpmn"
  }
}
```

## Entry Point Rules

For each root start event with a
`<uipath:entryPointId value="<uuid>" />` child in its `extensionElements`,
generated `entry-points.json` must include:

- `filePath` equal to `/content/<bpmn-file>#<start-event-id>`.
- `uniqueId` equal to the `uipath:entryPointId` value.
- `type` equal to `ProcessOrchestration`.
- `input` from root input variables whose `elementId` matches the start event.
- `output` from root output variables.

A start event without that element yields no entry point at all —
`update-metadata` reports `EntryPointCount: 0` and writes an empty
`entryPoints` array rather than inventing an id.

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

- Every `Intsvc.*` connection, `trigger`, object/property, or resource context value references an existing root binding with `=bindings.<id>`. The connection context field is `connection` for activities and `connectionId` for triggers/waits (`Intsvc.EventTrigger`, `Intsvc.WaitForEvent`).
- The referenced package resource exists in `bindings_v2.json` — for connection bindings this `Connection` resource is materialized by `uip maestro bpmn refresh` (and `pack`), including for triggers. If it is missing, the process passes `validate` but faults at runtime with a null connection (error 102010).
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
