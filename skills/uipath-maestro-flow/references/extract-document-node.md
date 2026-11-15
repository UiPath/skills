# Extract document node

*Commands: `uip maestro flow extraction check`, `uip maestro flow nodes create`, `uip maestro flow edges create`, `uip maestro flow validate`.*

An Extract document node (`uipath.ixp.extract-document-builder`) extracts named fields using taxonomy embedded in the `.flow`; it has no trained model or IXP project. Add, wire, and validate it; design taxonomy in [extract-document-taxonomy.md](extract-document-taxonomy.md).

```bash
uip maestro flow extraction check --output json
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label '<name>' --input '{"fileRef":"=js:$vars.<upstream>.output.<field>"}' --output json
uip maestro flow validate <file> --output json
```

**Support for this node is new.** If the CLI refuses the type, or an older CLI answers `error: unknown command` for `nodes`, say `uip` is outdated and ask the user to update.

## Which extraction node the user wants

Normally use a published IXP model, covered in [ixp.md](ixp.md), after building and deploying its project. Add `uipath.ixp.extract-document-builder` to a new flow only when requested by name. Keep that node and its inline taxonomy in an existing flow; run `uip maestro flow nodes list <file> --output json` to show its type. A published-model taxonomy belongs to `uipath-ixp`.

| Node | Node type | Where covered |
| --- | --- | --- |
| Extract document | `uipath.ixp.extract-document-builder` | this guide |
| Published IXP model — default | `uipath.ixp.<project>.<version>-<folder>` | [ixp.md](ixp.md) |
| IDP processor resource | `uipath.ixp.processor.<resource-key>` | not covered; add it in Studio Web |

The processor variant points to a solution processor resource and is a different type. These conveniences apply only to `uipath.ixp.extract-document-builder`; a CLI-created processor node is incomplete and must be left to Studio Web.

## At a glance

