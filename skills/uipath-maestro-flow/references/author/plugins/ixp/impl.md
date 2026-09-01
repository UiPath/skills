# IxP Extraction Node — Implementation

IxP Extraction nodes invoke published tenant-specific UiPath Intelligent eXtraction Platform (IxP) models. Their node type is `uipath.ixp.{sanitized-modelName}.{sanitized-fullyQualifiedName}`. Sanitize both tail segments in order: lowercase, then replace each run of characters outside `[a-z0-9]` with one `-`; slashes, spaces, underscores, dots, and dash runs collapse to `-`. The registry adds the separators. Always use the `nodeType` returned by `uip maestro flow registry search`, never construct it manually.

## Discovery and listing

For Maestro-flow questions about available IxP models, runtime projects, document extractors, or extraction nodes, use the `uipath-maestro-flow` Skill's registry search, not the `uipath-ixp` Skill. `uip ixp projects ...` lists IxP-product projects, not models wired into the Maestro flow registry. Each `Data[]` entry is one published model/runtime project visible to the flow registry.

Run:

```bash
uip login status --output json
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.ixp" --output json
```

For build-time discovery, run `uip login` first when needed. Parse the PascalCase envelope's flat `Data` list as `raw["Data"][i]["NodeType"]`, not `raw["Data"]["Nodes"]`:

```json
{
  "Result": "Success",
  "Code": "NodeSearchSuccess",
  "Data": [
    {
      "NodeType": "uipath.ixp.<sanitized-model>.<sanitized-fqn>",
      "Category": "document-processing",
      "DisplayName": "<model>",
      "Description": "(Shared)",
      "Version": "1.0.0",
      "Tags": "ixp, document-understanding, extraction"
    }
  ]
}
```

Search only lowercase `"uipath.ixp"`. Do not use domain-keyword searches (`"invoice"`, `"form"`, `"document"`, `"W-9"`, `"receipt"`, `"contract"`, etc.), `registry list` with client-side filtering, `"runtime"`, `"document extractor"`, `"extractor"`, uppercase `"IXP"`, or variant-prefix searches such as `"uipath.agent.resource.tool.ixp"` and `"core.ixp"`. At most, run one broader `registry search "ixp"` to confirm that no `uipath.ixp.*` result is hidden by prefix matching. A `uipath.agent.resource.tool.ixp.*` result is an agent-tool variant, not a flow extraction node; treat it as no published extraction model.

If `uip login status` reports logged out, tell the user to run `uip login` and stop; unauthenticated results may be OOTB-only and misleading. Do not log in for the user. Do not use `uip maestro flow process list` or Orchestrator-folder iteration; they enumerate deployed flow process instances, not published models. Do not guess `uip maestro flow list-*` or `uip maestro ixp list-*` commands; none exist and there is no fallback. <!-- uip-check-skip -->

For listing-only Q&A, present `Data[].DisplayName`, `Data[].NodeType`, and `Data[].Version`:

| Model (DisplayName) | NodeType | Version |
| --- | --- | --- |
| `<DisplayName>` | `<NodeType>` | `<Version>` |

Listing is read-only: do not scaffold, run `uip maestro flow init`, write a `.flow` file, or mock. If `Data: []`, answer that no IxP models are published on the tenant. Mocking is only for build-time planning.

