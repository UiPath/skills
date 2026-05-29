# IxP Extraction Node — Implementation

IxP Extraction nodes invoke a published UiPath Intelligent eXtraction Platform (IxP) model. They are tenant-specific resources with pattern `uipath.ixp.{sanitized-modelName}.{sanitized-fullyQualifiedName}`.

Sanitization rule (applied to both tail segments, in this order):

1. Lowercase.
2. Replace runs of any character outside `[a-z0-9]` with a single `-`. Slashes, spaces, underscores, and runs of dashes (e.g. `---`) all collapse to a single `-`. Dots in the FQN are NOT preserved — they also collapse to `-`.

The dot in `uipath.ixp.{model}.{fqn}` is the segment separator the registry adds *after* sanitizing each tail segment, not part of the sanitization itself.

Examples (verified against the live registry):

- `"birth_certificates_oob-6252526a-ixp"` + FQN `Shared/birth_certificates_oob-6252526a-ixp` → `uipath.ixp.birth-certificates-oob-6252526a-ixp.shared-birth-certificates-oob-6252526a-ixp` (underscores and slash both → `-`).
- `"idp-benchmark---invoices-c735405a-ixp"` + FQN `Shared/idp-benchmark---invoices-c735405a-ixp` → `uipath.ixp.idp-benchmark-invoices-c735405a-ixp.shared-idp-benchmark-invoices-c735405a-ixp` (run of `---` → single `-`).

Always prefer the `nodeType` returned by `uip maestro flow registry search` over constructing one by hand.

