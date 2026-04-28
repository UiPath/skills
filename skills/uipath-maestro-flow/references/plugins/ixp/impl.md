# IxP Extraction Node — Implementation

IxP Extraction nodes invoke a published UiPath Intelligent eXtraction Platform (IxP) model. They are tenant-specific resources with pattern `uipath.ixp.{sanitized-modelName}.{sanitized-fullyQualifiedName}`.

Sanitization rule (applied to both tail segments): runs of characters outside `[a-zA-Z0-9.]` → single `-`, then lowercased. Dots are preserved. Example: `"Invoice Model"` + `"shared.invoice-model"` → `uipath.ixp.invoice-model.shared.invoice-model`. Always prefer the `nodeType` returned by `uip maestro flow registry search` over constructing one by hand.

## Discovery

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.ixp" --output json
```

Requires `uip login`. Only published IxP models from your tenant appear. Example returned `nodeType`: `uipath.ixp.invoice-model.shared.invoice-model` (for a model named "Invoice Model" with `fullyQualifiedName` `shared.invoice-model`).

### Response shape

`registry search` returns a top-level envelope; `Data` is a flat list of node entries (PascalCase keys):

```json
{
  "Result": "Success",
  "Code": "NodeSearchSuccess",
  "Data": [
    {
      "NodeType": "uipath.ixp.invoice-model.shared.invoice-model",
      "Category": "document-extraction",
      "DisplayName": "Invoice Model",
      "Description": "",
      "Version": "1.0.0",
      "Tags": "ixp, document-understanding, extraction"
    }
  ]
}
```

Read entries as `raw["Data"][i]["NodeType"]` (not `raw["Data"]["Nodes"]`).

### If `Data` is empty → stop and use a mock

If `uip maestro flow registry search "uipath.ixp"` returns `Data: []`, **no IxP extraction model is published on this tenant**. Add a `core.logic.mock` placeholder node (see [If the Model Does Not Exist Yet](#if-the-model-does-not-exist-yet)) and surface the missing model in **Open Questions**.

**Stop searching.** Do not run any of these as a fallback:

- Domain-keyword searches: `registry search "invoice"`, `"form"`, `"document"`, `"W-9"`, `"receipt"`, `"contract"`, etc. — there is no domain-named extraction node; IxP is the only extraction primitive.
- `registry list` followed by client-side filtering for "ixp" / "extraction" — the strict `uipath.ixp` search is already authoritative.
- Variant-prefix searches: `registry search "uipath.agent.resource.tool.ixp"`, `"core.ixp"`, etc.

The fallback is `core.logic.mock`, full stop. At most run one broader `registry search "ixp"` to confirm there are no `uipath.ixp.*` hits hidden by stricter prefix matching, then mock.

> A `uipath.agent.resource.tool.ixp.*` hit on the broader `"ixp"` search is the *agent-tool* variant — not a flow extraction node. Treat it as "no extraction model published" and fall back to mock.

## Registry Validation

```bash
uip maestro flow registry get "<nodeType>" --output json
```

Confirm:

- Input port: `input`
- Output port: `success` (handle id; edges target this in `.flow` JSON. `handleType` is `output`)
- `model.type` — `bpmn:ServiceTask`
- `model.serviceType` — `IXP.Extraction`
- `inputDefinition.properties` — at minimum: `modelName`, `folderKey`, `folderName`, `versionTag`, `digitizationMode`, `fileRef` (required), `pageRange`, `documentTaxonomy`, `attachment`

> `model.version: "v2"` and the `content`/`Error` entries under `model.outputs` are injected during BPMN serialization, not the manifest — they appear in the emitted `.flow` JSON (see the JSON Structure section below) but not in `registry get` output.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `model` fields.

## JSON Structure

```json
{
  "id": "extractInvoiceFields",
  "type": "uipath.ixp.invoice-model.shared.invoice-model",
  "typeVersion": "1.0.0",
  "display": { "label": "Extract Invoice Fields" },
  "inputs": {
    "modelName": "Invoice Model",
    "folderKey": "<FOLDER_GUID>",
    "folderName": "Shared",
    "versionTag": "production",
    "digitizationMode": "fileUpload",
    "fileRef": "=$vars.start.output.invoice",
    "pageRange": "",
    "documentTaxonomy": null
  },
  "outputs": {
    "content": {
      "type": "object",
      "description": "Extraction result — field values per the model's taxonomy",
      "source": "=result",
      "var": "content"
    },
    "error": {
      "type": "object",
      "description": "Error information if extraction fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "IXP.Extraction",
    "version": "v2",
    "section": "Published",
    "context": [
      { "name": "folderKey",        "type": "string", "value": "<FOLDER_GUID>" },
      { "name": "modelName",        "type": "string", "value": "Invoice Model" },
      { "name": "digitizationMode", "type": "string", "value": "fileUpload" }
    ],
    "inputs": [
      {
        "name": "input",
        "type": "json",
        "target": "bodyField",
        "body": "{\"downloadedFileOutput\":\"=$vars.start.output.invoice\"}"
      }
    ],
    "outputs": [
      { "name": "content", "type": "jsonSchema", "source": "=result", "var": "content" },
      { "name": "Error",   "type": "jsonSchema", "source": "=Error",  "var": "error"   }
    ]
  }
}
```

### `inputs.fileRef` vs `model.inputs[].body.downloadedFileOutput`

These are not two fields to keep in sync — `inputs.fileRef` is the source of truth. The file-input entry in `model.inputs[]` (`{ name: "input", target: "bodyField", body: "{\"downloadedFileOutput\": ... }" }`) is emitted automatically from `inputs.fileRef` during BPMN serialization. When swapping the upstream source, edit `inputs.fileRef` only; do **not** hand-edit the `downloadedFileOutput` body.

### Optional `model.inputs` entries

- **Page range** (when the user supplies a sub-range of pages):
  ```json
  { "name": "pageRange", "type": "string", "target": "header", "value": "1-5" }
  ```
- **Document taxonomy** (when the flow supplies a typed taxonomy for typed extraction):
  ```json
  { "name": "documentTaxonomy", "type": "jsonSchema", "target": "bodyField", "body": "<TAXONOMY_JSON>" }
  ```

### `digitizationMode` values

| Value | When to use |
| --- | --- |
| `fileUpload` | Default. The flow provides a file reference (storage key) via `fileRef`. |
| `jobAttachment` | The document arrives as an Orchestrator job attachment. Set `inputs.attachment` per the schema below. |

#### `attachment` input shape (for `jobAttachment` mode)

```json
"inputs": {
  "modelName": "Invoice Model",
  "folderKey": "<FOLDER_GUID>",
  "folderName": "Shared",
  "versionTag": "production",
  "digitizationMode": "jobAttachment",
  "attachment": {
    "ID": "=$vars.triggerNode.output.attachmentKey",
    "FullName": "=$vars.triggerNode.output.fileName",
    "MimeType": "application/pdf",
    "Metadata": {}
  }
}
```

`ID` is the only required field (the Orchestrator attachment key). `FullName`, `MimeType`, and `Metadata` are optional. Confirm the emitted BPMN against `uip maestro flow registry get` before relying on this path — workbench test coverage for `jobAttachment` is limited today, so validate end-to-end on your tenant.

## Accessing Output

The extraction result is available downstream:

```javascript
// In a Script node after the IxP node
const fields = $vars.extractInvoiceFields.content;
return {
  total: fields.invoiceTotal,
  vendor: fields.vendorName
};
```

- `$vars.{nodeId}.content` — the extraction result (field values keyed by the model's taxonomy)
- `$vars.{nodeId}.error` — error details if extraction fails

The exact keys inside `content` depend on the IxP model's trained taxonomy. Inspect the model definition on the IxP product, or run a single extraction interactively to confirm field names before wiring downstream script logic.

## If the Model Does Not Exist Yet

Trigger: `uip maestro flow registry search "uipath.ixp"` returns `Data: []`, OR the only matches are `uipath.agent.resource.tool.ixp.*` (agent-tool variant — not a flow extraction node).

Action: insert a `core.logic.mock` placeholder via Direct JSON edit and stop. Do not iterate on registry searches.

1. Fetch the definition: `uip maestro flow registry get core.logic.mock --output json`. Copy `Data.Node` verbatim into `definitions[]` if not already present.
2. Add a node to `nodes[]` with a stable id (e.g. `extractContractFieldsMock`), `type: "core.logic.mock"`, and a `display.label` describing the extraction step in the user's domain (e.g. "Extract Contract Fields (mock — IxP model not yet published)") — not "IxP".
3. Add a `layout.nodes` entry at `position: { x: 400, y: 144 }`, size `96x96`.
4. Wire edges per the parent [flow-editing-operations.md](../../flow-editing-operations.md) guide. `core.logic.mock` is a no-op pass-through — no `inputs`, no `outputs` block, no `bindings_v2.json` changes.
5. Run `uip maestro flow validate <ProjectName>.flow --output json` once after all edits complete.

Surface the missing model in the **Open Questions** section of the architectural plan: the user must train and publish the IxP extraction model via the IxP product before the flow can run. After publishing, follow the [mock replacement procedure](../../flow-editing-operations-json.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real IxP node.

## Classifier Variant

IxP also exposes classifier models (type `Classifier`) that label documents rather than extracting named fields. Classifier models share the `uipath.ixp.*` node-type pattern but produce a different `content` shape. **Classifier configuration is not covered in this file** — if the user needs classification, flag it as a prerequisite and defer to a future revision of this impl.md.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Model not published, or registry cache stale | Run `uip login` then `uip maestro flow registry pull --force` |
| `model.context` rejected by runtime | `folderKey`, `modelName`, or `digitizationMode` missing from the context array | Confirm all three entries are present; they mirror the values in `inputs` |
| Empty `$vars.{nodeId}.content` | Model's taxonomy doesn't match the document, or extraction silently returned no fields | Inspect the raw API response via `$vars.{nodeId}.error` first; if no error, run the extraction against the same document on the IxP product UI to compare |
| `fileRef` not resolving | Expression references an upstream variable that isn't wired, or the upstream node didn't produce a file output | Verify the upstream node exports a file reference and that the `=$vars.{upstreamId}.output.<field>` expression matches |
| `digitizationMode: jobAttachment` fails | `attachment.ID` missing | Ensure the flow populates `attachment.ID` with the Orchestrator job attachment key |
| Extraction failed | Underlying IxP model errored (unsupported MIME type, corrupted file, service-side failure) | Check `$vars.{nodeId}.error.detail` for the IxP service response |
| `uip maestro flow node configure` rejects with "not a connector type node" | Expected — IxP is not a connector. | Edit `inputs.*` in the `.flow` JSON directly. |
