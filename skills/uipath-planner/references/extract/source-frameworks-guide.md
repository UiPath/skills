# Source Frameworks Guide — reading a source automation in `extract`

`extract` reads a source automation to write its genome: how each source is read, and how a framework migration pack is resolved.

## UiPath sources

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read whole with [uipath-source-guide.md](uipath-source-guide.md), deployed state included. A `.bpmn` here is an existing process project to document; a BPMN model handed over as the design to build from is input to `design`, not a source.

## Other frameworks — the framework migration pack

Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks whose detection signals match the given files. The genome names that framework in its Source Map; the name is what makes a build of it a **migration**.
3. **Run, then read.** Run the row's script before reading any export file, then read `<PACK_DIR>/<framework>/source-guide.md` in full and write the genome and its Source Map.

## When the pack does not answer

| Situation | What `extract` does |
|---|---|
| No row of the pack matches the files | Say which framework the files appear to come from and that the pack has no guide for it; never improvise an extraction |
| The pack is not available | Stop: no genome is extracted from a framework nobody has read |
