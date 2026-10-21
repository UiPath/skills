# Extract v2 node

*Commands: `uip maestro flow nodes create`, `uip maestro flow edges create`, `uip maestro flow validate`.*

An Extract v2 node (`uipath.ixp.extract-document-builder`) pulls named fields out of a document using a taxonomy it carries inline, in the `.flow` file itself. The product calls it **Extract document**, which is the name to use when talking to the user; Extract v2 is the internal name for the feature and appears in the CLI's own output. There is no trained model and no IXP project behind it, so a user who has never built one can add extraction to a flow in a single session. This guide covers getting the node into the flow: establishing that the tenant has it, adding it, wiring the file it reads, and validating. Designing what it extracts is the taxonomy, in [extract-v2-taxonomy.md](extract-v2-taxonomy.md).

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label '<name>' --input '{"fileRef":"=js:$vars.<upstream>.output.<field>"}' --output json
uip maestro flow validate <file> --output json
```

## Which extraction node the user wants

Three node families share the `uipath.ixp.` prefix and they are not interchangeable. Decide before adding anything.

| What the user has | Node type | Where it is covered |
| --- | --- | --- |
| Nothing trained — they describe the fields they want in words | `uipath.ixp.extract-document-builder` | this guide |
| A published IXP project with a trained model | `uipath.ixp.<project>.<version>-<folder>` | [ixp.md](ixp.md) |
| An IDP processor resource inside the solution | `uipath.ixp.processor.<resource-key>` | not covered here — add it in Studio Web |

Choose Extract v2 when the user says what to extract ("pull the invoice number, total and line items"). Choose the published model when they name an existing IXP project, model or deployment, or ask for a model someone has already trained. When the request is ambiguous, check what the tenant publishes before asking — a tenant with no published models has only one real option.

The processor variant looks like Extract v2 and is built from the same definition, but it is a different node type pointing at a processor resource that lives in the solution. The conveniences below apply to `uipath.ixp.extract-document-builder` and to nothing else, so a processor node added through the CLI arrives incomplete. Leave those to Studio Web.

## At a glance

Establish the tenant has the node, add it with a name that says what it extracts, wire the file it reads, write the taxonomy, validate.

```bash
uip maestro flow nodes create Flow/Flow.flow uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
uip maestro flow nodes list Flow/Flow.flow --output json
uip maestro flow validate Flow/Flow.flow --output json
```

A created node arrives complete apart from the file it reads. `fileRef` is the one input only the author can supply, and the flow does not validate without it. A valid flow is not yet a running one: the node extracts nothing until the user saves the flow once in Studio Web ([Making it actually extract](#making-it-actually-extract)).

## The loop

1. **Establish whether the tenant has the node.** The CLI cannot tell you — ask the user, under [Checking availability](#checking-availability). Where the answer is no, go to [When Extract v2 is not available](#when-extract-v2-is-not-available) and do not add it.
2. **Add the node** with `--label` naming what it extracts, and `--input` carrying `fileRef` when the upstream node already exists.
3. **Connect it in the graph** with `edges create`, so it runs in the right place.
4. **Write the taxonomy** — [extract-v2-taxonomy.md](extract-v2-taxonomy.md).
5. **Validate:** `uip maestro flow validate <file> --output json` must come back `Valid`.
6. **Report** what was added, where it reads its file from, and what it extracts — and tell the user to open the flow in Studio Web and save it, because until they do the node extracts nothing ([Making it actually extract](#making-it-actually-extract)). Taking it live is their step too.

## Checking availability

**The CLI cannot answer this question yet, and two things that look like answers are not.**

The registry carries a row for the node, and that row's `AvailableOnTenant` always reads `false`:

```bash
uip maestro flow registry search 'extract-document-builder' --output json
```

```json
{ "NodeType": "uipath.ixp.extract-document-builder", "DisplayName": "Extract v2", "AvailableOnTenant": false }
```

That `false` says nothing about the tenant. A tenant manifest is built from the out-of-the-box node catalogue, and this node is not in it — Studio Web adds it to the canvas from a builder, behind a feature flag. The CLI knows the node from its own bundled catalogue, which is why the row exists at all, and marks it unavailable because the tenant did not serve it. Every tenant answers the same way, enabled or not. Do not gate on it and do not report it to the user as a finding.

`nodes create` is not an answer either. The CLI builds this node's manifest locally for the same reason, so creating it succeeds on a tenant that cannot run it. The flow then fails at runtime rather than at authoring time.

So until the CLI grows a real check, ask instead of guessing. Tell the user you cannot verify it from here, and ask whether **Extract document** appears in their node picker in Studio Web. Their answer is the check. If they do not know, say plainly that you are building on the assumption it is enabled and that they should confirm before relying on the flow — then build, rather than stalling on a question they may not be able to answer.

**Ask about "Extract document", not "Extract v2".** The node is named Extract document in the product, and that is the only name the user sees. "Extract v2" is what the CLI's bundled catalogue still calls it, which is why the registry row above reads that way, and it is what the team calls the feature. A user looking at a picker that says Extract document will answer no to a question about Extract v2, and the node will be refused on a tenant that has it.

Treat the feature as unavailable without asking in one case: a deployment on Automation Suite, where structured extraction ships switched off. Go to [When Extract v2 is not available](#when-extract-v2-is-not-available).

## Adding the node

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract Invoice' --output json
```

