# Classify & Split Guide

Deciding whether a workload needs document classification, physical splitting, both, or neither — and
what is documented today.

## The capability exists; its configuration is not yet documented

IxP exposes classifier models (type `Classifier`) that label documents rather than extracting named
fields. They share the `uipath.ixp.*` node-type pattern and appear in the Flow registry after
`uip login` and `uip maestro flow registry pull`, exactly like extraction models.

What is missing is **documentation of the node's configuration and output shape**, not the capability.
[/uipath:uipath-maestro-flow — plugins/ixp/impl.md](../../uipath-maestro-flow/references/author/plugins/ixp/impl.md)
§ Classifier Variant states this directly: classifier output is classification labels rather than field
values, and its configuration is deferred.

So: discover the model, do not invent a node type, and do not assume the extraction node's `output`
shape applies.

```bash
uip login
uip maestro flow registry pull --force
uip maestro flow registry search "<model-or-doc-type>" --output json
```

[/uipath:uipath-maestro-flow — plugins/ixp/planning.md](../../uipath-maestro-flow/references/author/plugins/ixp/planning.md)
§ Listing Available Models / Runtime Projects covers the listing question. Model authoring, taxonomy, and
publishing belong to [/uipath:uipath-ixp — SKILL.md](../../uipath-ixp/SKILL.md).

## Decide what the workload actually needs

Work down this list and stop at the first match.

| Situation | What to do |
|---|---|
| One known document type per file | Nothing. Skip classification and splitting entirely; go straight to Extract |
| Types already in separate files, but routing depends on the label | Classify only, then branch on the label with a Switch node |
| Several logical documents inside one file | Determine boundaries, and split physically only if downstream processing requires separate documents |
| Known, fixed page ranges | A deterministic split in a script — no model needed, if the runtime has the required library |
| Unknown labels or unknown boundaries | A published classifier model, discovered from the registry |

Two failure modes this ordering prevents: classifying when the answer was already known, and extracting
a packet as one document — which merges unrelated headers and produces fields from the wrong form.

## Boundaries that decide the route

- **A label is not a split.** An agent or a classifier returning "this is an invoice" has produced a
  string. Physical segmentation of a PDF is separate work with a separate output — segment artifacts and
  their original page ranges.
- **Repeated instances of one type still need boundaries.** Three invoices in one file is a splitting
  problem even though classification has nothing to decide.
- **Locating a document does not validate it.** Finding the contract does not establish that it is
  signed, current, or the right version. That is downstream evidence analysis.
- **Retrieval cannot enumerate document instances.** Top-k search over a packet can miss additional
  copies and cannot produce a verified boundary map. Use classification and splitting, not search.
- **An agent's classification proposal is not production classification.** It may be appropriate when
  error costs are low and a review path exists. Evaluate it against the actual cost of a confusion, and
  never substitute it silently for a specialist model.

## Asymmetric error costs

When one confusion costs far more than others — approving something that should have been denied, for
instance — overall accuracy is the wrong measure.

1. Enumerate the classes, and name the confusing pairs explicitly.
2. Evaluate the critical confusions separately from overall accuracy.
3. Route uncertain cases to review rather than raising a threshold until the numbers look acceptable.
4. Hold the critical-error target ahead of the straight-through-processing target. High overall accuracy
   does not make the critical class safe.

Do not manufacture calibrated confidence from a model's self-rating.

## Always preserve correspondence to the source

Whatever performs the split, the output must carry: the label, the **original** page ranges, a reference
to each segment artifact, and an explicit unresolved status where boundaries could not be determined.
Downstream review and audit depend on tracing a field back to a page in the file the user supplied.

When a document crosses an input segment boundary, reconcile the boundary across segments before
reporting page ranges.

## If nothing is published yet

Mark the component unresolved, name the dependency — a classifier model trained and published to an
Orchestrator folder — and continue authoring the independent nodes. `uipath-maestro-flow` documents a
mock-node procedure for holding the graph shape while the model is pending, with downstream consumers
wired through `$vars` so the swap is mechanical.

A request for a draft does not justify inventing a working endpoint, and a mock never belongs in a path
described as production.

Cases: [CS1–CS3](case-library-guide.md#cs-classify--split).
