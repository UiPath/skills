# Reinstating CS — Classify & Split

Classify & Split is withheld from this release. The capability exists — IxP publishes classifier models
and they appear in the Flow registry — but its node configuration and output shape are not documented,
so an agent routed to CS cannot finish the build. Rather than ship a strategy that dead-ends, CS comes
out, and this file holds everything that was removed, verbatim, with where each piece goes back.

Work top to bottom. The counts at the end of each file section are the part no script checks.

> **Prerequisite.** Reinstate only once the classifier node's configuration and `output` shape are
> documented. That is the single fact whose absence caused the withdrawal; nothing else about CS changed.

> **Links in this file are deliberately de-linked**, rendered as `` `text → target` ``. A live Markdown
> link to a file this release no longer contains fails `npm run skills:check-links`. Restore them to real
> links as you paste each block back.

---

## 0. Read first — CS is a prerequisite, not a destination

PA was something a workload escalated *to*, so withdrawing it left nothing dangling. **CS is something
Extract goes *through*.** Three places encoded "separate the documents before extracting", and they were
not deleted — they were rewritten to state the obligation without naming a strategy:

| Site | Now reads | On reinstatement |
|---|---|---|
| `SKILL.md` workflow step 3 | "Mixed logical documents must be separated before EX. This release routes no strategy for that separation…" | restore "Mixed logical documents need CS before EX" |
| `SKILL.md` EX reject column | "…boundary resolution is a prerequisite this release does not route…" | restore "Logical documents are still mixed together" |
| `case-library-guide.md` EX1 boundary | "Packets need their document boundaries established first." | restore "Packets need CS1 first." |

Do not simply re-add the CS row and leave those three rewritten. The skill would then state the
obligation twice, once with a destination and once without.

---

## 1. `SKILL.md`

### 1a. Frontmatter description

Insert `Classify & Split vs ` after `choose Extract vs `. 702 characters without CS, 722 with it; cap 1024.

### 1b. Fast Routing — reinsert the CS row directly after the AF row

```markdown
| **CS** | Classify & Split | Mixed document types or several logical documents in one file, and routing or splitting depends on the label | No classifier model is published, or the label actually requires absence proof or policy reasoning |
```

The paragraph below the table reads "The other **five** are fixed capabilities"; restore it to **six**.

### 1c. When to Use — restore the capability in the list

Restore `classify and split` after `extract fields,`.

### 1d. Workflow step 3 — restore the destination

Currently:

```markdown
3. **Check document boundaries before extraction.** Mixed logical documents must be separated before EX.
   This release routes no strategy for that separation: resolve it deterministically (known page ranges,
   a separator convention) or report it as an unresolved dependency. Never extract a packet as one
   document — it merges unrelated headers and produces fields from the wrong form.
```

Restore to:

```markdown
3. **Check document boundaries before extraction.** Mixed logical documents need CS before EX. Route each
   step separately, and name one primary strategy for the requested deliverable.
```

### 1e. Reference Navigation — reinsert the row

Deleted rather than retargeted; the guide it pointed at did not survive.

```markdown
| Classification and physical splitting, and what is not yet documented | `classify-split-guide.md → references/classify-split-guide.md` |
```

### 1f. Anti-patterns — no change needed

"Treating an agent's class label as a physical split" was **kept**. It guards a real failure whether or
not CS ships, so do not add it again.

---

## 2. `references/classify-split-guide.md` — restore the whole file

Unlike PA's `search-strategy-guide.md`, which was shared with PS and so rewritten, this file was 100% CS
and was deleted outright. Recreate it exactly as below. **Both `skill-flavor` marker blocks must come
back with it** — a sparse override binds to them and the flavor build fails if either side is missing.

````markdown
# Classify & Split Guide

Deciding whether a workload needs document classification, physical splitting, both, or neither — and
what is documented today.

## The capability exists; its configuration is not yet documented

IxP exposes classifier models (type `Classifier`) that label documents rather than extracting named
fields. They share the `uipath.ixp.*` node-type pattern and appear in the Flow registry after
`uip login` and `uip maestro flow registry pull`, exactly like extraction models.

