# IxP Extraction

*Behavior and worked examples. Exact signatures, fields, and defaults: [`ixpExtract()`](api.md#ixpextract-function).*

IxP extraction runs a published Intelligent eXtraction Platform project on a
Flow attachment.

Signature:
`ixpExtract({ project, modelName, name, folderName, fileRef, pageRange?, versionTag?, folderPath?, description? })`.

```ts
.step('extract', ixpExtract({ project: ixpNodeType,
  modelName: 'invoice-model', name: 'Invoice Extractor',
  folderName: 'Shared', fileRef: out('start', 'invoiceFile') }))
```

## Resource identity

Refresh the registry first, then copy the complete node type and its companion
defaults. The node type is tenant/version identity, not a string to reconstruct:

```bash
uip maestro flow registry pull --force
uip maestro flow registry search '<project hint>' \
  -f 'type:startsWith=uipath.ixp' \
  --output-filter '[?AvailableOnTenant].NodeType' --output json
uip maestro flow registry get '<node-type>' \
  --output-filter '{project:Node.nodeType,modelName:Node.inputDefaults.modelName,folderName:Node.inputDefaults.folderName,folderPath:Node.inputDefaults.model.folderPath,versionTag:Node.inputDefaults.versionTag,taxonomyProject:Node.inputDefaults.projectName}' \
  --output json
```

`registry get` is the authoring source of truth. Copy `project`, `modelName`,
`folderName`, `folderPath`, and `versionTag` from that response; do not switch to
`uip ixp projects ...` or reconstruct the deployment through other IxP APIs.
`--output-filter` runs against the response's `Data` field, so registry-get paths
start at `Node`. The compact projection avoids materializing the full schema.

When code must read selected extraction fields, inspect only the two result-item
schemas:

```bash
uip maestro flow registry get '<node-type>' \
  --output-filter '{scalarResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Fields.items.properties),tableResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Tables.items.properties)}' \
  --output json
```

Scalar results are under `ExtractionResult.ResultsDocument.Fields[]`; table
results are under `ExtractionResult.ResultsDocument.Tables[]`. In both arrays,
`FieldName` identifies the model field and `Values` carries its extracted values.

If the registry has no suitable published extractor, report the missing
capability. `pageRange` is a product string; examples such as `1-5` are
illustrative because no local grammar is published.

## File input from a connector event

Read the trigger's `outputResponseDefinition` and pass the exact file-reference
field to `fileRef`. For example, a SharePoint-backed event that declares
`ReferenceID` is wired as `fileRef: out('start', 'ReferenceID')`. This direct
connector-event-to-IxP shape passes product validation; do not add a download
action merely to change the shape for a validate-only flow.

The SDK emits that `out(...)` handoff in the one envelope the IxP validator
accepts — a plain expression string:

```json
"fileRef": "=js:$vars.start.output.ReferenceID"
```

Do not replace it with a `{ "type": "jsExpression", ... }` envelope or a
hand-built attachment object. Add a download action only when the discovered
trigger contract has no file-reference field and requested runtime behavior
requires the file bytes.

## Joined document-event recipe

`documentCreated` is the event subscription resolved from its live connection;
`extractor` is the identity object copied from `registry get` as described above.
The trigger field flows straight into extraction, and the whole result flows
straight into delivery:

```ts
const documentCreated = {
  connector: 'uipath-microsoft-onedrive', event: 'file-created',
  connection: 'documents', folder: 'documentsFolder',
};

export default flow('archive-card-intake')
  .trigger(onEvent(documentCreated))
  .step('extract', ixpExtract({
    ...extractor,
    fileRef: out('start', 'ReferenceID'),
  }))
  .step('deliver', http({
    method: 'POST', url: 'https://catalog.example.test/cards', managed: false,
    body: out('extract'), contentType: 'application/json',
  }))
  .build();
```

## Downstream output

`out('<ixp-step>')` is the extraction result object and can be forwarded as a
whole, including as an HTTP request body. Pass the expression directly; no
serializer inspection or taxonomy lookup is needed for that shape. The joined
recipe above shows the complete handoff.

A model taxonomy is needed only when the flow must select named extracted
fields. If the trained model version is already known, run
`uip ixp deployments get-taxonomy '<taxonomyProject>' --version <number>` once.
Retry the same command at most once, and only when the response says
`RetryLater` or reports a transient 5xx failure. Do not retry validation errors
or `RetryWillNotFix`, and do not explore `uip ixp projects ...` to reconstruct
the deployment. If the one retry also fails, use defensive reads from the
`Fields[]` or `Tables[]` paths above, state the assumed field names, and finish
the compile/validation loop. This is interim guidance for
[UiPath/cli#3512](https://github.com/UiPath/cli/issues/3512).

## Recovery and evidence

Wire `.onError(...)` when unreadable documents or no-match results should follow
a recovery path; otherwise failing loud may be the correct scenario behavior.
Local execution uses an extraction fixture and proves wiring only. Product
debug is required only when the acceptance bar asks for proof that the chosen
model processed a real file or returned semantically correct fields. For a
validate-only bar, green product validation plus the intended emitted wiring is
complete.

The compiler also emits the project's `ixpDeployment` bindings.
