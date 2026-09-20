# Source Framework Contract

Extraction is framework-agnostic: [extraction-guide.md](../extraction-guide.md) runs the same pipeline for any source, and a **source guide** under `references/sources/` supplies the framework-specific knowledge. `uipath-source-guide.md` is the reference implementation. Add one guide per additional framework (Automation Anywhere, Blue Prism, Worksoft Certify, Power Automate, …); the pipeline picks the guide whose detection signals match.

## What a source guide must provide

Every source guide has these sections, in this order, with these headings:

1. **Detection** — file and folder signals that identify the framework and the unit of deployment. Must distinguish a single component from a multi-component bundle (solution, release package, project group). Must state the fallback when the top-level manifest is missing.
2. **Inventory and Exclusions** — file patterns per artifact type; directories and files that are generated, cached, or boilerplate and must not be read for logic.
3. **Component Detection** — how to recognise each buildable component type and which genome component **Type** and UiPath **Skill** it maps to. This table is the migration bridge: it says what each foreign construct becomes in UiPath.
4. **Signal Tables** — one table per artifact type: `signal | where in the file | what it tells you | example`. Cover: steps/actions, control flow (conditions, loops, switches), error handling (try/catch, retry, on-error paths), arguments and data (inputs, outputs, variables, data items), external targets (applications, URLs, connections, credentials), invocation edges (calls to other components), triggers and schedules.
5. **Target Resolution** — how to resolve indirect references to the real application or system (connection GUIDs, object references, library names → "Salesforce", "SAP GUI").
6. **Call Graph Rules** — where the entry point is declared, how invocation edges are expressed, ordering rules for parallel branches, how to handle libraries and unreachable objects.
7. **Expression Translation** — the framework's expression language(s) and how operators map to plain language (extends the table in [genome-format-guide.md § Business Rules](../genome-format-guide.md)).
8. **Platform Resources** — where queues, credentials, assets, schedules, and connections are declared, and their UiPath equivalents for the Platform Dependencies section.
9. **UI Target Locators** — where the framework stores the recognition data of the controls it automates (object maps, selectors, XPaths, image anchors), which locator formats occur and how each maps to a UiPath technology, and the command or procedure that derives a normalized target catalog from the export **at execution time** (extraction reads it for control types and actions and records counts; it writes no copy beside the genome). The attribute-by-attribute translation lives in a companion `references/sources/<framework>-selectors-guide.md` with one table per technology the framework records (`source field | UiPath tag.attribute | transform | confidence | notes`), whose right-hand side uses only the vocabulary of [selector-translation-guide.md](../selector-translation-guide.md) — the UiPath-side rules (criteria, anchors, position, purpose, confidence tiers) are stated there once and never restated in a source guide. A framework that stores none says so; execution then falls back to capture or placeholders.
10. **Test Data** — where data-driving rows live (recordsets, data sheets, variables), how to decode them into named rows and link them to the process that runs with them (the data catalog execution derives from the export), which columns are credentials (identity migrates as a credential-asset name plus environment, secrets never), and the source's execution flags.
10b. **Provenance the Source Map must carry, and the inventory shape** — what identifies the export (manifest fields, version, database, counts) and what identifies a source object unambiguously (name plus id where names repeat), so that [genome-format-guide.md § Source Map](../genome-format-guide.md) can be filled; and the command of the framework's script that writes the two files `scripts/genome-step-map.py` consumes — a process inventory (`[{id, name, recordset, calls: [{calleeId, recordset}]}]`) and a recordset list (`[{id, name}]`). The step-map script is framework-agnostic and reads no export; only the framework script does.
11. **Framework Pitfalls** — anything that misleads a reader: designer metadata that looks like logic, generated code, duplicate definitions, version-specific quirks.

## Rules

1. **Signals, not procedures.** A source guide tells the extractor what to look for and what it means. The pipeline (inventory → signals → call graph → mapping → write) stays in the extraction guide.
2. **Every construct maps to a UiPath skill.** The Component Detection table must name a skill from [skill-mapping-guide.md](../skill-mapping-guide.md) for every buildable construct, with a one-line rationale. A construct with no UiPath equivalent maps to the nearest skill and the genome flags the gap with `*[Inferred]*` in Build With.
3. **Behavioural output only.** Nothing in a source guide licenses activity names, object names, or variable names into the genome body. They may appear only in the Source Map.
4. **Self-contained.** A source guide may not link outside `skills/uipath-genome/`.

## Adding a framework

1. Copy the section skeleton above into `references/sources/<framework>-source-guide.md`.
2. Fill Detection first; the pipeline cannot select the guide without it.
3. Add a row to the **Source Frameworks** table in `SKILL.md` (detection, source guide, selectors guide or "none", script) — the single place both Extract and Execute look up a framework's guides.
4. When the framework records UI locators, add `references/sources/<framework>-selectors-guide.md` (formats, then one translation table per technology) and survey real exports before writing it — attribute names come from the data, not from the vendor's documentation.
5. Add one worked example under `assets/examples/` extracted from a real project of that framework, with a Source Map.
6. Add a smoke task under `tests/tasks/uipath-genome/` with a fixture project of that framework.