What is missing is **documentation of the node's configuration and output shape**, not the capability.
<!--skill-flavor:classify-ixp-impl:start-->
`/uipath:uipath-maestro-flow — plugins/ixp/impl.md → ../../uipath-maestro-flow/references/ixp.md`
<!--skill-flavor:classify-ixp-impl:end-->
§ Classifier Variant states this directly: classifier output is classification labels rather than field
values, and its configuration is deferred.

So: discover the model, do not invent a node type, and do not assume the extraction node's `output`
shape applies.

```bash
uip login
uip maestro flow registry pull --force
uip maestro flow registry search "<model-or-doc-type>" --output json
```

<!--skill-flavor:classify-ixp-planning:start-->
`/uipath:uipath-maestro-flow — plugins/ixp/planning.md → ../../uipath-maestro-flow/references/ixp.md`
<!--skill-flavor:classify-ixp-planning:end-->
§ Listing Available Models / Runtime Projects covers the listing question. Model authoring, taxonomy, and
publishing belong to `/uipath:uipath-ixp — SKILL.md → ../../uipath-ixp/SKILL.md`.

## Decide what the workload actually needs

Work down this list and stop at the first match.

| Situation | What to do |
|---|---|
| One known document type per file | Nothing. Skip classification and splitting entirely; go straight to Extract |
| Types already in separate files, but routing depends on the label | Classify only, then branch on the label with a Switch node |
| Several logical documents inside one file | Determine boundaries, and split physically only if downstream processing requires separate documents |
| Known, fixed page ranges | A deterministic split in a script — no model needed, if the runtime has the required library |
| Unknown labels or unknown boundaries | A published classifier model, discovered from the registry |

Two failure strategies this ordering prevents: classifying when the answer was already known, and extracting
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

Cases: `CS1–CS3 → case-library-guide.md#cs-classify--split`.
````

### 2a. The studioweb flavor override — restore in the same commit

Path: `skill-flavors/studioweb/uipath-doc-strategy-select/references/classify-split-guide.md`

`scripts/compose-skill-flavor.mjs` fails both ways: a canonical file with no override markers fails at
`:538`, an override whose canonical target is missing fails at `:524`. Restore both or neither.

````markdown
<!--skill-flavor:classify-ixp-impl:start-->
`/uipath:uipath-maestro-flow — plugins/ixp/impl.md → ../../uipath-maestro-flow/references/author/plugins/ixp/impl.md`
<!--skill-flavor:classify-ixp-impl:end-->

<!--skill-flavor:classify-ixp-planning:start-->
`/uipath:uipath-maestro-flow — plugins/ixp/planning.md → ../../uipath-maestro-flow/references/author/plugins/ixp/planning.md`
<!--skill-flavor:classify-ixp-planning:end-->
````

---

## 3. `references/case-library-guide.md`

### 3a. Reinsert the whole CS section between `## AF` and `## SU`

````markdown
## CS Classify & Split

Read `classify-split-guide.md → classify-split-guide.md` before these cases — classifier models exist, but
their node configuration is not yet documented.

### CS1 Locate documents in a large packet

**Problem description.** Thousand-page, image-only bundles arrive at high monthly volume, and several
named document types are buried somewhere inside each one. The job is to find them and their page ranges,
apply a rule about which copy is authoritative when the same document appears more than once, and only
then extract fields from what survives. Working behaviour: original page ranges come back for every
target document, including one that straddles an input segment boundary, and the record shows which
duplicate was retained and why.

**Best-fit solution.** A published classifier model discovered from the registry, or a deterministic
script split for known page ranges. Bind the resulting segments to Extract.

**Decision reasoning.** The decisive signal is that document boundaries are unknown inside a single
physical file — extraction cannot start until they are established. Segment the input if the
digitization budget requires it, preserve original page numbering, and reconcile document boundaries
across segments. Apply the duplicate rule deterministically to the candidates, then extract fields per
retained document.

**Negative example — counterexample.** Extracting the whole packet as one document merges unrelated
headers and fields. Using top-k retrieval to locate document instances can miss additional copies and
cannot produce a verified boundary map.

**Boundary.** Repeated documents of one type still need boundary separation. Already-separated files may
need classification only. Locating a document does not establish its validity — do not discard competing
copies before the duplicate rule can be evaluated.

