# Extract document node

*Commands: `uip maestro flow nodes create`, `uip maestro flow edges create`, `uip maestro flow validate`.*

An Extract document node (`uipath.ixp.extract-document-builder`) extracts named fields from taxonomy embedded in the `.flow`; it has no trained model or IXP project. Design taxonomy in [extract-document-taxonomy.md](extract-document-taxonomy.md).

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label '<name>' --input '{"fileRef":"=js:$vars.<upstream>.output.<field>"}' --output json
uip maestro flow validate <file> --output json
```

**Support for this node is new.** If installed `uip` rejects the type or returns `error: unknown command` for `nodes`, report that it is behind these commands and ask the user to update.

## Which extraction node the user wants

The default for document extraction in a flow is a published IXP model, covered in [ixp.md](ixp.md), where the IXP project is built and deployed first and the flow then runs against it. Use the Extract document node only when the user asks for it by name or is already using it: the flow holds a node of type `uipath.ixp.extract-document-builder` (`uip maestro flow nodes list <file> --output json` shows the types), or the request is about the taxonomy an Extract document node carries inline. A published-model node's taxonomy lives in its IXP project and belongs to `uipath-ixp`.

Three node families share the `uipath.ixp.` prefix and they are not interchangeable:

| Node | Node type | Where it is covered |
| --- | --- | --- |
| Extract document | `uipath.ixp.extract-document-builder` | this guide |
| A published IXP model — the default | `uipath.ixp.<project>.<version>-<folder>` | [ixp.md](ixp.md) |
| An IDP processor resource inside the solution | `uipath.ixp.processor.<resource-key>` | not covered here — add it in Studio Web |

The processor variant points to a solution processor and is a different node type. These conveniences apply only to `uipath.ixp.extract-document-builder`; a processor node added through CLI is incomplete, so leave it to Studio Web.

## At a glance

Add and label the node, wire `fileRef`, write taxonomy, bind the result, and validate. It does not extract until the user saves the flow once in Studio Web ([Making it actually extract](#making-it-actually-extract)). `fileRef` is the only author-supplied input and is required for validation.

```bash
uip maestro flow nodes create Flow/Flow.flow uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
uip maestro flow nodes list Flow/Flow.flow --output json
uip maestro flow validate Flow/Flow.flow --output json
```

## The loop

<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** Edit a `.flow` on disk. If it exists only in Studio Web, ask for its URL or solution id; nothing lists them ([Starting from a flow in Studio Web](extract-document-taxonomy.md#starting-from-a-flow-in-studio-web)).
<!--skill-flavor:extract-find-flow:end-->
1. **Declare the file input** unless it exists: `uip maestro flow variables create <file> invoice -d in -t file --description '<what the document is>'`. This makes `$vars.start.output.invoice` resolve before use.
2. **Add the node** with descriptive `--label` and `--input` containing `fileRef`.
3. **Connect it** with `edges create` ([Wiring the file it reads](#wiring-the-file-it-reads)).
4. **Write the taxonomy** in [extract-document-taxonomy.md](extract-document-taxonomy.md).
5. **Bind the result to a flow output** ([Returning the result](#returning-the-result)).
6. **Validate:** run `uip maestro flow validate <file> --output json`; it must return `Valid`.
7. **Report** what was added, its file source, extracted fields, and the required Studio Web save ([Making it actually extract](#making-it-actually-extract)); the user must take the flow live.

## Not available everywhere

The feature is new and tenant-gated. CLI creation and validation succeed either way; `registry search` reports `AvailableOnTenant: false` for this node on every tenant, while Studio Web's picker shows **Extract document** where enabled. If the tenant lacks it, or Automation Suite has structured extraction switched off, follow [When Extract document is not available](#when-extract-document-is-not-available).

## Adding the node

<!--skill-flavor:extract-sdk-mixing:start-->
**These commands edit the `.flow` file and do not mix with a TypeScript-source project.** A project initialized with `--sdk-source` compiles `.flow.ts` over the `.flow`, so check for `.flow-sdk/` first. If present, build this flow in a separate source-free project using only CLI; the SDK's `dynamicExtract()` is not the route here ([document-pipeline.md](document-pipeline.md)). Do not alternate between compilation and CLI edits.
<!--skill-flavor:extract-sdk-mixing:end-->

`--label` sets the canvas name and seeds the node id. Name the document and fields, not merely "Extract"; then run `uip maestro flow nodes list <file> --output json` to obtain the minted id.

The node supplies `inputs.schemaDocument` (empty taxonomy with six built-in field types), `inputs.modelConfig` (working defaults), `inputs.source` (minted identifier for the node's own extraction; nothing for you to supply), and `outputs.output`/`outputs.error` (both ports named on the instance, which is what lets a downstream `$vars` read resolve). It has no top-level `model` block: the slim manifest model belongs in `definitions[]`, and validation rejects an instance copy. `nodes create` leaves `modelName`, `folderKey`, and other deployment fields under `inputs` as empty strings; leave them empty because they belong to the published-model node in [ixp.md](ixp.md).

## Wiring the file it reads

`fileRef` is a runtime reference to an upstream output or flow variable, not a value:

```json
"fileRef": "=js:$vars.start.output.invoice"
```

Set it during creation when possible:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
```

