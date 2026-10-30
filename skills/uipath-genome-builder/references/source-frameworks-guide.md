# Source Frameworks Guide — reading a source automation in `extract` and `build`

`uipath-planner`'s `extract` reads a source automation to write its genome; `uipath-genome-builder`'s `build` reads the same source again to migrate what the genome body leaves out (UI targets, test data). This guide is the one home of how each source is read and how the framework migration pack is resolved; both skills ship it byte-identical and both verbs' read plans open it.

## UiPath sources

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read with [uipath-source-guide.md](uipath-source-guide.md):

- **`extract`** reads it whole, deployed state included. A `.bpmn` here is an existing process project to document; a BPMN model handed over as the design to build from is input to `uipath-planner`'s `design`, not a source.
- **`build`** reads only its § UI Target Locators and § Test Data, with `uipath-genome-builder`'s source-migration-guide.md § Migration preflight step 4, `uipath-genome-builder`'s ui-target-migration-guide.md § UI targets and `uipath-genome-builder`'s ui-verification-guide.md: its UI targets are carried over, not translated.

## Other frameworks — the framework migration pack

Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request, or `build`'s scaffolding answer (`uipath-genome-builder`'s execution-guide.md § 1.3), already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks: for `extract`, the row whose detection signals match the given files; for `build`, the framework the Source Map names. An extracted genome names its framework in the Source Map; that name selects the row and makes the build a **migration**.
3. **Run, then read.** Run the row's script before reading any export file.
   - **`extract`** reads `<PACK_DIR>/<framework>/source-guide.md` in full and writes the genome and its Source Map.
   - **`build`** reads `uipath-genome-builder`'s source-migration-guide.md whole and derives the catalogs with the same script (its § Migration preflight). A build with UI activities also reads `uipath-genome-builder`'s ui-target-migration-guide.md and `uipath-genome-builder`'s offline-definition-workarounds-guide.md, the source guide's § Composite actions and `<PACK_DIR>/<framework>/selectors-guide.md` by technology section together with `uipath-genome-builder`'s selector-translation-guide.md and its guide for each technology the target catalog holds — web (`uipath-genome-builder`'s selector-translation-web-guide.md), SAP GUI (`uipath-genome-builder`'s selector-translation-sap-guide.md), desktop (`uipath-genome-builder`'s selector-translation-desktop-guide.md); a build with test components reads `uipath-genome-builder`'s test-execution-guide.md.

## When the pack does not answer

| Situation | `extract` | `build` |
|---|---|---|
| No row of the pack matches the files | Say which framework the files appear to come from and that the pack has no guide for it; never improvise an extraction | — (the Source Map already names the framework) |
| The pack is not available | Stop: no genome is extracted from a framework nobody has read | Continue without the migration part — live capture or placeholders, stated in the report (`uipath-genome-builder`'s source-migration-guide.md § Migration preflight step 1) |
