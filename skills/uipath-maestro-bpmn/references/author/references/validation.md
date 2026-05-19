# Validation

Run validation after the local BPMN edit is coherent. Do not chase every intermediate invalid state while creating nodes and flows.

## Local checks

Validate these before Operate:

- The pass 1 skeleton has been confirmed or the edit is small and explicitly summarized.
- A pass 1 skeleton uses business-readable conditions rather than runtime
  `=vars.<variableId>` expressions for variables that do not exist until pass 2.
- BPMN XML parses with the UiPath extension descriptor.
- At least one valid diagram and plane exists.
- Diagram plane references an existing root process, collaboration, or subprocess.
- Every rendered node has a shape and every rendered edge has waypoints.
- Root variables, bindings, migration metadata, and transaction markers are structurally valid.
- New root variables use `uipath:input`, `uipath:inputOutput`, or
  `uipath:output`; generic `uipath:variable direction="..."` appears only when
  preserving imported XML.
- Entry point IDs are unique and appear on root-level start events.
- Entry point input variables use an `elementId` matching the start event.
- Binding expressions in context values resolve to root bindings.
- Required context/input fields are present for documented service types.
- Sequence flows connect legal source and target types.
- Message flows do not connect elements inside the same pool.
- Message event definitions reference declared `bpmn:message` elements.
- Gateway splits have valid conditions/defaults.
- Each scope has at most one blank start event.
- Event subprocesses have exactly one start event.
- Boundary error events and error event subprocesses reference valid error definitions.
- Boundary events own their exception outgoing flows; attached activities do
  not list boundary exception flows as normal incoming/outgoing flows.
- Multi-instance collection and item bindings reference declared variables and use explicit sequential/parallel metadata.
- Expressions avoid assignment operators in fields that require read-only expression evaluation.
- Output mappings target declared variables.
- CLI-owned Integration Service fields have been enriched or are clearly marked as blockers.

For local-only authoring, always execute at least one validation command before
packaging. The current local CLI validator expects a BPMN/XML file path, so use
the main source file:

```bash
uip maestro bpmn validate ProjectName/ProjectName.bpmn --output json
```

Only validate a project directory if the installed CLI explicitly supports that
shape. If the installed CLI does not expose validation, run an explicit XML
parse command against the BPMN source, for example:

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('ProjectName/ProjectName.bpmn')"
```

Do not treat reading the file or visually inspecting generated metadata as a
validation step; the validation command must run and succeed before `pack`.

## Package checks

Before executing `uip maestro bpmn pack`, ensure the project directory contains
`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, and
`package-descriptor.json`. If any generated file is missing, regenerate it or
write the placeholder-safe local-only shape from
[shared/local-metadata-regeneration-guide.md](../../shared/local-metadata-regeneration-guide.md)
before packing.

When generated package files exist, verify that:

- `bindings_v2.json` matches root bindings and enriched resource metadata.
- `entry-points.json` matches root start events, entry point IDs, and variable schemas.
- `operate.json` points at the intended main BPMN file and content type.
- `package-descriptor.json` includes the BPMN and generated JSON files under content.

Use [shared/local-metadata-regeneration-guide.md](../../shared/local-metadata-regeneration-guide.md) when a mismatch requires local regeneration or Integration Service enrichment.

## Result handling

- Blocking errors must be fixed before upload, publish, debug, or run.
- Warnings may be acceptable for local drafts, but warnings about CLI-owned executable elements are blockers for real runs.
- If validation tooling is missing, report the exact checks that could not run and keep the project in Author state.
- If Integration Service enrichment is unavailable, validation can pass only for source shape review; do not report the project as ready for Operate.

## Implementation status summary

When handing off to Operate or reporting completion, classify each external,
resource-backed, HTTP, human, child-process, or script-enrichment node:

- **Executable** - the node has concrete runtime metadata, declared input/output
  variables, mappings to downstream variables, and no unresolved placeholder.
- **Draft** - the BPMN shape and intent are present, but runtime metadata,
  binding, schema, or enrichment is unresolved.
- **Mock** - the node returns fixed sample data or bypasses the real external
  action.
- **Blocked** - required user, tenant, connection, schema, URL, or credential
  information is missing.

Do not use "fully implemented" for a process that contains draft, mock, or
blocked nodes. Name those nodes explicitly and state what is still required.
