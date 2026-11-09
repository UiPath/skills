# IxP Extraction

*Exact signatures, fields, and defaults: `ixpExtract()`.*

Run a published Intelligent eXtraction Platform project on a Flow attachment.

Signature: `ixpExtract({ project, modelName, name, folderName, fileRef, pageRange?, versionTag?, folderPath?, description? })`.

## At a glance

Copy identity fields from a freshly pulled tenant registry; never construct them. For read-only model questions, run one `registry search 'uipath.ixp'`; never fan out `registry get` across hits.

## Listing published models

Tenant-published-model questions are read-only listings, not build requests. Run:

<!--skill-flavor:ixp-list-commands:start-->
```bash
uip login status --output json      # without login, tenant IxP nodes are hidden
uip maestro flow registry pull --force
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```
<!--skill-flavor:ixp-list-commands:end-->

Treat each `Data[]` entry as one published model/runtime project visible to the flow registry. Present `DisplayName`, `NodeType` and `Version` as a table, then stop.

- **Do NOT call `registry get` on search hits.** Search answers listings; `registry get` resolves ONE node's authoring identity and runs only when authoring that node.
- **Do NOT scaffold a solution, run `uip maestro flow init`, or write a `.flow.ts` or `.flow` file.**
- **Do NOT mock.** If `Data: []`, state that no IxP models are published. `mock()` is only for build-time planning.
<!--skill-flavor:ixp-no-login:start-->
- **Do NOT log in for the user.** If `uip login status` shows logged-out, tell the user to run `uip login` and stop; unauthenticated listing returns misleading OOTB-only results.
<!--skill-flavor:ixp-no-login:end-->
- **Do NOT search by `runtime`, `document extractor`, `extractor`, or `IXP` (uppercase).** Search `uipath.ixp` (lowercase) only.
- **Do NOT switch to the `uipath-ixp` skill.** `uip ixp projects ...` lists IxP-product projects, not Maestro wiring.
- **Do NOT use `uip maestro flow process list` or Orchestrator folder iteration.** They enumerate deployed flow process instances, not published models.
- **Do NOT guess `uip maestro flow list-*` or `uip maestro ixp list-*` subcommands.** None exist; the CLI returns `unknown command`, with no fallback.

A `uipath.agent.resource.tool.ixp.*` hit on a broader `ixp` search is the agent-tool variant, not a flow extraction node. Treat it as no extraction model published and stop after that one broader check; do not iterate searches.

## Resource identity

This is the AUTHORING path for the one model a step runs. For listings, use [Listing published models](#listing-published-models): search answers them and `registry get` must not be fanned out.

Run the registry pull first, then copy the complete node type and companion defaults; node type is tenant/version identity, not a reconstructed string:

```bash
uip maestro flow registry pull --force
uip maestro flow registry search '<project hint>' \
  -f 'type:startsWith=uipath.ixp' \
  --output-filter '[?AvailableOnTenant].NodeType' --output json
uip maestro flow registry get '<node-type>' \
  --output-filter '{project:Node.nodeType,modelName:Node.inputDefaults.modelName,folderName:Node.inputDefaults.folderName,folderPath:Node.inputDefaults.model.folderPath,versionTag:Node.inputDefaults.versionTag,taxonomyProject:Node.inputDefaults.projectName}' \
  --output json
```

`registry get` is the authoring source of truth for ONE node. Copy `project`, `modelName`, `folderName`, `folderPath`, and `versionTag` from its response; do not use `uip ixp projects ...` or reconstruct deployment through other IxP APIs. `--output-filter` runs against the response's `Data` field, so registry-get paths start at `Node`; the projection avoids materializing the full schema.

To read selected extraction fields, inspect only these two result-item schemas:

```bash
uip maestro flow registry get '<node-type>' \
  --output-filter '{scalarResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Fields.items.properties),tableResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Tables.items.properties)}' \
  --output json
```

Scalar results are `ExtractionResult.ResultsDocument.Fields[]`; table results are `ExtractionResult.ResultsDocument.Tables[]`. In both, `FieldName` identifies the model field and `Values` carries extracted values.

If no suitable published extractor exists, follow the acceptance bar: for a runtime or published-model requirement, report the missing capability and stop. For a validate-only topology showing where extraction belongs, put `mock()` in the extraction position, validate the surrounding flow, and report the placeholder as the capability gap. Do not block validate-only topology on unavailable extractors or downstream endpoints when placeholders preserve the requested graph. `pageRange` is a product string; examples such as `1-5` are illustrative because no local grammar is published.

## File input from a connector event

Read the trigger's `outputResponseDefinition` and pass its exact file-reference field to `fileRef`; a `ReferenceID` field is wired as `fileRef: out('start', 'ReferenceID')`. This direct connector-event-to-IxP shape passes product validation; do not add a download action merely to alter a validate-only flow.

The SDK emits the accepted plain expression string:

```json
"fileRef": "=js:$vars.start.output.ReferenceID"
```

Do not replace it with a `{ "type": "jsExpression", ... }` envelope or hand-built attachment object. Add a download action only when the discovered trigger contract has no file-reference field and requested runtime behavior requires file bytes.

## Joined document-event recipe

`documentCreated` is the event subscription resolved from its live connection; `extractor` is the identity object copied from `registry get`. Wire the trigger field directly into extraction and the whole result into delivery:

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

`out('<ixp-step>')` is the extraction result object and may be forwarded whole, including as an HTTP request body. Pass it directly; no serializer inspection or taxonomy lookup is needed for that shape.

Use a model taxonomy only to select named extracted fields. If the trained model version is known, run `uip ixp deployments get-taxonomy '<taxonomyProject>' --version <number>` once. Retry the same command at most once, only for `RetryLater` or transient 5xx; do not retry validation errors or `RetryWillNotFix`, and do not explore `uip ixp projects ...` to reconstruct deployment. If that retry fails, use defensive reads from `Fields[]` or `Tables[]`, state assumed field names, and finish the compile/validation loop. This interim guidance references [UiPath/cli#3512](https://github.com/UiPath/cli/issues/3512).

## Recovery and evidence

Wire `.onError(...)` when unreadable documents or no-match results need recovery; otherwise failing loud may be correct. Local execution uses an extraction fixture and proves wiring only. Product debug is required only when the acceptance bar requires proof that the chosen model processed a real file or returned semantically correct fields. For validate-only, green product validation plus intended emitted wiring is complete.

The compiler also emits the project's `ixpDeployment` bindings.