## Discovery

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.ixp" --output json
```

Requires `uip login`. Only published IxP models from your tenant appear. Example returned `nodeType`: `uipath.ixp.idp-benchmark-invoices-c735405a-ixp.shared-idp-benchmark-invoices-c735405a-ixp` (for an `idp-benchmark---invoices-c735405a-ixp` model in the `Shared` folder).

### Response shape

`registry search` returns a top-level envelope; `Data` is a flat list of node entries (PascalCase keys):

```json
{
  "Result": "Success",
  "Code": "NodeSearchSuccess",
  "Data": [
    {
      "NodeType": "uipath.ixp.idp-benchmark-invoices-c735405a-ixp.shared-idp-benchmark-invoices-c735405a-ixp",
      "Category": "document-processing",
      "DisplayName": "idp-benchmark---invoices-c735405a-ixp",
      "Description": "(Shared)",
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

## Listing Published Models

When the user is working with a Maestro flow and asks what IxP models are available — "what IxP models can I access in Maestro?", "what IxP models / runtime projects can I use in this flow?", "what document extractors can I add here?", "list published extractors", "what extraction nodes are in the registry?" — answer with the same registry search **from the `uipath-maestro-flow` Skill**, not by switching to the `uipath-ixp` Skill (`uip ixp projects ...` lists IxP-product projects, not what is wired up for Maestro). Each `Data[]` entry corresponds to one published model (a.k.a. runtime project) visible to the flow registry on this tenant.

```bash
uip login status --output json                              # confirm auth — without login, tenant IxP nodes are hidden
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.ixp" --output json
```

Parse `Data[].DisplayName`, `Data[].NodeType`, and `Data[].Version` and present them as a table. Example:

| Model (DisplayName) | NodeType | Version |
| --- | --- | --- |
| idp-benchmark---invoices-c735405a-ixp | `uipath.ixp.idp-benchmark-invoices-c735405a-ixp.shared-idp-benchmark-invoices-c735405a-ixp` | `1.0.0` |

Rules for the listing path:

- **Do NOT scaffold a solution, run `uip maestro flow init`, or write a `.flow` file.** Listing is read-only Q&A.
- **Do NOT mock.** If `Data: []`, answer directly: no IxP models are published on this tenant. The `core.logic.mock` fallback is for build-time planning, not for listing-time Q&A.
- **Do NOT log in for the user.** If `uip login status` shows logged-out, tell the user to run `uip login` and stop — listing without auth returns OOTB-only results and is misleading.
- **Do NOT search by `"runtime"`, `"document extractor"`, `"extractor"`, or `"IXP"` (uppercase).** These return empty results or agent-tool variants — not extraction nodes. Use `"uipath.ixp"` (lowercase) only.
- **Do NOT use `uip maestro flow process list` or any Orchestrator folder iteration.** `flow process list` enumerates *deployed flow process instances* (with `--folder-key`), not published models. Listing published IxP models always goes through `registry search "uipath.ixp"`.
- **Do NOT guess `uip maestro flow list-*` or `uip maestro ixp list-*` subcommands.** None exist. The CLI returns `unknown command 'list-...'` and there is no fallback path to pursue. <!-- uip-check-skip -->

## Registry Validation

```bash
uip maestro flow registry get "<nodeType>" --output json
```

Confirm:

- `category` — `document-processing` (older `document-extraction` enum was renamed; current registry serves `document-processing`)
- Input port: `input`
- Output ports: `success` and `error` (the `error` port is gated by `inputs.errorHandlingEnabled`; manifest sets `supportsErrorHandling: true`). Edges target these handle IDs in `.flow` JSON; `handleType` is `output`.
- `model.type` — `bpmn:ServiceTask`. `model.serviceType` — `IXP.Extraction`. The manifest's `model` is two fields only (`type`, `serviceType`) — no `context`, no `version`. Both are injected by the BPMN serializer at compile time.
- `form.id` — `ixp-standalone-form`. Three sections: `ixp-model` (Configuration), `ixp-file-upload` (File input), `schema-definition` (Schema definition — a single custom field `inputs.model` rendered by the `ixp-model-taxonomy` component).
- `inputDefinition.properties` — `model` (object), `modelName`, `projectName`, `projectId`, `versionTag`, `folderKey`, `folderName`, `fileRef`, `pageRange`, `attachmentConfig`, `guardrails`, `attachment`. `inputDefinition.required` — `["fileRef"]`.
- `inputDefaults` — carries the full `model` metadata blob plus flat `modelName` / `projectName` / `folderKey` / `folderName` mirrors. The blob shape is `{ modelName, fullyQualifiedName, description, folderKey, folderName }` plus DU-API extras (`kind`, `type`, `detailsUrl`, `asyncDigitizationUrl`, `asyncExtractionUrl`).
- `outputDefinition` — populated. `output` carries the full extraction-result JSON schema; `error` carries the standard error envelope.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs` and `outputs` fields. Author CAPABILITY rule #15 (no top-level `model` block on the instance) and rule #14 (`outputs` populated for nodes that produce data) both apply.

## JSON Structure

The IxP node instance carries `inputs` and `outputs` — and **no top-level `model` block**. The slim manifest `model` (`{ type, serviceType }`) lives only in `definitions[]`; the runtime `model.context` / `model.version` / `model.inputs` / `model.outputs` envelope is injected by the BPMN serializer at compile time.

### Build procedure — copy from `registry get`, do not construct from memory

The IxP node instance is **derived from the registry response**, not authored from scratch. Any IxP node built from training-data recall will hit at least one of: missing `inputs.model` (canvas crash), missing `outputs.error` (broken `$vars` resolution), legacy forbidden fields (silent schema drift).

Run this once and source every field below from the response:

```bash
uip maestro flow registry get "<nodeType>" --output json > <tmpfile>.json
```

Then assemble the instance by copying these paths verbatim:

| Instance field | Source path in `registry get` response | Required |
| --- | --- | --- |
| `inputs.model` (full object) | `Data.Node.inputDefaults.model` | **YES** — undefined → canvas crash |
| `inputs.modelName` | `Data.Node.inputDefaults.modelName` | YES |
| `inputs.projectName` | `Data.Node.inputDefaults.projectName` | YES |
| `inputs.folderKey` | `Data.Node.inputDefaults.folderKey` | YES |
| `inputs.folderName` | `Data.Node.inputDefaults.folderName` | YES |
| `inputs.versionTag` | `""` (empty string unless pinning a version) | YES |
| `inputs.pageRange` | `""` (empty string for full document) | YES |
| `inputs.fileRef` | `"=js:$vars.<upstream>.output.<field>"` (author this) | YES |
| `outputs.output` (full object) | `Data.Node.outputDefinition.output` | **YES** — missing → `$vars.<id>.output` fails |
| `outputs.error` (full object) | `Data.Node.outputDefinition.error` | **YES** — missing → `$vars.<id>.error` fails |

**Forbidden in `inputs`** (legacy schema, removed from current standalone node — including any of these is a defect even if `flow validate` passes):

- `digitizationMode` — serializer defaults to `fileUpload` internally
- `documentTaxonomy` — replaced by `inputs.model` blob
- `attachmentId` — use `inputs.attachment` for Orchestrator job attachments instead
- `fileName` — derived from `fileRef` upstream
- `mimeType` — derived from `fileRef` upstream

If you find yourself typing any of those five field names while authoring an IxP node, stop and re-read this section.

### Final shape

```json
{
  "id": "extractInvoiceFields",
  "type": "uipath.ixp.invoice-model.shared-invoice-model",
  "typeVersion": "<typeVersion from `registry get` response>",
  "display": { "label": "Extract Invoice Fields" },
  "inputs": {
    "model": {
      "modelName": "Invoice Model",
      "description": "",
      "kind": "Extractor",
      "type": "IXP",
      "fullyQualifiedName": "Shared/invoice-model",
      "detailsUrl": "https://<tenant>.uipath.com/.../models/invoice-model?api-version=2.0",
      "asyncDigitizationUrl": "https://<tenant>.uipath.com/.../models/invoice-model/digitization/start?api-version=2.0",
      "asyncExtractionUrl": "https://<tenant>.uipath.com/.../models/invoice-model/extraction/start?api-version=2.0",
      "folderKey": "<FOLDER_GUID>",
      "folderName": "Shared"
    },
    "modelName": "Invoice Model",
    "description": "",
    "projectName": "Invoice Model",
    "versionTag": "",
    "folderKey": "<FOLDER_GUID>",
    "folderName": "Shared",
    "fileRef": "=js:$vars.start.output.invoice",
    "pageRange": ""
  },
  "outputs": {
    "output": { /* copy verbatim from definition.outputDefinition.output */ },
    "error":  { /* copy verbatim from definition.outputDefinition.error */ }
  }
}
```

### Authoring rules

1. **`inputs.model` MUST be present and MUST be the full blob from `Data.Node.inputDefaults.model`.** Copy verbatim — do not synthesize, do not abbreviate, do not omit the DU-API extras (`detailsUrl`, `asyncDigitizationUrl`, `asyncExtractionUrl`, `kind`, `type`). The `schema-definition` form section binds `inputs.model` to the `ixp-model-taxonomy` custom component, which destructures `modelName` and `folderKey` out of it. If `inputs.model` is undefined, clicking the node in Studio Web crashes the property panel with `Cannot destructure property 'modelName' of 't' as it is undefined` — and `flow validate` does not catch it.
2. **Flat mirrors stay alongside `inputs.model`.** `modelName`, `projectName`, `folderKey`, `folderName` are surfaced as disabled text fields in the `ixp-model` form section and are read directly from `inputs.*`, not from `inputs.model.*`.
3. **`fileRef` is the only schema-required input** (`inputDefinition.required: ["fileRef"]`). Use `=js:$vars.<upstream>.output.<field>` per Critical Rule #13.
4. **`outputs.output` AND `outputs.error` MUST both be present**, copied verbatim from `Data.Node.outputDefinition.output` and `Data.Node.outputDefinition.error`. Omitting either breaks downstream `$vars.<nodeId>.output` / `.error` resolution and hides the field in Studio Web's variable picker. `flow validate` does not catch the omission.
5. **No top-level `model` on the instance.** Studio Web–authored .flow files never carry one; the BPMN-format `model` envelope (with `context`, `version`, `inputs`, `outputs`) is emitted at serialize time only.
6. **`inputs` MUST NOT contain `digitizationMode`, `documentTaxonomy`, `attachmentId`, `fileName`, or `mimeType`.** These five fields were on a prior schema and have been removed from the standalone IxP node. Including them is the most common training-data-recall mistake. The serializer defaults `digitizationMode` to `fileUpload` internally — there is no scenario where you should set it on the instance.

The `definitions[]` entry is copied verbatim from `registry get` (`Data.Node`). Critical Rule #7 applies unchanged.

> **`uip maestro flow validate` enforces the Authoring rules above** via the `ixp-node` validator. Failures surface as `severity: "error"` issues with `path` like `nodes[<nodeId>].inputs.model` and a self-contained `message` describing the violation — fix the `.flow` file, not the validator. The registry's `inputDefinition.properties` is the schema of the property catalog, not a license to override the rules: `digitizationMode`, `documentTaxonomy`, `attachmentId`, `fileName`, and `mimeType` are NOT returned by `registry get` and must not be set on the instance.

### `inputs.fileRef` vs the emitted `model.inputs[]` body

`inputs.fileRef` is the source of truth. At BPMN serialize time, `packages/services/src/serialization/uipath-extension.ts:handleIxpExtraction` wraps the value into a `model.inputs[]` entry with target `bodyField` and body `{"downloadedFileOutput": <fileRef>}`. Edit `inputs.fileRef` only; never hand-edit the BPMN body.

### Optional `attachment` input (Orchestrator job attachments)

`inputDefinition.properties.attachment` accepts `{ ID, FullName, MimeType, Metadata }` for flows that consume Orchestrator job attachments. There is no form UI for this path on the standalone node today — set it programmatically in `inputs.attachment` if needed. `ID` is the only required field. Validate end-to-end on your tenant before relying on this path.

## Accessing Output

The extraction result is stored at `$vars.{nodeId}.output`. The IxP node's BPMN serializer maps the extraction service's `result` field directly to this variable (`source: '=result'`), so **the `result` wrapper is stripped** — `output` IS the extraction-result object, with no further wrapping.

Top-level keys of `$vars.{nodeId}.output`:

- `ExtractionResult` — `{ DocumentId, ResultsVersion, ResultsDocument }`. `ResultsDocument.Fields[]` carries the trained model's extracted values; `ResultsDocument.Tables[]` carries tabular extractions.
- `ExtractorPayloads` — provider-specific raw payloads.
- `BusinessrulesResults[]` — business-rule evaluation results, when configured.

Each `Fields[]` element is shaped:

```json
{
  "FieldId": "string",
  "FieldName": "string",
  "FieldType": "string",
  "IsMissing": false,
  "Values": ["string"],
  "Confidence": 95
}
```

Read field values via `find` against `FieldName`, then index into `Values[]`:

```javascript
// In a Script node after the IxP node
const fields = $vars.extractInvoiceFields.output.ExtractionResult.ResultsDocument.Fields || [];
const total = fields.find(f => f.FieldName === 'invoiceTotal')?.Values?.[0];
const vendor = fields.find(f => f.FieldName === 'vendor')?.Values?.[0];
return { total, vendor };
```

Sibling error variable: `$vars.{nodeId}.error` — populated when extraction fails *and* the `error` port is wired (`supportsErrorHandling: true`). Mapped from the service response's `Error` field (`source: '=Error'`).

### Wrong shapes the agent tends to invent

These all pass `flow validate` and fail silently at runtime:

- **Wrong:** `output.result.ExtractionResult.…` — there is no `result` wrapper at runtime; `=result` strips it before the value is assigned to `output`.
- **Wrong:** `output.<fieldName>` flat — extracted fields are not top-level properties of `output`; they live under `output.ExtractionResult.ResultsDocument.Fields[]` and are keyed by `FieldName`.
- **Wrong:** `output.ExtractionResult.Fields` — `Fields[]` is two levels under `ExtractionResult` (`output.ExtractionResult.ResultsDocument.Fields`), not one.

Studio Web's variable picker renders `output.ExtractionResult` as opaque and does NOT surface the nested `ResultsDocument.Fields[]` shape. The path above is the source of truth — copy it from this doc, not from picker autocomplete or `outputDefinition.output.schema` (the registry schema describes the pre-`=result` wrapper, not the runtime variable).

### Trained-model field taxonomy

The `FieldName` values present in `ResultsDocument.Fields[]` depend on the trained IxP model's taxonomy and are NOT exposed through `uip maestro flow registry get` (the registry's `outputDefinition.output.schema` describes the wrapper envelope shape, not the per-model trained fields). Get them from the deployment:

```bash
uip ixp deployments get-taxonomy --folder-key <folderKey> "<modelName>" --output json
```

Both args come from the `registry get` response you already fetched in [Build procedure](#build-procedure--copy-from-registry-get-do-not-construct-from-memory): `--folder-key` ← `Data.Node.inputDefaults.folderKey`; `<modelName>` (positional) ← `Data.Node.inputDefaults.modelName`. No additional discovery step. Requires `uip login`; the command uses the user Bearer to call the same DU-App route that Studio Web's "Schema definition" panel uses.

Response shape:

```json
{
  "documentTaxonomy": {
    "documentTypes": [
      {
        "fields": [
          {
            "fieldId": "string",
            "fieldName": "string",
            "type": "Text",
            "components": []
          }
        ]
      }
    ]
  }
}
```

`type` is one of `Text`, `Date`, `Number`, `Set`, `FieldGroup`. `components[]` is populated only when `type` is `FieldGroup` and carries sub-fields with the same shape recursively.

**camelCase → PascalCase translation.** The taxonomy response uses `fieldName` (camelCase); runtime `Fields[]` elements use `FieldName` (PascalCase). The string *contents* match — design-time `"Birth Date"` is `FieldName: "Birth Date"` at runtime — but the wrapper key changes case. Translate the key, not the value, when going from `get-taxonomy` output to runtime `Fields[].FieldName` lookups.

Agent call sequence:

1. `uip maestro flow registry search "uipath.ixp" --output json` — list IxP nodes.
2. `uip maestro flow registry get "<nodeType>" --output json` — read `Data.Node.inputDefaults.{folderKey, modelName}` (already done as part of [Build procedure](#build-procedure--copy-from-registry-get-do-not-construct-from-memory)).
3. `uip ixp deployments get-taxonomy --folder-key <folderKey> "<modelName>" --output json` — read `documentTaxonomy.documentTypes[].fields[].fieldName`.
4. Author downstream consumers with `$vars.<id>.output.ExtractionResult.ResultsDocument.Fields.find(f => f.FieldName === '<fieldName from step 3>')?.Values?.[0]`.

If the command fails (login expired, deployment not yet published, transient failure), fall back to defensive `find`-by-`FieldName` patterns with assumed field names and surface the assumptions to the user under **Open Questions**. Do NOT substitute a one-off extraction or IxP-product-UI inspection in the agent loop — `get-taxonomy` is the agent-loop path.

## If the Model Does Not Exist Yet

Trigger: `uip maestro flow registry search "uipath.ixp"` returns `Data: []`, OR the only matches are `uipath.agent.resource.tool.ixp.*` (agent-tool variant — not a flow extraction node).

Action: insert a `core.logic.mock` placeholder via Direct JSON edit and stop. Do not iterate on registry searches.

1. Fetch the definition: `uip maestro flow registry get core.logic.mock --output json`. Copy `Data.Node` verbatim into `definitions[]` if not already present.
2. Add a node to `nodes[]` with a stable id (e.g. `extractContractFieldsMock`), `type: "core.logic.mock"`, and a `display.label` whose **leading phrase** describes the work in the user's domain (e.g. `Extract Contract Fields`) rather than the underlying technology (`IxP Extraction`, `Run IxP`). The parenthetical may name IxP — e.g. `Extract Contract Fields (mock — IxP model not yet published)`.
3. Add a `layout.nodes` entry at `position: { x: 400, y: 144 }`, size `96x96`.
4. Wire edges per the parent [editing-operations.md](../../editing-operations.md) guide. `core.logic.mock` is a no-op pass-through — no `inputs`, no `outputs` block, no `bindings_v2.json` changes.
5. **Wire downstream consumers against the mock with `$vars` references, not static values.** Scripts, decisions, and end-node mappings that follow the mock MUST reference `$vars.{mockNodeId}.output` (the mock's only port) instead of hard-coded returns. Example: a script that summarises the (future) extraction writes `return { vendor: $vars.extractInvoiceFieldsMock.output.vendorName };`, not `return { ok: "OK" };`. This keeps the **node-graph** swap-ready — node IDs, edge shapes, and the `output` port name stay intact when the mock is replaced. **Field-access paths inside downstream scripts WILL need rewriting at swap time** — the real IxP `output` is shaped as `{ ExtractionResult: { ResultsDocument: { Fields: [...] } } }` (see [Accessing Output](#accessing-output)), so flat-field accessors against the mock become structured `Fields.find(f => f.FieldName === '<name>')?.Values?.[0]` lookups against the real node. Surface the post-swap rewrite as a follow-up under **Open Questions**.
6. Run `uip maestro flow validate <ProjectName>.flow --output json` once after all edits complete.

Surface the missing model in the **Open Questions** section of the architectural plan: the user must train and publish the IxP extraction model via the IxP product before the flow can run. After publishing, follow the [mock replacement procedure](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node) to swap the mock for the real IxP node.

## Classifier Variant

IxP also exposes classifier models (type `Classifier`) that label documents rather than extracting named fields. Classifier models share the `uipath.ixp.*` node-type pattern but produce a different `output` shape (classification labels, not field values). **Classifier configuration is not covered in this file** — if the user needs classification, flag it as a prerequisite and defer to a future revision of this impl.md.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Model not published, or registry cache stale | Run `uip login` then `uip maestro flow registry pull --force` |
| `model.context` rejected by runtime | `folderKey` or `modelName` missing from `inputs` (the context array is built from these) | Confirm `inputs.modelName` and `inputs.folderKey` are populated. |
| Empty `$vars.{nodeId}.output` | Model's taxonomy doesn't match the document, or extraction silently returned no fields | Inspect the raw API response via `$vars.{nodeId}.error` first; if no error, run the extraction against the same document on the IxP product UI to compare |
| `fileRef` not resolving | Expression references an upstream variable that isn't wired, or the upstream node didn't produce a file output | Verify the upstream node exports a file reference and that the `=js:$vars.{upstreamId}.output.<field>` expression matches |
| Extraction failed | Underlying IxP model errored (unsupported MIME type, corrupted file, service-side failure) | Check `$vars.{nodeId}.error.detail` for the IxP service response |
| `uip maestro flow node configure` rejects with "not a connector type node" | Expected — IxP is not a connector. | Edit `inputs.*` in the `.flow` JSON directly. |
| Studio Web: "Cannot destructure property 'modelName' of 't' as it is undefined" when clicking the node | `inputs.model` blob is missing or undefined. The `schema-definition` form section binds `inputs.model` to the `ixp-model-taxonomy` component, which destructures `modelName` and `folderKey` out of it. When `inputs.model` is missing, the destructure throws. | Copy `definition.inputDefaults.model` verbatim into the node instance's `inputs.model`. The blob carries `modelName`, `fullyQualifiedName`, `description`, `folderKey`, `folderName` plus DU-API extras (`kind`, `type`, `detailsUrl`, `asyncDigitizationUrl`, `asyncExtractionUrl`). See [JSON Structure](#json-structure). |
