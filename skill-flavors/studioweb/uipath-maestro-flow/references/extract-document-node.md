<!--skill-flavor:extract-find-flow:start-->
0. **Find the flow.** The target `.flow` is the open file at `CurrentFile.AbsolutePath`, in the open solution — nothing to pull down ([Project layout](../SKILL.md#project-layout)).
<!--skill-flavor:extract-find-flow:end-->

<!--skill-flavor:extract-sdk-mixing:start-->
**A flow that holds this node takes the decompile round trip** of the [Lifecycle](../SKILL.md#lifecycle): the node decompiles to `dynamicExtract()`, its `processorKey` with it. When merge's in-memory baseline compile fails on this node (an SDK copy before 6.118.0), do not decompile such a flow at all: make every change with the direct commands on the target `.flow` — `nodes`, `edges`, `variables`, `nodes schema` — and finish with `validate`.
<!--skill-flavor:extract-sdk-mixing:end-->

<!--skill-flavor:extract-processor-sync:start-->
At run time the extraction service resolves which processor to use from `inputs.processorKey`, a solution resource holding its own copy of the taxonomy. This host has no `.uipx`, so `nodes create` and `nodes schema set` add the processor to the open solution instead of writing a file under `resources/`. Nothing else creates it: the designer provisions only nodes without a key. So `ResourcePending` here means the node has no processor. When the message names a retry, run it once; otherwise, or if it reports `ResourcePending` again, report the message and stop.
<!--skill-flavor:extract-processor-sync:end-->

<!--skill-flavor:extract-after-save:start-->
Re-read the target `.flow` at the start of each turn rather than reusing an earlier copy: the designer saves as the user edits, with no save button. The node keeps its type, its `processorKey` and its resource file across those saves. A node the user added as the processor variant (`uipath.ixp.processor.<key>`) is a different node type — `nodes schema set` refuses it, and its taxonomy is edited in the designer.
<!--skill-flavor:extract-after-save:end-->

<!--skill-flavor:extract-model-settings:start-->
For an Extract document node setting or resource that this guide does not cover, do not look for a CLI path and do not edit the `.flow`, `.flow.ts` or project files to reach it. Say it is not available from here and link the [Extract document documentation](https://docs.uipath.com/ixp/automation-cloud/latest/flow-user-guide/introduction). The one exception in Studio Web is the model setup: strategy, model, language support, layout parsing and attribution are set through [Setting up the model](extract-document-taxonomy.md#setting-up-the-model), through the `ProposeModelSetup` host tool, never by editing the `.flow`.

| User request | Standard response |
|--------------|-------------------|
<!--skill-flavor:extract-model-settings:end-->

<!--skill-flavor:extract-taxonomy-writes:start-->
Add the node with a name that says what it extracts, wire the file it reads, write the taxonomy, validate.

In Studio Web a request to set up, define or be guided through a node's taxonomy (the "guided Extract setup", "start guiding me through defining my taxonomy") starts by reading [extract-document-taxonomy.md](extract-document-taxonomy.md) and following its steps in order. The first question is its single upload question for the use case and samples; never open with a document-type or "one type or several" choice, and never build a wizard of your own.

In Studio Web every taxonomy write goes through the `ProposeTaxonomyChange` host tool, including a one-field rename: the first draft and each change after it, as [Changing the taxonomy in chat](extract-document-taxonomy.md#changing-the-taxonomy-in-chat) describes. Never write a taxonomy with `EditFile`, `WriteFile` or a script on the `.flow`, and never with `uip maestro flow nodes schema set`. Read [extract-document-taxonomy.md](extract-document-taxonomy.md) before any taxonomy change. Use `mode` `"create"` only for a node with no fields yet; any change to existing fields, a one-field rename included, is `mode` `"edit"` with every changed field listed in `changes`, so the user sees the diff they approve.
<!--skill-flavor:extract-taxonomy-writes:end-->
