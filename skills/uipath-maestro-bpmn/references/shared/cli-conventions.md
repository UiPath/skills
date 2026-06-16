# CLI Conventions

This skill assumes a split boundary: the model authors BPMN source and its diagram; the `uip` CLI owns registry discovery, Integration Service enrichment, local validation, and packaging.

## Output parsing

When a CLI result is parsed programmatically, request JSON output (`--output json`). If a command does not support JSON output, do not scrape human text silently — report that the command is not machine-readable and keep the next step manual or advisory.

## Login boundary

Authoring works without login for local source edits and a well-formed-XML parse. Registry-backed discovery, Integration Service enrichment, and connection listing require login (`uip login`). Without login, only built-in (OOTB) extension types are available from the registry; connectors and Orchestrator processes are not discoverable.

## Integration Service enrichment

For `Intsvc.*` connector nodes and triggers, use `uip maestro bpmn registry get <type> --connection-id <id> --object-name <obj> --output json` to:

- Resolve the connector / operation metadata and live object field shapes (`ISEnrichment`).
- Write input/output expressions against the real fields.

The connection itself is bound through the template's `value="=bindings.{bindingId}"` and a `uipath:Bindings` entry holding the discovered connection ID. If enrichment is unavailable, leave the node as a draft intent and record the open question — do not hand-author connection IDs or private resource metadata.

## Side-effect boundary (authoring scope only)

Registry discovery, IS enrichment, the bundled validator, an XML parse, and local `pack` are authoring-safe. Upload, publish, deploy, debug, process run, and instance lifecycle are **out of scope** for this skill — do not invoke them.