Use the plain `=js:$vars.…` string. The structured form `{"type":"jsExpression","expression":"$vars.…","fieldType":"object"}` also validates, but `fieldType` is required; without it validation rejects the value. Do not use a literal filename or hand-built attachment object.

For connector events, read the trigger output contract for the file-reference field (for example, `ReferenceID` wires as `$vars.start.output.ReferenceID`); do not guess or add a download step. For a direct document input, declare it first:

```bash
uip maestro flow variables create <file> invoice -d in -t file --description 'The invoice document to extract' --output json
```

Treat an `EXPRESSION_DIAGNOSTIC` warning naming an undeclared `fileRef` input as an error. Connect the graph:

```bash
uip maestro flow edges create <file> <upstream-id> <extract-id> --output json
uip maestro flow edges create <file> <extract-id> <downstream-id> --output json
```

`edges create` uses the default source port, so the outgoing edge uses `success` without a flag. Graph ports (`success`, `error`) differ from variable outputs (`output`, `error`). Duplicate edges are safe; the command reports the existing edge.

## Reading what it extracts

Read extracted values at:

```js
$vars.<extract-node-id>.output.result.output
```

The `output` port contains a processed document with top-level `version`, `type`, `result`, `taxonomy`, and `metadata`. `result` contains `output` (field values), `attribution` (page locations keyed by JSON Pointer into `output`), and `traceContext`. Use `result.output` for values or the port for the whole document.

Read the embedded definition if the shape evolves: this node's `definitions[]` entry has `outputDefinition.output.schema.properties`. `registry get` returns `Node not found` because no tenant manifest carries this type.

**`ExtractionResult` is the published-model node's output, not this one.** `ExtractionResult.ResultsDocument.Fields[]` belongs to [ixp.md](ixp.md); a downstream step using that shape against this node reads a missing key.

The `error` port carries failures. Wire it with `edges create --source-port error` when an unreadable document should follow a recovery path; leaving it unwired means the flow fails loudly instead, which is often the right behaviour.

## Returning the result

Declare an output, create an End node, wire the extract node to it, then write the binding directly into the End node's `outputs` block; there is no CLI command for that final edit:

```bash
uip maestro flow variables create <file> extractedData -d out -t object --description 'The structured data extracted from the document' --output json
uip maestro flow nodes create <file> core.control.end --label 'End' --output json
uip maestro flow edges create <file> <extract-id> <end-id> --output json
```

Use this binding, keyed by the declared output name:

```json
{
  "id": "end1",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "display": { "label": "End" },
  "inputs": {},
  "outputs": {
    "extractedData": {
      "type": "object",
      "description": "",
      "source": "=js:$vars.<extract-id>.output.result.output",
      "var": "extractedData"
    }
  }
}
```

`var` names the global and `source` fills it. For partial or reshaped results, put a script between the nodes and bind its output. **There is no `variableUpdates` block on an End node;** validation rejects that shape.

## Validating

```bash
uip maestro flow validate <file> --output json
```

Validation requires `fileRef` to be a `$vars` reference, both output ports named on the instance, and no top-level `model` block. A new node fails only on unwired `fileRef`; that is expected until wiring is complete.

## Making it actually extract

A CLI-authored node can validate and deploy but extracts nothing until the user opens the flow in Studio Web and saves it once. Runtime resolves `inputs.processorKey` to a tenant-side processor holding its own taxonomy; CLI does not provision it. Without one, the instance faults:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

A fast completion or empty `{}` means unprovisioned, not a taxonomy matching nothing. The Studio Web save provisions the processor; do not synthesize or copy a `processorKey`, which names a different taxonomy.

<!--skill-flavor:extract-after-save:start-->
Saving in Studio Web may convert the node to `uipath.ixp.processor.<key>`, a different type. Pull the solution down before further editing; for that variant, `nodes schema set` refuses it and taxonomy editing continues in Studio Web.
<!--skill-flavor:extract-after-save:end-->