**These commands edit the `.flow` file, so they do not mix with a project built from TypeScript source.** A project initialised with `--sdk-source` generates its `.flow` from a `.flow.ts` by compiling, and the next compile overwrites whatever `nodes create` and `nodes schema set` wrote. Check for a `.flow-sdk/` directory before starting. Where one exists, either author the whole flow from source and accept that this node cannot be authored that way at all ([document-pipeline.md](document-pipeline.md) explains why the SDK factory does not fit it), or build the flow in a project without source and keep to the CLI. Do not alternate between the two and re-apply the CLI edits after each compile.

`--label` sets the canvas name and seeds the node id. Give it a name that says which document and which fields, not "Extract" — a flow with two extraction nodes is common, and the label is what the user reads on the canvas and in a trace. Run `uip maestro flow nodes list <file> --output json` afterwards to get the id that was minted; later commands address the node by that id.

The created node already carries everything else it needs:

| What it gets | Why it matters |
| --- | --- |
| `inputs.schemaDocument` | an empty taxonomy with the six built-in field types defined, so the first taxonomy written to it never has to invent a type shape |
| `inputs.modelConfig` | working model defaults, so the node runs without being configured |
| `inputs.source` | a minted identifier for the node's own extraction; nothing for you to supply |
| `outputs.output` and `outputs.error` | both ports named on the instance, which is what lets a downstream `$vars` read resolve |
| no top-level `model` block | the node carries no model deployment, and validation rejects one if it is there |

Do not write `model`, `modelName` or `folderKey` onto this node. Those name a trained IXP deployment and belong to the published-model node in [ixp.md](ixp.md); the Extract v2 node requires only `fileRef` and ignores them.

## Wiring the file it reads

`fileRef` says which document the node extracts from. It is a reference evaluated when the flow runs, not a value, and it must name an upstream node's output or a flow variable:

```json
"fileRef": "=js:$vars.start.output.invoice"
```

Set it at creation when the upstream node already exists:

```bash
uip maestro flow nodes create <file> uipath.ixp.extract-document-builder --label 'Extract Invoice' --input '{"fileRef":"=js:$vars.start.output.invoice"}' --output json
```

Two shapes are accepted — the plain `=js:$vars.…` string above, and the structured form `{"type":"jsExpression","expression":"$vars.start.output.invoice"}` with no `=js:` prefix inside it. Prefer the plain string: it is what Studio Web writes for this node family. Anything else, including a literal file name or a hand-built attachment object, reaches the runtime as a literal and the upstream output never resolves.

Where the file comes from depends on the trigger. A flow started with a file input reads `$vars.start.output.<input name>`. A connector event carries its own file-reference field, named in the trigger's output definition — a SharePoint-backed event declaring `ReferenceID` is wired as `$vars.start.output.ReferenceID`. Read the trigger's contract rather than guessing the field name, and do not insert a download step to change the shape; this node takes the reference directly.

Then connect the node in the graph:

```bash
uip maestro flow edges create <file> <upstream-id> <extract-id> --output json
uip maestro flow edges create <file> <extract-id> <downstream-id> --output json
```

Adding the same edge twice is safe — the command reports the existing edge rather than creating a duplicate.

## Reading what it extracts

