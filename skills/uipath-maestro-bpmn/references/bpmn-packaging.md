# BPMN packaging and contract metadata

Package metadata, layout, and validation layers for a compiled `.bpmn`.

## Contract metadata

<!-- RULE:bpmn.metadata.case-management -->
- Process-level `uipath:caseManagement` is distinct from typed `Orchestrator.StartCaseMgmtProcess`/`Orchestrator.StartCaseMgmtProcessAsync`. When explicitly required, author `.metadata({ caseManagement: { version: 'v1', value: '{"mode":"preserve-only"}' } })`; a case-process call does not emit or replace it.

## Packaging and layout

<!-- RULE:bpmn.package.derived -->
- Metadata derives from BPMN: `operate.json.main` and each `entry-points.json` `filePath` are `/content/<Name>.bpmn#<start-id>`; `package-descriptor.json` has a `files` map; `project.uiproj` names no file. Every root start gets `uipath:entryPointId`: explicit or stable SDK-derived GUID; changing process/start id changes it, so when renaming the process or start id of a deployed process, pin the old id. `refresh` reads it, so nothing is required before `.startEvent('<start-id>')`. Preserve `bpmn init` ids by decompiling its stub or use `.metadata({ entryPointId: '<uuid>' })`; additional root starts set `entryPointId` on each `.startEvent(id, { entryPointId })`; `false` emits none and must be deleted for id-less imports. Values must be GUIDs: `validate` refuses any other (`Root start event uipath:entryPointId value … must be a GUID`), and `check` reports `ENTRYPOINT_ID_NOT_GUID` first.
  Then generate the files from the built BPMN:
  ```sh
  uip maestro bpmn refresh <project-dir> --output json   # needs its project.uiproj
  ```
  `Data.WrittenFiles` identifies stale files. Do not use deprecated `update-metadata`; it omits `Intsvc.*` connection bindings, so its package passes `validate` and faults at run time.

  For `Demo.bpmn` with root start event `start`, `init` plus `refresh` write these
  values (other fields omitted):

  ```jsonc
  // project.uiproj (written by init; refresh leaves it alone)
  { "Name": "Demo", "ProjectType": "ProcessOrchestration" }
  // operate.json
  { "main": "/content/Demo.bpmn#start", "contentType": "ProcessOrchestration", "targetFramework": "Portable" }
  // entry-points.json
  { "entryPoints": [{ "filePath": "/content/Demo.bpmn#start", "type": "ProcessOrchestration",
      "input": { "type": "object", "properties": {} }, "output": { "type": "object", "properties": {} } }] }
  // bindings_v2.json
  { "version": "2.0", "resources": [] }
  // package-descriptor.json
  { "files": { "operate.json": "operate.json", "entry-points.json": "entry-points.json",
      "bindings.json": "bindings_v2.json", "Demo.bpmn": "Demo.bpmn" } }
  ```

  Inspect every generated metadata file against this contract: `entry-points.json.entryPoints` must be non-empty and reference the built BPMN/start id. If it is empty, do not hand-write the JSON: the BPMN was not compiled by the SDK and its root start event has no `uipath:entryPointId`; fix the source, rebuild, and rerun `refresh`. If refresh says `Expected one uipath:entryPointId on root manual start event`, delete `entryPointId: false` and rebuild.

<!-- RULE:bpmn.layout.separate -->
- Compile emits semantic XML without diagram; `validate` refuses files without one. Format every newly compiled process; format a merged one only when `refresh`/`validate` reports a missing diagram or shape, or for a template or a user-chosen replacement ([`bpmn.brownfield.format`](bpmn-runtime.md#brownfield-editing)).

## Product boundary

<!-- RULE:bpmn.validation.layers -->
- TypeScript checks call shape; `bpmn check` checks graph semantics; `uip maestro bpmn validate` checks the compiled product contract; a live run remains necessary for tenant resources and runtime outcomes.