### CS2 Isolate a contract before checking its signature

**Problem description.** A bundle contains many documents and the first task is simply to find one
specific contract inside it. A later, separate task asks whether the buyer actually signed that contract.
Conflating the two is the trap: locating a document says nothing about its validity. Working behaviour:
given a bundle containing several signed forms and an unsigned target contract, the correct contract is
isolated and the unsigned result is returned — no signature is borrowed from a neighbouring form.

**Best-fit solution.** A published classifier plus splitting. The downstream signature check is a separate
specialist capability, not an agent tool. Preserve segment references through verification.

**Decision reasoning.** The decisive signal is that one specific document must be isolated from a mixed
bundle before any evidence question can be asked of it. Classify and split out the target contract, pass
that segment to the signature check and, where required, an independent visual verification. Preserve
segment-to-original-page mapping and any disagreement between the two checks.

**Negative example — counterexample.** Searching the whole packet for any signature can accept a
signature from the wrong form. A classifier's label is never proof that the right party signed the right
field.

**Boundary.** If the contract is already a separate file, skip splitting. Signature presence, identity,
and authenticity are downstream evidence analysis; unresolved disagreement goes to review. The classifier
must never infer "signed" from the document type.

### CS3 Classify correspondence with asymmetric error cost

**Problem description.** One logical correspondence document has to be routed among roughly seven
predefined classes — authorization, denial, clinical request, pending review and similar. The classes are
not equally costly to confuse: sending an authorization down the denial path does far more damage than an
ordinary mix-up, so overall accuracy is the wrong thing to optimise. Working behaviour: the confusing
class pairs are blind-tested and the critical-error confusion matrix is inspected alongside the review
load, rather than a high aggregate score being accepted as evidence the critical class is safe.

**Best-fit solution.** Classification only — a published classifier or an explicitly evaluated agent
implementation — then a Switch node. Bind planned review to Human nodes.

**Decision reasoning.** The decisive signal is the asymmetry: one confusion costs far more than the
others, which changes the architecture and not just the threshold. Define the classes and name the
confusing pairs. Evaluate critical errors separately from overall accuracy. Route uncertain cases to
review. Select an architecture that meets the measured critical-error bar rather than assuming one pass
will.

**Negative example — observed failure.** A single-model classifier's confidence score failed to separate
critical errors: driving critical errors to zero collapsed straight-through processing to a small
fraction of volume. A more complex consensus design raised throughput substantially but still produced a
critical error — better, but not the zero-error result the requirement demanded.

**Boundary.** If a label really means "no urgency claim appears anywhere", that is an absence question —
````

### 3b. Restore the five cross-references

| Case | Currently reads | Restore to |
|---|---|---|
| AF3 boundary | *(sentence deleted)* | `Where the question is which of several document types this is, that is CS.` |
| EX1 boundary | `Packets need their document boundaries established first.` | `Packets need CS1 first.` |
| EX2 boundary | `Separate mixed logical documents first.` | `Split mixed logical documents first.` |
| BT1 boundary | `the documents must be separated before extraction.` | `classification and extraction come first.` |
| BT2 boundary | *(CS clause removed; boundary rewritten whole)* | `If the label is a routing decision over documents rather than a column on a row, that is CS.` |

BT2 is the one to read carefully. It already carried a PA-era "no strategy here covers it yet", so
removing the CS clause would have left two dangling clauses in one boundary; the whole boundary was
rewritten instead. Work CS's clause back into the rewritten prose rather than reverting it blind.

### 3c. Restore the two Boundary Lookup rows

```markdown
| Confidence-based approval misses critical errors | CS3 | EX1 for calibrated field-review design |
| Header groups or signatures come from the wrong document | CS1 or CS2 | Extract only after boundaries are established |
```

Both were rewritten rather than deleted: the first promoted `EX1` to primary, the second made its
counter-boundary the answer. Replace those two rows with the originals above.

### 3d. Counts

| Line | Currently | Restore to |
|---|---|---|
| header | `18 cases · 6 decision categories · 3 per category.` | `21 cases · 7 decision categories · 3 per category.` |
| Maintaining the library | `adding a nineteenth` | `adding a twenty-second` |

---

