# CLI Conventions

The BPMN skill assumes a split boundary: model-authored BPMN source plus CLI validation, enrichment, packaging, and cloud lifecycle.

## Output parsing

When a CLI result is parsed programmatically, request JSON output. If the command does not support JSON output yet, do not scrape human text silently; report that the command is not machine-readable and keep the next step manual or advisory.

## Side-effect boundary

Local validation, registry discovery, static inspection, and package dry-run style commands are authoring-safe. Upload, publish, deploy, debug, process run, instance lifecycle, and cloud resource mutation are operate actions and require explicit user consent.

## Login boundary

Authoring should work without login for local source edits and static validation. Registry-backed discovery, Integration Service enrichment, resource refresh, upload, debug, publish, process inspection, and run diagnosis may require login.

## Integration Service enrichment

For Integration Service nodes and triggers, use CLI or registry-backed tooling to:

- Resolve connector and operation metadata.
- Bind a selected connection.
- Generate or enrich `uipath:activity` / `uipath:event` XML.
- Generate `bindings_v2.json` resources.
- Generate dynamic input and output schemas.
- Validate required context/input fields.

If enrichment tooling is unavailable, leave the element as a draft intent and record the open question. Do not hand-author connection IDs or private resource metadata.

## Local metadata regeneration

When BPMN source changes, regenerate or verify local package metadata before cloud actions. The derived files are `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json`; the BPMN source and registry-backed enrichment inputs are authoritative. Follow [local-metadata-regeneration-guide.md](local-metadata-regeneration-guide.md) for entry point schema, binding resource, and `Intsvc.*` payload drift checks.

## Validation before operate

Before upload, debug, publish, or deploy, run the available local checks for:

- BPMN XML parse.
- Diagram presence and geometry.
- UiPath extension structure.
- Entry point extraction.
- Binding reference resolution.
- Generated package file consistency.
- Integration Service enrichment completeness.

Warnings about CLI-owned fields are blockers when the affected element will execute in a real run.
