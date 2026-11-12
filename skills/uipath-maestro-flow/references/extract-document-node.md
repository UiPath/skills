# Extract document node

*Commands: `uip maestro flow extraction check`, `uip maestro flow nodes create`, `uip maestro flow edges create`, `uip maestro flow validate`.*

An Extract document node (`uipath.ixp.extract-document-builder`) pulls named fields out of a document using a taxonomy it carries inline, in the `.flow` file itself. There is no trained model or IXP project behind it. This guide covers getting the node into the flow: adding it, wiring the file it reads, and validating. Designing what it extracts is the taxonomy, in [extract-document-taxonomy.md](extract-document-taxonomy.md).

```bash
uip maestro flow extraction check --output json
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label '<name>' --input '{"fileRef":"=js:$vars.<upstream>.output.<field>"}' --output json
uip maestro flow validate <file> --output json
```

**Support for this node is new.** A CLI that predates it refuses the type, and the `nodes` group itself answers `error: unknown command` on a CLI older still. Either means the installed `uip` is behind the commands rather than the node being wrong — say so and ask the user to update.

## Which extraction node the user wants

The default for document extraction in a flow is a published IXP model, covered in [ixp.md](ixp.md), where the IXP project is built and deployed first and the flow then runs against it. Use the Extract document node only when the user asks for it by name or is already using it: the flow holds a node of type `uipath.ixp.extract-document-builder` (`uip maestro flow nodes list <file> --output json` shows the types), or the request is about the taxonomy an Extract document node carries inline. A published-model node's taxonomy lives in its IXP project and belongs to `uipath-ixp`.

Three node families share the `uipath.ixp.` prefix and they are not interchangeable:

| Node | Node type | Where it is covered |
| --- | --- | --- |
| Extract document | `uipath.ixp.extract-document-builder` | this guide |
| A published IXP model — the default | `uipath.ixp.<project>.<version>-<folder>` | [ixp.md](ixp.md) |
| An IDP processor resource inside the solution | `uipath.ixp.processor.<resource-key>` | not covered here — add it in Studio Web |

The processor variant looks the same and is built from the same definition, but it is a different node type pointing at a processor resource that lives in the solution. The conveniences below apply to `uipath.ixp.extract-document-builder` and to nothing else, so a processor node added through the CLI arrives incomplete. Leave those to Studio Web.

## At a glance

Add the node with a name that says what it extracts, wire the file it reads, write the taxonomy, validate.

```bash
uip maestro flow nodes create Flow/Flow.flow uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
uip maestro flow nodes list Flow/Flow.flow --output json
uip maestro flow validate Flow/Flow.flow --output json
```