## 4. `references/strategy-routing-guide.md`

### 4a. Handoff map — reinsert the row

The only row whose Owner column is a guide rather than a skill, which is why it was deleted rather than
retargeted.

```markdown
| Classification or splitting | see `classify-split-guide.md → classify-split-guide.md` | — |
```

### 4b. Composition patterns — reinsert pattern 5, renumbering the current 5 back to 6

```markdown
5. **Segment, then extract.** Classification and boundary resolution → per-segment Extract, preserving
   original page ranges → deterministic duplicate rules → End.
```

---

## 5. `references/case-template.md`

| Line | Currently | Restore to |
|---|---|---|
| category list | `(AH, AF, SU, PS, EX, BT)` | `(AH, AF, CS, SU, PS, EX, BT)` |
| agreement clause | `18-case distribution` | `21-case distribution` |

CS had no per-category acceptance checklist item, so there is nothing to restore there.

---

## 6. Eval — `tests/tasks/uipath-doc-strategy-select/routing/`

### 6a. Restore the CS row to `strategy_selection.jsonl`

Takes the set from 6 rows back to 7, one per strategy. Insert after the AF row.

```json
{"id": "cs-complaint-channels--a", "pair": "cs-complaint-channels", "variant": "a", "expected_strategy": "CS", "provenance": "engagement", "workload": "Complaints reach us through twelve channels — email, web forms, a legacy messaging system, physical mail — and every one of them has to be sorted into one of seventy-seven categories before a case is opened. Getting the category wrong sends the complaint to the wrong team and restarts the clock. We need the category decided and the case routed; the case record itself gets built afterwards."}
```

### 6b. `check_strategy.py`

Move `"CS"` out of `STRATEGY_ANSWERS` and back into `STRATEGIES`, and drop it from the withheld-strategy
comment. The pattern: a withdrawn label stays *answerable* so a stale answer reads "selected CS" rather
than "unparseable", but can never be *expected*.

### 6c. `analyze_consistency.py`

`STRATEGIES` is a **second independent copy** — the module imports `KEY` and `STRATEGY_ANSWERS` from
`check_strategy` but not `STRATEGIES`. Add `"CS"` back there too.

### 6d. `strategy_selection.yaml`

| Site | Currently | Restore to |
|---|---|---|
| description, row count | `6 rows: one workload per strategy, across all six` | `7 rows … across all seven` |
| prompt vocabulary | `one of AH, AF, SU, PS, EX, BT` | `one of AH, AF, CS, SU, PS, EX, BT` |
| threshold comment | `0.78 x 6 rows = 4.68, so 5 of 6 must pass` | `0.78 x 7 rows = 5.46, so 6 of 7 must pass` |

Restore the paragraph explaining why a CS miss is tolerable. It is the only place in `tests/` citing the
unpublished-configuration fact, and `skills:check-links` does not scan task YAML, so nothing reports it
missing:

```text
CS is the strategy most likely to miss. There is no published Classify & Split node
configuration in Flow (references/classify-split-guide.md says so outright), so an
agent reasoning about what it can actually build may legitimately fall back. Read a
CS miss as a product-gap signal.
```

---

## 7. `CASE-MEMO-MAP.md` (local only, never committed)

Its header was updated from `(PA1–PA3 withheld)` to `(PA1–PA3 and CS1–CS3 withheld)`. The CS1–CS3
provenance rows and the three `cs-*` eval-row rows were annotated, not deleted. Drop the CS annotations
on reinstatement.

---

## Validation after reinstating

```bash
npm run skills:validate && npm run skills:build   # the flavor coupling fails here first
npm run skills:check-links
python3 scripts/check-skill-status.py --write-readme
python3 scripts/check-skills-sh.py
python3 scripts/check-task-host-paths.py
```

Then by hand, because no script checks these:

- Workflow steps run 1–6 with no gap, and step 3 names CS exactly once.
- `case-library-guide.md` reports 21 cases and `grep -c '^### '` agrees.
- Every Boundary Lookup row names a case that exists.
- `case-template.md`'s agreement clause matches the case count.
- `README.md`'s catalog row names Classify & Split, matching the frontmatter description.
- The three rewritten obligation sites in § 0 each state the rule once, not twice.
