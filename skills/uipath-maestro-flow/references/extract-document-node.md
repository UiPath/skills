# Extract document node

*Commands: `uip maestro flow nodes create`, `uip maestro flow edges create`, `uip maestro flow validate`.*

An Extract document node (`uipath.ixp.extract-document-builder`) pulls named fields out of a document using a taxonomy it carries inline, in the `.flow` file itself. There is no trained model or IXP project behind it. A user may call it Extract v2, its name during development; Extract document is the product name and the one to use with them. This guide covers getting the node into the flow: adding it, wiring the file it reads, and validating. Designing what it extracts is the taxonomy, in [extract-document-taxonomy.md](extract-document-taxonomy.md).

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label '<name>' --input '{"fileRef":"=js:$vars.<upstream>.output.<field>"}' --output json
uip maestro flow validate <file> --output json
```

**Support for this node is new.** A CLI that predates it refuses the type, and the `nodes` group itself answers `error: unknown command` on a CLI older still. Either means the installed `uip` is behind the commands rather than the node being wrong — say so and ask the user to update.

## Which extraction node the user wants

The default for document extraction in a flow is a published IXP model, covered in [ixp.md](ixp.md), where the IXP project is built and deployed first and the flow then runs against it. Use the Extract document node only when the user asks for it, by either name, or is already using it: the flow holds a node of type `uipath.ixp.extract-document-builder` (`uip maestro flow nodes list <file> --output json` shows the types), or the request is about the taxonomy an Extract document node carries inline. A published-model node's taxonomy lives in its IXP project and belongs to `uipath-ixp`.

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

`fileRef` is the one input only the author can supply, and the flow does not validate without it. The taxonomy is written next, in [extract-document-taxonomy.md](extract-document-taxonomy.md), and the node extracts nothing until the user saves the flow once in Studio Web ([Making it actually extract](#making-it-actually-extract)).

## The loop

0. **Find the flow.** Everything here edits a `.flow` on disk. When the user describes a flow they are already building and none exists locally, they may be referring to one
that lives in Studio Web and has to be pulled down first — ask them for its URL or solution id, since nothing lists them ([Starting from a flow in Studio Web](extract-document-taxonomy.md#starting-from-a-flow-in-studio-web)).
1. **Declare the file the flow takes in,** unless it already has one: `uip maestro flow variables create <file> invoice -d in -t file --description '<what the document is>'`. This is what makes `$vars.start.output.invoice` resolve, so it comes before the node that reads it.
2. **Add the node** with `--label` naming what it extracts, and `--input` carrying `fileRef`.
3. **Connect it in the graph** with `edges create` ([Wiring the file it reads](#wiring-the-file-it-reads)).
4. **Write the taxonomy** — [extract-document-taxonomy.md](extract-document-taxonomy.md).
5. **Bind the result to a flow output** so the extraction leaves the flow — [Returning the result](#returning-the-result).
6. **Validate:** `uip maestro flow validate <file> --output json` must come back `Valid`.
7. **Report** what was added, where it reads its file from, and what it extracts, and tell the user about the Studio Web save ([Making it actually extract](#making-it-actually-extract)). Taking the flow live is their step too.

## Not available everywhere

The feature is new and tenant-gated, so not every tenant has it yet. Nothing in the CLI shows the difference — creating and validating succeed either way, and `registry search` reports `AvailableOnTenant: false` for this node on every tenant — but the Studio Web node picker lists **Extract document** where it is enabled. Keep the gating in mind as a possible cause of errors. Where the tenant turns out not to have the feature, or on Automation Suite, where structured extraction ships switched off, go to [When Extract document is not available](#when-extract-document-is-not-available).

## Adding the node

**These commands edit the `.flow` file, so they do not mix with a project built from TypeScript source.** A project initialised with `--sdk-source` generates its `.flow` from a `.flow.ts` by compiling, and the next compile overwrites whatever `nodes create` and `nodes schema set` wrote. Check for a `.flow-sdk/` directory before starting. Where one exists, build the Extract document flow in a separate project without source and keep to the CLI — the SDK's `dynamicExtract()` is not the route here ([document-pipeline.md](document-pipeline.md) explains its limits). Do not alternate between the two and re-apply the CLI edits after each compile.

`--label` sets the canvas name and seeds the node id. Give it a name that says which document and which fields, not "Extract" — a flow with two extraction nodes is common, and the label is what the user reads on the canvas and in a trace. Run `uip maestro flow nodes list <file> --output json` afterwards to get the id that was minted; later commands address the node by that id.

The created node already carries everything else it needs:

| What it gets | Why it matters |
| --- | --- |
| `inputs.schemaDocument` | an empty taxonomy with the six built-in field types defined, so the first taxonomy written to it never has to invent a type shape |
| `inputs.modelConfig` | working model defaults, so the node runs without being configured |
| `inputs.source` | a minted identifier for the node's own extraction; nothing for you to supply |
| `outputs.output` and `outputs.error` | both ports named on the instance, which is what lets a downstream `$vars` read resolve |
| no top-level `model` block | the slim manifest model belongs in `definitions[]`, and validation rejects a copy on the instance |

Do not write `model`, `modelName` or `folderKey` under `inputs` either. Those name a trained IXP deployment and belong to the published-model node in [ixp.md](ixp.md). This node requires only `fileRef`; validation does not reject deployment fields under `inputs`, so they sit there unread.

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

That is what makes `$vars.start.output.invoice` resolve. Declaring it on the trigger is a separate step from wiring it into the node, and a `fileRef` pointing at an input that was never declared validates as a broken expression.

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

The flow file embeds the definition it was created with, so `uip maestro flow registry get uipath.ixp.extract-document-builder --output-filter 'keys(Node.outputDefinition.output.schema.properties)' --output json` can confirm the actual output schema should that evolve over time.

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

Validation checks this node against the definition `nodes create` embedded in the `.flow` itself, which is how it passes despite never appearing in a tenant manifest; the tenant's manifests, cached by `registry pull` and kept thirty minutes, are a cross-check for edge handles and other node types. For this node it enforces that `fileRef` is a `$vars` reference rather than a literal, that both output ports are named on the instance, and that no top-level `model` block is present. A freshly created node fails on `fileRef` alone until it is wired — that failure is the expected state, not a fault.

## Making it actually extract

A node authored entirely through the CLI validates and deploys, but extracts nothing until the user opens the flow in Studio Web and saves it once. Say this when handing the work over, rather than letting them discover it from a failed run.

At run time the extraction service resolves which processor to use from `inputs.processorKey`, a tenant-side resource holding its own copy of the taxonomy. Nothing in the CLI provisions one. Running without it faults the instance:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

Before that fault the node may appear to succeed: the element completes in a fraction of a second and publishes an empty object, which reads as a working step returning nothing rather than as a missing one. Treat an extract step that finishes that fast, or returns `{}`, as unprovisioned rather than as a taxonomy that matched nothing.

The Studio Web save is what provisions the processor; extraction works from then on. Do not synthesise a `processorKey`, and do not copy one from another node — it names a different taxonomy.

One thing to expect on the way back. Saving in Studio Web may convert the node to the processor variant (`uipath.ixp.processor.<key>`), which is a different node type from the one that was created. Pull the solution down again before editing it further, so a later CLI write does not overwrite what Studio Web wrote — and where the pulled node is the processor variant, `nodes schema set` refuses it, and the taxonomy is edited in Studio Web from then on.

## When Extract document is not available

Never add the node anyway, and never substitute a placeholder for it when the user asked for working extraction. Fall back in two steps.

**First, look for a published IXP model.** The user may already have a trained project that does the job:

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a published model fits what the user described, say that Extract document is not enabled on this tenant, say which model you are using instead and why, and build with it following [ixp.md](ixp.md). The two nodes are not equivalent — a published model extracts the fields it was trained on, so check its taxonomy covers what the user asked for before offering it, and say plainly what it does not cover.

**If there is no published model either, stop and explain.** Say which tenant was checked, that neither Extract document nor a trained model is available on it, and that enabling document extraction is a tenant administrator action covered in the UiPath product documentation. Do not scaffold a solution, do not write a flow file, and do not put a `mock()` in the extraction position — a placeholder is only for a validate-only topology whose stated purpose is to show where extraction belongs, and it is never a stand-in for extraction the user expects to run.

## What this guide does not cover

**The test set and the scorer.** A node's extraction dataset and its evaluator are created in Studio Web today; the CLI refuses to author an eval set targeting a document node and says so. Add the node and its taxonomy, then tell the user that seeding test documents and scoring them is their next step in Studio Web.

**Going live.** Publishing and deploying stay the user's decision, in Studio Web.

## Evidence boundary

Everything here is offline file authoring, apart from the registry lookup, which needs login to see what the tenant serves. `validate` proves the node is wired and shaped correctly — that `fileRef` resolves to something upstream, that the ports are named, that the taxonomy is well formed. It proves nothing about what the node extracts: that takes the Studio Web save ([Making it actually extract](#making-it-actually-extract)) and then a run against real documents, which usually sends the taxonomy back for a round of tightening.
