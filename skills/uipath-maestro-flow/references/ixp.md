# IxP Extraction

*Exact signatures, fields, and defaults: `ixpExtract()`.*

Run a published Intelligent eXtraction Platform project on a Flow attachment.

Signature:
`ixpExtract({ project, modelName, name, folderName, fileRef, pageRange?, versionTag?, folderPath?, description? })`.

```ts
.step('extract', ixpExtract({ project: ixpNodeType,
  modelName: 'invoice-model', name: 'Invoice Extractor',
  folderName: 'Shared', fileRef: out('start', 'invoiceFile') }))
```

## At a glance

Copy `project`, `modelName`, `folderName`, `folderPath`, and `versionTag` from the tenant registry; never construct them. For read-only model questions, run one `registry search 'uipath.ixp'`; never fan out `registry get` across hits.

## Listing published models

For "What document extractors can I add to this flow?", "what IxP models can I use here?", "list published extractors", or "what extraction nodes are in the registry?" (read-only Q&A, not build requests), run:

<!--skill-flavor:ixp-list-commands:start-->
```bash
uip login status --output json      # without login, tenant IxP nodes are hidden
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```
<!--skill-flavor:ixp-list-commands:end-->

Present each `Data[]` entry's `DisplayName`, `NodeType`, and `Version` as a table, then stop.

- Do **NOT** call `registry get` on search hits: search contains the answer. Use `registry get` only when authoring one specific node; it resolves ONE node's authoring identity.
- Do **NOT** scaffold, run `uip maestro flow init`, write a `.flow.ts` or `.flow` file, or mock. If `Data: []`, run `uip maestro flow registry pull --force` once and search again (reads are cached for 30 minutes). If still empty, state that no IxP models are published. `mock()` is for build-time planning, not listing Q&A.
<!--skill-flavor:ixp-no-login:start-->
- **Do NOT log in for the user.** If `uip login status` shows logged-out, tell the user to run `uip login` and stop; listing without auth returns OOTB-only results and is misleading.
<!--skill-flavor:ixp-no-login:end-->
- Search only `uipath.ixp` (lowercase), never `runtime`, `document extractor`, `extractor`, or uppercase `IXP`.
- Do **NOT** switch to the `uipath-ixp` skill: `uip ixp projects ...` lists IxP-product projects, not Maestro wiring.
- Do **NOT** use `uip maestro flow process list` or Orchestrator folder iteration; they enumerate deployed flow process instances, not published models.
- Do **NOT** guess `uip maestro flow list-*` or `uip maestro ixp list-*` subcommands; none exist and there is no fallback.
- A `uipath.agent.resource.tool.ixp.*` hit from a broader `ixp` search is the agent-tool variant, not a flow extraction node. Treat it as no extraction model published and stop after that one broader check; do not iterate registry searches.

## Resource identity

This is the AUTHORING path, for the one model a step will run; for listings, use [Listing published models](#listing-published-models). Copy the complete node type and its companion defaults. The node type is tenant/version identity, not a string to reconstruct:

```bash
uip maestro flow registry search '<project hint>' \
  -f 'type:startsWith=uipath.ixp' \
  --output-filter '[?AvailableOnTenant].NodeType' --output json
uip maestro flow registry get '<node-type>' \
  --output-filter '{project:Node.nodeType,modelName:Node.inputDefaults.modelName,folderName:Node.inputDefaults.folderName,folderPath:Node.inputDefaults.model.folderPath,versionTag:Node.inputDefaults.versionTag,taxonomyProject:Node.inputDefaults.projectName}' \
  --output json
```

Registry reads are cached for 30 minutes. If the model is missing, run `uip maestro flow registry pull --force` once and search again. `registry get` is the authoring source of truth for ONE node. Copy `project`, `modelName`, `folderName`, `folderPath`, and `versionTag` from that response; do not switch to `uip ixp projects ...` or reconstruct the deployment through other IxP APIs. `--output-filter` runs against `Data`, so get paths start at `Node`; the projection avoids the full schema.

To read selected extraction fields, inspect only these two result-item schemas:

```bash
uip maestro flow registry get '<node-type>' \
  --output-filter '{scalarResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Fields.items.properties),tableResultMembers:keys(Node.outputDefinition.output.schema.properties.ExtractionResult.properties.ResultsDocument.properties.Tables.items.properties)}' \
  --output json
```

Scalar results are `ExtractionResult.ResultsDocument.Fields[]`; table results are `ExtractionResult.ResultsDocument.Tables[]`. In both, `FieldName` identifies the model field and `Values` carries extracted values.

If no suitable published extractor exists: for a runtime or published-model requirement, report the missing capability and ask whether to build one with `uipath-ixp`; headless, with no one to ask, invoke `uipath-ixp` yourself and never use the Extract document node; for a validate-only topology showing where extraction belongs, put `mock()` in the extraction position, complete and validate the surrounding flow, and report the placeholder as the capability gap. Do not block validate-only topology on unavailable extractors or downstream endpoints when placeholders preserve the requested graph. `pageRange` is a product string; `1-5` is illustrative because no local grammar is published.

## File input from a connector event

Read the trigger's `outputResponseDefinition` and pass its exact file-reference field to `fileRef`; for example, a SharePoint-backed event that declares `ReferenceID` is wired as `fileRef: out('start', 'ReferenceID')`. This direct connector-event-to-IxP shape passes product validation; do not add a download action merely to change it in a validate-only flow.

The SDK emits that `out(...)` handoff in the one envelope the IxP validator accepts, a plain expression string:

```json
"fileRef": "=js:$vars.start.output.ReferenceID"
```

Do not replace it with `{ "type": "jsExpression", ... }` or a hand-built attachment object. Add a download action only when the discovered trigger contract has no file-reference field and requested runtime behavior requires file bytes.

## Joined document-event recipe

For a joined document event, resolve `documentCreated` from its live connection, copy the identity object `extractor` from `registry get` (see Resource identity), pass the trigger field directly to extraction, and pass the whole result directly to delivery:

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
    method: 'POST', url: 'https://catalog.example.test/cards', managed: true,
    body: out('extract'), contentType: 'application/json',
  }))
  .build();
```

## Downstream output

`out('<ixp-step>')` is the extraction result object and may be forwarded whole, including as an HTTP request body. Pass it directly; no serializer inspection or taxonomy lookup is needed for that shape.

A model taxonomy is needed only to select named fields. If the trained model version is known, run `uip ixp deployments get-taxonomy '<taxonomyProject>' --version <number>` once. Retry the same command at most once, only for `RetryLater` or transient 5xx; do not retry validation errors or `RetryWillNotFix`, and do not use `uip ixp projects ...` to reconstruct deployment. If that retry fails, use defensive reads from `Fields[]` or `Tables[]`, state assumed field names, and finish the compile/validation loop. This is interim guidance for [UiPath/cli#3512](https://github.com/UiPath/cli/issues/3512).

## Recovery and evidence

Wire `.onError(...)` when unreadable documents or no-match results need recovery; otherwise failing loudly may be correct. Local execution uses an extraction fixture and proves wiring only. Require product debugging only when the acceptance bar requires proof that the chosen model processed a real file or returned semantically correct fields. For validate-only bars, green product validation plus intended emitted wiring is complete.

The compiler also emits the project's `ixpDeployment` bindings.