Add a descriptive node, wire its file, write taxonomy, bind the result, and validate. `fileRef` is the only author-supplied input and is required for validation. The processor arrives with the node; packing keeps it synchronized ([Making it actually extract](#making-it-actually-extract)).

## The loop

<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** Edit a `.flow` on disk. If it is in Studio Web, ask for its URL or solution id; nothing lists them ([Starting from a flow in Studio Web](extract-document-taxonomy.md#starting-from-a-flow-in-studio-web)).
<!--skill-flavor:extract-find-flow:end-->
1. **Check the tenant:** run `uip maestro flow extraction check --output json`. Only `Available` proceeds automatically; an unsettled check requires the user ([Check the tenant can run it](#check-the-tenant-can-run-it)).
2. **Declare the input if absent:** run `uip maestro flow variables create <file> invoice -d in -t file --description '<what the document is>'`. Its `TriggerNodeId` is `<trigger>` in `$vars.<trigger>.output.invoice`.
3. **Add the node** with a descriptive `--label` and `--input` per [operate.md](operate.md#lay-out-the-emitted-flow-first).
4. **Connect it** with `edges create` ([Wiring the file it reads](#wiring-the-file-it-reads)).
5. **Write the taxonomy:** [extract-document-taxonomy.md](extract-document-taxonomy.md).
6. **Bind the result** to a flow output ([Returning the result](#returning-the-result)).
7. **Validate:** run `uip maestro flow validate <file> --output json`; it must return `Valid`.
8. **Report** what was added, its file source, extracted content, and `nodes create`'s processor result: in a solution the resource is under `resources/` and travels with the `.flow`; otherwise it remains to be created ([Making it actually extract](#making-it-actually-extract)). The user takes the flow live.

## Check the tenant can run it

Before adding a new node, run:

```bash
uip maestro flow extraction check --output json
```

`Data.Status` is the result and `Data.Reason` explains it:

| Status | Meaning |
| --- | --- |
| `Available` | both gates open |
| `FeatureDisabled` | extraction is off; a tenant administrator must enable it |
| `ModelUnavailable` | extraction is on but no model is available |
| `ServiceUnavailable` | no document-extraction service is available |
| `Unknown` | the service answered without settling either gate |

Continue on `Available`; use [When Extract document is not available](#when-extract-document-is-not-available) for the other three settled failures. `Unknown`, non-zero exit, expired login, and old CLI do not establish unavailability: report the command result and ask whether to try adding the node; if nobody can answer, add it and report that the check settled nothing.

This gates only adding a new node. Local `.flow` and taxonomy edits, `nodes provision`, and validation proceed without the tenant; report the status alongside them.

`Available` proves only its two gates. Deploy or run may still refuse the configured model, a cluster-wide switch, model-based attribution, full layout parsing, OCR language packs, or target-folder permissions. Do not call the node working after such a refusal and do not try folders in turn. If it names the model, identify it and direct the user to [Switching from one model to another](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#switching-from-one-model-to-another); changing it is the user's step. If the user requested that model by name, say this tenant cannot run it.

No other CLI command answers this question. `registry search` reports `AvailableOnTenant: false` for this node on every tenant because it comes from a builder, not the tenant node catalogue.

## Adding the node

<!--skill-flavor:extract-sdk-mixing:start-->
**These commands edit the `.flow` file, so they do not mix with a project built from TypeScript source.** A project initialized with `--sdk-source` compiles `.flow.ts` over CLI edits. Check for `.flow-sdk/`; if present, build this flow in a separate project without source and use only the CLI. The SDK's `dynamicExtract()` is not the route here ([document-pipeline.md](document-pipeline.md) explains its limits). Do not alternate between the two; re-apply CLI edits after each compile.
<!--skill-flavor:extract-sdk-mixing:end-->

`--label` sets the canvas name and seeds the node id; run `uip maestro flow nodes list <file> --output json` to obtain the minted id. `nodes create` supplies `inputs.schemaDocument` (empty taxonomy with six built-in field types), `inputs.modelConfig` (working model defaults), `inputs.source` (minted extraction identifier), `inputs.processorKey` and `inputs.processorName` (processor; in a solution its resource file is written, otherwise output says `ResourcePending` and pack creates it later ([Making it actually extract](#making-it-actually-extract))), and `outputs.output` and `outputs.error` (named instance ports for downstream `$vars`). It has no top-level `model` block: the slim manifest model belongs in `definitions[]`; validation rejects an instance copy.

Keep `modelName`, `folderKey`, and other deployment fields under `inputs` as empty strings. They identify a trained IXP deployment and belong to [ixp.md](ixp.md); this node requires only `fileRef`.

## Wiring the file it reads

`fileRef` is a runtime reference to an upstream output or flow variable, not a value:

```json
"fileRef": "=js:$vars.<trigger>.output.invoice"
```

Set it at creation when possible:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.<trigger>.output.invoice"}' --output json
```

Use the plain `=js:$vars.…` string. The structured form `{"type":"jsExpression","expression":"$vars.…","fieldType":"object"}` validates only when `fieldType` is present. A literal filename or hand-built attachment object remains literal and does not resolve upstream.

Use the trigger's declared file field; for a SharePoint-backed event declaring `ReferenceID`, wire `$vars.<trigger>.output.ReferenceID`. Read the trigger contract; do not guess or insert a download step.

For direct document input, run:

```bash
uip maestro flow variables create <file> invoice -d in -t file --description 'The invoice document to extract' --output json
```

This makes `$vars.<trigger>.output.invoice` resolvable; declaration and wiring are separate. An undeclared input may validate with an `EXPRESSION_DIAGNOSTIC` warning naming the missing input; treat that `fileRef` warning as an error.

Connect the graph:

```bash
uip maestro flow edges create <file> <upstream-id> <extract-id> --output json
uip maestro flow edges create <file> <extract-id> <downstream-id> --output json
```

`edges create` uses the default source port, so outgoing edges use `success`. Graph ports (`success`, `error`) differ from variable outputs (`output`, `error`). Repeating an edge is safe and reports the existing edge.

## Reading what it extracts

Read values at `$vars.<extract-node-id>.output.result.output`. The `output` port carries a whole processed document with top-level `version`, `type`, `result`, `taxonomy`, and `metadata`; `result` contains `output` (values keyed by taxonomy field), `attribution` (page locations keyed by JSON Pointer into `output`), and `traceContext`. Use `result.output` for values and the port itself for the whole document.

The embedded definition is authoritative: read `definitions[]` for this node type at `outputDefinition.output.schema.properties`. (`registry get` answers `Node not found` because no tenant manifest carries this type.)

**`ExtractionResult` is the published-model node's output, not this one.** Its `ExtractionResult.ResultsDocument.Fields[]` belongs to [ixp.md](ixp.md), and the shapes are not interchangeable.

The `error` port carries failures. Wire recovery with `edges create --source-port error`; leaving it unwired makes the flow fail loudly.

## Returning the result

Declare an output, add an End node, connect the extract node, then bind the output directly in the End node:

```bash
uip maestro flow variables create <file> extractedData -d out -t object --description 'The structured data extracted from the document' --output json
uip maestro flow nodes create <file> core.control.end --label 'End' --output json
uip maestro flow edges create <file> <extract-id> <end-id> --output json
```

Write this into the End node's `outputs` block; there is no CLI command for the binding:

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

`var` names the global and `source` fills it. For a subset or reshaped result, put a script between the extract node and End and bind that script's output. **There is no `variableUpdates` block on an End node;** validation rejects that shape.

## Validating

Run:

```bash
uip maestro flow validate <file> --output json
```

Validation requires `fileRef` to be a `$vars` reference, both output ports to be named on the instance, and no top-level `model` block. A newly created node fails only on unwired `fileRef`; that is expected.

## Making it actually extract

<!--skill-flavor:extract-processor-sync:start-->
At runtime, the service resolves `inputs.processorKey` to a solution resource containing its taxonomy. Run `nodes create` to mint the key and write the resource; run `nodes schema set` to write it for a node without a processor or update it in place; run `uip solution pack` to regenerate it from the node so the deployed processor matches the latest taxonomy. Keep the `.flow` and `resources/` file together when storing, uploading, or versioning the solution.
<!--skill-flavor:extract-processor-sync:end-->

A pre-provisioned, hand-written, or `.flow.ts`-compiled node may lack a processor; `validate` errors. Repair the whole file by running:

```bash
uip maestro flow nodes provision <file> --output json
```

Never hand-write `processorKey` or reuse another node's key. Each processor holds one node's definition; duplicate authorship makes pack or publish refuse. Deliberate sharing requires the reader to take the author's `processorKey` and set `inputs.processorReadOnly: true`; neither half works alone and validation rejects a read-only node without a key.

For a second node with identical fields and model settings, supply both inputs at creation:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract credit note' --input '{"fileRef":"=js:$vars.start.output.creditNote","processorKey":"<the authoring node key>","processorReadOnly":true}' --output json
```

A read-only node has no resource or taxonomy; it runs the author's processor. `nodes schema set` changes nothing that deploys when run on it.

A package without a processor may fault at runtime:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

It may first complete in a fraction of a second and publish an empty object. Treat that as a missing processor: provision, then pack or publish again.

<!--skill-flavor:extract-after-save:start-->
After Studio Web edits a pulled-down flow, pull the solution again before further CLI edits so the designer's saved changes are not overwritten; it saves continuously. The node retains its type, `processorKey`, and resource file. A Studio Web processor variant (`uipath.ixp.processor.<key>`) is a different type: `nodes schema set` refuses it and its taxonomy must be edited in Studio Web.
<!--skill-flavor:extract-after-save:end-->

## When Extract document is not available

Use the reason from `Data.Reason` or the deploy/run message, including unsupported details. Never add the node or substitute a placeholder when working extraction was requested.

**First, look for a published IXP model:**

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a suitable model exists, report the tenant result, identify and justify the replacement, verify its taxonomy covers the request, and build it via [ixp.md](ixp.md). State what it does not cover: published models extract only trained fields.

If none exists, stop. State the tenant, reported reason, absence of a trained model, and that enabling extraction requires a tenant administrator and UiPath product documentation. Do not scaffold, write a flow, or put `mock()` in the extraction position. A placeholder is permitted only for a validate-only topology explicitly showing where extraction belongs, never as expected extraction.

## Unsupported Capabilities

These requests are outside the skill. Recognize them, give the standard response, and route the user. Do NOT enter discovery (`uip --help`, grep, source reading). For uncovered settings or resources, do not seek a CLI path or edit `.flow`, `.flow.ts`, or project files. Say it is unavailable here and link [Extract document documentation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/introduction).

| User request | Standard response |
|---|---|
| "Pick the best model settings for these documents" / "tune the node for speed or accuracy" | "I can't change the node's model configuration from here. See [Model configuration](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model)." |
| "Use GPT-5 / Gemini Pro" / "change the extraction model" | "I can't change the extraction model of this node from here. See [Choosing the most suitable model](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#choosing-the-most-suitable-model) and [Switching from one model to another](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#switching-from-one-model-to-another)." |
| "Change the extraction strategy" / "use the Standard / Advanced strategy" | "I can't change the extraction strategy from here. See [Configuring the model](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#configuring-the-model)." |
| "Switch the language to Arabic / Japanese" / "set language to Auto-detect / Latin-based / Extended" | "I can't change language support from here. See [Language support](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#language-support)." |
| "Set layout parsing to None / Full" / "turn layout parsing on / off" | "I can't change layout parsing from here. See [Layout parsing](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#layout-parsing)." |
| "Use Rules-based / Model-based attribution" | "I can't change attribution from here. See [Attribution](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#attribution)." |
| "Add model overrides" / "set the overrides JSON" | "I can't set model configuration overrides from here. See [Overrides](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#overrides)." |
| "Import this IXP taxonomy file" (a file with `entity_defs` and `label_groups`) / "Export the taxonomy as an IXP file" | "I can't import or export IXP taxonomy files from here. Use Import/Export in the flow designer: [Importing and exporting taxonomies](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/importing-and-exporting-taxonomies). I can show the taxonomy, replace it from a flow-format file, or copy it from another Extract document node." |
| "Upload these documents" / "delete a test file" / "tag these documents" / "show the documents not annotated yet" / "reuse the other Extract node's documents" | "I can't manage the node's test documents from here. See [Uploading sample documents](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/uploading-sample-documents)." |
| "What would it extract from this file?" / "refresh the predictions" | "I can't run or refresh predictions for this node. See [Reviewing predictions](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/generating-and-reviewing-predictions)." |
| "Confirm these values" / "annotate the documents" | "I can't annotate test documents. See [Validating predicted values](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/validating-extractions)." |
| "Set up the evaluators" / "how should this field be scored?" | "I can't configure the node's evaluators. See [Running an evaluation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/running-an-evaluation)." |
| "Run an eval" / "evaluate on this one file" / "what's my score?" / "compare the eval runs" / "improve the accuracy" | "I can't run or read evaluations for this node. See [Running an evaluation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/running-an-evaluation) and [Evaluating model performance](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/evaluating-model-performance)." |

## Evidence boundary

This is offline file authoring except the tenant registry lookup. `validate` proves wiring and shape: resolvable upstream `fileRef`, named ports, valid taxonomy, and a processor. It does not prove extraction; deploy and run against real documents, usually followed by taxonomy refinement.
