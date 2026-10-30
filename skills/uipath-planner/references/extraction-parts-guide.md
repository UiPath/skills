# Extraction Parts Guide — extract in parts and reconcile

Runs when the extraction guide's sizing (its Step 2b) plans parts, under [parts-guide.md](parts-guide.md). Extraction's own agent is the orchestrator: besides the work that guide gives it, it reconciles the parts' output and writes the process genome.

1. **One part per component, reading its objects whole.** A component above one part's budget is split along its call graph: each part takes one phase's subtree (the object that runs the phase and what only it calls) and a step range the orchestrator assigns. Every object belongs to exactly one part. A part whose objects call an object another part owns names that part's step and does not describe the object.
2. **Who writes.** A part that owns a whole component writes that component's genome file. The parts of a split component write notes, and the orchestrator writes that component's genome from them. Notes go to the part's notes file in the working folder, in genome wording, so the orchestrator assembles and reconciles instead of rewording: each step of the range with its substeps, Business Rules, Error Handling entries, Acceptance Criteria and Source Map rows, then the facts the component's shared sections need (Interface, Target Applications, Platform Dependencies, open values).
3. **The shared decisions** ([parts-guide.md](parts-guide.md) item 1). The orchestrator runs the source guide's self-test and export-wide commands once, reads the export-wide renderings (an inventory profile) in full and the per-object renderings of the shared components, and writes into the brief:
   - the component list with file names; each part's objects and bytes, with the step range of each part of a split component;
   - each shared component's step numbers and public workflows with their arguments, so callers name them before that component is written;
   - the names of lanes, environments and every platform resource, one credential asset per login account ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md));
   - the questions that are process-wide, asked only in the process genome;
   - the owner of each helper that several components call;
   - each part's finding-id prefix, so ids stay unique within a component's Source Map.

   Parts never rerun an export-wide command. They read the renderings the extraction guide's Step 2b wrote (a UiPath part reads its files), and run the direct read only to verify suspected defects ([defect-verification-guide.md](defect-verification-guide.md)).
3a. **A part may run as a fork of the orchestrator** instead of a fresh subagent, under the rule on when a fork pays ([parts-guide.md](parts-guide.md) item 5). At extraction the shared reads are the brief, the extraction guide, this guide, the format guide, the template, the source guide and the export-wide renderings of rule 3; the fork reads its own objects' renderings. A fork writes only its genome or notes file and its ledger; the brief, the process genome, the extraction guide's Step 6b check and the Reconciliation stay the orchestrator's, and its return is checked as rule 9 says.
4. **The brief** ([parts-guide.md](parts-guide.md) item 2) names, among its absolute paths, the export, the pack, the genome folder and the working folder; its reads are those of rule 6 and its return contract that of rule 8.
5. **The ledger** ([parts-guide.md](parts-guide.md) item 3), in the working folder, lists every assigned object with its state (read, steps written or noted, findings verified), and its `Resume` block names the next object. A part that ends before reading all its objects returns the unread ones. The orchestrator writes them into the Source Map as a `Not read (run cut short)` row with each object's id and flags the steps they feed `*[Inferred]*`; [edit-guide.md § Partial Re-extraction](edit-guide.md) completes them.
6. **Every part reads by plan, in at most three turns** ([parts-guide.md](parts-guide.md) item 4). Turn 1: the brief, the extraction guide, this guide, parts-guide.md, the format guide (every section before § Process Genome Sections: a part writes a component genome), the extracted genome guide, the component template and the source guide as the extraction guide's § Source Guides requires; the transactional shape guide when the part's objects show per-item work, and the defect verification guide at the first suspected defect, as [extract-guide.md § Read Plan](extract-guide.md) opens them. Turn 2: the renderings of all the part's objects, in one message. Turn 3: only the direct reads its findings need and the sections a turn-2 read routes to.
7. **A part verifies its own suspected defects.** It runs both passes of [defect-verification-guide.md](defect-verification-guide.md) itself, since it holds the rendering and the direct read is a targeted lookup, and returns the verdicts. A finding on an object another part owns goes to the orchestrator as a new finding with its line.
8. **Return contract** ([parts-guide.md](parts-guide.md) item 6). A part returns:
   1. the file written — the genome file, or the notes file;
   2. counts: steps, rules, handlers, criteria, test cases;
   3. target applications;
   4. the Configuration Questions written, marked where another component may ask the same;
   5. platform resources, each with the name used;
   6. secrets found, by object and line, never the value;
   7. every verdict on a suspected defect, with the fields [defect-verification-guide.md](defect-verification-guide.md) returns and the behaviour the rebuild follows;
   8. cross-component calls: calling step, callee component and step, data passed, failure behaviour;
   9. transactional signals: per-item constructs with object and line, for the Transactional Shape;
   10. deviations from the brief, and every object left unread.
9. **Checking a return** ([parts-guide.md](parts-guide.md) item 6). Before reconciling, the orchestrator checks each part mechanically: the file exists with the counts returned, every defect has its Source Map row with lines, and every assigned object appears in a Source Map row or in the unread list.

## Reconciliation

Before the extraction guide's Step 6b Source Map check and before edits are offered, the orchestrator works through every item:

1. **Questions.** A question two or more components ask moves to the process genome's Configuration Questions; each component keeps, in its own numbered list, a one-line pointer that names that number, a statement with no question mark: `N. {What it decides}: process genome Configuration Question M.`
2. **Names.** Every platform resource, lane and environment carries the brief's name in every file; each drift is renamed.
3. **Defect index.** The process genome's defect table is built from the returned verdicts ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)).
4. **Rebuild follows.** Each defect is re-checked against that section's rule on which behaviour the rebuild follows, from the intent evidence its verdict returned. A wrong mark is corrected at the step and in the index.
5. **Code in bodies.** Search every genome file for selector tags (`<webctrl`, `<wnd`, `<html`, `<ctrl`), activity and command names, file extensions, drive and repository paths, and the source's variable syntax (source guide § Value syntax). A hit inside the Source Map is provenance and stays; so do a selector a test asserts as a value (extraction guide Step 3) and a text the source writes that [genome-format-guide.md § Provenance](genome-format-guide.md) keeps verbatim. Every other hit is translated or moved to the Source Map. Interface descriptions included ([genome-format-guide.md § Interface](genome-format-guide.md)).
6. **Cross-component calls.** Every returned call is a Handoffs row, and the Interfaces of both components agree with it. A helper several components call is described once, in its owner, and each caller names that owner's step.

Then the extraction guide's Step 6b check runs over every file, and its Step 7 offers edits.
