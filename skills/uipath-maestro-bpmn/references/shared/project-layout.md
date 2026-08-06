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

For a new local project, place source files under a single project directory.
`uip maestro bpmn init <ProjectName> --output json` nests that directory inside
a solution. Inside a solution it registers the project with the parent `.uipx`;
outside any solution it auto-scaffolds `<ProjectName>Solution/` and nests the
project inside (the response adds `Data.AutoCreatedSolution` =
`{ Name, Path, SolutionFile }` and reports `SolutionRegistration.Status:
Registered`; re-running is idempotent and reports `AlreadyRegistered`):

```text
ProjectNameSolution/             ← auto-scaffolded when init runs outside a solution
  ProjectNameSolution.uipx
  ProjectName/
    ProjectName.bpmn
    project.uiproj
```

If a **non-empty** directory already exists at the path you typed, init warns
and leaves it untouched — the project still lands in
`<ProjectName>Solution/<ProjectName>/`, not the existing directory.

## Generated or CLI-managed package files

- `bindings_v2.json` - resource bindings generated or enriched from BPMN and registry/connection metadata.
- `entry-points.json` - runnable start-event entry points and input/output schemas.
- `operate.json` - runtime/package metadata.
- `package-descriptor.json` - package manifest mapping generated files and BPMN content.

Treat these JSON files as derived unless a CLI contract explicitly identifies a field as user-authored. For source fixes, edit BPMN or rerun CLI enrichment rather than patching generated output by hand.

After source validation, generate the complete set with:

```bash
uip maestro bpmn \
  refresh <project-path> --output json
```

Refresh is the offline, provider-neutral source-to-derived boundary. It
regenerates all four files as one atomic set from the authored BPMN and
`project.uiproj`; it does not discover or import tenant resources. Local
packaging then consumes that generated set. In particular,
`uip maestro bpmn pack <project-path> <OutputDir> --output json` does not create
a missing descriptor from only the BPMN and `project.uiproj`.

For the regeneration and drift-check contract, see [local-metadata-regeneration-guide.md](local-metadata-regeneration-guide.md).

## Package content

Create the project with `uip maestro bpmn init` and preserve its generated
files. For solution registration and metadata ownership, see
[local-metadata-regeneration-guide.md](local-metadata-regeneration-guide.md).
Do not hand-author generated metadata.

A Process Orchestration package content folder contains:

- One or more `.bpmn` files.
- `bindings_v2.json`.
- `entry-points.json`.
- `operate.json`.
- `package-descriptor.json`.

The package descriptor's root `files` object maps the BPMN and generated JSON
files. Entry-point and operate paths use `/content/<file>.bpmn#<start-event-id>`
to identify the packaged BPMN entry point, using the root start event's unique
entry-point ID.

## Authoring boundary

Authoring owns local files and local validation. It can create or edit BPMN source, preserve existing generated files for comparison, and run validation/generation commands. It stops before upload, debug, publish, or run unless the user explicitly consents.

Operate owns cloud-side side effects: upload, publish, deploy, debug, process run, instance lifecycle, and cloud resource refresh.

Diagnose owns post-run inspection: incidents, variables, element executions, deployed assets, traces, and correlation back to BPMN element IDs.
