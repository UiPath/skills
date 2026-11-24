# Extract document node

*Commands: `uip maestro flow extraction check`, then the SDK loop (`decompile`, `check`, `compile` or `merge`) and `uip maestro flow validate`. Exact factory signature: `dynamicExtract()` ([document-pipeline.md](document-pipeline.md)).*

Add this node to a new flow only when the user names it ([Which extraction node the user wants](#which-extraction-node-the-user-wants)). "We don't have a trained model yet" does not name it; that request goes to [ixp.md](ixp.md).

An Extract document node (`uipath.ixp.extract-document-builder`) extracts named fields using taxonomy embedded in the `.flow`; it has no trained model or IXP project. In source it is one `dynamicExtract()` step. Add, wire, and validate it; design taxonomy in [extract-document-taxonomy.md](extract-document-taxonomy.md).

```bash
uip maestro flow extraction check --output json
# new flow: scaffold, then author the step in .flow-sdk/<Name>.flow.ts and compile (SKILL.md, Lifecycle)
# existing flow: decompile, edit the source, check, merge (SKILL.md, Editing an existing flow)
uip maestro flow validate <file> --output json
```

```ts
.input({ invoice: { type: types.file, description: 'The invoice document to extract' } })
.step('extractInvoice', dynamicExtract({ fileRef: input('invoice'), schema: invoiceTaxonomy }),
  { label: 'Extract invoice' })
```

**Support for this node is new.** It needs `@uipath/maestro-builder-sdk` 6.119.0 or later; a merge that repairs or edits an existing node needs 6.124.16 or later ([Making it actually extract](#making-it-actually-extract)). Read the installed version before blaming the SDK (`npm ls -g @uipath/maestro-builder-sdk`, or the project's `node_modules`); below the floor, upgrade it ([document-pipeline.md](document-pipeline.md#authoring-it-the-processor-and-the-sdk-it-needs)).

## Which extraction node the user wants

In a new flow, document extraction is a published IXP model, covered in [ixp.md](ixp.md): the IXP project is built and deployed first, and the flow then runs against it. That holds when no model exists yet ([ixp.md](ixp.md#resource-identity)). Add the Extract document node to a new flow only when the user asks for it by name, or offer it when `uipath-ixp` reports IXP not enabled. In an existing flow, keep the extraction node it has (each node's `type` in the `.flow`; decompile writes this one as `dynamicExtract()`); a builder node or its inline taxonomy stays on this guide. A published-model taxonomy belongs to `uipath-ixp`.

| Node | Node type | Where covered |
| --- | --- | --- |
| Extract document | `uipath.ixp.extract-document-builder` | this guide |
| Published IXP model — default | `uipath.ixp.<project>.<version>-<folder>` | [ixp.md](ixp.md) |
| IDP processor resource | `uipath.ixp.processor.<resource-key>` | not covered; add it in Studio Web |

The three `uipath.ixp.` families are not interchangeable. The processor variant looks the same and uses the same definition, but points to a solution processor resource and is a different type. The conveniences below apply only to `uipath.ixp.extract-document-builder`; a processor node is added and edited in Studio Web.

## At a glance

Add a descriptive `dynamicExtract()` step, wire its file, write taxonomy, return the result, and validate. `fileRef` is the only author-supplied input and is required for validation. Compile or merge gives the node its processor; packing keeps it synchronized ([Making it actually extract](#making-it-actually-extract)).

## The loop

<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** Work on a `.flow` on disk. If the user describes a flow they are already building and none exists locally, it may live in Studio Web and need pulling down first; ask for its URL or solution id; nothing lists them ([Starting from a flow in Studio Web](extract-document-taxonomy.md#starting-from-a-flow-in-studio-web)).
<!--skill-flavor:extract-find-flow:end-->
1. **Check the tenant:** run `uip maestro flow extraction check --output json`. Any settled answer other than `Available` stops the loop; an unsettled check is a question for the user ([Check the tenant can run it](#check-the-tenant-can-run-it)).
2. **Get the source.** A new flow: scaffold it ([SKILL.md, Project layout](../SKILL.md#project-layout)). An existing flow: decompile it ([SKILL.md, Editing an existing flow](../SKILL.md#editing-an-existing-flow)); a supplied `.flow-sdk/<Name>.flow.ts` is edited where it is ([brownfield.md](brownfield.md#a-supplied-source)).
3. **Declare the input if absent:** `.input({ invoice: { type: types.file, description: '<what the document is>' } })`. The trigger then carries it as `$vars.<trigger>.output.invoice`.
4. **Add the step** where the flow reads the document, with a `label` naming what it extracts ([Adding the node](#adding-the-node)). Chaining it after its predecessor is its incoming edge ([Wiring the file it reads](#wiring-the-file-it-reads)). Same model as an existing Extract document node: the step takes that node's `processorKey` and `processorReadOnly: true`, and step 5 is skipped ([Making it actually extract](#making-it-actually-extract)).
5. **Write the taxonomy** in the step's `schema`: [extract-document-taxonomy.md](extract-document-taxonomy.md).
6. **Return the result** as a flow output ([Returning the result](#returning-the-result)).
7. **Check and write:** run `check`, then `compile` (new flow) or `merge` (existing flow), as the SKILL.md loop says. Then run `uip maestro flow validate <file> --output json`; it must return `Valid`.
<!--skill-flavor:extract-report:start-->
8. **Report** what was added, where it reads its file from, which fields it extracts, and the processor: compile and merge print `wrote resources/solution_folder/idpProcessor/extraction/<Label>.json (IDP processor)` inside a solution, and keep that file with the `.flow`; outside one, they print that the file is created when the project is packed ([Making it actually extract](#making-it-actually-extract)). Taking the flow live is the user's step.
<!--skill-flavor:extract-report:end-->

## Check the tenant can run it

Before adding a new node, run:

```bash
uip maestro flow extraction check --output json
```

The check answers, for the signed-in tenant, whether extraction is on and whether any model exists. `Data.Status` is the result and `Data.Reason` explains it:

| Status | Meaning |
| --- | --- |
| `Available` | both gates open |
| `FeatureDisabled` | extraction is off; a tenant administrator must enable it |
| `ModelUnavailable` | extraction is on but no model is available |
| `ServiceUnavailable` | no document-extraction service is available |
| `Unknown` | the service answered without settling either gate |

Continue on `Available`; use [When Extract document is not available](#when-extract-document-is-not-available) for the other three settled failures. `Unknown`, non-zero exit, expired login, and old CLI do not establish unavailability: report the command result and ask whether to try adding the node; if nobody can answer, add it and report that the check settled nothing.

This gates only adding a new node. Edits to an existing node, its taxonomy, the repair of a missing processor, and validation go ahead whatever the status says; report the status alongside them.

`Available` proves only its two gates. Deploy or run may still refuse the configured model, a cluster-wide switch, model-based attribution, full layout parsing, OCR language packs, or target-folder permissions. Take the fallback in [When Extract document is not available](#when-extract-document-is-not-available) when one arrives. Do not call the node working after such a refusal and do not try folders in turn. If the refusal names the model, say which one the node carries and direct the user to [Switching from one model to another](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/configuring-the-model#switching-from-one-model-to-another); changing it is the user's step. If the user requested that model by name, say instead that this tenant cannot run it.

No other CLI command answers this question. `registry search` reports `AvailableOnTenant: false` for this node on every tenant because it comes from a builder, not the tenant node catalogue.

## Adding the node

<!--skill-flavor:extract-sdk-mixing:start-->
**Author the node in the source, never in the `.flow`.** In a project with `.flow-sdk/<Name>.flow.ts`, add the step there; otherwise decompile first ([SKILL.md, Editing an existing flow](../SKILL.md#editing-an-existing-flow)). A hand edit of the `.flow` is overwritten by the next compile and skips everything compile does for the node.
<!--skill-flavor:extract-sdk-mixing:end-->

```ts
.step('extractInvoice', dynamicExtract({ fileRef: input('invoice'), schema: invoiceTaxonomy }),
  { label: 'Extract invoice' })
```

The step name is the node id; the `label` sets the canvas name and the processor's name. Name the document and fields, not "Extract", since flows often have two extraction nodes. Pass no `model`: compile gives the node its working model defaults (`inputs.modelConfig`), an empty taxonomy with the six built-in field types when `schema` is omitted, a minted extraction identifier (`inputs.source`), the processor (`inputs.processorKey` and `inputs.processorName`; in a solution its resource file is written, otherwise it is created when the project is packed ([Making it actually extract](#making-it-actually-extract))), and the named `output` and `error` ports for downstream reads.

Keep `modelName`, `folderKey`, and other deployment fields out of the step. They identify a trained IXP deployment and belong to [ixp.md](ixp.md); this node requires only `fileRef`.

## Wiring the file it reads

`fileRef` is a runtime reference to an upstream output or flow variable, not a value. For direct document input, declare the input and read it:

```ts
.input({ invoice: { type: types.file, description: 'The invoice document to extract' } })
.step('extractInvoice', dynamicExtract({ fileRef: input('invoice') }), { label: 'Extract invoice' })
```

Compile writes it as `"fileRef": "=js:$vars.<trigger>.output.invoice"`. Declaration and wiring are separate: `input('invoice')` with no `invoice` input still validates, with an `EXPRESSION_DIAGNOSTIC` warning naming the missing input; treat that `fileRef` warning as an error. A literal filename or hand-built attachment object remains literal and does not resolve upstream.

Use the trigger's declared file field; for a SharePoint-backed event declaring `ReferenceID`, read `$vars.<trigger>.output.ReferenceID`. Read the trigger contract; do not guess or insert a download step.

Chaining the step is its incoming edge: `.step('extractInvoice', …)` after the step that precedes it, and the next `.step(…)` is its outgoing edge on `success`. To insert it into an existing path, move the old edge through it rather than adding a second path ([SKILL.md, Editing an existing flow](../SKILL.md#editing-an-existing-flow)). Graph ports (`success`, `error`) differ from variable outputs (`output`, `error`).

## Reading what it extracts

Read values at `$vars.<extract-node-id>.output.result.output`. The `output` port carries a whole processed document with top-level `version`, `type`, `result`, `taxonomy`, and `metadata`; `result` contains `output` (values keyed by taxonomy field), `attribution` (page locations keyed by JSON Pointer into `output`), and `traceContext`. Use `result.output` for values and the port itself for the whole document.

The embedded definition is authoritative: read `definitions[]` for this node type at `outputDefinition.output.schema.properties`. (`registry get` answers `Node not found` because no tenant manifest carries this type.)

**`ExtractionResult` is the published-model node's output, not this one.** Its `ExtractionResult.ResultsDocument.Fields[]` belongs to [ixp.md](ixp.md), and the shapes are not interchangeable.

The `error` port carries failures. Wire it with `.onError(…)` only when an unreadable document should follow a recovery path ([error-handling.md](error-handling.md)); leaving it unwired makes the flow fail loudly, often the right behaviour.

## Returning the result

Declare an output and return the extracted values from the step:

```ts
.output({ extractedData: { type: types.object, description: 'The structured data extracted from the document' } })
// … the steps, ending with the extract step …
.return({ extractedData: out('extractInvoice', 'result.output') })
```

Compile writes the End node's `outputs.extractedData`, whose `source` reads `$vars.extractInvoice.output.result.output`. There is no `variableUpdates` block on an End node; validation rejects that shape. For a subset or reshaped result, put a `script()` between the extract step and the return and return that script's output ([return.md](return.md)).

## Validating

Run:

```bash
uip maestro flow validate <file> --output json
```

Validation requires `fileRef` to be a `$vars` reference, both output ports to be named on the instance, a processor (`inputs.processorKey`), and no top-level `model` block. Compile and merge write all of them; a failure names what the source still lacks.

## Making it actually extract

<!--skill-flavor:extract-processor-sync:start-->
At runtime, the service resolves `inputs.processorKey` to a solution resource containing its taxonomy. Compile and merge provision it while you author: compile mints the key, one per step and the same on every recompile; inside a solution, compile and merge write the resource (`resources/solution_folder/idpProcessor/extraction/<Label>.json`) for each node they write, keep it in step with the node's taxonomy, and declare it in `bindings_v2.json`; `uip solution pack` regenerates it from the node so the deployed processor matches the latest taxonomy. Keep the `.flow` and `resources/` file together when storing, uploading, or versioning the solution.
<!--skill-flavor:extract-processor-sync:end-->

A node from before processors were provisioned, or written by hand, arrives without a processor; `validate` reports an error at `inputs.processorKey`. Repair it with the brownfield loop and no edit: decompile, then `merge`. Merge gives every Extract document node that authors a processor but names none the key compile minted for it, and writes its resource file, printing `named no IDP processor … gave it <key>` and `wrote …/<Label>.json (IDP processor)`. This needs SDK 6.124.16 or later; on an older SDK the merged node stays keyless: upgrade the SDK. If `validate`'s message suggests another command, do not run it: the round trip is the repair.

Never hand-write `processorKey` or give a node another node's key as its own. Each processor holds one node's definition; duplicate authorship makes pack or publish refuse. Deliberate sharing requires the reader to take the author's `processorKey` and set `inputs.processorReadOnly: true`; neither half works alone and validation rejects a read-only node without a key.

A node's model is its processor: its taxonomy and model settings together. A second node that uses the same model as an existing one reads that node's processor rather than getting a copy of its own; never a new processor synced to the same taxonomy and model. Give the step both inputs, since nothing adds them later. The author's key is in the decompiled source (`processorKey: "…"` on its step) and in its `.flow` node:

```ts
.step('extractCreditNote', dynamicExtract({
  fileRef: input('creditNote'),
  processorKey: '<the authoring node key>',
  processorReadOnly: true,
}), { label: 'Extract credit note' })
```

A read-only node has no resource or taxonomy of its own: compile mints it no key and writes no file; it runs the author's processor. A `schema` on it changes nothing that deploys.

A package without a processor faults at runtime:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

It may first complete in a fraction of a second and publish an empty object. Treat that as a missing processor, not a taxonomy that matched nothing: repair it as above, then pack or publish again.

<!--skill-flavor:extract-after-save:start-->
After a pulled-down flow has been through Studio Web, pull the solution again and decompile again before further edits, so the designer's saved changes are not overwritten; it saves continuously. The node retains its type, `processorKey`, and resource file. A Studio Web processor variant (`uipath.ixp.processor.<key>`) is a different type, not `dynamicExtract()`: its taxonomy must be edited in Studio Web.
<!--skill-flavor:extract-after-save:end-->

## When Extract document is not available

`uipath-ixp` reporting IXP not enabled is not this case; `extraction check` decides. Report the reason from `Data.Reason` or the deploy/run message, even when it names something this guide does not describe. Never add the node anyway, and never substitute a placeholder when working extraction was requested.

**First, look for a published IXP model:**

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a suitable model exists, verify its taxonomy covers the request, then report the tenant result, identify and justify the replacement, and build it via [ixp.md](ixp.md). State what it does not cover: published models extract only trained fields.

If none exists, stop. State the tenant, reported reason, absence of a trained model, and that enabling extraction is a tenant administrator action covered in UiPath product documentation. Do not scaffold a solution, write a flow, or put `mock()` in the extraction position. A placeholder is permitted only for a validate-only topology explicitly showing where extraction belongs, never as expected extraction.

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

This is offline file authoring except the tenant extraction check. `validate` proves wiring and shape: resolvable upstream `fileRef`, named ports, valid taxonomy, and a processor. It does not prove extraction: that takes a deploy and a run against real documents, which usually sends the taxonomy back for tightening.