If `Data: []` for build-time work, stop searching, use `core.logic.mock` as described in [If the Model Does Not Exist Yet](#if-the-model-does-not-exist-yet), and surface the missing model in **Open Questions**.

## Registry validation

Run:

```bash
uip maestro flow registry get "<node-type>" --output json
```

Confirm that:

- `category` is `document-processing` (`document-extraction` is the old enum).
- The input port is `input`; output ports are `success` and `error`. `error` is gated by `inputs.errorHandlingEnabled`; the manifest has `supportsErrorHandling: true`. `.flow` edges target these handle IDs and use `handleType: "output"`.
- `model.type` is `bpmn:ServiceTask` and `model.serviceType` is `IXP.Extraction`. The manifest `model` has only `type` and `serviceType`; it has no `context` or `version`, which the BPMN serializer injects.
- `form.id` is `ixp-standalone-form`; sections are `ixp-model` (Configuration), `ixp-file-upload` (File input), and `schema-definition` (Schema definition, one custom `inputs.model` field rendered by `ixp-model-taxonomy`).
- `inputDefinition.properties` includes `model` (object), `modelName`, `projectName`, `projectId`, `versionTag`, `folderKey`, `folderName`, `fileRef`, `pageRange`, `attachmentConfig`, `guardrails`, and `attachment`; `inputDefinition.required` is `["fileRef"]`.
- `inputDefaults` contains the full `model` metadata blob and flat `modelName`, `projectName`, `folderKey`, and `folderName` mirrors. The deployment-node blob is `{ id, modelName, modelDisplayName, folderKey, folderName, folderPath, description }`. `model.modelName` is often `null` for published/OOB deployments; use `model.modelDisplayName` as the human name and required non-empty `modelName` value.
- `outputDefinition` is populated: `output` contains the extraction-result JSON schema and `error` the standard error envelope.

## Adding and editing

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Apply CAPABILITY rule #15 (no top-level `model` block on the instance), rule #14 (`variables.nodes[]` for every data-producing node), and Critical Rule #7. Unlike general action nodes, `uipath.ixp.*` instances require `outputs`; see [Authoring rules](#authoring-rules).

Always land the extraction node, even when configuration is incomplete; see [Landing the node when you cannot fully configure it](#landing-the-node-when-you-cannot-fully-configure-it).

## JSON structure and authoring

An IxP instance has `inputs` and `outputs`, with no top-level `model`. The slim manifest `model` (`{ type, serviceType }`) exists only in `definitions[]`; the BPMN serializer injects runtime `model.context`, `model.version`, `model.inputs`, and `model.outputs`.

### Build procedure — copy from `registry get`, do not construct from memory

Run once:

```bash
uip maestro flow registry get "<node-type>" --output json > <tmpfile>.json
```

Copy these fields from `Data.Node`:

| Instance field | Source | Required |
|---|---|---|
| `inputs.model` | `Data.Node.inputDefaults.model`, verbatim except the `modelName` rule below | YES; undefined crashes the canvas |
| `inputs.model.modelName` | `Data.Node.inputDefaults.model.modelName`; if `null`/empty, use `Data.Node.inputDefaults.model.modelDisplayName` | YES; non-empty or `flow validate` fails (`ixp-node`) |
| `inputs.modelName` | `Data.Node.inputDefaults.modelName` | YES |
| `inputs.projectName` | `Data.Node.inputDefaults.projectName` | YES |
| `inputs.folderKey` | `Data.Node.inputDefaults.folderKey` | YES |
| `inputs.folderName` | `Data.Node.inputDefaults.folderName` | YES |
| `inputs.versionTag` | `""`, unless pinning a version | YES |
| `inputs.pageRange` | `""` for the full document | YES |
| `inputs.fileRef` | `=js:$vars.<upstream>.output.<field>` pointing to the whole file/attachment object | YES |
| `outputs.output` | Fixed literal below | YES |
| `outputs.error` | Fixed literal below | YES |

Never add removed legacy inputs: `digitizationMode`, `documentTaxonomy`, `attachmentId`, `fileName`, or `mimeType`. `digitizationMode` defaults internally to `fileUpload`; `documentTaxonomy` was replaced by `inputs.model`; attachments bind through `inputs.fileRef` as the whole object; `fileName` and `mimeType` derive from `fileRef`. A bare ID in `fileRef` can pass validation but faults at debug with `[430002] Invalid input on document extraction`.

Use this instance shape:

```json
{
  "id": "<stable-id>",
  "type": "uipath.ixp.<sanitized-model>.<sanitized-fqn>",
  "typeVersion": "<typeVersion from `registry get` response>",
  "display": { "label": "<label>" },
  "inputs": {
    "model": {
      "id": "<model GUID — from inputDefaults.model.id>",
      "modelName": "<non-empty modelDisplayName if needed>",
      "modelDisplayName": "<modelDisplayName>",
      "folderKey": "<folderKey>",
      "folderName": "<folderName>",
      "folderPath": "<folderPath>",
      "description": "<description>"
    },
    "modelName": "<modelName>",
    "description": "<description>",
    "projectName": "<projectName>",
    "versionTag": "",
    "folderKey": "<folderKey>",
    "folderName": "<folderName>",
    "fileRef": "=js:$vars.<upstream>.output.<field>",
    "pageRange": ""
  },
  "outputs": {
    "output": {
      "name": "output",
      "type": "object",
      "source": "=this",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

`outputs` is this fixed four-field literal for every IxP node; do not omit it. Copying `outputDefinition.output` also validates but unnecessarily includes an approximately 18KB `schema` blob. Copy the `definitions[]` entry verbatim from `registry get` (`Data.Node`), including required `sortOrder`.

Authoring rules:

1. `inputs.model` must be present and copied from `Data.Node.inputDefaults.model`; do not abbreviate, omit, or invent fields. Current deployment blobs contain `{ id, modelName, modelDisplayName, folderKey, folderName, folderPath, description }`, not older `fullyQualifiedName`, `kind`, `type`, `detailsUrl`, or `async*` fields. `ixp-model-taxonomy` destructures `modelName` and `folderKey`; missing `inputs.model` crashes Studio Web (`Cannot destructure property 'modelName' of 't' as it is undefined`) and fails validation. `inputs.model.modelName` must be a non-empty string. If the registry value is `null`/empty, use that blob's `modelDisplayName`; this is not synthesis. If `folderKey` is empty, use flat `inputDefaults.folderKey`.
2. Keep flat mirrors `modelName`, `projectName`, `folderKey`, and `folderName` beside `inputs.model`; the `ixp-model` form reads them directly from `inputs.*`.
3. `fileRef` is the only schema-required input (`inputDefinition.required: ["fileRef"]`). Use `=js:$vars.<upstream>.output.<field>` per Critical Rule #13. The source variable must be declared `type: "file"`, not `type: "object"`; see [Wiring `fileRef`](#wiring-fileref--file-variable-bound-to-the-trigger).
4. Both `outputs.output` and `outputs.error` are mandatory; copy the fixed literals. `flow validate` hard-fails with `[nodes[<nodeId>].outputs.output] outputs.output must be present on the instance` or the matching `outputs.error` message.
5. Do not put a top-level `model` on the instance. The BPMN `model` envelope is emitted only during serialization.
6. Do not put `digitizationMode`, `documentTaxonomy`, `attachmentId`, `fileName`, or `mimeType` in `inputs`.
7. Every edge has exactly the relevant five keys: `id`, `sourceNodeId`, `sourcePort`, `targetNodeId`, and `targetPort`. Use `sourceNodeId`/`targetNodeId`, not `source`/`target`; output ports are those in [Registry Validation](#registry-validation).

`uip maestro flow validate` enforces these rules through `ixp-node`, returning `severity: "error"` issues with paths such as `nodes[<nodeId>].inputs.model`. Fix the `.flow`, not the validator. `inputDefinition.properties` describes the property catalog and does not authorize the five removed fields.

### `inputs.fileRef` versus emitted `model.inputs[]`

`inputs.fileRef` is authoritative. At BPMN serialization, `packages/services/src/serialization/uipath-extension.ts:handleIxpExtraction` wraps it in a `model.inputs[]` entry with target `bodyField` and body `{ "downloadedFileOutput": <fileRef> }`. Edit only `inputs.fileRef`; never hand-edit the BPMN body.

### Wiring `fileRef` — file variable bound to the trigger

Use a flow `in` variable of `type: "file"` bound through `triggerNodeId`, then reference it through the trigger output:

```json
"variables": {
  "globals": [
    {
      "id": "<fileVariableId>",
      "direction": "in",
      "type": "file",
      "triggerNodeId": "start"
    }
  ]
}
```

```json
"inputs": {
  "fileRef": "=js:$vars.start.output.<fileVariableId>"
}
```

Run debug with `uip maestro flow debug --attachment <variableId>=<localPath>` (for example, `--attachment disputedInvoice=./path/to/invoice.pdf`). The CLI uploads and binds `{ ID, FullName, MimeType, Metadata }`; keys are case-sensitive and `ID` is uppercase. The flag is repeatable, and `<variableId>` must match a `variables.globals[]` `id`; see [cli-commands.md — Pre-flight](../../../shared/cli-commands.md#pre-flight---attachment-binding). Do not use `type: "object"`, direct `=js:$vars.<variableId>`, or a bare GUID, URL, path, `.ID`, or `.FullName`.

### Optional `attachment` input (Orchestrator job attachments)

`inputDefinition.properties.attachment` accepts `{ ID, FullName, MimeType, Metadata }`; there is currently no standalone-node form UI. Set `inputs.attachment` programmatically if needed, with `ID` required, and validate end-to-end on the tenant. This does not replace `fileRef`: extraction reads `fileRef`, which must contain the whole attachment object, never `<attachment>.ID`.

## Accessing output

The result is at `$vars.{nodeId}.output`. Serialization maps the service `result` directly with `source: '=result'`, stripping the `result` wrapper. Thus `output` is the extraction-result object:

- `ExtractionResult`: `{ DocumentId, ResultsVersion, ResultsDocument }`; `ResultsDocument.Fields[]` contains extracted values and `ResultsDocument.Tables[]` tabular results.
- `ExtractorPayloads`: provider-specific raw payloads.
- `BusinessrulesResults[]`: business-rule results when configured.

A field has `FieldId`, `FieldName`, `FieldType`, `IsMissing`, `Values`, and `Confidence`; `Confidence` is commonly numeric, for example `95`. Read values by `FieldName`, then `Values[0]`:

```javascript
const fields = $vars.<nodeId>.output.ExtractionResult.ResultsDocument.Fields || [];
const value = fields.find(f => f.FieldName === '<fieldName>')?.Values?.[0];
return { value };
```

The sibling `$vars.{nodeId}.error` is populated on failure when the `error` port is wired (`supportsErrorHandling: true`), from the service `Error` field (`source: '=Error'`). Do not use `output.result.ExtractionResult`, flat `output.<fieldName>`, or `output.ExtractionResult.Fields`; use `output.ExtractionResult.ResultsDocument.Fields[]`. Studio Web's picker does not expose this nested shape; do not infer it from autocomplete or `outputDefinition.output.schema`, which describes the pre-`=result` wrapper.

## Trained-model field taxonomy

Registry output does not expose trained field names. Run:

```bash
uip ixp deployments get-taxonomy "<project-name>" --version <N> --output json
```

`<project-name>` is a project name from `uip ixp projects list`; `--version` is required and comes from `uip ixp projects list-models "<project-name>"`. Login is required. The expected response is:

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

`type` is one of `Text`, `Date`, `Number`, `Set`, or `FieldGroup`. `components[]` is populated only for `FieldGroup` and recursively has the same shape. Taxonomy uses camelCase `fieldName`; runtime fields use PascalCase `FieldName`. Translate only the wrapper key, not the value.

Agent call sequence:

1. Run `uip maestro flow registry search "uipath.ixp" --output json` to list IxP nodes.
2. Run `uip maestro flow registry get "<node-type>" --output json` and read `Data.Node.inputDefaults.{folderKey, modelName}` as part of [Build procedure](#build-procedure--copy-from-registry-get-do-not-construct-from-memory).
3. Run `uip ixp deployments get-taxonomy "<project-name>" --version <N> --output json` and read `documentTaxonomy.documentTypes[].fields[].fieldName`.
4. Author consumers using `$vars.<id>.output.ExtractionResult.ResultsDocument.Fields.find(f => f.FieldName === '<fieldName from step 3>')?.Values?.[0]`.

If taxonomy lookup fails because of no matching project, login expiry, unpublished deployment, or a transient error, make one attempt only. Then use defensive `find`-by-`FieldName` with assumed names and surface assumptions under **Open Questions**. Do not retry spelling variants, substitute a one-off extraction, or inspect the IxP product UI in the agent loop; `get-taxonomy` is the agent-loop path.

## Landing the node when you cannot fully configure it

**The extraction step must ALWAYS land a node — never drop it because configuration is incomplete.** A greenfield/exploration turn, an unwired upstream, an unresolved or unnamed **downstream** target, a "you don't need a working flow" instruction, or an unconfirmed model are NOT reasons to skip it. Ambiguity anywhere else in the flow is never a reason to stop before scaffolding: create the project, land the extraction node, and carry the open decision in **Open Questions** rather than asking and halting. The common failure is landing the steps around extraction while the extraction node itself goes missing. Author it before the trigger and connector nodes — connector configuration branches open-endedly, and this is the node the request is about.

- If `registry search "uipath.ixp"` returns entries, land the real `uipath.ixp.*` node. Build it from `registry get`, including `inputs.model` and fixed `outputs`; use a placeholder `fileRef` if necessary, and put unresolved model choice, file source, and taxonomy in **Open Questions**. Do not downgrade to `core.logic.mock`.
- If `Data: []`, land `core.logic.mock` as described below.

## If the Model Does Not Exist Yet

Trigger when `uip maestro flow registry search "uipath.ixp"` returns `Data: []`, or only `uipath.agent.resource.tool.ixp.*` variants.

Run once:

```bash
uip maestro flow registry get core.logic.mock --output json
```

Then:

1. Copy `Data.Node` verbatim into `definitions[]` if absent.
2. Add a stable `core.logic.mock` node to `nodes[]`; its `display.label` must begin with the user's domain work, not the technology. A parenthetical may say `mock — IxP model not yet published`.
3. Add `layout.nodes` at `position: { x: 400, y: 144 }`, size `96x96`.
4. Wire edges using [editing-operations.md](../../editing-operations.md). The mock is a no-op pass-through: no `inputs`, no `outputs`, and no `bindings_v2.json` changes.
5. Wire downstream consumers to `$vars.{mockNodeId}.output`, not static values, so the graph is swap-ready. Rewrite field-access paths when replacing the mock because real output is `{ ExtractionResult: { ResultsDocument: { Fields: [...] } } }`; surface that follow-up under **Open Questions**.
6. Run `uip maestro flow validate <ProjectName>.flow --output json` once after all edits.

State in **Open Questions** that the user must train and publish the IxP model before the flow can run. After publication, use [mock replacement procedure](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node).

## Classifier Variant

Classifier models have `type: Classifier`, share the `uipath.ixp.*` pattern, and return classification labels rather than named fields. Classifier configuration is outside this document; flag it as a prerequisite and defer to a future revision of this impl.md.

## Debug

| Error | Cause | Fix |
|---|---|---|
| Node type not found in registry | Model unpublished or registry cache stale | Run `uip login`, then `uip maestro flow registry pull --force`. |
| `model.context` rejected by runtime | `folderKey` or `modelName` missing from `inputs` | Populate `inputs.modelName` and `inputs.folderKey`. |
| Empty `$vars.{nodeId}.output` | Taxonomy mismatch or no returned fields | Inspect `$vars.{nodeId}.error`; if absent, compare the same document in the IxP product UI. |
| `fileRef` not resolving | Upstream variable is unwired or produces no file | Verify the upstream file output and `=js:$vars.<upstreamId>.output.<field>` expression. |
| `[430002] Invalid input on document extraction operation` at debug | `fileRef` contains attachment `.ID` or another scalar | Bind the whole object: `=js:$vars.<upstream>.output.<attachment>`. |
| `[430002] Invalid input on document extraction operation` with backend detail `'downloadedFileOutput' is missing the required 'ID' field` | Source flow input is `type: "object"` rather than `type: "file"` | Declare the input `type: "file"`; see [Wiring `fileRef`](#wiring-fileref--file-variable-bound-to-the-trigger). |
| Extraction failed | Unsupported MIME type, corrupt file, or service failure | Check `$vars.{nodeId}.error.detail`. |
| `uip maestro flow node configure` says `not a connector type node` | IxP is not a connector | Edit `inputs.*` directly in the `.flow` JSON. |
| Studio Web `Cannot destructure property 'modelName' of 't' as it is undefined` | Missing `inputs.model` | Copy `definition.inputDefaults.model` verbatim into `inputs.model`; it contains `id`, `modelName`, `modelDisplayName`, `folderKey`, `folderName`, `folderPath`, and `description`. |
| `flow validate` says `inputs.model must be an object with non-empty string modelName and folderKey` | `inputDefaults.model.modelName` was copied as common `null` | Set `inputs.model.modelName` from `inputDefaults.model.modelDisplayName` (Authoring rule #1); if needed, take `folderKey` from flat `inputDefaults.folderKey`. |