## When Extract document is not available

Never add the unavailable node or substitute a placeholder for requested working extraction.

**First, look for a published IXP model:**

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a suitable published model exists, say Extract document is not enabled, identify the replacement and why, verify its taxonomy covers the request, state what it does not cover, and build it under [ixp.md](ixp.md). Published and Extract document nodes are not equivalent.

If none exists, stop. Say which tenant was checked, that neither Extract document nor a trained model is available, and that a tenant administrator must enable document extraction as covered in UiPath product documentation. Do not scaffold, write a flow file, or place `mock()` in the extraction position. A placeholder is allowed only for a validate-only topology explicitly showing where extraction belongs, never as expected runtime extraction.

## Unsupported Capabilities

These requests are outside the skill. Recognise the request, reply with the standard response, and route the user. Do NOT enter discovery (`uip --help`, grep, source reading).

For an uncovered Extract document setting or resource, do not seek a CLI path or edit `.flow`, `.flow.ts`, or project files. Say it is unavailable here and link [Extract document documentation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/introduction).

| User request | Standard response |
|--------------|-------------------|
| "Add a node that uses the same model as the other Extract node" / "reuse the other Extract node's settings or documents" | "I can't link a new node to another Extract node from here. Do that in the flow designer: [Adding an Extract node to a flow](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/managing-extract-nodes#adding-an-extract-node-to-a-flow). I can copy its taxonomy to a new Extract document node. It extracts the same fields, with default model settings and no documents." |
| "Pick the best model settings for these documents" / "tune the node for speed or accuracy" | "I can't change the node's model configuration from here. See [Model configuration](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model)." |
| "Use GPT-5 / Gemini Pro" / "change the extraction model" | "I can't change the extraction model of this node from here. See [Choosing the most suitable model](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#choosing-the-most-suitable-model) and [Switching from one model to another](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#switching-from-one-model-to-another)." |
| "Change the extraction strategy" / "use the Standard / Advanced strategy" | "I can't change the extraction strategy from here. See [Configuring the model](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#configuring-the-model)." |
| "Switch the language to Arabic / Japanese" / "set language to Auto-detect / Latin-based / Extended" | "I can't change language support from here. See [Language support](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#language-support)." |
| "Set layout parsing to None / Full" / "turn layout parsing on / off" | "I can't change layout parsing from here. See [Layout parsing](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#layout-parsing)." |
| "Use Rules-based / Model-based attribution" | "I can't change attribution from here. See [Attribution](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#attribution)." |
| "Add model overrides" / "set the overrides JSON" | "I can't set model configuration overrides from here. See [Overrides](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#overrides)." |
| "Import this IXP taxonomy file" (a file with `entity_defs` and `label_groups`) / "Export the taxonomy as an IXP file" | "I can't import or export IXP taxonomy files from here. Use Import/Export in the flow designer: [Importing and exporting taxonomies](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/importing-and-exporting-taxonomies). I can show the taxonomy, replace it from a flow-format file, or copy it from another Extract document node." |
| "Upload these documents" / "delete a test file" / "tag these documents" / "show the documents not annotated yet" | "I can't manage the node's test documents from here. See [Uploading sample documents](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/uploading-sample-documents)." |
| "What would it extract from this file?" / "refresh the predictions" | "I can't run or refresh predictions for this node. See [Reviewing predictions](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/generating-and-reviewing-predictions)." |
| "Confirm these values" / "annotate the documents" | "I can't annotate test documents. See [Validating predicted values](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/validating-extractions)." |
| "Set up the evaluators" / "how should this field be scored?" | "I can't configure the node's evaluators. See [Running an evaluation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/running-an-evaluation)." |
| "Run an eval" / "evaluate on this one file" / "what's my score?" / "compare the eval runs" / "improve the accuracy" | "I can't run or read evaluations for this node. See [Running an evaluation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/running-an-evaluation) and [Evaluating model performance](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/evaluating-model-performance)." |
| "Make the extract node actually run" / "provision the processor" / "set the processorKey" | "I can't create the node's processor from here. Save the flow once in the flow designer; that creates it, and extraction works after you publish and deploy." |

## Evidence boundary

This is offline file authoring except registry lookup, which needs login to see tenant offerings. `validate` proves wiring and shape: `fileRef` resolves upstream, ports are named, and taxonomy is well formed. It does not prove extraction; that requires the Studio Web save ([Making it actually extract](#making-it-actually-extract)) and a run against real documents, typically followed by taxonomy refinement.