The result arrives on the node's `output` port, under `processedDocument`:

```js
$vars.<extract-node-id>.output.processedDocument
```

**`ExtractionResult` is the published-model node's output, not this one.** The two nodes emit different shapes, and a downstream step written against the wrong one reads a key that is not there. `ExtractionResult.ResultsDocument.Fields[]` belongs to the node in [ixp.md](ixp.md); Extract v2 emits `processedDocument`, whose contents follow the taxonomy the node carries.

The `error` port carries failures. Wire it with `edges create --source-port error` when an unreadable document should follow a recovery path; leaving it unwired means the flow fails loudly instead, which is often the right behaviour.

## Validating

```bash
uip maestro flow validate <file> --output json
```

Validation checks the flow against the tenant's node manifests, read from the cache `registry pull` writes and kept thirty minutes; `--force` refetches them. For this node it enforces that `fileRef` is a `$vars` reference rather than a literal, that both output ports are named on the instance, and that no top-level `model` block is present. A freshly created node fails on `fileRef` alone until it is wired — that failure is the expected state, not a fault.

## Making it actually extract

**A node authored entirely through the CLI validates, deploys, and then extracts nothing.** The flow is correct; it is not yet runnable. Say this to the user as part of handing the work over, rather than letting them discover it from a failed run.

At run time the extraction service resolves which processor to use from `inputs.processorKey`, a tenant-side resource holding its own copy of the taxonomy. Nothing in the CLI provisions one. Running without it faults the instance:

```
errorCode 461008 — Invalid IDP.Extraction node input
'processorKey' is required and must be a GUID, unless a processor name and folder are provided to resolve one
```

Before that fault the node may appear to succeed: the element completes in a fraction of a second and publishes an empty object, which reads as a working step returning nothing rather than as a missing one. Treat an extract step that finishes that fast, or returns `{}`, as unprovisioned rather than as a taxonomy that matched nothing.

**Opening the flow in Studio Web and saving it is what provisions the processor.** So the handover is: the flow is built and valid, the user saves it once in Studio Web, and extraction works from then on. Do not try to synthesise a `processorKey`, and do not write one copied from another node — it names a different taxonomy.

One thing to expect on the way back. Saving in Studio Web may convert the node to the processor variant (`uipath.ixp.processor.<key>`), which is a different node type from the one that was created. Pull the solution down again before editing it further, so a later CLI write does not overwrite what Studio Web wrote.

## When Extract v2 is not available

This is a normal outcome, not an error to work around. On Automation Suite structured extraction ships switched off, so refusing is the default experience there rather than the exception. Never add the node anyway, and never substitute a placeholder for it when the user asked for working extraction.

Fall back in two steps.

**First, look for a published IXP model.** The user may already have a trained project that does the job:

```bash
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```

If a published model fits what the user described, say that Extract v2 is not enabled on this tenant, say which model you are using instead and why, and build with it following [ixp.md](ixp.md). The two nodes are not equivalent — a published model extracts the fields it was trained on, so check its taxonomy covers what the user asked for before offering it, and say plainly what it does not cover.

**If there is no published model either, stop and explain.** Say which tenant was checked, that neither Extract v2 nor a trained model is available on it, and that enabling document extraction is a tenant administrator action covered in the UiPath product documentation. Do not scaffold a solution, do not write a flow file, and do not put a `mock()` in the extraction position — a placeholder is only for a validate-only topology whose stated purpose is to show where extraction belongs, and it is never a stand-in for extraction the user expects to run.

## What this guide does not cover

**The test set and the scorer.** A node's extraction dataset and its evaluator are created in Studio Web today; the CLI refuses to author an eval set targeting a document node and says so. Add the node and its taxonomy, then tell the user that seeding test documents and scoring them is their next step in Studio Web.

**Going live.** Publishing and deploying stay the user's decision, in Studio Web.

## Evidence boundary

Everything here is offline file authoring, apart from the registry lookup, which needs login to see what the tenant serves. `validate` proves the node is wired and shaped correctly — that `fileRef` resolves to something upstream, that the ports are named, that the taxonomy is well formed. It proves nothing about what the node extracts, and a green validate does not mean the node can run at all: that needs the processor the user provisions by saving in Studio Web. Only a run against real documents, after that save, shows what the taxonomy actually pulls out, and it usually needs a round of tightening afterwards.