`fileRef` is the one input only the author can supply, and the flow does not validate without it. The taxonomy is written next, in [extract-document-taxonomy.md](extract-document-taxonomy.md). The processor the extraction runs through arrives with the node, and packing keeps it in step ([Making it actually extract](#making-it-actually-extract)).

## The loop

<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** Everything here edits a `.flow` on disk. When the user describes a flow they are already building and none exists locally, they may be referring to one
that lives in Studio Web and has to be pulled down first — ask them for its URL or solution id, since nothing lists them ([Starting from a flow in Studio Web](extract-document-taxonomy.md#starting-from-a-flow-in-studio-web)).
<!--skill-flavor:extract-find-flow:end-->
1. **Check the tenant can run it:** `uip maestro flow extraction check --output json`. Anything other than `Available` stops the loop here ([Check the tenant can run it](#check-the-tenant-can-run-it)).
2. **Declare the file the flow takes in,** unless it already has one: `uip maestro flow variables create <file> invoice -d in -t file --description '<what the document is>'`. This is what makes `$vars.start.output.invoice` resolve, so it comes before the node that reads it.
3. **Add the node** with `--label` naming what it extracts, and `--input` carrying `fileRef`.
4. **Connect it in the graph** with `edges create` ([Wiring the file it reads](#wiring-the-file-it-reads)).
5. **Write the taxonomy** — [extract-document-taxonomy.md](extract-document-taxonomy.md).
6. **Bind the result to a flow output** so the extraction leaves the flow — [Returning the result](#returning-the-result).
7. **Validate:** `uip maestro flow validate <file> --output json` must come back `Valid`.
8. **Report** what was added, where it reads its file from, what it extracts, and what `nodes create` reported about its processor: inside a solution the resource file was written under `resources/` and travels with the `.flow`, and outside one it is still to be created ([Making it actually extract](#making-it-actually-extract)). Taking the flow live is the user's step.

## Check the tenant can run it

Document extraction is enabled per tenant, and the models it extracts with are granted per tenant too. Ask before you author:

```bash
uip maestro flow extraction check --output json
```

`Data.Status` is the answer, and only `Available` means the node is worth adding:

| Status | What it means |
| --- | --- |
| `Available` | document extraction is on for this tenant, and it has a model to extract with |
| `FeatureDisabled` | a tenant administrator has to turn document extraction on |
| `ServiceUnavailable` | this environment serves no document extraction |
| `ModelUnavailable` | extraction is on, but the tenant has no model to extract with |
| `Unknown` | a service answered without settling it, so nothing is proven |

The command reports on the signed-in tenant, and `-t <tenant-name>` checks for another tenant. On anything other than `Available`, go to [When Extract document is not available](#when-extract-document-is-not-available). That includes `Unknown`, which leaves the question open rather than answering it.

Nothing else in the CLI answers this, so do not read one of these in its place. `nodes create` and `validate` are local file edits, so they succeed on any tenant. `registry search` reports `AvailableOnTenant: false` for this node on every tenant, because the node reaches the canvas from a builder rather than from the tenant's node catalogue.

**`Available` is not a promise that a run succeeds.** It covers the two gates the check can read. Extraction can still be refused later, at deploy or on the first run, for a reason no read-only call shows beforehand:

- the environment does not run structured extraction, which a stock Automation Suite install does not
- the model this node is configured with is not among the ones the tenant is granted, which the check does not look at — it asks only whether the tenant has any
- model-based attribution, full layout parsing or an OCR language pack is configured and not granted, each being a separate grant
- the user cannot run it in the target folder

Treat any of these the same way as a check that came back unavailable: report what the service said and go to [When Extract document is not available](#when-extract-document-is-not-available). Do not hand over a flow with the node still in it as working, and do not try folders in turn looking for one that passes.

Where the refusal names the model, say which one the node carries and that the tenant is not granted it. Never swap in another model quietly: which model extracts is the user's choice, and changing it is not something this guide does ([Unsupported Capabilities](#unsupported-capabilities)). Where the user never named a model, say that another of the tenant's models may suit and let them choose. Where they asked for that model by name, the answer is that this tenant cannot run it.

## Adding the node

<!--skill-flavor:extract-sdk-mixing:start-->
**These commands edit the `.flow` file, so they do not mix with a project built from TypeScript source.** A project initialised with `--sdk-source` generates its `.flow` from a `.flow.ts` by compiling, and the next compile overwrites whatever `nodes create` and `nodes schema set` wrote. Check for a `.flow-sdk/` directory before starting. Where one exists, build the Extract document flow in a separate project without source and keep to the CLI — the SDK's `dynamicExtract()` is not the route here ([document-pipeline.md](document-pipeline.md) explains its limits). Do not alternate between the two and re-apply the CLI edits after each compile.
<!--skill-flavor:extract-sdk-mixing:end-->

`--label` sets the canvas name and seeds the node id. Give it a name that says which document and which fields, not "Extract" — a flow with two extraction nodes is common, and the label is what the user reads on the canvas and in a trace. Run `uip maestro flow nodes list <file> --output json` afterwards to get the id that was minted; later commands address the node by that id.

The created node already carries everything else it needs:

| What it gets | Why it matters |
| --- | --- |
| `inputs.schemaDocument` | an empty taxonomy with the six built-in field types defined, so the first taxonomy written to it never has to invent a type shape |
| `inputs.modelConfig` | working model defaults, so the node runs without being configured |
| `inputs.source` | a minted identifier for the node's own extraction; nothing for you to supply |
| `inputs.processorKey` and `inputs.processorName` | the processor the extraction runs through; inside a solution its resource file is written too, and outside one the output says `ResourcePending` and pack creates it later ([Making it actually extract](#making-it-actually-extract)) |
| `outputs.output` and `outputs.error` | both ports named on the instance, which is what lets a downstream `$vars` read resolve |
| no top-level `model` block | the slim manifest model belongs in `definitions[]`, and validation rejects a copy on the instance |

`nodes create` writes `modelName`, `folderKey` and the other deployment fields under `inputs` as empty strings — leave them empty. They name a trained IXP deployment and belong to the published-model node in [ixp.md](ixp.md); this node requires only `fileRef`, and filled-in values sit there unread.

## Wiring the file it reads

`fileRef` says which document the node extracts from. It is a reference evaluated when the flow runs, not a value, and it must name an upstream node's output or a flow variable:

```json
"fileRef": "=js:$vars.start.output.invoice"
```

Set it at creation when the upstream node already exists:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
```

Write it as the plain `=js:$vars.…` string above, the simplest form that validates. The structured form `{"type":"jsExpression","expression":"$vars.…","fieldType":"object"}` also validates, but only with `fieldType` present — without it the value is not recognised as an expression and validation rejects it twice over. A literal file name or a hand-built attachment object reaches the runtime as a literal and the upstream output never resolves.

Where the file comes from depends on the trigger. A connector event carries its own file-reference field, named in the trigger's output definition — a SharePoint-backed event declaring `ReferenceID` is wired as `$vars.start.output.ReferenceID`. Read the trigger's contract rather than guessing the field name, and do not insert a download step to change the shape; this node takes the reference directly.

A flow that simply takes a document in needs that input declared before anything can reference it:

```bash
uip maestro flow variables create <file> invoice -d in -t file --description 'The invoice document to extract' --output json
```

That is what makes `$vars.start.output.invoice` resolve. Declaring it on the trigger is a separate step from wiring it into the node. A `fileRef` pointing at an input that was never declared still validates, with an `EXPRESSION_DIAGNOSTIC` warning naming the missing input — treat that warning on `fileRef` as an error.

Then connect the node in the graph:

```bash
uip maestro flow edges create <file> <upstream-id> <extract-id> --output json
uip maestro flow edges create <file> <extract-id> <downstream-id> --output json
```

`edges create` picks the node's default source port, so the outgoing edge leaves on `success` without a flag. The graph ports (`success`, `error`) are distinct from the variable outputs read with `$vars` (`output`, `error`), which share a name on the error side only.

Adding the same edge twice is safe — the command reports the existing edge rather than creating a duplicate.

## Reading what it extracts

The extracted fields arrive two levels down the node's `output` port, one property per taxonomy field:

```js
$vars.<extract-node-id>.output.result.output
```

The port carries a whole processed document, of which the extracted values are one part. Its top level has `version`, `type`, `result`, `taxonomy` and `metadata`. Inside `result` sit `output` (the values, keyed by field name), `attribution` (where on the page each value came from, keyed by a JSON Pointer into `output`) and `traceContext`. Reach for `result.output` when a downstream step wants the data, and for the port itself when something wants the document whole.

The flow file embeds the definition it was created with, so should the shape evolve, read it off the file itself: the `definitions[]` entry for this node type, at `outputDefinition.output.schema.properties`. (`registry get` answers `Node not found` for this type, since no tenant manifest carries it.)

**`ExtractionResult` is the published-model node's output, not this one.** The two nodes emit different shapes, and a downstream step written against the wrong one reads a key that is not there. `ExtractionResult.ResultsDocument.Fields[]` belongs to the node in [ixp.md](ixp.md).

The `error` port carries failures. Wire it with `edges create --source-port error` when an unreadable document should follow a recovery path; leaving it unwired means the flow fails loudly instead, which is often the right behaviour.

## Returning the result

Extraction that nothing reads is not much use, so the flow usually declares an output carrying it. That takes three steps, and the last one has no CLI command — write it into the `.flow` file directly rather than going looking for a verb that does it.

Declare the output global, then add an End node and wire the extract node to it:

```bash
uip maestro flow variables create <file> extractedData -d out -t object --description 'The structured data extracted from the document' --output json
uip maestro flow nodes create <file> core.control.end --label 'End' --output json
uip maestro flow edges create <file> <extract-id> <end-id> --output json
```

The binding itself lives in the End node's own `outputs` block, keyed by the output's name:

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

`var` names the declared global and `source` is the expression that fills it. Returning the extracted values means pointing `source` at `result.output`; a flow that returns only part of them, or reshapes them, puts a script between the extract node and the End node and binds that script's output instead.

**There is no `variableUpdates` block on an End node.** That shape belongs elsewhere in the format and `validate` rejects it here, so a flow output written that way fails with no obvious cause.

## Validating

```bash
uip maestro flow validate <file> --output json
```

For this node, validation enforces that `fileRef` is a `$vars` reference rather than a literal, that both output ports are named on the instance, and that no top-level `model` block is present. A freshly created node fails on `fileRef` alone until it is wired — that failure is the expected state, not a fault.

## Making it actually extract

<!--skill-flavor:extract-processor-sync:start-->
At run time the extraction service resolves which processor to use from `inputs.processorKey`, a solution resource holding its own copy of the taxonomy. The CLI provisions it while you author: `nodes create` mints the key and writes the processor's resource file into the enclosing solution, `nodes schema set` does the same for a node that has none, and `uip solution pack` regenerates the resource from the node — so the deployed processor matches the taxonomy last written. The `.flow` and the resource file under `resources/` belong together: whatever stores, uploads or versions the solution must carry both, since pack builds from what it is given.
<!--skill-flavor:extract-processor-sync:end-->

A node from before the CLI provisioned anything, one written by hand, or one compiled from `.flow.ts` source, arrives without a processor. `validate` reports it as an error, and one command repairs the whole file:

```bash
uip maestro flow nodes provision <file> --output json
```

Never write a `processorKey` by hand, and never give a node another node's key as its own: a processor holds exactly one node's extraction definition, and a solution where two nodes define the same one refuses to pack or publish. A node that deliberately runs another node's processor is the one place a key is shared — it takes that node's `processorKey` and sets `inputs.processorReadOnly: true` alongside it, so the key says which processor it reads and the flag says it is not the author. Neither half works without the other: a read-only node carrying no key names nothing to read, and validation rejects it.

A second node that extracts the same fields with the same model settings as an existing one is a node of this kind, rather than a copy of its taxonomy: it runs the processor that node defines, so whatever deploys for one deploys for both. Both inputs go on when the node is created, since nothing adds them to a node that already exists:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract credit note' --input '{"fileRef":"=js:$vars.start.output.creditNote","processorKey":"<the authoring node key>","processorReadOnly":true}' --output json
```

Such a node gets no resource file of its own, and it holds no taxonomy of its own either — the extraction it runs is the one the authoring node defines. Writing a schema to it changes nothing that deploys, which is what `nodes schema set` reports when it is run on one.

A package built from a node without a processor faults at run time:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

and before that fault the step can look like it worked: it completes in a fraction of a second and publishes an empty object. Treat a deployed extract step behaving that way as shipped without its processor — provision, then pack or publish again — rather than as a taxonomy that matched nothing.

<!--skill-flavor:extract-after-save:start-->
When the flow has been through Studio Web since it was pulled down, pull the solution again before editing it further, so a later CLI write does not overwrite what the designer saved — it saves as the user edits, with no save button. The node comes back as it went: the designer keeps its type, its `processorKey` and its resource file. A node the user added there as the processor variant (`uipath.ixp.processor.<key>`) is a different node type — `nodes schema set` refuses it, and its taxonomy is edited in Studio Web.
<!--skill-flavor:extract-after-save:end-->

## When Extract document is not available

This covers both answers: a check that came back as anything other than `Available`, and a refusal that arrives later from deploy or a run. Take the reason from whichever reported it — `Data.Reason` from the check, or the service's own message — and keep it in what you say, including when it names something this guide does not describe.

Never add the node anyway, and never substitute a placeholder for it when the user asked for working extraction. Fall back in two steps.

**First, look for a published IXP model.** The user may already have a trained project that does the job:

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a published model fits what the user described, say what the check reported about this tenant, say which model you are using instead and why, and build with it following [ixp.md](ixp.md). The two nodes are not equivalent — a published model extracts the fields it was trained on, so check its taxonomy covers what the user asked for before offering it, and say plainly what it does not cover.

**If there is no published model either, stop and explain.** Say which tenant was checked and what the check reported — `Data.Reason` says it in a sentence — that no trained model is available on it either, and that enabling document extraction is a tenant administrator action covered in the UiPath product documentation. Do not scaffold a solution, do not write a flow file, and do not put a `mock()` in the extraction position — a placeholder is only for a validate-only topology whose stated purpose is to show where extraction belongs, and it is never a stand-in for extraction the user expects to run.

## Unsupported Capabilities

These requests fall outside the skill. Recognise the request, reply with the standard response, route the user. Do NOT enter discovery (`uip --help`, grep, source reading).

For an Extract document node setting or resource that this guide does not cover, do not look for a CLI path and do not edit the `.flow`, `.flow.ts` or project files to reach it. Say it is not available from here and link the [Extract document documentation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/introduction).

| User request | Standard response |
|--------------|-------------------|
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

Everything here is offline file authoring, apart from the registry lookup, which needs login to see what the tenant serves. `validate` proves the node is wired and shaped correctly — that `fileRef` resolves to something upstream, that the ports are named, that the taxonomy is well formed, that the node has its processor. It proves nothing about what the node extracts: that takes a deploy and a run against real documents, which usually sends the taxonomy back for a round of tightening.
