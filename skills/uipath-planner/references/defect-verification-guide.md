# Defect Verification Guide — suspected source defects

A finding that the source misbehaves is a **suspected defect** until the two passes below settle it. Examples: a flag set but never tested, an exit that cannot fire, a result checked but never captured, an irreversible write (a posting, a creation) followed by steps that can fail before its result is recorded, a retry an exception bypasses, a notice prepared but never sent, a branch whose test contradicts its own comment, one copy of a template doing what its sibling does not. The inventory output is a rendering the pack's script produced, and extraction has read it, not the source. So the finding may belong to the source, or to the rendering. Settle each one in two passes before it is written as a defect.

## Two passes

1. **The rendering, in full.** Re-read every object the finding rests on in the uncompressed rendering, never a compact or folded one. That includes:
   - the call's argument and result bindings, in both directions;
   - the callee's error and final blocks;
   - the disabled code (a superseded flow often explains a value the live flow only carries);
   - the sibling copies.
   Then follow the effect through the bindings to where it lands: what the caller does next, and what a later or resumed run does with what was, or was not, written.
2. **The framework's source, directly.** Open the source objects the finding rests on in the export itself, located by the identity the source guide uses (object id, editor line, node path). Read them the way the source guide states next to its command block: the pack's direct-read lookup for a structured export, which prints every key and masks secrets as the renderings do, or the cited lines of the file for code. Only when a pack offers no direct read, use a generic reader, and print no secret with it:
   - For a structured export (JSON, XML, a database dump): parse the file, select the object, and print every key. Drop only empty values and binary blobs.
   - For code: read the lines themselves.
   Compare field by field with what the rendering showed for exactly the facts the finding rests on: operators and every operand of a condition chain, bindings, flags, defaults, the presence or absence of a command. Never check through a projection that names the fields it keeps. It hides every key it did not name, such as a chained condition kept under its own key or a result binding held on the node rather than in its attributes. A reader that misses such a key produces a "discrepancy" that is the reader's own. Read the objects targeted, not whole files. The source guide's warnings against reading raw exports are about bulk reading, and this is a lookup.

## Classify and write

Classify each finding by what the two passes show, and write it accordingly:

| Finding | When | Genome | Also |
|---|---|---|---|
| **Rendering artefact** | the source differs from the rendering | write the behaviour from the source; no defect | report the renderer defect for the pack, with the object and the field |
| **Source defect** | rendering and source agree, and the behaviour contradicts the evident intent — the source's own comment or log text, a sibling copy, the step's purpose | marked **Source defect** per [extracted-genome-guide.md § Source Defects](extracted-genome-guide.md); evidence in the Source Map | the consequence traced through the source; the parts that depend on data, configuration, platform or package behaviour flagged `*[Inferred]*` |
| **Source rule** | rendering and source agree, and the source's comment or design shows the behaviour is intended | the rule, unmarked | nothing |
| **Unresolved** | the structure is certain, but the behaviour turns on a setting or platform or package semantics that neither the export, the pack, the vendor's documentation nor the platform's own code settles | both readings stated, the one the rebuild follows marked `*[Inferred]*` | report the undocumented semantics for the pack |

Semantics the vendor's documentation or the platform's own code settles — a default both the rendering and the export leave out, what a node does with an empty input — are facts, not unresolved: write them at the step, name the page, or the file and line, in the finding's Source Map row, and report them for the pack when its source guide lacks them.

Each finding gets its own Source Map row, with the object ids, the line numbers and the classification. Each component also gets one Verification row saying that both passes were made and whether the rendering matched the source. A finding nobody verified is not written as a defect. When time does not allow both passes, or a verdict does not come back, it is written as the behaviour the rendering shows, flagged `*[Inferred]*`, with its Source Map row saying which pass is missing.

## With subagents

**With subagents.** Where the host offers subagents and the passes would read more than a subagent's own fixed reads (this guide and the source guide sections below), the two passes run in them, in parallel, and extraction keeps only their verdicts: the direct reads and the traced bindings are then most of the verification's reading, and a verdict is a few lines. A few findings on small renderings cost less verified by extraction itself than the fixed reads a subagent repeats. One subagent takes the findings of one object, or of the objects one finding spans, so it reads each source guide section once. Its brief names the findings (the behaviour suspected, with object ids and lines), the export path, `<PACK_DIR>` and its reads: this guide whole; the source guide's command block with the paragraphs after it, its value syntax, and the signal rows of the commands the findings involve. The subagent writes nothing and returns, per finding, a verdict, never a retelling:

1. The class, from the table above.
2. The behaviour as fact, each fact with its object id, line, and the source key and value it rests on.
3. Whether the rendering matched the source; when not, the object and the field, for the pack report.
4. The consequence through the bindings, each hop with its object id and line.
5. Where the intent is stated: a comment or log text at the defect, or a sibling copy that does it, with its line; otherwise "the step's purpose only". [extracted-genome-guide.md § Source Defects](extracted-genome-guide.md) decides from it which behaviour the rebuild follows.
6. For an unresolved finding, both readings and the setting or semantics they turn on.

In a run in parts, each part runs both passes itself ([extraction-parts-guide.md](extraction-parts-guide.md) rule 7). A further suspicion the subagent meets comes back unverified, with its line, as a new finding. A fact returned without its line is unverified, and a verdict that arrives cut off is asked for again, never completed from the part received. When a verdict contradicts what extraction read in the rendering, extraction re-reads the cited line with the direct read before writing. Without subagents, extraction runs both passes itself.

**Writing while the verdicts are out.** Where the subagents run in the background, extraction does not wait for them. It goes on with the remaining steps and writes the files, each finding's step stating the behaviour the rendering shows, with no marker, no intent and no defect-index row. As each verdict arrives, extraction edits it in where the table above says: the step (the marker, the behaviour rewritten from the source, or both readings), the finding's Source Map row, and, for a defect, the process genome's index row; then the component's Verification row. Once the last verdict is in, the Source Map check ([extract-guide.md](extract-guide.md) Step 6b) runs again, and only then are edits offered.
