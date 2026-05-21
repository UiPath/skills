# Project Layout

Maestro BPMN Process Orchestration projects use BPMN XML as source and generated JSON files as package/runtime metadata. Local authoring can use a standalone project directory; Studio Web upload, publish, debug, and run require the project to be wrapped or registered in a UiPath solution directory.

## Workspace Choices

For local-only authoring, validation, or packaging, keep the project at the path
the user requested:

```text
ProjectName/
  ProjectName.bpmn
  project.uiproj
  bindings_v2.json
  entry-points.json
  operate.json
  package-descriptor.json
```

```bash
uip maestro bpmn init ProjectName --output json
uip maestro bpmn validate ./ProjectName/ProjectName.bpmn --output json
uip maestro bpmn pack ./ProjectName ./dist -n ProjectName --output json
```

For Studio Web upload, publish, debug, or run, use a solution directory with a
`.uipx` manifest and one or more project subdirectories:

```text
SolutionName/
  SolutionName.uipx
  ProjectName/
    ProjectName.bpmn
    project.uiproj
    bindings_v2.json
    entry-points.json
    operate.json
    package-descriptor.json
```

Create the solution first, then initialize the BPMN project inside it:

```bash
uip solution new --help --output json
uip solution new SolutionName --output json
cd SolutionName
uip maestro bpmn init ProjectName --output json
uip solution project list --output json
```

Use `uip solution new` to create the solution directory and `.uipx` manifest.
Current `uip maestro bpmn init` registers the project when it runs inside a
solution. If an older CLI does not register it, use
`uip solution project add ProjectName SolutionName.uipx --output json`. Use
`uip solution project import --source <ProjectDir> --solutionFile <SolutionFile> --output json`
when an existing project starts outside the solution.

## Canonical source files

- `<project>.bpmn` - BPMN process source and UiPath extension XML. For a new
  project, keep the BPMN source basename exactly aligned with the project
  directory/name. For example, `InvoiceTriageBpmn/InvoiceTriageBpmn.bpmn`, not
  `InvoiceTriageBpmn/invoice-triage-bpmn.bpmn`.
- `project.uiproj` - UiPath project metadata. Keep it in the same project
  directory as the main BPMN file: `InvoiceTriageBpmn/project.uiproj`, not next
  to the project directory.

For a local-only task, do not move the project under a solution if the user or
test harness asked for a specific project path. Before cloud lifecycle actions,
wrap or import the project into a solution and report that change.

## Generated or CLI-managed package files

- `bindings_v2.json` - resource bindings generated or enriched from BPMN and registry/connection metadata.
- `entry-points.json` - runnable start-event entry points and input/output schemas.
- `operate.json` - runtime/package metadata.
- `package-descriptor.json` - package manifest mapping generated files and BPMN content.

Treat these JSON files as derived unless a CLI contract explicitly identifies a field as user-authored. For source fixes, edit BPMN or rerun CLI enrichment rather than patching generated output by hand.

Local packaging requires the generated metadata set to exist. In particular,
`uip maestro bpmn pack <SolutionDir>/<ProjectName> <OutputDir> --name <ProjectName> --output json` consumes
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

The local package descriptor maps BPMN and generated JSON files with its `files` map; the packaged artifact places those files under `content/`. The entry point file path references the BPMN file and start event, using the root start event's unique entry point ID.

## Authoring boundary

Authoring owns local files and local validation. It can create or edit BPMN source, preserve existing generated files for comparison, and run validation/generation commands. It stops before upload, debug, publish, or run unless the user explicitly consents.

Operate owns cloud-side side effects: upload, publish, deploy, debug, process run, instance lifecycle, and cloud resource refresh.

Diagnose owns post-run inspection: incidents, variables, element executions, deployed assets, traces, and correlation back to BPMN element IDs.
