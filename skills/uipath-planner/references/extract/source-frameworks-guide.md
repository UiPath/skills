# Source Frameworks Guide — reading a source automation in `extract`

`extract` reads a source automation to write its genome: how each source is read, and how a framework migration pack is resolved.

## UiPath sources

A UiPath source (`.uipx`, `project.json`, `project.uiproj`, `.xaml`/`.cs`, `.flow`, `.bpmn`, `caseplan.case`, `caseplan.json`, `agent.json`, `Workflow.json`, `uipath.json`) is read whole with [uipath-source-guide.md](uipath-source-guide.md), deployed state included. A `.bpmn` here is an existing process project to document; a BPMN model handed over as the design to build from is input to `design`, not a source.

## Other frameworks — the framework migration pack

Every other framework is read through the **framework migration pack**, which holds per framework a **source guide**, a **selectors guide** and an **inventory script**. Resolve it once per run:

1. **Ask which pack to read**, unless the request already names one. The question: "Which migration pack — the guides and script that read the export — should I use: UiPath's pack (https://github.com/UiPath/business-logic-extraction), or another, as a folder path or a git URL?" When the request says to proceed without questions, use UiPath's pack. Download UiPath's pack into a new scratch folder, which needs no git and no GitHub account; `<PACK_DIR>` is then `<SCRATCH_DIR>/business-logic-extraction-main`:

   ```bash
   curl -fsSL https://github.com/UiPath/business-logic-extraction/archive/refs/heads/main.tar.gz | tar -xzf - -C "<SCRATCH_DIR>"
   ```

   In Windows PowerShell, where `curl` is `Invoke-WebRequest` and a pipe breaks binary data, save the archive with `curl.exe -fsSL -o "<SCRATCH_DIR>/packs.tar.gz"` and the same URL, then run `tar.exe -xzf "<SCRATCH_DIR>/packs.tar.gz" -C "<SCRATCH_DIR>"`. Another git URL is cloned into a scratch folder first, and the clone is `<PACK_DIR>`; a folder path is `<PACK_DIR>` itself. Never search the disk for a pack, never work from memory of its contents, never copy its files into this skill or beside a genome.
2. **Select the framework row** in `<PACK_DIR>/README.md` § Frameworks whose detection signals match the given files. The genome names that framework in its Source Map; the name is what makes a build of it a **migration**.
3. **Run, then read.** Run the row's script before reading any export file, then read `<PACK_DIR>/<framework>/source-guide.md` in full and write the genome and its Source Map.

## When the pack does not answer

| Situation | What `extract` does |
|---|---|
| The download or clone fails | Say why, and ask for a folder path |
| No row of the pack matches the files | Say which framework the files appear to come from and that the pack has no guide for it, and ask for a pack that has one; never improvise an extraction |
| The pack is not available | Stop: no genome is extracted from a framework nobody has read |

When the request says to proceed without questions, a failed download or clone and a pack with no matching row ask nothing: the pack is not available.
