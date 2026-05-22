# Project Layout

Maestro BPMN Process Orchestration projects use BPMN XML as source and generated JSON files as package/runtime metadata.

## Canonical source files

- `<project>.bpmn` - BPMN process source and UiPath extension XML. For a new
  project, keep the BPMN source basename exactly aligned with the project
  directory/name. For example, `InvoiceTriageBpmn/InvoiceTriageBpmn.bpmn`, not
  `InvoiceTriageBpmn/invoice-triage-bpmn.bpmn`.
- `project.uiproj` - UiPath project metadata. Keep it in the same project
  directory as the main BPMN file: `InvoiceTriageBpmn/project.uiproj`, not next
  to the project directory.

For a new local project, create a single project directory and place source
files under it:

```text
ProjectName/
  ProjectName.bpmn
  project.uiproj
```

## Generated or CLI-managed package files

- `bindings_v2.json` - resource bindings generated or enriched from BPMN and registry/connection metadata.
- `entry-points.json` - runnable start-event entry points and input/output schemas.
- `operate.json` - runtime/package metadata.
- `package-descriptor.json` - package manifest mapping generated files and BPMN content.

Treat these JSON files as derived unless a CLI contract explicitly identifies a field as user-authored. For source fixes, edit BPMN or rerun CLI enrichment rather than patching generated output by hand.

Local packaging requires the generated metadata set to exist. In particular,
`uip maestro bpmn pack <project-path> <OutputDir> --output json` consumes
`package-descriptor.json`; it does not create a missing descriptor from only
the BPMN and `project.uiproj`.

For the regeneration and drift-check contract, see [local-metadata-regeneration-guide.md](local-metadata-regeneration-guide.md).

## Package content

A Process Orchestration package content folder contains:

- One or more `.bpmn` files.
- `bindings_v2.json`.
- `entry-points.json`.
- `operate.json`.
- `package-descriptor.json`.

The package descriptor maps BPMN and generated JSON files under `content/`. The entry point file path references the BPMN file and start event, using the root start event's unique entry point ID.

## Authoring boundary

Authoring owns local files and local validation. It can create or edit BPMN source, preserve existing generated files for comparison, and run validation/generation commands. It stops before upload, debug, publish, or run unless the user explicitly consents.

Operate owns cloud-side side effects: upload, publish, deploy, debug, process run, instance lifecycle, and cloud resource refresh.

Diagnose owns post-run inspection: incidents, variables, element executions, deployed assets, traces, and correlation back to BPMN element IDs.
