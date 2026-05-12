# Validation

Run validation after the local BPMN edit is coherent. Do not chase every intermediate invalid state while creating nodes and flows.

## Local checks

Validate these before Operate:

- The pass 1 skeleton has been confirmed or the edit is small and explicitly summarized.
- BPMN XML parses with the UiPath extension descriptor.
- At least one valid diagram and plane exists.
- Diagram plane references an existing root process, collaboration, or subprocess.
- Every rendered node has a shape and every rendered edge has waypoints.
- Root variables, bindings, migration metadata, and transaction markers are structurally valid.
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
- Multi-instance collection and item bindings reference declared variables and use explicit sequential/parallel metadata.
- Expressions avoid assignment operators in fields that require read-only expression evaluation.
- Output mappings target declared variables.
- CLI-owned Integration Service fields have been enriched or are clearly marked as blockers.

For local-only authoring, always execute at least one validation command before
packaging. Prefer `uip maestro bpmn validate <ProjectDir> --output json` when
the installed CLI exposes it. If the installed CLI does not expose validation,
run an explicit XML parse command against the BPMN source, for example:

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('ProjectName/ProjectName.bpmn')"
```

Do not treat reading the file or visually inspecting generated metadata as a
validation step; the validation command must run and succeed before `pack`.

## Package checks

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
