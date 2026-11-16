# Source Frameworks Guide — reading a source automation in `build`

`build` reads an extracted genome's source again to migrate what the genome body leaves out (UI targets, test data). The genome's Source Map names the source framework ([genome-reading-guide.md § Source Map](genome-reading-guide.md)).

## UiPath sources

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read through [source-migration-guide.md § UI Target Locators](source-migration-guide.md) and § Test Data, with [source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4, [ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md) and [ui-verification-guide.md](ui-verification-guide.md): its UI targets are carried over, not translated.

## Other frameworks — the framework migration pack

Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask for its location.** Ask "Where is the framework migration guide?" unless the request, or the scaffolding answer ([configuration-questions-guide.md](configuration-questions-guide.md)), already gave it. Accept a folder path (`<PACK_DIR>`); a git URL is cloned into a scratch folder first. Never search the disk for it, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks: the framework the Source Map names. That name makes the build a **migration**.
3. **Run, then read.** Run the row's script before reading any export file. Read [source-migration-guide.md](source-migration-guide.md) whole and derive the catalogs with the same script (its § Migration preflight). Whoever names a deliverable also reads the source guide's § Component Detection naming, for the product terms it lists ([source-migration-guide.md § Source steps that are not UI actions](source-migration-guide.md)). Whoever writes UI activities or targets also reads [ui-target-migration-guide.md](ui-target-migration-guide.md), [composite-interactions-guide.md](composite-interactions-guide.md), the source guide's § Composite actions and `<PACK_DIR>/<framework>/selectors-guide.md` by technology section; whoever writes or registers targets — a target spec, Object Repository elements — also reads [offline-definition-workarounds-guide.md](offline-definition-workarounds-guide.md) and [selector-translation-guide.md](selector-translation-guide.md) with [selector-matching-guide.md](selector-matching-guide.md) and its guide for each technology the target catalog holds — web ([selector-translation-web-guide.md](selector-translation-web-guide.md)), SAP GUI ([selector-translation-sap-guide.md](selector-translation-sap-guide.md)), desktop ([selector-translation-desktop-guide.md](selector-translation-desktop-guide.md)); whoever builds test components reads [test-execution-guide.md](test-execution-guide.md).

## When the pack does not answer

| Situation | `build` |
|---|---|
| The pack is not available | Continue without the migration part — live capture or placeholders, stated in the report ([source-migration-guide.md § Migration preflight](source-migration-guide.md) step 1) |
